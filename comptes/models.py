from django.db import models
from django.contrib.auth.models import AbstractUser

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
    proprietaire = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, null=True, blank=True, limit_choices_to={'profession': 'proprietaire'})
    image = models.ImageField(upload_to='biens/', null=True, blank=True)

    def __str__(self):
        return f"{self.type_bien} - {self.superficie}m²"

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
        null=True,  # Permet temporairement null
        blank=True  # Permet temporairement blank
    )
    titre = models.CharField(max_length=200)
    description = models.TextField()
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titre}"

# ==================== ANNONCES ET COMMENTAIRES ====================

class Annonce(models.Model):
    titre = models.CharField(max_length=255)
    intitule = models.TextField()
    date_publication = models.DateField(auto_now_add=True)
    auteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    bien = models.ForeignKey(BienImmobilier, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='annonces/', null=True, blank=True)

    def __str__(self):
        return self.titre

class Commentaire(models.Model):
    contenu = models.TextField()
    date_commentaire = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    annonce = models.ForeignKey(Annonce, on_delete=models.CASCADE)

    def __str__(self):
        return f"Commentaire par {self.utilisateur} sur {self.annonce}"

# ==================== DOCUMENTS ET PAIEMENTS ====================

class Document(models.Model):
    type_doc = models.CharField(max_length=100)

    def __str__(self):
        return self.type_doc

class Paiement(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    bien = models.ForeignKey(BienImmobilier, on_delete=models.CASCADE)
    date_paiement = models.DateField()
    montant = models.FloatField()
    document = models.OneToOneField(Document, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.montant}€ par {self.utilisateur} pour {self.bien}"

class Facture(models.Model):
    paiement = models.ForeignKey(Paiement, on_delete=models.CASCADE)
    montant = models.FloatField()
    date_paiement = models.DateField()

    def __str__(self):
        return f"Facture de {self.montant}frc pour {self.paiement}"