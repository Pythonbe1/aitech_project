from django.contrib import admin

from .models import Camera, Permission, DetectionClasses

admin.site.register(Camera)
admin.site.register(Permission)
admin.site.register(DetectionClasses)
