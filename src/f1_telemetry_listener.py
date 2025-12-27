"""
F1 25 UDP Telemetry Listener
"""

import socket
import csv
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class F1TelemetryListener:
    def __init__(self, ip="127.0.0.1", port=20777):
        self.ip = ip
        self.port = port
        self.socket = None
        
    def setup(self):
        """Initialize UDP socket"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind((self.ip, self.port))
            logger.info(f"Listening on {self.ip}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to setup: {e}")
            return False
    
    def start(self, timeout=60):
        """Start listening"""
        if not self.socket:
            self.setup()
        
        logger.info("Waiting for F1 25 data...")
        
        try:
            if timeout > 0:
                self.socket.settimeout(timeout)
            
            packet_count = 0
            while True:
                data, addr = self.socket.recvfrom(2048)
                packet_count += 1
                
                if packet_count % 20 == 0:
                    print(f"✓ Received packet #{packet_count} ({len(data)} bytes)")
        
        except socket.timeout:
            logger.info("Timeout")
        except KeyboardInterrupt:
            logger.info("Stopped")
        finally:
            if self.socket:
                self.socket.close()


if __name__ == "__main__":
    listener = F1TelemetryListener()
    listener.start(timeout=30)
