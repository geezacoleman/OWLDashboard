import logging
import requests
import time
from datetime import datetime
from typing import Dict, Optional


class OWLFinder:
    def __init__(self, subnet: str):
        self.subnet = subnet
        self.owls: Dict[str, dict] = {}
        self.logger = logging.getLogger("OWL.Discovery")

    def discovery_loop(self):
        """Continuous network scanning loop."""
        while True:
            self.scan_network()
            time.sleep(10)  # Scan every 10 seconds

    def scan_network(self):
        """Scan subnet for OWLs."""
        for i in range(2, 255):
            ip = f"{self.subnet}.{i}"
            try:
                # Try to reach OWL health endpoint
                response = requests.get(
                    f"http://{ip}:5000/health",
                    timeout=0.5
                )
                if response.ok:
                    owl_data = response.json()
                    owl_id = owl_data['owl_id']

                    # Update or add OWL
                    self.owls[owl_id] = {
                        'ip': ip,
                        'last_seen': datetime.now().isoformat(),
                        'status': 'connected'
                    }
            except requests.exceptions.RequestException:
                continue

    def get_owls(self) -> dict:
        """Get all discovered OWLs."""
        return self.owls

    def get_owl(self, owl_id: str) -> Optional[dict]:
        """Get specific OWL details."""
        return self.owls.get(owl_id)

    def verify_owl(self, ip: str) -> bool:
        """Verify if an IP belongs to an OWL."""
        try:
            response = requests.get(f"http://{ip}:5000/health", timeout=0.5)
            return response.ok
        except requests.exceptions.RequestException:
            return False