import os
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_file_size(value):
    """Valide la taille du fichier (max 10MB)"""
    filesize = value.size
    
    if filesize > 10 * 1024 * 1024:  # 10MB
        raise ValidationError(_("La taille du fichier ne peut pas dépasser 10MB."))
    
    return value

def validate_file_type(value):
    """Valide le type de fichier (images uniquement)"""
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    
    if hasattr(value, 'content_type') and value.content_type not in allowed_types:
        raise ValidationError(_("Format de fichier non supporté. Utilisez JPG, PNG ou WEBP."))
    
    return value

def validate_positive_number(value):
    """Valide qu'un nombre est positif"""
    if value <= 0:
        raise ValidationError(_("La valeur doit être supérieure à 0."))
    return value

def validate_superficie(value):
    """Valide la superficie (doit être positive et raisonnable)"""
    if value <= 0:
        raise ValidationError(_("La superficie doit être supérieure à 0."))
    if value > 10000:  # 10,000 m² max
        raise ValidationError(_("La superficie semble trop élevée. Vérifiez votre saisie."))
    return value

def validate_prix(value):
    """Valide le prix (doit être positif et raisonnable)"""
    if value <= 0:
        raise ValidationError(_("Le prix doit être supérieur à 0."))
    if value > 10000000:  # 10M€ max
        raise ValidationError(_("Le prix semble trop élevé. Vérifiez votre saisie."))
    return value

def get_file_extension(filename):
    """Retourne l'extension du fichier"""
    return os.path.splitext(filename)[1].lower()

def is_valid_image_extension(filename):
    """Vérifie si l'extension du fichier est une image valide"""
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    return get_file_extension(filename) in valid_extensions

def format_file_size(size_bytes):
    """Formate la taille du fichier en format lisible"""
    if size_bytes == 0:
        return "0 Bytes"
    
    size_names = ["Bytes", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def clean_phone_number(phone):
    """Nettoie et valide un numéro de téléphone"""
    if not phone:
        return phone
    
    # Supprimer tous les caractères non numériques sauf + et -
    cleaned = ''.join(c for c in phone if c.isdigit() or c in '+-')
    
    # Validation basique
    if len(cleaned) < 10:
        raise ValidationError(_("Le numéro de téléphone doit contenir au moins 10 chiffres."))
    
    return cleaned

def validate_description_length(value):
    """Valide la longueur de la description"""
    if len(value.strip()) < 10:
        raise ValidationError(_("La description doit contenir au moins 10 caractères."))
    if len(value) > 2000:
        raise ValidationError(_("La description ne peut pas dépasser 2000 caractères."))
    return value 