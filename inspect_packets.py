#!/usr/bin/env python3
"""
F1 25 UDP Packet Inspector
Inspect raw packet data to understand structure
"""

import socket
import struct
import sys


def inspect_header(data):
    """Inspect packet header"""
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


def inspect_telemetry_packet(data, player_index=0):
    """Inspect Type 6 (Car Telemetry) packet structure"""
    if len(data) < 100:
        return
    
    print("\n" + "="*60)
    print("Type 6 - Car Telemetry Packet")
    print("="*60)
    
    # Skip header
    offset = 29
    
    # Try to find telemetry data structure
    # Each car has telemetry, player car is at index player_index
    
    print(f"\nPlayer car index: {player_index}")
    print(f"Data size: {len(data)} bytes")
    print(f"After header: {len(data) - 29} bytes")
    
    # Show first 200 bytes after header in hex
    print(f"\nFirst 100 bytes after header (hex):")
    for i in range(offset, min(offset + 100, len(data)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
        print(f"  Offset {i:4d}: {hex_str}")
    
    # Try different interpretations
    print(f"\n" + "-"*60)
    print("Attempting different data interpretations:")
    print("-"*60)
    
    # Try reading as unsigned shorts (2 bytes each)
    print(f"\nAs uint16 (2-byte values):")
    for i in range(offset, min(offset + 40, len(data)), 2):
        if i + 2 <= len(data):
            val = struct.unpack('<H', data[i:i+2])[0]
            print(f"  Offset {i:4d}: {val:6d} (0x{val:04x})")
    
    # Try reading as bytes
    print(f"\nAs uint8 (1-byte values):")
    for i in range(offset, min(offset + 40, len(data))):
        val = data[i]
        print(f"  Offset {i:4d}: {val:3d} (0x{val:02x})")


def main():
    print("🔍 F1 25 UDP Packet Inspector")
    print("=" * 60)
    print("This tool will capture and display raw packet structure.")
    print("Press Ctrl+C after capturing a few packets.\n")
    
    # Create UDP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 20777))
    s.settimeout(10)
    
    print("📡 Listening on port 20777...")
    print("Start F1 25 and drive around.\n")
    
    telemetry_count = 0
    max_inspect = 3  # Only inspect first 3 telemetry packets
    
    try:
        while telemetry_count < max_inspect:
            try:
                data, addr = s.recvfrom(2048)
                
                header = inspect_header(data)
                if not header:
                    continue
                
                packet_type = header['packet_id']
                
                # Only inspect telemetry packets
                if packet_type == 6:
                    telemetry_count += 1
                    print(f"\n✅ Captured Telemetry Packet #{telemetry_count}")
                    print(f"   Frame: {header['frame_identifier']}")
                    print(f"   Session time: {header['session_time']:.2f}s")
                    
                    inspect_telemetry_packet(data, header['player_car_index'])
                    
                    if telemetry_count >= max_inspect:
                        print(f"\n\n✅ Captured {max_inspect} telemetry packets.")
                        break
                        
            except socket.timeout:
                print("⚠️  Timeout waiting for packets. Is F1 25 running?")
                break
                
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user.")
    finally:
        s.close()
    
    print("\n" + "="*60)
    print("🔍 Inspection complete!")
    print("="*60)


if __name__ == "__main__":
    main()
