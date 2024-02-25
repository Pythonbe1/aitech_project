import cv2


class VideoCamera(object):
    def __init__(self, url):
        self.url = cv2.VideoCapture(url)

    def __del__(self):
        cv2.destroyAllWindows()

    def get_frame(self):
        success, imgNp = self.url.read()
        resize = cv2.resize(imgNp, (640, 480), interpolation=cv2.INTER_LINEAR)
        ret, jpeg = cv2.imencode('.jpg', resize)
        return jpeg.tobytes()

    @staticmethod
    def gen(camera, path_weights, detection_function, telegram_message):
        while True:
            frame = camera.get_frame()
            annotated_frame = detection_function(path_weights, frame, telegram_message=telegram_message)
            ret, jpeg = cv2.imencode('.jpg', annotated_frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

    @staticmethod
    def gen_stream(camera):
        while True:
            frame = camera.get_frame()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
