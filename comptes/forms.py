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
        fields = ['titre', 'description']

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
        fields = ['image', 'superficie', 'description', 'nbr_chambre', 'piece_speciale', 'prix']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'superficie': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'nbr_chambre': forms.NumberInput(attrs={'class': 'form-control'}),
            'piece_speciale': forms.TextInput(attrs={'class': 'form-control'}),
            'prix': forms.NumberInput(attrs={'class': 'form-control'})
        }

class AppartementForm(forms.ModelForm):
    prix = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Appartement
        fields = ['image', 'superficie', 'etage', 'prix']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'superficie': forms.NumberInput(attrs={'class': 'form-control'}),
            'etage': forms.NumberInput(attrs={'class': 'form-control'})
        }

class TerrainForm(forms.ModelForm):
    prix = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Terrain
        fields = ['image', 'superficie', 'nbr_parcelles', 'prix']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'superficie': forms.NumberInput(attrs={'class': 'form-control'}),
            'nbr_parcelles': forms.NumberInput(attrs={'class': 'form-control'})
        }