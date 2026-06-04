"""Custom-domain verification via DNS CNAME lookup.

A user attaches a domain like ``alex.dev`` to a portfolio. To serve their
portfolio there, they must point a CNAME record at our hosting hostname
(``CUSTOM_DOMAIN_TARGET`` below). This module provides:

- ``normalize_domain``: canonical form for storage / lookup (lowercase,
  strip scheme + path, reject obvious garbage).
- ``verify_cname``: resolves the domain's CNAME and reports whether it
  points at our target. Used by the polling endpoint.

We do NOT verify ownership via TXT records yet — for the v1.2.1 MVP, a
CNAME pointing at our infra is sufficient proof of intent. TXT-based
proof can be added in v1.6 alongside the production-readiness work.

DNS lookups are kept synchronous because dnspython's async resolver pulls
in extra deps and CNAME lookups are sub-50ms in practice. The handler
dispatches them to a thread.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Final

logger = logging.getLogger(__name__)

# Where users must point their CNAME. Hard-coded for now; can be sourced
# from settings once we run more than one ingress hostname.
CUSTOM_DOMAIN_TARGET: Final[str] = "portfolios.vyroportify.com"

# RFC-1035-ish: labels of [a-z0-9-], dots between labels, no leading/trailing
# hyphen, total ≤ 253 chars. We're permissive on TLD length so new gTLDs work.
_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)"
    r"(?!-)(?:[a-z0-9-]{1,63}(?<!-)\.)+"
    r"[a-z]{2,63}$"
)

# Domains that are obvious abuse targets — refuse on input so a hostile user
# can't claim e.g. "vyroportify.com" and overshadow our own marketing site.
_RESERVED_SUFFIXES: Final[tuple[str, ...]] = (
    "vyroportify.com",
    "localhost",
    "local",
    "internal",
    "example.com",
    "example.org",
    "test",
)


class DomainValidationError(ValueError):
    """The input is not a usable custom-domain string."""


def normalize_domain(raw: str) -> str:
    """Return the canonical form, or raise DomainValidationError."""
    if not raw:
        raise DomainValidationError("Domain is required")

    s = raw.strip().lower()
    # Strip scheme if pasted as a URL.
    for scheme in ("https://", "http://"):
        if s.startswith(scheme):
            s = s[len(scheme):]
    # Strip path / port if pasted as a URL.
    s = s.split("/", 1)[0].split(":", 1)[0]

    if not _DOMAIN_RE.match(s):
        raise DomainValidationError("Not a valid domain name")

    for suffix in _RESERVED_SUFFIXES:
        if s == suffix or s.endswith("." + suffix):
            raise DomainValidationError("This domain is reserved")

    return s


@dataclass(frozen=True)
class VerificationResult:
    domain: str
    verified: bool
    cname_target: str | None
    expected_target: str
    detail: str


def verify_cname(domain: str, *, _resolver=None) -> VerificationResult:
    """Resolve *domain*'s CNAME and check it points at our target.

    The ``_resolver`` parameter is a test seam — pass a callable
    ``(name, rdtype) -> Iterable[record]`` to bypass real DNS. In
    production we use dnspython.
    """
    expected = CUSTOM_DOMAIN_TARGET

    if _resolver is None:
        try:
            import dns.resolver  # type: ignore[import-not-found]
        except ImportError:
            logger.error("dnspython not installed — domain verification disabled")
            return VerificationResult(
                domain=domain,
                verified=False,
                cname_target=None,
                expected_target=expected,
                detail="DNS resolver unavailable on the server",
            )
        _resolver = dns.resolver.resolve  # type: ignore[assignment]

    try:
        answers = list(_resolver(domain, "CNAME"))
    except Exception as exc:  # NXDOMAIN, NoAnswer, Timeout, etc.
        return VerificationResult(
            domain=domain,
            verified=False,
            cname_target=None,
            expected_target=expected,
            detail=f"No CNAME record found ({type(exc).__name__})",
        )

    targets = [str(getattr(a, "target", a)).rstrip(".").lower() for a in answers]
    target = targets[0] if targets else None

    if target == expected.lower():
        return VerificationResult(
            domain=domain,
            verified=True,
            cname_target=target,
            expected_target=expected,
            detail="CNAME points at the expected target",
        )

    return VerificationResult(
        domain=domain,
        verified=False,
        cname_target=target,
        expected_target=expected,
        detail=(
            f"CNAME points to {target!r}, expected {expected!r}"
            if target
            else "CNAME record is empty"
        ),
    )
