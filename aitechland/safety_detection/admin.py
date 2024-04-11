from django.contrib import admin

from .models import Camera, Permission, CameraCredential, DetectionClasses

admin.site.register(Camera)
admin.site.register(Permission)
admin.site.register(CameraCredential)
admin.site.register(DetectionClasses)


