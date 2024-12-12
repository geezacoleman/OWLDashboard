import logging
from typing import Optional
from flask import Response
import requests
from requests.auth import HTTPBasicAuth


class StreamManager:
    def __init__(self, credentials: dict, timeout: int = 10):
        self.logger = logging.getLogger("OWL.Stream")
        self.auth = HTTPBasicAuth(credentials['username'], credentials['password'])
        self.timeout = timeout

        # Session setup
        self.session = requests.Session()
        self.session.verify = False
        self.session.auth = self.auth

    def get_stream(self, owl_id: str, ip: str) -> Optional[Response]:
        """Get video stream from an OWL"""
        try:
            response = self.session.get(
                f"https://{ip}/video_feed",
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()

            return Response(
                self._stream_generator(response, owl_id),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )

        except Exception as e:
            self.logger.error(f"Failed to get stream from {owl_id}: {str(e)}")
            return None

    def _stream_generator(self, response, owl_id):
        """Generate video stream from OWL response"""
        try:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        except Exception as e:
            self.logger.error(f"Stream from {owl_id} interrupted: {str(e)}")
            return

    def close(self):
        """Clean up resources"""
        if self.session:
            self.session.close()