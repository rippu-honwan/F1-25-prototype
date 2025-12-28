#!/usr/bin/env python3
"""
F1 25 UDP テレメトリー レコーダー
F1 25 から UDP データを受け取ります。
すべてのパケットタイプをファイルに保存します。
"""

import socket
import struct
import csv
from datetime import datetime
from collections import defaultdict
import os


class F1テレメトリーレコーダー:
    """F1 25 の UDP データをすべて保存します。
    
    パケットを受け取って、CSV ファイルに書き込みます。
    - packet_type: パケットの種類
    - packet_hex: パケットの生データ
    - speed_kph: 速度
    - throttle: アクセル
    - brake: ブレーキ
    - rpm: エンジン回転数
    """
    
    def __init__(self, filename=None, track_name="unknown"):
        """初期化します。ファイルを作ります。
        
        Args:
            filename: ファイル名 (指定しない場合は自動生成)
            track_name: サーキット名 (例: 'monza', 'silverstone')
        """
        if filename is None:
            filename = f"telemetry_{track_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        self.filename = filename
        self.track_name = track_name
        
        # CSV の欄を決めます
        self.fieldnames = [
            'timestamp',      # 日時
            'frame_id',       # フレーム番号
            'packet_type',    # パケットの種類 (0-15)
            'packet_size',    # パケットのサイズ
            'packet_hex',     # パケットの生データ (16進数)
            'speed_kph',      # 速度 (時速)
            'throttle',       # アクセル (0-100%)
            'brake',          # ブレーキ (0-100%)
            'steering',       # ハンドル (-1.0 ～ 1.0)
            'rpm',            # エンジン回転数
            'gear',           # ギア (1-8)
            'drs',            # DRS (空力翼)
        ]
        
        # フォルダを作ります
        os.makedirs('telemetry_data', exist_ok=True)
        filepath = os.path.join('telemetry_data', filename)
        self.filepath = filepath
        
        # ファイルを開きます
        self.csv_file = open(filepath, 'w', newline='')
        self.writer = csv.DictWriter(self.csv_file, fieldnames=self.fieldnames)
        self.writer.writeheader()
        self.csv_file.flush()
        
        # パケット数をカウントします
        self.packet_count = defaultdict(int)
        self.start_time = datetime.now()
        
        print(f"🏎️  ファイルに保存します: {filepath}")
        print(f"   モード: 完全 (すべてのパケットタイプ)")
    
    def parse_header(self, data):
        """UDP パケットのヘッダーを読みます。
        
        ヘッダーは 29 バイトです。
        - packet_id: パケットの種類 (0-15)
        - frame_identifier: フレーム番号
        
        Args:
            data: UDP パケットのバイト列
            
        Returns:
            ヘッダー情報の辞書、または None
        """
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
        """パケットから運転データを読みます。
        
        Type 6 パケットには以下のデータが含まれます:
        - speed_kph: 速度
        - throttle: アクセルの位置 (0-100)
        - brake: ブレーキの位置 (0-100)
        - rpm: エンジンの回転数
        - steering: ハンドルの角度
        
        Args:
            data: UDP パケットのバイト列
            player_index: プレイヤーのカー番号 (デフォルト: 0)
            
        Returns:
            運転データの辞書
        """
        if len(data) < 100:
            return {}
        
        try:
            offset = 29  # ヘッダーの後から
            
            # 速度を読みます (2 バイト)
            speed = struct.unpack('<H', data[offset:offset+2])[0]
            
            # ブレーキを読みます (1 バイト)
            brake = data[offset + 21]
            
            # アクセルを読みます (1 バイト)
            throttle = data[offset + 19]
            
            # RPM を読みます (2 バイト)
            rpm = struct.unpack('<H', data[offset+22:offset+24])[0]
            # RPM を正しい値に変換します
            rpm = rpm * 20 if 300 < rpm < 1500 else rpm
            
            # ハンドルを読みます (2 バイト、符号付き)
            try:
                steering_raw = struct.unpack('<h', data[offset+20:offset+22])[0]
                steering = steering_raw / 32767.0  # -1.0 ～ 1.0 に変換
            except:
                steering = 0
            
            # DRS と ギア
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
        """UDP パケットを 1 つ保存します。
        
        Args:
            data: UDP パケットのバイト列
        """
        header = self.parse_header(data)
        if not header:
            return
        
        packet_type = header['packet_id']
        self.packet_count[packet_type] += 1
        
        # パケットを 16 進数に変換
        packet_hex = data.hex()
        
        # 行を作ります
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
        
        # Type 6 の場合、運転データを読みます
        if packet_type == 6:
            telemetry = self.parse_telemetry_data(data)
            if telemetry and telemetry.get('speed_kph', 0) > 0:
                row.update(telemetry)
        
        # ファイルに書き込みます
        self.writer.writerow(row)
        self.csv_file.flush()
    
    def close(self):
        """ファイルを閉じます。統計を表示します。"""
        self.csv_file.close()
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        print(f"\n✅ 保存が完了しました!")
        print(f"   ファイル: {self.filepath}")
        print(f"   時間: {elapsed:.1f} 秒")
        print(f"\n📊 パケット統計:")
        
        total = sum(self.packet_count.values())
        print(f"   合計: {total} 個")
        
        # パケットの種類の名前
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
        
        # パケット数を表示します
        for ptype in sorted(self.packet_count.keys()):
            if ptype in packet_names:
                name = packet_names[ptype]
                count = self.packet_count[ptype]
                print(f"   Type {ptype:2d} - {name:20s}: {count:6d} 個")
            else:
                count = self.packet_count[ptype]
                print(f"   Type {ptype:2d} - 不明                : {count:6d} 個")


def main():
    """メインプログラム。UDP を聞きます。"""
    print("🏎️  F1 25 UDP テレメトリー レコーダー")
    print("=" * 50)
    
    # サーキット名を入力
    track_name = input("サーキット名を入力してください: ").strip() or "unknown"
    
    # レコーダーを作ります
    recorder = F1テレメトリーレコーダー(track_name=track_name)
    
    # UDP ソケットを作ります
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 20777))
    s.settimeout(600)
    
    print(f"\n📡 ポート 20777 を聞きます...")
    print(f"   Ctrl+C を押して停止してください\n")
    
    try:
        while True:
            data, addr = s.recvfrom(2048)
            recorder.record_packet(data)
            
            total = sum(recorder.packet_count.values())
            if total > 0 and total % 500 == 0:
                print(f"✓ {total} 個のパケットを保存しました...")
                
    except KeyboardInterrupt:
        print("\n\n⏹️  停止します...")
    finally:
        recorder.close()
        s.close()


if __name__ == "__main__":
    main()
