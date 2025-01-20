from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URLs que no requieren autenticación
        exempt_urls = [
            '/users/login/',
            '/admin/login/',
            '/admin/',
        ]
        
        # Verificar si el usuario no está autenticado y la URL no está exenta
        if not request.user.is_authenticated and request.path_info not in exempt_urls:
            # Guardar la URL actual para redirigir después del login
            request.session['next'] = request.path_info
            return redirect('users:login')
            
        response = self.get_response(request)
        return response