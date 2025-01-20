from django.contrib import admin
from apps.students.models import Student
from apps.users.models import User

class StudentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'student_id', 'grade', 'parallel', 'academic_year', 'is_active', 'photo')
    list_filter = ('is_active', 'academic_year', 'grade', 'parallel')
    search_fields = ('first_name', 'last_name', 'student_id', 'grade', 'parallel')
    ordering = ('last_name', 'first_name')
    
    fieldsets = (
        (None, {
            'fields': ('first_name', 'last_name', 'student_id', 'birth_date', 'parent', 'grade', 'parallel', 'academic_year', 'is_active', 'photo')
        }),
    )
    
    # Asegurarse de que los usuarios solo puedan seleccionar padres como "parent"
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'parent':
            kwargs['queryset'] = User.objects.filter(user_type='parent')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Registra el modelo y su clase de administración
admin.site.register(Student, StudentAdmin)
