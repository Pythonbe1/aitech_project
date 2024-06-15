import logging
import multiprocessing
import os
import queue
import threading
import time
from datetime import datetime, timedelta

import cv2
import torch
from ultralytics import YOLO

from daemon.calculation.Calculation import Calculation
from daemon.constants import CLASS_NAMES
from safety_detection.models import CameraState, Image, Camera, DetectionClasses
from django.conf import settings

logging.basicConfig(level=logging.DEBUG)


class CameraStreamViewer:
    def __init__(self, url: str, weights_path: str,
                 frame_rate: int = 1, save_path: str = None,
                 queue_size: int = 50):
        self.stop_event = multiprocessing.Event()
        self.url = url
        self.weights_path = weights_path
        self.frame_rate = frame_rate
        self.save_path = save_path or settings.MEDIA_ROOT
        self.cap = cv2.VideoCapture(url)
        self.camera_ip = self._extract_camera_ip()
        self.last_detection_time = {}
        self.last_state_update_time = datetime.now()
        self.last_error_time = None
        self.frame_queue = queue.Queue(maxsize=queue_size)

    def _extract_camera_ip(self) -> str:
        return self.url.split('@')[1].split(':')[0]

    def update_camera_state(self, state: str):
        current_time = datetime.now()
        time_diff = current_time - self.last_state_update_time
        if time_diff >= timedelta(seconds=60):
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
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = YOLO(self.weights_path).to(device)
        while not self.stop_event.is_set():
            if self.cap.grab():
                start_time = time.time()
                ret, frame = self.cap.retrieve()
                if ret:
                    self.update_camera_state('Online')
                    self._process_frame(frame, model)
                    # Ensure the frame rate
                    elapsed_time = time.time() - start_time
                    sleep_time = max(15.0 / self.frame_rate - elapsed_time, 0)
                    time.sleep(sleep_time)
            else:
                self.update_camera_state('Offline')

    def _process_frame(self, frame, model):
        resize_frame = cv2.resize(frame, (640, 640), interpolation=cv2.INTER_LINEAR)
        results = model.track(resize_frame, conf=0.50, verbose=False, tracker='bytetrack.yaml')
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
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
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

    def stop(self):
        self.stop_event.set()
        if self.cap.isOpened():
            self.cap.release()
            logging.info(f'Stopped camera stream for IP: {self.camera_ip}')
