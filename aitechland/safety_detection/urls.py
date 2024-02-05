# safety_detection/urls.py

from django.urls import path

from . import views

app_name = 'safety_detection'

urlpatterns = [
    path('success/', views.SuccessView.as_view(), name='success'),
    # other URL patterns
]
