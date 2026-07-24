"""اختبارات build_collector: التأكد من بناء الـ Collector الصحيح حسب نوع المصدر."""

import pytest

from ai_daily.collectors.factory import build_collector
from ai_daily.collectors.rss_collector import RssCollector
from ai_daily.collectors.web_scraper_collector import WebScraperCollector
from ai_daily.models.source_config import SourceConfig


def test_build_collector_returns_rss_collector_for_rss_type():
    """التأكد أن مصدر type='rss' بيبني RssCollector."""
    source = SourceConfig(name="Test", type="rss", url="https://example.com/feed")

    collector = build_collector(source)

    assert isinstance(collector, RssCollector)


def test_build_collector_returns_web_scraper_for_scraping_type():
    """التأكد أن مصدر type='scraping' بيبني WebScraperCollector بالـ selectors الصحيحة."""
    source = SourceConfig(
        name="Test",
        type="scraping",
        url="https://example.com/news",
        selectors={"item": ".news-item", "title": ".news-title"},
    )

    collector = build_collector(source)

    assert isinstance(collector, WebScraperCollector)


def test_build_collector_raises_for_unsupported_type():
    """التأكد أن نوع غير معروف بيرفع ValueError واضح (خط دفاع إضافي)."""
    # نبني SourceConfig مباشرة (متخطين تحقق load_sources) عشان نختبر factory لوحدها
    source = SourceConfig(name="Test", type="unknown_type", url="https://example.com")

    with pytest.raises(ValueError):
        build_collector(source)
