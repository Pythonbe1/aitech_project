from django.contrib import admin
from .models import UserProfile, Camera, Permission, Image, DetectionClasses

admin.site.register(UserProfile)
admin.site.register(Camera)
admin.site.register(Permission)
admin.site.register(Image)
admin.site.register(DetectionClasses)
