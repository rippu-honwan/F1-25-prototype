"""Quick test script"""
from src.f1_telemetry_listener import F1TelemetryListener

if __name__ == "__main__":
    listener = F1TelemetryListener()
    listener.start(timeout=30)
