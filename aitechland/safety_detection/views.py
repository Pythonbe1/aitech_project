import ast
from datetime import datetime
from io import BytesIO

import openpyxl
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models import F
from django.http import HttpResponse
from django.http.response import StreamingHttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render

from safety_detection.alarm_detection.FireDetection import FireDetection
from safety_detection.alarm_detection.HelmetDetection import HelmetHead
from safety_detection.models import Permission, Image, CameraState, Camera
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


def video_feed_gen(request, camera_ip):
    logged_in_user = request.user
    camera_info = get_camera_info(logged_in_user)

    if camera_ip in camera_info:
        camera_data = camera_info[camera_ip]

        video_url = (
            f"rtsp:/{camera_data['camera_login']}:{camera_data['camera_password']}"
            f"@{camera_ip}:{camera_data['rtsp_port']}"
            f"/cam/realmonitor?channel={camera_data['channel_id']}&subtype=0&unicast=true&proto=Onvif")

        if 'fire' in camera_data['detect_names']:
            path_weights = '/home/bekbol/PycharmProjects/ai_techland_safety_detetcion/aitechland/safety_detection/weights/fire_detection.pt'
            # Use FireDetection class for detection
            detection_function = FireDetection.get_fire_detection
            telegram_message = 'FIRE is detected!'
            video_url = (
                f"rtsp:/{camera_data['camera_login']}:{camera_data['camera_password']}"
                f"@{camera_ip}:{camera_data['rtsp_port']}"
                f"/Streaming/Channels/{camera_data['channel_id']}")
        else:
            path_weights = '/home/bekbol/PycharmProjects/ai_techland_safety_detetcion/aitechland/safety_detection/weights/helmet_head_detection.pt'
            # Use HelmetHead class for detection
            detection_function = HelmetHead.get_head_helmet_detection
            telegram_message = 'Not all workers are wearing helmet'

        return StreamingHttpResponse(VideoCamera.gen(VideoCamera(video_url),
                                                     path_weights,
                                                     detection_function,
                                                     telegram_message=telegram_message),
                                     content_type='multipart/x-mixed-replace; boundary=frame')

    else:
        return HttpResponseNotFound('Camera not found')


def alarm_show(request, camera_ip):
    # Filter Image instances based on the camera_ip, ordered by creation date descending
    images = Image.objects.filter(camera__ip_address=camera_ip).order_by('-create_date', '-create_time')[:9]

    # Constructing the list of dictionaries with related values
    image_data = []
    for image in images:
        image_dict = {
            'object': image.camera.area_name,
            'camera_ip': image.camera.ip_address,
            'alarm': image.class_name.name,
            'date': image.create_date,
            'time': image.create_time,
            # Use the image filename directly as the link
            'image_link': settings.MEDIA_URL + image.image_file
        }
        image_data.append(image_dict)
    # Convert list of dictionaries to JSON and return as response
    return JsonResponse(image_data, safe=False)


def alarm_index(request, filter_param=None):
    permissions = Permission.objects.filter(user_id=request.user.id)
    camera_ids = [permission.camera.id for permission in permissions]

    if filter_param:
        filter_param = ast.literal_eval(filter_param)

        camera_ip = filter_param.get('cameraIP')
        from_date = filter_param.get('fromDate')
        to_date = filter_param.get('toDate')
        detection_class = filter_param.get('detectionClass')

        filters = Q()
        if camera_ip:
            filters &= Q(camera__ip_address__in=camera_ip)
        if from_date:
            filters &= Q(create_date__gte=datetime.strptime(from_date, '%Y-%m-%d'))
        if to_date:
            filters &= Q(create_date__lte=datetime.strptime(to_date, '%Y-%m-%d'))
        if detection_class:
            filters &= Q(class_name__name=detection_class)

        images = Image.objects.filter(filters)
    else:
        images = Image.objects.filter(camera_id__in=camera_ids)

    image_data = []
    for image in images:
        image_dict = {
            'object': image.camera.area_name,
            'camera_ip': image.camera.ip_address,
            'alarm': image.class_name.name,
            'date': image.create_date,
            'time': image.create_time,
            # Use the image filename directly as the link
            'image_link': settings.MEDIA_URL + image.image_file
        }
        image_data.append(image_dict)

    paginator = Paginator(image_data, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'safety_detection/alarm.html',
                  {'page_obj': page_obj, 'image_data': image_data})


