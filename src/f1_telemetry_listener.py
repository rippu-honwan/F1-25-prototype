"""
F1 25 UDP Telemetry Listener
Packet を受け取り、データを収集して CSV に保存
"""

import socket
import logging

from .data_collector import TelemetryDataCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class F1TelemetryListener:
    def __init__(self, ip="0.0.0.0", port=20777, player_car_index=0):
        self.ip = ip
        self.port = port
        self.socket = None
        self.collector = TelemetryDataCollector(player_car_index=player_car_index)
        
    def setup(self):
        """UDP ソケットを初期化する"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.ip, self.port))
            print(f"✓ {self.ip}:{self.port} でリッスン開始")
            logger.info(f"Listening on {self.ip}:{self.port}")
            return True
        except Exception as e:
            print(f"✗ エラー: {e}")
            logger.error(f"Failed to setup: {e}")
            return False
    
    def start(self, timeout=60):
        """UDP データをリッスンして収集する"""
        if not self.socket:
            if not self.setup():
                return
        
        print(f"\n待機中... ({timeout}秒でタイムアウト)")
        logger.info("Waiting for F1 25 data...")
        
        try:
            if timeout > 0:
                self.socket.settimeout(timeout)
            
            packet_count = 0
            while True:
                data, addr = self.socket.recvfrom(2048)
                packet_count += 1
                
                # Packet を処理してデータ収集
                self.collector.process_packet(data)
                
                if packet_count == 1:
                    print(f"\n✓ データ受信開始！")
                
                if packet_count % 500 == 0:
                    print(f"✓ {packet_count} パケット受信 (Lap: {self.collector.lap_data_count}, Telemetry: {self.collector.car_telemetry_count})")
        
        except socket.timeout:
            print(f"\n⏱ タイムアウト ({packet_count} パケット受信)")
            logger.info("Timeout")
        except KeyboardInterrupt:
            print(f"\n⏹ 停止しました ({packet_count} パケット受信)")
            logger.info("Stopped")
        except Exception as e:
            print(f"\n✗ エラー: {e}")
            logger.error(f"Error: {e}")
        finally:
            if self.socket:
                self.socket.close()
                print("\nソケットをクローズしました")
                
                # 統計情報を表示して CSV に保存
                self.collector.print_stats()
                
                if self.collector.frame_data:
                    output_file = self.collector.save_to_csv()
                    print(f"✓ CSV ファイルを保存しました: {output_file}")


if __name__ == "__main__":
    listener = F1TelemetryListener()
    listener.start(timeout=600)  # 10 、テコードーで反標を受け取るようにしました
