from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Add any additional user profile information here, if needed
    class Meta:
        db_table = 'user'
        managed = False


class DetectionClasses(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'detection_class'
        managed = False


class Camera(models.Model):
    detect_name = models.ForeignKey(DetectionClasses, on_delete=models.CASCADE)
    ip_address = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'camera'
        managed = False


class Permission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)

    # Add any additional permission information here, like roles
    class Meta:
        db_table = 'permission'
        managed = False


class Image(models.Model):
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    class_name = models.CharField(max_length=100)
    image_file = models.ImageField(upload_to='images/')

    class Meta:
        db_table = 'image'
        managed = False
