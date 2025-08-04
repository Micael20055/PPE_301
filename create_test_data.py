import os
import django

def create_test_data():
    # Configuration de l'environnement Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PPE_301.settings')
    django.setup()

    from django.contrib.auth import get_user_model
    from comptes.models import BienImmobilier, Commentaire, Utilisateur, Maison, Appartement, Terrain
    from django.utils import timezone

    # Création d'un utilisateur de test
    User = get_user_model()
    
    # Vérifier si l'utilisateur existe déjà
    if not User.objects.filter(email='test@example.com').exists():
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            profession='proprietaire'
        )
        print(f"Utilisateur créé: {user.email}")
    else:
        user = User.objects.get(email='test@example.com')
        print(f"Utilisateur existant récupéré: {user.email}")

    # Type de bien (utilise les choix définis dans le modèle BienImmobilier)
    type_bien = 'Appartement'

    # Création d'un bien immobilier de base
    bien, created = BienImmobilier.objects.get_or_create(
        type_bien=type_bien,
        defaults={
            'superficie': 75.5,
            'description': 'Un bel appartement pour les tests',
            'prix': 350000,
            'proprietaire': user,
        }
    )
    if created:
        print(f"Bien immobilier créé: {bien}")
        
        # Création d'un appartement associé
        appartement = Appartement.objects.create(
            bien=bien,
            etage=2,
            nbr_chambre=3
        )
        print(f"Appartement créé: {appartement}")
    else:
        print(f"Bien immobilier existant récupéré: {bien}")
        
        # Vérifier si l'appartement existe déjà
        if not hasattr(bien, 'appartement'):
            appartement = Appartement.objects.create(
                bien=bien,
                etage=2,
                nbr_chambre=3
            )
            print(f"Appartement créé pour le bien existant: {appartement}")

    # Création d'un commentaire de test
    comment, created = Commentaire.objects.get_or_create(
        bien=bien,
        auteur=user,
        defaults={
            'contenu': 'Ceci est un commentaire de test',
            'date_creation': timezone.now(),
            'date_modification': timezone.now(),
            'lu': False
        }
    )
    
    if created:
        print(f"Commentaire créé: {comment.id}")
    else:
        print(f"Commentaire existant récupéré: {comment.id}")

    print("\nDonnées de test créées avec succès!")
    print(f"- Utilisateur: {user.email} (ID: {user.id})")
    print(f"- Bien immobilier: {bien.type_bien} de {bien.superficie}m² (ID: {bien.id})")
    print(f"- Commentaire: {comment.id}")

if __name__ == "__main__":
    create_test_data()
