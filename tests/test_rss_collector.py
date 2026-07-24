"""اختبارات RssCollector باستخدام ملف RSS محلي (بدون اتصال إنترنت فعلي)."""

from pathlib import Path

from ai_daily.collectors.rss_collector import RssCollector

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_feed.xml"


def test_collect_returns_only_valid_items():
    """التأكد أن العناصر السليمة فقط تُرجَع، والعنصر الناقص (بدون رابط) يُتجاهل."""
    collector = RssCollector(source_name="SampleFeed", feed_url=str(FIXTURE_PATH))

    items = collector.collect()

    # الملف التجريبي فيه 3 عناصر، واحد منهم ناقص (بدون رابط) ولازم يتجاهل
    assert len(items) == 2
    assert all(item.source == "SampleFeed" for item in items)


def test_collected_item_fields_are_mapped_correctly():
    """التأكد أن الحقول (عنوان، رابط، محتوى، تاريخ) اتنقلت صح من الـ feed."""
    collector = RssCollector(source_name="SampleFeed", feed_url=str(FIXTURE_PATH))

    items = collector.collect()
    first_item = items[0]

    assert first_item.title == "OpenAI releases new model"
    assert first_item.url == "https://example.com/news/openai-new-model"
    assert "new model release" in first_item.content
    assert first_item.published_at is not None
    assert first_item.published_at.year == 2026
