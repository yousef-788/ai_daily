"""اختبارات format_digest."""

from datetime import date

from ai_daily.models.content_item import ContentItem
from ai_daily.publishers.formatting import format_digest


def _make_item(title: str, content: str, category: str = "news") -> ContentItem:
    return ContentItem(
        title=title,
        url=f"https://example.com/{title}",
        source="TestSource",
        content=content,
        category=category,
    )


def test_format_digest_with_no_items():
    """التأكد أن قائمة فاضية بترجع رسالة واضحة بدل نص فاضي أو خطأ."""
    result = format_digest([], digest_date=date(2026, 7, 22))

    assert "لا يوجد محتوى جديد اليوم" in result
    assert "2026-07-22" in result


def test_format_digest_includes_all_items():
    """التأكد أن كل عنصر بيظهر في النشرة بعنوانه ورابطه."""
    items = [_make_item("Title One", "Content one"), _make_item("Title Two", "Content two")]

    result = format_digest(items, digest_date=date(2026, 7, 22))

    assert "Title One" in result
    assert "Title Two" in result
    assert "https://example.com/Title One" in result
    assert "https://example.com/Title Two" in result


def test_format_digest_truncates_long_content():
    """التأكد أن محتوى طويل جدًا بيتقص لطول معقول في النشرة."""
    long_content = "x" * 500
    items = [_make_item("Long Item", long_content)]

    result = format_digest(items, digest_date=date(2026, 7, 22))

    assert "x" * 500 not in result  # النص الكامل ميظهرش
    assert "..." in result  # علامة القص موجودة


def test_format_digest_groups_items_into_sections_by_category():
    """التأكد أن العناصر بتتقسم لأقسام منفصلة حسب category بعناوين واضحة."""
    items = [
        _make_item("News Item", "news content", category="news"),
        _make_item("Tool Item", "tool content", category="tools"),
        _make_item("Job Item", "job content", category="jobs"),
    ]

    result = format_digest(items, digest_date=date(2026, 7, 22))

    assert "أخبار الذكاء الاصطناعي" in result
    assert "أدوات وتحديثات جديدة" in result
    assert "وظائف الذكاء الاصطناعي" in result
    # التأكد أن قسم الأخبار ظهر قبل قسم الأدوات قبل قسم الوظائف (الترتيب المحدد مسبقًا)
    news_position = result.index("أخبار الذكاء الاصطناعي")
    tools_position = result.index("أدوات وتحديثات جديدة")
    jobs_position = result.index("وظائف الذكاء الاصطناعي")
    assert news_position < tools_position < jobs_position


def test_format_digest_omits_empty_sections():
    """التأكد أن قسم بدون أي عناصر مايظهرش خالص في النشرة."""
    items = [_make_item("Only News", "content", category="news")]

    result = format_digest(items, digest_date=date(2026, 7, 22))

    assert "أدوات وتحديثات جديدة" not in result
    assert "وظائف الذكاء الاصطناعي" not in result


def test_format_digest_handles_unknown_category_gracefully():
    """التأكد أن category غير معروف بيروح لقسم 'أخرى' بدل ما يسبب خطأ أو يختفي."""
    items = [_make_item("Mystery Item", "content", category="something_unexpected")]

    result = format_digest(items, digest_date=date(2026, 7, 22))

    assert "Mystery Item" in result
    assert "أخرى" in result
