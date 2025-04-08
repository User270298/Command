from django.db import migrations

def add_measurement_types(apps, schema_editor):
    MeasurementType = apps.get_model('equipment', 'MeasurementType')
    
    measurement_types = [
        'Измерения геометрических величин',
        'Измерения механических величин',
        'Измерения параметров потока, расхода, уровня и объема веществ',
        'Измерения давления и вакуумные',
        'Измерения физико-химического состава и свойств веществ',
        'Теплофизические и температурные измерения',
        'Измерения времени и частоты',
        'Измерения электрических и магнитных величин',
        'Радиотехнические и радиоэлектронные измерения',
        'Измерения акустических величин',
        'Оптико-физические измерения',
        'Измерения характеристик ионизирующих излучений и ядерных констант',
        'Метеорологические измерения',
        'Специальные измерения'
    ]
    
    for type_name in measurement_types:
        MeasurementType.objects.get_or_create(name=type_name)

def remove_measurement_types(apps, schema_editor):
    MeasurementType = apps.get_model('equipment', 'MeasurementType')
    MeasurementType.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('equipment', '0003_initial'),
    ]

    operations = [
        migrations.RunPython(add_measurement_types, remove_measurement_types),
    ] 