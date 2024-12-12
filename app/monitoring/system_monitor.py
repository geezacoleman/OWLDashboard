import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import requests
from requests.auth import HTTPBasicAuth
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class SystemMonitor:
    def __init__(self, credentials: dict, stats_timeout: int = 5, stream_timeout: int = 10):
        self.logger = logging.getLogger("OWL.Monitor")
        self.auth = HTTPBasicAuth(credentials['username'], credentials['password'])
        self.stats_timeout = stats_timeout
        self.stream_timeout = stream_timeout

        # Cache setup
        self.stats_cache: Dict[str, dict] = {}
        self.cache_duration = timedelta(seconds=5)

        # Session setup
        self.session = requests.Session()
        self.session.verify = False  # Allow self-signed certificates
        self.session.auth = self.auth

    def get_owl_stats(self, ip: str) -> dict:
        """Get system statistics from an OWL device"""
        try:
            # Check cache first
            if ip in self.stats_cache:
                cache_time = datetime.fromisoformat(self.stats_cache[ip]['timestamp'])
                if datetime.now() - cache_time < self.cache_duration:
                    return self.stats_cache[ip]['stats']

            # Make HTTPS request
            response = self.session.get(
                f"https://{ip}/system_stats",
                timeout=self.stats_timeout
            )
            response.raise_for_status()

            # Process response
            stats = response.json()
            processed_stats = {
                'temp': stats.get('cpu_temp', 0),
                'cpu': stats.get('cpu_percent', 0),
                'detecting': stats.get('detecting', False),
                'status': 'connected',
                'error': None
            }

            # Update cache
            self.stats_cache[ip] = {
                'timestamp': datetime.now().isoformat(),
                'stats': processed_stats
            }

            return processed_stats

        except Exception as e:
            self.logger.error(f"Failed to get stats from {ip}: {str(e)}")

            # Return cached stats if available
            if ip in self.stats_cache:
                stats = self.stats_cache[ip]['stats'].copy()
                stats['status'] = 'error'
                stats['error'] = str(e)
                return stats

            return {
                'temp': 0,
                'cpu': 0,
                'detecting': False,
                'status': 'error',
                'error': str(e)
            }

    def close(self):
        """Clean up resources"""
        if self.session:
            self.session.close()