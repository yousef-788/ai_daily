"""
text_cleaner.py
----------------
أول تطبيق فعلي لعقد BaseProcessor: بينظّف حقل content من أي HTML tags
ومسافات/أسطر زائدة، تمهيدًا لأي معالجة لاحقة (تلخيص AI مثلًا).
"""

import re
from dataclasses import replace
from html.parser import HTMLParser

from ai_daily.models.content_item import ContentItem
from ai_daily.processors.base import BaseProcessor


class _HtmlTextExtractor(HTMLParser):
    """أداة داخلية بسيطة تستخرج النص الخام فقط من محتوى HTML.

    نستخدم HTMLParser (من المكتبة القياسية) بدل Regex، لأنه بيفهم
    بنية الـ HTML الفعلية (tags متداخلة، إلخ) بدل ما يحاول "يخمّن"
    شكلها بنمط نصي بسيط.
    """

    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        self._chunks.append(data)

    def get_text(self) -> str:
        return "".join(self._chunks)


def _strip_html_tags(raw_html: str) -> str:
    """يرجّع النص الخام فقط من نص يحتمل احتواءه على HTML tags."""
    extractor = _HtmlTextExtractor()
    extractor.feed(raw_html)
    return extractor.get_text()


def _normalize_whitespace(text: str) -> str:
    """يستبدل أي تتابع من المسافات/الأسطر الفارغة بمسافة واحدة، ويشيل الأطراف."""
    return re.sub(r"\s+", " ", text).strip()


class TextCleanerProcessor(BaseProcessor):
    """يعالج ContentItem بتنظيف حقل content من HTML والمسافات الزائدة."""

    def process(self, item: ContentItem) -> ContentItem:
        """يرجّع نسخة جديدة من العنصر بحقل content منظّف.

        باقي الحقول (العنوان، الرابط، المصدر...) بتفضل زي ما هي، لأن
        هذا الـ Processor مسؤوليته الوحيدة هي تنظيف النص.
        """
        cleaned_content = _normalize_whitespace(_strip_html_tags(item.content))
        return replace(item, content=cleaned_content)
