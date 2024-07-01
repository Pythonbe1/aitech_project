import os
import cv2
from datetime import datetime
import logging
from safety_detection.models import Camera, DetectionClasses, Image

logging.basicConfig(level=logging.DEBUG)


class DetectionSaver:
    def __init__(self, save_path: str):
        self.save_path = save_path

    def save_detection(self, frame, class_name: str, camera_ip: str):
        camera_info = self.get_camera_and_class_ids(camera_ip, class_name)
        if camera_info:
            self._save_frame_and_database(frame, class_name, camera_info, camera_ip)
        else:
            logging.warning("Camera info not found. Skipping saving and database operations.")

    def _save_frame_and_database(self, frame, class_name: str, camera_info: tuple, camera_ip: str):
        camera_id, class_name_id = camera_info
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{camera_ip}_{class_name}_{timestamp}.jpeg"
        filepath = os.path.join(self.save_path, filename)

        try:
            cv2.imwrite(filepath, frame)
            self._save_to_database(camera_id, class_name_id, filename)
        except Exception as e:
            logging.error(f"Error saving frame: {e}")

    @staticmethod
    def get_camera_and_class_ids(camera_ip: str, class_name: str) -> tuple:
        try:
            camera = Camera.objects.get(ip_address=camera_ip)
            class_obj = DetectionClasses.objects.get(name=class_name)
            return camera.id, class_obj.id
        except Camera.DoesNotExist:
            logging.warning(f"Camera with IP {camera_ip} does not exist.")
        except DetectionClasses.DoesNotExist:
            logging.warning(f"Detection class {class_name} does not exist.")
        return None

    @staticmethod
    def _save_to_database(camera_id: int, class_name_id: int, filename: str):
        Image.objects.create(
            camera_id=camera_id,
            class_name_id=class_name_id,
            image_file=filename
        )
        logging.info('Record saved in DB')
