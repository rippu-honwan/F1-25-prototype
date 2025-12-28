#!/usr/bin/env python3
"""
F1 25 UDP Telemetry Recorder - UNIVERSAL VERSION
Captures ALL packet types with raw binary data for future extensibility
"""

import socket
import struct
import csv
from datetime import datetime
from collections import defaultdict
import os


class F1TelemetryRecorderUniversal:
    """Record F1 25 UDP data with all packet types preserved"""
    
    def __init__(self, filename=None, track_name="unknown"):
        if filename is None:
            filename = f"telemetry_{track_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        self.filename = filename
        self.track_name = track_name
        
        # Store raw packets for future parsing
        self.fieldnames = [
            'timestamp',
            'frame_id',
            'packet_type',
            'packet_size',
            'packet_hex',
            'speed_kph',
            'throttle',
            'brake',
            'steering',
            'rpm',
            'gear',
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
        print(f"   Mode: UNIVERSAL (all packet types with raw data)")
    
    def parse_header(self, data):
        """Parse F1 25 UDP header (29 bytes)"""
        if len(data) < 29:
            return None
        
        try:
            header = struct.unpack('<H5BQfIIBB', data[0:29])
            return {
                'packet_format': header[0],
                'game_year': header[1],
                'packet_id': header[5],
                'session_time': header[7],
                'frame_identifier': header[8],
                'player_car_index': header[10],
            }
        except:
            return None
    
    def parse_telemetry_data(self, data, player_index=0):
        """Extract telemetry from Type 6 packet (for CSV columns)"""
        if len(data) < 100:
            return {}
        
        try:
            offset = 29
            
            speed = struct.unpack('<H', data[offset:offset+2])[0]
            brake = data[offset + 21]
            throttle = data[offset + 19]
            rpm = struct.unpack('<H', data[offset+22:offset+24])[0]
            rpm = rpm * 20 if 300 < rpm < 1500 else rpm
            
            try:
                steering_raw = struct.unpack('<h', data[offset+20:offset+22])[0]
                steering = steering_raw / 32767.0
            except:
                steering = 0
            
            drs = data[offset + 26] if len(data) > offset + 26 else 0
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
        except:
            return {}
    
    def record_packet(self, data):
        """Record any UDP packet with raw data"""
        header = self.parse_header(data)
        if not header:
            return
        
        packet_type = header['packet_id']
        self.packet_count[packet_type] += 1
        
        # Convert packet to hex for storage
        packet_hex = data.hex()
        
        row = {
            'timestamp': datetime.now().isoformat(),
            'frame_id': header['frame_identifier'],
            'packet_type': packet_type,
            'packet_size': len(data),
            'packet_hex': packet_hex,
            'speed_kph': '',
            'throttle': '',
            'brake': '',
            'steering': '',
            'rpm': '',
            'gear': '',
            'drs': '',
        }
        
        # Extract telemetry if Type 6
        if packet_type == 6:
            telemetry = self.parse_telemetry_data(data)
            if telemetry and telemetry.get('speed_kph', 0) > 0:
                row.update(telemetry)
        
        # Write all packets (both with and without extracted data)
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
        
        packet_names = {
            0: "Motion",
            1: "Session",
            2: "Lap Data",
            5: "Time Trial",
            6: "Car Telemetry",
            7: "Car Status",
            10: "Car Damage",
            11: "Session History",
            12: "Tyre Sets",
            13: "Motion Ex",
        }
        
        for ptype in sorted(self.packet_count.keys()):
            if ptype in packet_names:
                name = packet_names[ptype]
                count = self.packet_count[ptype]
                print(f"   Type {ptype:2d} - {name:20s}: {count:6d} packets")
            else:
                count = self.packet_count[ptype]
                print(f"   Type {ptype:2d} - Unknown              : {count:6d} packets")
        
        print(f"\n📋 Raw packet data stored in: packet_hex column")
        print(f"   Use for future parsing of additional packet types")


def main():
    print("🏎️  F1 25 UDP Telemetry Recorder - UNIVERSAL")
    print("=" * 50)
    
    track_name = input("Enter track name: ").strip() or "unknown"
    
    recorder = F1TelemetryRecorderUniversal(track_name=track_name)
    
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
