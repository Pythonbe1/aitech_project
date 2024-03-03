from django.db import models
from django.contrib.auth.models import User as AuthUser


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

    def __str__(self):
        return f'{self.area_name} {self.ip_address}'

    class Meta:
        db_table = 'camera'
        managed = False


class Permission(models.Model):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE)
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)

    # Add any additional permission information here, like roles
    class Meta:
        db_table = 'permission'
        managed = False

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
