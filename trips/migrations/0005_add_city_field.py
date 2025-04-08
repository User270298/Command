from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('trips', '0004_alter_businesstrip_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='businesstrip',
            name='city',
            field=models.CharField(default='', max_length=100, verbose_name='Город'),
        ),
    ] 