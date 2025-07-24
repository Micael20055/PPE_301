from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse, HttpResponseServerError
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.db.models import Count, Q, Sum
import logging
from .forms import CustomUserCreationForm, ProfilForm
from .models import Utilisateur, Publication, BienImmobilier, Transaction, Maison, Appartement, Terrain, Visite, Paiement, Commentaire
from .forms import PublicationForm, TransactionForm, PaiementForm, MaisonForm, AppartementForm, TerrainForm, CommentaireForm

logger = logging.getLogger(__name__)

@csrf_protect
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('comptes:redirect_user')
    else:
        form = CustomUserCreationForm()
    return render(request, 'comptes/register.html', {'form': form})

@login_required
def redirect_user(request):
    user = request.user
    print(f"\n=== DÉBOGAGE REDIRECTION ===")
    print(f"Utilisateur: {user} (ID: {user.id}, Profession: {user.profession if hasattr(user, 'profession') else 'Non définie'})")
    
    if user.is_superuser:
        print("Redirection vers l'admin")
        return redirect('/admin/')
        
    if not hasattr(user, 'profession') or not user.profession:
        print("ERREUR: La profession de l'utilisateur n'est pas définie")
        return redirect('comptes:login')
        
    if user.profession == 'client':
        print("Redirection vers l'interface utilisateur moderne")
        return redirect('utilisateur:index')
    elif user.profession == 'agent':
        print("Redirection vers les publications de l'agent")
        return redirect('comptes:publications')
    elif user.profession == 'proprietaire':
        print("Redirection vers le tableau de bord du propriétaire")
        return redirect('comptes:proprietaire_dashboard')
    else:
        print(f"ERREUR: Profession inconnue: {user.profession}")
        return redirect('comptes:login')

@login_required
@user_passes_test(lambda u: u.profession == 'client')
def client_dashboard(request):
    return HttpResponse("Bienvenue, client !")

def home(request):
    if request.user.is_authenticated:
        print("\n=== DÉBOGAGE VUE HOME ===")
        print(f"Utilisateur connecté: {request.user} (ID: {request.user.id}, Profession: {request.user.profession if hasattr(request.user, 'profession') else 'Non définie'})")
        
        if hasattr(request.user, 'profession'):
            if request.user.profession == 'client':
                print("Redirection vers l'interface utilisateur moderne")
                return redirect('utilisateur:index')
            elif request.user.profession == 'agent':
                print("Redirection vers les publications de l'agent")
                return redirect('comptes:publications')
            elif request.user.profession == 'proprietaire':
                print("Redirection vers le tableau de bord du propriétaire")
                return redirect('comptes:proprietaire_dashboard')
        
        print("ERREUR: La profession de l'utilisateur n'est pas définie")
        return redirect('comptes:login')
    
    print("Utilisateur non connecté, affichage de la page d'accueil")
    return render(request, 'comptes/home.html')

