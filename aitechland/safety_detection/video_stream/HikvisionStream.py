import cv2
import numpy as np
from hikvisionapi import Client

class VideoStream:
    def __init__(self, ip_address, username, password):
        self.ip_address = ip_address
        self.username = username
        self.password = password

    def start_video_stream(self):
        # Connect to the IP camera
        cam = Client(self.ip_address, self.username, self.password)

        while True:
            # Capture video frame
            vid = cam.Streaming.channels[102].picture(method='get', type='opaque_data')

            # Decode and yield frames continuously
            bytes = b''
            for chunk in vid.iter_content(chunk_size=1024):
                bytes += chunk
                a = bytes.find(b'\xff\xd8')
                b = bytes.find(b'\xff\xd9')
                if a != -1 and b != -1:
                    jpg = bytes[a:b + 2]
                    bytes = bytes[b + 2:]
                    frame = cv2.imdecode(
                        np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    _, jpeg = cv2.imencode('.jpg', frame)
                    yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
