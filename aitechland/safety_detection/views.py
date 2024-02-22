import cv2
from django.http.response import StreamingHttpResponse, HttpResponseNotFound
from django.shortcuts import render

from safety_detection.models import Permission
from safety_detection.alarm_detection.HelmetDetection import HelmetHead
from safety_detection.alarm_detection.FireDetection import FireDetection
from safety_detection.video_stream.LiveVideoStream import VideoCamera


# Fetch camera IPs and additional information once
def get_camera_info(user):
    camera_info = {}
    permissions = Permission.objects.filter(user_id=user.id)
    for permission in permissions:
        camera = permission.camera
        camera_credential = camera.credential_for_ip  # Get the associated CameraCredential
        detect_names = list(camera.detect_names.values_list('name', flat=True))  # Fetch detect_names
        camera_info[camera.ip_address] = {
            'rtsp_port': camera.rtsp_port,
            'channel_id': camera.channel_id,
            'camera_login': camera_credential.camera_login,  # Retrieve camera_login from CameraCredential
            'camera_password': camera_credential.camera_password,  # Retrieve camera_password from CameraCredential
            'detect_names': detect_names  # Include detect_names in the dictionary
        }
    return camera_info


# Create generator function for video feed
def gen(camera, path_weights, detection_function, telegram_message):
    while True:
        frame = camera.get_frame()
        annotated_frame = detection_function(path_weights, frame, telegram_message=telegram_message)
        ret, jpeg = cv2.imencode('.jpg', annotated_frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')


def gen_stream(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


def video_feed(request, camera_index):
    logged_in_user = request.user
    camera_info = get_camera_info(logged_in_user)

    ip_cameras = list(camera_info.keys())

    if camera_index < len(ip_cameras):
        ip_address = ip_cameras[camera_index]
        camera_data = camera_info[ip_address]
        video_url = (
            f"rtsp:/{camera_data['camera_login']}:{camera_data['camera_password']}"
            f"@{ip_address}:{camera_data['rtsp_port']}"
            f"/Streaming/Channels/{camera_data['channel_id']}")

        # Determine the path of weights based on detect_names
        if 'fire' in camera_data['detect_names']:
            path_weights = '/home/bekbol/PycharmProjects/ai_techland_safety_detetcion/aitechland/safety_detection/weights/fire_detection.pt'
            # Use FireDetection class for detection
            detection_function = FireDetection.get_fire_detection
            telegram_message = 'FIRE is detected!'
            video_url = (
                f"rtsp:/{camera_data['camera_login']}:{camera_data['camera_password']}"
                f"@{ip_address}:{camera_data['rtsp_port']}"
                f"/Streaming/Channels/{camera_data['channel_id']}")
        else:
            path_weights = '/home/bekbol/PycharmProjects/ai_techland_safety_detetcion/aitechland/safety_detection/weights/helmet_head_detection.pt'
            # Use HelmetHead class for detection
            detection_function = HelmetHead.get_head_helmet_detection
            telegram_message = 'Not all workers are wearing helmet'


        return StreamingHttpResponse(gen_stream(VideoCamera(video_url)),
                                     content_type='multipart/x-mixed-replace; boundary=frame')
    else:
        return HttpResponseNotFound('Camera not found')


def index(request):
    camera_info = get_camera_info(request.user)
    camera_indexes = range(len(camera_info))
    return render(request, 'safety_detection/main.html', {'camera_indexes': camera_indexes})
