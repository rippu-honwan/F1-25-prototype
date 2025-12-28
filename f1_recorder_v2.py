#!/usr/bin/env python3
"""
F1 25 UDP Telemetry Recorder V2
Improved packet parsing based on F1 25 UDP specification
"""

import socket
import struct
import csv
from datetime import datetime
from collections import defaultdict
import os


class F1TelemetryRecorderV2:
    """Record F1 25 UDP telemetry data to CSV with correct parsing"""
    
    def __init__(self, filename=None, track_name="unknown"):
        if filename is None:
            filename = f"telemetry_{track_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        self.filename = filename
        self.track_name = track_name
        
        # Define CSV headers
        self.fieldnames = [
            'timestamp',
            'frame_id',
            'session_time',
            'lap_number',
            'lap_distance',
            'throttle',
            'brake',
            'steering',
            'speed_kph',
            'gear',
            'rpm',
            'drs',
            'ers_deploy_mode',
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
        self.current_lap = 0
        self.current_lap_distance = 0
        
        print(f"🎯 Recording to: {filepath}")
    
    def parse_header(self, data):
        """Parse F1 25 UDP header (first 29 bytes)"""
        if len(data) < 29:
            return None
        
        try:
            # Unpack header with correct format
            # Format: <H B B B B B Q f I I B B
            header = struct.unpack('<H5BQfIIBB', data[0:29])
            
            return {
                'packet_format': header[0],       # uint16
                'game_year': header[1],           # uint8  
                'game_major': header[2],          # uint8
                'game_minor': header[3],          # uint8
                'packet_version': header[4],      # uint8
                'packet_id': header[5],           # uint8 (packet type)
                'session_uid': header[6],         # uint64
                'session_time': header[7],        # float
                'frame_identifier': header[8],    # uint32
                'overall_frame_identifier': header[9],  # uint32
                'player_car_index': header[10],   # uint8
                'secondary_player_car_index': header[11],  # uint8
            }
        except:
            return None
    
    def parse_lap_data(self, data, header):
        """Parse Type 2 (Lap Data) packet"""
        if len(data) < 100:
            return None
        
        try:
            # Skip header (29 bytes)
            offset = 29
            player_index = header['player_car_index']
            
            # Each lap data is 54 bytes, skip to player car
            lap_data_offset = offset + (player_index * 54)
            
            if len(data) < lap_data_offset + 54:
                return None
            
            # Parse player lap data
            lap_data = struct.unpack('<IfHHfHBBHBBBBBBBBfBB', 
                                    data[lap_data_offset:lap_data_offset+54])
            
            return {
                'last_lap_time_ms': lap_data[0],
                'current_lap_time_ms': lap_data[1],
                'sector1_time_ms': lap_data[2],
                'sector1_time_minutes': lap_data[3],
                'sector2_time_ms': lap_data[4],
                'sector2_time_minutes': lap_data[5],
                'lap_distance': lap_data[6],
                'total_distance': lap_data[7],
                'current_lap_num': lap_data[14],
            }
        except:
            return None
    
    def parse_car_telemetry(self, data, header):
        """Parse Type 6 (Car Telemetry) packet"""
        if len(data) < 100:
            return None
        
        try:
            # Skip header (29 bytes)
            offset = 29
            player_index = header['player_car_index']
            
            # Each car telemetry is 60 bytes, skip to player car
            telemetry_offset = offset + (player_index * 60)
            
            if len(data) < telemetry_offset + 60:
                return None
            
            # Parse player telemetry (first 20 bytes contain main data)
            tel_data = data[telemetry_offset:telemetry_offset+60]
            
            speed = struct.unpack('<H', tel_data[0:2])[0]  # uint16 - speed in kph
            throttle = tel_data[2]  # 0-100%
            steer = struct.unpack('<h', tel_data[3:5])[0]  # int16 (-100 to 100)
            brake = tel_data[5]  # 0-100%
            clutch = tel_data[6]  # 0-100%
            gear = struct.unpack('<b', tel_data[7:8])[0]  # int8 (-1 to 8)
            engine_rpm = struct.unpack('<H', tel_data[8:10])[0]  # uint16
            drs = tel_data[10]  # 0 or 1
            
            return {
                'speed_kph': speed,
                'throttle': throttle,
                'steering': steer,
                'brake': brake,
                'gear': gear,
                'rpm': engine_rpm,
                'drs': drs,
            }
        except:
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
            'lap_number': self.current_lap,
            'lap_distance': self.current_lap_distance,
            'throttle': '',
            'brake': '',
            'steering': '',
            'speed_kph': '',
            'gear': '',
            'rpm': '',
            'drs': '',
            'ers_deploy_mode': '',
        }
        
        # Parse based on packet type
        if packet_type == 2:  # Lap Data
            lap_data = self.parse_lap_data(data, header)
            if lap_data:
                self.current_lap = lap_data.get('current_lap_num', self.current_lap)
                self.current_lap_distance = lap_data.get('lap_distance', self.current_lap_distance)
                row['lap_number'] = self.current_lap
                row['lap_distance'] = self.current_lap_distance
                
        elif packet_type == 6:  # Car Telemetry
            telemetry = self.parse_car_telemetry(data, header)
            if telemetry:
                row.update(telemetry)
                # Only write if we have meaningful telemetry data
                if telemetry.get('speed_kph', 0) > 0:
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
            6: "Car Telemetry",
            7: "Car Status",
        }
        
        for ptype in sorted(self.packet_count.keys()):
            if ptype in packet_names:
                name = packet_names[ptype]
                count = self.packet_count[ptype]
                print(f"   Type {ptype:2d} - {name:20s}: {count:5d} packets")


def main():
    print("🎮 F1 25 UDP Telemetry Recorder V2")
    print("=" * 50)
    
    track_name = input("Enter track name (e.g., monza, silverstone): ").strip() or "unknown"
    
    recorder = F1TelemetryRecorderV2(track_name=track_name)
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 20777))
    s.settimeout(600)
    
    print(f"\n📡 Listening for UDP packets...")
    print(f"   Port: 20777")
    print(f"   Track: {track_name}")
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
