"""Unit tests for app.services.email_service (v1.2.0)."""

from unittest.mock import MagicMock, patch

from app.services import email_service


class TestTemplates:
    def test_welcome_renders_name_and_dashboard_link(self):
        tpl = email_service.welcome("Alex")
        assert "Alex" in tpl.html
        assert "/dashboard" in tpl.html
        assert tpl.subject.lower().startswith("welcome")

    def test_welcome_handles_empty_name(self):
        tpl = email_service.welcome("")
        assert "there" in tpl.html

    def test_portfolio_published_includes_public_url(self):
        tpl = email_service.portfolio_published("Alex", "https://example.com/p/a")
        assert "https://example.com/p/a" in tpl.html

    def test_plan_changed_titles_plan_name(self):
        tpl = email_service.plan_changed("Alex", "pro")
        assert "Pro" in tpl.subject
        assert "Pro" in tpl.html

    def test_payment_failed_subject(self):
        tpl = email_service.payment_failed("Alex")
        assert "Payment" in tpl.subject


class TestSendEmailSync:
    def test_noop_when_resend_key_missing(self):
        with patch.object(email_service.settings, "RESEND_API_KEY", ""):
            ok = email_service.send_email_sync(
                to="a@example.com", template=email_service.welcome("Alex")
            )
        assert ok is False

    def test_noop_on_invalid_address(self):
        with patch.object(email_service.settings, "RESEND_API_KEY", "re_test"):
            ok = email_service.send_email_sync(
                to="not-an-email", template=email_service.welcome("Alex")
            )
        assert ok is False

    def test_posts_to_resend_with_expected_payload(self):
        fake_response = MagicMock(status_code=200, text="ok")
        fake_client = MagicMock()
        fake_client.__enter__.return_value.post.return_value = fake_response

        with patch.object(email_service.settings, "RESEND_API_KEY", "re_test"), \
             patch.object(email_service.settings, "RESEND_FROM_EMAIL", "Vyro <no@vyro.io>"), \
             patch.object(email_service.httpx, "Client", return_value=fake_client):
            ok = email_service.send_email_sync(
                to="a@example.com", template=email_service.welcome("Alex")
            )

        assert ok is True
        post = fake_client.__enter__.return_value.post
        assert post.called
        url, = post.call_args.args
        kwargs = post.call_args.kwargs
        assert url == email_service.RESEND_API_URL
        payload = kwargs["json"]
        assert payload["from"] == "Vyro <no@vyro.io>"
        assert payload["to"] == ["a@example.com"]
        assert payload["subject"].lower().startswith("welcome")
        assert "Alex" in payload["html"]
        assert kwargs["headers"]["Authorization"] == "Bearer re_test"

    def test_returns_false_on_4xx_from_resend(self):
        fake_response = MagicMock(status_code=422, text="invalid from")
        fake_client = MagicMock()
        fake_client.__enter__.return_value.post.return_value = fake_response

        with patch.object(email_service.settings, "RESEND_API_KEY", "re_test"), \
             patch.object(email_service.httpx, "Client", return_value=fake_client):
            ok = email_service.send_email_sync(
                to="a@example.com", template=email_service.welcome("Alex")
            )

        assert ok is False

    def test_returns_false_on_network_error(self):
        import httpx

        fake_client = MagicMock()
        fake_client.__enter__.return_value.post.side_effect = httpx.ConnectError("boom")

        with patch.object(email_service.settings, "RESEND_API_KEY", "re_test"), \
             patch.object(email_service.httpx, "Client", return_value=fake_client):
            ok = email_service.send_email_sync(
                to="a@example.com", template=email_service.welcome("Alex")
            )

        assert ok is False
