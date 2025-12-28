"""
F1 25 UDP Packet Parser
Packet header を解析して packet type を識別する
"""

import struct
from enum import IntEnum


class PacketType(IntEnum):
    """F1 25 Packet Types"""
    MOTION = 0
    SESSION = 1
    LAP_DATA = 2
    EVENT = 3
    PARTICIPANTS = 4
    CAR_SETUPS = 5
    CAR_TELEMETRY = 6
    CAR_STATUS = 7
    FINAL_CLASSIFICATION = 8
    LOBBY_INFO = 9
    CAR_DAMAGE = 10
    SESSION_HISTORY = 11


class PacketHeader:
    """F1 25 Packet Header (最小限の情報を読み取る)"""
    
    # 簡略化されたヘッダー読み取り
    MIN_SIZE = 6  # 最低限 packet type を取得するために必要なバイト数
    
    def __init__(self, data: bytes):
        if len(data) < self.MIN_SIZE:
            raise ValueError(f"データが短すぎます: {len(data)} bytes (必要: 最低 {self.MIN_SIZE})")
        
        try:
            # F1 25 の packet header 構造:
            # Bytes 0-1: Packet format (uint16)
            # Byte 2: Game year (uint8)
            # Byte 3: Game major version (uint8) 
            # Byte 4: Game minor version (uint8)
            # Byte 5: Packet type (uint8)
            # ... その他のフィールド
            
            self.format_version = struct.unpack('<H', data[0:2])[0]
            self.game_year = data[2]
            self.game_major_version = data[3]
            self.game_minor_version = data[4]
            self.packet_type = PacketType(data[5])
            
            # 追加情報（24バイト以上ある場合のみ）
            if len(data) >= 24:
                self.session_uid = struct.unpack('<Q', data[6:14])[0]
                self.session_time = struct.unpack('<f', data[14:18])[0]
                self.frame_identifier = struct.unpack('<I', data[18:22])[0]
                self.player_car_index = data[22]
            else:
                self.session_uid = 0
                self.session_time = 0.0
                self.frame_identifier = 0
                self.player_car_index = 0
                
        except Exception as e:
            raise ValueError(f"ヘッダー解析エラー: {e}")
    
    def __repr__(self):
        return (
            f"PacketHeader("
            f"format={self.format_version}, "
            f"year={self.game_year}, "
            f"packet_type={self.packet_type.name}, "
            f"frame={self.frame_identifier})"
        )


class PacketParser:
    """UDP packet を解析する"""
    
    @staticmethod
    def parse_header(data: bytes) -> PacketHeader:
        """Packet header を解析"""
        try:
            return PacketHeader(data)
        except Exception as e:
            # エラーをログに出力せず、None を返す（大量のエラーを防ぐ）
            return None
    
    @staticmethod
    def get_packet_type(data: bytes) -> PacketType:
        """データから packet type を取得（高速）"""
        if len(data) < 6:
            return None
        try:
            return PacketType(data[5])
        except:
            return None
    
    @staticmethod
    def is_lap_data(data: bytes) -> bool:
        """Lap Data packet (Type 2) かどうか"""
        return PacketParser.get_packet_type(data) == PacketType.LAP_DATA
    
    @staticmethod
    def is_car_telemetry(data: bytes) -> bool:
        """Car Telemetry packet (Type 6) かどうか"""
        return PacketParser.get_packet_type(data) == PacketType.CAR_TELEMETRY


if __name__ == "__main__":
    # テスト用
    print("✓ Packet Parser モジュール読み込み完了")
    print(f"サポート Packet Types: {[pt.name for pt in PacketType]}")
