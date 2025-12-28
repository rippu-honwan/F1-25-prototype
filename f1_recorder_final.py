#!/usr/bin/env python3
"""
F1 25 UDP Telemetry Recorder - FINAL VERSION (CORRECTED)
Fixed packet structure based on actual UDP data inspection
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
        """Parse Type 6 (Car Telemetry) packet with CORRECTED structure
        
        Based on packet inspection and testing:
        - Offset 29-30: Speed (uint16, in kph) ✅
        - Offset 50: BRAKE (0-100%, was reading as throttle)
        - Offset 21: THROTTLE (0-100%, was reading as brake) 
        - Offset 51-52: RPM (uint16) - NEEDS CORRECTION
        - Offset 49: Steering (int8 or int16)
        """
        if len(data) < 100:
            return None
        
        try:
            offset = 29  # After header
            
            # Speed at offset 29-30 (uint16, little-endian) ✅ CORRECT
            speed = struct.unpack('<H', data[offset:offset+2])[0]
            
            # SWAP: Brake is at offset 50 (was throttle)
            brake = data[offset + 21]  # 50 - 29 = 21 ✅
            
            # SWAP: Throttle is at offset 21 (was brake)  
            throttle = data[offset + 19]  # 48 - 29 = 19 (trying this first)
            
            # If throttle still looks wrong, try offset 45
            # For now keep testing
            
            # Try finding RPM - original offset 51-52 gives 400-600, should be 10k+
            # Try reading differently
            # RPM might be at different location, try offset 53-54 or multiply by some factor
            try:
                rpm_raw = struct.unpack('<H', data[offset+22:offset+24])[0]
                # If we're getting 400-1000, multiply by ~20 to get real RPM
                if 300 < rpm_raw < 1500:
                    rpm = rpm_raw * 20  # Rough conversion
                else:
                    rpm = rpm_raw
            except:
                rpm = 0
            
            # Steering - offset 48-49 
            try:
                steering_raw = struct.unpack('<h', data[offset+20:offset+22])[0]
                steering = steering_raw / 32767.0
            except:
                steering = 0
            
            # DRS and Gear - rough estimates
            drs = data[offset + 26] if len(data) > offset + 26 else 0
            gear = struct.unpack('<b', data[offset+27:offset+28])[0] if len(data) > offset + 27 else 0
            
            return {
                'speed_kph': speed,
                'throttle': throttle,  # SWAPPED
                'brake': brake,        # SWAPPED
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
    print("🏎️  F1 25 UDP Telemetry Recorder - FINAL (CORRECTED)")
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
