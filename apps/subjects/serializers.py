from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.subjects.models import Subject

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'first_name', 'last_name', 'email']

class SubjectSerializer(serializers.ModelSerializer):
    teacher_details = TeacherSerializer(source='teacher', read_only=True)
    
    class Meta:
        model = Subject
        fields = ['id', 'name', 'code', 'credits', 'teacher', 'teacher_details']
        extra_kwargs = {
            'teacher': {'write_only': True},
        }
    
    def validate_code(self, value):
        """
        Validate that the subject code is unique (case-insensitive)
        """
        if Subject.objects.filter(code__iexact=value).exists():
            if self.instance and self.instance.code.lower() == value.lower():
                return value
            raise serializers.ValidationError("Ya existe una materia con este código.")
        return value
    
