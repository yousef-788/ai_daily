"""
main.py
-------
نقطة الدخول الرئيسية لتشغيل المشروع.

التدفق الكامل حاليًا: يقرأ المصادر من ملف الإعدادات الخارجي
(config/sources.json)، يبني Collector مناسب لكل مصدر، يجمع المحتوى،
يستبعد أي عنصر سبق جمعه من قبل (منع التكرار)، يمرّر العناصر الجديدة
على سلسلة من الـ Processors (تنظيف النص حاليًا)، ثم يحفظ نشرة اليوم
كملف مسودة جاهز للنشر اليدوي على قناة واتساب.
"""

import logging
from datetime import date
from pathlib import Path

from ai_daily.collectors.factory import build_collector
from ai_daily.config import get_optional_env, load_environment, load_sources
from ai_daily.models.content_item import ContentItem
from ai_daily.processors.ai_summarizer import AISummarizerProcessor
from ai_daily.processors.base import BaseProcessor
from ai_daily.processors.text_cleaner import TextCleanerProcessor
from ai_daily.publishers.base import BasePublisher
from ai_daily.publishers.composite_publisher import CompositePublisher
from ai_daily.publishers.file_publisher import FilePublisher
from ai_daily.publishers.whatsapp_channel_publisher import WhatsAppChannelPublisher
from ai_daily.storage.base import SeenItemsStore
from ai_daily.storage.json_seen_items_store import JsonSeenItemsStore

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_SOURCES_PATH = PROJECT_ROOT / "config" / "sources.json"
DEFAULT_SEEN_ITEMS_PATH = PROJECT_ROOT / "data" / "seen_items.json"
DEFAULT_DRAFTS_DIR = PROJECT_ROOT / "data" / "drafts"
DEFAULT_LOGS_DIR = PROJECT_ROOT / "data" / "logs"

# نستخدم هذه العلامة لتمييز الـ handlers اللي أضافتها configure_logging بالذات،
# عشان نقدر نشيلها ونستبدلها بأمان لو الدالة اتنادت أكتر من مرة في نفس العملية
# (زي وقت تشغيل الاختبارات)، من غير ما نأثر على أي handlers تانية (مثل أدوات pytest).
_LOG_HANDLER_MARKER = "_ai_daily_managed_handler"


def configure_logging(logs_dir: Path) -> None:
    """يضبط الـ logging ليكتب لكل من الشاشة (Console) وملف يومي دائم.

    ملف الـ log بيتسمى بتاريخ اليوم (زي ملفات المسودات بالظبط)، عشان
    لو حصلت مشكلة في أي تشغيلة سابقة، نقدر نرجع لسجلها بسهولة.

    الدالة آمنة عند الاستدعاء أكتر من مرة: بتشيل أي handlers سبق
    وأضافتها هي بالذات قبل ما تضيف الجديدة، بدل ما تتكرر رسائل الـ log.

    Args:
        logs_dir: المجلد الذي ستُحفظ فيه ملفات الـ log اليومية.
    """
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = logs_dir / f"{date.today().isoformat()}.log"

    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        if getattr(handler, _LOG_HANDLER_MARKER, False):
            root_logger.removeHandler(handler)

    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    setattr(file_handler, _LOG_HANDLER_MARKER, True)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    setattr(console_handler, _LOG_HANDLER_MARKER, True)

    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


# القيمة الافتراضية لسقف استدعاءات AI في التشغيلة الواحدة، لو المستخدم
# ماحددش قيمة مخصصة بنفسه في .env. رقم متحفّظ يناسب تشغيلة يومية عادية.
DEFAULT_AI_MAX_CALLS_PER_RUN = 30

# الأقسام اللي هيتفعّل عليها التلخيص بالـ AI افتراضيًا. الأخبار (news)
# بس، لأن الأدوات والوظائف أصلًا مختصرة ومش محتاجة تلخيص إضافي.
DEFAULT_AI_SUMMARY_CATEGORIES = "news"


def build_processors() -> list[BaseProcessor]:
    """يبني سلسلة الـ Processors التي سيتم تطبيقها على كل عنصر.

    التنظيف (TextCleanerProcessor) بيشتغل دايمًا. أما التلخيص بالـ AI
    فبيتفعّل بس لو ANTHROPIC_API_KEY متاح في البيئة، عشان المشروع
    يفضل شغال حتى من غير مفتاح API (بمحتوى منظّف بس بدون تلخيص).

    Returns:
        list[BaseProcessor]: سلسلة الـ Processors مرتبة بترتيب التنفيذ.
    """
    processors: list[BaseProcessor] = [TextCleanerProcessor()]

    api_key = get_optional_env("ANTHROPIC_API_KEY")
    if api_key:
        from anthropic import Anthropic  # استيراد محلي: نتجنب الاعتماد الإجباري لو المفتاح غير مستخدم

        max_calls = int(
            get_optional_env("AI_MAX_SUMMARIES_PER_RUN", str(DEFAULT_AI_MAX_CALLS_PER_RUN))
        )
        categories_raw = get_optional_env(
            "AI_SUMMARY_CATEGORIES", DEFAULT_AI_SUMMARY_CATEGORIES
        )
        target_categories = {c.strip() for c in categories_raw.split(",") if c.strip()}

        processors.append(
            AISummarizerProcessor(
                client=Anthropic(api_key=api_key),
                max_calls_per_run=max_calls,
                target_categories=target_categories,
            )
        )
        logger.info(
            "تلخيص المحتوى بالـ AI مفعّل (الأقسام: %s، الحد الأقصى: %d استدعاء لكل تشغيلة).",
            sorted(target_categories),
            max_calls,
        )
    else:
        logger.info(
            "ANTHROPIC_API_KEY غير موجود، سيتم تخطي خطوة التلخيص بالـ AI "
            "(سيُنشر المحتوى بعد التنظيف فقط)."
        )

    return processors


