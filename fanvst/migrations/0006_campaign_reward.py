from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fanvst', '0005_artist_social_links'),
    ]

    operations = [
        migrations.CreateModel(
            name='CampaignReward',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('min_amount', models.DecimalField(decimal_places=2, max_digits=8)),
                ('sort_order', models.PositiveSmallIntegerField(default=0)),
                ('campaign', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='rewards',
                    to='fanvst.campaign',
                )),
            ],
            options={
                'ordering': ['min_amount', 'sort_order'],
            },
        ),
    ]
