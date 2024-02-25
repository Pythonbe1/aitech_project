from django.urls import path
from . import views

app_name = 'safety_detection'

urlpatterns = [
    path('video_feed/<int:camera_index>/', views.video_feed, name='video_feed'),
    path('', views.index, name='index'),

    # Other URL patterns...
]
