"""اختبارات WebScraperCollector.

منطق التحليل (_parse_html) منفصل عن الجلب الفعلي (_fetch_html)، فبنختبر
التحليل مباشرة بنص HTML محلي بدون أي اتصال إنترنت حقيقي.
"""

from pathlib import Path

import pytest

from ai_daily.collectors.web_scraper_collector import WebScraperCollector

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_page.html"

SAMPLE_SELECTORS = {
    "item": "article.news-item",
    "title": "h2.news-title a",
    "summary": "p.news-summary",
}


def _make_collector(selectors: dict[str, str] = SAMPLE_SELECTORS) -> WebScraperCollector:
    return WebScraperCollector(
        source_name="SamplePageSource",
        url="https://example.com/news",
        selectors=selectors,
    )


def test_parse_html_returns_only_valid_items():
    """التأكد أن العناصر السليمة فقط تُرجَع، والعنصر الناقص (بدون رابط) يُتجاهل."""
    collector = _make_collector()
    html = FIXTURE_PATH.read_text(encoding="utf-8")

    items = collector._parse_html(html)

    # الملف التجريبي فيه 3 عناصر، واحد ناقص (بدون رابط) لازم يتجاهل
    assert len(items) == 2
    assert all(item.source == "SamplePageSource" for item in items)


def test_parse_html_extracts_fields_correctly():
    """التأكد أن العنوان والملخص اتقرأوا صح من العنصر."""
    collector = _make_collector()
    html = FIXTURE_PATH.read_text(encoding="utf-8")

    items = collector._parse_html(html)
    first_item = items[0]

    assert first_item.title == "OpenAI releases new model"
    assert "new model release" in first_item.content


def test_parse_html_resolves_relative_links_to_absolute():
    """التأكد أن الرابط النسبي (/news/1) بيتحوّل لرابط كامل بالنسبة لرابط الصفحة."""
    collector = _make_collector()
    html = FIXTURE_PATH.read_text(encoding="utf-8")

    items = collector._parse_html(html)

    assert items[0].url == "https://example.com/news/openai-new-model"
    # الرابط اللي كان أصلًا كامل (absolute) يفضل زي ما هو
    assert items[1].url == "https://example.com/news/gemini-update"


def test_missing_required_selector_raises_error_on_init():
    """التأكد أن نقص selector مطلوب (title) بيوقف الإنشاء برسالة خطأ واضحة."""
    with pytest.raises(ValueError):
        _make_collector(selectors={"item": "article.news-item"})
