"""
json_seen_items_store.py
-------------------------
تطبيق بسيط لعقد SeenItemsStore، بيحفظ روابط العناصر التي تمت رؤيتها
في ملف JSON محلي. مناسب لمرحلة الـ MVP الحالية (تشغيل دفعي مرة يوميًا).
"""

import json
import logging
from pathlib import Path

from ai_daily.storage.base import SeenItemsStore

logger = logging.getLogger(__name__)


class JsonSeenItemsStore(SeenItemsStore):
    """يحفظ ويسترجع الروابط التي سبق رؤيتها من/إلى ملف JSON.

    Attributes:
        file_path: مسار ملف JSON المستخدم للتخزين.
    """

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)
        self._seen_urls: set[str] = self._load()

    def is_seen(self, url: str) -> bool:
        """يتحقق هل هذا الرابط موجود بالفعل في الملف المحفوظ."""
        return url in self._seen_urls

    def mark_seen(self, urls: list[str]) -> None:
        """يضيف الروابط الجديدة للذاكرة الداخلية، ثم يحفظ الملف فورًا.

        الحفظ الفوري (بدل الاعتماد على استدعاء save() منفصل) يضمن إننا
        منسناش نحفظ لو حصل خطأ بعد استدعاء mark_seen() في مكان تاني.
        """
        self._seen_urls.update(urls)
        self._save()

    def _load(self) -> set[str]:
        """يقرأ الروابط المحفوظة من الملف، أو يبدأ بمجموعة فاضية لو الملف مش موجود بعد."""
        if not self.file_path.exists():
            return set()

        try:
            raw_data = json.loads(self.file_path.read_text(encoding="utf-8"))
            return set(raw_data)
        except (json.JSONDecodeError, TypeError):
            # لو الملف موجود لكن تالف/فاسد، الأفضل نبدأ بذاكرة فاضية
            # ونسجّل تحذير، بدل ما نوقف المشروع بالكامل.
            logger.warning(
                "ملف التخزين '%s' تالف أو غير صالح، سيتم البدء بذاكرة فاضية.",
                self.file_path,
            )
            return set()

    def _save(self) -> None:
        """يحفظ الحالة الحالية للروابط في ملف JSON."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text(
            json.dumps(sorted(self._seen_urls), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
