from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fanvst', '0005_fanprofile_show_real_name_to_artists'),
    ]

    operations = [
        # Índice en Campaign.status — acelera .filter(status='active') que se ejecuta constantemente
        migrations.AlterField(
            model_name='campaign',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft', 'Borrador'),
                    ('active', 'Activa'),
                    ('completed', 'Completada'),
                    ('cancelled', 'Cancelada'),
                ],
                db_index=True,
                default='draft',
                max_length=20,
            ),
        ),
        # Campo para idempotencia en pagos PayPal de contribuciones a campañas
        migrations.AddField(
            model_name='campaigncontribution',
            name='paypal_order_id',
            field=models.CharField(blank=True, db_index=True, default='', max_length=100),
        ),
    ]
