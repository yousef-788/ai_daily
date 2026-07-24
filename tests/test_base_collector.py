"""اختبارات للتأكد من سلوك BaseCollector كعقد (Interface)."""

import pytest

from ai_daily.collectors.base import BaseCollector
from ai_daily.models.content_item import ContentItem


def test_cannot_instantiate_base_collector_directly():
    """التأكد أن BaseCollector تجريدي ولا يمكن إنشاء كائن منه مباشرة."""
    with pytest.raises(TypeError):
        BaseCollector()  # type: ignore[abstract]


def test_subclass_must_implement_collect():
    """التأكد أن أي كلاس وارث لازم يطبّق collect() وإلا فشل الإنشاء."""

    class IncompleteCollector(BaseCollector):
        source_name = "Incomplete"
        # لم يتم تطبيق collect() عمدًا

    with pytest.raises(TypeError):
        IncompleteCollector()  # type: ignore[abstract]


def test_valid_subclass_works_correctly():
    """التأكد أن كلاس ملتزم بالعقد بالكامل يعمل بشكل صحيح."""

    class DummyCollector(BaseCollector):
        source_name = "Dummy"

        def collect(self) -> list[ContentItem]:
            return [
                ContentItem(
                    title="Dummy news",
                    url="https://example.com/1",
                    source=self.source_name,
                    content="Dummy content",
                )
            ]

    collector = DummyCollector()
    result = collector.collect()

    assert len(result) == 1
    assert result[0].source == "Dummy"
