from django.db import migrations, models


def add_description_to_annonce(apps, schema_editor):
    # Cette fonction va ajouter une chaîne vide comme valeur par défaut pour les annonces existantes
    Annonce = apps.get_model('comptes', 'Annonce')
    for annonce in Annonce.objects.all():
        if not hasattr(annonce, 'description') or annonce.description is None:
            annonce.description = ""
            annonce.save()


class Migration(migrations.Migration):

    dependencies = [
        ('comptes', '0009_fix_migration_conflict'),  # La dernière migration appliquée
    ]

    operations = [
        migrations.AddField(
            model_name='annonce',
            name='description',
            field=models.TextField(default='', blank=True),
            preserve_default=True,
        ),
        migrations.RunPython(add_description_to_annonce, reverse_code=migrations.RunPython.noop),
    ]
