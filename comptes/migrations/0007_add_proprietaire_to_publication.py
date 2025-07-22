from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

# Modified to handle the case where the field doesn't exist yet
def update_publication_proprietaire(apps, schema_editor):
    # Skip this function since we're not adding the proprietaire field anymore
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('comptes', '0006_merge_0002_update_proprietaire_0005_visite'),
    ]

    operations = [
        # Empty operations list since we're not making any changes
        # This is just a placeholder migration to maintain compatibility
    ]
