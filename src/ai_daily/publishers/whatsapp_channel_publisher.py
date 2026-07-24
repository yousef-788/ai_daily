"""
whatsapp_channel_publisher.py
-------------------------------
Publisher ينشر نشرة اليوم فعليًا في قناة واتساب، عن طريق استدعاء WAHA
(WhatsApp HTTP API) - أداة مفتوحة المصدر بتوفر REST API فوق جلسة
واتساب ويب متصلة برقمك (بعد ربطه لمرة واحدة بمسح QR code).

ملحوظة مهمة: هذا استخدام غير رسمي لواتساب (مش مدعوم رسميًا من Meta/WhatsApp)،
فيه احتمال (غير مؤكد، لكن موجود) لحظر الرقم حسب حجم وأنماط الاستخدام.
"""

import logging

from ai_daily.models.content_item import ContentItem
from ai_daily.publishers.base import BasePublisher
from ai_daily.publishers.formatting import format_digest
from ai_daily.utils.retry import post_json_with_retry

logger = logging.getLogger(__name__)


class WhatsAppChannelPublisher(BasePublisher):
    """ينشر نشرة اليوم في قناة واتساب عبر WAHA API.

    Attributes:
        base_url: رابط سيرفر WAHA (مثال: https://your-app.up.railway.app).
        api_key: مفتاح الـ API المُعرَّف وقت إعداد WAHA (WAHA_API_KEY).
        channel_id: معرّف القناة (صيغة: xxxxxxxxxxxxx@newsletter).
        session: اسم جلسة WAHA المرتبطة برقمك (افتراضيًا "default").
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        channel_id: str,
        session: str = "default",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.channel_id = channel_id
        self.session = session

    def publish(self, items: list[ContentItem]) -> None:
        """يبني نص النشرة، ويرسله فعليًا لقناة واتساب عبر WAHA.

        فشل النشر (مثال: WAHA مش شغال، أو الجلسة اتقطعت) بيتم تسجيله
        كخطأ بدل ما يوقف باقي عملية main.py (زي حفظ النسخة المحلية).
        """
        digest_text = format_digest(items)

        payload = {
            "chatId": self.channel_id,
            "text": digest_text,
            "session": self.session,
        }

        try:
            post_json_with_retry(
                f"{self.base_url}/api/sendText",
                json_payload=payload,
                headers=self._headers(),
            )
            logger.info("تم نشر نشرة اليوم في قناة واتساب بنجاح.")
        except Exception:  # noqa: BLE001 - فشل النشر ميوقفش باقي عملية main.py
            logger.exception("فشل نشر النشرة في قناة واتساب عبر WAHA.")

    def _headers(self) -> dict[str, str]:
        """هيدرز طلب WAHA API (مفتاح المصادقة + نوع المحتوى)."""
        return {
            "Content-Type": "application/json",
            "X-Api-Key": self.api_key,
        }
