"""
wuzzuf_jobs_collector.py
--------------------------
Collector يجمع وظائف الذكاء الاصطناعي في مصر من Wuzzuf، باستخدام الـ
API الداخلي الحقيقي للموقع (JSON) بدل تحليل HTML بـ CSS selectors.

ليه API بدل Web Scraping عادي؟
1) أكثر ثباتًا: تصميم الموقع (وأسماء CSS classes) بيتغيّر بمرور الوقت،
   لكن الـ API الداخلي أكثر استقرارًا لأنه العمود الفقري لتطبيق الموقع.
2) بيانات منظمة (JSON) بدل استخراج نص من HTML بتخمين هيكلي.

الـ API محتاج خطوتين (اكتشفناهم من كود مفتوح المصدر بيستخدم نفس الـ API):
1) البحث: POST /api/search/job → بيرجع IDs بس + مقتطفات نصية.
2) التفاصيل: GET /api/job?filter[other][ids]=... → بيرجع العنوان
   والرابط والموقع وتفاصيل كل وظيفة بالـ IDs دي.

ملحوظة: الـ API ده داخلي (مش موثّق رسميًا من Wuzzuf)، فمن الممكن يتغيّر
شكله أو يتفعّل عليه نفس حماية الـ Scraping العادي. لو فشل، الرسالة في
الـ log هتوضح السبب (خطأ شبكة / رفض الطلب / تغيّر شكل الاستجابة).
"""

import logging
from urllib.parse import urljoin

from ai_daily.collectors.base import BaseCollector
from ai_daily.models.content_item import ContentItem
from ai_daily.utils.retry import DEFAULT_HEADERS, fetch_url_with_retry, post_json_with_retry

logger = logging.getLogger(__name__)

WUZZUF_BASE_URL = "https://wuzzuf.net/"
SEARCH_API_URL = "https://wuzzuf.net/api/search/job"
JOB_DETAILS_API_URL = "https://wuzzuf.net/api/job"

# كلمات مفتاحية للتأكد إن الوظيفة فعلًا متعلقة بالـ AI، كطبقة حماية إضافية
# فوق نتائج بحث Wuzzuf نفسها (اللي مش دايمًا دقيقة 100%).
DEFAULT_AI_KEYWORDS = (
    "ai",
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "data scientist",
    "data science",
    "nlp",
    "llm",
    "computer vision",
    "generative ai",
    "prompt engineer",
    "ml engineer",
    "ذكاء اصطناعي",
)


