from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.users.views.auth import LoginTemplateView, get_csrf_token, LoginView, LogoutView, UserDetailView
from apps.users.views.modules import ModuleViewSet
from apps.users.views.sender import UserManagementAPIView, UserManagementView, UserViewSet
from apps.users.views.users import UserProfileDetailView, UserProfileUpdateView  # Asegúrate de importar LoginView

router = DefaultRouter()
router.register(r'modules', ModuleViewSet)
router.register(r'api-users', UserViewSet)

app_name = 'users'

urlpatterns = [
    path('', include(router.urls)),
    path('csrf/', get_csrf_token, name='csrf'),
    path('login/', LoginView.as_view(), name='login'),
    path('auth/', LoginTemplateView.as_view(), name='auth'),
    path('dashboard/', UserManagementView.as_view(), name='dashboard'),
    path('request/api-users', UserManagementAPIView.as_view(), name='user_api'),
    path('request/api-users/<int:pk>/', UserManagementAPIView.as_view(), name='user_api_detail'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('user/', UserDetailView.as_view(), name='user-detail'),
    path('profile/', UserProfileDetailView.as_view(), name='user_profile_detail'),
    path('profile/edit/', UserProfileUpdateView.as_view(), name='user_profile_edit'),
]