"""اختبارات build_publishers: التأكد أن ناشر واتساب يتفعّل شرطيًا فقط."""

from ai_daily.main import build_publishers
from ai_daily.publishers.composite_publisher import CompositePublisher
from ai_daily.publishers.file_publisher import FilePublisher
from ai_daily.publishers.whatsapp_channel_publisher import WhatsAppChannelPublisher


def _clear_waha_env(monkeypatch):
    monkeypatch.delenv("WAHA_BASE_URL", raising=False)
    monkeypatch.delenv("WAHA_API_KEY", raising=False)
    monkeypatch.delenv("WHATSAPP_CHANNEL_ID", raising=False)


def test_build_publishers_without_waha_config_only_includes_file_publisher(monkeypatch):
    """التأكد أنه بدون إعدادات WAHA كاملة، النشر يقتصر على الملف المحلي فقط."""
    _clear_waha_env(monkeypatch)

    result = build_publishers()

    assert isinstance(result, CompositePublisher)
    assert len(result.publishers) == 1
    assert isinstance(result.publishers[0], FilePublisher)


def test_build_publishers_with_full_waha_config_adds_whatsapp_publisher(monkeypatch):
    """التأكد أنه مع توفر كل إعدادات WAHA الثلاثة، ناشر واتساب بيتضاف."""
    monkeypatch.setenv("WAHA_BASE_URL", "https://example.up.railway.app")
    monkeypatch.setenv("WAHA_API_KEY", "test-key")
    monkeypatch.setenv("WHATSAPP_CHANNEL_ID", "123@newsletter")

    result = build_publishers()

    assert len(result.publishers) == 2
    assert isinstance(result.publishers[0], FilePublisher)
    assert isinstance(result.publishers[1], WhatsAppChannelPublisher)


def test_build_publishers_with_partial_waha_config_skips_whatsapp_publisher(monkeypatch):
    """التأكد أن نقص أي إعداد واحد من الثلاثة بيمنع تفعيل ناشر واتساب (تجنّب إعداد ناقص/خاطئ)."""
    _clear_waha_env(monkeypatch)
    monkeypatch.setenv("WAHA_BASE_URL", "https://example.up.railway.app")
    monkeypatch.setenv("WAHA_API_KEY", "test-key")
    # WHATSAPP_CHANNEL_ID غير موجود عمدًا

    result = build_publishers()

    assert len(result.publishers) == 1
    assert isinstance(result.publishers[0], FilePublisher)
