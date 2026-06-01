"""Tests de integración del pipeline completo."""

from __future__ import annotations

from src.api.schemas import AlertLevelSchema, DrowsinessMetrics
from src.core.event_classifier import classify_event
from src.core.temporal import AlertLevel, TemporalState


class MockFrameResult:
    """Simula FrameResult para pruebas."""

    def __init__(
        self,
        phone_detected=False,
        is_distracted=False,
        yawning=False,
    ):
        self.phone_detected = phone_detected
        self.is_distracted = is_distracted
        self.yawning = yawning

        self.ear = 0.25
        self.mor = 0.35
        self.head_yaw = 10.0
        self.head_pitch = 5.0
        self.face_detected = True
        self.timestamp = 123456.0


def test_classify_event_drowsiness():
    state = TemporalState(
        perclos=0.7,
        alert_level=AlertLevel.CRITICAL,
        frames_in_window=90,
        closed_frames=63,
        event_types=(),
    )

    result = MockFrameResult()

    events = classify_event(result, state)

    assert "drowsiness" in events


def test_classify_event_phone():
    state = TemporalState(
        perclos=0.0,
        alert_level=AlertLevel.NONE,
        frames_in_window=90,
        closed_frames=0,
        event_types=(),
    )

    result = MockFrameResult(
        phone_detected=True,
    )

    events = classify_event(result, state)

    assert "phone" in events


def test_classify_event_yawn():
    state = TemporalState(
        perclos=0.0,
        alert_level=AlertLevel.NONE,
        frames_in_window=90,
        closed_frames=0,
        event_types=(),
    )

    result = MockFrameResult(
        yawning=True,
    )

    events = classify_event(result, state)

    assert "yawn" in events


def test_classify_event_distraction():
    state = TemporalState(
        perclos=0.0,
        alert_level=AlertLevel.NONE,
        frames_in_window=90,
        closed_frames=0,
        event_types=(),
    )

    result = MockFrameResult(
        is_distracted=True,
    )

    events = classify_event(result, state)

    assert "distraction" in events


def test_classify_multiple_events():
    state = TemporalState(
        perclos=0.8,
        alert_level=AlertLevel.CRITICAL,
        frames_in_window=90,
        closed_frames=72,
        event_types=(),
    )

    result = MockFrameResult(
        phone_detected=True,
        is_distracted=True,
        yawning=True,
    )

    events = classify_event(result, state)

    assert "drowsiness" in events
    assert "phone" in events
    assert "distraction" in events
    assert "yawn" in events

    assert len(events) == 4


def test_temporal_state_event_types():
    state = TemporalState(
        perclos=0.6,
        alert_level=AlertLevel.HIGH,
        frames_in_window=90,
        closed_frames=54,
        event_types=("drowsiness", "phone"),
    )

    assert "drowsiness" in state.event_types
    assert "phone" in state.event_types


def test_metrics_schema_accepts_new_fields():
    metrics = DrowsinessMetrics(
        ear=0.25,
        mor=0.40,
        perclos=0.30,
        alert_level=AlertLevelSchema.LOW,
        phone_detected=True,
        is_distracted=True,
        head_yaw=15.0,
        head_pitch=7.0,
        yawning=True,
        driving_minutes=125.0,
        face_detected=True,
        fps=29.8,
        timestamp=123456.0,
    )

    assert metrics.phone_detected is True
    assert metrics.is_distracted is True
    assert metrics.yawning is True
    assert metrics.driving_minutes == 125.0


def test_phone_mapping():
    metrics = DrowsinessMetrics(
        ear=0.3,
        mor=0.2,
        perclos=0.1,
        alert_level=AlertLevelSchema.NONE,
        phone_detected=True,
        is_distracted=False,
        head_yaw=0.0,
        head_pitch=0.0,
        yawning=False,
        driving_minutes=0.0,
        face_detected=True,
        fps=30.0,
        timestamp=1.0,
    )

    assert metrics.phone_detected


def test_distraction_mapping():
    metrics = DrowsinessMetrics(
        ear=0.3,
        mor=0.2,
        perclos=0.1,
        alert_level=AlertLevelSchema.NONE,
        phone_detected=False,
        is_distracted=True,
        head_yaw=25.0,
        head_pitch=10.0,
        yawning=False,
        driving_minutes=0.0,
        face_detected=True,
        fps=30.0,
        timestamp=1.0,
    )

    assert metrics.is_distracted