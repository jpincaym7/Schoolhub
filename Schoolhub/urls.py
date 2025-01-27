"""
URL configuration for Schoolhub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from apps.home.views import DashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('apps.users.urls'), name = 'users'),
    path('subjects/', include('apps.subjects.urls'), name = 'subjects'),
    path('students/', include('apps.students.urls'), name = 'students'),
    path('communications/', include('apps.communications.urls'), name = 'communications'),
    path('', DashboardView.as_view(), name='api_dashboard'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)