import logging
from typing import Optional
from flask import Response
import requests


class StreamManager:
    def __init__(self):
        self.logger = logging.getLogger("OWL.Stream")

    def get_stream(self, owl_id: str, ip: str) -> Optional[Response]:
        """Get video stream from an OWL"""
        try:
            # Proxy the video feed from the OWL
            response = requests.get(
                f"http://{ip}:5000/video_feed",
                stream=True,
                timeout=5
            )

            if response.ok:
                return Response(
                    self._stream_generator(response),
                    mimetype='multipart/x-mixed-replace; boundary=frame'
                )
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get stream from {owl_id}: {e}")
            return None

    def _stream_generator(self, response):
        """Generate video stream from OWL response"""
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                yield chunk