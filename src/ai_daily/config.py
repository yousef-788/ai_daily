"""
config.py
---------
هذا الملف مسؤول عن تجميع إعدادات المشروع: قراءة ملف المصادر الخارجي
(sources.json)، وقراءة متغيرات البيئة الحساسة (API keys وغيرها) من
ملف .env بدل ما تكون مكتوبة (hardcoded) داخل الكود.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

from ai_daily.models.source_config import SourceConfig

# النوع "type" المسموح بها حاليًا في ملف المصادر.
# قائمة صريحة بدل قبول أي قيمة، عشان نكتشف الأخطاء الإملائية بدري.
SUPPORTED_SOURCE_TYPES = {"rss", "scraping", "wuzzuf_jobs"}


def load_sources(config_path: str | Path) -> list[SourceConfig]:
    """يقرأ ملف المصادر الخارجي (JSON) ويحوّله إلى قائمة SourceConfig.

    Args:
        config_path: مسار ملف JSON الذي يحتوي على قائمة المصادر.

    Returns:
        list[SourceConfig]: قائمة إعدادات المصادر الصالحة.

    Raises:
        FileNotFoundError: لو الملف مش موجود أصلًا.
        ValueError: لو محتوى الملف مش بالشكل المتوقع، أو فيه نوع مصدر غير مدعوم.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"ملف المصادر غير موجود: {path}")

    raw_data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(raw_data, list):
        raise ValueError("ملف المصادر يجب أن يحتوي على قائمة (JSON array) في المستوى الأعلى.")

    sources: list[SourceConfig] = []
    for entry in raw_data:
        source = SourceConfig(
            name=entry["name"],
            type=entry["type"],
            url=entry["url"],
            selectors=entry.get("selectors", {}),
            category=entry.get("category", "news"),
        )
        if source.type not in SUPPORTED_SOURCE_TYPES:
            raise ValueError(
                f"نوع مصدر غير مدعوم: '{source.type}' للمصدر '{source.name}'. "
                f"الأنواع المدعومة: {SUPPORTED_SOURCE_TYPES}"
            )
        sources.append(source)

    return sources


def load_environment(env_path: str | Path | None = None) -> None:
    """يحمّل متغيرات البيئة من ملف .env إلى os.environ.

    لو متغير موجود بالفعل في بيئة التشغيل الحقيقية (مثال: مضبوط من
    السيرفر مباشرة)، بيفضل هو الأولوية ومبيتغطاش بقيمة ملف .env
    (override=False)، عشان بيئات الإنتاج تقدر تتحكم في قيمها بأمان.

    Args:
        env_path: مسار ملف .env. لو None، بيدوّر تلقائيًا بدءًا من
            المجلد الحالي وصعودًا (سلوك python-dotenv الافتراضي).
    """
    load_dotenv(dotenv_path=env_path, override=False)


def get_required_env(name: str) -> str:
    """يرجّع قيمة متغير بيئة مطلوب، أو يرفع خطأ واضح لو مش موجود.

    Args:
        name: اسم متغير البيئة (مثال: "ANTHROPIC_API_KEY").

    Returns:
        str: قيمة المتغير.

    Raises:
        ValueError: لو المتغير غير موجود أو فاضي.
    """
    value = os.environ.get(name)
    if not value:
        raise ValueError(
            f"متغير البيئة المطلوب '{name}' غير موجود. "
            f"تأكد من ضبطه في ملف .env أو في بيئة التشغيل."
        )
    return value


def get_optional_env(name: str, default: str | None = None) -> str | None:
    """يرجّع قيمة متغير بيئة اختياري، أو القيمة الافتراضية لو مش موجود.

    Args:
        name: اسم متغير البيئة.
        default: القيمة الافتراضية لو المتغير غير موجود.

    Returns:
        str | None: قيمة المتغير أو القيمة الافتراضية.
    """
    return os.environ.get(name, default)
