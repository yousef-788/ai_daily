"""
content_item.py
----------------
يعرّف هذا الملف "الوحدة الأساسية" التي تتنقل بين مكونات المشروع المختلفة:
collectors (تجمعها) -> processors (تعالجها) -> publishers (تنشرها).

الهدف من توحيد الشكل هنا: أي مصدر جديد نضيفه لاحقًا (RSS، API، Scraping...)
يكفي أن يُرجع كائنات من نوع ContentItem، وباقي المشروع يتعامل معه بنفس الطريقة
بدون حاجة لمعرفة تفاصيل المصدر.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ContentItem:
    """يمثل عنصر محتوى واحد (خبر أو مقال) جاي من أي مصدر.

    Attributes:
        title: عنوان الخبر/المقال.
        url: الرابط الأصلي للمحتوى (يُستخدم لاحقًا لمنع تكرار النشر).
        source: اسم المصدر الذي جاء منه المحتوى (مثال: "TechCrunch").
        content: النص الخام للمحتوى قبل أي معالجة.
        published_at: تاريخ نشر المحتوى في مصدره الأصلي (إن وُجد).
        collected_at: تاريخ ووقت جمعنا نحن لهذا المحتوى (يُملأ تلقائيًا).
        category: تصنيف المحتوى ضمن أقسام النشرة (مثال: "news", "tools", "jobs").
            يُستخدم لتقسيم النشرة النهائية لأقسام منفصلة بدل خلط كل شيء معًا.
    """

    title: str
    url: str
    source: str
    content: str
    published_at: datetime | None = None
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    category: str = "news"

    def __post_init__(self) -> None:
        """تحقق بسيط من سلامة البيانات الأساسية عند إنشاء الكائن.

        هذا ليس "منطق معالجة" (processing)، بل مجرد تأكيد أن العنصر
        يحمل الحد الأدنى من البيانات الصالحة لكي يُستخدم في باقي المشروع.
        """
        if not self.title.strip():
            raise ValueError("ContentItem يجب أن يحتوي على عنوان (title).")
        if not self.url.strip():
            raise ValueError("ContentItem يجب أن يحتوي على رابط (url).")
        if not self.source.strip():
            raise ValueError("ContentItem يجب أن يحتوي على اسم مصدر (source).")
