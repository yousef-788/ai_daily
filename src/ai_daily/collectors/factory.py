"""
factory.py
----------
مسؤول عن تحويل SourceConfig (إعدادات) إلى كائن Collector فعلي جاهز للاستخدام.

الفائدة من فصل هذا المنطق هنا: أي مكان في المشروع يحتاج "يبني" Collector
(main.py الآن، وربما جدولة (scheduler) لاحقًا) يستخدم نفس الدالة، بدل ما
يكرر نفس شرط if/elif في أكتر من مكان.
"""

from ai_daily.collectors.base import BaseCollector
from ai_daily.collectors.rss_collector import RssCollector
from ai_daily.collectors.web_scraper_collector import WebScraperCollector
from ai_daily.collectors.wuzzuf_jobs_collector import WuzzufJobsCollector
from ai_daily.models.source_config import SourceConfig


def build_collector(source: SourceConfig) -> BaseCollector:
    """يبني ويرجّع كائن Collector مناسب لنوع المصدر المُعطى.

    Args:
        source: إعدادات المصدر (اسم، نوع، رابط، ومعلومات إضافية حسب النوع).

    Returns:
        BaseCollector: كائن Collector جاهز لاستدعاء collect() عليه.

    Raises:
        ValueError: لو نوع المصدر غير مدعوم (خط دفاع إضافي، رغم إن
            load_sources() في config.py بالفعل بيتحقق من ده مسبقًا).
    """
    if source.type == "rss":
        return RssCollector(source_name=source.name, feed_url=source.url, category=source.category)

    if source.type == "scraping":
        return WebScraperCollector(
            source_name=source.name,
            url=source.url,
            selectors=source.selectors,
            category=source.category,
        )

    if source.type == "wuzzuf_jobs":
        page_size = int(source.selectors.get("page_size", "50"))
        return WuzzufJobsCollector(
            source_name=source.name,
            search_query=source.url,
            page_size=page_size,
            category=source.category,
        )

    raise ValueError(f"لا يوجد Collector مدعوم لنوع المصدر: '{source.type}'")
