# Generated by Django 5.1 on 2025-01-22 17:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0002_promedioanual_calificacion'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='promedioanual',
            name='promedio_p3',
        ),
        migrations.AlterField(
            model_name='calificacion',
            name='parcial',
            field=models.IntegerField(choices=[(1, 'Primer Parcial'), (2, 'Segundo Parcial')], default=1),
        ),
    ]
