from django.db import migrations, models


def seed_public_alias(apps, schema_editor):
    FanProfile = apps.get_model('fanvst', 'FanProfile')
    for profile in FanProfile.objects.select_related('user').all():
        if profile.public_alias:
            continue
        profile.public_alias = f'Fan {profile.user_id}'[:50]
        profile.save(update_fields=['public_alias'])


class Migration(migrations.Migration):

    dependencies = [
        ('fanvst', '0003_directtip_paypal_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='fanprofile',
            name='public_alias',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.RunPython(seed_public_alias, migrations.RunPython.noop),
    ]
