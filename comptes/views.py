from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
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
    # Récupérer les statistiques
    total_biens = BienImmobilier.objects.count()
    total_clients = Utilisateur.objects.filter(profession='client').count()
    total_transactions = Transaction.objects.count()
    total_visites = Visite.objects.count()

    # Récupérer les biens de l'agence
    biens = BienImmobilier.objects.all().order_by('-id')[:6]  # Les 6 derniers biens

    return render(request, 'comptes/dashboard_agence.html', {
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

# This function was removed to avoid conflict with the more general detail_bien function below

@login_required
@user_passes_test(lambda u: u.profession == 'client')
def programmer_visite(request, pk):
    bien = get_object_or_404(BienImmobilier, pk=pk)
    
    if request.method == 'POST':
        try:
            date_str = request.POST.get('date_visite')
            # Convertir la date en datetime naive
            date_naive = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
            # Ajouter le fuseau horaire actif
            date_visite = timezone.make_aware(date_naive)
            
            # Vérifier si la date est dans le futur
            now = timezone.now()
            if date_visite <= now:
                return JsonResponse({'success': False, 'message': 'Veuillez sélectionner une date future'})
            
            # Vérifier si le client a déjà une visite programmée pour ce bien
            if Visite.objects.filter(bien=bien, client=request.user, statut='planifiee').exists():
                return JsonResponse({'success': False, 'message': 'Vous avez déjà une visite programmée pour ce bien'})
            
            # Créer la nouvelle visite
            visite = Visite.objects.create(
                bien=bien,
                client=request.user,
                proprietaire=bien.proprietaire,  # Associer automatiquement le propriétaire
                date_visite=date_visite,
                statut='planifiee',
                remarques=request.POST.get('remarques', '')
            )
            
            # Envoyer une notification au propriétaire
            try:
                subject = f'Nouvelle visite programmée pour {bien.get_type_bien_display()}' 
                message = f'''
                Bonjour {bien.proprietaire.get_full_name() or bien.proprietaire.username},
                
                Une nouvelle visite a été programmée pour votre bien :
                - Type: {bien.get_type_bien_display()}
                - Adresse: {bien.adresse}
                - Date: {date_visite.strftime('%d/%m/%Y à %H:%M')}
                - Client: {request.user.get_full_name() or request.user.username}
                - Téléphone: {request.user.telephone or 'Non renseigné'}
                - Email: {request.user.email}
                
                Connectez-vous à votre espace pour plus de détails.
                '''
                
                send_mail(
                    subject=subject,
                    message=message.strip(),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[bien.proprietaire.email],
                    fail_silently=False,
                )
            except Exception as e:
                # En cas d'erreur d'envoi d'email, on continue mais on log l'erreur
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur lors de l'envoi de la notification de visite : {str(e)}")
            
            return JsonResponse({
                'success': True, 
                'message': 'Visite programmée avec succès. Le propriétaire a été notifié.'
            })
            
        except ValueError as e:
            return JsonResponse({'success': False, 'message': 'Format de date invalide'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Une erreur est survenue : {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

@login_required
@user_passes_test(lambda u: u.profession == 'client')
def annuler_visite(request, pk):
    visite = get_object_or_404(Visite, pk=pk, client=request.user)
    visite.statut = 'annulee'
    visite.save()
    return redirect('comptes:client_home')

@login_required
@user_passes_test(lambda u: u.profession == 'client')
def contacter_proprietaire(request, pk):
    bien = get_object_or_404(BienImmobilier, pk=pk)
    proprietaire = bien.proprietaire
    
    if request.method == 'POST':
        message = request.POST.get('message')
        
        # Envoyer un email au propriétaire
        subject = f'Nouveau message concernant {bien.type_bien} - {bien.titre}'
        message_body = f"""Bonjour {proprietaire.username},

Vous avez reçu un nouveau message concernant votre bien {bien.type_bien} - {bien.titre}:

{message}

Cordialement,
L'équipe ImmoDash"""
        
        send_mail(
            subject,
            message_body,
            settings.DEFAULT_FROM_EMAIL,
            [proprietaire.email]
        )
        
        return JsonResponse({'success': True, 'message': 'Message envoyé avec succès'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

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
    
    # Récupérer les visites pour les biens du propriétaire
    visites = Visite.objects.filter(bien__proprietaire=request.user)
    total_visites = visites.count()
    
    # Récupérer les paiements via les transactions liées aux biens du propriétaire
    total_paiements = Paiement.objects.filter(
        bien__proprietaire=request.user
    ).count()
    
    # Préparer les données pour le template
    context = {
        'total_biens': total_biens,
        'total_visites': total_visites,
        'total_paiements': total_paiements,
        'biens': biens.order_by('-id')[:5],  # 5 biens les plus récents (par ID décroissant)
        'visites_recentes': visites.order_by('-date_visite')[:5]  # 5 visites les plus récentes
    }
    
    # Ajouter des logs de débogage
    print("\n=== DÉBOGAGE TABLEAU DE BORD PROPRIÉTAIRE ===")
    print(f"Utilisateur: {request.user} (ID: {request.user.id})")
    print(f"Nombre de biens: {biens.count()}")
    print(f"Nombre de visites: {visites.count()}")
    print("Contenu du contexte:", context)
    print("=== FIN DÉBOGAGE ===\n")
    
    return render(request, 'comptes/proprietaire_dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.profession == 'proprietaire')
def visites(request):
    # Récupérer toutes les visites du propriétaire
    visites = Visite.objects.filter(bien__proprietaire=request.user).order_by('-date_visite')
    return render(request, 'comptes/visites.html', {'visites': visites})

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
@user_passes_test(lambda u: u.profession == 'agent')
def agent_dashboard(request):
    # Récupérer les données de l'agence
    agence = request.user.agence
    
    # Récupérer les statistiques
    total_biens = BienImmobilier.objects.filter(proprietaire__agence=agence).count()
    total_clients = Utilisateur.objects.filter(profession='client').count()
    total_transactions = Transaction.objects.filter(bien__proprietaire__agence=agence).count()
    total_visites = Visite.objects.filter(bien__proprietaire__agence=agence).count()
    
    # Récupérer les dernières transactions
    transactions = Transaction.objects.filter(bien__proprietaire__agence=agence).order_by('-date_transaction')[:5]
    
    # Récupérer les prochaines visites
    visites = Visite.objects.filter(bien__proprietaire__agence=agence, date_visite__gte=timezone.now()).order_by('date_visite')[:5]
    
    context = {
        'agence': agence,
        'total_biens': total_biens,
        'total_clients': total_clients,
        'total_transactions': total_transactions,
        'total_visites': total_visites,
        'transactions': transactions,
        'visites': visites
    }
    
    return render(request, 'comptes/dashboard_agence.html', context)

@login_required
@user_passes_test(lambda u: u.profession == 'agent')
def agent_index(request):
    user = request.user
    # Nombre de biens publiés par ce propriétaire/agent
    biens_count = BienImmobilier.objects.filter(proprietaire=user).count()
    # Nombre de visites à venir (exemple, adapte selon ton modèle)
    visites_count = Visite.objects.filter(bien__proprietaire=user).count() if 'Visite' in globals() else 0
    # Nombre de transactions conclues
    transactions_count = Transaction.objects.filter(bien__proprietaire=user).count()
    biens = BienImmobilier.objects.filter(proprietaire=user)
    return render(request, 'comptes/index.html', {
        'biens_count': biens_count,
        'visites_count': visites_count,
        'transactions_count': transactions_count,
        'bien_list': biens,
    })

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
    total_visites = Visite.objects.filter(bien__proprietaire=request.user).count()
    
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
    type_bien = request.GET.get('type_bien', '')
    prix_min = request.GET.get('prix_min', '')
    prix_max = request.GET.get('prix_max', '')
    
    biens = BienImmobilier.objects.all()
    
    if type_bien:
        biens = biens.filter(type_bien=type_bien)
    
    if prix_min:
        biens = biens.filter(prix__gte=prix_min)
    
    if prix_max:
        biens = biens.filter(prix__lte=prix_max)
    
    context = {
        'biens': biens,
        'type_bien': type_bien,
        'prix_min': prix_min,
        'prix_max': prix_max
    }
    return render(request, 'comptes/search_results.html', context)

def get_default_image_url():
    """Retourne l'URL d'une image par défaut"""
    return '/static/images/default-property.jpg'

# Vue de détail du bien
def detail_bien(request, pk):
    bien = get_object_or_404(BienImmobilier, pk=pk)
    
    # Vérifier si le bien a une image, sinon utiliser une image par défaut
    image_url = get_default_image_url()
    if hasattr(bien, 'image') and bien.image:
        try:
            if bien.image.url:
                image_url = bien.image.url
        except ValueError:
            # Si l'image n'existe pas sur le système de fichiers
            pass
    
    # Déterminer le type de bien et récupérer les détails spécifiques
    details = None
    if hasattr(bien, 'maison'):
        details = bien.maison
    elif hasattr(bien, 'appartement'):
        details = bien.appartement
    elif hasattr(bien, 'terrain'):
        details = bien.terrain
    
    context = {
        'bien': bien,
        'image_url': image_url,
        'details': details,
        'has_image': hasattr(bien, 'image') and bool(bien.image)
    }
    
    return render(request, 'comptes/detail_bien.html', context)

# Vues pour les types de biens
def listings(request):
    biens = BienImmobilier.objects.all()
    context = {
        'biens': biens,
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

"""def visites_view(request):
    form = VisiteForm()
    return render(request, 'comptes/visites.html', {'form': form})
"""
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

def visites_view(request):
    if not request.user.is_authenticated or request.user.profession != 'proprietaire':
        return redirect('comptes:login')
    
    visites = Visite.objects.filter(bien__proprietaire=request.user).order_by('-date_visite')
    total_visites = visites.count()
    visites_en_attente = visites.filter(statut='en_attente').count()
    visites_confirmees = visites.filter(statut='confirme').count()
    
    return render(request, 'comptes/visites.html', {
        'visites': visites,
        'total_visites': total_visites,
        'visites_en_attente': visites_en_attente,
        'visites_confirmees': visites_confirmees
    })

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
                logger.error(f"L'agent {request.user.username} n'a pas d'agence associée")
                # Si l'agent n'a pas d'agence, on ne peut pas afficher de publications
                return render(request, 'comptes/mes_publications.html', {
                    'publications': [],
                    'total_publications': 0,
                    'biens_publications': 0,
                    'total_visites': 0,
                    'total_commentaires': 0,
                    'is_agent': True,
                    'error_message': "Votre compte agent n'est associé à aucune agence. Veuillez contacter l'administrateur."
                })
                
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
        commentaires_par_bien = dict(Commentaire.objects.filter(
            annonce__bien_id__in=bien_ids
        ).values('annonce__bien').annotate(total=Count('id')).values_list('annonce__bien', 'total'))
        
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
        error_msg = f"Erreur dans publications_view: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
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
