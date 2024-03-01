from django.core.paginator import Paginator
from django.http.response import StreamingHttpResponse, HttpResponseNotFound
from django.shortcuts import render
import ast

from filters.views import get_filtered_data
from safety_detection.alarm_detection.FireDetection import FireDetection
from safety_detection.alarm_detection.HelmetDetection import HelmetHead
from safety_detection.models import Permission
from safety_detection.video_stream.LiveVideoStream import VideoCamera


def get_camera_info(user):
    camera_info = {}
    permissions = Permission.objects.filter(user_id=user.id)

    # Filter permissions based on the provided cameraIP, if any

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


def index(request, camera_ip=None):
    camera_info = get_camera_info(request.user)

    if camera_ip:  # Filter camera IPs if camera_ip is provided
        camera_ip = ast.literal_eval(camera_ip)
        camera_info = {ip: camera_info[ip] for ip in camera_ip['cameraIP'] if ip in camera_info}

    camera_ips = list(camera_info.keys())
    paginator = Paginator(camera_ips, 2)  # Assuming you want 2 camera IPs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'safety_detection/main.html', {'page_obj': page_obj, 'camera_info': camera_info})


def video_feed(request, camera_ip):
    logged_in_user = request.user
    camera_info = get_camera_info(logged_in_user)

    if camera_ip in camera_info:
        camera_data = camera_info[camera_ip]
        video_url = (
            f"rtsp:/{camera_data['camera_login']}:{camera_data['camera_password']}"
            f"@{camera_ip}:{camera_data['rtsp_port']}"
            f"/cam/realmonitor?channel={camera_data['channel_id']}&subtype=0&unicast=true&proto=Onvif")

        return StreamingHttpResponse(VideoCamera.gen_stream(VideoCamera(video_url)),
                                     content_type='multipart/x-mixed-replace; boundary=frame')
    else:
        return HttpResponseNotFound('Camera not found')
