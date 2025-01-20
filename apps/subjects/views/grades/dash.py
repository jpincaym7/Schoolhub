from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.subjects.models import Subject, ActivityTemplate, Activity, AcademicPeriod
from django.core.exceptions import PermissionDenied

class SubjectListView(LoginRequiredMixin, ListView):
    """Vista para listar las materias del profesor"""
    model = Subject
    template_name = 'subjects/subject_list.html'
    context_object_name = 'subjects'

    def get_queryset(self):
        """Filtrar materias por el profesor actual"""
        return Subject.objects.filter()

class SubjectActivitiesView(LoginRequiredMixin, DetailView):
    """Vista para mostrar y gestionar actividades de una materia"""
    model = Subject
    template_name = 'subjects/subject_activities.html'
    context_object_name = 'subject'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Añadir el ID de la materia para uso en JavaScript
        context['subject_id'] = self.object.id
        return context


class ActivityGradesView(LoginRequiredMixin, DetailView):
    """Vista para gestionar las calificaciones de una actividad"""
    model = ActivityTemplate
    template_name = 'subjects/activity_grades.html'
    context_object_name = 'activity'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activity_id'] = self.object.id
        context['activities'] = Activity.objects.filter(template=self.object)
        activity_id = self.kwargs.get('activity_id')  # Obtiene el ID de la URL
        if activity_id:
            context['selected_activity'] = Activity.objects.get(id=activity_id)
        
        print(context) 

        return context
