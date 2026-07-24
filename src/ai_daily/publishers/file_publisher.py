"""
file_publisher.py
------------------
أول تطبيق فعلي لعقد BasePublisher: يحفظ نشرة اليوم كملف نصي (Draft)
في مجلد محدد، بدل الإرسال الفعلي لواتساب (لسه مش متاح في هذه المرحلة).
"""

import logging
from datetime import date
from pathlib import Path

from ai_daily.models.content_item import ContentItem
from ai_daily.publishers.base import BasePublisher
from ai_daily.publishers.formatting import format_digest

logger = logging.getLogger(__name__)


class FilePublisher(BasePublisher):
    """يحفظ نشرة اليوم كملف نصي داخل مجلد المسودات.

    اسم الملف بيتحدد بتاريخ اليوم (مثال: 2026-07-22.txt)، عشان لو
    شغّلنا المشروع أكتر من مرة في نفس اليوم، الملف يتحدّث بدل ما
    يتكرر بأسماء مختلفة.

    Attributes:
        output_dir: المجلد اللي هتتخزن فيه ملفات المسودات.
    """

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)

    def publish(self, items: list[ContentItem]) -> None:
        """يبني نص النشرة من العناصر ويحفظه في ملف مسودة بتاريخ اليوم."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        digest_text = format_digest(items, digest_date=date.today())
        file_path = self.output_dir / f"{date.today().isoformat()}.txt"
        file_path.write_text(digest_text, encoding="utf-8")

        logger.info("تم حفظ مسودة النشرة في: %s", file_path)
