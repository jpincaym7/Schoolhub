from decimal import Decimal
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from apps.subjects.models.academic import PeriodoAcademico
from apps.subjects.models.activity import Calificacion, PromedioAnual
from apps.subjects.models.subject import Materia
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

class CalManageView(TemplateView):
    template_name = 'teacher/calificaciones/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['periodos'] = PeriodoAcademico.objects.all()
        if hasattr(self.request.user, 'profesor'):
            context['materias'] = self.request.user.profesor.materias.all()
        else:
            context['materias'] = Materia.objects.all()
        return context

class CalificacionesAPIView(APIView):
    def get(self, request):
        periodo = request.query_params.get('periodo')
        materia = request.query_params.get('materia')
        parcial = request.query_params.get('parcial')
        
        calificaciones = Calificacion.objects.filter(
            detalle_matricula__matricula__periodo_id=periodo,
            detalle_matricula__materia_id=materia,
            parcial=parcial
        ).select_related(
            'detalle_matricula__matricula__estudiante__usuario'
        )
        
        return Response([{
            'id': c.id,
            'nombre': f"{c.detalle_matricula.matricula.estudiante.usuario.first_name} {c.detalle_matricula.matricula.estudiante.usuario.last_name}",
            'tarea1': c.tarea1,
            'tarea2': c.tarea2,
            'tarea3': c.tarea3,
            'tarea4': c.tarea4,
            'examen': c.examen,
            'promedio_final': c.promedio_final
        } for c in calificaciones])

@method_decorator(csrf_exempt, name='dispatch')
class CalificacionesBulkAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            grades_data = request.data
            updated_grades = []
            
            for grade in grades_data:
                calificacion = Calificacion.objects.get(id=grade['student_id'])
                
                # Convertir todos los valores a Decimal
                calificacion.tarea1 = Decimal(str(grade['tarea1']))
                calificacion.tarea2 = Decimal(str(grade['tarea2']))
                calificacion.tarea3 = Decimal(str(grade['tarea3']))
                calificacion.tarea4 = Decimal(str(grade['tarea4']))
                calificacion.examen = Decimal(str(grade['examen']))
                
                # Guardar las calificaciones
                calificacion.save()
                
                # Obtener o crear el PromedioAnual correspondiente
                promedio_anual, created = PromedioAnual.objects.get_or_create(
                    detalle_matricula=calificacion.detalle_matricula
                )
                
                # Actualizar el promedio para el parcial
                if calificacion.parcial == 1:
                    promedio_anual.promedio_p1 = calificacion.promedio_final
                elif calificacion.parcial == 2:
                    promedio_anual.promedio_p2 = calificacion.promedio_final
                
                # Guardar el PromedioAnual actualizado
                promedio_anual.save()
                
                updated_grades.append({
                    'id': calificacion.id,
                    'promedio_final': float(calificacion.promedio_final)  # Convertir a float para JSON
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
            
class CalificacionesExcelAPIView(APIView):
    def post(self, request):
        try:
            file = request.FILES.get('file')
            if not file:
                return Response({
                    'error': 'No se proporcionó ningún archivo'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Aquí iría la lógica para procesar el archivo Excel
            # Puedes usar pandas o openpyxl para esto
            
            return Response({
                'message': 'Archivo procesado exitosamente'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)