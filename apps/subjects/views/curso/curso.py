from rest_framework import viewsets, serializers
from django.db import transaction
from apps.subjects.models.Curso import Curso
from apps.subjects.models.Especialidad import Especialidad
from apps.subjects.models.academic import PeriodoAcademico
from apps.subjects.serializers.curso import CursoSerializer
from apps.users.decorators import module_permission_required
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy


class CursoManagementView(LoginRequiredMixin, TemplateView):
    template_name = 'admin/cursos/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['especialidades'] = Especialidad.objects.filter()
        context['periodos'] = PeriodoAcademico.objects.filter()
        context['niveles'] = dict(Curso.NIVELES)
        context['api_url'] = '/subjects/api-cursos/'
        return context

class CursoViewSet(viewsets.ModelViewSet):
    serializer_class = CursoSerializer
    queryset = Curso.objects.all()
    
    @module_permission_required('CURSOS', 'view')
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @module_permission_required('CURSOS', 'view')
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @module_permission_required('CURSOS', 'create')
    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            return super().create(request, *args, **kwargs)
    
    @module_permission_required('CURSOS', 'create')
    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            return super().update(request, *args, **kwargs)
    
    @module_permission_required('CURSOS', 'edit')
    def partial_update(self, request, *args, **kwargs):
        with transaction.atomic():
            return super().partial_update(request, *args, **kwargs)
    
    @module_permission_required('CURSOS', 'delete')
    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            return super().destroy(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por nivel si se proporciona en query params
        nivel = self.request.query_params.get('nivel', None)
        if nivel:
            queryset = queryset.filter(nivel=nivel)
            
        # Filtrar por especialidad si se proporciona en query params
        especialidad_id = self.request.query_params.get('especialidad', None)
        if especialidad_id:
            queryset = queryset.filter(especialidad_id=especialidad_id)
            
        # Filtrar por periodo si se proporciona en query params
        periodo_id = self.request.query_params.get('periodo', None)
        if periodo_id:
            queryset = queryset.filter(periodo_id=periodo_id)
            
        return queryset
