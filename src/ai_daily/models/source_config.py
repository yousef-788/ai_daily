"""
source_config.py
-----------------
يمثل هذا الملف "إعدادات مصدر واحد" كما تُقرأ من ملف المصادر الخارجي
(مثال: config/sources.json). منفصل عن ContentItem لأن هذا يصف "من أين
نجمع"، بينما ContentItem يصف "ماذا جمعنا".
"""

from dataclasses import dataclass, field


@dataclass
class SourceConfig:
    """يمثل إعدادات مصدر واحد لجمع المحتوى.

    Attributes:
        name: اسم تعريفي للمصدر (يُستخدم كـ source_name في الـ ContentItem).
        type: نوع المصدر (مثال: "rss"، "scraping"). يحدد أي Collector سيتم استخدامه.
        url: رابط المصدر (أو مسار ملف محلي وقت الاختبار). لمصادر
            type="wuzzuf_jobs"، هذا الحقل يُستخدم كنص بحث (مثال:
            "Artificial Intelligence") بدل رابط كامل، لأن المصدر ده
            بيبني الطلب لـ Wuzzuf API بنفسه.
        selectors: CSS selectors مطلوبة فقط لمصادر type="scraping"، لوصف
            شكل الصفحة (مكان كل خبر، عنوانه، رابطه...). فاضية لأي نوع تاني.
        category: تصنيف هذا المصدر ضمن أقسام النشرة (news/tools/jobs).
            يُطبَّق تلقائيًا على كل عنصر محتوى يُجمع من هذا المصدر.
    """

    name: str
    type: str
    url: str
    selectors: dict[str, str] = field(default_factory=dict)
    category: str = "news"
