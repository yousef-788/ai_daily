"""اختبارات AISummarizerProcessor باستخدام كائن Anthropic client وهمي (Fake).

لا تحتاج هذه الاختبارات أي مفتاح API حقيقي ولا اتصال بالإنترنت، لأننا
بنمرر كائن وهمي بنفس شكل client.messages.create() الحقيقي.
"""

from ai_daily.models.content_item import ContentItem
from ai_daily.processors.ai_summarizer import AISummarizerProcessor


class _FakeTextBlock:
    """يحاكي شكل الـ text block اللي بيرجعه Anthropic SDK الحقيقي."""

    def __init__(self, text: str) -> None:
        self.text = text


class _FakeResponse:
    """يحاكي شكل الـ response اللي بيرجعه client.messages.create() الحقيقي."""

    def __init__(self, text: str) -> None:
        self.content = [_FakeTextBlock(text)]


class _FakeMessages:
    """يحاكي الـ namespace messages بتاع الـ client الحقيقي."""

    def __init__(self, response_text: str | None = None, should_raise: bool = False) -> None:
        self._response_text = response_text
        self._should_raise = should_raise
        self.last_call_kwargs: dict | None = None  # لتتبع آخر طلب اتبعت، لأغراض الاختبار

    def create(self, **kwargs):
        self.last_call_kwargs = kwargs
        if self._should_raise:
            raise RuntimeError("Simulated API failure")
        return _FakeResponse(self._response_text)


class _FakeAnthropicClient:
    """كائن وهمي بديل لـ anthropic.Anthropic، بنفس الواجهة المستخدمة فقط."""

    def __init__(self, response_text: str | None = None, should_raise: bool = False) -> None:
        self.messages = _FakeMessages(response_text, should_raise)


def _make_item() -> ContentItem:
    return ContentItem(
        title="OpenAI releases new model",
        url="https://example.com/1",
        source="TestSource",
        content="A very long raw article body about the new model release...",
    )


def test_process_replaces_content_with_summary():
    """التأكد أن محتوى العنصر بيتستبدل بالملخص المُرجَع من الـ client."""
    client = _FakeAnthropicClient(response_text="ملخص قصير للخبر.")
    processor = AISummarizerProcessor(client=client)

    result = processor.process(_make_item())

    assert result.content == "ملخص قصير للخبر."
    assert result.title == "OpenAI releases new model"  # باقي الحقول لم تتغير


def test_process_sends_title_and_content_in_prompt():
    """التأكد أن العنوان والمحتوى بيتبعتوا فعليًا في الطلب للموديل."""
    client = _FakeAnthropicClient(response_text="ملخص")
    processor = AISummarizerProcessor(client=client)

    processor.process(_make_item())

    sent_message = client.messages.last_call_kwargs["messages"][0]["content"]
    assert "OpenAI releases new model" in sent_message
    assert "A very long raw article body" in sent_message


def test_process_falls_back_to_original_content_on_api_failure():
    """التأكد أن فشل الـ API بيرجّع المحتوى الأصلي بدل ما يوقف كل العملية."""
    client = _FakeAnthropicClient(should_raise=True)
    processor = AISummarizerProcessor(client=client)
    original_item = _make_item()

    result = processor.process(original_item)

    assert result.content == original_item.content  # المحتوى الأصلي اتحفظ زي ما هو


def test_respects_max_calls_per_run_limit():
    """التأكد أن العناصر اللي بعد الحد الأقصى بترجع بمحتواها الأصلي بدون استدعاء API."""
    client = _FakeAnthropicClient(response_text="ملخص")
    processor = AISummarizerProcessor(client=client, max_calls_per_run=2)

    items = [_make_item() for _ in range(4)]
    results = [processor.process(item) for item in items]

    # أول عنصرين لخّصهم فعليًا (المحتوى اتغيّر)، والباقي رجع بمحتواه الأصلي
    assert results[0].content == "ملخص"
    assert results[1].content == "ملخص"
    assert results[2].content == items[2].content  # لم يُلخَّص
    assert results[3].content == items[3].content  # لم يُلخَّص


def test_unlimited_calls_when_max_calls_per_run_is_none():
    """التأكد أن عدم تحديد سقف (القيمة الافتراضية None) بيسمح بأي عدد استدعاءات."""
    client = _FakeAnthropicClient(response_text="ملخص")
    processor = AISummarizerProcessor(client=client)  # بدون max_calls_per_run

    items = [_make_item() for _ in range(10)]
    results = [processor.process(item) for item in items]

    assert all(result.content == "ملخص" for result in results)


def test_summarizes_only_items_in_target_categories():
    """التأكد أن العناصر خارج target_categories بترجع زي ما هي بدون استدعاء API."""
    client = _FakeAnthropicClient(response_text="ملخص AI")
    processor = AISummarizerProcessor(client=client, target_categories={"news"})

    news_item = ContentItem(
        title="News", url="https://example.com/n", source="Test", content="raw news", category="news"
    )
    job_item = ContentItem(
        title="Job", url="https://example.com/j", source="Test", content="raw job", category="jobs"
    )

    news_result = processor.process(news_item)
    job_result = processor.process(job_item)

    assert news_result.content == "ملخص AI"  # اتلخّص
    assert job_result.content == "raw job"  # رجع زي ما هو، من غير تلخيص


def test_target_categories_none_summarizes_everything():
    """التأكد أن عدم تحديد target_categories (القيمة الافتراضية None) بيلخّص كل الأقسام."""
    client = _FakeAnthropicClient(response_text="ملخص")
    processor = AISummarizerProcessor(client=client)  # target_categories=None افتراضيًا

    job_item = ContentItem(
        title="Job", url="https://example.com/j", source="Test", content="raw job", category="jobs"
    )

    result = processor.process(job_item)

    assert result.content == "ملخص"


def test_skipped_categories_do_not_count_against_max_calls():
    """التأكد أن العناصر المُتخطّاة بسبب category ماتستهلكش من سقف الاستدعاءات."""
    client = _FakeAnthropicClient(response_text="ملخص")
    processor = AISummarizerProcessor(
        client=client, target_categories={"news"}, max_calls_per_run=1
    )

    job_item = ContentItem(
        title="Job", url="https://example.com/j", source="Test", content="raw job", category="jobs"
    )
    news_item_1 = ContentItem(
        title="N1", url="https://example.com/n1", source="Test", content="raw", category="news"
    )
    news_item_2 = ContentItem(
        title="N2", url="https://example.com/n2", source="Test", content="raw", category="news"
    )

    # نمرر وظيفة (متخطاة) قبل خبرين، عشان نتأكد إن الوظيفة ماستهلكتش من السقف
    processor.process(job_item)
    result_1 = processor.process(news_item_1)  # لازم يتلخص (أول استدعاء فعلي)
    result_2 = processor.process(news_item_2)  # لازم يترفض (وصلنا للسقف: 1)

    assert result_1.content == "ملخص"
    assert result_2.content == "raw"
