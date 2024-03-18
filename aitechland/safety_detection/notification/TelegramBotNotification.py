import requests


class TelegramNotification:
    @staticmethod
    def send_telegram_image_notification(token, bot_message, chat_id, image):
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        data = {
            "chat_id": chat_id,
            "caption": bot_message
        }
        files = {
            "photo": ("image.jpg", image)
        }

        response = requests.post(url, data=data, files=files)
        return response.json()

    @staticmethod
    def send_telegram_text_notification(token, bot_message, chat_id):
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        chat_id = chat_id
        data = {
            "chat_id": chat_id,
            "text": bot_message
        }
        requests.post(url, json=data)
