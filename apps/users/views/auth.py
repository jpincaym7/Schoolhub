from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.middleware.csrf import get_token
from django.contrib.auth import login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from apps.users.models import Module, User
from apps.users.serializers import LoginSerializer, UserSerializer
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator

class LoginTemplateView(TemplateView):
    template_name = 'security/login.html'  # El template que quieres renderizar

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # Aquí puedes pasar el formulario de login al template
        return context

@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({'detail': 'CSRF cookie set'})

class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            # Utilizar LOGIN_REDIRECT_URL desde la configuración
            return Response({
                'success': True,
                'user': UserSerializer(user).data,
                'redirect_url': settings.LOGIN_REDIRECT_URL  # Redirige según la configuración
            })
        return Response(
            {'success': False, 'message': 'Credenciales inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({
            'success': True,
            'message': 'Sesión cerrada correctamente',
            'redirect_url': '/users/auth/'
        })

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
