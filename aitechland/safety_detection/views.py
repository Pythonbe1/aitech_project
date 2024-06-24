import ast
import json
from datetime import datetime
from io import BytesIO

import cv2
import openpyxl
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import HttpResponse
from django.http.response import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404

from safety_detection.models import Permission, Image, CameraState, Camera, ROICoordinates


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


def analysis(request):
    # Detection Statistics
    detection_counts = list(Image.objects.values('class_name__name').annotate(count=Count('class_name__name')))

    # Camera Overview with Alert Counts
    cameras = Camera.objects.all()

    # Initialize a list to store data for each camera
    chart_data = []

    for camera in cameras:
        # Filter images for the current camera
        camera_images = Image.objects.filter(camera=camera)

        # Count detections for each type
        head_count = camera_images.filter(class_name__name='head').count()
        fire_count = camera_images.filter(class_name__name='fire').count()
        smoke_count = camera_images.filter(class_name__name='smoke').count()

        # Format the area_name and ip_address
        area_name_ip = f"{camera.area_name} ({camera.ip_address})"

        # Prepare data for the chart
        chart_data.append({
            'area_name_ip': area_name_ip,
            'head_count': head_count,
            'fire_count': fire_count,
            'smoke_count': smoke_count
        })

    # Serialize chart_data to JSON
    chart_data_json = json.dumps(chart_data)

    context = {
        'detection_counts': detection_counts,
        'chart_data_json': chart_data_json,  # Pass JSON string to template
        'cameras': cameras,
    }

    return render(request, 'safety_detection/analysis.html', context)


def get_camera_frame(request, camera_id):
    camera = get_object_or_404(Camera, id=camera_id)
    credential = camera.credential_for_ip
    video_url = (
        f"rtsp://{credential.camera_login}:{credential.camera_password}@{camera.ip_address}:{camera.rtsp_port}"
        f"/cam/realmonitor?channel={camera.channel_id}&subtype=0&unicast=true&proto=Onvif"
    )

    try:
        cap = cv2.VideoCapture(video_url)
        if not cap.isOpened():
            raise IOError(f"Unable to open video stream from {video_url}")

        ret, frame = cap.read()

        if ret:
            _, jpeg = cv2.imencode('.jpg', frame)
            cap.release()
            return HttpResponse(jpeg.tobytes(), content_type='image/jpeg')
        else:
            cap.release()
            return HttpResponse(status=500)

    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error fetching camera frame: {str(e)}")
        return HttpResponse(status=500)


from django.shortcuts import redirect


def save_rois(request):
    if request.method == 'POST':
        camera_id = request.POST.get('camera_id')
        roi_coordinates = request.POST.get('roi_coordinates')

        try:
            camera = Camera.objects.get(id=camera_id)
            rois_data = json.loads(roi_coordinates)
            roi_instance = ROICoordinates(camera=camera, roi_data=rois_data)
            roi_instance.save()
            return redirect('some_view_name')  # Adjust the redirection as needed
        except Camera.DoesNotExist:
            return HttpResponseBadRequest("Invalid camera ID")
    else:
        return HttpResponseBadRequest("Invalid request method")
