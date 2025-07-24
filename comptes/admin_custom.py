from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Utilisateur

class CustomUserAdmin(UserAdmin):
    # Configuration pour la liste des utilisateurs
    list_display = ('username', 'email', 'first_name', 'last_name', 'profession', 'is_staff')
    list_filter = ('profession', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    
    # Configuration pour le formulaire de modification
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Profil'), {'fields': ('profession',)}),
    )
    
    # Configuration pour le formulaire d'ajout
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'profession'),
        }),
    )

# Enregistrement du modèle Utilisateur avec la configuration personnalisée
admin.site.register(Utilisateur, CustomUserAdmin)
