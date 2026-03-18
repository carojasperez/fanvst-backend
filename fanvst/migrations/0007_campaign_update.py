from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fanvst', '0006_campaign_reward'),
    ]

    operations = [
        migrations.CreateModel(
            name='CampaignUpdate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('title', models.CharField(max_length=200)),
                ('body', models.TextField()),
                ('campaign', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='updates',
                    to='fanvst.campaign',
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
