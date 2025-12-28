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
    """F1 25 Packet Header (24 bytes)"""
    
    FORMAT_STRING = "<2sHBBBBBBHHHBBBBB"
    SIZE = 24
    
    def __init__(self, data: bytes):
        if len(data) < self.SIZE:
            raise ValueError(f"データが短すぎます: {len(data)} bytes (必要: {self.SIZE})")
        
        unpacked = struct.unpack(self.FORMAT_STRING, data[:self.SIZE])
        
        self.format_version = int.from_bytes(unpacked[0], 'little')
        self.game_year = unpacked[1]
        self.game_major_version = unpacked[2]
        self.game_minor_version = unpacked[3]
        self.packet_version = unpacked[4]
        self.packet_type = PacketType(unpacked[5])
        self.session_uid = unpacked[6]
        self.session_time = unpacked[7]
        self.frame_identifier = unpacked[8]
        self.overall_frame_identifier = unpacked[9]
        self.player_car_index = unpacked[10]
        self.secondary_player_car_index = unpacked[11]
        # remaining bytes for future use
    
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
            print(f"エラー: ヘッダ解析失敗 - {e}")
            return None
    
    @staticmethod
    def get_packet_type(data: bytes) -> PacketType:
        """データから packet type を取得（高速）"""
        if len(data) < 6:
            return None
        return PacketType(data[5])
    
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
    print(f"サポート Packet Types: {list(PacketType)}")
