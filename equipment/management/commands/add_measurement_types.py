from django.core.management.base import BaseCommand
from equipment.models import MeasurementType

MEASUREMENT_TYPES = [
    'измерения геометрических величин',
    'измерения механических величин',
    'измерения параметров потока, расхода, уровня и объема веществ',
    'измерения давления и вакуумные',
    'измерения физико-химического состава и свойств веществ',
    'теплофизические и температурные измерения',
    'измерения времени и частоты',
    'измерения электрических и магнитных величин',
    'радиотехнические и радиоэлектронные измерения',
    'измерения акустических величин',
    'оптико-физические измерения',
    'измерения характеристик ионизирующих излучений и ядерных констант',
    'метеорологические измерения',
    'специальные измерения (в соответствии со специализацией)',
]

class Command(BaseCommand):
    help = 'Добавляет стандартные типы измерений в MeasurementType.'

    def handle(self, *args, **options):
        created = 0
        for name in MEASUREMENT_TYPES:
            obj, was_created = MeasurementType.objects.get_or_create(name=name)
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Добавлено {created} новых типов измерений.')) 