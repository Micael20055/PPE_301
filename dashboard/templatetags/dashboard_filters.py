from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Filtre personnalisé pour accéder à une valeur de dictionnaire par clé dans un template.
    
    Args:
        dictionary (dict): Le dictionnaire source
        key (str): La clé à rechercher dans le dictionnaire
        
    Returns:
        La valeur correspondante à la clé ou 0 si la clé n'existe pas
        
    Exemple d'utilisation:
        {{ my_dict|get_item:'ma_cle' }}
    """
    if not isinstance(dictionary, dict):
        return 0
    return dictionary.get(key, 0)
