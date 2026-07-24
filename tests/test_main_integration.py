"""اختبار تكاملي (Integration) للتأكد أن main.collect_all يربط كل الأجزاء صح."""

import json
from pathlib import Path

from ai_daily.main import collect_all
from ai_daily.storage.json_seen_items_store import JsonSeenItemsStore

FIXTURE_FEED_PATH = Path(__file__).parent / "fixtures" / "sample_feed.xml"


def _write_sources_file(tmp_path: Path) -> Path:
    """دالة مساعدة: تنشئ ملف مصادر تجريبي يشاور على fixture RSS المحلي."""
    sources_file = tmp_path / "sources.json"
    sources_file.write_text(
        json.dumps(
            [{"name": "IntegrationTestSource", "type": "rss", "url": str(FIXTURE_FEED_PATH)}]
        ),
        encoding="utf-8",
    )
    return sources_file


def test_collect_all_wires_config_factory_and_collector_together(tmp_path):
    """يتأكد أن collect_all بيقرأ الإعدادات، يبني الـ Collector الصحيح،
    ويرجّع عناصر ContentItem سليمة من مصدر واحد.
    """
    sources_file = _write_sources_file(tmp_path)
    store = JsonSeenItemsStore(tmp_path / "seen.json")

    items = collect_all(sources_file, store)

    # ملف الـ fixture فيه 3 عناصر، واحد ناقص (بدون رابط) لازم يتجاهل
    assert len(items) == 2
    assert all(item.source == "IntegrationTestSource" for item in items)


def test_second_run_does_not_return_already_seen_items(tmp_path):
    """يحاكي تشغيل main.py مرتين على نفس المصادر: التشغيلة التانية
    لازم ترجّع صفر عناصر جديدة، لأن كل حاجة اتجمعت خلال التشغيلة الأولى.
    """
    sources_file = _write_sources_file(tmp_path)
    store = JsonSeenItemsStore(tmp_path / "seen.json")

    first_run_items = collect_all(sources_file, store)
    second_run_items = collect_all(sources_file, store)

    assert len(first_run_items) == 2
    assert len(second_run_items) == 0

