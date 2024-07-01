import threading
import time

from django.conf import settings

from daemon.camera_processing.camera_manager import CameraManager
from daemon.camera_processing.detection_saver import DetectionSaver
from daemon.camera_processing.frame_processor import FrameProcessor
from daemon.constants import CLASS_NAMES


class CameraStreamViewer:
    def __init__(self, video_url: str, weights_path: str, frame_rate: int = 1, save_path: str = None):
        self.camera_manager = CameraManager(video_url, frame_rate)
        self.frame_processor = FrameProcessor(weights_path, frame_rate)
        self.detection_saver = DetectionSaver(save_path or settings.MEDIA_ROOT)

        threading.Thread(target=self._read_and_process_frames, daemon=True).start()

    def start(self):
        while not self.camera_manager.stop_event.is_set():
            time.sleep(1)

    def _read_and_process_frames(self):
        while not self.camera_manager.stop_event.is_set():
            frame = self.camera_manager.read_frame()
            if frame is not None:
                result = self.frame_processor.process_frame(frame, self.camera_manager.camera_ip)
                if result is not None:
                    results, class_counts = result
                    plotted_frame = results.plot(conf=False)
                    class_name = next(class_name for class_name in CLASS_NAMES if class_name in class_counts)
                    self.detection_saver.save_detection(plotted_frame, class_name, self.camera_manager.camera_ip)

    def release(self):
        self.camera_manager.release()
