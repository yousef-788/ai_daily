"""
rss_collector.py
-----------------
أول تطبيق فعلي لعقد BaseCollector: يجمع المحتوى من مصدر RSS/Atom
باستخدام مكتبة feedparser، ويحوّله إلى قائمة من ContentItem الموحّدة.
"""

import logging
from datetime import datetime, timezone
from time import struct_time
from urllib.parse import urlparse

import feedparser

from ai_daily.collectors.base import BaseCollector
from ai_daily.models.content_item import ContentItem
from ai_daily.utils.retry import fetch_url_with_retry

logger = logging.getLogger(__name__)


class RssCollector(BaseCollector):
    """Collector يقرأ عناصر المحتوى من مصدر RSS/Atom واحد.

    Attributes:
        source_name: اسم تعريفي للمصدر (مثال: "TechCrunch").
        feed_url: رابط الـ RSS feed (أو مسار ملف محلي وقت الاختبار).
    """

    def __init__(self, source_name: str, feed_url: str, category: str = "news") -> None:
        self.source_name = source_name
        self.feed_url = feed_url
        self.category = category

    def collect(self) -> list[ContentItem]:
        """يقرأ الـ feed ويحوّل كل عنصر صالح فيه إلى ContentItem.

        أي عنصر ناقص بيانات أساسية (عنوان أو رابط) يتم تجاهله بدل ما
        يوقف كل عملية الجمع، عشان مصدر واحد "وسخ" ميكسرش باقي المصادر.

        Returns:
            list[ContentItem]: عناصر المحتوى الصالحة التي تم جمعها.
        """
        parsed_feed = self._parse_feed()

        # feedparser لا يرفع Exception عند فشل الجلب، بل يسجل الخطأ في bozo_exception
        if parsed_feed.bozo:
            logger.warning(
                "تعذّرت قراءة feed المصدر '%s' بشكل سليم: %s",
                self.source_name,
                parsed_feed.get("bozo_exception"),
            )

        items: list[ContentItem] = []
        for entry in parsed_feed.entries:
            content_item = self._entry_to_content_item(entry)
            if content_item is not None:
                items.append(content_item)

        return items

    def _parse_feed(self) -> feedparser.FeedParserDict:
        """يجلب ويحلّل الـ feed، مع إعادة محاولة تلقائية لو كان رابط HTTP حقيقي.

        لو feed_url مسار ملف محلي (بيُستخدم في الاختبارات)، بنمرره لـ
        feedparser مباشرة زي ما هو، لأن أداة الـ retry مخصصة لطلبات HTTP فقط.
        """
        is_http_url = urlparse(self.feed_url).scheme in ("http", "https")

        if is_http_url:
            response = fetch_url_with_retry(self.feed_url)
            return feedparser.parse(response.content)

        return feedparser.parse(self.feed_url)

    def _entry_to_content_item(self, entry: feedparser.FeedParserDict) -> ContentItem | None:
        """يحوّل عنصر واحد من الـ feed إلى ContentItem، أو None لو ناقص بيانات أساسية."""
        title = entry.get("title", "").strip()
        url = entry.get("link", "").strip()

        if not title or not url:
            logger.warning(
                "تم تجاهل عنصر من المصدر '%s' لنقص بيانات أساسية (عنوان/رابط).",
                self.source_name,
            )
            return None

        # الوصف قد يأتي تحت اسم summary أو description حسب صيغة الـ feed
        content = entry.get("summary", "").strip()

        return ContentItem(
            title=title,
            url=url,
            source=self.source_name,
            content=content,
            published_at=self._parse_published_date(entry.get("published_parsed")),
            category=self.category,
        )

    @staticmethod
    def _parse_published_date(published_parsed: struct_time | None) -> datetime | None:
        """يحوّل تاريخ النشر من صيغة feedparser (struct_time) إلى datetime قياسي."""
        if published_parsed is None:
            return None
        return datetime(*published_parsed[:6], tzinfo=timezone.utc)
