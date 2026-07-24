"""
web_scraper_collector.py
--------------------------
تطبيق ثانٍ لعقد BaseCollector: يجمع المحتوى من صفحة HTML عادية (مالهاش
RSS feed)، باستخدام CSS selectors قابلة للتخصيص لكل مصدر.

بعكس RssCollector اللي بيعتمد على صيغة RSS الموحّدة، هنا بنحتاج "نوصف"
للـ Collector شكل الصفحة (مكان كل خبر، عنوانه، رابطه، ملخصه) لأنه
بيختلف من موقع لموقع.
"""

import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import Tag

from ai_daily.collectors.base import BaseCollector
from ai_daily.models.content_item import ContentItem
from ai_daily.utils.retry import fetch_url_with_retry

logger = logging.getLogger(__name__)


class WebScraperCollector(BaseCollector):
    """Collector عام يجمع المحتوى من صفحة HTML باستخدام CSS selectors.

    Attributes:
        source_name: اسم تعريفي للمصدر.
        url: رابط الصفحة التي تحتوي على قائمة الأخبار.
        selectors: قاموس CSS selectors بالمفاتيح التالية:
            - "item" (مطلوب): selector للعنصر الذي يمثل خبرًا واحدًا.
            - "title" (مطلوب): selector للعنوان داخل كل عنصر.
            - "link" (اختياري): selector لرابط الخبر. لو غير موجود،
              يُفترض أن عنصر العنوان نفسه هو رابط (<a>).
            - "summary" (اختياري): selector لملخص/وصف الخبر.
    """

    REQUIRED_SELECTOR_KEYS = ("item", "title")

    def __init__(
        self, source_name: str, url: str, selectors: dict[str, str], category: str = "news"
    ) -> None:
        missing_keys = [key for key in self.REQUIRED_SELECTOR_KEYS if key not in selectors]
        if missing_keys:
            raise ValueError(
                f"المصدر '{source_name}' ناقص CSS selectors مطلوبة: {missing_keys}"
            )

        self.source_name = source_name
        self.url = url
        self.selectors = selectors
        self.category = category

    def collect(self) -> list[ContentItem]:
        """يجلب الصفحة ويحوّل كل عنصر مطابق فيها إلى ContentItem."""
        html = self._fetch_html()
        return self._parse_html(html)

    def _fetch_html(self) -> str:
        """يجلب محتوى الصفحة HTML عبر HTTP، مع إعادة محاولة تلقائية عند فشل مؤقت."""
        response = fetch_url_with_retry(self.url)
        return response.text

    def _parse_html(self, html: str) -> list[ContentItem]:
        """يحلّل نص HTML ويستخرج منه عناصر المحتوى الصالحة.

        منطق التحليل منفصل عن الجلب (_fetch_html) عمدًا، عشان نقدر
        نختبره بنص HTML جاهز بدون أي اتصال شبكة فعلي.
        """
        soup = BeautifulSoup(html, "html.parser")

        items: list[ContentItem] = []
        for element in soup.select(self.selectors["item"]):
            content_item = self._element_to_content_item(element)
            if content_item is not None:
                items.append(content_item)

        return items

    def _element_to_content_item(self, element: Tag) -> ContentItem | None:
        """يحوّل عنصر HTML واحد (خبر) إلى ContentItem، أو None لو ناقص بيانات أساسية."""
        title_element = element.select_one(self.selectors["title"])
        if title_element is None:
            logger.warning(
                "تم تجاهل عنصر من المصدر '%s': لا يوجد عنوان مطابق للـ selector.",
                self.source_name,
            )
            return None
        title = title_element.get_text(strip=True)

        link_selector = self.selectors.get("link", self.selectors["title"])
        link_element = element.select_one(link_selector)
        href = link_element.get("href") if link_element else None
        if not title or not href:
            logger.warning(
                "تم تجاهل عنصر من المصدر '%s': نقص بيانات أساسية (عنوان/رابط).",
                self.source_name,
            )
            return None

        # تحويل الروابط النسبية (مثال: "/news/1") لروابط كاملة بالنسبة لرابط الصفحة الأصلي.
        absolute_url = urljoin(self.url, href)

        summary = ""
        summary_selector = self.selectors.get("summary")
        if summary_selector:
            summary_element = element.select_one(summary_selector)
            if summary_element:
                summary = summary_element.get_text(strip=True)

        return ContentItem(
            title=title, url=absolute_url, source=self.source_name, content=summary,
            category=self.category,
        )
