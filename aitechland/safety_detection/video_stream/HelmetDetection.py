from ultralytics import YOLO


class HelmetHead:
    @staticmethod
    def get_head_helmet_detection(path_weights, frame):
        model = YOLO(path_weights)
        results = model.track(frame, persist=True)
        annotated_frame = results[0].plot()
        return annotated_frame
