import time
import logging
import multiprocessing
from multiprocessing import Pool

from django.conf import settings
from django.core.management.base import BaseCommand

from daemon.camera_processing.CameraStreamViewer import CameraStreamViewer
from safety_detection.models import Camera

logging.basicConfig(level=logging.INFO)


class Command(BaseCommand):
    help = 'Run a simple daemon'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting daemon...")
        self.daemonize()

    def daemonize(self):
        while True:
            try:
                self.stdout.write("Daemon is working...")
                self.process_cameras()
            except Exception as e:
                logging.error(f"Error in daemon process: {e}")
            time.sleep(10)  # Sleep for 10 seconds

    def process_cameras(self):
        cameras = Camera.objects.select_related('credential_for_ip').all()
        camera_data = [(camera.ip_address, camera.rtsp_port, camera.channel_id,
                        camera.credential_for_ip.camera_login, camera.credential_for_ip.camera_password)
                       for camera in cameras]
        self.start_processing(camera_data)

    def start_processing(self, data):
        num_cores = max(multiprocessing.cpu_count(), 8)  # Adjust as needed
        weights_path = getattr(settings, 'NEURAL_PATH', None)
        if not weights_path:
            logging.error("Weights path is not defined in settings.")
            return

        with Pool(processes=num_cores) as pool:
            pool.map(self.stream_camera, [(camera_data, weights_path) for camera_data in data])

    @staticmethod
    def stream_camera(args):
        camera_data, weights_path = args
        ip_address, rtsp_port, channel_id, camera_login, camera_password = camera_data
        video_url = (
            f"rtsp://{camera_login}:{camera_password}@{ip_address}:{rtsp_port}"
            f"/cam/realmonitor?channel={channel_id}&subtype=0&unicast=true&proto=Onvif"
        )
        logging.info(f"Processing camera: {video_url}")

        viewer = CameraStreamViewer(video_url, weights_path)
        try:
            viewer.start()
        finally:
            viewer.release()

    def handle_new_camera(self, camera_data):
        ip_address, rtsp_port, channel_id, camera_login, camera_password = camera_data
        video_url = (
            f"rtsp://{camera_login}:{camera_password}@{ip_address}:{rtsp_port}"
            f"/cam/realmonitor?channel={channel_id}&subtype=0&unicast=true&proto=Onvif"
        )
        logging.info(f"Handling new camera: {video_url}")

        weights_path = getattr(settings, 'NEURAL_PATH', None)
        if not weights_path:
            logging.error("Weights path is not defined in settings.")
            return

        viewer = CameraStreamViewer(video_url, weights_path)
        try:
            viewer.start()
        finally:
            viewer.release()

    def add_camera(self, camera_data):
        ip_address, rtsp_port, channel_id, camera_login, camera_password = camera_data
        logging.info(f"Adding new camera: {ip_address}")

        # Assuming Camera.objects.create(...) or similar logic to add a new camera to the database
        # After adding the camera, call handle_new_camera to start processing the new camera
        self.handle_new_camera(camera_data)

    def remove_camera(self, camera_ip):
        logging.info(f"Removing camera: {camera_ip}")

        # Assuming Camera.objects.filter(ip_address=camera_ip).delete() or similar logic to remove a camera
        # Perform any cleanup tasks as needed
