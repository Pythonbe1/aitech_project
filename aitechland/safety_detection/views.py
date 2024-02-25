import cv2
from asgiref.sync import sync_to_async
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.http.response import StreamingHttpResponse, HttpResponseNotFound
from django.shortcuts import render

from safety_detection.alarm_detection.FireDetection import FireDetection
from safety_detection.alarm_detection.HelmetDetection import HelmetHead
from safety_detection.models import Permission
from safety_detection.video_stream.LiveVideoStream import VideoCamera


def get_camera_ips(request):
    # Retrieve the user object based on your authentication logic
    user = request.user
    camera_info = get_camera_info(user)
    # Extract IP addresses and area names from camera_info
    ips_and_areas = [{'ip_address': ip, 'area_name': info['area_name']} for ip, info in camera_info.items()]
    return JsonResponse({'camera_info': ips_and_areas})


def get_camera_info(user):
    camera_info = {}
    permissions = Permission.objects.filter(user_id=user.id)
    for permission in permissions:
        camera = permission.camera
        camera_credential = camera.credential_for_ip
        detect_names = list(camera.detect_names.values_list('name', flat=True))
        # Retrieve the area name associated with the camera
        area_name = camera.area_name if camera.area_name else None
        camera_info[camera.ip_address] = {
            'rtsp_port': camera.rtsp_port,
            'channel_id': camera.channel_id,
            'camera_login': camera_credential.camera_login,
            'camera_password': camera_credential.camera_password,
            'detect_names': detect_names,
            'area_name': area_name,  # Include the area name in the dictionary
        }
    return camera_info


def index(request):
    camera_info = get_camera_info(request.user)
    camera_indexes = list(range(len(camera_info)))

    paginator = Paginator(camera_indexes, 2)  # Assuming you want 2 camera indexes per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'safety_detection/main.html', {'page_obj': page_obj})


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

        return StreamingHttpResponse(VideoCamera.gen_stream(VideoCamera(video_url)),
                                     content_type='multipart/x-mixed-replace; boundary=frame')
    else:
        return HttpResponseNotFound('Camera not found')