@login_required
@user_passes_test(lambda u: u.profession == 'proprietaire')
def paiement_form(request):
    if request.method == 'POST':
        form = PaiementForm(request.POST)
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.proprietaire = request.user
            paiement.save()
            return redirect('comptes:paiements')
    else:
        form = PaiementForm()
    return render(request, 'comptes/paiement_form.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.profession == 'agent')
def dashboard_agence(request):
    # Vérifier si l'utilisateur est bien un agent et a une agence
    if not hasattr(request.user, 'agence') or not request.user.agence:
        messages.error(request, "Votre compte agent n'est pas associé à une agence.")
        return redirect('comptes:home')
    
    agence = request.user.agence
    
    # Récupérer les statistiques filtrées par agence
    total_biens = BienImmobilier.objects.filter(proprietaire__agence=agence).count()
    total_clients = Utilisateur.objects.filter(profession='client', agence=agence).count()
    
    # Pour les transactions et visites, on suppose qu'elles sont liées aux biens de l'agence
    total_transactions = Transaction.objects.filter(bien__proprietaire__agence=agence).count()
    total_visites = Visite.objects.filter(
        Q(bien__proprietaire__agence=agence) | 
        Q(proprietaire__agence=agence)
    ).distinct().count()

    # Récupérer les biens de l'agence (les 6 derniers)
    biens = BienImmobilier.objects.filter(
        proprietaire__agence=agence
    ).order_by('-id')[:6]

    return render(request, 'comptes/dashboard_agence.html', {
        'agence': agence,  # Ajout de l'agence au contexte
        'total_biens': total_biens,
        'total_clients': total_clients,
        'total_transactions': total_transactions,
        'total_visites': total_visites,
        'biens': biens
    })

@login_required
@user_passes_test(lambda u: u.profession == 'client')
def client_home(request):
    # Récupérer les biens disponibles
    biens = BienImmobilier.objects.all().order_by('-id')[:6]  # Les 6 derniers biens
    
    # Récupérer les visites programmées du client
    visites = Visite.objects.filter(client=request.user)
    
    return render(request, 'comptes/client_home.html', {
        'biens': biens,
        'visites': visites
    })

@login_required
@user_passes_test(lambda u: u.profession == 'proprietaire')
def proprietaire_dashboard(request):
    """
    Affiche le tableau de bord du propriétaire avec les statistiques de ses biens immobiliers.
    """
    # Récupérer les biens du propriétaire
    biens = BienImmobilier.objects.filter(proprietaire=request.user)
    
    # Calculer les statistiques
    total_biens = biens.count()
    
    # Récupérer les paiements via les transactions liées aux biens du propriétaire
    total_paiements = Paiement.objects.filter(
        bien__proprietaire=request.user
    ).count()
    
    # Préparer les données pour le template
    context = {
        'total_biens': total_biens,
        'total_paiements': total_paiements,
        'biens': biens.order_by('-id')[:5],  # 5 biens les plus récents (par ID décroissant)
        'visites_recentes': []
    }
    
    # Ajouter des logs de débogage
    print("\n=== DÉBOGAGE TABLEAU DE BORD PROPRIÉTAIRE ===")
    print(f"Utilisateur: {request.user} (ID: {request.user.id})")
    print(f"Nombre de biens: {biens.count()}")
    print("Contenu du contexte:", context)
    print("=== FIN DÉBOGAGE ===\n")
    
    return render(request, 'comptes/proprietaire_dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.profession == 'proprietaire')
def paiements(request):
    # Récupérer tous les paiements du propriétaire
    paiements = Paiement.objects.filter(bien__proprietaire=request.user).order_by('-date')
    return render(request, 'comptes/paiements.html', {'paiements': paiements})

@login_required
@user_passes_test(lambda u: u.profession == 'proprietaire')
def commentaires(request):
    # Récupérer tous les commentaires sur les biens du propriétaire
    commentaires = Commentaire.objects.filter(bien__proprietaire=request.user).order_by('-date_creation')
    return render(request, 'comptes/commentaires.html', {'commentaires': commentaires})

@login_required
@user_passes_test(lambda u: u.profession == 'proprietaire')
def mes_publications(request):
    """
    Affiche les biens immobiliers du propriétaire connecté.
    """
    # Log de débogage
    print("\n=== DÉBOGAGE MES PUBLICATIONS ===")
    print(f"Utilisateur connecté: {request.user} (ID: {request.user.id}, Profession: {request.user.profession})")
    
    # Récupérer les biens du propriétaire
    biens_du_proprio = BienImmobilier.objects.filter(proprietaire=request.user)
    
    # Log des biens trouvés
    print(f"Nombre de biens trouvés: {biens_du_proprio.count()}")
    for bien in biens_du_proprio:
        print(f"- Bien ID: {bien.id}, Type: {bien.type_bien}, Propriétaire ID: {bien.proprietaire_id if bien.proprietaire else 'Aucun'}")
    
    # Préparer le contexte avec les données nécessaires
    context = {
        'biens': biens_du_proprio,
        'total_biens': biens_du_proprio.count(),
        'is_agent': request.user.profession == 'agent',
        'user_id': request.user.id  # Ajout de l'ID utilisateur pour le débogage
    }
    
    print("Contexte envoyé au template:", context)
    print("=== FIN DÉBOGAGE MES PUBLICATIONS ===\n")
    
    return render(request, 'comptes/mes_publications.html', context)

@login_required
@user_passes_test(lambda u: u.profession == 'client')
def modifier_profil(request):
    if request.method == 'POST':
        form = ProfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('comptes:profil_view')
    else:
        form = ProfilForm(instance=request.user)
    
    return render(request, 'comptes/modifier_profil.html', {'form': form})

def login_view(request):
    # Si l'utilisateur est déjà connecté, on le redirige directement
    if request.user.is_authenticated:
        print("\n=== DÉBOGAGE LOGIN (déjà authentifié) ===")
        print(f"Utilisateur déjà connecté: {request.user}")
        return redirect('comptes:redirect_user')
        
    error_message = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        print("\n=== DÉBOGAGE TENTATIVE DE CONNEXION ===")
        print(f"Nom d'utilisateur: {username}")
        
        if not username or not password:
            error_message = "Veuillez remplir tous les champs."
            print("ERREUR: Champs manquants")
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                print(f"Authentification réussie pour l'utilisateur: {user} (ID: {user.id}, Profession: {user.profession if hasattr(user, 'profession') else 'Non définie'})")
                login(request, user)
                print("Utilisateur connecté avec succès, redirection vers redirect_user")
                return redirect('comptes:redirect_user')
            else:
                error_message = "Nom d'utilisateur ou mot de passe incorrect."
                print("ERREUR: Échec de l'authentification")
    
    return render(request, 'comptes/login.html', {'error_message': error_message})

@login_required
def logout_view(request):
    logout(request)
    return redirect('comptes:register')

@login_required
@user_passes_test(lambda u: u.profession == 'proprietaire')
def proprietaire_index(request):
    # Récupérer les biens du propriétaire avec leurs publications
    biens = BienImmobilier.objects.filter(proprietaire=request.user)
    
    # Calculer les statistiques
    total_biens = biens.count()
    total_prix = sum(bien.prix for bien in biens)
    total_superficie = sum(bien.superficie for bien in biens)
    
    context = {
        'biens': biens,
        'total_biens': total_biens,
        'total_prix': total_prix,
        'total_superficie': total_superficie
    }
    
    return render(request, 'comptes/proprietaire_dashboard.html', context)

@login_required
def dashboard_home(request):
    # Récupérer les statistiques
    total_biens = BienImmobilier.objects.filter(proprietaire=request.user).count()
    total_transactions = Transaction.objects.filter(bien__proprietaire=request.user).count()
    total_commentaires = Commentaire.objects.filter(annonce__bien__proprietaire=request.user).count()
    total_visites = 0
    
    # Récupérer les activités récentes
    recent_activities = [
        {
            'type': 'Nouvelle Publication',
            'description': 'Vous avez créé une nouvelle publication',
            'date': timezone.now()
        },
        {
            'type': 'Transaction',
            'description': 'Une offre a été faite sur votre bien',
            'date': timezone.now() - timedelta(days=1)
        },
        {
            'type': 'Visite',
            'description': 'Un client a visité votre bien',
            'date': timezone.now() - timedelta(days=2)
        }
    ]
    
    context = {
        'total_biens': total_biens,
        'total_transactions': total_transactions,
        'total_commentaires': total_commentaires,
        'total_visites': total_visites,
        'recent_activities': recent_activities
    }
    
    return render(request, 'comptes/dashboard_home.html', context)

# Vue pour le profil
@login_required
def profil_view(request):
    user = request.user
    biens = None
    
    if user.profession == 'proprietaire':
        # Pour les propriétaires, afficher leurs biens
        biens = BienImmobilier.objects.filter(proprietaire=user)
    elif user.profession == 'agent':
        # Pour les agents, afficher les biens des propriétaires de leur agence
        if hasattr(user, 'agence') and user.agence:
            # Récupérer les propriétaires de l'agence
            proprietaires = Utilisateur.objects.filter(
                agence=user.agence,
                profession='proprietaire'
            )
            # Récupérer les biens de ces propriétaires
            biens = BienImmobilier.objects.filter(proprietaire__in=proprietaires)
    
    context = {
        'user': user,
        'biens': biens or [],  # S'assurer que biens n'est jamais None
        'is_agent': hasattr(user, 'profession') and user.profession == 'agent'
    }
    return render(request, 'comptes/profil.html', context)

# Vue About
def about(request):
    return render(request, 'comptes/about.html')

# Vue Blog
def blog(request):
    return render(request, 'comptes/blog.html')

# Vue Contact
@login_required
def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre message a été envoyé avec succès !')
            return redirect('comptes:contact')
    else:
        form = ContactForm()
    
    return render(request, 'comptes/contact.html', {'form': form})

# Vue de recherche
def search(request):
    # Récupération des paramètres avec valeurs par défaut
    type_bien = request.GET.get('type_bien', '').strip()
    prix_min = request.GET.get('prix_min', '').strip()
    prix_max = request.GET.get('prix_max', '').strip()
    
    # Journalisation des paramètres reçus
    print("\n" + "="*50)
    print("=== DÉBUT DE LA RECHERCHE ===")
    print(f"URL complète: {request.get_full_path()}")
    print(f"Paramètres GET: {request.GET}")
    print(f"Type de bien: '{type_bien}'")
    print(f"Prix min: '{prix_min}'")
    print(f"Prix max: '{prix_max}'")
    
    # Construction de la requête de base
    biens = BienImmobilier.objects.all()
    print(f"\nRequête initiale: {biens.query}")
    
    # Application des filtres
    if type_bien:
        # Conversion en minuscules pour une comparaison insensible à la casse
        type_bien_lower = type_bien.lower()
        print(f"\nAvant filtrage par type - Nombre de biens: {biens.count()}")
        print(f"Recherche de type de bien (insensible à la casse): '{type_bien_lower}'")
        
        # Méthode alternative avec une requête brute pour le débogage
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, type_bien, prix FROM comptes_bienimmobilier WHERE LOWER(type_bien) = %s", [type_bien_lower])
            resultats = cursor.fetchall()
            print(f"Résultats bruts de la requête SQL: {resultats}")
        
        biens = biens.filter(type_bien__iexact=type_bien_lower)
        print(f"Après filtrage par type - Nombre de biens: {biens.count()}")
    
    if prix_min:
        try:
            prix_min_int = int(prix_min)
            print(f"\nAvant filtrage par prix min - Nombre de biens: {biens.count()}")
            biens = biens.filter(prix__gte=prix_min_int)
            print(f"Après filtrage par prix min ({prix_min_int}€) - Nombre de biens: {biens.count()}")
        except (ValueError, TypeError) as e:
            print(f"Erreur avec le prix min '{prix_min}': {str(e)}")
    
    if prix_max:
        try:
            prix_max_int = int(prix_max)
            print(f"\nAvant filtrage par prix max - Nombre de biens: {biens.count()}")
            biens = biens.filter(prix__lte=prix_max_int)
            print(f"Après filtrage par prix max ({prix_max_int}€) - Nombre de biens: {biens.count()}")
        except (ValueError, TypeError) as e:
            print(f"Erreur avec le prix max '{prix_max}': {str(e)}")
    
    # Comptage des résultats
    nombre_resultats = biens.count()
    print("\n" + "="*50)
    print(f"=== RÉSULTATS DE LA RECHERCHE ===")
    print(f"Nombre total de résultats: {nombre_resultats}")
    print("Premiers résultats:")
    for bien in biens[:5]:  # Afficher les 5 premiers résultats pour le débogage
        print(f"- ID: {bien.id}, Type: '{bien.type_bien}', Prix: {bien.prix}€")
    
    # Préparation du contexte
    context = {
        'biens': biens,
        'type_bien': type_bien,
        'prix_min': prix_min if prix_min else '',
        'prix_max': prix_max if prix_max else '',
        'nombre_resultats': nombre_resultats
    }
    print("\nContexte envoyé au template:", context)
    print("="*50 + "\n")
    
    return render(request, 'comptes/search_results.html', context)

def get_default_image_url():
    """Retourne l'URL d'une image par défaut"""
    return '/static/images/default-property.jpg'

# Vue de détail du bien
def detail_bien(request, pk):
    # Log pour vérifier l'ID du bien demandé
    print(f"\n=== DEBUT VUE DETAIL_BIEN ===")
    print(f"ID du bien demandé: {pk}")
    
    # Récupérer le bien
    bien = get_object_or_404(BienImmobilier, pk=pk)
    
    # Log pour vérifier les détails du bien récupéré
    print(f"Bien récupéré - ID: {bien.id}, Type: {bien.type_bien}, Description: {bien.description}")
    print(f"Propriétaire: {bien.proprietaire} (ID: {bien.proprietaire_id if bien.proprietaire else 'Aucun'})")
    
    # Vérifier si le bien a une image, sinon utiliser une image par défaut
    image_url = get_default_image_url()
    if hasattr(bien, 'image') and bien.image:
        try:
            if bien.image.url:
                image_url = bien.image.url
                print(f"Image trouvée: {image_url}")
        except ValueError:
            # Si l'image n'existe pas sur le système de fichiers
            print("Avertissement: L'image référencée n'existe pas sur le système de fichiers")
    else:
        print("Aucune image associée à ce bien")
    
    # Déterminer le type de bien et récupérer les détails spécifiques
    details = None
    if hasattr(bien, 'maison'):
        details = bien.maison
        print(f"Détails spécifiques: Maison - {details}")
    elif hasattr(bien, 'appartement'):
        details = bien.appartement
        print(f"Détails spécifiques: Appartement - {details}")
    elif hasattr(bien, 'terrain'):
        details = bien.terrain
        print(f"Détails spécifiques: Terrain - {details}")
    else:
        print("Aucun détail spécifique trouvé pour ce type de bien")
    
    # Préparer le contexte
    context = {
        'bien': bien,
        'image_url': image_url,
        'details': details,
        'has_image': hasattr(bien, 'image') and bool(bien.image)
    }
    
    print(f"=== FIN VUE DETAIL_BIEN ===\n")
    
    return render(request, 'comptes/detail_bien.html', context)

# Vues pour les types de biens
def listings(request):
    # Récupération des paramètres de filtre
    type_bien = request.GET.get('type_bien', '').strip()
    prix_min = request.GET.get('prix_min', '').strip()
    prix_max = request.GET.get('prix_max', '').strip()
    
    # Journalisation des paramètres
    print("\n=== PARAMÈTRES DE FILTRAGE (listings) ===")
    print(f"Type de bien: '{type_bien}'")
    print(f"Prix min: '{prix_min}'")
    print(f"Prix max: '{prix_max}'")
    
    # Construction de la requête de base
    biens = BienImmobilier.objects.all()
    
    # Application des filtres
    if type_bien:
        type_bien_lower = type_bien.lower()
        biens = biens.filter(type_bien__iexact=type_bien_lower)
        print(f"Filtre type_bien appliqué: {type_bien_lower}")
    
    if prix_min:
        try:
            prix_min_int = int(prix_min)
            biens = biens.filter(prix__gte=prix_min_int)
            print(f"Filtre prix_min appliqué: {prix_min_int}€")
        except (ValueError, TypeError) as e:
            print(f"Erreur avec le prix min '{prix_min}': {str(e)}")
    
    if prix_max:
        try:
            prix_max_int = int(prix_max)
            biens = biens.filter(prix__lte=prix_max_int)
            print(f"Filtre prix_max appliqué: {prix_max_int}€")
        except (ValueError, TypeError) as e:
            print(f"Erreur avec le prix max '{prix_max}': {str(e)}")
    
    # Comptage des résultats
    nombre_resultats = biens.count()
    print(f"Nombre de résultats trouvés: {nombre_resultats}")
    
    context = {
        'biens': biens,
        'type_bien': type_bien,
        'prix_min': prix_min if prix_min else '',
        'prix_max': prix_max if prix_max else '',
        'nombre_resultats': nombre_resultats,
        'titre': 'Tous les biens'
    }
    
    return render(request, 'comptes/listings.html', context)

def condos(request):
    biens = BienImmobilier.objects.filter(type_bien='Appartement')
    context = {
        'biens': biens,
        'titre': 'Condos'
    }
    return render(request, 'comptes/listings.html', context)

def houses(request):
    biens = BienImmobilier.objects.filter(type_bien='Maison')
    context = {
        'biens': biens,
        'titre': 'Maisons'
    }
    return render(request, 'comptes/listings.html', context)

def lands(request):
    biens = BienImmobilier.objects.filter(type_bien='Terrain')
    context = {
        'biens': biens,
        'titre': 'Terrains'
    }
    return render(request, 'comptes/listings.html', context)

@login_required
@user_passes_test(lambda u: u.profession == 'client')
def mes_favoris(request):
    """Vue pour afficher les biens favoris de l'utilisateur"""
    # Récupérer les favoris de l'utilisateur connecté
    # Note: Implémentez cette logique selon votre modèle de données
    favoris = []  # Remplacer par la logique de récupération des favoris
    
    context = {
        'favoris': favoris,
        'title': 'Mes favoris'
    }
    return render(request, 'comptes/mes_favoris.html', context)

@login_required
@user_passes_test(lambda u: u.profession == 'client')
def profil_view(request):
    return render(request, 'comptes/profil.html')

@login_required
@user_passes_test(lambda u: u.profession == 'proprietaire')
def proprietaire_dashboard(request):
    """
    Affiche le tableau de bord du propriétaire avec les statistiques de ses biens immobiliers.
    """
    # Récupérer les biens du propriétaire
    biens = BienImmobilier.objects.filter(proprietaire=request.user)
    
    # Calculer les statistiques
    total_biens = biens.count()
    
    # Récupérer les paiements via les transactions liées aux biens du propriétaire
    total_paiements = Paiement.objects.filter(
        bien__proprietaire=request.user
    ).count()
    
    # Préparer les données pour le template
    context = {
        'total_biens': total_biens,
        'total_paiements': total_paiements,
        'biens': biens.order_by('-id')[:5],  # 5 biens les plus récents (par ID décroissant)
        'visites_recentes': []
    }
    
    # Ajouter des logs de débogage
    print("\n=== DÉBOGAGE TABLEAU DE BORD PROPRIÉTAIRE ===")
    print(f"Utilisateur: {request.user} (ID: {request.user.id})")
    print(f"Nombre de biens: {biens.count()}")
    print("Contenu du contexte:", context)
    print("=== FIN DÉBOGAGE ===\n")
    
    return render(request, 'comptes/proprietaire_dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.profession == 'proprietaire')
def commentaires_view(request):
    # Si l'utilisateur est un propriétaire, afficher les commentaires sur ses biens
    if request.user.profession == 'proprietaire':
        commentaires = Commentaire.objects.filter(bien__proprietaire=request.user).order_by('-date_creation')
    # Si l'utilisateur est un agent, afficher les commentaires sur les biens de son agence
    elif request.user.profession == 'agent' and hasattr(request.user, 'agence'):
        commentaires = Commentaire.objects.filter(bien__publication__agence=request.user.agence).order_by('-date_creation')
    else:
        commentaires = Commentaire.objects.none()
    
    return render(request, 'comptes/commentaires.html', {'commentaires': commentaires})

import logging
logger = logging.getLogger(__name__)

@login_required
def ajouter_commentaire(request, bien_id):
    """
    Vue pour ajouter un commentaire à un bien immobilier
    """
    logger.info(f"Ajout d'un commentaire - Utilisateur connecté: {request.user.username} (ID: {request.user.id})")
    logger.info(f"Session: {dict(request.session)}")
    
    bien = get_object_or_404(BienImmobilier, id=bien_id)
    
    if request.method == 'POST':
        form = CommentaireForm(request.POST)
        if form.is_valid():
            try:
                commentaire = form.save(commit=False)
                commentaire.bien = bien
                commentaire.auteur = request.user
                logger.info(f"Création d'un commentaire - Auteur: {commentaire.auteur.username} (ID: {commentaire.auteur.id})")
                commentaire.save()
                logger.info(f"Commentaire enregistré avec l'ID: {commentaire.id}")
                messages.success(request, 'Votre commentaire a été ajouté avec succès !')
            except Exception as e:
                logger.error(f"Erreur lors de l'enregistrement du commentaire: {str(e)}")
                messages.error(request, 'Une erreur est survenue lors de l\'enregistrement de votre commentaire.')
        else:
            logger.error(f"Formulaire invalide: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans le champ {field}: {error}")
    
    # Rediriger vers la page du bien dans tous les cas
    return redirect('comptes:detail_bien', pk=bien_id)

@login_required
def transactions_view(request):
    """
    Affiche la liste des transactions de l'utilisateur connecté.
    Pour les propriétaires : affiche les transactions liées à leurs biens
    Pour les clients : affiche leurs propres transactions
    """
    user = request.user
    
    if user.profession == 'proprietaire':
        # Pour les propriétaires, afficher les transactions de leurs biens
        transactions = Transaction.objects.filter(bien__proprietaire=user).select_related('bien', 'acheteur')
    elif user.profession == 'client':
        # Pour les clients, afficher leurs propres transactions
        transactions = Transaction.objects.filter(acheteur=user).select_related('bien', 'vendeur')
    else:
        transactions = Transaction.objects.none()
    
    context = {
        'transactions': transactions,
        'total_transactions': transactions.count(),
        'transactions_en_cours': transactions.filter(statut='en_cours').count(),
        'transactions_terminees': transactions.filter(statut='terminee').count(),
    }
    
    return render(request, 'comptes/transactions.html', context)

def paiements_view(request):
    if not request.user.is_authenticated or request.user.profession != 'proprietaire':
        return redirect('comptes:login')
    
    paiements = Paiement.objects.filter(bien__proprietaire=request.user).order_by('-date')
    total_paiements = paiements.count()
    total_recettes = paiements.aggregate(Sum('montant'))['montant__sum'] or 0
    
    return render(request, 'comptes/paiements.html', {
        'paiements': paiements,
        'total_paiements': total_paiements,
        'total_recettes': total_recettes
    })

@login_required
def detail_visite(request, pk):
    """Affiche les détails d'une visite spécifique"""
    try:
        visite = get_object_or_404(Visite, pk=pk)
        
        # Vérifier que l'utilisateur a le droit de voir cette visite
        if request.user != visite.proprietaire and request.user != visite.client:
            messages.error(request, "Vous n'avez pas la permission de voir cette visite.")
            return redirect('comptes:visites')
        
        context = {
            'visite': visite,
            'user': request.user,
            'is_proprietaire': request.user == visite.proprietaire,
            'is_client': request.user == visite.client,
        }
        return render(request, 'comptes/detail_visite.html', context)
    
    except Exception as e:
        messages.error(request, f"Une erreur est survenue : {str(e)}")
        return redirect('comptes:visites')

@login_required
def confirmer_visite(request, pk):
    """Confirme une visite planifiée"""
    try:
        visite = get_object_or_404(Visite, pk=pk)
        
        # Vérifier que l'utilisateur est bien le propriétaire
        if request.user != visite.proprietaire:
            messages.error(request, "Vous n'avez pas la permission de confirmer cette visite.")
            return redirect('comptes:visites')
        
        # Vérifier que la visite est bien en attente
        if visite.statut != 'planifiee':
            messages.warning(request, "Cette visite ne peut pas être confirmée car elle n'est pas en attente.")
            return redirect('comptes:visites')
        
        # Mettre à jour le statut
        visite.statut = 'confirme'
        visite.save()
        
        messages.success(request, "La visite a été confirmée avec succès.")
        return redirect('comptes:visites')
    
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de la confirmation de la visite : {str(e)}")
        return redirect('comptes:visites')

@login_required
def annuler_visite(request, pk):
    """Annule une visite planifiée"""
    try:
        visite = get_object_or_404(Visite, pk=pk)
        
        # Vérifier que l'utilisateur a le droit d'annuler cette visite
        if request.user not in [visite.proprietaire, visite.client]:
            messages.error(request, "Vous n'avez pas la permission d'annuler cette visite.")
            return redirect('comptes:visites')
        
        # Vérifier que la visite est bien en attente ou confirmée
        if visite.statut not in ['planifiee', 'confirme']:
            messages.warning(request, "Cette visite ne peut pas être annulée car elle n'est pas en attente ou confirmée.")
            return redirect('comptes:visites')
        
        # Mettre à jour le statut
        visite.statut = 'annulee'
        visite.save()
        
        messages.success(request, "La visite a été annulée avec succès.")
        return redirect('comptes:visites')
    
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de l'annulation de la visite : {str(e)}")
        return redirect('comptes:visites')

@login_required
def programmer_visite(request, pk):
    """Affiche le formulaire de programmation d'une visite pour un bien spécifique"""
    try:
        # Récupérer le bien ou renvoyer une 404
        bien = get_object_or_404(BienImmobilier, pk=pk)
        
        # Vérifier que l'utilisateur est un client
        if request.user.profession != 'client':
            messages.error(request, "Seuls les clients peuvent programmer des visites.")
            return redirect('comptes:detail_bien', pk=bien.id)
            
        # Vérifier que l'utilisateur n'est pas le propriétaire du bien
        if request.user == bien.proprietaire:
            messages.error(request, "Vous ne pouvez pas programmer de visite pour votre propre bien.")
            return redirect('comptes:detail_bien', pk=bien.id)
        
        if request.method == 'POST':
            form = VisiteForm(request.POST)
            if form.is_valid():
                try:
                    # Créer la visite
                    visite = form.save(commit=False)
                    visite.bien = bien
                    visite.client = request.user
                    visite.proprietaire = bien.proprietaire
                    visite.statut = 'planifiee'  # Définir le statut initial
                    visite.save()
                    
                    # Envoyer une notification au propriétaire (à implémenter)
                    # send_visite_notification(visite)
                    
                    messages.success(request, "Votre demande de visite a été enregistrée avec succès.")
                    return redirect('comptes:detail_visite', pk=visite.id)
                    
                except Exception as e:
                    messages.error(request, f"Une erreur est survenue lors de l'enregistrement de la visite : {str(e)}")
                    logger.error(f"Erreur lors de la programmation d'une visite : {str(e)}", exc_info=True)
        else:
            # Pré-remplir la date avec demain à 14h par défaut
            demain = timezone.now() + timezone.timedelta(days=1)
            date_par_defaut = demain.replace(hour=14, minute=0, second=0, microsecond=0)
            form = VisiteForm(initial={'date_visite': date_par_defaut})
        
        context = {
            'form': form,
            'bien': bien,
        }
        return render(request, 'comptes/programmer_visite.html', context)
        
    except Exception as e:
        messages.error(request, "Une erreur inattendue s'est produite.")
        logger.error(f"Erreur dans programmer_visite : {str(e)}", exc_info=True)
        return redirect('comptes:home')

import logging
logger = logging.getLogger(__name__)

@login_required
def visites_view(request):
    """
    Affiche la liste des visites pour un propriétaire ou un agent.
    Pour les propriétaires : affiche les visites de leurs biens
    Pour les agents : affiche les visites des biens de leur agence
    """
    logger.info("\n" + "="*80)
    logger.info("=== DÉBUT VUE VISITES (NOUVELLE REQUÊTE) ===")
    logger.info(f"Utilisateur: {request.user} (ID: {request.user.id}, Profession: {request.user.profession})")
    
    # Vérification des permissions
    if request.user.profession not in ['proprietaire', 'agent']:
        logger.error("Accès refusé : l'utilisateur n'est ni propriétaire ni agent")
        messages.error(request, 'Accès non autorisé. Vous devez être propriétaire ou agent.')
        return redirect('comptes:home')
    
    is_agent = request.user.profession == 'agent'
    logger.info(f"Type d'utilisateur: {'Agent' if is_agent else 'Propriétaire'}")
    
    # Vérification de l'agence pour les agents
    agence = None
    if is_agent:
        if not hasattr(request.user, 'agence') or not request.user.agence:
            logger.error("L'agent n'est pas rattaché à une agence")
            messages.error(request, 'Votre compte agent n\'est pas rattaché à une agence. Veuillez contacter l\'administrateur.')
            return redirect('comptes:dashboard_agence')
        agence = request.user.agence
        logger.info(f"Agent rattaché à l'agence: {agence.nom_agence} (ID: {agence.id})")
    else:
        logger.info(f"Utilisateur propriétaire (ID: {request.user.id})")
    
    try:
        logger.info("\n=== DÉBOGAGE VUE VISITES ===")
        
        # 1. Récupération des biens selon le type d'utilisateur
        if is_agent:
            # Pour un agent : récupérer les biens des propriétaires de l'agence
            biens_utilisateur = BienImmobilier.objects.filter(
                proprietaire__agence=agence
            ).select_related('proprietaire')
            logger.info(f"Agent {request.user} - {biens_utilisateur.count()} biens trouvés pour l'agence {agence.nom_agence}")
        else:
            # Pour un propriétaire : récupérer ses biens personnels
            biens_utilisateur = BienImmobilier.objects.filter(proprietaire=request.user)
            logger.info(f"Propriétaire {request.user} - {biens_utilisateur.count()} biens trouvés")
        
        # 2. Récupération des visites avec les relations nécessaires
        logger.info("\nRécupération des visites...")
        
        if is_agent:
            # Pour un agent : récupérer les visites des biens de l'agence
            # Utilisation d'une seule requête plus simple et plus efficace
            visites = []
            
            logger.info(f"Agent {request.user} - {visites.count()} visites trouvées pour l'agence {agence.nom_agence}")
        else:
            # Pour un propriétaire : récupérer les visites de ses biens
            visites = []
            
            logger.info(f"Propriétaire {request.user} - {visites.count()} visites trouvées")
        
        # 3. Préparation du contexte pour le template
        logger.info("\nPréparation du contexte...")
        
        # Compter les visites par statut pour les statistiques
        if is_agent:
            # Pour un agent : compter les visites de l'agence
            visites_planifiees = 0
            
            visites_confirmees = 0
            
            visites_annulees = 0
            
        else:
            # Pour un propriétaire : compter ses visites personnelles
            visites_planifiees = 0
            
            visites_confirmees = 0
            
            visites_annulees = 0
            
        # Récupérer les 5 prochaines visites
        prochaines_visites = []
        
        # Préparer le contexte
        context = {
            'visites': visites,
            'prochaines_visites': prochaines_visites,
            'statuts_visites': {
                'Planifiées': visites_planifiees,
                'Confirmées': visites_confirmees,
                'Annulées': visites_annulees
            },
            'total_visites': visites.count(),
            'is_agent': is_agent,
            'agence': agence if is_agent else None,
            'debug': settings.DEBUG,
            'debug_user_info': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'profession': request.user.profession,
                'agence': agence.nom_agence if is_agent and agence else None,
                'date_joined': request.user.date_joined,
            },
            'debug_visites_count': visites.count(),
            'debug_biens_count': biens_utilisateur.count(),
            'debug_biens': list(biens_utilisateur.values('id', 'type_bien', 'adresse', 'proprietaire_id')),
            'debug_visites_list': list(visites.values('id', 'bien_id', 'client_id', 'date_visite', 'statut')[:10]),
            'debug_visites_query': str(visites.query),
            'debug_biens_query': str(biens_utilisateur.query) if biens_utilisateur.exists() else "Aucun bien trouvé"
        }
        
        # Ajouter les statistiques de visites
        context.update({
            'visites_planifiees': visites_planifiees,
            'visites_confirmees': visites_confirmees,
            'visites_annulees': visites_annulees,
        })
        
        # Log des informations importantes
        logger.info("Contexte préparé avec succès")
        logger.info(f"- Nombre total de visites: {visites.count()}")
        logger.info(f"- Visites planifiées: {visites_planifiees}")
        logger.info(f"- Visites confirmées: {visites_confirmees}")
        logger.info(f"- Visites annulées: {visites_annulees}")
        
        if not visites.exists():
            logger.warning("Aucune visite trouvée pour cet utilisateur/agence")
            if is_agent:
                logger.info("Raisons possibles:")
                logger.info(f"1. Aucun bien n'est associé à l'agence {agence.nom_agence}")
                logger.info(f"2. Aucune visite n'est associée aux biens de l'agence {agence.nom_agence}")
            else:
                logger.info("Raisons possibles:")
                logger.info(f"1. Aucun bien n'est associé à l'utilisateur {request.user}")
                logger.info(f"2. Aucune visite n'est associée aux biens de l'utilisateur {request.user}")
        
        logger.info("\n=== FIN DÉBOGAGE VUE VISITES ===\n" + "="*50 + "\n")
        
        # Rendu du template
        return render(request, 'comptes/visites.html', context)
        
    except Exception as e:
        import traceback
        import sys
        error_traceback = traceback.format_exc()
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        # Afficher des informations détaillées sur l'erreur
        print("\n" + "!"*80)
        print("=== ERREUR DANS VUE VISITES ===")
        print(f"Type d'erreur: {type(e).__name__}")
        print(f"Message: {str(e)}")
        print(f"Fichier: {exc_traceback.tb_frame.f_code.co_filename}")
        print(f"Ligne: {exc_traceback.tb_lineno}")
        print("\nContexte de l'erreur:")
        print(f"- Utilisateur: {request.user} (ID: {request.user.id}, Profession: {request.user.profession})")
        
        # Afficher les variables locales au moment de l'erreur
        print("\nVariables locales:")
        for name, value in exc_traceback.tb_frame.f_locals.items():
            print(f"  {name} = {value}")
        
        # Afficher des informations sur les visites
        try:
            from comptes.models import Visite, BienImmobilier
            
            # Vérifier si l'utilisateur a des biens
            biens_count = BienImmobilier.objects.filter(proprietaire=request.user).count()
            print(f"\n- Nombre de biens pour ce propriétaire: {biens_count}")
            
            # Compter les visites par propriétaire
            visites_par_proprio = Visite.objects.filter(proprietaire=request.user).count()
            print(f"- Nombre de visites (par propriétaire): {visites_par_proprio}")
            
            # Compter les visites par biens du propriétaire
            biens_utilisateur = BienImmobilier.objects.filter(proprietaire=request.user)
            visites_par_biens = Visite.objects.filter(bien__in=biens_utilisateur).count()
            print(f"- Nombre de visites (par biens): {visites_par_biens}")
            
            # Afficher les 5 premières visites pour débogage
            visites = Visite.objects.filter(proprietaire=request.user).select_related('bien', 'client')[:5]
            print("\nDétail des visites:")
            for i, v in enumerate(visites, 1):
                print(f"  {i}. Visite ID: {v.id}, Bien: {v.bien_id} ({v.bien.type_bien if v.bien else 'N/A'}), "
                      f"Client: {v.client_id}, Statut: {v.statut}")
                
        except Exception as inner_e:
            print(f"\nErreur lors de la récupération des informations de débogage: {str(inner_e)}")
            print(f"Type d'erreur: {type(inner_e).__name__}")
            print(f"Message: {str(inner_e)}")
        
        print("\nTraceback complet:")
        print(error_traceback)
        print("!"*80 + "\n")
        
        # En environnement de production, ne pas afficher les détails de l'erreur à l'utilisateur
        messages.error(request, "Une erreur est survenue lors du chargement des visites. L'équipe technique a été informée.")
        
        # Pour le débogage en développement, vous pouvez décommenter la ligne ci-dessous
        # pour voir les détails de l'erreur dans l'interface d'administration
        # messages.error(request, f"Erreur: {str(e)}")
        
        return redirect('comptes:proprietaire_dashboard')

def choix_type_publication(request):
    return render(request, 'comptes/choix_type_publication.html')

def choix_bien(request):
    type_action = request.GET.get('type')  # 'vente' ou 'location'
    return render(request, 'comptes/choix_bien.html', {'type_action': type_action})

def ajouter_publication(request):
    # Récupérer les paramètres de l'URL
    type_action = request.GET.get('type') or request.POST.get('type')
    bien = request.GET.get('bien') or request.POST.get('bien')
    
    # Vérifier que nous avons les paramètres nécessaires
    if not type_action or not bien:
        return render(request, 'comptes/ajouter_publication.html', {
            'error_message': "Type d'action et type de bien sont requis"
        })
    
    # Initialiser les formulaires
    maison_form = MaisonForm()
    appartement_form = AppartementForm()
    terrain_form = TerrainForm()
    
    if not request.user.is_authenticated:
        return redirect('login')
        
    if request.method == 'POST':
        # Récupérer les données du formulaire
        superficie = request.POST.get('superficie')
        description = request.POST.get('description')
        prix = request.POST.get('prix')
        image = request.FILES.get('image')
        
        # Vérifier que tous les champs requis sont présents
        if not all([superficie, description, prix, image]):
            return render(request, 'comptes/ajouter_publication.html', {
                'type_action': type_action,
                'bien': bien,
                'error_message': "Veuillez remplir tous les champs requis",
                'maison_form': maison_form,
                'appartement_form': appartement_form,
                'terrain_form': terrain_form
            })
            
        try:
            # Convertir les valeurs numériques
            superficie = float(superficie)
            prix = float(prix)
            
            if superficie <= 0:
                raise ValueError("La superficie doit être supérieure à 0")
            if prix <= 0:
                raise ValueError("Le prix doit être supérieur à 0")
            
            # Créer le bien de base avec les champs communs
            bien_base = BienImmobilier.objects.create(
                type_bien=bien,
                superficie=superficie,
                description=description,
                prix=prix,
                proprietaire=request.user,
                image=image
            )
            
            # Créer le type de bien spécifique
            if bien == 'maison':
                maison_form = MaisonForm(request.POST)
                if maison_form.is_valid():
                    maison = maison_form.save(commit=False)
                    maison.bien = bien_base
                    maison.save()
                else:
                    bien_base.delete()
                    return render(request, 'comptes/ajouter_publication.html', {
                        'type_action': type_action,
                        'bien': bien,
                        'error_message': "Erreur dans le formulaire de la maison",
                        'maison_form': maison_form,
                        'appartement_form': appartement_form,
                        'terrain_form': terrain_form
                    })
            elif bien == 'appartement':
                appartement_form = AppartementForm(request.POST)
                if appartement_form.is_valid():
                    appartement = appartement_form.save(commit=False)
                    appartement.bien = bien_base
                    appartement.save()
                else:
                    bien_base.delete()
                    return render(request, 'comptes/ajouter_publication.html', {
                        'type_action': type_action,
                        'bien': bien,
                        'error_message': "Erreur dans le formulaire de l'appartement",
                        'maison_form': maison_form,
                        'appartement_form': appartement_form,
                        'terrain_form': terrain_form
                    })
            elif bien == 'terrain':
                terrain_form = TerrainForm(request.POST)
                if terrain_form.is_valid():
                    terrain = terrain_form.save(commit=False)
                    terrain.bien = bien_base
                    terrain.save()
                else:
                    bien_base.delete()
                    return render(request, 'comptes/ajouter_publication.html', {
                        'type_action': type_action,
                        'bien': bien,
                        'error_message': "Erreur dans le formulaire du terrain",
                        'maison_form': maison_form,
                        'appartement_form': appartement_form,
                        'terrain_form': terrain_form
                    })
                
            # Créer une publication avec le modèle Publication
            Publication.objects.create(
                bien=bien_base,
                titre=f"{type_action.capitalize()} {bien}",
                description=description,
                prix=prix,
                date_creation=timezone.now()
            )
            
            return redirect('comptes:mes_publications')
            
        except ValueError as e:
            return render(request, 'comptes/ajouter_publication.html', {
                'type_action': type_action,
                'bien': bien,
                'error_message': str(e),
                'maison_form': maison_form,
                'appartement_form': appartement_form,
                'terrain_form': terrain_form
            })
        except Exception as e:
            return render(request, 'comptes/ajouter_publication.html', {
                'type_action': type_action,
                'bien': bien,
                'error_message': f"Une erreur est survenue: {str(e)}",
                'maison_form': maison_form,
                'appartement_form': appartement_form,
                'terrain_form': terrain_form
            })
    
    # Afficher le formulaire
    return render(request, 'comptes/ajouter_publication.html', {
        'type_action': type_action,
        'bien': bien,
        'maison_form': maison_form,
        'appartement_form': appartement_form,
        'terrain_form': terrain_form
    })

@login_required
def modifier_publication(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Récupérer le bien à modifier
    bien = get_object_or_404(BienImmobilier, pk=pk)
    
    # Vérifier que l'utilisateur est le propriétaire du bien
    if bien.proprietaire != request.user:
        return HttpResponse("Vous n'avez pas l'autorisation de modifier cette publication", status=403)
    
    # Initialiser le formulaire spécifique selon le type de bien
    bien_form = None
    if bien.type_bien.lower() == 'maison':
        bien_form = MaisonForm(instance=bien.maison)
    elif bien.type_bien.lower() == 'appartement':
        bien_form = AppartementForm(instance=bien.appartement)
    elif bien.type_bien.lower() == 'terrain':
        bien_form = TerrainForm(instance=bien.terrain)
    
    if request.method == 'POST':
        # Mettre à jour les champs de base du bien
        bien.superficie = request.POST.get('superficie', bien.superficie)
        bien.description = request.POST.get('description', bien.description)
        bien.prix = request.POST.get('prix', bien.prix)
        if 'image' in request.FILES:
            bien.image = request.FILES['image']
        bien.save()
        
        # Mettre à jour les champs spécifiques au type de bien
        if bien_form:
            bien_form = bien_form.__class__(request.POST, instance=getattr(bien, bien.type_bien.lower()))
            if bien_form.is_valid():
                bien_form.save()
        
        return redirect('comptes:mes_publications')
    
    return render(request, 'comptes/modifier_publication.html', {
        'bien_form': bien_form,
        'bien': bien
    })

@login_required
def supprimer_publication(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Récupérer le bien à supprimer
    bien = get_object_or_404(BienImmobilier, pk=pk)
    
    # Vérifier que l'utilisateur est le propriétaire du bien
    if bien.proprietaire != request.user:
        return HttpResponse("Vous n'avez pas l'autorisation de supprimer cette publication", status=403)
    
    if request.method == 'POST':
        # Supprimer d'abord la publication associée si elle existe
        try:
            publication = Publication.objects.get(bien=bien)
            publication.delete()
        except Publication.DoesNotExist:
            pass  # Aucune publication associée, on continue
            
        # Puis supprimer le bien
        bien.delete()
        return redirect('comptes:mes_publications')
    
    return render(request, 'comptes/supprimer_publication.html', {
        'bien': bien
    })

@login_required
def publications_view(request):
    try:
        logger.info(f"Accès à publications_view par l'utilisateur: {request.user.username} (type: {getattr(request.user, 'profession', 'non défini')})")
        
        # Vérifier si l'utilisateur a un profil valide
        if not hasattr(request.user, 'profession') or not request.user.profession:
            logger.error("L'utilisateur n'a pas de profession définie")
            return HttpResponse("Erreur de configuration du profil utilisateur. Veuillez contacter l'administrateur.")

        # Préparer la requête de base pour les publications
        if request.user.profession == 'agent':
            # Vérifier si l'agent a une agence associée
            if not hasattr(request.user, 'agence') or not request.user.agence:
                logger.warning(f"L'agent {request.user.username} n'a pas d'agence associée - Affichage des biens sans filtre d'agence")
                # Modification: Au lieu de bloquer, on continue avec une liste vide de propriétaires
                # L'agent pourra voir les biens mais ne pourra pas en ajouter/modifier
                proprietaires = Utilisateur.objects.none()
                bien_ids = []
                
            # Récupérer les propriétaires de l'agence
            proprietaires = Utilisateur.objects.filter(
                agence=request.user.agence,
                profession='proprietaire'
            )
            
            if not proprietaires.exists():
                logger.info(f"Aucun propriétaire trouvé pour l'agence {request.user.agence.nom_agence}")
                return render(request, 'comptes/mes_publications.html', {
                    'publications': [],
                    'total_publications': 0,
                    'biens_publications': 0,
                    'total_visites': 0,
                    'total_commentaires': 0,
                    'is_agent': True,
                    'info_message': "Aucun propriétaire n'est actuellement associé à votre agence."
                })
            
            # Récupérer les publications des biens de ces propriétaires
            publications = Publication.objects.filter(
                bien__proprietaire__in=proprietaires
            ).select_related('bien', 'bien__proprietaire').order_by('-date_creation')
            
            # Récupérer les IDs des biens pour les statistiques
            bien_ids = list(BienImmobilier.objects.filter(
                proprietaire__in=proprietaires
            ).values_list('id', flat=True))
            
        else:
            # Pour les propriétaires, récupérer uniquement leurs propres publications
            publications = Publication.objects.filter(
                bien__proprietaire=request.user
            ).select_related('bien').order_by('-date_creation')
            
            # Récupérer les IDs des biens pour les statistiques
            bien_ids = list(BienImmobilier.objects.filter(
                proprietaire=request.user
            ).values_list('id', flat=True))
        
        # Si aucun bien trouvé, retourner une page vide
        if not bien_ids and not publications.exists():
            logger.info("Aucun bien ou publication trouvé pour cet utilisateur")
            return render(request, 'comptes/mes_publications.html', {
                'publications': [],
                'total_publications': 0,
                'biens_publications': 0,
                'total_visites': 0,
                'total_commentaires': 0,
                'is_agent': request.user.profession == 'agent'
            })
        
        # Récupérer les statistiques de visites
        visites_par_bien = dict(Visite.objects.filter(
            bien_id__in=bien_ids
        ).values('bien').annotate(total=Count('id')).values_list('bien', 'total'))
        
        # Récupérer les statistiques de commentaires
        try:
            commentaires_par_bien = dict(Commentaire.objects.filter(
                annonce__bien_id__in=bien_ids
            ).values('annonce__bien').annotate(total=Count('id')).values_list('annonce__bien', 'total'))
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération des commentaires: {str(e)}")
            commentaires_par_bien = {}
        
        # Préparer les données pour le template
        for publication in publications:
            publication.visites = visites_par_bien.get(publication.bien_id, 0)
            publication.commentaires = commentaires_par_bien.get(publication.bien_id, 0)
        
        # Préparer le contexte
        context = {
            'publications': publications,
            'total_publications': publications.count(),
            'biens_publications': len({pub.bien_id for pub in publications if hasattr(pub, 'bien_id')}),
            'total_visites': sum(visites_par_bien.values()),
            'total_commentaires': sum(commentaires_par_bien.values()),
            'is_agent': request.user.profession == 'agent'
        }
        
        logger.info(f"Publications chargées avec succès: {context['total_publications']} publications, {context['total_visites']} visites, {context['total_commentaires']} commentaires")
        
        return render(request, 'comptes/mes_publications.html', context)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        error_msg = f"Erreur dans publications_view: {str(e)}\n{error_details}"
        logger.error(error_msg)
        
        # Afficher plus de détails dans la réponse en mode debug
        if settings.DEBUG:
            return HttpResponse(f"""
                <h1>Erreur lors du chargement des publications</h1>
                <p>Message d'erreur: {str(e)}</p>
                <pre>{error_details}</pre>
                <p>Veuillez rafraîchir la page ou réessayer plus tard.</p>
            """, status=500)
        else:
            return HttpResponseServerError("Une erreur est survenue lors du chargement des publications. Veuillez réessayer plus tard.")


def contacter_proprietaire(request, pk):
    """
    Vue pour contacter le propriétaire d'un bien
    """
    if not request.user.is_authenticated:
        messages.warning(request, 'Veuillez vous connecter pour contacter le propriétaire')
        return redirect('comptes:login')
    
    bien = get_object_or_404(BienImmobilier, pk=pk)
    
    if request.method == 'POST':
        try:
            sujet = request.POST.get('sujet', '')
            message = request.POST.get('message', '')
            
            if not sujet or not message:
                messages.error(request, 'Veuillez remplir tous les champs')
                return redirect('comptes:detail_bien', pk=bien.id)
            
            # Envoyer l'email au propriétaire
            sujet_email = f"[Contact] {sujet} - {bien.titre}"
            message_email = f"""
            Nouveau message concernant le bien : {bien.titre}
            
            De : {request.user.get_full_name() or request.user.username}
            Email : {request.user.email}
            Téléphone : {request.user.telephone or 'Non renseigné'}
            
            Message :
            {message}
            """
            
            send_mail(
                subject=sujet_email,
                message=message_email.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[bien.proprietaire.email],
                fail_silently=False,
            )
            
            messages.success(request, 'Votre message a été envoyé au propriétaire')
            return redirect('comptes:detail_bien', pk=bien.id)
            
        except Exception as e:
            messages.error(request, f'Une erreur est survenue : {str(e)}')
            return redirect('comptes:detail_bien', pk=bien.id)
    
    # Si méthode GET, rediriger vers la page du bien avec un ancre vers le formulaire de contact
    return redirect('comptes:detail_bien', pk=bien.id) + '#contact-form'
