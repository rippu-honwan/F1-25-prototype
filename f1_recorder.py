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
            'packet_type',
            'throttle',
            'brake',
            'steering',
            'speed',
            'gear',
            'rpm',
            'drs',
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
    
    def parse_header(self, data):
        """Parse F1 25 UDP header (24 bytes)
        
        Structure:
        Bytes 0-1:   Packet format (2025)
        Bytes 2:     Game year (25)
        Bytes 3:     Game version major
        Bytes 4:     Game version minor  
        Bytes 5:     Packet version
        Bytes 6:     Packet ID (Type)
        Bytes 7-14:  Session UID
        Bytes 15-22: Session time (float)
        Bytes 23-26: Frame ID
        """
        if len(data) < 24:
            return None
        
        try:
            # Safe unpacking with error handling
            packet_format = struct.unpack('<H', data[0:2])[0]
            game_year = data[2]
            packet_version = data[5]
            packet_type = data[6]
            frame_id = struct.unpack('<I', data[16:20])[0]
            
            return {
                'packet_format': packet_format,
                'game_year': game_year,
                'packet_version': packet_version,
                'packet_type': packet_type,
                'frame_id': frame_id,
            }
        except Exception as e:
            print(f"⚠️  Header parse error: {e}")
            return None
    
    def parse_car_telemetry(self, data):
        """Parse Type 6 (Car Telemetry) packet
        
        Simplified parsing - just get basic values
        """
        if len(data) < 100:
            return None
        
        try:
            header_size = 24
            offset = header_size
            
            # Safe extraction with bounds checking
            telemetry = {}
            
            # Throttle (byte)
            if len(data) > offset:
                telemetry['throttle'] = data[offset]
            
            # Brake (byte)
            if len(data) > offset + 1:
                telemetry['brake'] = data[offset + 1]
            
            # Steering (short, convert to -1.0 to 1.0)
            if len(data) > offset + 3:
                steering_raw = struct.unpack('<h', data[offset+2:offset+4])[0]
                telemetry['steering'] = round(steering_raw / 32767.0, 3)
            
            # RPM (ushort)
            if len(data) > offset + 5:
                telemetry['rpm'] = struct.unpack('<H', data[offset+4:offset+6])[0]
            
            # Speed (ushort, kph)
            if len(data) > offset + 7:
                telemetry['speed'] = struct.unpack('<H', data[offset+6:offset+8])[0]
            
            # DRS (byte)
            if len(data) > offset + 8:
                telemetry['drs'] = data[offset + 8]
            
            # Gear (signed byte)
            if len(data) > offset + 9:
                telemetry['gear'] = struct.unpack('<b', data[offset+9:offset+10])[0]
            
            return telemetry
            
        except Exception as e:
            return None
    
    def parse_motion(self, data):
        """Parse Type 0 (Motion) packet"""
        if len(data) < 100:
            return None
        
        try:
            header_size = 24
            offset = header_size
            
            motion = {}
            
            # Position X (float)
            if len(data) > offset + 3:
                motion['position_x'] = round(struct.unpack('<f', data[offset:offset+4])[0], 2)
            
            # Position Y (float)
            if len(data) > offset + 7:
                motion['position_y'] = round(struct.unpack('<f', data[offset+4:offset+8])[0], 2)
            
            # Position Z (float)
            if len(data) > offset + 11:
                motion['position_z'] = round(struct.unpack('<f', data[offset+8:offset+12])[0], 2)
            
            return motion
            
        except Exception as e:
            return None
    
    def record_packet(self, data):
        """Record a UDP packet"""
        if len(data) < 24:
            return
        
        try:
            # Parse header safely
            header = self.parse_header(data)
            if not header:
                return
            
            packet_type = header['packet_type']
            self.packet_count[packet_type] += 1
            
            row = {
                'timestamp': datetime.now().isoformat(),
                'frame_id': header['frame_id'],
                'packet_type': packet_type,
                'throttle': '',
                'brake': '',
                'steering': '',
                'speed': '',
                'gear': '',
                'rpm': '',
                'drs': '',
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
            
            # Write to CSV only if we have meaningful data
            if any(row.get(field) != '' for field in self.fieldnames if field not in ['timestamp', 'frame_id', 'packet_type']):
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
        packet_errors = 0
        while True:
            data, addr = s.recvfrom(2048)
            recorder.record_packet(data)
            
            # Show progress every 500 packets
            total = sum(recorder.packet_count.values())
            if total > 0 and total % 500 == 0:
                print(f"✓ Recorded {total} packets...")
                # Print current packet type distribution
                types_str = ", ".join([f"T{t}:{recorder.packet_count[t]}" for t in sorted(recorder.packet_count.keys())])
                print(f"  Types: {types_str}")
                
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping recording...")
    finally:
        recorder.close()
        s.close()


if __name__ == "__main__":
    main()
