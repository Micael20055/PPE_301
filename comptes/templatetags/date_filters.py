from django import template
from django.utils import timezone
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def french_date(value):
    """
    Affiche une date en français de manière simple
    """
    if not value:
        return ""
    
    # Format simple : "25 juillet 2024 à 14:30"
    mois = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin',
            'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
    
    return f"{value.day} {mois[value.month - 1]} {value.year} à {value.strftime('%H:%M')}"

@register.filter
def relative_date(value):
    """
    Affiche une date relative en français
    """
    if not value:
        return ""
    
    now = timezone.now()
    diff = now - value
    
    # Si c'est aujourd'hui
    if value.date() == now.date():
        if diff.seconds < 60:
            return "À l'instant"
        elif diff.seconds < 3600:
            minutes = diff.seconds // 60
            return f"Il y a {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            hours = diff.seconds // 3600
            return f"Il y a {hours} heure{'s' if hours > 1 else ''}"
    
    # Si c'est hier
    elif value.date() == (now.date() - timedelta(days=1)):
        return f"Hier à {value.strftime('%H:%M')}"
    
    # Sinon, afficher la date complète
    else:
        return french_date(value) 