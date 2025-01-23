import random
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth.models import Permission
from apps.users.models import User
from apps.users.permissions import IsAdminUser
from apps.users.serializers import  UserCreateSerializer,  UserSerializer, UserUpdateSerializer
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
import string
from django.template.loader import render_to_string

class UserManagementView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'admin/users/dashboard.html'
    login_url = reverse_lazy('users:login')
    
    def test_func(self):
        """Verifica que el usuario tenga permisos de administrador"""
        return self.request.user.user_type == 'admin'
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        return JsonResponse({
            'error': 'No tienes permisos para acceder a esta página',
            'redirect_url': reverse_lazy('')
        }, status=403)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'section': 'user_management',
            'is_admin': self.request.user.user_type == 'admin',
            'available_user_types': [
                {'value': 'admin', 'label': 'Administrador'},
                {'value': 'teacher', 'label': 'Profesor'},
                {'value': 'student', 'label': 'Estudiante'},
            ]
        })
        return context

class UserManagementAPIView(APIView):
    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'DELETE']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get(self, request):
        users = User.objects.all().order_by('first_name')
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user_data = serializer.validated_data
            
            # Generate password
            last_name = user_data.get('last_name', '')
            phone = user_data.get('phone', '')
            password = self.generate_password(last_name, phone)
            
            # Create user with generated password
            user = User.objects.create_user(
                **user_data,
                password=password
            )
            
            # Send email for teachers and parents
            if user.user_type in ['teacher', 'estudiante']:
                self.send_registration_email(user.email, user.first_name, user.username, password, user.user_type)
            
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        serializer = UserUpdateSerializer(
            user,
            data=request.data,
            context={'request': request},
            partial=True
        )
        
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            return Response(
                {'error': 'No puedes eliminar tu propio usuario'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def generate_password(last_name, phone):
        random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=4))
        base = f"{last_name[:3].capitalize()}{phone[-4:]}"
        return f"{base}{random_suffix}"

    @staticmethod
    def send_registration_email(email, first_name, username, password, user_type):
        subject = "Registro en el Sistema Académico"
        
        # Renderiza el template de correo HTML
        message = render_to_string(
            'emails/registration_email.html',
            {
                'first_name': first_name,
                'username': username,
                'user_type': user_type,
                'password': password,
            }
        )
        
        from_email = settings.DEFAULT_FROM_EMAIL
        send_mail(
            subject,
            message,  # El contenido HTML ya es el mensaje
            from_email,
            [email],
            html_message=message  # Establece el mensaje HTML
        )

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = None
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user_type = self.request.query_params.get('user_type', None)
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        return queryset