"""
base.py
-------
يعرّف هذا الملف العقد (Interface) الذي يجب أن يلتزم به أي مصدر لجمع المحتوى
(RSS، API، Scraping من موقع معين...).

الفكرة: باقي المشروع (مثل نقطة التشغيل main.py لاحقًا) هيتعامل مع أي Collector
من خلال هذا العقد فقط، من غير ما يعرف تفاصيل كل مصدر على حدة.
"""

from abc import ABC, abstractmethod

from ai_daily.models.content_item import ContentItem


class BaseCollector(ABC):
    """العقد الأساسي الذي يجب أن يطبّقه أي Collector.

    أي كلاس جديد لجمع المحتوى (مثال: RssCollector، TwitterCollector...)
    يجب أن يرث من هذا الكلاس ويطبّق method واحدة: collect().
    """

    #: اسم تعريفي للمصدر، تُستخدم لاحقًا في الـ logging وربط النتائج بمصدرها.
    source_name: str

    @abstractmethod
    def collect(self) -> list[ContentItem]:
        """يجمع المحتوى من المصدر ويُرجعه كقائمة من ContentItem.

        كل كلاس وارث لازم يطبّق المنطق الفعلي لجمع البيانات هنا.
        هذه المرحلة (تعريف العقد) لا تحتوي على أي تطبيق فعلي بعد.

        Returns:
            list[ContentItem]: قائمة بعناصر المحتوى التي تم جمعها.
        """
        raise NotImplementedError
