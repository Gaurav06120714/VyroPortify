"""S3-compatible object storage service.

Works identically against:
  - AWS S3   → set STORAGE_PROVIDER=s3
  - Cloudflare R2 → set STORAGE_PROVIDER=r2 + R2_ENDPOINT_URL

All public methods are async via run_in_executor so the event loop is never blocked
by boto3's synchronous network calls.

Usage
-----
    from app.services.s3_service import storage

    # Upload
    key = await storage.upload_file(file_bytes, user_id, filename, content_type)

    # Presigned download URL — valid for 48 hours
    url = await storage.presigned_url(key, ttl_hours=48)

    # Delete
    await storage.delete_file(key)
"""

import asyncio
import logging
import uuid
from datetime import UTC, datetime
from functools import partial
from typing import BinaryIO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Allowed MIME types and their canonical extensions ──────────────────────────
ALLOWED_MIME_TYPES: dict[str, str] = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "doc",
}

# ── Presigned URL constraints ──────────────────────────────────────────────────
# ttl_hours must be a positive multiple of 2 and ≤ PRESIGNED_URL_MAX_HOURS.
_MIN_HOURS = 2
_STEP_HOURS = 2  # must be a multiple of 2


# ── Validation helpers ─────────────────────────────────────────────────────────

def validate_presigned_ttl(ttl_hours: int) -> int:
    """Validate and return ttl_hours; raise ValueError if out of range.

    Rules:
        - Must be a positive multiple of 2  (2, 4, 6, … 168)
        - Must be ≤ settings.PRESIGNED_URL_MAX_HOURS
    """
    if ttl_hours < _MIN_HOURS:
        raise ValueError(f"ttl_hours must be at least {_MIN_HOURS}")
    if ttl_hours % _STEP_HOURS != 0:
        raise ValueError(f"ttl_hours must be a multiple of {_STEP_HOURS}")
    if ttl_hours > settings.PRESIGNED_URL_MAX_HOURS:
        raise ValueError(
            f"ttl_hours cannot exceed {settings.PRESIGNED_URL_MAX_HOURS} "
            f"({settings.PRESIGNED_URL_MAX_HOURS // 24} days)"
        )
    return ttl_hours


def validate_content_type(content_type: str) -> str:
    """Return the file extension for an allowed content-type; raise ValueError otherwise."""
    normalised = content_type.split(";")[0].strip().lower()  # strip charset= etc.
    if normalised not in ALLOWED_MIME_TYPES:
        allowed = ", ".join(sorted(ALLOWED_MIME_TYPES.keys()))
        raise ValueError(f"Unsupported file type '{normalised}'. Allowed: {allowed}")
    return ALLOWED_MIME_TYPES[normalised]


def build_s3_key(user_id: uuid.UUID, filename: str, content_type: str) -> str:
    """Return a unique, collision-free S3 key.

    Structure: resumes/<user_id>/<timestamp>-<uuid4>.<ext>

    The uuid4 suffix guarantees uniqueness even if two users upload the same
    filename at the exact same millisecond.
    """
    ext = validate_content_type(content_type)
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    unique = uuid.uuid4().hex[:8]
    return f"resumes/{user_id}/{ts}-{unique}.{ext}"


# ── S3 client factory ──────────────────────────────────────────────────────────

def _make_s3_client():  # type: ignore[return]
    """Build a boto3 S3 client configured for the active provider.

    AWS S3  → standard endpoint, SigV4
    Cloudflare R2 → custom endpoint_url, SigV4 (R2 is S3-compatible)
    """
    kwargs: dict = {
        "service_name": "s3",
        "aws_access_key_id": settings.storage_access_key_id,
        "aws_secret_access_key": settings.storage_secret_access_key,
        "region_name": settings.storage_region,
        "config": Config(
            signature_version="s3v4",
            retries={"max_attempts": 3, "mode": "adaptive"},
        ),
    }

    endpoint = settings.storage_endpoint_url
    if endpoint:
        kwargs["endpoint_url"] = endpoint

    return boto3.client(**kwargs)


# ── Storage service ────────────────────────────────────────────────────────────

