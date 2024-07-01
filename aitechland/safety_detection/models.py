import cv2
from django.contrib.auth.models import User as AuthUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django import forms


class DetectionClasses(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'detection_class'
        managed = True


class CameraCredential(models.Model):
    credential_name = models.CharField(max_length=256, null=True)
    camera_login = models.CharField(max_length=256, null=False)
    camera_password = models.CharField(max_length=256, null=False)

    def __str__(self):
        return self.credential_name

    class Meta:
        db_table = 'camera_credential'
        managed = True


class Camera(models.Model):
    detect_names = models.ManyToManyField(DetectionClasses)
    area_name = models.CharField(max_length=256)
    ip_address = models.CharField(max_length=100)
    rtsp_port = models.IntegerField()
    channel_id = models.IntegerField()
    credential_for_ip = models.ForeignKey(CameraCredential, on_delete=models.CASCADE)
    is_run_daemon = models.BooleanField(default=False)  # Add this line

    def __str__(self):
        return f'{self.area_name} {self.ip_address}'

    class Meta:
        db_table = 'camera'
        managed = True


class ROICoordinates(models.Model):
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    roi_data = models.TextField(default='[]')  # Store as a JSON string

    def __str__(self):
        return f"{self.camera} ROI {self.roi_data}"

    def save_roi_data(self, roi_data):
        self.roi_data = roi_data
        self.save()

    class Meta:
        db_table = 'roi_coordinates'
        managed = True


class ROICoordinatesForm(forms.ModelForm):
    roi_data = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = ROICoordinates
        fields = ['camera', 'roi_data']


class Permission(models.Model):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE)
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)

    class Meta:
        db_table = 'permission'
        managed = True

    def __str__(self):
        return f'{self.user} {self.camera}'


class Image(models.Model):
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    class_name = models.ForeignKey(DetectionClasses, on_delete=models.CASCADE)
    image_file = models.CharField(max_length=100)
    create_date = models.DateField(auto_now_add=True)  # Separate field for date
    create_time = models.TimeField(auto_now_add=True)  # Separate field for time

    def __str__(self):
        return f'Image for {self.camera} - Class: {self.class_name}'

    class Meta:
        db_table = 'image'
        managed = True


class CameraState(models.Model):
    id = models.AutoField(primary_key=True)
    camera_ip = models.CharField(max_length=100, unique=True)  # Assuming camera_ip is unique
    state = models.CharField(max_length=100, default='Online')
    create_date = models.DateField(auto_now=True)
    create_time = models.TimeField(auto_now=True)

    class Meta:
        db_table = 'camera_state'
        managed = True


@receiver(post_save, sender=ROICoordinates)
def capture_frame(sender, instance, **kwargs):
    camera = instance.camera
    credential = camera.credential_for_ip
    video_url = (
        f"rtsp://{credential.camera_login}:{credential.camera_password}@{camera.ip_address}:{camera.rtsp_port}"
        f"/cam/realmonitor?channel={camera.channel_id}&subtype=0&unicast=true&proto=Onvif"
    )

    cap = cv2.VideoCapture(video_url)
    ret, frame = cap.read()

    if ret:
        frame_path = f'media/roi_frame_{instance.id}.jpg'
        cv2.imwrite(frame_path, frame)
        print(f"Frame captured and saved at {frame_path}")
    else:
        print("Failed to capture frame from camera.")

    cap.release()