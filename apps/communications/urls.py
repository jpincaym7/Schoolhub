from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.communications.views.TeacherOffice import TeacherOfficeHoursViewSet, OfficeHoursTemplateView

app_name = 'communications'

router = DefaultRouter()
router.register('office-api', TeacherOfficeHoursViewSet, basename='office-hours')

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
    
    # Template view
    path('office-hours/', OfficeHoursTemplateView.as_view(), name='office-hours'),
]