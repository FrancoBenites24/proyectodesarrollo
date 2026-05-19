from src.core.detector import FrameResult
from src.core.phone_result import PhoneResult


def test_phone_result_defaults():
    result = PhoneResult()

    assert result.phone_detected is False
    assert result.hand_detected is False
    assert result.hand_position is None
    assert result.confidence == 0.0


def test_frame_result_has_phone_detected():
    result = FrameResult()

    assert hasattr(result, "phone_detected")
    assert result.phone_detected is False