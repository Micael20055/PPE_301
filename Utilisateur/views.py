from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from comptes.models import BienImmobilier, Publication, Transaction, Commentaire
from comptes.forms import ContactForm, RechercheForm, InscriptionNewsletterForm
from django.utils import timezone

def index(request):
    """Page d'accueil du site"""
    # Récupérer les 6 derniers biens ajoutés
    derniers_biens = Publication.objects.all().order_by('-date_creation')[:6]
    
    context = {
        'biens_vedette': derniers_biens,
        'form_recherche': RechercheForm(),
        'form_newsletter': InscriptionNewsletterForm(),
    }
    return render(request, 'utilisateur/index.html', context)

def biens(request):
    """Page de liste des biens immobiliers"""
    # Tous les biens sont visibles par défaut
    biens_liste = Publication.objects.all()
    
    # Filtres par type de bien
    type_bien = request.GET.get('type')
    if type_bien and type_bien in dict(BienImmobilier.TYPE_CHOICES):
        biens_liste = biens_liste.filter(bien__type_bien=type_bien)
    
    # Tri
    tri = request.GET.get('tri', 'date_desc')
    if tri == 'prix_asc':
        biens_liste = biens_liste.order_by('bien__prix')
    elif tri == 'prix_desc':
        biens_liste = biens_liste.order_by('-bien__prix')
    elif tri == 'date_asc':
        biens_liste = biens_liste.order_by('date_creation')
    else:  # date_desc par défaut
        biens_liste = biens_liste.order_by('-date_creation')
    
    context = {
        'biens': biens_liste,
        'types_biens': BienImmobilier.TYPE_CHOICES,
        'tri_actuel': tri,
        'form_recherche': RechercheForm(request.GET or None),
    }
    return render(request, 'utilisateur/biens.html', context)

def detail_bien(request, bien_id):
    """Page de détail d'un bien immobilier avec commentaires"""
    bien = get_object_or_404(BienImmobilier, pk=bien_id)
    
    # Vérifier si l'utilisateur est connecté
    if request.user.is_authenticated:
        # Vérifier si l'utilisateur a déjà mis ce bien en favori
        est_favori = request.user.favoris.filter(pk=bien_id).exists()
    else:
        est_favori = False
    
    # Gestion du formulaire de commentaire
    commentaire_envoye = False
    if request.method == 'POST' and 'commentaire' in request.POST:
        if not request.user.is_authenticated:
            messages.warning(request, 'Veuillez vous connecter pour laisser un commentaire.')
            return redirect('login') + f'?next={request.path}'
            
        contenu = request.POST.get('contenu', '').strip()
        if contenu:
            Commentaire.objects.create(
                bien=bien,
                auteur=request.user,
                contenu=contenu
            )
            commentaire_envoye = True
            messages.success(request, 'Votre commentaire a été envoyé avec succès !')
            return redirect('utilisateur:detail_bien', bien_id=bien_id)
        else:
            messages.error(request, 'Le commentaire ne peut pas être vide.')
    
    # Récupérer les commentaires existants
    commentaires = bien.commentaires.all().select_related('auteur')
    
    # Formulaire de contact
    form_contact = ContactForm()
    if request.method == 'POST' and 'contact' in request.POST:
        form_contact = ContactForm(request.POST)
        if form_contact.is_valid():
            # Traitement du formulaire (à implémenter)
            messages.success(request, 'Votre message a été envoyé avec succès !')
            return redirect('utilisateur:detail_bien', bien_id=bien_id)
    
    # Biens similaires (même type de bien, exclure le bien actuel)
    biens_similaires = BienImmobilier.objects.filter(
        type_bien=bien.type_bien
    ).exclude(pk=bien_id).select_related('publication')[:4]
    
    # Préparer les détails spécifiques au type de bien
    details_bien = {}
    if hasattr(bien, 'maison'):
        details_bien = {
            'type': 'maison',
            'chambres': bien.maison.nbr_chambre,
            'salles_bain': getattr(bien.maison, 'nbr_salle_bain', 'Non spécifié'),
            'etages': getattr(bien.maison, 'nbr_etages', 'Non spécifié'),
            'jardin': 'Oui' if getattr(bien.maison, 'jardin', False) else 'Non',
            'garage': getattr(bien.maison, 'nbr_garage', 0),
            'annee_construction': getattr(bien.maison, 'annee_construction', 'Non spécifiée'),
        }
    elif hasattr(bien, 'appartement'):
        details_bien = {
            'type': 'appartement',
            'chambres': bien.appartement.nbr_chambre,
            'salles_bain': getattr(bien.appartement, 'nbr_salle_bain', 'Non spécifié'),
            'etage': getattr(bien.appartement, 'etage', 'Rez-de-chaussée'),
            'ascenseur': 'Oui' if getattr(bien.appartement, 'ascenseur', False) else 'Non',
            'balcon': 'Oui' if getattr(bien.appartement, 'balcon', False) else 'Non',
            'parking': 'Oui' if getattr(bien.appartement, 'place_parking', 0) > 0 else 'Non',
        }
    elif hasattr(bien, 'terrain'):
        details_bien = {
            'type': 'terrain',
            'surface_constructible': getattr(bien.terrain, 'surface_constructible', 'Non spécifiée'),
            'viabilise': 'Oui' if getattr(bien.terrain, 'viabilise', False) else 'Non',
            'pente': getattr(bien.terrain, 'pente', 'Non spécifiée'),
            'acces': getattr(bien.terrain, 'acces', 'Non spécifié'),
        }
    
    context = {
        'bien': bien,
        'est_favori': est_favori,
        'biens_similaires': biens_similaires,
        'form_contact': form_contact,
        'commentaires': commentaires,
        'details_bien': details_bien,
        'commentaire_envoye': commentaire_envoye,
    }
    return render(request, 'utilisateur/detail_bien.html', context)

def contact(request):
    """Page de contact"""
    form = ContactForm()
    
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Envoyer l'email (à implémenter)
            messages.success(request, 'Votre message a bien été envoyé !')
            return redirect('utilisateur:contact')
    
    context = {
        'form': form,
    }
    return render(request, 'utilisateur/contact.html', context)

def a_propos(request):
    """Page À propos"""
    return render(request, 'utilisateur/a_propos.html')

def mentions_legales(request):
    """Page des mentions légales"""
    return render(request, 'utilisateur/mentions_legales.html')

def conditions_generales(request):
    """Page des conditions générales d'utilisation"""
    return render(request, 'utilisateur/conditions_generales.html')

# Vues de compatibilité pour les anciennes URLs
def home(request):
    return redirect('utilisateur:index')

def properties(request):
    return redirect('utilisateur:biens')

def property_details(request, bien_id):
    return redirect('utilisateur:detail_bien', bien_id=bien_id)

# Autres vues secondaires (à implémenter si nécessaire)
def blog(request):
    return render(request, 'utilisateur/blog.html')

def recherche_avancee(request):
    """Page de recherche avancée"""
    form = RechercheForm(request.GET or None)
    resultats = []
    
    if form.is_valid():
        # Implémenter la logique de recherche
        pass
    
    context = {
        'form': form,
        'resultats': resultats,
    }
    return render(request, 'utilisateur/recherche_avancee.html', context)