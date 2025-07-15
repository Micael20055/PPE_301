from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur, Publication, Transaction, Annonce, Commentaire, Paiement, Maison, Appartement, Terrain

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = Utilisateur
        fields = ['username', 'email', 'password1', 'password2', 'profession']

class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ['description']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control'})
        }

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['bien', 'acheteur', 'type_transaction', 'montant', 'date_transaction']

class AnnonceForm(forms.ModelForm):
    class Meta:
        model = Annonce
        fields = ['titre', 'intitule', 'bien', 'image', 'auteur']

class CommentaireForm(forms.ModelForm):
    class Meta:
        model = Commentaire
        fields = ['contenu', 'utilisateur', 'annonce']

class PaiementForm(forms.ModelForm):
    class Meta:
        model = Paiement
        fields = ['utilisateur', 'bien', 'date_paiement', 'montant', 'document']

class MaisonForm(forms.ModelForm):
    class Meta:
        model = Maison
        fields = ['nbr_chambre', 'piece_speciale', 'nbr_etages']
        widgets = {
            'nbr_chambre': forms.NumberInput(attrs={'class': 'form-control'}),
            'piece_speciale': forms.TextInput(attrs={'class': 'form-control'}),
            'nbr_etages': forms.NumberInput(attrs={'class': 'form-control'})
        }

class AppartementForm(forms.ModelForm):
    class Meta:
        model = Appartement
        fields = ['etage', 'nbr_chambre']
        widgets = {
            'etage': forms.NumberInput(attrs={'class': 'form-control'}),
            'nbr_chambre': forms.NumberInput(attrs={'class': 'form-control'})
        }

class TerrainForm(forms.ModelForm):
    class Meta:
        model = Terrain
        fields = ['nbr_parcelles']
        widgets = {
            'nbr_parcelles': forms.NumberInput(attrs={'class': 'form-control'})
        }