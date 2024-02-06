from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Add any additional user profile information here, if needed


class Camera(models.Model):
    name = models.CharField(max_length=100)
    ip_address = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Add any additional camera information here


class Permission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    # Add any additional permission information here, like roles


class Image(models.Model):
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    class_name = models.CharField(max_length=100)
    image_file = models.ImageField(upload_to='images/')
    # Add any additional image-related information here, like timestamp


class DetectionClasses(models.Model):
    name = models.CharField(max_length=100)
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    # Add any additional class name information here


class test(models.Model):
    name = models.CharField(max_length=100)
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    # Add any additional class name information here
