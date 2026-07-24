"""اختبارات CompositePublisher."""

from ai_daily.models.content_item import ContentItem
from ai_daily.publishers.base import BasePublisher
from ai_daily.publishers.composite_publisher import CompositePublisher


class _RecordingPublisher(BasePublisher):
    """Publisher تجريبي بيسجّل هل publish() اتنادت عليه ولا لأ."""

    def __init__(self, should_fail: bool = False) -> None:
        self.was_called = False
        self.should_fail = should_fail

    def publish(self, items: list[ContentItem]) -> None:
        self.was_called = True
        if self.should_fail:
            raise RuntimeError("Simulated publisher failure")


def test_calls_all_publishers():
    """التأكد أن كل الـ Publishers في القائمة بينفّذوا فعليًا."""
    publisher_1 = _RecordingPublisher()
    publisher_2 = _RecordingPublisher()
    composite = CompositePublisher([publisher_1, publisher_2])

    composite.publish([])

    assert publisher_1.was_called is True
    assert publisher_2.was_called is True


def test_one_publisher_failure_does_not_block_others():
    """التأكد أن فشل Publisher واحد ميمنعش تنفيذ اللي بعده."""
    failing_publisher = _RecordingPublisher(should_fail=True)
    working_publisher = _RecordingPublisher()
    composite = CompositePublisher([failing_publisher, working_publisher])

    composite.publish([])  # ميرفعش أي استثناء للخارج

    assert working_publisher.was_called is True
