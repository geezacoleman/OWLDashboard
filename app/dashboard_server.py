import logging
import getpass
from pathlib import Path
from flask import Flask, render_template, jsonify
from cryptography.fernet import Fernet
from .discovery.owl_finder import OWLFinder
from .monitoring.system_monitor import SystemMonitor
from .video.stream_manager import StreamManager
import os


class OWLDashboardServer:
    def __init__(self, port: int = 5000, subnet: str = "192.168.1"):
        self.app = Flask(__name__)
        self.port = port
        self.subnet = subnet

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("OWL.Dashboard")

        # Get credentials
        self.credentials = self._setup_credentials()

        # Initialize components with credentials
        self.owl_finder = OWLFinder(subnet, self.credentials)
        self.system_monitor = SystemMonitor(self.credentials)
        self.stream_manager = StreamManager(self.credentials)

        # Setup routes
        self._setup_routes()

    def _setup_credentials(self):
        """Setup credentials either from user input or stored encrypted credentials"""
        creds_file = Path.home() / '.owl' / 'credentials.enc'
        key_file = Path.home() / '.owl' / 'key'

        # Create .owl directory if it doesn't exist
        creds_file.parent.mkdir(exist_ok=True)

        if creds_file.exists() and key_file.exists():
            # Try to load existing credentials
            try:
                with open(key_file, 'rb') as f:
                    key = f.read()
                fernet = Fernet(key)

                with open(creds_file, 'rb') as f:
                    encrypted_creds = f.read()
                    decrypted = fernet.decrypt(encrypted_creds).decode()
                    username, password = decrypted.split(':')

                self.logger.info("Loaded existing credentials")
                return {'username': username, 'password': password}
            except Exception as e:
                self.logger.warning(f"Failed to load credentials: {e}")

        # Ask for new credentials
        print("\nOWL Dashboard Authentication Setup")
        print("----------------------------------")
        username = input("Enter username: ").strip()
        while not username:
            print("Username cannot be empty")
            username = input("Enter username: ").strip()

        password = getpass.getpass("Enter password: ")
        while len(password) < 8:
            print("Password must be at least 8 characters")
            password = getpass.getpass("Enter password: ")

        save = input("Save credentials for future use? (y/n): ").lower().strip() == 'y'

        if save:
            try:
                # Generate new key
                key = Fernet.generate_key()
                fernet = Fernet(key)

                # Save key
                with open(key_file, 'wb') as f:
                    f.write(key)
                os.chmod(key_file, 0o600)

                # Encrypt and save credentials
                creds_string = f"{username}:{password}"
                encrypted = fernet.encrypt(creds_string.encode())
                with open(creds_file, 'wb') as f:
                    f.write(encrypted)
                os.chmod(creds_file, 0o600)

                self.logger.info("Saved encrypted credentials")
            except Exception as e:
                self.logger.error(f"Failed to save credentials: {e}")

        return {'username': username, 'password': password}

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