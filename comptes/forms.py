from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur, Publication, Transaction, Annonce, Commentaire, Paiement

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = Utilisateur
        fields = ['username', 'email', 'password1', 'password2', 'profession']

class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ['titre', 'type_bien', 'description', 'prix', 'adresse', 'image', 'auteur']

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