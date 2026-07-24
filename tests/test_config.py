"""اختبارات load_sources في config.py."""

import json

import pytest

from ai_daily.config import load_sources


def test_load_valid_sources_file(tmp_path):
    """التأكد أن ملف مصادر سليم يتم تحويله لقائمة SourceConfig صحيحة."""
    sources_file = tmp_path / "sources.json"
    sources_file.write_text(
        json.dumps([{"name": "TestSource", "type": "rss", "url": "https://example.com/feed"}]),
        encoding="utf-8",
    )

    sources = load_sources(sources_file)

    assert len(sources) == 1
    assert sources[0].name == "TestSource"
    assert sources[0].type == "rss"


def test_missing_file_raises_error(tmp_path):
    """التأكد أن مسار غير موجود يرفع FileNotFoundError واضح."""
    missing_path = tmp_path / "does_not_exist.json"

    with pytest.raises(FileNotFoundError):
        load_sources(missing_path)


def test_unsupported_source_type_raises_error(tmp_path):
    """التأكد أن نوع مصدر غير مدعوم يرفع ValueError واضح بدل تجاهله بصمت."""
    sources_file = tmp_path / "sources.json"
    sources_file.write_text(
        json.dumps([{"name": "BadSource", "type": "twitter", "url": "https://example.com"}]),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_sources(sources_file)
