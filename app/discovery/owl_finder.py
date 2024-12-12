import logging
import threading
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional
from requests.auth import HTTPBasicAuth
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class OWLFinder:
    def __init__(self, subnet: str, credentials: dict, scan_interval: int = 10, timeout: float = 2.0):
        """
        Initialize OWL discovery service.

        Args:
            subnet: Network subnet to scan (e.g., "192.168.1")
            credentials: Dict containing 'username' and 'password'
            scan_interval: Time between network scans in seconds
            timeout: Connection timeout in seconds
        """
        self.subnet = subnet
        self.scan_interval = scan_interval
        self.timeout = timeout
        self.owls: Dict[str, dict] = {}
        self.logger = logging.getLogger("OWL.Discovery")
        self.discovery_thread = None
        self.running = False

        # Authentication setup
        self.auth = HTTPBasicAuth(credentials['username'], credentials['password'])

        # Initialize session for connection pooling
        self.session = requests.Session()
        self.session.verify = False  # Allow self-signed certificates
        self.session.auth = self.auth

        # Track failed attempts and last seen times
        self.failed_attempts: Dict[str, int] = {}
        self.last_seen: Dict[str, datetime] = {}
        self.max_failed_attempts = 3
        self.stale_threshold = timedelta(minutes=5)

    def start_discovery(self):
        """Start the discovery process"""
        self.running = True
        self.discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
        self.discovery_thread.start()
        self.logger.info(f"Started OWL discovery on subnet {self.subnet}")

    def stop_discovery(self):
        """Stop the discovery process and cleanup"""
        self.running = False
        if self.discovery_thread:
            self.discovery_thread.join()
        if self.session:
            self.session.close()
        self.logger.info("Stopped OWL discovery")

    def _discovery_loop(self):
        """Continuous network scanning loop"""
        while self.running:
            self.scan_network()
            self._cleanup_stale_owls()
            time.sleep(self.scan_interval)

    def _cleanup_stale_owls(self):
        """Remove OWLs that haven't been seen recently"""
        current_time = datetime.now()
        stale_owls = []

        for owl_id, last_seen in self.last_seen.items():
            if current_time - last_seen > self.stale_threshold:
                stale_owls.append(owl_id)
                self.logger.info(f"OWL {owl_id} at {self.owls[owl_id]['ip']} is no longer responding")

        for owl_id in stale_owls:
            self.owls.pop(owl_id, None)
            self.last_seen.pop(owl_id, None)
            self.failed_attempts.pop(owl_id, None)

    def scan_network(self):
        """Scan subnet for OWLs"""
        for i in range(2, 255):
            if not self.running:
                break

            ip = f"{self.subnet}.{i}"

            # Skip IPs with too many failed attempts
            if self.failed_attempts.get(ip, 0) >= self.max_failed_attempts:
                continue

            try:
                # Try to get system stats
                response = self.session.get(
                    f"https://{ip}/system_stats",
                    timeout=self.timeout
                )
                response.raise_for_status()

                stats = response.json()
                owl_id = str(i)  # Using last octet as ID

                # Update OWL information
                self.owls[owl_id] = {
                    'ip': ip,
                    'last_seen': datetime.now().isoformat(),
                    'status': stats.get('status', 'connected'),
                    'cpu_temp': stats.get('cpu_temp', 0),
                    'cpu_percent': stats.get('cpu_percent', 0),
                    'detecting': stats.get('detecting', False)
                }

                # Update tracking
                self.last_seen[owl_id] = datetime.now()
                self.failed_attempts.pop(ip, None)

                if owl_id not in self.owls:
                    self.logger.info(f"Found new OWL {owl_id} at {ip}")

            except requests.exceptions.RequestException as e:
                # Track failed attempts
                self.failed_attempts[ip] = self.failed_attempts.get(ip, 0) + 1

                if self.failed_attempts[ip] == 1:  # Log only first failure
                    self.logger.debug(f"Failed to connect to {ip}: {str(e)}")
                elif self.failed_attempts[ip] == self.max_failed_attempts:
                    self.logger.warning(f"Stopping attempts to {ip} after {self.max_failed_attempts} failures")

    def get_owls(self) -> dict:
        """Get all discovered OWLs"""
        return self.owls

    def get_owl(self, owl_id: str) -> Optional[dict]:
        """Get specific OWL details"""
        return self.owls.get(owl_id)

    def reset_failed_attempts(self, ip: Optional[str] = None):
        """Reset failed attempt counter for specific IP or all IPs"""
        if ip:
            self.failed_attempts.pop(ip, None)
        else:
            self.failed_attempts.clear()