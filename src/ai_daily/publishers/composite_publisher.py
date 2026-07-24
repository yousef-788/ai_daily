"""
composite_publisher.py
------------------------
Publisher "مركّب" بينفّذ أكتر من Publisher تاني بالترتيب، بدل ما نضطر
نختار واحد بس. مفيد عشان نحتفظ بنسخة محلية (FilePublisher) كنسخة
احتياطية، في نفس وقت النشر الفعلي في قناة واتساب.
"""

import logging

from ai_daily.models.content_item import ContentItem
from ai_daily.publishers.base import BasePublisher

logger = logging.getLogger(__name__)


class CompositePublisher(BasePublisher):
    """ينفّذ قائمة من الـ Publishers بالترتيب على نفس عناصر المحتوى.

    فشل Publisher واحد (مثال: قناة واتساب مش متاحة) بيتم عزله وتسجيله،
    بدل ما يمنع باقي الـ Publishers (زي حفظ النسخة المحلية) من الشغل.

    Attributes:
        publishers: قائمة الـ Publishers المطلوب تنفيذهم بالترتيب.
    """

    def __init__(self, publishers: list[BasePublisher]) -> None:
        self.publishers = publishers

    def publish(self, items: list[ContentItem]) -> None:
        """ينفّذ publish() على كل Publisher في القائمة، بمعزل عن أخطاء بعضهم."""
        for publisher in self.publishers:
            try:
                publisher.publish(items)
            except Exception:  # noqa: BLE001 - نعزل فشل Publisher واحد عن الباقي
                logger.exception(
                    "فشل Publisher من نوع '%s'.", type(publisher).__name__
                )
