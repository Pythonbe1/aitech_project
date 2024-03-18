from django.urls import path
from . import views

app_name = 'safety_detection'

urlpatterns = [
    # Update the URL pattern to accept camera IP as a parameter
    path('video_feed/<str:camera_ip>/', views.video_feed, name='video_feed'),
    path('index/<str:camera_ip>/', views.index, name='index'),  # Add this line
    path('alarm_show/<str:camera_ip>/', views.alarm_show, name='alarm_show'),
    path('', views.index, name='index'),
    path('alarm_index/', views.alarm_index, name='alarm_index'),
    path('alarm_index/<str:filter_param>', views.alarm_index, name='alarm_index'),
    path('alarm_index_export/', views.alarm_index_export, name='alarm_index_export'),
    path('index_processed/', views.processed_index, name='processed_index'),  # Add this line
    path('index_processed/<str:filter_param>', views.processed_index, name='processed_index'),  # Add this line
    path('video_feed_gen/<str:camera_ip>/', views.video_feed_gen, name='video_feed_gen'),
    path('monitoring_index/', views.monitoring_index, name='monitoring_index')

]
