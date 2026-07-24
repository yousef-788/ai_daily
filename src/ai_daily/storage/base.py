"""
base.py
-------
يعرّف هذا الملف العقد (Interface) الذي يجب أن تلتزم به أي وسيلة تخزين
تُستخدم لمنع تكرار نشر نفس المحتوى (سواء ملف JSON بسيط الآن، أو قاعدة
بيانات حقيقية لاحقًا).
"""

from abc import ABC, abstractmethod


class SeenItemsStore(ABC):
    """العقد الأساسي لأي وسيلة تتبع "العناصر التي سبق جمعها/نشرها".

    يُستخدم الرابط (url) كمعرّف فريد للعنصر، لأنه من المفترض أن يكون
    ثابتًا لكل خبر/مقال بغض النظر عن المصدر.
    """

    @abstractmethod
    def is_seen(self, url: str) -> bool:
        """يتحقق هل هذا الرابط سبق تسجيله من قبل أم لا."""
        raise NotImplementedError

    @abstractmethod
    def mark_seen(self, urls: list[str]) -> None:
        """يسجّل مجموعة من الروابط كعناصر "تمت رؤيتها"."""
        raise NotImplementedError
