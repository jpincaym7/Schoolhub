# Generated by Django 5.1 on 2025-01-29 03:18

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0006_alter_asignacionprofesor_unique_together_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='periodoacademico',
            options={'ordering': ['-fecha_inicio'], 'verbose_name': 'Período Académico', 'verbose_name_plural': 'Períodos Académicos'},
        ),
        migrations.AlterField(
            model_name='periodoacademico',
            name='activo',
            field=models.BooleanField(default=True, verbose_name='Período Activo'),
        ),
        migrations.AlterField(
            model_name='periodoacademico',
            name='fecha_fin',
            field=models.DateField(verbose_name='Fecha de Fin'),
        ),
        migrations.AlterField(
            model_name='periodoacademico',
            name='fecha_inicio',
            field=models.DateField(verbose_name='Fecha de Inicio'),
        ),
        migrations.AlterField(
            model_name='periodoacademico',
            name='nombre',
            field=models.CharField(max_length=100, verbose_name='Nombre del Período'),
        ),
        migrations.CreateModel(
            name='Trimestre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(3)], verbose_name='Número de Trimestre')),
                ('fecha_inicio', models.DateField(verbose_name='Fecha de Inicio')),
                ('fecha_fin', models.DateField(verbose_name='Fecha de Fin')),
                ('periodo_academico', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trimestres', to='subjects.periodoacademico', verbose_name='Período Académico')),
            ],
            options={
                'verbose_name': 'Trimestre',
                'verbose_name_plural': 'Trimestres',
                'ordering': ['numero'],
                'unique_together': {('periodo_academico', 'numero')},
            },
        ),
    ]
