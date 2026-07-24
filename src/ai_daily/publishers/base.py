"""
base.py
-------
يعرّف هذا الملف العقد (Interface) الذي يجب أن يلتزم به أي Publisher
(ملف مسودة محلي الآن، واتساب API حقيقي لاحقًا).
"""

from abc import ABC, abstractmethod

from ai_daily.models.content_item import ContentItem


class BasePublisher(ABC):
    """العقد الأساسي الذي يجب أن يطبّقه أي Publisher.

    الـ Publisher بياخد "دفعة" من عناصر المحتوى (نشرة اليوم كلها)
    مش عنصر واحد، لأن الهدف النهائي هو رسالة/نشرة واحدة يومية
    تجمع كل الأخبار الجديدة، مش رسالة منفصلة لكل خبر.
    """

    @abstractmethod
    def publish(self, items: list[ContentItem]) -> None:
        """ينشر (أو يجهّز للنشر) مجموعة عناصر المحتوى المُعطاة.

        Args:
            items: عناصر المحتوى الجاهزة للنشر (بعد الجمع والمعالجة).
        """
        raise NotImplementedError
