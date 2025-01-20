from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.users.views.auth import LoginView, LogoutView  # Asegúrate de importar LoginView
from apps.users.views.assingment import UserManagementAPIView, UserManagementView, UserViewSet
from apps.users.views.modules.dashboard import ModuleManagementView
from apps.users.views.modules.modules import ModulePermissionViewSet, ModuleViewSet

router = DefaultRouter()
router.register(r'api', UserViewSet)
router.register(r'modules', ModuleViewSet)
router.register(r'module_permissions', ModulePermissionViewSet)

app_name = 'users'

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('management/', ModuleManagementView.as_view(), name='module_management'),
    path('management-users/', UserManagementView.as_view(), name='user_management'),
    path('request/api-users', UserManagementAPIView.as_view(), name='user_api'),
    path('request/api-users/<int:pk>/', UserManagementAPIView.as_view(), name='user_api_detail'),
]