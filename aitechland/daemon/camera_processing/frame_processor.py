import logging
import time

import cv2
import torch
from ultralytics import YOLO

from daemon.calculation.calculation import Calculation
from daemon.constants import CLASS_NAMES

logging.basicConfig(level=logging.DEBUG)


class FrameProcessor:
    def __init__(self, weights_path: str, frame_rate: int):
        self.weights_path = weights_path
        self.frame_rate = frame_rate
        self.last_frame_time = time.time()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = YOLO(self.weights_path).to(self.device)
        self.last_detection_time = {}

    def process_frame(self, frame, camera_ip: str):
        current_time = time.time()
        if current_time - self.last_frame_time < 1.0 / self.frame_rate:
            return None

        self.last_frame_time = current_time

        resized_frame = cv2.resize(frame, (640, 640), interpolation=cv2.INTER_LINEAR)
        results = self.model.track(resized_frame, conf=0.6, verbose=False)
        class_counts = Calculation.count_classes(results[0].names, results[0].boxes.cls.int().tolist())

        if any(class_name in class_counts for class_name in CLASS_NAMES):
            self.last_detection_time[camera_ip] = current_time
            return results[0], class_counts
        return None
