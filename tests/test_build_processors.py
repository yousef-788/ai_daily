"""اختبارات build_processors: التأكد أن التلخيص بالـ AI يتفعّل شرطيًا فقط."""

from ai_daily.main import build_processors
from ai_daily.processors.ai_summarizer import AISummarizerProcessor
from ai_daily.processors.text_cleaner import TextCleanerProcessor


def test_build_processors_without_api_key_only_includes_cleaner(monkeypatch):
    """التأكد أنه بدون ANTHROPIC_API_KEY، الـ pipeline بيحتوي على التنظيف فقط."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    processors = build_processors()

    assert len(processors) == 1
    assert isinstance(processors[0], TextCleanerProcessor)


def test_build_processors_with_api_key_includes_summarizer(monkeypatch):
    """التأكد أنه مع وجود ANTHROPIC_API_KEY، الـ AI Summarizer بيتضاف للـ pipeline."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-testing-only")

    processors = build_processors()

    assert len(processors) == 2
    assert isinstance(processors[0], TextCleanerProcessor)
    assert isinstance(processors[1], AISummarizerProcessor)


def test_build_processors_respects_custom_max_calls_env_var(monkeypatch):
    """التأكد أن AI_MAX_SUMMARIES_PER_RUN بيتقرأ ويتوصل صح للـ AISummarizerProcessor."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-testing-only")
    monkeypatch.setenv("AI_MAX_SUMMARIES_PER_RUN", "5")

    processors = build_processors()

    summarizer = processors[1]
    assert isinstance(summarizer, AISummarizerProcessor)
    assert summarizer.max_calls_per_run == 5


def test_build_processors_defaults_to_news_only_summarization(monkeypatch):
    """التأكد أن التلخيص بيقتصر على قسم news بس افتراضيًا (من غير تحديد AI_SUMMARY_CATEGORIES)."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-testing-only")
    monkeypatch.delenv("AI_SUMMARY_CATEGORIES", raising=False)

    processors = build_processors()

    summarizer = processors[1]
    assert summarizer.target_categories == {"news"}


def test_build_processors_respects_custom_categories_env_var(monkeypatch):
    """التأكد أن AI_SUMMARY_CATEGORIES بتتقرأ وتتحول لمجموعة أقسام صحيحة."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-testing-only")
    monkeypatch.setenv("AI_SUMMARY_CATEGORIES", "news, tools")

    processors = build_processors()

    summarizer = processors[1]
    assert summarizer.target_categories == {"news", "tools"}
