from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from .forms import CustomUserCreationForm
from .models import Utilisateur, Publication, BienImmobilier, Transaction
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
        return redirect('agent_index')
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
    type_action = request.GET.get('type')
    bien = request.GET.get('bien')  # 'maison', 'appartement', 'terrain'
    # Sélectionne le bon formulaire selon le bien
    if bien == 'maison':
        form_class = MaisonForm
    elif bien == 'appartement':
        form_class = AppartementForm
    elif bien == 'terrain':
        form_class = TerrainForm
    else:
        form_class = None

    if request.method == 'POST' and form_class:
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            bien_obj = form.save(commit=False)
            bien_obj.proprietaire = request.user
            bien_obj.save()
            
            # Création automatique de la publication avec le prix du formulaire
            Publication.objects.create(
                bien=bien_obj,
                titre=f"{type_action.capitalize()} {bien}",
                description=f"Description {bien}",
                prix=form.cleaned_data['prix']  # Utilise le prix du formulaire
            )
            return redirect('mes_publications')
    else:
        form = form_class() if form_class else None

    return render(request, 'comptes/ajouter_publication.html', {
        'form': form,
        'type_action': type_action,
        'bien': bien,
    })

def modifier_publication(request, pk):
    publication = get_object_or_404(Publication, pk=pk)
    if request.method == 'POST':
        form = PublicationForm(request.POST, request.FILES, instance=publication)
        if form.is_valid():
            form.save()
            return redirect('mes_publications')
    else:
        form = PublicationForm(instance=publication)
    return render(request, 'comptes/modifier_publication.html', {'form': form})

def supprimer_publication(request, pk):
    publication = get_object_or_404(Publication, pk=pk)
    if request.method == 'POST':
        publication.delete()
        return redirect('mes_publications')
    return render(request, 'comptes/supprimer_publication.html', {'publication': publication})

@login_required
def mes_publications(request):
    # Récupérer les publications liées aux biens du propriétaire connecté
    publications = Publication.objects.filter(
        bien__proprietaire=request.user
    ).select_related('bien')  # Pour optimiser les requêtes
    return render(request, 'comptes/publications.html', {'publications': publications})
