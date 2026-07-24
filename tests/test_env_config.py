"""اختبارات load_environment و get_required_env و get_optional_env."""

import pytest

from ai_daily.config import get_optional_env, get_required_env, load_environment


@pytest.fixture(autouse=True)
def _clean_test_env_var(monkeypatch):
    """يتأكد أن متغير الاختبار TEST_VAR نظيف قبل وبعد كل اختبار،
    عشان اختبار ميأثرش على اللي بعده (os.environ حالة عامة مشتركة).
    """
    monkeypatch.delenv("TEST_VAR", raising=False)
    yield
    monkeypatch.delenv("TEST_VAR", raising=False)


def test_load_environment_reads_env_file(tmp_path, monkeypatch):
    """التأكد أن load_environment بتحمّل متغير من ملف .env فعليًا في os.environ."""
    env_file = tmp_path / ".env"
    env_file.write_text("TEST_VAR=hello_from_env_file\n", encoding="utf-8")

    load_environment(env_path=env_file)

    assert get_required_env("TEST_VAR") == "hello_from_env_file"


def test_get_required_env_raises_when_missing():
    """التأكد أن غياب متغير مطلوب بيرفع خطأ واضح بدل None صامت."""
    with pytest.raises(ValueError):
        get_required_env("TEST_VAR")


def test_get_optional_env_returns_default_when_missing():
    """التأكد أن متغير اختياري غير موجود بيرجّع القيمة الافتراضية."""
    result = get_optional_env("TEST_VAR", default="fallback_value")

    assert result == "fallback_value"


def test_get_optional_env_returns_actual_value_when_present(monkeypatch):
    """التأكد أن متغير موجود فعليًا بيتقرأ صح، مش القيمة الافتراضية."""
    monkeypatch.setenv("TEST_VAR", "real_value")

    result = get_optional_env("TEST_VAR", default="fallback_value")

    assert result == "real_value"
