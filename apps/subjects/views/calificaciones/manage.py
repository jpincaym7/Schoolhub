from decimal import Decimal
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from apps.subjects.models.academic import PeriodoAcademico, Trimestre
from apps.subjects.models.activity import (
    Calificacion, PromedioAnual, PromedioTrimestre, Parcial
)
from apps.subjects.models.subject import Materia
from apps.subjects.serializers.calificaciones import (
    CalificacionSerializer, PromedioTrimestreSerializer
)

class CalManageView(TemplateView):
    template_name = 'teacher/calificaciones/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get active period first
        periodo_activo = PeriodoAcademico.objects.filter(activo=True).first()
        
        context['periodos'] = PeriodoAcademico.objects.all()
        context['periodo_activo'] = periodo_activo
        
        if periodo_activo:
            context['trimestres'] = Trimestre.objects.filter(periodo=periodo_activo)
        
        print(context)
        if hasattr(self.request.user, 'profesor'):
            context['materias'] = self.request.user.profesor.materias.all()
        else:
            context['materias'] = Materia.objects.all()
        return context

class CalificacionesAPIView(APIView):
    def get(self, request):
        periodo_id = request.query_params.get('periodo')
        materia_id = request.query_params.get('materia')
        trimestre_id = request.query_params.get('trimestre')
        parcial_id = request.query_params.get('parcial')  # Número del parcial (1 o 2)
        
        # Validar que `parcial_numero` sea un número
        try:
            parcial_numero = int(parcial_id)
        except (ValueError, TypeError):
            return Response({"error": "El parcial debe ser un número válido."}, status=status.HTTP_400_BAD_REQUEST)

        # Obtener el objeto `Parcial`
        parcial = Parcial.objects.filter(
            trimestre_id=trimestre_id,
            numero=parcial_numero
        ).first()

        if not parcial:
            return Response({"error": "Parcial no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        # Filtrar calificaciones con `select_related` para optimizar consultas
        calificaciones = Calificacion.objects.filter(
            detalle_matricula__matricula__periodo_id=periodo_id,
            detalle_matricula__materia_id=materia_id,
            parcial=parcial
        ).select_related(
            'detalle_matricula__matricula__estudiante__usuario',
            'parcial__trimestre'
        )

        if not calificaciones.exists():
            return Response({"message": "No hay calificaciones disponibles."}, status=status.HTTP_204_NO_CONTENT)

        # Serializar resultados
        data = [{
            'id': c.id,
            'nombre': f"{c.detalle_matricula.matricula.estudiante.usuario.first_name} {c.detalle_matricula.matricula.estudiante.usuario.last_name}",
            'tarea1': c.tarea1,
            'tarea2': c.tarea2,
            'tarea3': c.tarea3,
            'tarea4': c.tarea4,
            'examen': c.examen,
            'promedio_final': c.promedio_final,
            'trimestre': c.parcial.trimestre.get_trimestre_display(),
            'parcial': c.parcial.get_numero_display()
        } for c in calificaciones]

        return Response(data, status=status.HTTP_200_OK)

    def get_promedios_trimestre(self, request):
        periodo_id = request.query_params.get('periodo')
        materia_id = request.query_params.get('materia')
        trimestre_id = request.query_params.get('trimestre')

        promedios = PromedioTrimestre.objects.filter(
            detalle_matricula__matricula__periodo_id=periodo_id,
            detalle_matricula__materia_id=materia_id,
            trimestre_id=trimestre_id
        ).select_related(
            'detalle_matricula__matricula__estudiante__usuario',
            'trimestre'
        )

        if not promedios.exists():
            return Response({"message": "No hay promedios disponibles."}, status=status.HTTP_204_NO_CONTENT)

        serializer = PromedioTrimestreSerializer(promedios, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
@method_decorator(csrf_exempt, name='dispatch')
class CalificacionesBulkAPIView(APIView):
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            grades_data = request.data
            updated_grades = []
            
            for grade in grades_data:
                calificacion = Calificacion.objects.select_related(
                    'parcial__trimestre'
                ).get(id=grade['student_id'])
                
                # Convertir valores a Decimal
                calificacion.tarea1 = Decimal(str(grade['tarea1']))
                calificacion.tarea2 = Decimal(str(grade['tarea2']))
                calificacion.tarea3 = Decimal(str(grade['tarea3']))
                calificacion.tarea4 = Decimal(str(grade['tarea4']))
                calificacion.examen = Decimal(str(grade['examen']))
                
                # Guardar calificaciones
                calificacion.save()
                
                # Actualizar promedios del trimestre
                promedio_trimestre, created = PromedioTrimestre.objects.get_or_create(
                    detalle_matricula=calificacion.detalle_matricula,
                    trimestre=calificacion.parcial.trimestre
                )
                
                # La actualización del promedio se maneja en el modelo
                
                updated_grades.append({
                    'id': calificacion.id,
                    'promedio_final': float(calificacion.promedio_final)
                })
            
            return Response({
                'message': 'Calificaciones actualizadas exitosamente',
                'grades': updated_grades
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'error': 'Error en el formato de los números: ' + str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class ExamenTrimestralAPIView(APIView):
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            examenes_data = request.data
            updated_promedios = []
            
            for examen in examenes_data:
                promedio = PromedioTrimestre.objects.get(id=examen['promedio_id'])
                promedio.examen_trimestral = Decimal(str(examen['examen_trimestral']))
                promedio.save()
                
                # Actualizar promedio anual
                promedio_anual, created = PromedioAnual.objects.get_or_create(
                    detalle_matricula=promedio.detalle_matricula
                )
                
                # Actualizar el promedio del trimestre correspondiente
                trimestre_num = promedio.trimestre.trimestre
                if trimestre_num == '1':
                    promedio_anual.promedio_t1 = promedio.promedio_final
                elif trimestre_num == '2':
                    promedio_anual.promedio_t2 = promedio.promedio_final
                elif trimestre_num == '3':
                    promedio_anual.promedio_t3 = promedio.promedio_final
                
                promedio_anual.save()
                
                updated_promedios.append({
                    'id': promedio.id,
                    'promedio_final': float(promedio.promedio_final)
                })
            
            return Response({
                'message': 'Exámenes trimestrales actualizados exitosamente',
                'promedios': updated_promedios
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'error': 'Error en el formato de los números: ' + str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class CalificacionesExcelAPIView(APIView):
    @transaction.atomic
    def post(self, request):
        try:
            file = request.FILES.get('file')
            trimestre_id = request.data.get('trimestre')
            parcial_id = request.data.get('parcial')
            
            if not all([file, trimestre_id, parcial_id]):
                return Response({
                    'error': 'Faltan parámetros requeridos'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Aquí iría la lógica para procesar el archivo Excel
            # Usando pandas o openpyxl
            # Asegurarse de validar que el trimestre y parcial coincidan
            
            return Response({
                'message': 'Calificaciones importadas exitosamente'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)