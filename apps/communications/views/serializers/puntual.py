from django.utils import timezone
from rest_framework import serializers
from apps.communications.models import Asistencia
from apps.students.models import DetalleMatricula, Matricula

class DetalleMatriculaSerializer(serializers.ModelSerializer):
    materia_nombre = serializers.CharField(source='materia.nombre', read_only=True)

    class Meta:
        model = DetalleMatricula
        fields = ['id', 'materia', 'materia_nombre', 'fecha_agregada']
        read_only_fields = ['fecha_agregada']

class MatriculaSerializer(serializers.ModelSerializer):
    detallematricula_set = DetalleMatriculaSerializer(many=True, read_only=True)
    estudiante_nombre = serializers.CharField(source='estudiante.nombre', read_only=True)
    periodo_nombre = serializers.CharField(source='periodo.nombre', read_only=True)

    class Meta:
        model = Matricula
        fields = ['id', 'estudiante', 'estudiante_nombre', 'periodo', 'periodo_nombre', 
                  'numero_matricula', 'fecha_inscripcion', 'detallematricula_set']
        read_only_fields = ['fecha_inscripcion', 'numero_matricula']

    def validate(self, data):
        # Validar que el estudiante no tenga más de una matrícula por periodo
        estudiante = data.get('estudiante')
        periodo = data.get('periodo')
        
        if estudiante and periodo:
            existing_matricula = Matricula.objects.filter(
                estudiante=estudiante, 
                periodo=periodo
            ).exists()
            
            if existing_matricula:
                raise serializers.ValidationError({
                    'detail': 'El estudiante ya tiene una matrícula para este periodo académico.'
                })
        
        return data

class AsistenciaSerializer(serializers.ModelSerializer):
    estudiante_nombre = serializers.CharField(source='matricula.estudiante.nombre', read_only=True)
    materia_nombre = serializers.CharField(source='matricula.detallematricula_set.first.materia.nombre', read_only=True)

    class Meta:
        model = Asistencia
        fields = ['id', 'matricula', 'estudiante_nombre', 'materia_nombre', 
                  'fecha', 'asistio', 'justificacion']
        extra_kwargs = {
            'justificacion': {'required': False, 'allow_blank': True}
        }

    def validate(self, data):
        # Validaciones de asistencia
        matricula = data.get('matricula')
        fecha = data.get('fecha')
        
        # Verificar que la fecha no sea futura
        if fecha and fecha > timezone.now().date():
            raise serializers.ValidationError({
                'fecha': 'La fecha no puede ser futura.'
            })
        
        # Si no asistió, requiere justificación
        if not data.get('asistio', True) and not data.get('justificacion'):
            raise serializers.ValidationError({
                'justificacion': 'Se requiere una justificación cuando no se asiste.'
            })
        
        # Prevenir duplicados de asistencia
        if Asistencia.objects.filter(
            matricula=matricula, 
            fecha=fecha
        ).exists():
            raise serializers.ValidationError({
                'detail': 'Ya existe un registro de asistencia para esta fecha y matrícula.'
            })
        
        return data
    
class AsistenciaMasivaSerializer(serializers.Serializer):
    fecha_inicio = serializers.DateField(required=True)
    fecha_fin = serializers.DateField(required=True)
    matriculas = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )
    asistencias = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )

    def validate(self, data):
        fecha_inicio = data['fecha_inicio']
        fecha_fin = data['fecha_fin']
        
        # Validar que el rango de fechas sea válido
        if fecha_inicio > fecha_fin:
            raise serializers.ValidationError({
                'fecha_inicio': 'La fecha de inicio debe ser anterior a la fecha fin.'
            })
        
        # Validar que las fechas no sean futuras
        today = timezone.now().date()
        if fecha_inicio > today or fecha_fin > today:
            raise serializers.ValidationError({
                'detail': 'No se pueden registrar asistencias en fechas futuras.'
            })
        
        # Validar que el rango no sea mayor a 31 días
        if (fecha_fin - fecha_inicio).days > 31:
            raise serializers.ValidationError({
                'detail': 'El rango de fechas no puede ser mayor a 31 días.'
            })
        
        return data    

class AsistenciaCreateUpdateSerializer(serializers.ModelSerializer):
    estudiante_nombre = serializers.CharField(source='matricula.estudiante.nombre', read_only=True)
    materia_nombre = serializers.CharField(source='matricula.detallematricula_set.first.materia.nombre', read_only=True)

    class Meta:
        model = Asistencia
        fields = ['id', 'matricula', 'estudiante_nombre', 'materia_nombre', 
                  'fecha', 'asistio', 'justificacion']
        extra_kwargs = {
            'justificacion': {'required': False, 'allow_blank': True}
        }

    def validate(self, data):
        # Validaciones avanzadas de asistencia
        matricula = data.get('matricula')
        fecha = data.get('fecha')
        
        # Prevenir registro de asistencia en fechas futuras
        if fecha and fecha > timezone.now().date():
            raise serializers.ValidationError({
                'fecha': 'No se pueden registrar asistencias en fechas futuras.'
            })
        
        # Requiere justificación si no asistió
        if not data.get('asistio', True) and not data.get('justificacion'):
            raise serializers.ValidationError({
                'justificacion': 'Se requiere justificación cuando no se asiste.'
            })
        
        # Prevenir duplicados de asistencia
        if Asistencia.objects.filter(
            matricula=matricula, 
            fecha=fecha
        ).exists():
            raise serializers.ValidationError({
                'detail': 'Ya existe un registro de asistencia para esta fecha y matrícula.'
            })
        
        return data

    def create(self, validated_data):
        # Lógica personalizada de creación
        asistencia = Asistencia.objects.create(**validated_data)
        
        # Registro de log o notificación (ejemplo)
        self.log_attendance_action(asistencia, 'created')
        
        return asistencia

    def update(self, instance, validated_data):
        # Permitir solo actualizaciones específicas
        instance.asistio = validated_data.get('asistio', instance.asistio)
        instance.justificacion = validated_data.get('justificacion', instance.justificacion)
        
        # No permitir cambiar matrícula o fecha
        instance.save()
        
        # Registro de log o notificación
        self.log_attendance_action(instance, 'updated')
        
        return instance

    def log_attendance_action(self, asistencia, action):
        # Método para registrar acciones (puede integrarse con sistema de logs)
        pass