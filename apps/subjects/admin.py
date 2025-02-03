from django.contrib import admin
from apps.students.models import DetalleMatricula, DetalleMatriculaTrimestre, Estudiante, Matricula
from apps.subjects.models.Curso import Curso
from apps.subjects.models.Especialidad import Especialidad
from apps.subjects.models.Teacher import Profesor
from apps.subjects.models.academic import PeriodoAcademico, Trimestre
from django.utils.translation import gettext_lazy as _
from apps.subjects.models.activity import Calificacion, PromedioAnual
from apps.subjects.models.grades import AsignacionProfesor, AsignacionProfesorTrimestre
from django.utils.html import format_html
from apps.subjects.serializers import calificaciones

@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'materia', 'parcial', 'promedio_final')
    list_filter = ('asignacion_profesor__materia', 'parcial')
    search_fields = ('detalle_matricula__matricula__estudiante__usuario__first_name',
                    'detalle_matricula__matricula__estudiante__usuario__last_name')
    
    def estudiante(self, obj):
        return obj.detalle_matricula.matricula.estudiante

    def materia(self, obj):
        return obj.detalle_matricula.materia

@admin.register(PromedioAnual)
class PromedioAnualAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'materia', 'promedio_final')
    search_fields = ('detalle_matricula__matricula__estudiante__usuario__first_name',
                    'detalle_matricula__matricula__estudiante__usuario__last_name')
    
    def estudiante(self, obj):
        return obj.detalle_matricula.matricula.estudiante

    def materia(self, obj):
        return obj.detalle_matricula.materia

class DetalleMatriculaInline(admin.TabularInline):
    model = DetalleMatricula
    extra = 1
    readonly_fields = ('fecha_agregada',)

@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ('get_nombre_completo', 'curso', 'get_email')
    list_filter = ('curso',)
    search_fields = ('usuario__first_name', 'usuario__last_name', 'usuario__email')

    def get_queryset(self, request):
        # Filtra los Estudiantes solo con user_type 'estudiante'
        queryset = super().get_queryset(request)
        return queryset.filter(usuario__user_type='estudiante')
    
    def get_nombre_completo(self, obj):
        return f"{obj.usuario.first_name} {obj.usuario.last_name}"
    get_nombre_completo.short_description = 'Nombre Completo'
    
    def get_email(self, obj):
        return obj.usuario.email
    get_email.short_description = 'Email'
    

class DetalleMatriculaTrimestreInline(admin.TabularInline):
    model = DetalleMatriculaTrimestre
    extra = 0
    can_delete = False
    readonly_fields = ['trimestre']
    
    def has_add_permission(self, request, obj=None):
        return False

class DetalleMatriculaInline(admin.TabularInline):
    model = DetalleMatricula
    extra = 1
    show_change_link = True
    fields = ['materia', 'fecha_agregada']
    readonly_fields = ['fecha_agregada']

@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ['numero_matricula', 'estudiante', 'periodo', 'fecha_inscripcion', 'get_materias_count']
    list_filter = ['periodo', 'fecha_inscripcion']
    search_fields = ['numero_matricula', 'estudiante__usuario__first_name', 'estudiante__usuario__last_name']
    readonly_fields = ['fecha_inscripcion']  # Eliminamos 'numero_matricula' para que sea editable
    inlines = [DetalleMatriculaInline]

    def get_materias_count(self, obj):
        return obj.materias.count()
    get_materias_count.short_description = 'Número de Materias'

@admin.register(DetalleMatricula)
class DetalleMatriculaAdmin(admin.ModelAdmin):
    list_display = ['matricula', 'materia', 'fecha_agregada', 'get_trimestres_count']
    list_filter = ['materia', 'fecha_agregada']
    search_fields = ['matricula__numero_matricula', 'materia__nombre']
    readonly_fields = ['fecha_agregada']
    inlines = [DetalleMatriculaTrimestreInline]
    
    def get_trimestres_count(self, obj):
        return obj.trimestres.count()
    get_trimestres_count.short_description = 'Número de Trimestres'

@admin.register(DetalleMatriculaTrimestre)
class DetalleMatriculaTrimestreAdmin(admin.ModelAdmin):
    list_display = ['detalle_matricula', 'trimestre']
    list_filter = ['trimestre']
    search_fields = ['detalle_matricula__matricula__numero_matricula']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Profesor)
class ProfesorAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'especialidad', 'materias_list')
    list_filter = ('especialidad',)
    search_fields = ('usuario__first_name', 'usuario__last_name', 'especialidad__nombre')
    ordering = ('usuario__last_name', 'usuario__first_name')

    def materias_list(self, obj):
        """Muestra las materias asignadas al profesor."""
        return ", ".join([materia.nombre for materia in obj.materias.all()])
    materias_list.short_description = "Materias"

@admin.register(AsignacionProfesor)
class AsignacionProfesorAdmin(admin.ModelAdmin):
    list_display = ('profesor', 'materia', 'curso', 'periodo', 'get_asignaciones_trimestre')
    list_filter = ('profesor', 'materia', 'curso', 'periodo')
    search_fields = ('profesor__first_name', 'materia__nombre', 'curso__nombre', 'periodo__nombre')
    ordering = ('periodo', 'curso', 'materia', 'profesor')

    def get_asignaciones_trimestre(self, obj):
        return ", ".join([str(trimestre) for trimestre in obj.trimestres.all()])
    get_asignaciones_trimestre.short_description = _('Trimestres Asignados')
    
    def save_model(self, request, obj, form, change):
        # Guardamos la asignación y los trimestres relacionados
        super().save_model(request, obj, form, change)
        
        # Aseguramos que las asignaciones de trimestres se hayan creado
        if not change:  # Solo si es una nueva asignación
            for trimestre in obj.curso.trimestres.all():
                AsignacionProfesorTrimestre.objects.get_or_create(
                    asignacion=obj,
                    trimestre=trimestre
                )

@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion_corta')  # Campos visibles en la lista
    search_fields = ('nombre',)  # Búsqueda por nombre
    list_filter = ('nombre',)  # Filtros laterales
    ordering = ('nombre',)  # Ordenar alfabéticamente por nombre
    readonly_fields = ('descripcion_corta',)  # Campo de solo lectura en el formulario
    fieldsets = (
        ('Información General', {
            'fields': ('nombre', 'descripcion', 'descripcion_corta')
        }),
    )
    
    def descripcion_corta(self, obj):
        """Mostrar una versión abreviada de la descripción."""
        return obj.descripcion[:50] + "..." if len(obj.descripcion) > 50 else obj.descripcion
    descripcion_corta.short_description = "Descripción Corta"
    
@admin.register(PeriodoAcademico)
class PeriodoAcademicoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_inicio', 'fecha_fin', 'activo')  # Campos visibles en la lista
    list_filter = ('activo', 'fecha_inicio', 'fecha_fin')  # Filtros laterales
    search_fields = ('nombre',)  # Búsqueda por nombre
    ordering = ('-fecha_inicio',)  # Ordenación descendente por fecha de inicio
    date_hierarchy = 'fecha_inicio'  # Navegación jerárquica por fecha
    fieldsets = (
        (None, {
            'fields': ('nombre', 'activo')
        }),
        (_('Fechas'), {
            'fields': ('fecha_inicio', 'fecha_fin'),
            'classes': ('collapse',),  # Permite colapsar esta sección
        }),
    )
    actions = ['desactivar_periodos', 'activar_periodos']

    def desactivar_periodos(self, request, queryset):
        queryset.update(activo=False)
        self.message_user(request, _('Los periodos seleccionados han sido desactivados.'))
    desactivar_periodos.short_description = _('Desactivar periodos seleccionados')

    def activar_periodos(self, request, queryset):
        queryset.update(activo=True)
        self.message_user(request, _('Los periodos seleccionados han sido activados.'))
    activar_periodos.short_description = _('Activar periodos seleccionados')


@admin.register(Trimestre)
class TrimestreAdmin(admin.ModelAdmin):
    list_display = ('trimestre', 'periodo')
    list_filter = ('trimestre', 'periodo')
    search_fields = ('trimestre', 'periodo__nombre')
    ordering = ('periodo', 'trimestre')
    
@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nivel', 'especialidad', 'periodo')
    list_filter = ('nivel', 'especialidad', 'periodo')
    search_fields = ('nombre', 'especialidad__nombre', 'periodo__nombre')
    ordering = ('periodo', 'nivel')
    filter_horizontal = ('trimestres',)  # Esto permite una interfaz para añadir trimestres en el admin

    def save_model(self, request, obj, form, change):
        # Guardamos el curso y los trimestres
        super().save_model(request, obj, form, change)
        # Después de guardar el curso, nos aseguramos de que tenga los tres trimestres
        if obj.periodo:
            for num_trimestre in ['1', '2', '3']:
                trimestre, created = Trimestre.objects.get_or_create(
                    periodo=obj.periodo,
                    trimestre=num_trimestre
                )
                obj.trimestres.add(trimestre)