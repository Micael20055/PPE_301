from django.db import migrations, models
import django.db.models.deletion


def remove_annonce_tables(apps, schema_editor):
    """Supprime les tables liées au modèle Annonce."""
    # Suppression des tables dans l'ordre inverse des dépendances
    # D'abord les commentaires qui dépendent de Annonce
    Commentaire = apps.get_model('comptes', 'Commentaire')
    Commentaire.objects.all().delete()
    
    # Puis les annonces elles-mêmes
    Annonce = apps.get_model('comptes', 'Annonce')
    Annonce.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('comptes', '0012_remove_annonce'),
    ]

    operations = [
        # Suppression des contraintes de clé étrangère
        migrations.RemoveField(
            model_name='commentaire',
            name='annonce',
        ),
        
        # Suppression des tables
        migrations.RunPython(
            code=remove_annonce_tables,
            reverse_code=migrations.RunPython.noop,
        ),
        
        # Suppression du modèle Commentaire car il dépend de Annonce
        migrations.DeleteModel(
            name='Commentaire',
        ),
        
        # Suppression du modèle Annonce
        migrations.DeleteModel(
            name='Annonce',
        ),
    ]
