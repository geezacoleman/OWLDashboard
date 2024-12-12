import logging
import threading
import time
import requests
from datetime import datetime
from typing import Dict, Optional


class OWLFinder:
    def __init__(self, subnet: str):
        self.subnet = subnet
        self.owls: Dict[str, dict] = {}
        self.logger = logging.getLogger("OWL.Discovery")
        self.discovery_thread = None
        self.running = False

    def start_discovery(self):
        """Start the discovery process"""
        self.running = True
        self.discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
        self.discovery_thread.start()

    def stop_discovery(self):
        """Stop the discovery process"""
        self.running = False
        if self.discovery_thread:
            self.discovery_thread.join()

    def _discovery_loop(self):
        """Continuous network scanning loop"""
        while self.running:
            self.scan_network()
            time.sleep(10)  # Scan every 10 seconds

    def scan_network(self):
        """Scan subnet for OWLs"""
        for i in range(2, 255):
            ip = f"{self.subnet}.{i}"
            try:
                response = requests.get(
                    f"http://{ip}:5000/health",
                    timeout=0.5
                )
                if response.ok:
                    owl_data = response.json()
                    owl_id = owl_data['owl_id']

                    self.owls[owl_id] = {
                        'ip': ip,
                        'last_seen': datetime.now().isoformat(),
                        'status': 'connected'
                    }
                    self.logger.info(f"Found OWL {owl_id} at {ip}")
            except requests.exceptions.RequestException:
                continue

    def get_owls(self) -> dict:
        """Get all discovered OWLs"""
        return self.owls

    def get_owl(self, owl_id: str) -> Optional[dict]:
        """Get specific OWL details"""
        return self.owls.get(owl_id)