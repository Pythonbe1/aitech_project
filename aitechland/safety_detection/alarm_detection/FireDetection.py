import io
import time

import cv2
from ultralytics import YOLO

from safety_detection.Calculation import Calculation
from safety_detection.notification.TelegramBotNotification import TelegramNotification


class FireDetection:
    @staticmethod
    def get_fire_detection(path_weights, frame, telegram_message):
        last_notification_time = 0  # Variable to track the time of the last notification
        model = YOLO(path_weights)
        results = model.track(frame, persist=True)
        class_counts = Calculation.Calculation.count_classes(results[0].names, results[0].boxes.cls.int().tolist())
        for class_name, count in class_counts.items():
            if count != 0:
                current_time = time.time()

                if current_time - last_notification_time >= 600:
                    # Send notification via Telegram
                    token = '6924970652:AAHOLRKQLsd6sNmLzg7nRtjKHW7-dB8ohdY'
                    chat_id = -4189341273
                    bot_message = f"'{telegram_message}'"
                    image_data = cv2.imencode('.jpg', results[0].plot())[
                        1].tostring()  # Convert frame to JPEG image data
                    image = io.BytesIO(image_data)
                    TelegramNotification.send_telegram_image_notification(token, bot_message, chat_id, image)
                    last_notification_time = current_time

        annotated_frame = results[0].plot()
        return annotated_frame
