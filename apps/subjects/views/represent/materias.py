from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.students.models import Student
from apps.subjects.models import Subject
from apps.users.decorators import module_permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from apps.students.models import Student
from apps.subjects.models import Subject, Activity, PartialGrade, QuimesterGrade
from django.db.models import Prefetch

class StudentSubjectsView(LoginRequiredMixin, TemplateView):
    template_name = 'subjects/materias-dashboard.html'

    @module_permission_required('ASIG#1', 'view')
    def dispatch(self, *args, **kwargs):
        if self.request.user.user_type != 'parent':
            raise PermissionDenied("Solo los representantes pueden acceder a esta vista.")
        return super().dispatch(*args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener al representante actual
        parent = self.request.user
        
        # Obtener los estudiantes relacionados con este representante
        students = Student.objects.filter(parent=parent)
        
        # Crear un diccionario para almacenar las materias por estudiante
        student_subjects = {}
        
        for student in students:
            # Obtener las materias a través de las calificaciones parciales
            subjects = Subject.objects.filter(
                activity__student=student
            ).distinct().select_related('teacher')
            
            # Almacenar las materias para este estudiante
            student_subjects[student] = subjects
        
        context['student_subjects'] = student_subjects
        return context