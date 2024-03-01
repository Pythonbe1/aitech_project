from django.urls import path
from . import views

app_name = 'safety_detection'

urlpatterns = [
    # Update the URL pattern to accept camera IP as a parameter
    path('video_feed/<str:camera_ip>/', views.video_feed, name='video_feed'),
    path('index/<str:camera_ip>/', views.index, name='index'),  # Add this line
    path('', views.index, name='index'),

]

