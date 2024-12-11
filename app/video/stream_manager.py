import logging
from typing import Dict, Optional
from flask import Response
import requests


class StreamManager:
    def __init__(self):
        self.streams: Dict[str, dict] = {}
        self.logger = logging.getLogger("OWL.Stream")

    def get_stream(self, owl_id: str) -> Optional[Response]:
        """Get video stream from an OWL."""
        if owl_id not in self.streams:
            return None

        try:
            # Proxy the video feed from the OWL
            owl_ip = self.streams[owl_id]['ip']
            response = requests.get(
                f"http://{owl_ip}:5000/video_feed",
                stream=True
            )

            return Response(
                self._stream_generator(response),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get stream from {owl_id}: {e}")
            return None

    def _stream_generator(self, response):
        """Generate video stream from OWL response."""
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                yield chunk

    def add_stream(self, owl_id: str, ip: str):
        """Add a new video stream."""
        self.streams[owl_id] = {
            'ip': ip,
            'active': True
        }

    def remove_stream(self, owl_id: str):
        """Remove a video stream."""
        if owl_id in self.streams:
            del self.streams[owl_id]