"""
Test Script: F1 25 Telemetry Listener with Data Collection
"""

from src.f1_telemetry_listener import F1TelemetryListener

if __name__ == "__main__":
    print("\n" + "="*60)
    print("✓ F1 25 Telemetry Listener 起動")
    print("="*60)
    
    listener = F1TelemetryListener(player_car_index=0)
    listener.start(timeout=600)  # 10分間 (600秒)
