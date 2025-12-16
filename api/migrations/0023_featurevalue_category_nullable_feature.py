from django.db import migrations, models


def populate_featurevalue_category(apps, schema_editor):
    FeatureValue = apps.get_model('api', 'FeatureValue')
    for fv in FeatureValue.objects.all():
        if getattr(fv, 'feature_id', None):
            feature = getattr(fv, 'feature', None)
            if feature and getattr(feature, 'category_id', None):
                fv.category_id = feature.category_id
                fv.save(update_fields=['category'])


class Migration(migrations.Migration):
    dependencies = [
        ('api', '0022_alter_productfeature_unique_together_featurevalue_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='featurevalue',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='feature_values', to='api.category', verbose_name='Категория'),
        ),
        migrations.AlterField(
            model_name='featurevalue',
            name='feature',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='values', to='api.feature', verbose_name='Характеристика'),
        ),
        migrations.RunPython(populate_featurevalue_category, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name='featurevalue',
            unique_together={('category', 'value')},
        ),
    ]
