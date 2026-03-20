from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fanvst', '0004_fanprofile_public_alias'),
    ]

    operations = [
        migrations.AddField(
            model_name='fanprofile',
            name='show_real_name_to_artists',
            field=models.BooleanField(default=False),
        ),
    ]

