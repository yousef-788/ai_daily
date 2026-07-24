"""
base.py
-------
يعرّف هذا الملف العقد (Interface) الذي يجب أن يلتزم به أي Processor
يعالج عناصر المحتوى (تنظيف، تلخيص AI لاحقًا، تصنيف...).

كل Processor بياخد ContentItem ويرجّع ContentItem جديد (بدون تعديل
الأصلي)، عشان يبقى سهل نتتبع أثر كل خطوة معالجة على حدة وقت الاختبار
أو التصحيح (debugging).
"""

from abc import ABC, abstractmethod

from ai_daily.models.content_item import ContentItem


class BaseProcessor(ABC):
    """العقد الأساسي الذي يجب أن يطبّقه أي Processor."""

    @abstractmethod
    def process(self, item: ContentItem) -> ContentItem:
        """يعالج عنصر محتوى واحد ويرجّع نسخة جديدة معدّلة منه.

        Args:
            item: عنصر المحتوى الأصلي قبل هذه الخطوة من المعالجة.

        Returns:
            ContentItem: نسخة جديدة من العنصر بعد المعالجة.
        """
        raise NotImplementedError
