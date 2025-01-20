# Generated by Django 5.1 on 2025-01-20 08:01

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0001_initial'),
        ('subjects', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AcademicPeriod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(2)], verbose_name='Número de Quimestre')),
                ('school_year', models.CharField(max_length=9, verbose_name='Año Lectivo')),
            ],
            options={
                'verbose_name': 'Período Académico',
                'verbose_name_plural': 'Períodos Académicos',
                'ordering': ['school_year', 'number'],
                'unique_together': {('number', 'school_year')},
            },
        ),
        migrations.CreateModel(
            name='ActivityTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nombre')),
                ('description', models.TextField(blank=True, verbose_name='Descripción')),
                ('activity_type', models.CharField(choices=[('individual', 'Individual'), ('group', 'Grupal')], max_length=20, verbose_name='Tipo de Actividad')),
                ('partial_number', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(3)], verbose_name='Número de Parcial')),
                ('sequence_number', models.PositiveSmallIntegerField(editable=False, verbose_name='Número de Secuencia')),
                ('academic_period', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='subjects.academicperiod', verbose_name='Período Académico')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='subjects.subject', verbose_name='Materia')),
            ],
            options={
                'verbose_name': 'Plantilla de Actividad',
                'verbose_name_plural': 'Plantillas de Actividades',
                'unique_together': {('subject', 'academic_period', 'partial_number', 'activity_type', 'sequence_number')},
            },
        ),
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nombre')),
                ('description', models.TextField(blank=True, verbose_name='Descripción')),
                ('activity_type', models.CharField(choices=[('individual', 'Individual'), ('group', 'Grupal')], max_length=20, verbose_name='Tipo de Actividad')),
                ('partial_number', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(3)], verbose_name='Número de Parcial')),
                ('sequence_number', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(2)], verbose_name='Número de Secuencia')),
                ('score', models.DecimalField(decimal_places=2, default=0, max_digits=4, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)], verbose_name='Calificación')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('academic_period', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='subjects.academicperiod', verbose_name='Período Académico')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', to='students.student', verbose_name='Estudiante')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='subjects.subject', verbose_name='Materia')),
                ('template', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='activities', to='subjects.activitytemplate', verbose_name='Plantilla de Actividad')),
            ],
            options={
                'verbose_name': 'Actividad',
                'verbose_name_plural': 'Actividades',
                'ordering': ['partial_number', 'activity_type', 'sequence_number'],
                'unique_together': {('student', 'subject', 'academic_period', 'partial_number', 'activity_type', 'sequence_number')},
            },
        ),
        migrations.CreateModel(
            name='PartialGrade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('partial_number', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(3)], verbose_name='Número de Parcial')),
                ('evaluation_score', models.DecimalField(decimal_places=2, default=0, max_digits=4, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)], verbose_name='Nota Evaluación')),
                ('final_score', models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=4, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)], verbose_name='Nota Final')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('academic_period', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='subjects.academicperiod', verbose_name='Período Académico')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='partial_grades', to='students.student', verbose_name='Estudiante')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='subjects.subject', verbose_name='Materia')),
            ],
            options={
                'verbose_name': 'Calificación Parcial',
                'verbose_name_plural': 'Calificaciones Parciales',
                'ordering': ['academic_period', 'partial_number'],
                'unique_together': {('student', 'subject', 'academic_period', 'partial_number')},
            },
        ),
        migrations.CreateModel(
            name='QuimesterGrade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('final_score', models.DecimalField(decimal_places=2, default=0, max_digits=4, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)], verbose_name='Nota Final')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('academic_period', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='subjects.academicperiod', verbose_name='Período Académico')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quimester_grades', to='students.student', verbose_name='Estudiante')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='subjects.subject', verbose_name='Materia')),
            ],
            options={
                'verbose_name': 'Calificación Quimestral',
                'verbose_name_plural': 'Calificaciones Quimestrales',
                'ordering': ['academic_period'],
                'unique_together': {('student', 'subject', 'academic_period')},
            },
        ),
    ]