from ultralytics import YOLO


class FireDetection:
    @staticmethod
    def get_fire_detection(path_weights, frame):
        model = YOLO(path_weights)
        results = model(frame)
        annotated_frame = results[0].plot()
        return annotated_frame
