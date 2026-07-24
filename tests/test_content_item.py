"""اختبارات بسيطة للتأكد من سلامة ContentItem."""

import pytest

from ai_daily.models.content_item import ContentItem


def test_create_valid_content_item():
    """التأكد أن إنشاء عنصر ببيانات صحيحة يعمل بدون أخطاء."""
    item = ContentItem(
        title="OpenAI releases new model",
        url="https://example.com/news/1",
        source="TechCrunch",
        content="Some raw article text...",
    )

    assert item.title == "OpenAI releases new model"
    assert item.collected_at is not None  # يُملأ تلقائيًا


def test_missing_title_raises_error():
    """التأكد أن غياب العنوان يوقف إنشاء الكائن برسالة خطأ واضحة."""
    with pytest.raises(ValueError):
        ContentItem(
            title="   ",
            url="https://example.com/news/1",
            source="TechCrunch",
            content="Some text",
        )
