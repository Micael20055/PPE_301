from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from .forms import CustomUserCreationForm
from .models import Utilisateur, Publication, BienImmobilier, Transaction, Maison, Appartement, Terrain
from .forms import PublicationForm, CommentaireForm, TransactionForm, PaiementForm
from .forms import MaisonForm, AppartementForm, TerrainForm

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('redirect')
    else:
        form = CustomUserCreationForm()
    return render(request, 'comptes/register.html', {'form': form})

@login_required
def redirect_user(request):
    user = request.user
    if user.is_superuser:
        return redirect('/admin/')
    if user.profession == 'client':
        return redirect('home')
    elif user.profession == 'agent':
        return redirect('mes_publications')
    elif user.profession == 'proprietaire':
        return redirect('proprietaire_index')
    else:
        return redirect('/login/')

@login_required
@user_passes_test(lambda u: u.profession == 'client')
def client_dashboard(request):
    return HttpResponse("Bienvenue, client !")
def home(request):
    return redirect('register')

@login_required
@user_passes_test(lambda u: u.profession == 'agent')
def agent_dashboard(request):
    return HttpResponse("Bienvenue, agent immobilier !")

@login_required
@user_passes_test(lambda u: u.profession == 'proprietaire')
def proprietaire_dashboard(request):
    return HttpResponse("Bienvenue, propriétaire !")

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
    return render(request, 'comptes/index_proprietaire.html')



def dashboard_home(request):
    biens = BienImmobilier.objects.all().select_related('maison', 'appartement', 'terrain')
    # Ajoute aussi les autres contextes déjà présents
    return render(request, 'comptes/index.html', {
        'biens': biens,
        # ... autres variables de contexte ...
    })

def profil_view(request):
    return render(request, 'comptes/profil.html')

@login_required
def publications_view(request):
    # Récupérer les publications liées aux biens du propriétaire connecté
    publications = Publication.objects.filter(bien__proprietaire=request.user)
    return render(request, 'comptes/publications.html', {'publications': publications})

def commentaires_view(request):
    form = CommentaireForm()
    return render(request, 'comptes/commentaires.html', {'form': form})

"""def visites_view(request):
    form = VisiteForm()
    return render(request, 'comptes/visites.html', {'form': form})
"""
def transactions_view(request):
    form = TransactionForm()
    return render(request, 'comptes/transactions.html', {'form': form})

def paiements_view(request):
    form = PaiementForm()
    return render(request, 'comptes/paiements.html', {'form': form})

