from django.urls import path
from . import views

app_name = 'safety_detection'

urlpatterns = [
    path('', views.index, name='index'),
    path('video_feed/<int:camera_index>/', views.video_feed, name='video_feed'),
    # Other URL patterns...
]
