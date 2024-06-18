import os
import time
import cv2
import torch
import threading
from ultralytics import YOLO
from daemon.calculation.Calculation import Calculation
from safety_detection.models import CameraState, Image, Camera, DetectionClasses
import logging
from django.conf import settings
from daemon.constants import CLASS_NAMES
from datetime import datetime, timedelta

logging.basicConfig(level=logging.DEBUG)


class CameraStreamViewer:
    def __init__(self, video_url: str, weights_path: str, frame_rate: int = 1, save_path: str = None):
        self.video_url = video_url  # Store the video URL
        self.weights_path = weights_path
        self.frame_rate = frame_rate
        self.save_path = save_path or settings.MEDIA_ROOT
        self.cap = cv2.VideoCapture(video_url)
        self.camera_ip = self._extract_camera_ip()
        self.last_detection_time = {}
        self.last_state_update_time = datetime.now()
        self.last_error_time = None
        self.stop_event = threading.Event()
        self.dropped_frames_count = 0
        self.reconnect_delay = 60  # Delay for reconnection in seconds

        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FPS, self.frame_rate)
            self.update_camera_state('Online')
        else:
            self.update_camera_state('Offline')

        threading.Thread(target=self._read_and_process_frames, daemon=True).start()
        threading.Thread(target=self._reconnect_camera, daemon=True).start()

    def _extract_camera_ip(self) -> str:
        return self.video_url.split('@')[1].split(':')[0]

    def update_video_url(self, video_url: str):
        self.video_url = video_url
        self.cap = cv2.VideoCapture(video_url)
        self.camera_ip = self._extract_camera_ip()
        logging.info(f"Updated video URL to: {self.video_url}")

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

    def start(self):
        while not self.stop_event.is_set():
            time.sleep(1)

    def _read_and_process_frames(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = YOLO(self.weights_path).to(device)

        last_frame_time = time.time()

        while not self.stop_event.is_set():
            current_time = time.time()
            ret, frame = self.cap.read()

            if not ret:
                self.update_camera_state('Offline')
                logging.warning(f"Failed to read frame from camera: {self.camera_ip}")
                self.last_error_time = datetime.now()
                self._shutdown_and_reconnect()
                continue

            if current_time - last_frame_time < 1.0 / self.frame_rate:
                # Drop frames if less than 1 second / frame_rate has passed
                continue

            last_frame_time = current_time

            self.update_camera_state('Online')
            self._process_frame(frame, model)

    def _shutdown_and_reconnect(self):
        self.cap.release()
        logging.info(f"Shutting down camera: {self.camera_ip} for {self.reconnect_delay} seconds.")
        time.sleep(self.reconnect_delay)
        self.cap = cv2.VideoCapture(self.video_url)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FPS, self.frame_rate)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 10)  # Adjust buffer size if needed
            self.update_camera_state('Online')
        else:
            self.update_camera_state('Offline')
            logging.warning(f"Failed to reconnect to camera: {self.camera_ip}")

    def _process_frame(self, frame, model):
        resized_frame = cv2.resize(frame, (640, 640), interpolation=cv2.INTER_LINEAR)
        results = model.track(resized_frame, conf=0.60, verbose=False)
        class_counts = Calculation.count_classes(results[0].names, results[0].boxes.cls.int().tolist())

        if any(class_name in class_counts for class_name in CLASS_NAMES):
            self._handle_detections(class_counts, results[0])

    def _handle_detections(self, class_counts, results):
        current_time = time.time()
        if current_time - self.last_detection_time.get(self.camera_ip, 0) >= settings.CAMERA_SAVE_INTERVAL:
            self.last_detection_time[self.camera_ip] = current_time
            logging.info('Detection found')
            plotted_frame = results.plot(conf=False)
            class_name = next(class_name for class_name in CLASS_NAMES if class_name in class_counts)
            camera_info = self.get_camera_and_class_ids(self.camera_ip, class_name)

            if camera_info:
                self._save_detection(plotted_frame, class_name, camera_info)
            else:
                logging.warning("Camera info not found. Skipping saving and database operations.")

    def _save_detection(self, frame, class_name: str, camera_info: tuple):
        camera_id, class_name_id = camera_info
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{self.camera_ip}_{class_name}_{timestamp}.jpeg"
        filepath = os.path.join(self.save_path, filename)

        try:
            cv2.imwrite(filepath, frame)
            self.save_frame(filepath)
            self.save_to_database(camera_id, class_name_id, filename)
        except Exception as e:
            logging.error(f"Error saving frame: {e}")

    def save_frame(self, filepath: str):
        logging.info(f'Frame saved at: {filepath}')

    def get_camera_and_class_ids(self, camera_ip: str, class_name: str) -> tuple:
        try:
            camera = Camera.objects.get(ip_address=camera_ip)
            class_obj = DetectionClasses.objects.get(name=class_name)
            return camera.id, class_obj.id
        except Camera.DoesNotExist:
            logging.warning(f"Camera with IP {camera_ip} does not exist.")
        except DetectionClasses.DoesNotExist:
            logging.warning(f"Detection class {class_name} does not exist.")
        return None

    def save_to_database(self, camera_id: int, class_name_id: int, filename: str):
        Image.objects.create(
            camera_id=camera_id,
            class_name_id=class_name_id,
            image_file=filename
        )
        logging.info('Record saved in DB')

    def release(self):
        self.stop_event.set()
        self.cap.release()
        cv2.destroyAllWindows()

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
