from django.db import migrations, models
from django.db.models import Q

def update_proprietaire(apps, schema_editor):
    BienImmobilier = apps.get_model('comptes', 'BienImmobilier')
    # Récupérer tous les biens sans propriétaire
    biens_sans_proprietaire = BienImmobilier.objects.filter(proprietaire=None)
    
    # Pour chaque bien sans propriétaire, trouver le premier propriétaire disponible
    for bien in biens_sans_proprietaire:
        try:
            # On peut utiliser un propriétaire par défaut ou une logique spécifique
            # Ici, on va simplement mettre le premier propriétaire trouvé
            proprietaire = models.Utilisateur.objects.filter(profession='proprietaire').first()
            if proprietaire:
                bien.proprietaire = proprietaire
                bien.save()
        except models.Utilisateur.DoesNotExist:
            pass

class Migration(migrations.Migration):

    dependencies = [
        ('comptes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(update_proprietaire),
    ]
