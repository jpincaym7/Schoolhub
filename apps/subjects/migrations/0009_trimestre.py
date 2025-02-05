# Generated by Django 5.1 on 2025-01-29 03:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0008_alter_periodoacademico_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Trimestre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('trimestre', models.CharField(choices=[('1', 'Primer Trimestre'), ('2', 'Segundo Trimestre'), ('3', 'Tercer Trimestre')], max_length=1)),
                ('periodo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trimestres', to='subjects.periodoacademico')),
            ],
            options={
                'unique_together': {('periodo', 'trimestre')},
            },
        ),
    ]
