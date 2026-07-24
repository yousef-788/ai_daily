"""اختبارات FilePublisher."""

from datetime import date

from ai_daily.models.content_item import ContentItem
from ai_daily.publishers.file_publisher import FilePublisher


def test_publish_creates_dated_file_with_expected_content(tmp_path):
    """التأكد أن publish() بينشئ ملف بتاريخ اليوم وفيه نص النشرة الصحيح."""
    publisher = FilePublisher(tmp_path)
    items = [
        ContentItem(
            title="Sample News",
            url="https://example.com/1",
            source="TestSource",
            content="Some content",
        )
    ]

    publisher.publish(items)

    expected_file = tmp_path / f"{date.today().isoformat()}.txt"
    assert expected_file.exists()
    assert "Sample News" in expected_file.read_text(encoding="utf-8")


def test_publish_creates_output_dir_if_missing(tmp_path):
    """التأكد أن المجلد بيتنشئ تلقائيًا لو مش موجود أصلًا."""
    nested_dir = tmp_path / "drafts" / "nested"
    publisher = FilePublisher(nested_dir)

    publisher.publish([])

    assert nested_dir.exists()


def test_publish_with_empty_items_still_writes_file(tmp_path):
    """التأكد أن نشرة بدون عناصر جديدة برضه بتتحفظ (برسالة 'لا يوجد محتوى جديد')."""
    publisher = FilePublisher(tmp_path)

    publisher.publish([])

    expected_file = tmp_path / f"{date.today().isoformat()}.txt"
    assert expected_file.exists()
    assert "لا يوجد محتوى جديد اليوم" in expected_file.read_text(encoding="utf-8")
