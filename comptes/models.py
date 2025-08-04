from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import os
from .utils import validate_superficie, validate_prix, validate_file_size, validate_file_type

def upload_to_bien(instance, filename):
    """Génère un chemin de fichier pour les images des biens"""
    return os.path.join('biens', str(instance.bien.id), filename)

class Utilisateur(AbstractUser):
    PROFESSION_CHOICES = [
        ('client', 'Client'),
        ('agent', 'Agent Immobilier'),
        ('proprietaire', 'Propriétaire'),
    ]
    profession = models.CharField(max_length=20, choices=PROFESSION_CHOICES, null=True, blank=True)


    def __str__(self):
        return f"{self.username} ({self.profession})"

# ==================== BIENS IMMOBILIERS ====================

class BienImmobilier(models.Model):
    TYPE_CHOICES = [
        ('Maison', 'Maison'),
        ('Appartement', 'Appartement'),
        ('Terrain', 'Terrain'),
    ]
    date_creation = models.DateTimeField(default=timezone.now, verbose_name="Date de création")
    type_bien = models.CharField(max_length=20, choices=TYPE_CHOICES)
    superficie = models.FloatField(
        validators=[validate_superficie],
        help_text="Superficie en m²"
    )
    description = models.TextField(
        blank=True,
        max_length=2000,
        help_text="Description détaillée du bien (max 2000 caractères)"
    )
    prix = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[validate_prix],
        help_text="Prix en euros"
    )
    proprietaire = models.ForeignKey(
        Utilisateur, 
        on_delete=models.CASCADE,
        limit_choices_to={'profession': 'proprietaire'},
        help_text="Chaque bien doit avoir un propriétaire.",
        null=True,
        blank=True
    )
    image = models.ImageField(
        upload_to='biens/', 
        null=True, 
        blank=True,
        validators=[validate_file_size, validate_file_type],
        help_text="Image du bien (JPG, PNG, WEBP, max 10MB)"
    )

    def __str__(self):
        return f"{self.id}: {self.type_bien} - {self.superficie}m² - {self.prix}€ - Prop: {self.proprietaire_id if self.proprietaire else 'Aucun'}"

class Maison(models.Model):
    bien = models.OneToOneField(BienImmobilier, on_delete=models.CASCADE, related_name='maison')
    nbr_chambre = models.IntegerField(null=True, blank=True)
    piece_speciale = models.CharField(max_length=255, null=True, blank=True)
    nbr_etages = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'comptes_maison'

    def __str__(self):
        return f"Maison {self.bien}"


class Appartement(models.Model):
    bien = models.OneToOneField(BienImmobilier, on_delete=models.CASCADE, related_name='appartement')
    etage = models.IntegerField(null=True, blank=True)
    nbr_chambre = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'comptes_appartement'

    def __str__(self):
        return f"Appartement {self.bien}"


class Terrain(models.Model):
    bien = models.OneToOneField(BienImmobilier, on_delete=models.CASCADE, related_name='terrain')
    nbr_parcelles = models.IntegerField()

    class Meta:
        db_table = 'comptes_terrain'

    def __str__(self):
        return f"Terrain {self.bien}"

# ==================== TRANSACTIONS ====================

class Transaction(models.Model):
    TYPE_CHOICES = [
        ('location', 'Location'),
        ('vente', 'Vente'),
    ]
    bien = models.ForeignKey(BienImmobilier, on_delete=models.CASCADE)
    acheteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, limit_choices_to={'profession': 'client'})
    type_transaction = models.CharField(max_length=20, choices=TYPE_CHOICES)
    montant = models.FloatField()
    date_transaction = models.DateField()

    def __str__(self):
        return f"{self.type_transaction.capitalize()} de {self.bien} à {self.acheteur}"

# ==================== PUBLICATION ====================

