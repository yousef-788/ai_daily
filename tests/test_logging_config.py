"""اختبارات configure_logging."""

import logging

from ai_daily.main import _LOG_HANDLER_MARKER, configure_logging


def _managed_handlers_count() -> int:
    """عدد الـ handlers اللي configure_logging مسؤولة عنها في الـ root logger."""
    root_logger = logging.getLogger()
    return sum(1 for h in root_logger.handlers if getattr(h, _LOG_HANDLER_MARKER, False))


def test_creates_dated_log_file(tmp_path):
    """التأكد أن الدالة بتنشئ ملف log بتاريخ اليوم فعليًا."""
    from datetime import date

    configure_logging(tmp_path)

    expected_file = tmp_path / f"{date.today().isoformat()}.log"
    assert expected_file.exists()


def test_logged_message_is_written_to_file(tmp_path):
    """التأكد أن رسالة log فعلية بتتكتب في الملف."""
    configure_logging(tmp_path)
    test_logger = logging.getLogger("test_logger_for_file_check")

    test_logger.info("رسالة اختبار فريدة 12345")

    from datetime import date

    log_file = tmp_path / f"{date.today().isoformat()}.log"
    assert "رسالة اختبار فريدة 12345" in log_file.read_text(encoding="utf-8")


def test_calling_twice_does_not_duplicate_handlers(tmp_path):
    """التأكد أن استدعاء الدالة مرتين ما بيضاعفش عدد الـ handlers (لا تكرار في الرسائل)."""
    configure_logging(tmp_path)
    configure_logging(tmp_path)

    # لازم يفضل بالظبط handler واحد للملف وواحد للشاشة، مش أكتر
    assert _managed_handlers_count() == 2
