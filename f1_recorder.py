#!/usr/bin/env python3
"""
F1 25 UDP Telemetry Recorder
Records real-time telemetry data from F1 25 game via UDP
"""

import socket
import struct
import csv
from datetime import datetime
from collections import defaultdict
import os


class F1TelemetryRecorder:
    """Record F1 25 UDP telemetry data to CSV"""
    
    def __init__(self, filename=None, track_name="unknown"):
        """Initialize recorder
        
        Args:
            filename: Output CSV filename
            track_name: Name of the track (e.g., 'monza', 'silverstone')
        """
        if filename is None:
            filename = f"telemetry_{track_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        self.filename = filename
        self.track_name = track_name
        
        # Define CSV headers
        self.fieldnames = [
            'timestamp',
            'frame_id',
            'lap_number',
            'packet_type',
            'throttle',
            'brake',
            'steering',
            'speed',
            'gear',
            'rpm',
            'drs',
            'lat_g',
            'lon_g',
            'vert_g',
            'position_x',
            'position_y',
            'position_z',
        ]
        
        # Create output directory if needed
        os.makedirs('telemetry_data', exist_ok=True)
        
        # Save to telemetry_data folder
        filepath = os.path.join('telemetry_data', filename)
        self.filepath = filepath
        
        self.csv_file = open(filepath, 'w', newline='')
        self.writer = csv.DictWriter(self.csv_file, fieldnames=self.fieldnames)
        self.writer.writeheader()
        self.csv_file.flush()
        
        self.packet_count = defaultdict(int)
        self.start_time = datetime.now()
        
        print(f"🎯 Recording to: {filepath}")
    
    def parse_car_telemetry(self, data):
        """Parse Type 6 (Car Telemetry) packet
        
        F1 25 UDP Packet Structure (Type 6):
        Header: 24 bytes
        Car telemetry data: m_carTelemetryData[22] (22 cars)
        """
        if len(data) < 100:
            return None
        
        try:
            header_size = 24
            offset = header_size
            
            # Car telemetry structure (simplified)
            throttle = struct.unpack('<B', data[offset:offset+1])[0] if len(data) > offset else 0
            brake = struct.unpack('<B', data[offset+1:offset+2])[0] if len(data) > offset+1 else 0
            steering = struct.unpack('<h', data[offset+2:offset+4])[0] / 32767.0 if len(data) > offset+3 else 0
            
            # RPM
            rpm = struct.unpack('<H', data[offset+4:offset+6])[0] if len(data) > offset+5 else 0
            
            # Speed (kph)
            speed = struct.unpack('<H', data[offset+6:offset+8])[0] if len(data) > offset+7 else 0
            
            # DRS
            drs = struct.unpack('<B', data[offset+8:offset+9])[0] if len(data) > offset+8 else 0
            
            # Gear
            gear = struct.unpack('<b', data[offset+9:offset+10])[0] if len(data) > offset+9 else 0
            
            return {
                'throttle': throttle,
                'brake': brake,
                'steering': round(steering, 3),
                'speed': speed,
                'gear': gear,
                'rpm': rpm,
                'drs': drs,
                'lat_g': '',
                'lon_g': '',
                'vert_g': '',
            }
        except Exception as e:
            print(f"⚠️  Error parsing telemetry: {e}")
            return None
    
    def parse_motion(self, data):
        """Parse Type 0 (Motion) packet"""
        if len(data) < 100:
            return None
        
        try:
            header_size = 24
            offset = header_size
            
            # Position (X, Y, Z)
            pos_x = struct.unpack('<f', data[offset:offset+4])[0] if len(data) > offset+3 else 0
            pos_y = struct.unpack('<f', data[offset+4:offset+8])[0] if len(data) > offset+7 else 0
            pos_z = struct.unpack('<f', data[offset+8:offset+12])[0] if len(data) > offset+11 else 0
            
            return {
                'position_x': round(pos_x, 2),
                'position_y': round(pos_y, 2),
                'position_z': round(pos_z, 2),
            }
        except Exception as e:
            print(f"⚠️  Error parsing motion: {e}")
            return None
    
    def record_packet(self, data):
        """Record a UDP packet"""
        if len(data) < 24:
            return
        
        try:
            # Parse header
            header_data = struct.unpack('<HBBBBBQfII', data[:20])
            frame_id = header_data[8]
            
            packet_type = data[6]
            self.packet_count[packet_type] += 1
            
            row = {
                'timestamp': datetime.now().isoformat(),
                'frame_id': frame_id,
                'lap_number': '',
                'packet_type': packet_type,
                'throttle': '',
                'brake': '',
                'steering': '',
                'speed': '',
                'gear': '',
                'rpm': '',
                'drs': '',
                'lat_g': '',
                'lon_g': '',
                'vert_g': '',
                'position_x': '',
                'position_y': '',
                'position_z': '',
            }
            
            # Parse based on packet type
            if packet_type == 6:  # Car Telemetry
                telemetry = self.parse_car_telemetry(data)
                if telemetry:
                    row.update(telemetry)
                    
            elif packet_type == 0:  # Motion
                motion = self.parse_motion(data)
                if motion:
                    row.update(motion)
            
            # Write to CSV
            self.writer.writerow(row)
            self.csv_file.flush()
            
        except Exception as e:
            print(f"⚠️  Error recording packet: {e}")
    
    def close(self):
        """Close the recorder and print statistics"""
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
            name = packet_names.get(ptype, f"Unknown ({ptype})")
            count = self.packet_count[ptype]
            print(f"   Type {ptype:2d} - {name:20s}: {count:5d} packets")


def main():
    """Main entry point"""
    print("🎮 F1 25 UDP Telemetry Recorder")
    print("=" * 50)
    
    # Get track name
    track_name = input("Enter track name (e.g., monza, silverstone): ").strip() or "unknown"
    
    recorder = F1TelemetryRecorder(track_name=track_name)
    
    # Create UDP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 20777))
    s.settimeout(600)  # 10 minute timeout
    
    print(f"\n📡 Listening for UDP packets...")
    print(f"   Port: 20777")
    print(f"   Track: {track_name}")
    print(f"   Press Ctrl+C to stop\n")
    
    try:
        while True:
            data, addr = s.recvfrom(2048)
            recorder.record_packet(data)
            
            # Show progress every 1000 packets
            total = sum(recorder.packet_count.values())
            if total % 1000 == 0:
                print(f"✓ Recorded {total} packets...")
                
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping recording...")
    finally:
        recorder.close()
        s.close()


if __name__ == "__main__":
    main()
