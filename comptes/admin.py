from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    Utilisateur, BienImmobilier, Maison, Appartement, Terrain,
    Transaction, Publication, Visite, Document, Paiement, Commentaire
)

# Configuration personnalisée pour l'admin Utilisateur
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'profession', 'is_staff')
    list_filter = ('profession', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Profil'), {'fields': ('profession',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'profession'),
        }),
    )
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    
    # Spécification du template personnalisé
    change_list_template = 'admin/comptes/utilisateur/change_list.html'

# Enregistrement des modèles
admin.site.register(Utilisateur, CustomUserAdmin)

@admin.register(BienImmobilier)
class BienImmobilierAdmin(admin.ModelAdmin):
    list_display = ('id', 'type_bien', 'superficie', 'prix', 'proprietaire')
    list_filter = ('type_bien',)
    search_fields = ('description', 'proprietaire__username')

@admin.register(Maison)
class MaisonAdmin(admin.ModelAdmin):
    list_display = ('bien', 'nbr_chambre', 'piece_speciale')
    search_fields = ('bien__description',)

@admin.register(Appartement)
class AppartementAdmin(admin.ModelAdmin):
    list_display = ('bien', 'etage', 'nbr_chambre')
    search_fields = ('bien__description',)

@admin.register(Terrain)
class TerrainAdmin(admin.ModelAdmin):
    list_display = ('bien', 'nbr_parcelles')
    search_fields = ('bien__description',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('bien', 'acheteur', 'type_transaction', 'montant', 'date_transaction')
    list_filter = ('type_transaction',)
    search_fields = ('bien__description', 'acheteur__username')

@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('titre', 'bien', 'prix', 'date_creation')
    search_fields = ('titre', 'description')
    list_filter = ('date_creation',)

@admin.register(Visite)
class VisiteAdmin(admin.ModelAdmin):
    list_display = ('bien', 'client', 'proprietaire', 'date_visite', 'statut')
    list_filter = ('statut', 'date_visite')
    search_fields = ('bien__description', 'client__username', 'proprietaire__username')

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('bien', 'montant', 'date', 'statut')
    list_filter = ('statut', 'date')
    search_fields = ('bien__description', 'description')

@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    list_display = ('bien', 'auteur', 'date_creation', 'lu')
    list_filter = ('lu', 'date_creation')
    search_fields = ('contenu', 'auteur__username', 'bien__description')

# Modèle Document optionnel
admin.site.register(Document)
