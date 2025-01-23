# middleware.py
from django.http import JsonResponse
from django.urls import reverse
from django.conf import settings

class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Lista de URLs que no requieren autenticación
        public_urls = [
            reverse('users:login'),
            reverse('users:csrf'),
            '/admin/login/',
        ]

        if not request.user.is_authenticated and request.path not in public_urls:
            if request.headers.get('accept') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'message': 'No autenticado',
                    'redirect_url': reverse('users:login')
                }, status=401)

        response = self.get_response(request)
        return response