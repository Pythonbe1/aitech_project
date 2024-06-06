# myapp/management/commands/run_daemon.py
import logging
import multiprocessing
import time
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

        while True:
            self.stdout.write("Daemon is working...")
            self.process_cameras()
            time.sleep(10)  # Sleep for 10 seconds

        self.stdout.write("Daemon stopped.")

    def process_cameras(self):
        cameras = Camera.objects.select_related('credential_for_ip').all()
        camera_data = [(camera.ip_address, camera.rtsp_port, camera.channel_id,
                        camera.credential_for_ip.camera_login, camera.credential_for_ip.camera_password)
                       for camera in cameras]
        self.start_processing(camera_data)

    def start_processing(self, data):
        num_cores = min(multiprocessing.cpu_count(), 8)
        pool = Pool(processes=num_cores)
        weights_path = getattr(settings, 'NEURAL_PATH', None)  # Get weights path from settings
        if weights_path:
            pool.map(self.stream_camera, [(camera_data, weights_path) for camera_data in data])
        else:
            logging.error("Weights path is not defined in settings.")
        pool.close()
        pool.join()

    @staticmethod
    def stream_camera(args):
        camera_data, weights_path = args  # Unpack the arguments tuple
        ip_address, rtsp_port, channel_id, camera_login, camera_password = camera_data
        video_url = (
            f"rtsp://{camera_login}:{camera_password}@{ip_address}:{rtsp_port}"
            f"/cam/realmonitor?channel={channel_id}&subtype=0&unicast=true&proto=Onvif"
        )
        viewer = CameraStreamViewer(video_url, weights_path)
        viewer.start()
        viewer.release()
