from django.contrib import admin
from apps.subjects.models.academic import AcademicPeriod
from apps.subjects.models.activity import Activity, ActivityTemplate
from apps.subjects.models.grades import PartialGrade, QuimesterGrade
from  apps.subjects.models.subject import Subject



@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'credits', 'teacher')
    search_fields = ('name', 'code')
    list_filter = ('teacher',)
    ordering = ('name',)


@admin.register(AcademicPeriod)
class AcademicPeriodAdmin(admin.ModelAdmin):
    list_display = ['number', 'school_year']
    list_filter = ['number', 'school_year']
    search_fields = ['school_year']
    ordering = ['school_year', 'number']
    unique_together = ('number', 'school_year')

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    """Configuración profesional para el modelo Activity"""
    list_display = (
        'name', 
        'student', 
        'subject', 
        'academic_period', 
        'partial_number', 
        'sequence_number', 
        'activity_type', 
        'score', 
        'created_at'
    )
    list_filter = (
        'academic_period', 
        'subject', 
        'activity_type', 
        'partial_number', 
        'sequence_number'
    )
    search_fields = ('name', 'description', 'student__name', 'subject__name')
    ordering = ['academic_period', 'partial_number', 'sequence_number']
    date_hierarchy = 'created_at'
    actions = ['reset_scores']

    def reset_scores(self, request, queryset):
        """Acción personalizada para reiniciar las calificaciones"""
        updated = queryset.update(score=0)
        self.message_user(request, f"Se reiniciaron {updated} calificaciones.")
    reset_scores.short_description = "Reiniciar calificaciones seleccionadas"

@admin.register(ActivityTemplate)
class ActivityTemplateAdmin(admin.ModelAdmin):
    """Configuración profesional para el modelo ActivityTemplate"""
    list_display = (
        'name', 
        'subject', 
        'academic_period', 
        'partial_number', 
        'sequence_number', 
        'activity_type'
    )
    list_filter = ('academic_period', 'subject', 'activity_type')
    search_fields = ('name', 'description', 'subject__name')
    ordering = ['academic_period', 'partial_number', 'sequence_number']

    def create_activities_for_students(self, request, queryset):
        """Acción personalizada para crear actividades basadas en plantillas"""
        # Lógica para crear actividades
        for template in queryset:
            # Aquí puedes definir cómo obtener estudiantes específicos
            students = template.subject.students.all()
            activities = template.create_activities_for_students(students)
            self.message_user(
                request, 
                f"Se crearon {len(activities)} actividades para la plantilla '{template.name}'."
            )
    create_activities_for_students.short_description = "Crear actividades para estudiantes seleccionados"

@admin.register(PartialGrade)
class PartialGradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'academic_period', 'partial_number', 'evaluation_score', 'final_score']
    list_filter = ['partial_number', 'subject', 'student', 'academic_period']
    search_fields = ['student__name', 'subject__name']
    ordering = ['academic_period', 'partial_number']

@admin.register(QuimesterGrade)
class QuimesterGradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'academic_period', 'final_score']
    list_filter = ['subject', 'student', 'academic_period']
    search_fields = ['student__name', 'subject__name']
    ordering = ['academic_period']


