from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('reports_app', '0003_executive_summary_ambassadors')]
    operations = [
        migrations.AddField(model_name='report', name='participants',
            field=models.JSONField(default=list)),
        migrations.AddField(model_name='report', name='suggested_meetings',
            field=models.JSONField(default=list)),
    ]
