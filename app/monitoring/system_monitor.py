import logging
import requests
from datetime import datetime
from typing import Dict


class SystemMonitor:
    def __init__(self):
        self.stats_cache: Dict[str, dict] = {}
        self.logger = logging.getLogger("OWL.Monitor")

    def get_owl_stats(self, ip: str) -> dict:
        """Get system stats from an OWL"""
        try:
            response = requests.get(f"http://{ip}:5000/system_stats", timeout=1)
            if response.ok:
                stats = response.json()
                self.stats_cache[ip] = {
                    'timestamp': datetime.now().isoformat(),
                    'stats': stats
                }
                return {
                    'temp': stats['cpu_temp'],
                    'cpu': stats['cpu_percent'],
                    'detecting': stats.get('detecting', False),
                    'error': stats.get('error')
                }
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get stats from {ip}: {e}")

        # Return cached stats if available
        if ip in self.stats_cache:
            return self.stats_cache[ip]['stats']

        return {
            'temp': 0,
            'cpu': 0,
            'detecting': False,
            'error': 'connection_lost'
        }