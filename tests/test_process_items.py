"""اختبارات process_items في main.py."""

from ai_daily.main import process_items
from ai_daily.models.content_item import ContentItem
from ai_daily.processors.base import BaseProcessor


class _UppercaseTitleProcessor(BaseProcessor):
    """Processor تجريبي بسيط لأغراض الاختبار فقط: يحوّل العنوان لحروف كبيرة."""

    def process(self, item: ContentItem) -> ContentItem:
        from dataclasses import replace

        return replace(item, title=item.title.upper())


def test_process_items_applies_processors_in_order():
    """التأكد أن كل Processor في السلسلة بيتنفذ بالترتيب على كل عنصر."""
    items = [
        ContentItem(title="hello", url="https://example.com/1", source="Test", content="<p>x</p>")
    ]
    processors: list[BaseProcessor] = [_UppercaseTitleProcessor()]

    result = process_items(items, processors)

    assert result[0].title == "HELLO"


def test_process_items_with_empty_processor_list_returns_items_unchanged():
    """التأكد أن قائمة Processors فاضية بترجع العناصر زي ما هي بدون أي تعديل."""
    items = [
        ContentItem(title="hello", url="https://example.com/1", source="Test", content="raw")
    ]

    result = process_items(items, processors=[])

    assert result == items
