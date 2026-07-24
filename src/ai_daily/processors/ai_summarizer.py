"""
ai_summarizer.py
-----------------
Processor يستخدم Anthropic API لتلخيص محتوى الخبر إلى نص عربي قصير
جاهز للنشر في نشرة AI Daily اليومية على واتساب.
"""

import logging
from dataclasses import replace

from anthropic import Anthropic

from ai_daily.models.content_item import ContentItem
from ai_daily.processors.base import BaseProcessor

logger = logging.getLogger(__name__)

# نموذج اقتصادي مناسب لمهمة تلخيص بسيطة ومتكررة يوميًا (مش محتاجين أقوى نموذج هنا).
DEFAULT_MODEL = "claude-haiku-4-5-20251001"

# نتجنب إرسال نص طويل جدًا للنموذج بدون داعٍ (تكلفة ووقت استجابة أعلى بلا فائدة إضافية).
MAX_CONTENT_CHARS_FOR_PROMPT = 3000

SUMMARIZATION_SYSTEM_PROMPT = (
    "أنت محرر نشرة إخبارية عربية متخصصة في أخبار الذكاء الاصطناعي باسم AI Daily. "
    "مهمتك تلخيص الخبر التالي في 2-3 جمل عربية واضحة ومباشرة، بأسلوب صحفي مختصر، "
    "بدون مقدمات أو تعليقات إضافية، وبدون إعادة كتابة العنوان."
)


class AISummarizerProcessor(BaseProcessor):
    """يلخّص محتوى كل عنصر باستخدام Anthropic API.

    الاعتماد على كائن `client` جاهز (بدل بناء الاتصال داخليًا) هو
    Dependency Injection: بيسهّل اختبار هذا الكلاس بدون استدعاء API
    حقيقي، لأن الاختبارات بتمرر كائن وهمي (Fake) بنفس الشكل.

    Attributes:
        client: كائن Anthropic جاهز (أو أي كائن يطابق نفس الواجهة).
        model: اسم الموديل المستخدم للتلخيص.
        max_calls_per_run: أقصى عدد استدعاءات API مسموح بها في التشغيلة
            الواحدة (للتحكم في التكلفة). None يعني بدون حد أقصى.
        target_categories: مجموعة الأقسام (category) المطلوب تلخيصها فقط
            (مثال: {"news"}). None يعني تلخيص كل الأقسام بدون تفرقة.
            عناصر خارج الأقسام المستهدفة بترجع زي ما هي بدون أي استدعاء
            API، فمفيش تكلفة أو وقت ضايع على محتوى مش محتاج تلخيص.
    """

    def __init__(
        self,
        client: Anthropic,
        model: str = DEFAULT_MODEL,
        max_calls_per_run: int | None = None,
        target_categories: set[str] | None = None,
    ) -> None:
        self.client = client
        self.model = model
        self.max_calls_per_run = max_calls_per_run
        self.target_categories = target_categories
        self._calls_made = 0  # عداد داخلي، يتصفّر تلقائيًا مع كل كائن جديد (كل تشغيلة)

    def process(self, item: ContentItem) -> ContentItem:
        """يستبدل محتوى العنصر بملخص قصير مولّد بالـ AI.

        العنصر بيتخطى (يرجع زي ما هو، من غير أي استدعاء API) في حالتين:
        1) لو category بتاعه مش ضمن target_categories المحددة.
        2) لو وصلنا للحد الأقصى المسموح به من الاستدعاءات في هذه التشغيلة.

        لو استدعاء الـ API فشل لأي سبب (شبكة، تجاوز حد استخدام...)، يتم
        الرجوع للمحتوى الأصلي بدل ما فشل عنصر واحد يوقف كل عملية النشر.
        """
        if self.target_categories is not None and item.category not in self.target_categories:
            return item

        if self.max_calls_per_run is not None and self._calls_made >= self.max_calls_per_run:
            logger.info(
                "تم الوصول للحد الأقصى لاستدعاءات AI في هذه التشغيلة (%d)، "
                "سيتم تخطي تلخيص '%s' ونشر محتواه الأصلي.",
                self.max_calls_per_run,
                item.title,
            )
            return item

        self._calls_made += 1
        try:
            summary = self._summarize(item)
        except Exception:  # noqa: BLE001 - نتعمد عزل فشل عنصر واحد عن الباقي
            logger.exception(
                "فشل تلخيص العنصر '%s' بالـ AI، سيتم استخدام المحتوى الأصلي.", item.title
            )
            return item

        return replace(item, content=summary)

    def _summarize(self, item: ContentItem) -> str:
        """يبني الطلب ويستدعي الـ API فعليًا، ويرجّع نص الملخص."""
        truncated_content = item.content[:MAX_CONTENT_CHARS_FOR_PROMPT]

        response = self.client.messages.create(
            model=self.model,
            max_tokens=200,
            system=SUMMARIZATION_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"العنوان: {item.title}\n\nالمحتوى: {truncated_content}",
                }
            ],
        )

        return response.content[0].text.strip()