def collect_all(sources_path: Path, store: SeenItemsStore) -> list[ContentItem]:
    """يجمع المحتوى الجديد فقط (غير المكرر) من كل المصادر المذكورة في ملف الإعدادات.

    لو مصدر واحد فشل (مثال: الرابط غير متاح)، يتم تسجيل الخطأ والاستمرار
    في باقي المصادر، بدل ما فشل مصدر واحد يوقف عملية الجمع بالكامل.

    Args:
        sources_path: مسار ملف JSON الذي يحتوي على قائمة المصادر.
        store: وسيلة تتبع العناصر التي سبق رؤيتها، لاستبعاد المكرر منها.

    Returns:
        list[ContentItem]: عناصر المحتوى الجديدة فقط (التي لم تُر من قبل).
    """
    sources = load_sources(sources_path)

    new_items: list[ContentItem] = []
    for source in sources:
        collector = build_collector(source)
        try:
            collected = collector.collect()
        except Exception:  # noqa: BLE001 - نتعمد الإمساك بأي خطأ لعزل المصادر عن بعضها
            logger.exception("فشل جمع المحتوى من المصدر '%s'.", source.name)
            continue

        fresh_items = [item for item in collected if not store.is_seen(item.url)]
        logger.info(
            "المصدر '%s': جُمع %d عنصر، منهم %d جديد (بعد استبعاد المكرر).",
            source.name,
            len(collected),
            len(fresh_items),
        )
        new_items.extend(fresh_items)

    # نسجّل العناصر الجديدة كـ "تمت رؤيتها" فقط بعد نجاح كل عملية الجمع،
    # عشان لو حصل خطأ غير متوقع في نص العملية، ميتسجلش عنصر جمعناه فعلاً كمكرر بالغلط.
    store.mark_seen([item.url for item in new_items])

    return new_items


def process_items(items: list[ContentItem], processors: list[BaseProcessor]) -> list[ContentItem]:
    """يمرّر كل عنصر على سلسلة الـ Processors بالترتيب، ويرجّع النتيجة النهائية.

    كل Processor بياخد نتيجة اللي قبله، فترتيب القائمة processors مهم.

    Args:
        items: عناصر المحتوى المطلوب معالجتها.
        processors: قائمة الـ Processors مرتبة بترتيب التنفيذ.

    Returns:
        list[ContentItem]: العناصر بعد مرورها على كل خطوات المعالجة.
    """
    processed_items: list[ContentItem] = []
    for item in items:
        for processor in processors:
            item = processor.process(item)
        processed_items.append(item)

    return processed_items


def build_publishers() -> BasePublisher:
    """يبني الـ Publisher (أو مجموعة Publishers) المطلوب تشغيلهم في هذه التشغيلة.

    FilePublisher (نسخة محلية في data/drafts) بيشتغل دايمًا كنسخة
    احتياطية مضمونة. WhatsAppChannelPublisher بيتفعّل بس لو إعدادات
    WAHA الثلاثة (BASE_URL, API_KEY, CHANNEL_ID) متوفرة كلها في البيئة.

    Returns:
        BasePublisher: كائن Publisher واحد (ممكن يكون CompositePublisher
            بيلف أكتر من Publisher جوّاه).
    """
    publishers: list[BasePublisher] = [FilePublisher(DEFAULT_DRAFTS_DIR)]

    waha_base_url = get_optional_env("WAHA_BASE_URL")
    waha_api_key = get_optional_env("WAHA_API_KEY")
    whatsapp_channel_id = get_optional_env("WHATSAPP_CHANNEL_ID")

    if waha_base_url and waha_api_key and whatsapp_channel_id:
        publishers.append(
            WhatsAppChannelPublisher(
                base_url=waha_base_url, api_key=waha_api_key, channel_id=whatsapp_channel_id
            )
        )
        logger.info("النشر الفعلي في قناة واتساب مفعّل.")
    else:
        logger.info(
            "إعدادات WAHA غير مكتملة، سيتم الاكتفاء بحفظ نسخة محلية من النشرة "
            "(WAHA_BASE_URL / WAHA_API_KEY / WHATSAPP_CHANNEL_ID)."
        )

    return CompositePublisher(publishers)


def main() -> None:
    """نقطة تشغيل المشروع: تجمع المحتوى الجديد، تعالجه، وتحفظ مسودة النشر."""
    configure_logging(DEFAULT_LOGS_DIR)
    load_environment()  # تحميل متغيرات .env (يُستخدم لقراءة ANTHROPIC_API_KEY إن وُجد)

    store = JsonSeenItemsStore(DEFAULT_SEEN_ITEMS_PATH)
    raw_items = collect_all(DEFAULT_SOURCES_PATH, store)
    items = process_items(raw_items, build_processors())

    publisher: BasePublisher = build_publishers()
    publisher.publish(items)

    print(f"\nتم جمع ومعالجة {len(items)} عنصر جديد، وتم حفظ مسودة النشرة في {DEFAULT_DRAFTS_DIR}")


if __name__ == "__main__":
    main()
