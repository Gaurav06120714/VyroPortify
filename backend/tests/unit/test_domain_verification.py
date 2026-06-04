"""Unit tests for app.services.domain_verification (v1.2.1)."""

import pytest

from app.services import domain_verification as dv


class TestNormalizeDomain:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("Alex.dev", "alex.dev"),
            ("  alex.dev ", "alex.dev"),
            ("https://alex.dev/", "alex.dev"),
            ("http://alex.dev:8080/portfolio", "alex.dev"),
            ("ALEX.DEV", "alex.dev"),
            ("sub.alex.dev", "sub.alex.dev"),
        ],
    )
    def test_canonicalizes(self, raw, expected):
        assert dv.normalize_domain(raw) == expected

    @pytest.mark.parametrize(
        "raw",
        [
            "",
            "not a domain",
            "-leading-hyphen.dev",
            "trailing-.dev",
            "no-tld",
            "a." * 130 + "dev",  # > 253 chars
        ],
    )
    def test_rejects_invalid(self, raw):
        with pytest.raises(dv.DomainValidationError):
            dv.normalize_domain(raw)

    @pytest.mark.parametrize(
        "raw",
        [
            "vyroportify.com",
            "anything.vyroportify.com",
            "example.com",
            "localhost.local",
        ],
    )
    def test_rejects_reserved(self, raw):
        with pytest.raises(dv.DomainValidationError):
            dv.normalize_domain(raw)


class _FakeRecord:
    def __init__(self, target: str):
        self.target = target

    def __str__(self) -> str:
        return self.target


class TestVerifyCname:
    def test_verified_when_cname_matches_target(self):
        def resolver(name, rdtype):
            assert name == "alex.dev"
            assert rdtype == "CNAME"
            return [_FakeRecord(dv.CUSTOM_DOMAIN_TARGET + ".")]

        result = dv.verify_cname("alex.dev", _resolver=resolver)
        assert result.verified is True
        assert result.cname_target == dv.CUSTOM_DOMAIN_TARGET
        assert result.expected_target == dv.CUSTOM_DOMAIN_TARGET

    def test_not_verified_on_wrong_target(self):
        def resolver(name, rdtype):
            return [_FakeRecord("some-other-host.example.")]

        result = dv.verify_cname("alex.dev", _resolver=resolver)
        assert result.verified is False
        assert result.cname_target == "some-other-host.example"
        assert "expected" in result.detail.lower()

    def test_not_verified_on_nxdomain(self):
        def resolver(name, rdtype):
            raise Exception("NXDOMAIN")

        result = dv.verify_cname("nope.dev", _resolver=resolver)
        assert result.verified is False
        assert result.cname_target is None
        assert "no cname" in result.detail.lower()

    def test_case_insensitive_match(self):
        def resolver(name, rdtype):
            return [_FakeRecord(dv.CUSTOM_DOMAIN_TARGET.upper() + ".")]

        result = dv.verify_cname("alex.dev", _resolver=resolver)
        assert result.verified is True
