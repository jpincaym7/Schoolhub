from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from apps.subjects.models import (
    QuimesterGrade,
    PartialGrade,
    Activity,
    AcademicPeriod,
    Subject
)
from apps.students.models import Student, BehaviorSummary
from apps.users.decorators import module_permission_required

class ParentDashboardView(LoginRequiredMixin, ListView):
    model = Student
    template_name = 'grades/parent_dashboard.html'
    context_object_name = 'students'

    @module_permission_required('VIRTUAL#1', 'view')
    def dispatch(self, *args, **kwargs):
        if self.request.user.user_type != 'parent':
            raise PermissionDenied("Solo los representantes pueden acceder a esta vista.")
        return super().dispatch(*args, **kwargs)

    def _get_current_school_year(self):
        school_year = self.kwargs.get('school_year')
        
        if not school_year:
            current_date = timezone.now().date()
            current_year = current_date.year
            
            if current_date.month <= 6:
                school_year = f"{current_year-1}-{current_year}"
            else:
                school_year = f"{current_year}-{current_year+1}"
            
        return school_year

    def _get_current_period(self):
        school_year = self._get_current_school_year()
        period_id = self.request.GET.get('period_id')
        
        if period_id:
            try:
                return AcademicPeriod.objects.get(id=period_id)
            except AcademicPeriod.DoesNotExist:
                pass

        current_period = AcademicPeriod.objects.filter(
            school_year=school_year
        ).order_by('-number').first()
        
        if not current_period:
            current_period = AcademicPeriod.objects.order_by(
                '-school_year', 
                '-number'
            ).first()
            
        if not current_period:
            current_period = AcademicPeriod.objects.create(
                number=1,
                school_year=school_year
            )
            
        return current_period

    def _get_quimester(self):
        return self.request.GET.get('quimester', '1')

    def get_queryset(self):
        current_period = self._get_current_period()
        quimester = self._get_quimester()
        # Prefetch relacionadas para optimizar queries
        activities_prefetch = Prefetch(
            'activities',
            queryset=Activity.objects.filter(
                academic_period=current_period,
            ).select_related('subject')
        )
        
        partial_grades_prefetch = Prefetch(
            'partial_grades',
            queryset=PartialGrade.objects.filter(
                academic_period=current_period,
            ).select_related('subject')
        )
        
        quimester_grades_prefetch = Prefetch(
            'quimester_grades',
            queryset=QuimesterGrade.objects.filter(
                academic_period=current_period,
            ).select_related('subject')
        )
        
        behavior_prefetch = Prefetch(
            'behavior_summaries',
            queryset=BehaviorSummary.objects.filter(
                academic_period=current_period,
            )
        )
        
        return Student.objects.filter(
            parent=self.request.user,
            is_active=True
        ).prefetch_related(
            activities_prefetch,
            partial_grades_prefetch,
            quimester_grades_prefetch,
            behavior_prefetch
        )

    def _get_subjects_data(self, student):
        quimester = self._get_quimester()
        subjects_data = {}
        
        for subject in Subject.objects.all():
            # Obtener calificaciones ya calculadas
            quimester_grade = next(
                (grade for grade in student.quimester_grades.all() 
                 if grade.subject_id == subject.id),
                None
            )
            
            partial_grades = [
                grade for grade in student.partial_grades.all()
                if grade.subject_id == subject.id
            ]
            
            activities = [
                activity for activity in student.activities.all()
                if activity.subject_id == subject.id
            ]

            subjects_data[subject.id] = {
                'subject': subject,
                'quimester_grade': quimester_grade,
                'partial_grades': sorted(partial_grades, key=lambda x: x.partial_number),
                'activities': sorted(
                    activities,
                    key=lambda x: (x.partial_number, x.activity_type, x.sequence_number)
                )
            }
        
        return subjects_data

    def _get_behavior_summary(self, student):
        current_period = self._get_current_period()
        try:
            summary = student.behavior_summaries.get(
                academic_period=current_period,
            )
            return {
                'positive': summary.positive_count,
                'negative': summary.negative_count,
                'neutral': summary.neutral_count,
                'partial_summaries': [
                    summary.get_partial_counts(i) for i in range(1, 4)
                ]
            }
        except BehaviorSummary.DoesNotExist:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        students_data = {}
        current_period = self._get_current_period()

        # Obtener todos los períodos académicos disponibles
        academic_periods = AcademicPeriod.objects.all().order_by('-school_year', '-number')
        
        for student in self.get_queryset():
            students_data[student.id] = {
                'student': student,
                'current_period': current_period,
                'subjects_data': self._get_subjects_data(student),
                'behavior_summary': self._get_behavior_summary(student)
            }
        print(students_data)
        context.update({
            'students_data': students_data,
            'single_student': len(students_data) == 1,
            'academic_periods': academic_periods,
            'current_period': current_period,
            'current_quimester': self._get_quimester()
        })
        
        if context['single_student']:
            student_id = list(students_data.keys())[0]
            context.update(students_data[student_id])

        return context