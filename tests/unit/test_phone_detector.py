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


def test_phone_detector_detect_no_face():
    from src.core.phone_detector import PhoneDetector
    detector = PhoneDetector()
    res = detector.detect(None, None, 480, 480)
    assert res.phone_detected is False
    assert res.hand_detected is False


def test_phone_detector_detect_no_hands():
    from unittest.mock import MagicMock
    from src.core.phone_detector import PhoneDetector
    
    detector = PhoneDetector()
    # Mockear HandsWrapper para retornar lista vacía o None
    detector._hands.process = MagicMock(return_value=None)
    
    mock_face = MagicMock()
    res = detector.detect(None, mock_face, 480, 480)
    assert res.phone_detected is False
    assert res.hand_detected is False