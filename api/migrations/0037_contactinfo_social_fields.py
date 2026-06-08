from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0036_banner_title_optional'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactinfo',
            name='instagram',
            field=models.URLField(blank=True, null=True, verbose_name='Instagram'),
        ),
        migrations.AddField(
            model_name='contactinfo',
            name='telegram',
            field=models.URLField(blank=True, null=True, verbose_name='Telegram'),
        ),
        migrations.AddField(
            model_name='contactinfo',
            name='whatsapp',
            field=models.URLField(blank=True, null=True, verbose_name='WhatsApp'),
        ),
        migrations.AddField(
            model_name='contactinfo',
            name='facebook',
            field=models.URLField(blank=True, null=True, verbose_name='Facebook'),
        ),
    ]
