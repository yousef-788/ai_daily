"""اختبارات WhatsAppChannelPublisher.

نستخدم monkeypatch لاستبدال post_json_with_retry بنسخة وهمية، بدون
أي اتصال إنترنت حقيقي أو استدعاء فعلي لـ WAHA.
"""

from ai_daily.models.content_item import ContentItem
from ai_daily.publishers import whatsapp_channel_publisher as publisher_module
from ai_daily.publishers.whatsapp_channel_publisher import WhatsAppChannelPublisher


def _make_publisher() -> WhatsAppChannelPublisher:
    return WhatsAppChannelPublisher(
        base_url="https://example-waha.up.railway.app",
        api_key="test-api-key",
        channel_id="123456789@newsletter",
    )


def test_publish_sends_correct_payload_and_headers(monkeypatch):
    """التأكد أن الطلب بيتبعت بالـ endpoint والـ payload والهيدرز الصحيحة."""
    captured = {}

    def fake_post(url, json_payload, headers, **kwargs):
        captured["url"] = url
        captured["json_payload"] = json_payload
        captured["headers"] = headers

    monkeypatch.setattr(publisher_module, "post_json_with_retry", fake_post)

    publisher = _make_publisher()
    items = [
        ContentItem(title="خبر", url="https://example.com/1", source="Test", content="محتوى")
    ]

    publisher.publish(items)

    assert captured["url"] == "https://example-waha.up.railway.app/api/sendText"
    assert captured["json_payload"]["chatId"] == "123456789@newsletter"
    assert "خبر" in captured["json_payload"]["text"]
    assert captured["headers"]["X-Api-Key"] == "test-api-key"


def test_publish_strips_trailing_slash_from_base_url(monkeypatch):
    """التأكد أن رابط WAHA بيتنضّف من الـ slash الزيادة في الآخر لتفادي روابط مزدوجة."""
    captured = {}

    def fake_post(url, json_payload, headers, **kwargs):
        captured["url"] = url

    monkeypatch.setattr(publisher_module, "post_json_with_retry", fake_post)

    publisher = WhatsAppChannelPublisher(
        base_url="https://example-waha.up.railway.app/",  # لاحظ الـ slash في الآخر
        api_key="test-key",
        channel_id="123@newsletter",
    )
    publisher.publish([])

    assert captured["url"] == "https://example-waha.up.railway.app/api/sendText"


def test_publish_does_not_raise_when_waha_request_fails(monkeypatch):
    """التأكد أن فشل الإرسال (مثال: WAHA مش شغال) ميوقفش البرنامج بخطأ غير متوقع."""

    def fake_post(*args, **kwargs):
        raise Exception("Simulated WAHA connection failure")

    monkeypatch.setattr(publisher_module, "post_json_with_retry", fake_post)

    publisher = _make_publisher()

    # الأهم هنا: السطر ده ميرفعش أي Exception للخارج
    publisher.publish([ContentItem(title="خبر", url="https://x.com", source="S", content="c")])
