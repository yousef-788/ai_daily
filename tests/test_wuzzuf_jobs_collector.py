"""اختبارات WuzzufJobsCollector.

نستخدم monkeypatch لاستبدال استدعاءات الشبكة الحقيقية (post_json_with_retry
و fetch_url_with_retry) بنسخ وهمية ترجّع بيانات بنفس شكل استجابة Wuzzuf
API الحقيقية (اللي فحصناها من مشروع مفتوح المصدر)، بدون أي اتصال إنترنت.
"""

import pytest

from ai_daily.collectors import wuzzuf_jobs_collector as collector_module
from ai_daily.collectors.wuzzuf_jobs_collector import WuzzufJobsCollector


class _FakeResponse:
    """يحاكي شكل requests.Response، بيرجع بيانات JSON محددة مسبقًا."""

    def __init__(self, json_data: dict) -> None:
        self._json_data = json_data

    def json(self) -> dict:
        return self._json_data


def _make_collector() -> WuzzufJobsCollector:
    return WuzzufJobsCollector(source_name="Wuzzuf AI Jobs", search_query="Artificial Intelligence")


def _search_response(ids: list[str]) -> _FakeResponse:
    """يحاكي استجابة /api/search/job (بترجع IDs بس)."""
    return _FakeResponse({"data": [{"id": job_id} for job_id in ids], "meta": {"totalResultsCount": len(ids)}})


def _job_details_response(jobs: list[dict]) -> _FakeResponse:
    """يحاكي استجابة /api/job (بترجع تفاصيل كاملة لكل وظيفة)."""
    return _FakeResponse({"data": jobs})


def _make_job_attrs(title: str, uri: str, city: str = "Cairo", country: str = "Egypt") -> dict:
    """دالة مساعدة لبناء عنصر وظيفة بنفس شكل attributes الحقيقي."""
    return {
        "attributes": {
            "title": title,
            "uri": uri,
            "location": {"city": {"name": city}, "country": {"name": country}},
            "careerLevel": {"name": "Experienced"},
            "postedAt": "07/22/2026 10:00:00",
        }
    }


def test_collect_returns_only_ai_related_jobs(monkeypatch):
    """التأكد أن الوظائف غير المتعلقة بالـ AI بتتفلتر حتى لو رجعت من الـ API."""
    collector = _make_collector()

    monkeypatch.setattr(
        collector_module, "post_json_with_retry", lambda *a, **kw: _search_response(["id1", "id2"])
    )
    monkeypatch.setattr(
        collector_module,
        "fetch_url_with_retry",
        lambda *a, **kw: _job_details_response(
            [
                _make_job_attrs("AI Engineer", "jobs/p/ai-engineer"),
                _make_job_attrs("Sales Manager", "jobs/p/sales-manager"),
            ]
        ),
    )

    items = collector.collect()

    titles = [item.title for item in items]
    assert "AI Engineer" in titles
    assert "Sales Manager" not in titles


def test_collect_resolves_job_urls_correctly(monkeypatch):
    """التأكد أن رابط الوظيفة بيتبنى صح من الـ uri النسبي."""
    collector = _make_collector()

    monkeypatch.setattr(collector_module, "post_json_with_retry", lambda *a, **kw: _search_response(["id1"]))
    monkeypatch.setattr(
        collector_module,
        "fetch_url_with_retry",
        lambda *a, **kw: _job_details_response(
            [_make_job_attrs("Machine Learning Engineer", "jobs/p/ml-engineer-cairo")]
        ),
    )

    items = collector.collect()

    assert items[0].url == "https://wuzzuf.net/jobs/p/ml-engineer-cairo"


def test_collect_builds_content_from_location_level_and_date(monkeypatch):
    """التأكد أن الموقع والمستوى الوظيفي وتاريخ النشر بيتجمعوا في content."""
    collector = _make_collector()

    monkeypatch.setattr(collector_module, "post_json_with_retry", lambda *a, **kw: _search_response(["id1"]))
    monkeypatch.setattr(
        collector_module,
        "fetch_url_with_retry",
        lambda *a, **kw: _job_details_response(
            [_make_job_attrs("AI Researcher", "jobs/p/ai-researcher", city="Giza", country="Egypt")]
        ),
    )

    items = collector.collect()

    assert "Giza, Egypt" in items[0].content
    assert "Experienced" in items[0].content


def test_collect_returns_empty_list_when_no_search_results(monkeypatch):
    """التأكد أن نتيجة بحث فاضية بترجّع قائمة فاضية بدل خطأ."""
    collector = _make_collector()

    monkeypatch.setattr(collector_module, "post_json_with_retry", lambda *a, **kw: _search_response([]))

    items = collector.collect()

    assert items == []


def test_collect_handles_search_api_failure_gracefully(monkeypatch):
    """التأكد أن فشل استدعاء API البحث (زي 403 Forbidden) بيرجّع قائمة فاضية بدل ما يكسر البرنامج."""
    collector = _make_collector()

    def fake_search(*args, **kwargs):
        raise Exception("Simulated 403 Forbidden")

    monkeypatch.setattr(collector_module, "post_json_with_retry", fake_search)

    items = collector.collect()

    assert items == []


def test_collect_handles_missing_title_or_uri_gracefully(monkeypatch):
    """التأكد أن وظيفة ناقصة بيانات أساسية (عنوان/رابط) بتتجاهل بدل ما تسبب خطأ."""
    collector = _make_collector()

    incomplete_job = {"attributes": {"title": "AI Engineer", "uri": ""}}  # uri فاضي

    monkeypatch.setattr(collector_module, "post_json_with_retry", lambda *a, **kw: _search_response(["id1"]))
    monkeypatch.setattr(
        collector_module, "fetch_url_with_retry", lambda *a, **kw: _job_details_response([incomplete_job])
    )

    items = collector.collect()

    assert items == []


def test_job_details_request_does_not_send_content_type_header(monkeypatch):
    """التأكد أن طلب GET التفاصيل مبيبعتش Content-Type: application/json.

    هذا Regression Test لخطأ حقيقي حصل فعليًا: إرسال Content-Type بيقول
    JSON من غير أي body فعلي خلّى Wuzzuf يرفض الطلب بخطأ "415 Unsupported
    Media Type". لازم الطلب ده يفضل من غير هيدر Content-Type.
    """
    collector = _make_collector()
    captured_kwargs = {}

    def fake_fetch(url, **kwargs):
        captured_kwargs.update(kwargs)
        return _job_details_response([_make_job_attrs("AI Engineer", "jobs/p/ai-engineer")])

    monkeypatch.setattr(collector_module, "post_json_with_retry", lambda *a, **kw: _search_response(["id1"]))
    monkeypatch.setattr(collector_module, "fetch_url_with_retry", fake_fetch)

    collector.collect()

    sent_headers = captured_kwargs.get("headers")
    assert sent_headers is None or "Content-Type" not in sent_headers
