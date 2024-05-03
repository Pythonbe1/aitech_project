from ultralytics import YOLO


class FireDetection:
    @staticmethod
    def get_fire_detection(path_weights, frame):
        model = YOLO(path_weights)
        results = model.predict(frame, conf=0.3)
        annotated_frame = results[0].plot(conf=False)
        return annotated_frame
