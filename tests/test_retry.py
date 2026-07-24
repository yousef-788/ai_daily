"""اختبارات fetch_url_with_retry و post_json_with_retry.

نستخدم monkeypatch لاستبدال requests.request و time.sleep بنسخ وهمية، عشان:
1) الاختبارات ماتحتاجش أي اتصال إنترنت حقيقي.
2) الاختبارات تبقى سريعة (بدون انتظار فعلي لمدة الـ backoff).
"""

import requests
import pytest

from ai_daily.utils import retry as retry_module
from ai_daily.utils.retry import DEFAULT_HEADERS, fetch_url_with_retry, post_json_with_retry


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    """يمنع أي انتظار فعلي أثناء الاختبار (استبدال time.sleep بدالة فارغة)."""
    monkeypatch.setattr(retry_module.time, "sleep", lambda seconds: None)


class _FakeResponse:
    """يحاكي شكل requests.Response الناجح."""

    def raise_for_status(self) -> None:
        pass  # استجابة ناجحة، مفيش خطأ نرفعه


def test_fetch_succeeds_on_first_attempt(monkeypatch):
    """التأكد أن نجاح المحاولة الأولى بيرجّع الاستجابة فورًا بدون أي إعادة محاولة."""
    call_count = 0

    def fake_request(method, url, timeout, headers, json=None):
        nonlocal call_count
        call_count += 1
        assert method == "GET"
        return _FakeResponse()

    monkeypatch.setattr(retry_module.requests, "request", fake_request)

    fetch_url_with_retry("https://example.com/feed")

    assert call_count == 1


def test_fetch_sends_realistic_user_agent_by_default(monkeypatch):
    """التأكد أن الطلب بيبعت User-Agent يشبه متصفح حقيقي افتراضيًا.

    ده مهم عمليًا: مواقع كتير (زي Wuzzuf) بترفض الطلبات اللي معاها
    User-Agent الافتراضي بتاع مكتبة requests لأنه بيكشف إنه سكربت آلي.
    """
    captured_headers = {}

    def fake_request(method, url, timeout, headers, json=None):
        captured_headers.update(headers)
        return _FakeResponse()

    monkeypatch.setattr(retry_module.requests, "request", fake_request)

    fetch_url_with_retry("https://example.com/feed")

    assert captured_headers == DEFAULT_HEADERS
    assert "python-requests" not in captured_headers["User-Agent"]


def test_fetch_custom_headers_override_default(monkeypatch):
    """التأكد أن تمرير headers مخصصة بيستبدل الافتراضية، مش يضيف ليها."""
    captured_headers = {}

    def fake_request(method, url, timeout, headers, json=None):
        captured_headers.update(headers)
        return _FakeResponse()

    monkeypatch.setattr(retry_module.requests, "request", fake_request)

    fetch_url_with_retry("https://example.com/feed", headers={"X-Custom": "value"})

    assert captured_headers == {"X-Custom": "value"}


def test_fetch_succeeds_after_temporary_failures(monkeypatch):
    """التأكد أن فشل مؤقت (محاولتين) متبوع بنجاح بيرجّع الاستجابة في النهاية."""
    call_count = 0

    def fake_request(method, url, timeout, headers, json=None):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise requests.ConnectionError("Simulated temporary network failure")
        return _FakeResponse()

    monkeypatch.setattr(retry_module.requests, "request", fake_request)

    fetch_url_with_retry("https://example.com/feed", max_retries=5)

    assert call_count == 3  # فشلت مرتين ونجحت في الثالثة


def test_fetch_raises_after_exhausting_all_retries(monkeypatch):
    """التأكد أن استمرار الفشل بيرفع الخطأ الأصلي بعد استنفاد كل المحاولات."""

    def fake_request(method, url, timeout, headers, json=None):
        raise requests.ConnectionError("Persistent network failure")

    monkeypatch.setattr(retry_module.requests, "request", fake_request)

    with pytest.raises(requests.ConnectionError):
        fetch_url_with_retry("https://example.com/feed", max_retries=3)


def test_fetch_does_not_retry_beyond_max_retries(monkeypatch):
    """التأكد أن عدد المحاولات الفعلي بيطابق max_retries بالظبط، مش أكتر."""
    call_count = 0

    def fake_request(method, url, timeout, headers, json=None):
        nonlocal call_count
        call_count += 1
        raise requests.ConnectionError("Always fails")

    monkeypatch.setattr(retry_module.requests, "request", fake_request)

    with pytest.raises(requests.ConnectionError):
        fetch_url_with_retry("https://example.com/feed", max_retries=3)

    assert call_count == 3


def test_post_json_sends_correct_method_and_payload(monkeypatch):
    """التأكد أن post_json_with_retry بتبعت method=POST والـ payload الصحيح."""
    captured = {}

    def fake_request(method, url, timeout, headers, json=None):
        captured["method"] = method
        captured["json"] = json
        return _FakeResponse()

    monkeypatch.setattr(retry_module.requests, "request", fake_request)

    post_json_with_retry("https://example.com/api/search", json_payload={"query": "AI"})

    assert captured["method"] == "POST"
    assert captured["json"] == {"query": "AI"}


def test_post_json_retries_on_temporary_failure(monkeypatch):
    """التأكد أن POST كمان بيعيد المحاولة عند فشل مؤقت زي GET بالظبط."""
    call_count = 0

    def fake_request(method, url, timeout, headers, json=None):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise requests.ConnectionError("Simulated failure")
        return _FakeResponse()

    monkeypatch.setattr(retry_module.requests, "request", fake_request)

    post_json_with_retry("https://example.com/api/search", json_payload={}, max_retries=3)

    assert call_count == 2
