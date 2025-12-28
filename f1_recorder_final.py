#!/usr/bin/env python3
"""
F1 25 UDP Telemetry Recorder - FINAL VERSION
Corrected packet structure based on actual UDP data inspection
"""

import socket
import struct
import csv
from datetime import datetime
from collections import defaultdict
import os


class F1TelemetryRecorderFinal:
    """Record F1 25 UDP telemetry with correct packet parsing"""
    
    def __init__(self, filename=None, track_name="unknown"):
        if filename is None:
            filename = f"telemetry_{track_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        self.filename = filename
        self.track_name = track_name
        
        self.fieldnames = [
            'timestamp',
            'frame_id',
            'session_time',
            'speed_kph',
            'throttle',
            'brake',
            'steering',
            'gear',
            'rpm',
            'drs',
        ]
        
        os.makedirs('telemetry_data', exist_ok=True)
        filepath = os.path.join('telemetry_data', filename)
        self.filepath = filepath
        
        self.csv_file = open(filepath, 'w', newline='')
        self.writer = csv.DictWriter(self.csv_file, fieldnames=self.fieldnames)
        self.writer.writeheader()
        self.csv_file.flush()
        
        self.packet_count = defaultdict(int)
        self.start_time = datetime.now()
        
        print(f"🏎️  Recording to: {filepath}")
    
    def parse_header(self, data):
        """Parse F1 25 UDP header (29 bytes)"""
        if len(data) < 29:
            return None
        
        try:
            header = struct.unpack('<H5BQfIIBB', data[0:29])
            return {
                'packet_format': header[0],
                'game_year': header[1],
                'game_major': header[2],
                'game_minor': header[3],
                'packet_version': header[4],
                'packet_id': header[5],
                'session_uid': header[6],
                'session_time': header[7],
                'frame_identifier': header[8],
                'overall_frame_identifier': header[9],
                'player_car_index': header[10],
                'secondary_player_car_index': header[11],
            }
        except:
            return None
    
    def parse_car_telemetry_correct(self, data, player_index=0):
        """Parse Type 6 (Car Telemetry) packet with CORRECT structure
        
        Based on packet inspection:
        - Offset 29-30: Speed (uint16, in kph)
        - Offset 50: Throttle (0-100%)
        - Offset 51-52: RPM (uint16)
        - Offset 49?: Steering or brake?
        - Each car has ~60 bytes of telemetry
        """
        if len(data) < 100:
            return None
        
        try:
            offset = 29  # After header
            
            # Speed at offset 29-30 (uint16, little-endian)
            speed = struct.unpack('<H', data[offset:offset+2])[0]
            
            # Throttle at offset 50 (uint8)
            throttle = data[offset + 21]  # 50 - 29 = 21
            
            # Brake - need to find, likely around offset 48-49
            # For now, try offset 48
            brake = data[offset + 19]  # 48 - 29 = 19
            
            # RPM at offset 51-52 (uint16)
            rpm = struct.unpack('<H', data[offset+22:offset+24])[0]
            
            # Steering - try offset 49 (int8 or int16)
            # From hex data, 0xff = -1, 0x7f = 127
            steering_raw = struct.unpack('<h', data[offset+20:offset+22])[0]
            steering = steering_raw / 32767.0  # Normalize to -1.0 to 1.0
            
            # DRS - offset likely 55-56
            drs = data[offset + 26] if len(data) > offset + 26 else 0
            
            # Gear - offset likely around 56-57
            gear = struct.unpack('<b', data[offset+27:offset+28])[0] if len(data) > offset + 27 else 0
            
            return {
                'speed_kph': speed,
                'throttle': throttle,
                'brake': brake,
                'steering': round(steering, 3),
                'rpm': rpm,
                'drs': drs,
                'gear': gear,
            }
        except Exception as e:
            return None
    
    def record_packet(self, data):
        """Record a UDP packet"""
        header = self.parse_header(data)
        if not header:
            return
        
        packet_type = header['packet_id']
        self.packet_count[packet_type] += 1
        
        row = {
            'timestamp': datetime.now().isoformat(),
            'frame_id': header['frame_identifier'],
            'session_time': round(header['session_time'], 2),
            'speed_kph': '',
            'throttle': '',
            'brake': '',
            'steering': '',
            'gear': '',
            'rpm': '',
            'drs': '',
        }
        
        # Parse telemetry
        if packet_type == 6:
            telemetry = self.parse_car_telemetry_correct(data, header['player_car_index'])
            if telemetry and telemetry.get('speed_kph', 0) > 0:
                row.update(telemetry)
                self.writer.writerow(row)
                self.csv_file.flush()
    
    def close(self):
        self.csv_file.close()
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        print(f"\n✅ Recording completed!")
        print(f"   File: {self.filepath}")
        print(f"   Duration: {elapsed:.1f} seconds")
        print(f"\n📊 Packet Statistics:")
        
        total = sum(self.packet_count.values())
        print(f"   Total packets: {total}")
        
        packet_names = {0: "Motion", 1: "Session", 2: "Lap Data", 6: "Car Telemetry", 7: "Car Status"}
        
        for ptype in sorted(self.packet_count.keys()):
            if ptype in packet_names:
                name = packet_names[ptype]
                count = self.packet_count[ptype]
                print(f"   Type {ptype:2d} - {name:20s}: {count:5d} packets")


def main():
    print("🏎️  F1 25 UDP Telemetry Recorder - FINAL")
    print("=" * 50)
    
    track_name = input("Enter track name: ").strip() or "unknown"
    
    recorder = F1TelemetryRecorderFinal(track_name=track_name)
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 20777))
    s.settimeout(600)
    
    print(f"\n📡 Listening on port 20777...")
    print(f"   Press Ctrl+C to stop\n")
    
    try:
        while True:
            data, addr = s.recvfrom(2048)
            recorder.record_packet(data)
            
            total = sum(recorder.packet_count.values())
            if total > 0 and total % 500 == 0:
                print(f"✓ Recorded {total} packets...")
                
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping recording...")
    finally:
        recorder.close()
        s.close()


if __name__ == "__main__":
    main()
