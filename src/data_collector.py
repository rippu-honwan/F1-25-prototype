"""
F1 25 Telemetry Data Collector
Packet を受け符わせて CSV に保存する
"""

import csv
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from .packet_parser import PacketParser, PacketType
from .telemetry_packets import LapDataPacket, CarTelemetryPacket


class TelemetryDataCollector:
    """F1 25 Telemetry データを収集して CSV に保存"""
    
    def __init__(self, output_dir: str = "data", player_car_index: int = 0):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.player_car_index = player_car_index
        
        # ティメトリーデータを上佳の頵序で阳上げる
        self.frame_data = {}
        
        # 託費リクエスト
        self.lap_data_frames = set()
        self.car_telemetry_frames = set()
        
        # 統計
        self.total_packets = 0
        self.lap_data_count = 0
        self.car_telemetry_count = 0
    
    def process_packet(self, data: bytes) -> bool:
        """UDP Packet を受け取り、データを抽出"""
        self.total_packets += 1
        
        try:
            # Header を解析して Packet Type を識別
            header = PacketParser.parse_header(data)
            if not header:
                return False
            
            frame_id = header.frame_identifier
            
            # Frame ごとの辞書を初期化
            if frame_id not in self.frame_data:
                self.frame_data[frame_id] = {
                    'frame_id': frame_id,
                    'timestamp': header.session_time,
                    'lap_data': None,
                    'telemetry': None,
                }
            
            # Packet Type ごとに処理
            if header.packet_type == PacketType.LAP_DATA:
                lap_data = LapDataPacket.parse_lap_data(data, self.player_car_index)
                if lap_data:
                    self.frame_data[frame_id]['lap_data'] = lap_data
                    self.lap_data_count += 1
                    self.lap_data_frames.add(frame_id)
            
            elif header.packet_type == PacketType.CAR_TELEMETRY:
                telemetry = CarTelemetryPacket.parse_car_telemetry(data, self.player_car_index)
                if telemetry:
                    self.frame_data[frame_id]['telemetry'] = telemetry
                    self.car_telemetry_count += 1
                    self.car_telemetry_frames.add(frame_id)
            
            return True
        
        except Exception as e:
            print(f"エラー: Packet 処理失敗 - {e}")
            return False
    
    def save_to_csv(self, filename: Optional[str] = None) -> Path:
        """CSV ファイルに保存"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"f1_telemetry_{timestamp}.csv"
        
        output_path = self.output_dir / filename
        
        # 並べ理をポブ粗いを割り形を整理して、佳い出力を生成
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # ヘッダー
            writer.writerow([
                'Frame', 'Time(s)', 'Speed(km/h)', 'Throttle', 'Brake', 'Steer',
                'Gear', 'RPM', 'DRS', 'BrakesTemp(C)', 'TyresTemp(C)', 'TyresPressure(kPa)',
                'LapNum', 'LapTime(ms)', 'LastLapTime(ms)', 'Sector1(ms)', 'Sector2(ms)',
                'LapDistance(m)', 'TotalDistance(m)', 'CarPosition'
            ])
            
            # データを上佳の頵序で連等ごとに書き込み
            for frame_id in sorted(self.frame_data.keys()):
                frame = self.frame_data[frame_id]
                lap = frame['lap_data']
                telem = frame['telemetry']
                
                # 両方のデータがいれば学習
                if lap and telem:
                    writer.writerow([
                        frame_id,
                        f"{frame['timestamp'] / 1000:.2f}",  # 空時間 (s)
                        telem.speed,
                        f"{telem.throttle:.3f}",
                        f"{telem.brake:.3f}",
                        f"{telem.steer:.3f}",
                        telem.gear,
                        telem.engine_rpm,
                        int(telem.drs_open),
                        f"{telem.brakes_temp[0]:.1f}",  # 前輊の决平
                        f"{sum(telem.tyres_surface_temp) / 4:.1f}",  # タイヤ温度平均
                        f"{sum(telem.tyres_pressure) / 4:.1f}",  # タイヤ気圧平均
                        lap.current_lap_num,
                        lap.current_lap_time_in_ms,
                        lap.last_lap_time_in_ms,
                        lap.sector_1_time_in_ms,
                        lap.sector_2_time_in_ms,
                        f"{lap.lap_distance:.1f}",
                        f"{lap.total_distance:.1f}",
                        lap.car_position,
                    ])
        
        return output_path
    
    def print_stats(self):
        """収集情報を出力"""
        print(f"\n{'='*60}")
        print(f"✓ データ収集完了")
        print(f"{'='*60}")
        print(f"総 Packet 数: {self.total_packets}")
        print(f"Lap Data Packet: {self.lap_data_count}")
        print(f"Car Telemetry Packet: {self.car_telemetry_count}")
        print(f"総フレーム数: {len(self.frame_data)}")
        print(f"完全なデータ (Lap + Telemetry): {len(self.lap_data_frames & self.car_telemetry_frames)}")
        print(f"上佳値輹出ディレクトリ: {self.output_dir.absolute()}")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    print("✓ Data Collector モジュール読み込み完了")
