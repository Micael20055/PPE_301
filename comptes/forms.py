from django import forms
from django.forms import ModelForm, TextInput, NumberInput, Select, Textarea
from django.core.validators import EmailValidator
from django.utils import timezone

class RechercheForm(forms.Form):
    """Formulaire de recherche de biens immobiliers"""
    type_bien = forms.ChoiceField(
        choices=[
            ('', 'Tous les types'),
            ('Maison', 'Maison'),
            ('Appartement', 'Appartement'),
            ('Terrain', 'Terrain'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
        })
    )
    prix_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
            'placeholder': 'Prix min',
            'min': '0',
            'step': '1000'
        })
    )
    prix_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
            'placeholder': 'Prix max',
            'min': '0',
            'step': '1000'
        })
    )
    localisation = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
            'placeholder': 'Localisation (ville, quartier...)'
        })
    )


class InscriptionNewsletterForm(forms.Form):
    """Formulaire d'inscription à la newsletter"""
    email = forms.EmailField(
        label='Votre adresse email',
        validators=[EmailValidator(message="Veuillez entrer une adresse email valide.")],
        widget=forms.EmailInput(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
            'placeholder': 'votre@email.com',
            'required': 'required'
        })
    )
    consentement = forms.BooleanField(
        label='J\'accepte de recevoir des offres par email',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Ici, vous pourriez ajouter une logique pour vérifier si l'email est déjà inscrit
        return email.lower()

    def clean(self):
        cleaned_data = super().clean()
        prix_min = cleaned_data.get('prix_min')
        prix_max = cleaned_data.get('prix_max')

        if prix_min and prix_max and prix_min > prix_max:
            raise forms.ValidationError("Le prix minimum ne peut pas être supérieur au prix maximum.")

        return cleaned_data


class ContactForm(forms.Form):
    nom = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
        'placeholder': 'Votre nom'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
        'placeholder': 'Votre email'
    }))
    sujet = forms.CharField(max_length=200, widget=forms.TextInput(attrs={
        'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
        'placeholder': 'Sujet'
    }))
    message = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
        'placeholder': 'Votre message',
        'rows': 5
    }))
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur, Publication, Transaction, Paiement, Maison, Appartement, Terrain, Commentaire, Visite

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = Utilisateur
        fields = ['username', 'email', 'password1', 'password2', 'profession']

class VisiteForm(forms.ModelForm):
    """Formulaire pour la programmation d'une visite"""
    date_visite = forms.DateTimeField(
        label="Date et heure de la visite",
        widget=forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
            },
            format='%Y-%m-%dT%H:%M'
        ),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    
    remarques = forms.CharField(
        label="Remarques (facultatif)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
            'rows': 3,
            'placeholder': 'Précisez vos disponibilités ou demandes particulières...'
        })
    )
    
    class Meta:
        model = Visite
        fields = ['date_visite', 'remarques']
        
    def clean_date_visite(self):
        date_visite = self.cleaned_data.get('date_visite')
        if date_visite and date_visite < timezone.now():
            raise forms.ValidationError("La date de visite ne peut pas être dans le passé.")
        return date_visite

class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ['description']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
                'rows': 4
            })
        }

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['bien', 'acheteur', 'type_transaction', 'montant', 'date_transaction']
        widgets = {
            'bien': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
            }),
            'acheteur': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
            }),
            'type_transaction': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
            }),
            'montant': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
            }),
            'date_transaction': forms.DateInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
                'type': 'date'
            })
        }

# Formulaire Annonce supprimé
# Formulaire Commentaire supprimé car il dépendait de Annonce

class PaiementForm(forms.ModelForm):
    class Meta:
        model = Paiement
        fields = ['bien', 'montant', 'description', 'statut']
        widgets = {
            'bien': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
            }),
            'montant': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
            }),
            'description': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
                'rows': 3
            }),
            'statut': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
            })
        }

class MaisonForm(forms.ModelForm):
    class Meta:
        model = Maison
        fields = ['nbr_chambre', 'piece_speciale', 'nbr_etages']
        widgets = {
            'nbr_chambre': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
            }),
            'piece_speciale': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
            }),
            'nbr_etages': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
            })
        }

class AppartementForm(forms.ModelForm):
    class Meta:
        model = Appartement
        fields = ['etage', 'nbr_chambre']
        widgets = {
            'etage': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
            }),
            'nbr_chambre': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
            })
        }

class TerrainForm(forms.ModelForm):
    class Meta:
        model = Terrain
        fields = ['nbr_parcelles']
        widgets = {
            'nbr_parcelles': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
            })
        }

class CommentaireForm(forms.ModelForm):
    class Meta:
        model = Commentaire
        fields = ['contenu']
        widgets = {
            'contenu': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
                'rows': 4,
                'placeholder': 'Écrivez votre commentaire ici...'
            })
        }

class ProfilForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ['username', 'first_name', 'last_name', 'email', 'profession']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
            }),
            'profession': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
            })
        }