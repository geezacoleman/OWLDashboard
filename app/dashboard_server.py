import logging
from flask import Flask, render_template, jsonify
from datetime import datetime
from .discovery.owl_finder import OWLFinder
from .monitoring.system_monitor import SystemMonitor
from .video.stream_manager import StreamManager


class OWLDashboardServer:
    def __init__(self, port: int = 5000, subnet: str = "192.168.1"):
        self.app = Flask(__name__)
        self.port = port
        self.subnet = subnet

        # Initialize components
        self.owl_finder = OWLFinder(subnet)
        self.system_monitor = SystemMonitor()
        self.stream_manager = StreamManager()

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("OWL.Dashboard")

        # Setup routes
        self._setup_routes()

    def _setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('dashboard.html')

        @self.app.route('/system_stats')
        def get_stats():
            """Get all OWL stats"""
            owls = self.owl_finder.get_owls()
            for owl_id, owl in owls.items():
                stats = self.system_monitor.get_owl_stats(owl['ip'])
                owls[owl_id].update(stats)
            return jsonify(owls)

        @self.app.route('/owl/<owl_id>/stream')
        def get_stream(owl_id):
            """Get video stream for specific OWL"""
            owl = self.owl_finder.get_owl(owl_id)
            if owl:
                return self.stream_manager.get_stream(owl_id, owl['ip'])
            return jsonify({'error': 'OWL not found'}), 404

    def run(self):
        """Run the dashboard server"""
        self.logger.info(f"Starting OWL Dashboard Server on port {self.port}")
        self.owl_finder.start_discovery()
        self.app.run(host='0.0.0.0', port=self.port)