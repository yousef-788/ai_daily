"""اختبارات TextCleanerProcessor."""

from ai_daily.models.content_item import ContentItem
from ai_daily.processors.text_cleaner import TextCleanerProcessor


def _make_item(content: str) -> ContentItem:
    """دالة مساعدة لإنشاء ContentItem بسرعة لأغراض الاختبار."""
    return ContentItem(
        title="Test title",
        url="https://example.com/1",
        source="TestSource",
        content=content,
    )


def test_strips_html_tags():
    """التأكد أن الـ HTML tags بتتشال ويفضل النص الفعلي بس."""
    processor = TextCleanerProcessor()
    item = _make_item("<p>Hello <b>World</b>!</p>")

    result = processor.process(item)

    assert result.content == "Hello World!"


def test_normalizes_extra_whitespace():
    """التأكد أن المسافات والأسطر الزائدة بتتحول لمسافة واحدة."""
    processor = TextCleanerProcessor()
    item = _make_item("Hello    \n\n   World")

    result = processor.process(item)

    assert result.content == "Hello World"


def test_does_not_mutate_original_item():
    """التأكد أن المعالجة بترجع نسخة جديدة، والعنصر الأصلي يفضل زي ما هو (Immutability)."""
    processor = TextCleanerProcessor()
    original = _make_item("<p>Raw HTML</p>")

    result = processor.process(original)

    assert original.content == "<p>Raw HTML</p>"  # الأصلي لم يتغيّر
    assert result.content == "Raw HTML"
    assert result is not original


def test_other_fields_remain_unchanged():
    """التأكد أن باقي الحقول (عنوان، رابط، مصدر) بتفضل زي ما هي بعد المعالجة."""
    processor = TextCleanerProcessor()
    item = _make_item("<p>Some content</p>")

    result = processor.process(item)

    assert result.title == item.title
    assert result.url == item.url
    assert result.source == item.source