def alarm_index_export(request, filter_param=None):
    permissions = Permission.objects.filter(user_id=request.user.id)
    camera_ids = [permission.camera.id for permission in permissions]

    if filter_param:
        filter_param = ast.literal_eval(filter_param)

        camera_ip = filter_param.get('cameraIP')
        from_date = filter_param.get('fromDate')
        to_date = filter_param.get('toDate')
        detection_class = filter_param.get('detectionClass')

        filters = Q()
        if camera_ip:
            filters &= Q(camera__ip_address__in=camera_ip)
        if from_date:
            filters &= Q(create_date__gte=datetime.strptime(from_date, '%Y-%m-%d'))
        if to_date:
            filters &= Q(create_date__lte=datetime.strptime(to_date, '%Y-%m-%d'))
        if detection_class:
            filters &= Q(class_name__name=detection_class)

        images = Image.objects.filter(filters)
    else:
        images = Image.objects.filter(camera_id__in=camera_ids)

    image_data = []
    for image in images:
        image_dict = {
            'object': image.camera.area_name,
            'camera_ip': image.camera.ip_address,
            'alarm': image.class_name.name,
            'date': image.create_date,
            'time': image.create_time,
            # Use the image filename directly as the link
            'image_link': settings.MEDIA_URL + image.image_file
        }
        image_data.append(image_dict)

    # Create an Excel workbook and add data to it
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.append(['Object', 'Camera IP', 'Alarm', 'Date', 'Time', 'Image Link'])
    for item in image_data:
        worksheet.append(
            [item['object'], item['camera_ip'], item['alarm'], item['date'], item['time'], item['image_link']])

    # Save the workbook to a BytesIO buffer
    excel_buffer = BytesIO()
    workbook.save(excel_buffer)

    # Create an HttpResponse with the Excel file as an attachment
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=alarm_data.xlsx'
    response.write(excel_buffer.getvalue())

    return response


def processed_index(request, filter_param=None):
    camera_info = get_camera_info(request.user)
    camera_ips = list(camera_info.keys())

    if filter_param:
        filter_param = ast.literal_eval(filter_param)

        camera_ip = filter_param.get('cameraIP')[0]
        from_date = filter_param.get('fromDate')
        to_date = filter_param.get('toDate')
        detection_class = filter_param.get('detectionClass')
        # camera_info = {ip: camera_info[ip] for ip in camera_ip['cameraIP'] if ip in camera_info}
    else:

        camera_ip = camera_ips[0] if camera_ips else None  # Get the first IP address, or None if list is empty

    return render(request, 'safety_detection/processed.html',
                  {'first_camera_ip': camera_ip})


def monitoring_index(request):
    logged_in_user = request.user
    camera_info = get_camera_info(logged_in_user)
    camera_ips = list(camera_info.keys())

    # Retrieve CameraState objects for the camera IPs
    camera_states = CameraState.objects.filter(camera_ip__in=camera_ips)

    # Get area names for each camera_ip
    area_name_dict = {}
    for camera_ip in camera_ips:
        try:
            camera = Camera.objects.get(ip_address=camera_ip)
            area_name_dict[camera_ip] = camera.area_name
        except Camera.DoesNotExist:
            area_name_dict[camera_ip] = 'Unknown'

    data = []
    for state in camera_states:
        area_name = area_name_dict.get(state.camera_ip, 'Unknown')  # Default to 'Unknown' if no match found
        image_dict = {
            'camera_ip': state.camera_ip,
            'state': state.state,
            'date': state.create_date,
            'time': state.create_time,
            'area_name': area_name
        }
        data.append(image_dict)

    paginator = Paginator(data, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'safety_detection/monitoring.html', {'page_obj': page_obj, 'camera_states': data})
