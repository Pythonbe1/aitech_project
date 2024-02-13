from django.http import StreamingHttpResponse
from django.views.generic import TemplateView
from safety_detection.models import Permission, Camera
from safety_detection.video_stream.HikvisionStream import VideoStream


class VideoStreamView(TemplateView):
    template_name = 'safety_detection/main.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        logged_in_user = self.request.user
        camera_ids = Permission.objects.filter(user_id=logged_in_user.id).values_list('camera_id', flat=True)
        ip_cameras = Camera.objects.filter(id__in=camera_ids).values_list('ip_address', flat=True)
        context['ip_camera_urls'] = ['http://' + ip for ip in ip_cameras]
        return context

    def get(self, request, *args, **kwargs):
        ip_addresses = self.get_context_data().get('ip_camera_urls')
        username = 'admin'
        password = '12345678a'

        video_streams = []

        if ip_addresses:
            # Create a VideoStream instance for each camera
            for ip_address in ip_addresses:
                video_stream = VideoStream(ip_address, username, password)
                video_streams.append(video_stream)

        # Start streaming from all cameras
        merged_stream = zip(*[video_stream.start_video_stream() for video_stream in video_streams])
        return StreamingHttpResponse(merged_stream, content_type='multipart/x-mixed-replace; boundary=frame')
