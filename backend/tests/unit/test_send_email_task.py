"""Unit tests for app.workers.tasks.send_email."""

from unittest.mock import patch

from app.workers.tasks.send_email import send_email_task


class TestSendEmailTask:
    def test_unknown_template_returns_false_without_raising(self):
        # Call .run() to bypass Celery delivery and exercise the function body.
        result = send_email_task.run(
            to="a@example.com", template_name="nope", params={}
        )
        assert result is False

    def test_bad_params_logged_and_returns_false(self):
        # `welcome` takes `name`, not `nickname` — bad params shouldn't crash.
        result = send_email_task.run(
            to="a@example.com",
            template_name="welcome",
            params={"nickname": "Alex"},
        )
        assert result is False

    def test_dispatches_to_email_service(self):
        with patch(
            "app.workers.tasks.send_email.email_service.send_email_sync",
            return_value=True,
        ) as mock_send:
            result = send_email_task.run(
                to="a@example.com",
                template_name="welcome",
                params={"name": "Alex"},
            )

        assert result is True
        assert mock_send.called
        kwargs = mock_send.call_args.kwargs
        assert kwargs["to"] == "a@example.com"
        assert "Alex" in kwargs["template"].html
