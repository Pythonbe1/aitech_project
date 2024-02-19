import cv2
from django.http import StreamingHttpResponse
from django.views.generic import TemplateView
from safety_detection.models import Permission, Camera


class VideoStreamView(TemplateView):
    template_name = 'safety_detection/main.html'

    def render_to_response(self, context, **response_kwargs):
        logged_in_user = self.request.user
        camera_ids = Permission.objects.filter(user_id=logged_in_user.id).values_list('camera_id', flat=True)
        ip_cameras = Camera.objects.filter(id__in=camera_ids).values_list('ip_address', flat=True)

        # Create a list to store VideoCapture objects for each camera
        videos = [cv2.VideoCapture(f"rtsp:/admin:12345678a@{ip}:554/Streaming/Channels/1") for ip in ip_cameras]

        def generate_frames():
            while True:
                for video in videos:
                    success, frame = video.read()
                    if not success:
                        break
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        return StreamingHttpResponse(generate_frames(), content_type='multipart/x-mixed-replace; boundary=frame')


