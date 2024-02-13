from django.db import models
from django.contrib.auth.models import User as AuthUser


class DetectionClasses(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'detection_class'
        managed = True


class Camera(models.Model):
    detect_names = models.ManyToManyField(DetectionClasses)
    area_name = models.CharField(max_length=256)
    ip_address = models.CharField(max_length=100)

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

# class Image(models.Model):
#     camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
#     class_name = models.CharField(max_length=100)
#     image_file = models.ImageField(upload_to='images/')
#
#     class Meta:
#         db_table = 'image'
#         managed = False
