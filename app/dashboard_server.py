# dashboard_server.py
import logging
import requests
from flask import Flask, render_template, jsonify
from datetime import datetime
import threading
import time


class OWLDashboardServer:
    def __init__(self, port: int = 5000, subnet: str = "192.168.1"):
        self.app = Flask(__name__)
        self.port = port
        self.subnet = subnet
        self.owls = {}  # Store discovered OWLs and their status

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("OWL.Dashboard")

        # Setup routes
        self._setup_routes()

        # Start discovery thread
        self.discovery_thread = threading.Thread(target=self._owl_discovery_loop, daemon=True)
        self.discovery_thread.start()

    def _setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('dashboard.html', owls=self.owls)

        @self.app.route('/owls')
        def get_owls():
            return jsonify(self.owls)

        @self.app.route('/owl/<owl_id>/status')
        def get_owl_status(owl_id):
            if owl_id in self.owls:
                return jsonify(self.owls[owl_id])
            return jsonify({'error': 'OWL not found'}), 404

    def _owl_discovery_loop(self):
        """Continuously scan network for OWLs."""
        while True:
            self._discover_owls()
            time.sleep(10)  # Scan every 10 seconds

    def _discover_owls(self):
        """Scan subnet for OWLs."""
        for i in range(2, 255):
            ip = f"{self.subnet}.{i}"
            try:
                # Try to reach OWL health endpoint
                response = requests.get(f"http://{ip}:5000/health", timeout=0.5)
                if response.ok:
                    owl_data = response.json()
                    owl_id = owl_data['owl_id']

                    # Update or add OWL status
                    self.owls[owl_id] = {
                        'ip': ip,
                        'last_seen': datetime.now().isoformat(),
                        'status': 'connected',
                        'cpu_temp': owl_data.get('cpu_temp', 0),
                        'cpu_usage': owl_data.get('cpu_percent', 0)
                    }
            except requests.exceptions.RequestException:
                continue

    def _check_owl_health(self, owl_id):
        """Check health of specific OWL."""
        if owl_id not in self.owls:
            return False

        owl = self.owls[owl_id]
        try:
            response = requests.get(f"http://{owl['ip']}:5000/system_stats")
            if response.ok:
                stats = response.json()
                owl.update({
                    'last_seen': datetime.now().isoformat(),
                    'status': 'connected',
                    'cpu_temp': stats.get('cpu_temp', 0),
                    'cpu_usage': stats.get('cpu_percent', 0)
                })
                return True
        except requests.exceptions.RequestException:
            owl['status'] = 'disconnected'
            return False

    def run(self):
        """Run the dashboard server."""
        self.logger.info(f"Starting OWL Dashboard Server on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port)


if __name__ == "__main__":
    dashboard = OWLDashboardServer()
    dashboard.run()