class S3StorageService:
    """Thin async wrapper around boto3's S3 client.

    boto3 is synchronous — every call is offloaded to the default thread-pool
    executor via ``asyncio.get_event_loop().run_in_executor`` so FastAPI's
    event loop is never blocked.
    """

    def __init__(self) -> None:
        self._client = None   # lazy — created on first use
        self._lock = asyncio.Lock()

    def _get_client(self):
        """Return (or lazily create) the boto3 S3 client."""
        if self._client is None:
            self._client = _make_s3_client()
        return self._client

    async def _run(self, fn, *args, **kwargs):
        """Run a synchronous boto3 call in a thread-pool executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(fn, *args, **kwargs))

    # ── Public API ─────────────────────────────────────────────────────────

    async def upload_file(
        self,
        data: bytes | BinaryIO,
        user_id: uuid.UUID,
        filename: str,
        content_type: str,
    ) -> str:
        """Upload *data* to S3/R2 and return the object key.

        Args:
            data:         Raw bytes or a file-like object.
            user_id:      Owner's UUID — used to namespace the S3 key.
            filename:     Original filename (used only for extension detection).
            content_type: MIME type (e.g. ``"application/pdf"``).

        Returns:
            The S3 object key (store this in the database as ``s3_key``).

        Raises:
            ValueError:  Unsupported content-type.
            ClientError: boto3 / S3 error.
        """
        key = build_s3_key(user_id, filename, content_type)
        bucket = settings.storage_bucket

        client = self._get_client()

        put_kwargs: dict = {
            "Bucket": bucket,
            "Key": key,
            "ContentType": content_type,
            # Prevent public access — always use presigned URLs
            "ServerSideEncryption": "AES256",
            "Metadata": {
                "uploaded-by": str(user_id),
                "original-filename": filename[:1024],  # S3 metadata max
            },
        }

        if isinstance(data, bytes):
            put_kwargs["Body"] = data
            await self._run(client.put_object, **put_kwargs)
        else:
            # file-like object → use upload_fileobj (handles multipart automatically)
            await self._run(client.upload_fileobj, data, bucket, key, ExtraArgs={
                "ContentType": content_type,
                "ServerSideEncryption": "AES256",
                "Metadata": put_kwargs["Metadata"],
            })

        logger.info("Uploaded s3://%s/%s (user=%s)", bucket, key, user_id)
        return key

    async def upload_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str,
    ) -> str:
        """Upload raw bytes to an explicit S3 key (no key derivation).

        Used by v2.3 resume PDF exports where the key encodes the
        content hash for cache-friendly deduplication.
        """
        bucket = settings.storage_bucket

        def _put():
            return self._get_client().put_object(
                Bucket=bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                ACL="private",
            )

        await self._run(_put)
        return key

    async def presigned_url(
        self,
        key: str,
        ttl_hours: int = settings.PRESIGNED_URL_DEFAULT_HOURS,
    ) -> str:
        """Generate a presigned GET URL for *key*.

        Args:
            key:       S3 object key returned by :meth:`upload_file`.
            ttl_hours: URL validity in hours.
                       Must be a positive multiple of 2 (e.g. 2, 4, 24, 48).
                       Maximum is ``settings.PRESIGNED_URL_MAX_HOURS``.

        Returns:
            A time-limited presigned URL string. The URL is usable without any
            AWS credentials — suitable to hand directly to the browser.

        Raises:
            ValueError:  Invalid ttl_hours value.
            ClientError: boto3 / S3 error.

        Examples:
            >>> url = await storage.presigned_url(key, ttl_hours=24)
            >>> url = await storage.presigned_url(key, ttl_hours=48)
            >>> url = await storage.presigned_url(key, ttl_hours=96)
        """
        ttl_hours = validate_presigned_ttl(ttl_hours)
        ttl_seconds = ttl_hours * 3600

        client = self._get_client()

        url: str = await self._run(
            client.generate_presigned_url,
            "get_object",
            Params={"Bucket": settings.storage_bucket, "Key": key},
            ExpiresIn=ttl_seconds,
        )

        logger.debug(
            "Generated presigned URL for %s (ttl=%dh expires_in=%ds)",
            key, ttl_hours, ttl_seconds,
        )
        return url

    async def delete_file(self, key: str) -> None:
        """Delete the object at *key* from the active bucket.

        Silently succeeds if the object does not exist (idempotent).

        Args:
            key: S3 object key to delete.

        Raises:
            ClientError: boto3 / S3 error other than NoSuchKey.
        """
        client = self._get_client()
        bucket = settings.storage_bucket

        try:
            await self._run(client.delete_object, Bucket=bucket, Key=key)
            logger.info("Deleted s3://%s/%s", bucket, key)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                logger.warning("Delete called on non-existent key: %s", key)
                return
            logger.error("S3 delete failed for key=%s: %s", key, exc)
            raise

    async def download_file(self, key: str) -> bytes:
        """Download and return the raw bytes of an S3 object.

        Args:
            key: S3 object key to download.

        Raises:
            ClientError: If the object doesn't exist or access is denied.
        """
        client = self._get_client()
        bucket = settings.storage_bucket

        def _get():
            response = client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()

        data: bytes = await self._run(_get)
        logger.info("Downloaded s3://%s/%s (%d bytes)", bucket, key, len(data))
        return data

    async def object_exists(self, key: str) -> bool:
        """Return True if the object exists in the bucket (head_object check)."""
        client = self._get_client()
        try:
            await self._run(client.head_object, Bucket=settings.storage_bucket, Key=key)
            return True
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey"):
                return False
            raise

    def reset_client(self) -> None:
        """Force a new boto3 client on next use (useful after credential rotation)."""
        self._client = None


# ── Singleton — import this everywhere ────────────────────────────────────────
storage = S3StorageService()
