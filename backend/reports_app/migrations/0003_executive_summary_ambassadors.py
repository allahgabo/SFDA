from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('reports_app', '0002_userprofile'),
    ]
    operations = [
        migrations.AddField(
            model_name='report',
            name='executive_summary',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='report',
            name='key_ambassadors',
            field=models.JSONField(default=list),
        ),
    ]
