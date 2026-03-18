from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fanvst', '0007_campaign_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='artistprofile',
            name='handle',
            field=models.SlugField(
                blank=True,
                help_text='Identificador único tipo @handle (ej: monlaferte)',
                max_length=60,
                null=True,
                unique=True,
            ),
        ),
    ]
