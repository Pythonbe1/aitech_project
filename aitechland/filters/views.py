from django.http import JsonResponse

from safety_detection.models import Permission
from django.shortcuts import redirect
import ast


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


def get_camera_ips(request):
    # Retrieve the user object based on your authentication logic
    user = request.user
    camera_info = get_camera_info(user)
    # Extract IP addresses and area names from camera_info
    ips_and_areas = [{'ip_address': ip, 'area_name': info['area_name']} for ip, info in camera_info.items()]
    return JsonResponse({'camera_info': ips_and_areas})


def get_class_names(request):
    user = request.user
    camera_info = get_camera_info(user)
    class_names_set = set()  # Use set to store unique values

    # Iterate over camera_info dictionary items
    for ip, info in camera_info.items():
        detect_names = info.get('detect_names', [])
        class_names_set.update(detect_names)  # Update set with detect_names

    class_names = list(class_names_set)  # Convert set back to list
    return JsonResponse({'class_names': class_names})


def get_filtered_data(request):
    fromDate = request.GET.get('fromDate')
    toDate = request.GET.get('toDate')
    cameraIP = request.GET.get('cameraIP')
    if cameraIP:
        cameraIP = cameraIP.split(',')
    detectionClass = request.GET.get('detectionClass')
    return redirect('safety_detection:index', {'cameraIP': cameraIP,
                                               'toDate': toDate,
                                               'fromDate': fromDate,
                                               'detectionClass': detectionClass})


def get_filtered_data_alarm(request):
    fromDate = request.GET.get('fromDate')
    toDate = request.GET.get('toDate')
    cameraIP = request.GET.get('cameraIP')
    if cameraIP:
        cameraIP = cameraIP.split(',')
    detectionClass = request.GET.get('detectionClass')
    return redirect('safety_detection:alarm_index', filter_param={'cameraIP': cameraIP,
                                                                  'toDate': toDate,
                                                                  'fromDate': fromDate,
                                                                  'detectionClass': detectionClass})
