"""
formatting.py
-------------
مسؤول عن تحويل قائمة ContentItem إلى نص نشرة واحدة منسّق، مقسّمة لأقسام
حسب نوع المحتوى (أخبار / أدوات / وظائف...)، جاهزة للنشر في قناة واتساب.
هذا المنطق منفصل عن أي Publisher معيّن، عشان أي تطبيق جديد (FilePublisher
الآن، WhatsAppPublisher لاحقًا) يستخدم نفس التنسيق بدل ما يكرره.
"""

from collections import defaultdict
from datetime import date

from ai_daily.models.content_item import ContentItem

# أقصى عدد حروف من محتوى الخبر نعرضهم في النشرة، لإبقاء الرسالة مختصرة وسهلة القراءة.
CONTENT_EXCERPT_LENGTH = 200

# ترتيب وعناوين الأقسام المعروفة. أي category جديد مش موجود هنا هيظهر
# في قسم "أخرى" في آخر النشرة تلقائيًا، بدل ما يختفي أو يسبب خطأ.
CATEGORY_SECTIONS: dict[str, str] = {
    "news": "📰 أخبار الذكاء الاصطناعي",
    "tools": "🛠️ أدوات وتحديثات جديدة",
    "jobs": "💼 وظائف الذكاء الاصطناعي في مصر",
}
FALLBACK_CATEGORY_LABEL = "📌 أخرى"


def format_digest(items: list[ContentItem], digest_date: date | None = None) -> str:
    """يبني نص نشرة "AI Daily" اليومية مقسّمة لأقسام من قائمة عناصر المحتوى.

    Args:
        items: عناصر المحتوى الجديدة (بعد الجمع ومنع التكرار والمعالجة).
        digest_date: تاريخ النشرة. الافتراضي: تاريخ اليوم.

    Returns:
        str: نص النشرة الكامل مقسّمًا لأقسام، جاهز للنسخ أو الإرسال.
    """
    digest_date = digest_date or date.today()
    header = f"🗞️ AI Daily — {digest_date.isoformat()}"

    if not items:
        return f"{header}\n\nلا يوجد محتوى جديد اليوم."

    items_by_category = _group_by_category(items)

    sections = [header]
    for category, section_title in CATEGORY_SECTIONS.items():
        category_items = items_by_category.pop(category, [])
        if category_items:
            sections.append(_format_section(section_title, category_items))

    # أي categories متبقية (مش معرّفة في CATEGORY_SECTIONS) بتتجمع في قسم "أخرى"
    remaining_items = [item for items_list in items_by_category.values() for item in items_list]
    if remaining_items:
        sections.append(_format_section(FALLBACK_CATEGORY_LABEL, remaining_items))

    return "\n\n".join(sections).strip()


def _group_by_category(items: list[ContentItem]) -> dict[str, list[ContentItem]]:
    """يجمّع العناصر في قاموس حسب category، مع الحفاظ على ترتيب ظهورها الأصلي."""
    grouped: dict[str, list[ContentItem]] = defaultdict(list)
    for item in items:
        grouped[item.category].append(item)
    return grouped


def _format_section(section_title: str, items: list[ContentItem]) -> str:
    """يبني نص قسم واحد من النشرة (عنوان القسم + العناصر مرقّمة داخله)."""
    lines = [section_title, ""]
    for index, item in enumerate(items, start=1):
        excerpt = item.content[:CONTENT_EXCERPT_LENGTH].strip()
        if len(item.content) > CONTENT_EXCERPT_LENGTH:
            excerpt += "..."

        lines.append(f"{index}. *{item.title}* ({item.source})\n{excerpt}\n{item.url}\n")

    return "\n".join(lines).strip()
