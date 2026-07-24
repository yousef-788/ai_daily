"""
retry.py
--------
أداة مساعدة عامة لجلب رابط عبر HTTP مع إعادة محاولة تلقائية عند فشل
مؤقت (Timeout، انقطاع اتصال...)، بدل ما أي Collector يفشل من أول
محاولة لمشكلة شبكة عابرة.
"""

import logging
import time

import requests

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_SECONDS = 1.0

# بعض المواقع (خصوصًا اللي فيها حماية زي Cloudflare) بترفض أي طلب من
# غير User-Agent يشبه متصفح حقيقي، وبترفض افتراضي مكتبة requests
# ("python-requests/x.x") لأنه بيكشف إن الطلب جاي من سكربت آلي.
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}


def fetch_url_with_retry(
    url: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    headers: dict[str, str] | None = None,
) -> requests.Response:
    """يجلب رابط عبر HTTP GET، مع إعادة محاولة تلقائية عند فشل مؤقت.

    كل محاولة فاشلة بتستنى فترة متزايدة (Exponential backoff بسيط: مدة
    البداية × رقم المحاولة) قبل المحاولة التالية، عشان نديله فرصة
    يتعافى بدل ما نضغط عليه أكتر فورًا.

    Args:
        url: الرابط المطلوب جلبه.
        timeout: أقصى وقت انتظار (بالثواني) لكل محاولة على حدة.
        max_retries: أقصى عدد محاولات إجمالي (بما فيها المحاولة الأولى).
        backoff_seconds: مدة الانتظار الأساسية بين المحاولات (بالثواني).
        headers: هيدرز HTTP إضافية. الافتراضي: User-Agent يشبه متصفح حقيقي
            (DEFAULT_HEADERS)، لتفادي رفض المواقع المحمية للطلبات الآلية.

    Returns:
        requests.Response: الاستجابة الناجحة (status code سليم).

    Raises:
        requests.RequestException: لو كل المحاولات فشلت.
    """
    return _request_with_retry(
        "GET", url, timeout=timeout, max_retries=max_retries,
        backoff_seconds=backoff_seconds, headers=headers,
    )


def post_json_with_retry(
    url: str,
    json_payload: dict,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    headers: dict[str, str] | None = None,
) -> requests.Response:
    """يرسل طلب POST بجسم JSON، مع إعادة محاولة تلقائية عند فشل مؤقت.

    نفس منطق fetch_url_with_retry بالظبط، لكن لطلبات POST (مثال: استدعاء
    API بحث بيحتاج إرسال بيانات، مش بس جلب رابط GET).

    Args:
        url: رابط الـ API المطلوب استدعاؤه.
        json_payload: جسم الطلب (هيتحول لـ JSON تلقائيًا).
        timeout: أقصى وقت انتظار (بالثواني) لكل محاولة.
        max_retries: أقصى عدد محاولات إجمالي.
        backoff_seconds: مدة الانتظار الأساسية بين المحاولات.
        headers: هيدرز HTTP إضافية (زي Content-Type).

    Returns:
        requests.Response: الاستجابة الناجحة.

    Raises:
        requests.RequestException: لو كل المحاولات فشلت.
    """
    return _request_with_retry(
        "POST", url, timeout=timeout, max_retries=max_retries,
        backoff_seconds=backoff_seconds, headers=headers, json=json_payload,
    )


def _request_with_retry(
    method: str,
    url: str,
    timeout: int,
    max_retries: int,
    backoff_seconds: float,
    headers: dict[str, str] | None,
    json: dict | None = None,
) -> requests.Response:
    """المنطق المشترك الفعلي لإعادة المحاولة، تستخدمه كل من GET وPOST أعلاه."""
    request_headers = headers if headers is not None else DEFAULT_HEADERS
    last_error: requests.RequestException | None = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.request(
                method, url, timeout=timeout, headers=request_headers, json=json
            )
            response.raise_for_status()
            return response
        except requests.RequestException as error:
            last_error = error
            logger.warning(
                "فشلت محاولة %d/%d لـ %s '%s': %s", attempt, max_retries, method, url, error
            )
            if attempt < max_retries:
                time.sleep(backoff_seconds * attempt)

    # لو وصلنا هنا، يبقى كل المحاولات فشلت (last_error لازم يكون متحدد).
    assert last_error is not None
    raise last_error
