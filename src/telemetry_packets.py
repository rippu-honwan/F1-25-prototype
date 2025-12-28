"""
F1 25 Telemetry Packet Structures
Packet 2 (Lap Data) と Packet 6 (Car Telemetry) を定義
"""

import struct
from dataclasses import dataclass
from typing import List


@dataclass
class LapData:
    """Lap Data 統計 (Packet 2 内の各車輋用)"""
    last_lap_time_in_ms: int          # 前回のラップ時間 (ms)
    current_lap_time_in_ms: int       # 現在のラップ時間 (ms)
    sector_1_time_in_ms: int          # Sector 1 時間
    sector_1_time_minutes: int        # Sector 1 分賽版
    sector_2_time_in_ms: int          # Sector 2 時間
    sector_2_time_minutes: int        # Sector 2 分賽版
    delta_to_car_in_front: float      # 前車までの時間差
    delta_to_race_leader: float       # レースリーダーまでの時間差
    lap_distance: float               # 現在のラップトラック上の位置 (m)
    total_distance: float             # 総走行距離 (m)
    safety_car_delta: float           # SC delta
    car_position: int                 # グリッド上の位置
    current_lap_num: int              # 現在のラップ番号
    pit_status: int                   # Pit Status
    num_pit_stops: int                # Pit Stop 回数
    finished: bool                    # 完了したか
    
    def __repr__(self):
        return (
            f"Lap(lap#{self.current_lap_num}, "
            f"time={self.current_lap_time_in_ms}ms, "
            f"dist={self.total_distance:.1f}m)"
        )


@dataclass
class CarTelemetry:
    """Car Telemetry データ (Packet 6 内の各車輋用)"""
    speed: int                        # 速度 (km/h)
    throttle: float                   # アクセル適用 (0.0-1.0)
    steer: float                      # ハンドル作用 (-1.0 to 1.0)
    brake: float                      # ブレーキ適用 (0.0-1.0)
    clutch: int                       # クラッチ (0-100)
    gear: int                         # 現在のギア
    engine_rpm: int                   # エンジン RPM
    drs_open: bool                    # DRS オープン
    rev_lights_percent: int           # Rev lights (看)
    brakes_temp: tuple                # ブレーキ温度 (前後左右, 度C)
    tyres_surface_temp: tuple         # タイヤ表面温度
    tyres_inner_temp: tuple           # タイヤ内部温度
    tyres_pressure: tuple             # タイヤ気右 (kPa)
    
    def __repr__(self):
        return (
            f"Telemetry(speed={self.speed}km/h, "
            f"throttle={self.throttle:.2f}, "
            f"brake={self.brake:.2f}, "
            f"rpm={self.engine_rpm})"
        )


class LapDataPacket:
    """Packet 2: Lap Data Parser"""
    
    HEADER_SIZE = 24
    # 各車輋ごとのデータサイズ (bytes)
    SINGLE_CAR_SIZE = 82
    
    FORMAT_STRING = "<IffIIffffIBBBBB"
    
    @staticmethod
    def parse_lap_data(data: bytes, car_index: int = 0) -> LapData:
        """特定の車輋の Lap Data を解析"""
        if car_index < 0 or car_index >= 20:
            raise ValueError(f"車輋インデックスが不正: {car_index}")
        
        # 車輋ごとのデータを抽出
        start = LapDataPacket.HEADER_SIZE + (car_index * LapDataPacket.SINGLE_CAR_SIZE)
        end = start + LapDataPacket.SINGLE_CAR_SIZE
        
        if len(data) < end:
            return None
        
        car_data = data[start:end]
        
        try:
            unpacked = struct.unpack(LapDataPacket.FORMAT_STRING, car_data[:74])
            
            return LapData(
                last_lap_time_in_ms=unpacked[0],
                current_lap_time_in_ms=unpacked[1],
                sector_1_time_in_ms=unpacked[2],
                sector_1_time_minutes=unpacked[3],
                sector_2_time_in_ms=unpacked[4],
                sector_2_time_minutes=unpacked[5],
                delta_to_car_in_front=unpacked[6],
                delta_to_race_leader=unpacked[7],
                lap_distance=unpacked[8],
                total_distance=unpacked[9],
                safety_car_delta=unpacked[10],
                car_position=unpacked[11],
                current_lap_num=unpacked[12],
                pit_status=unpacked[13],
                num_pit_stops=unpacked[14],
                finished=bool(unpacked[15]),
            )
        except Exception as e:
            print(f"エラー: Lap Data 解析失敗 - {e}")
            return None


class CarTelemetryPacket:
    """Packet 6: Car Telemetry Parser"""
    
    HEADER_SIZE = 24
    # 各車輋ごとのテレメトリーデータサイズ
    SINGLE_CAR_SIZE = 68
    
    FORMAT_STRING = "<HfffffBHBBBBBBBBBBBBBBBBffffff"
    
    @staticmethod
    def parse_car_telemetry(data: bytes, car_index: int = 0) -> CarTelemetry:
        """特定の車輋の Telemetry を解析"""
        if car_index < 0 or car_index >= 20:
            raise ValueError(f"車輋インデックスが不正: {car_index}")
        
        # 車輋ごとのデータを抽出
        start = CarTelemetryPacket.HEADER_SIZE + (car_index * CarTelemetryPacket.SINGLE_CAR_SIZE)
        end = start + CarTelemetryPacket.SINGLE_CAR_SIZE
        
        if len(data) < end:
            return None
        
        car_data = data[start:end]
        
        try:
            unpacked = struct.unpack(CarTelemetryPacket.FORMAT_STRING, car_data)
            
            return CarTelemetry(
                speed=unpacked[0],
                throttle=unpacked[1],
                steer=unpacked[2],
                brake=unpacked[3],
                clutch=unpacked[4],
                gear=unpacked[5],
                engine_rpm=unpacked[6],
                drs_open=bool(unpacked[7]),
                rev_lights_percent=unpacked[8],
                brakes_temp=(
                    unpacked[9],   # 前後
                    unpacked[10],  # 左右
                    unpacked[11],
                    unpacked[12],
                ),
                tyres_surface_temp=(
                    unpacked[13], unpacked[14], unpacked[15], unpacked[16],  # RL, RR, FL, FR
                ),
                tyres_inner_temp=(
                    unpacked[17], unpacked[18], unpacked[19], unpacked[20],
                ),
                tyres_pressure=(
                    unpacked[21], unpacked[22], unpacked[23], unpacked[24],
                ),
            )
        except Exception as e:
            print(f"エラー: Car Telemetry 解析失敗 - {e}")
            return None


if __name__ == "__main__":
    print("✓ Telemetry Packets モジュール読み込み完了")
    print("- LapData 批出可能")
    print("- CarTelemetry 批出可能")
