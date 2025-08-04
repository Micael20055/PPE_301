from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import BienImmobilier, Publication, Commentaire, Notification

User = get_user_model()

class UtilisateurModelTest(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            username='client_test',
            email='client@test.com',
            password='testpass123',
            profession='client'
        )
        self.proprietaire_user = User.objects.create_user(
            username='proprietaire_test',
            email='proprietaire@test.com',
            password='testpass123',
            profession='proprietaire'
        )

    def test_utilisateur_creation(self):
        """Test de création d'utilisateurs"""
        self.assertEqual(self.client_user.profession, 'client')
        self.assertEqual(self.proprietaire_user.profession, 'proprietaire')

    def test_utilisateur_str(self):
        """Test de la méthode __str__"""
        self.assertIn('client_test', str(self.client_user))

class BienImmobilierModelTest(TestCase):
    def setUp(self):
        self.proprietaire = User.objects.create_user(
            username='proprietaire',
            email='proprietaire@test.com',
            password='testpass123',
            profession='proprietaire'
        )
        self.bien = BienImmobilier.objects.create(
            type_bien='Maison',
            superficie=120.5,
            description='Belle maison',
            prix=250000.00,
            proprietaire=self.proprietaire
        )

    def test_bien_creation(self):
        """Test de création d'un bien immobilier"""
        self.assertEqual(self.bien.type_bien, 'Maison')
        self.assertEqual(self.bien.superficie, 120.5)
        self.assertEqual(self.bien.prix, 250000.00)

    def test_bien_str(self):
        """Test de la méthode __str__"""
        self.assertIn('Maison', str(self.bien))

class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            profession='client'
        )

    def test_home_view_authenticated(self):
        """Test de la vue home pour un utilisateur connecté"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('comptes:home'))
        self.assertEqual(response.status_code, 302)  # Redirection attendue

    def test_home_view_unauthenticated(self):
        """Test de la vue home pour un utilisateur non connecté"""
        response = self.client.get(reverse('comptes:home'))
        self.assertEqual(response.status_code, 200)

    def test_login_view(self):
        """Test de la vue de connexion"""
        response = self.client.get(reverse('comptes:login'))
        self.assertEqual(response.status_code, 200)

class CommentaireModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            profession='client'
        )
        self.proprietaire = User.objects.create_user(
            username='proprietaire',
            email='proprietaire@test.com',
            password='testpass123',
            profession='proprietaire'
        )
        self.bien = BienImmobilier.objects.create(
            type_bien='Maison',
            superficie=120.5,
            description='Belle maison',
            prix=250000.00,
            proprietaire=self.proprietaire
        )
        self.commentaire = Commentaire.objects.create(
            bien=self.bien,
            auteur=self.user,
            contenu='Très beau bien !'
        )

    def test_commentaire_creation(self):
        """Test de création d'un commentaire"""
        self.assertEqual(self.commentaire.contenu, 'Très beau bien !')
        self.assertEqual(self.commentaire.auteur, self.user)
        self.assertFalse(self.commentaire.lu)

    def test_commentaire_est_une_reponse(self):
        """Test de la propriété est_une_reponse"""
        self.assertFalse(self.commentaire.est_une_reponse)
        
        # Créer une réponse
        reponse = Commentaire.objects.create(
            bien=self.bien,
            auteur=self.proprietaire,
            parent=self.commentaire,
            contenu='Merci pour votre commentaire !'
        )
        self.assertTrue(reponse.est_une_reponse)

class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            profession='client'
        )
        self.notification = Notification.objects.create(
            utilisateur=self.user,
            titre='Test notification',
            message='Ceci est un test',
            type_notification='message'
        )

    def test_notification_creation(self):
        """Test de création d'une notification"""
        self.assertEqual(self.notification.titre, 'Test notification')
        self.assertFalse(self.notification.lu)

    def test_notification_marquer_comme_lu(self):
        """Test de marquage comme lu"""
        self.assertFalse(self.notification.lu)
        self.notification.marquer_comme_lu()
        self.assertTrue(self.notification.lu)
