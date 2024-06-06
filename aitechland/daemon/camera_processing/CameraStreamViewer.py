# camera_processing/CameraStreamViewer.py

import os
import time
import cv2
import torch
from ultralytics import YOLO
from daemon.calculation.Calculation import Calculation
from safety_detection.models import CameraState, Image, Camera, DetectionClasses
import logging
from django.conf import settings

logging.basicConfig(level=logging.INFO)


class CameraStreamViewer:
    def __init__(self, url: str, weights_path: str, save_path: str = None):
        self.url = url
        self.weights_path = weights_path
        self.save_path = save_path or settings.MEDIA_ROOT
        self.cap = cv2.VideoCapture(url)
        if not self.cap.isOpened():
            self.update_camera_state('Offline')
        self.last_detection_time = {}

    def update_camera_state(self, state: str):
        camera_ip = self.url.split('@')[1].split(':')[0]
        CameraState.objects.update_or_create(
            camera_ip=camera_ip,
            defaults={'state': state}
        )

    def start(self, save_interval: int = 120):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = YOLO(self.weights_path)
        model.to(device)
        while True:
            ret, frame = self.cap.read()
            if frame is not None:
                camera_ip = self.url.split('@')[1].split(':')[0]
                self.update_camera_state('Online')
                resize_frame = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_LINEAR)
                results = model.predict(resize_frame, conf=0.40, verbose=True)
                class_counts = Calculation.count_classes(results[0].names, results[0].boxes.cls.int().tolist())
                if any(class_name in class_counts for class_name in ['smoke', 'head', 'fire', 'helmet']):
                    current_time = time.time()
                    if (camera_ip not in self.last_detection_time or
                            current_time - self.last_detection_time[camera_ip] >= save_interval):
                        self.last_detection_time[camera_ip] = current_time
                        logging.info('Detection found')
                        plotted_frame = results[0].plot(conf=False)
                        class_name = next(class_name for class_name in ['smoke', 'head', 'fire', 'helmet'] if
                                          class_name in class_counts)
                        camera_info = self.get_camera_and_class_ids(camera_ip, class_name)
                        if camera_info is not None:
                            camera_id, class_name_id = camera_info
                            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                            filename = f"{camera_ip}_{class_name}_{timestamp}.jpeg"
                            filepath = os.path.join(self.save_path, filename)
                            try:
                                cv2.imwrite(filepath, plotted_frame)
                                self.save_frame(plotted_frame, class_name)
                                self.save_to_database(camera_id, class_name_id, filename)
                            except Exception as e:
                                logging.error(f"Error saving frame: {e}")
                        else:
                            logging.warning("Camera info not found. Skipping saving and database operations.")
            else:
                logging.warning("Failed to read frame from camera: %s", self.url.split('@')[1].split(':')[0])

    def save_frame(self, frame, class_name: str):
        camera_ip = self.url.split('@')[1].split(':')[0]
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        filename = f"{camera_ip}_{class_name}_{timestamp}.jpeg"
        filepath = os.path.join(self.save_path, filename)
        cv2.imwrite(filepath, frame)
        logging.info(f'Frame saved at: {filepath}')
        return filepath  # Return the file path for further processing or logging

    def get_camera_and_class_ids(self, camera_ip: str, class_name: str):
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
        return 'Saved in DB'

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()