def visites_view(request):
    return render(request, 'comptes/visites.html')

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
            print(f"Bien créé avec ID: {bien_base.id}")
            print(f"POST data: {request.POST}")
            
            # Créer le type de bien spécifique
            if bien == 'maison':
                print("\nCréation de la maison...")
                maison_form = MaisonForm(request.POST)
                print(f"\nDonnées du formulaire maison: {maison_form.data}")
                print(f"\nErreurs initiales: {maison_form.errors}")
                
                if maison_form.is_valid():
                    maison = maison_form.save(commit=False)
                    maison.bien = bien_base
                    maison.save()
                    print("\nMaison créée avec succès")
                else:
                    print(f"\nErreurs du formulaire maison: {maison_form.errors}")
                    print(f"\nTypes des champs: {maison_form.fields.keys()}")
                    print(f"\nDonnées nettoyées: {maison_form.cleaned_data}")
                    return render(request, 'comptes/ajouter_publication.html', {
                        'type_action': type_action,
                        'bien': bien,
                        'error_message': "Erreur dans le formulaire de la maison",
                        'maison_form': maison_form,
                        'appartement_form': appartement_form,
                        'terrain_form': terrain_form
                    })
            elif bien == 'appartement':
                print("\nCréation de l'appartement...")
                appartement_form = AppartementForm(request.POST)
                print(f"\nDonnées du formulaire appartement: {appartement_form.data}")
                print(f"\nErreurs initiales: {appartement_form.errors}")
                
                if appartement_form.is_valid():
                    appartement = appartement_form.save(commit=False)
                    appartement.bien = bien_base
                    appartement.save()
                    print("\nAppartement créé avec succès")
                else:
                    print(f"\nErreurs du formulaire appartement: {appartement_form.errors}")
                    print(f"\nTypes des champs: {appartement_form.fields.keys()}")
                    print(f"\nDonnées nettoyées: {appartement_form.cleaned_data}")
                    return render(request, 'comptes/ajouter_publication.html', {
                        'type_action': type_action,
                        'bien': bien,
                        'error_message': "Erreur dans le formulaire de l'appartement",
                        'maison_form': maison_form,
                        'appartement_form': appartement_form,
                        'terrain_form': terrain_form
                    })
            elif bien == 'terrain':
                print("\nCréation du terrain...")
                terrain_form = TerrainForm(request.POST)
                print(f"\nDonnées du formulaire terrain: {terrain_form.data}")
                print(f"\nErreurs initiales: {terrain_form.errors}")
                
                if terrain_form.is_valid():
                    terrain = terrain_form.save(commit=False)
                    terrain.bien = bien_base
                    terrain.save()
                    print("\nTerrain créé avec succès")
                else:
                    print(f"\nErreurs du formulaire terrain: {terrain_form.errors}")
                    print(f"\nTypes des champs: {terrain_form.fields.keys()}")
                    print(f"\nDonnées nettoyées: {terrain_form.cleaned_data}")
                    return render(request, 'comptes/ajouter_publication.html', {
                        'type_action': type_action,
                        'bien': bien,
                        'error_message': "Erreur dans le formulaire du terrain",
                        'maison_form': maison_form,
                        'appartement_form': appartement_form,
                        'terrain_form': terrain_form
                    })
                
            # Créer la publication
            Publication.objects.create(
                bien=bien_base,
                titre=f"{type_action.capitalize()} {bien}",
                description=description,
                prix=prix
            )
            print("\nPublication créée avec succès")
            
            return redirect('mes_publications')
            
        except ValueError as e:
            print(f"Erreur de valeur: {str(e)}")
            return render(request, 'comptes/ajouter_publication.html', {
                'type_action': type_action,
                'bien': bien,
                'error_message': str(e),
                'maison_form': maison_form,
                'appartement_form': appartement_form,
                'terrain_form': terrain_form
            })
        except Exception as e:
            print(f"Erreur: {str(e)}")
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
    
    # Récupérer la publication et le bien associé
    publication = get_object_or_404(Publication, pk=pk)
    bien = publication.bien
    
    # Vérifier que l'utilisateur est le propriétaire du bien
    if bien.proprietaire != request.user:
        return HttpResponse("Vous n'avez pas l'autorisation de modifier cette publication", status=403)
    
    # Initialiser les formulaires
    publication_form = PublicationForm(instance=publication)
    bien_form = None
    
    # Initialiser le formulaire spécifique selon le type de bien
    if bien.type_bien == 'Maison':
        bien_form = MaisonForm(instance=bien.maison)
    elif bien.type_bien == 'Appartement':
        bien_form = AppartementForm(instance=bien.appartement)
    elif bien.type_bien == 'Terrain':
        bien_form = TerrainForm(instance=bien.terrain)
    
    if request.method == 'POST':
        # Traiter le formulaire de base
        publication_form = PublicationForm(request.POST, instance=publication)
        
        # Mettre à jour le bien
        bien.superficie = request.POST.get('superficie', bien.superficie)
        bien.description = request.POST.get('description', bien.description)
        bien.prix = request.POST.get('prix', bien.prix)
        if 'image' in request.FILES:
            bien.image = request.FILES['image']
        bien.save()
        
        # Mettre à jour la publication
        publication_form.save()
        
        # Mettre à jour le formulaire spécifique
        if bien_form:
            bien_form = bien_form.__class__(request.POST, instance=getattr(bien, bien.type_bien.lower()))
            if bien_form.is_valid():
                bien_form.save()
        
        return redirect('mes_publications')
    
    return render(request, 'comptes/modifier_publication.html', {
        'publication_form': publication_form,
        'bien_form': bien_form,
        'bien': bien
    })

@login_required
def supprimer_publication(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')
    publication = get_object_or_404(Publication, pk=pk)
    
    # Vérifier que l'utilisateur est le propriétaire du bien
    if publication.bien.proprietaire != request.user:
        return HttpResponse("Vous n'avez pas l'autorisation de supprimer cette publication", status=403)
    
    if request.method == 'POST':
        publication.delete()
        return redirect('mes_publications')
    return render(request, 'comptes/supprimer_publication.html', {'publication': publication})

@login_required
def mes_publications(request):
    if not request.user.is_authenticated:
        return redirect('login')
    # Récupérer les publications liées aux biens du propriétaire connecté
    publications = Publication.objects.filter(
        bien__proprietaire=request.user
    ).select_related('bien')  # Pour optimiser les requêtes
    return render(request, 'comptes/publications.html', {'publications': publications})
