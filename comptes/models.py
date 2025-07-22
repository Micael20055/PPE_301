from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import os

def upload_to_bien(instance, filename):
    """Génère un chemin de fichier pour les images des biens"""
    return os.path.join('biens', str(instance.bien.id), filename)

class Agence(models.Model):
    nom_agence = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=15)
    adresse = models.TextField()
    siret = models.CharField(max_length=14)
    logo = models.ImageField(upload_to='agences/logos/', null=True, blank=True)
    description = models.TextField(blank=True)
    statut = models.CharField(max_length=50, default='Active')

    def __str__(self):
        return self.nom_agence

class Utilisateur(AbstractUser):
    PROFESSION_CHOICES = [
        ('client', 'Client'),
        ('agent', 'Agent Immobilier'),
        ('proprietaire', 'Propriétaire'),
    ]
    profession = models.CharField(max_length=20, choices=PROFESSION_CHOICES, null=True, blank=True)
    agence = models.OneToOneField(Agence, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.profession})"

# ==================== BIENS IMMOBILIERS ====================

class BienImmobilier(models.Model):
    TYPE_CHOICES = [
        ('Maison', 'Maison'),
        ('Appartement', 'Appartement'),
        ('Terrain', 'Terrain'),
    ]
    type_bien = models.CharField(max_length=20, choices=TYPE_CHOICES)
    superficie = models.FloatField()
    description = models.TextField(blank=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2)  # Ajout du champ prix
    proprietaire = models.ForeignKey(
        Utilisateur, 
        on_delete=models.CASCADE,
        limit_choices_to={'profession': 'proprietaire'},
        help_text="Chaque bien doit avoir un propriétaire.",
        null=True,
        blank=True
    )
    image = models.ImageField(upload_to='biens/', null=True, blank=True)

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
    """Modèle pour les commentaires sur les biens immobiliers"""
    bien = models.ForeignKey(BienImmobilier, on_delete=models.CASCADE, related_name='commentaires')
    auteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='commentaires')
    contenu = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-date_creation']
        verbose_name = 'Commentaire'
        verbose_name_plural = 'Commentaires'
    
    def __str__(self):
        return f"Commentaire de {self.auteur} sur {self.bien} ({self.date_creation.strftime('%d/%m/%Y %H:%M')})"


# class Facture(models.Model):
#     paiement = models.ForeignKey(Paiement, on_delete=models.CASCADE)
#     montant = models.FloatField()
#     date_paiement = models.DateField()
#     fichier = models.FileField(upload_to='factures/')
# 
#     def __str__(self):
#         return f"Facture {self.id} - {self.montant}€"frc pour {self.paiement}"