from django.urls import path
from . import views


app_name = 'safety_detection'

urlpatterns = [
    path('alarm_show/<str:camera_ip>/', views.alarm_show, name='alarm_show'),
    path('alarm_index/', views.alarm_index, name='alarm_index'),
    path('alarm_index/<str:filter_param>/', views.alarm_index, name='alarm_index'),
    path('alarm_index_export/', views.alarm_index_export, name='alarm_index_export'),
    path('monitoring_index/', views.monitoring_index, name='monitoring_index'),
    path('analysis/', views.analysis, name='analysis'),
    path('get_camera_frame/<int:camera_id>/', views.get_camera_frame, name='get_camera_frame'),

]