class WuzzufJobsCollector(BaseCollector):
    """يجمع إعلانات وظائف من Wuzzuf عبر الـ API الداخلي، ويفلترها للمتعلق بالـ AI.

    Attributes:
        source_name: اسم تعريفي للمصدر.
        search_query: كلمة البحث المُرسلة لـ API البحث (مثال: "Artificial Intelligence").
        page_size: أقصى عدد نتائج بحث نطلبها من الـ API في المرة الواحدة.
        ai_keywords: الكلمات المفتاحية المستخدمة لفلترة الوظائف ذات الصلة بالـ AI.
        category: تصنيف هذا المصدر ضمن أقسام النشرة (jobs افتراضيًا).
    """

    def __init__(
        self,
        source_name: str,
        search_query: str = "Artificial Intelligence",
        page_size: int = 50,
        ai_keywords: tuple[str, ...] = DEFAULT_AI_KEYWORDS,
        category: str = "jobs",
    ) -> None:
        self.source_name = source_name
        self.search_query = search_query
        self.page_size = page_size
        self.ai_keywords = ai_keywords
        self.category = category

    def collect(self) -> list[ContentItem]:
        """يبحث عن وظائف، يجيب تفاصيلها الكاملة، ويفلترها للمتعلق بالـ AI فقط."""
        try:
            job_ids = self._search_job_ids()
        except Exception:  # noqa: BLE001 - نعزل فشل البحث عن باقي المصادر
            logger.exception("فشل البحث في Wuzzuf API للمصدر '%s'.", self.source_name)
            return []

        if not job_ids:
            logger.info("لم يُرجع بحث Wuzzuf أي نتائج للمصدر '%s'.", self.source_name)
            return []

        try:
            job_details = self._fetch_job_details(job_ids)
        except Exception:  # noqa: BLE001 - نعزل فشل جلب التفاصيل عن باقي المصادر
            logger.exception("فشل جلب تفاصيل الوظائف من Wuzzuf API للمصدر '%s'.", self.source_name)
            return []

        return self._to_content_items(job_details)

    def _search_job_ids(self) -> list[str]:
        """يستدعي API البحث ويرجّع قائمة IDs الوظائف المطابقة."""
        payload = {
            "startIndex": 0,
            "pageSize": self.page_size,
            "longitude": "0",
            "latitude": "0",
            "query": self.search_query,
            "searchFilters": {},
        }
        response = post_json_with_retry(
            SEARCH_API_URL, json_payload=payload, headers=self._search_headers()
        )
        results = response.json().get("data", [])
        return [item["id"] for item in results if "id" in item]

    def _fetch_job_details(self, job_ids: list[str]) -> list[dict]:
        """يستدعي API التفاصيل بالـ IDs المجمّعة، ويرجّع تفاصيل كل وظيفة.

        ملحوظة: هذا طلب GET بدون أي body، فبنستخدم الهيدرز الافتراضية
        بس (بدون Content-Type: application/json)، لأن إرسال هيدر
        Content-Type بيقول لـ JSON من غير ما نبعت أي body فعلي بيخلي
        السيرفر يرفض الطلب برسالة "415 Unsupported Media Type".
        """
        ids_param = ",".join(job_ids)
        url = f"{JOB_DETAILS_API_URL}?filter[other][ids]={ids_param}"
        response = fetch_url_with_retry(url)
        return response.json().get("data", [])

    def _to_content_items(self, job_details: list[dict]) -> list[ContentItem]:
        """يحوّل تفاصيل الوظائف الخام (JSON) إلى ContentItem، بعد فلترة الصلة بالـ AI."""
        items: list[ContentItem] = []

        for job in job_details:
            attributes = job.get("attributes", {})
            title = (attributes.get("title") or "").strip()
            uri = attributes.get("uri") or ""

            if not title or not uri:
                logger.warning(
                    "تم تجاهل وظيفة من المصدر '%s': نقص بيانات أساسية (عنوان/رابط).",
                    self.source_name,
                )
                continue

            if not self._is_ai_related(title):
                continue

            job_url = urljoin(WUZZUF_BASE_URL, uri)
            content = self._build_content(attributes)

            items.append(
                ContentItem(
                    title=title,
                    url=job_url,
                    source=self.source_name,
                    content=content,
                    category=self.category,
                )
            )

        return items

    def _is_ai_related(self, title: str) -> bool:
        """يتحقق هل العنوان يحتوي على كلمة مفتاحية متعلقة بالـ AI."""
        lowered_title = title.lower()
        return any(keyword in lowered_title for keyword in self.ai_keywords)

    @staticmethod
    def _build_content(attributes: dict) -> str:
        """يبني نص وصفي مختصر من الموقع والمستوى الوظيفي وتاريخ النشر."""
        parts: list[str] = []

        location = attributes.get("location") or {}
        city = (location.get("city") or {}).get("name")
        country = (location.get("country") or {}).get("name")
        if city and country:
            parts.append(f"{city}, {country}")
        elif country:
            parts.append(country)

        career_level = (attributes.get("careerLevel") or {}).get("name")
        if career_level:
            parts.append(career_level)

        posted_at = attributes.get("postedAt")
        if posted_at:
            parts.append(posted_at)

        return " | ".join(parts)

    @staticmethod
    def _search_headers() -> dict[str, str]:
        """هيدرز طلب البحث (POST) فقط: بيضيف Content-Type فوق الافتراضية،
        لأن هذا الطلب (وحده) بيبعت body فعلي بصيغة JSON."""
        return {**DEFAULT_HEADERS, "Content-Type": "application/json;charset=UTF-8"}
