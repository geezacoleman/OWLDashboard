import logging
import requests
from datetime import datetime
from typing import Dict, Optional


class SystemMonitor:
    def __init__(self):
        self.stats_cache: Dict[str, dict] = {}
        self.logger = logging.getLogger("OWL.Monitor")

    def get_owl_stats(self, ip: str) -> dict:
        """Get system stats from an OWL."""
        try:
            response = requests.get(f"http://{ip}:5000/system_stats")
            if response.ok:
                stats = response.json()
                self.stats_cache[ip] = {
                    'timestamp': datetime.now().isoformat(),
                    'stats': stats
                }
                return stats
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get stats from {ip}: {e}")

        # Return cached stats if available
        if ip in self.stats_cache:
            return self.stats_cache[ip]['stats']

        return {
            'error': 'Could not retrieve stats',
            'cpu_percent': 0,
            'cpu_temp': 0,
            'status': 'disconnected'
        }

    def monitor_health(self, ip: str) -> bool:
        """Check if OWL is healthy."""
        try:
            response = requests.get(f"http://{ip}:5000/health")
            return response.ok
        except requests.exceptions.RequestException:
            return False