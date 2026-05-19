"""Estado global de la detección."""

import os


def get_alert_system():
    use_voice = os.getenv("ALERT_MODE", "voice") == "voice"
    if use_voice:
        from src.alarm.voice_alert import VoiceAlertSystem
        return VoiceAlertSystem()
    else:
        from src.alarm.alert_system import AlertSystem
        return AlertSystem()