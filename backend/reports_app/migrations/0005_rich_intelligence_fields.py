from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('reports_app', '0004_participants_suggested_meetings')]
    operations = [
        migrations.AddField(model_name='report', name='conference_summary',    field=models.TextField(blank=True, default='')),
        migrations.AddField(model_name='report', name='conference_history',    field=models.TextField(blank=True, default='')),
        migrations.AddField(model_name='report', name='ksa_participation_history', field=models.TextField(blank=True, default='')),
        migrations.AddField(model_name='report', name='sfda_relevance',        field=models.TextField(blank=True, default='')),
        migrations.AddField(model_name='report', name='bilateral_relations',   field=models.TextField(blank=True, default='')),
        migrations.AddField(model_name='report', name='geopolitical_summary',  field=models.TextField(blank=True, default='')),
        migrations.AddField(model_name='report', name='entry_requirements',    field=models.TextField(blank=True, default='')),
        migrations.AddField(model_name='report', name='leadership_brief',      field=models.TextField(blank=True, default='')),
        migrations.AddField(model_name='report', name='trade_exchange',        field=models.TextField(blank=True, default='')),
        migrations.AddField(model_name='report', name='sfda_talking_points',   field=models.JSONField(default=list)),
        migrations.AddField(model_name='report', name='embassy',               field=models.JSONField(default=dict)),
    ]
