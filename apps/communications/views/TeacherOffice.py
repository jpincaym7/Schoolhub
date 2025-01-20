from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.communications.models import TeacherOfficeHours
from apps.communications.serializers.Hours import TeacherOfficeHoursSerializer, TeacherOfficeHoursListSerializer
from django.db.models import Q

class TeacherOfficeHoursViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing teacher office hours
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['teacher', 'day_of_week', 'is_active']
    search_fields = ['teacher__first_name', 'teacher__last_name', 'location']
    ordering_fields = ['day_of_week', 'start_time', 'created_at']
    ordering = ['day_of_week', 'start_time']

    def get_queryset(self):
        """
        Returns the base queryset filtered by user type
        """
        queryset = TeacherOfficeHours.objects.select_related('teacher')
        
        user = self.request.user
        if user.user_type == 'teacher':
            # Teachers only see their own office hours
            return queryset.filter(Q(teacher=user) & Q(is_active=True))
        # Other users see all active office hours
        return queryset.filter(is_active=True)

    def get_serializer_class(self):
        """
        Returns the appropriate serializer based on the action
        """
        if self.action == 'list':
            return TeacherOfficeHoursListSerializer
        return TeacherOfficeHoursSerializer

    def perform_create(self, serializer):
        """
        Saves the office hours
        """
        if self.request.user.user_type == 'teacher':
            # If the user is a teacher, automatically set them as the teacher
            serializer.save(teacher=self.request.user)
        else:
            serializer.save()

    @action(detail=False, methods=['get'])
    def my_office_hours(self, request):
        """
        Endpoint for teachers to view their office hours
        """
        if request.user.user_type != 'teacher':
            return Response(
                {'detail': _('Solo los profesores pueden acceder a este endpoint')},
                status=status.HTTP_403_FORBIDDEN
            )

        queryset = self.get_queryset()
        serializer = TeacherOfficeHoursListSerializer(queryset, many=True)
        return Response(serializer.data)

class OfficeHoursTemplateView(LoginRequiredMixin, TemplateView):
    """
    View for rendering the office hours management template
    """
    template_name = 'communications/office_hours.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context.update({
            'user_type': user.user_type,
            'page_title': _('Horarios de Atención'),
            'is_teacher': user.user_type == 'teacher',
            'days_of_week': TeacherOfficeHours.DAYS_OF_WEEK,
            'breadcrumbs': [
                {'title': _('Inicio'), 'url': '/'},
                {'title': _('Comunicaciones'), 'url': '/communications/'},
                {'title': _('Horarios de Atención'), 'active': True}
            ]
        })

        return context