"""
URL configuration for aitechland project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static
from account.views import LoginView

urlpatterns = [
                  path('safety_detection/', include('safety_detection.urls', namespace='safety_detection')),
                  path('account/', include('account.urls')),
                  path('admin/', admin.site.urls),
                  path('filters/', include('filters.urls', namespace='filters')),
                  path('', LoginView.as_view(), name='login'),

                  # Add other URL patterns as needed
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
