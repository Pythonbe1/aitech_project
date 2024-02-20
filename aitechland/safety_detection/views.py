from django.http.response import StreamingHttpResponse, HttpResponseNotFound
from django.shortcuts import render

from safety_detection.models import Permission, Camera
from safety_detection.video_stream.LiveVideoStream import VideoCamera


# Fetch camera IPs once
def get_camera_ips(user):
    camera_ids = Permission.objects.filter(user_id=user.id).values_list('camera_id', flat=True)
    return Camera.objects.filter(id__in=camera_ids).values_list('ip_address', flat=True)


# Create generator function for video feed
def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


# View function for both video feeds
def video_feed(request, camera_index):
    logged_in_user = request.user
    ip_cameras = get_camera_ips(logged_in_user)

    if camera_index < len(ip_cameras):
        video_url = f"rtsp:/admin:12345678a@{ip_cameras[camera_index]}:554/Streaming/Channels/1"
        return StreamingHttpResponse(gen(VideoCamera(video_url)),
                                     content_type='multipart/x-mixed-replace; boundary=frame')
    else:
        return HttpResponseNotFound('Camera not found')


def index(request):
    ip_cameras = get_camera_ips(request.user)
    camera_indexes = range(len(ip_cameras))
    return render(request, 'safety_detection/main.html', {'camera_indexes': camera_indexes})
