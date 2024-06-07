import os
import time
import cv2
import torch
from ultralytics import YOLO
from daemon.calculation.Calculation import Calculation
from safety_detection.models import CameraState, Image, Camera, DetectionClasses
import logging
from django.conf import settings
from daemon.constants import CLASS_NAMES  # Import the class names from constants
from datetime import datetime, timedelta

logging.basicConfig(level=logging.DEBUG)


class CameraStreamViewer:
    def __init__(self, url: str, weights_path: str, save_path: str = None):
        """
        Initialize the CameraStreamViewer.

        :param url: The URL of the camera stream.
        :param weights_path: Path to the model weights.
        :param save_path: Path to save images, defaults to settings.MEDIA_ROOT.
        """
        self.url = url
        self.weights_path = weights_path
        self.save_path = save_path or settings.MEDIA_ROOT
        self.cap = cv2.VideoCapture(url)
        self.camera_ip = self._extract_camera_ip()
        if not self.cap.isOpened():
            self.update_camera_state('Offline')
        self.last_detection_time = {}
        self.last_state_update_time = datetime.now()

    def _extract_camera_ip(self) -> str:
        """
        Extract the camera IP address from the URL.

        :return: The IP address as a string.
        """
        return self.url.split('@')[1].split(':')[0]

    def update_camera_state(self, state: str):
        """
        Update the camera state in the database if more than 41 minutes have passed since the last update.

        :param state: The new state of the camera.
        """
        current_time = datetime.now()
        time_diff = current_time - self.last_state_update_time

        # Check if more than 41 minutes have passed since the last update
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
        else:
            logging.debug(f'Skipping state update for IP: {self.camera_ip}, last update was {time_diff} ago.')

    def start(self):
        """
        Start the camera stream processing.
        """
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = YOLO(self.weights_path).to(device)
        while True:
            ret, frame = self.cap.read()
            if frame is not None:
                self.update_camera_state('Online')
                self._process_frame(frame, model)
            else:
                self.update_camera_state('Offline')
                logging.warning("Failed to read frame from camera: %s", self.camera_ip)
                time.sleep(2)

    def _process_frame(self, frame, model):
        """
        Process a single frame from the camera stream.

        :param frame: The frame to process.
        :param model: The YOLO model for prediction.
        """
        resize_frame = cv2.resize(frame, (640, 640), interpolation=cv2.INTER_LINEAR)
        results = model.predict(resize_frame, conf=0.50, verbose=False)
        class_counts = Calculation.count_classes(results[0].names, results[0].boxes.cls.int().tolist())
        if any(class_name in class_counts for class_name in CLASS_NAMES):
            self._handle_detections(class_counts, results[0])

    def _handle_detections(self, class_counts, results):
        """
        Handle the detections in a frame.

        :param class_counts: Counts of detected classes.
        :param results: YOLO detection results.
        """
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
        """
        Save a detection frame and update the database.

        :param frame: The frame to save.
        :param class_name: The detected class name.
        :param camera_info: Tuple containing camera and class IDs.
        """
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
        """
        Log the saved frame.

        :param filepath: Path to the saved frame.
        """
        logging.info(f'Frame saved at: {filepath}')

    def get_camera_and_class_ids(self, camera_ip: str, class_name: str) -> tuple:
        """
        Get the camera and class IDs from the database.

        :param camera_ip: The camera IP address.
        :param class_name: The class name.
        :return: Tuple containing camera ID and class ID, or None if not found.
        """
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
        """
        Save a detection record to the database.

        :param camera_id: The camera ID.
        :param class_name_id: The class name ID.
        :param filename: The filename of the saved image.
        """
        Image.objects.create(
            camera_id=camera_id,
            class_name_id=class_name_id,
            image_file=filename
        )
        logging.info('Record saved in DB')

    def release(self):
        """
        Release the camera resource.
        """
        self.cap.release()
        cv2.destroyAllWindows()
