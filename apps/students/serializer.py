from rest_framework import serializers
from django.db.models import Count
from apps.students.models import Student
import datetime

class StudentSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Student con validaciones personalizadas y
    generación automática de IDs estudiantiles.
    """
    photo = serializers.ImageField(
        required=False, allow_null=True, use_url=True
    )

    class Meta:
        model = Student
        fields = [
            'id', 'first_name', 'last_name', 'student_id', 'birth_date',
            'parent', 'grade', 'parallel', 'academic_year', 'is_active', 'photo'
        ]
        read_only_fields = ['student_id']

    def validate_parent(self, value):
        # Validación de padres como antes
        if self.instance:
            if self.instance.parent_id == value.id:
                return value

        student_count = Student.objects.filter(
            parent=value,
            is_active=True
        ).count()

        if student_count >= 2:
            raise serializers.ValidationError(
                "Este representante ya tiene el máximo de 2 estudiantes permitidos."
            )
        return value

    def validate_birth_date(self, value):
        # Validación de fecha de nacimiento como antes
        today = datetime.date.today()
        age = today.year - value.year - (
            (today.month, today.day) < (value.month, value.day)
        )
        
        if value > today:
            raise serializers.ValidationError(
                "La fecha de nacimiento no puede ser futura."
            )
        if age < 3 or age > 20:
            raise serializers.ValidationError(
                "La edad del estudiante debe estar entre 3 y 20 años."
            )
        return value

    def _generate_student_id(self):
        # Generar ID de estudiante como antes
        current_year = datetime.date.today().year
        last_student = Student.objects.filter(
            student_id__startswith=f"{current_year}-"
        ).order_by('-student_id').first()

        if last_student:
            last_number = int(last_student.student_id.split('-')[1])
            new_number = last_number + 1
        else:
            new_number = 1

        return f"{current_year}-{new_number:04d}"

    def create(self, validated_data):
        validated_data['student_id'] = self._generate_student_id()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('student_id', None)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['full_name'] = f"{instance.first_name} {instance.last_name}"
        return data