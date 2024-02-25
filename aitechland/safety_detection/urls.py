from django.urls import path
from . import views

app_name = 'safety_detection'

urlpatterns = [
    path('video_feed/<int:camera_index>/', views.video_feed, name='video_feed'),
    path('get-camera-ips/', views.get_camera_ips, name='get_camera_ips'),  # Add this line for the new view
    path('', views.index, name='index'),

    # Other URL patterns...
]
