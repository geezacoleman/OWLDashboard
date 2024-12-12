import logging
import threading
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional


class OWLFinder:
    def __init__(self, subnet: str, scan_interval: int = 10, timeout: float = 2.0):
        self.subnet = subnet
        self.scan_interval = scan_interval
        self.timeout = timeout
        self.owls: Dict[str, dict] = {}
        self.logger = logging.getLogger("OWL.Discovery")
        self.discovery_thread = None
        self.running = False

        # Track failed attempts
        self.failed_ips = {}
        self.max_retries = 3
        self.retry_cooldown = 300  # 5 minutes cooldown for failed IPs

    def start_discovery(self):
        """Start the discovery process"""
        self.running = True
        self.discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
        self.discovery_thread.start()
        self.logger.info(f"Started OWL discovery on subnet {self.subnet}")

    def stop_discovery(self):
        """Stop the discovery process"""
        self.running = False
        if self.discovery_thread:
            self.discovery_thread.join()
        self.logger.info("Stopped OWL discovery")

    def _discovery_loop(self):
        """Continuous network scanning loop"""
        while self.running:
            self.scan_network()
            self._cleanup_stale_owls()
            time.sleep(self.scan_interval)

    def _cleanup_stale_owls(self):
        """Remove OWLs that haven't been seen in 5 minutes"""
        current_time = datetime.now()
        stale_owls = []

        for owl_id, owl_data in self.owls.items():
            last_seen = datetime.fromisoformat(owl_data['last_seen'])
            if (current_time - last_seen) > timedelta(minutes=5):
                stale_owls.append(owl_id)
                self.logger.warning(f"OWL {owl_id} at {owl_data['ip']} hasn't responded in 5 minutes")

        for owl_id in stale_owls:
            del self.owls[owl_id]

    def _should_retry_ip(self, ip: str) -> bool:
        """Check if we should retry a previously failed IP"""
        if ip not in self.failed_ips:
            return True

        fails, last_attempt = self.failed_ips[ip]
        if fails >= self.max_retries:
            # Check if cooldown period has passed
            if (datetime.now() - last_attempt) > timedelta(seconds=self.retry_cooldown):
                # Reset failed attempts after cooldown
                del self.failed_ips[ip]
                return True
            return False
        return True

    def scan_network(self):
        """Scan subnet for OWLs using system_stats endpoint"""
        for i in range(2, 255):
            if not self.running:
                break

            ip = f"{self.subnet}.{i}"

            if not self._should_retry_ip(ip):
                continue

            try:
                # Try standard HTTP first
                response = requests.get(
                    f"http://{ip}:5000/system_stats",
                    timeout=self.timeout
                )

                # If that fails, try HTTPS
                if not response.ok:
                    response = requests.get(
                        f"https://{ip}:443/system_stats",
                        timeout=self.timeout,
                        verify=False  # Accept self-signed certs
                    )

                if response.ok:
                    stats = response.json()

                    # Generate a unique ID based on IP if not provided
                    owl_id = str(i)  # Using last octet as ID

                    self.owls[owl_id] = {
                        'ip': ip,
                        'last_seen': datetime.now().isoformat(),
                        'status': stats.get('status', 'unknown'),
                        'cpu_temp': stats.get('cpu_temp', 0),
                        'cpu_percent': stats.get('cpu_percent', 0),
                        'detecting': stats.get('detecting', False),
                        'error': stats.get('error')
                    }

                    if owl_id not in self.owls:
                        self.logger.info(f"Found new OWL {owl_id} at {ip}")

                    # Clear any failed attempts on success
                    if ip in self.failed_ips:
                        del self.failed_ips[ip]

            except requests.exceptions.RequestException as e:
                # Track failed attempts
                fails, _ = self.failed_ips.get(ip, (0, datetime.now()))
                self.failed_ips[ip] = (fails + 1, datetime.now())

                if fails == 0:  # Only log on first failure
                    self.logger.debug(f"Failed to connect to {ip}: {str(e)}")

    def get_owls(self) -> dict:
        """Get all discovered OWLs"""
        return self.owls

    def get_owl(self, owl_id: str) -> Optional[dict]:
        """Get specific OWL details"""
        return self.owls.get(owl_id)