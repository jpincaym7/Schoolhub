from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import login, logout
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.http import JsonResponse
import json
from apps.users.serializers import LoginSerializer, UserSerializer

class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    template_name = 'security/login.html'

    def get_dashboard_url(self, user):
        """
        Determina la URL del dashboard según el tipo de usuario.
        """
        user_type_mapping = {
            'admin': 'dashboard',
            'teacher': 'dashboard',
            'parent': 'dashboard',
            'student': 'dashboard',  # Dashboard común para todos los tipos
        }
        
        # Obtener la URL según el tipo de usuario (todos redirigen al mismo dashboard)
        url_name = user_type_mapping.get(user.user_type, 'dashboard')
        return reverse(url_name)

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return JsonResponse({
                'success': True,
                'redirect_url': self.get_dashboard_url(request.user)
            })
        return render(request, self.template_name)

    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        try:
            # Manejar datos JSON desde la solicitud AJAX
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
            
            serializer = self.serializer_class(data=data)
            
            if serializer.is_valid():
                user = serializer.validated_data['user']
                login(request, user)
                
                user_serializer = UserSerializer(user)
                redirect_url = self.get_dashboard_url(user)
                
                return JsonResponse({
                    'success': True,
                    'user': user_serializer.data,
                    'redirect_url': redirect_url
                })
            
            return JsonResponse({
                'success': False,
                'message': 'Credenciales inválidas'
            }, status=401)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Formato de datos inválido'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            logout(request)  # Cerrar sesión del usuario
            return JsonResponse({
                'success': True,
                'message': 'Has cerrado sesión correctamente',
                'redirect_url': reverse('users:login')  # Redirige a la página de login
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)