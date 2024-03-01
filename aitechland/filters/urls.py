from django.urls import path
from . import views

app_name = 'filters'

urlpatterns = [
    path('get-camera-ips/', views.get_camera_ips, name='get_camera_ips'),
    path('get-detect-names/', views.get_class_names, name='get_class_names'),
    path('get-filtered-data/', views.get_filtered_data, name='get_filtered_data'),
]