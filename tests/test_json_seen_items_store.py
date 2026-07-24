"""اختبارات JsonSeenItemsStore."""

from ai_daily.storage.json_seen_items_store import JsonSeenItemsStore


def test_new_store_has_nothing_seen(tmp_path):
    """التأكد أن مخزن جديد (ملف غير موجود) يعتبر أي رابط غير مرئي من قبل."""
    store = JsonSeenItemsStore(tmp_path / "seen.json")

    assert store.is_seen("https://example.com/1") is False


def test_mark_seen_persists_across_instances(tmp_path):
    """التأكد أن الروابط المُسجَّلة تُحفظ فعليًا وتُقرأ صح من كائن جديد لاحقًا.

    هذا يحاكي إعادة تشغيل main.py في يوم تالٍ.
    """
    file_path = tmp_path / "seen.json"

    first_run_store = JsonSeenItemsStore(file_path)
    first_run_store.mark_seen(["https://example.com/1", "https://example.com/2"])

    second_run_store = JsonSeenItemsStore(file_path)

    assert second_run_store.is_seen("https://example.com/1") is True
    assert second_run_store.is_seen("https://example.com/2") is True
    assert second_run_store.is_seen("https://example.com/3") is False


def test_corrupted_file_falls_back_to_empty_store(tmp_path):
    """التأكد أن ملف تخزين تالف لا يوقف المشروع، بل يبدأ بذاكرة فاضية."""
    file_path = tmp_path / "seen.json"
    file_path.write_text("this is not valid json {{{", encoding="utf-8")

    store = JsonSeenItemsStore(file_path)

    assert store.is_seen("https://example.com/1") is False
