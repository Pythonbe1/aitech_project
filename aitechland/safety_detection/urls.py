from django.urls import path
from . import views

app_name = 'safety_detection'

urlpatterns = [
    path('success/', views.VideoStreamView.as_view(), name='success'),

    # Other URL patterns...
]
