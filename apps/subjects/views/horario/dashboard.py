from rest_framework import serializers, viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import transaction
from datetime import datetime, time
from apps.subjects.models.Horario import HorarioAtencion
from apps.subjects.models.Teacher import Profesor
from apps.subjects.serializers.horario import HorarioAtencionSerializer
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.decorators.http import require_GET

class HorariosAtencionView(LoginRequiredMixin, TemplateView):
    template_name = 'teacher/horarios/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            # Get the professor profile for the logged-in user
            profesor = Profesor.objects.get(usuario=self.request.user)
            context['profesor_id'] = profesor.id
            context['profesor_nombre'] = f"{profesor.usuario.first_name} {profesor.usuario.last_name}"
        except Profesor.DoesNotExist:
            context['profesor_id'] = None
            context['profesor_nombre'] = None
        context['dias_semana'] = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes']
        return context

class HorarioAtencionViewSet(viewsets.ModelViewSet):
    serializer_class = HorarioAtencionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Get the queryset of HorarioAtencion objects for the current user's professor.
        """
        try:
            profesor = Profesor.objects.get(usuario=self.request.user)
            queryset = HorarioAtencion.objects.filter(profesor=profesor)
            
            # Optional filtering by day
            dia = self.request.query_params.get('dia')
            if dia:
                queryset = queryset.filter(dia=dia.upper())
                
            return queryset.order_by('dia', 'hora_inicio')
        except Profesor.DoesNotExist:
            return HorarioAtencion.objects.none()
    
    def perform_create(self, serializer):
        """
        Ensure the horario is created for the current user's professor.
        """
        try:
            profesor = Profesor.objects.get(usuario=self.request.user)
            serializer.save(profesor=profesor)
        except Profesor.DoesNotExist:
            raise ValidationError(_("No se encontró el perfil de profesor para el usuario actual"))