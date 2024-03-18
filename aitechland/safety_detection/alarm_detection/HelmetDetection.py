from ultralytics import YOLO
from safety_detection.Calculation import Calculation
from safety_detection.notification.TelegramBotNotification import TelegramNotification
import io
import time
import cv2


class HelmetHead:
    @staticmethod
    def get_head_helmet_detection(path_weights, frame, telegram_message):
        last_notification_time = 0
        model = YOLO(path_weights)
        results = model(frame)
        class_counts = Calculation.Calculation.count_classes(results[0].names, results[0].boxes.cls.int().tolist())
        if len(results[0].boxes.cls.int().tolist()) != class_counts.get('helmet', 0):
            current_time = time.time()
            # Send notification via Telegram every 10 seconds
            if current_time - last_notification_time >= 300:
                # Send notification via Telegram
                # token = '6924970652:AAHOLRKQLsd6sNmLzg7nRtjKHW7-dB8ohdY'
                # chat_id = -4189341273
                # bot_message = f"'{telegram_message}'"
                # image_data = cv2.imencode('.jpg', results[0].plot())[
                #     1].tostring()  # Convert frame to JPEG image data
                # image = io.BytesIO(image_data)
                # TelegramNotification.send_telegram_image_notification(token, bot_message, chat_id, image)
                last_notification_time = current_time

        annotated_frame = results[0].plot()

        return annotated_frame