class Publication(models.Model):
    bien = models.ForeignKey(
        BienImmobilier, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    titre = models.CharField(max_length=200)
    description = models.TextField()
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    date_creation = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return f"{self.titre}"

# ==================== VISITES ====================

class Visite(models.Model):
    STATUT_CHOICES = [
        ('planifiee', 'Planifiée'),
        ('effectuee', 'Effectuée'),
        ('annulee', 'Annulée'),
        ('confirme', 'Confirmée')
    ]
    
    bien = models.ForeignKey(BienImmobilier, on_delete=models.CASCADE, related_name='visites')
    client = models.ForeignKey(
        Utilisateur, 
        on_delete=models.CASCADE,
        limit_choices_to={'profession': 'client'},
        related_name='visites_client'
    )
    proprietaire = models.ForeignKey(
        Utilisateur, 
        on_delete=models.CASCADE,
        limit_choices_to={'profession': 'proprietaire'},
        related_name='visites_proprietaire',
        null=True,
        blank=True
    )
    date_visite = models.DateTimeField()
    date_creation = models.DateTimeField(default=timezone.now)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='planifiee')
    remarques = models.TextField(blank=True)
    
    def __str__(self):
        return f"Visite de {self.client} sur {self.bien} ({self.get_statut_display()})"
    
    def save(self, *args, **kwargs):
        if not self.proprietaire_id:
            self.proprietaire = self.bien.proprietaire
        super().save(*args, **kwargs)

# ==================== DOCUMENTS ET PAIEMENTS ====================

class Document(models.Model):
    type_doc = models.CharField(max_length=100)

    def __str__(self):
        return self.type_doc

class Paiement(models.Model):
    STATUT_CHOICES = [
        ('paye', 'Payé'),
        ('en_attente', 'En attente'),
        ('annule', 'Annulé')
    ]
    
    bien = models.ForeignKey(BienImmobilier, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"Paiement de {self.montant}€ pour {self.bien} ({self.get_statut_display()})"

class Commentaire(models.Model):
    """Modèle pour les commentaires sur les biens immobiliers avec réponses"""
    bien = models.ForeignKey(BienImmobilier, on_delete=models.CASCADE, related_name='commentaires')
    auteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='commentaires')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='reponses')
    contenu = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    lu = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-date_creation']
        verbose_name = 'Commentaire'
        verbose_name_plural = 'Commentaires'
    
    def __str__(self):
        return f"Commentaire de {self.auteur} sur {self.bien} ({self.date_creation.strftime('%d/%m/%Y %H:%M')})"
    
    @property
    def est_une_reponse(self):
        """Vérifie si le commentaire est une réponse à un autre commentaire"""
        return self.parent is not None
    
    def get_reponses(self):
        """Récupère toutes les réponses à ce commentaire"""
        return self.reponses.all().order_by('date_creation')
    
    def marquer_comme_lu(self):
        """Marque le commentaire comme lu"""
        self.lu = True
        self.save(update_fields=['lu'])
    
    def notifier_reponse(self, reponse):
        """Envoie une notification au client lorsqu'une réponse est ajoutée"""
        from django.contrib import messages
        from django.urls import reverse
        from django.utils import timezone
        
        # Créer une notification pour le client
        Notification.objects.create(
            utilisateur=self.auteur,
            titre=f'Nouvelle réponse à votre commentaire',
            message=f'Le propriétaire a répondu à votre commentaire sur le bien: {self.bien.titre}',
            url=reverse('comptes:detail_bien', kwargs={'pk': self.bien.id}),
            type_notification='reponse_commentaire'
        )


# class Facture(models.Model):
#     paiement = models.ForeignKey(Paiement, on_delete=models.CASCADE)
#     montant = models.FloatField()
#     date_paiement = models.DateField()
#     fichier = models.FileField(upload_to='factures/')
# 
#     def __str__(self):
#         return f"Facture {self.id} - {self.montant}€"frc pour {self.paiement}"

class Notification(models.Model):
    """Modèle pour les notifications utilisateur"""
    TYPE_CHOICES = [
        ('reponse_commentaire', 'Réponse à un commentaire'),
        ('nouvelle_publication', 'Nouvelle publication'),
        ('visite_confirmee', 'Visite confirmée'),
        ('visite_annulee', 'Visite annulée'),
        ('message', 'Message'),
    ]
    
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='notifications')
    titre = models.CharField(max_length=200)
    message = models.TextField()
    url = models.CharField(max_length=500, blank=True, null=True)
    type_notification = models.CharField(max_length=50, choices=TYPE_CHOICES, default='message')
    lu = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_creation']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"Notification pour {self.utilisateur}: {self.titre}"
    
    def marquer_comme_lu(self):
        """Marque la notification comme lue"""
        self.lu = True
        self.save(update_fields=['lu'])