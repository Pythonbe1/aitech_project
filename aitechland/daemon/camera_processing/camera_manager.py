import cv2
import threading
import time
from datetime import datetime, timedelta
import logging
from safety_detection.models import CameraState

logging.basicConfig(level=logging.DEBUG)


class CameraManager:
    def __init__(self, video_url: str, frame_rate: int, reconnect_delay: int = 60):
        self.video_url = video_url
        self.frame_rate = frame_rate
        self.reconnect_delay = reconnect_delay
        self.cap = cv2.VideoCapture(video_url)
        self.camera_ip = self._extract_camera_ip()
        self.last_error_time = None
        self.last_state_update_time = datetime.now()
        self.stop_event = threading.Event()

        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FPS, self.frame_rate)
            self.update_camera_state('Online')
        else:
            self.update_camera_state('Offline')

        threading.Thread(target=self._reconnect_camera, daemon=True).start()

    def _extract_camera_ip(self) -> str:
        return self.video_url.split('@')[1].split(':')[0]

    def update_camera_state(self, state: str):
        current_time = datetime.now()
        if current_time - self.last_state_update_time >= timedelta(seconds=60):
            try:
                CameraState.objects.update_or_create(
                    camera_ip=self.camera_ip,
                    defaults={'state': state}
                )
                self.last_state_update_time = current_time
                logging.info(f'Camera state updated to {state} for IP: {self.camera_ip}')
            except Exception as e:
                logging.error(f"Error updating camera state: {e}")

    def read_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.update_camera_state('Offline')
            logging.warning(f"Failed to read frame from camera: {self.camera_ip}")
            self.last_error_time = datetime.now()
            self._shutdown_and_reconnect()
            return None
        self.update_camera_state('Online')
        return frame

    def _shutdown_and_reconnect(self):
        self.cap.release()
        logging.info(f"Shutting down camera: {self.camera_ip} for {self.reconnect_delay} seconds.")
        time.sleep(self.reconnect_delay)
        self.cap = cv2.VideoCapture(self.video_url)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FPS, self.frame_rate)
            self.update_camera_state('Online')
        else:
            self.update_camera_state('Offline')
            logging.warning(f"Failed to reconnect to camera: {self.camera_ip}")

    def _reconnect_camera(self):
        while not self.stop_event.is_set():
            time.sleep(60)
            current_time = datetime.now()
            if self.last_error_time and current_time - self.last_error_time > timedelta(seconds=self.reconnect_delay):
                logging.info(f"Attempting to reconnect to camera: {self.camera_ip}")
                self.cap.release()
                self.cap = cv2.VideoCapture(self.video_url)
                if self.cap.isOpened():
                    self.cap.set(cv2.CAP_PROP_FPS, self.frame_rate)
                    self.update_camera_state('Online')
                    self.last_error_time = None
                else:
                    self.update_camera_state('Offline')
                    logging.warning(f"Failed to reconnect to camera: {self.camera_ip}")

    def release(self):
        self.stop_event.set()
        self.cap.release()
