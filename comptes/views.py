from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from .forms import CustomUserCreationForm
from .models import Utilisateur

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
        return redirect('/agent-dashboard/')
    elif user.profession == 'proprietaire':
        return redirect('/proprietaire-dashboard/')
    else:
        return redirect('/login/')

@login_required
@user_passes_test(lambda u: u.profession == 'client')
def client_dashboard(request):
    return HttpResponse("Bienvenue, client !")

@login_required
@user_passes_test(lambda u: u.profession == 'agent')
def agent_dashboard(request):
    return HttpResponse("Bienvenue, agent immobilier !")

@login_required
@user_passes_test(lambda u: u.profession == 'proprietaire')
def proprietaire_dashboard(request):
    return HttpResponse("Bienvenue, propriétaire !")
def home(request):
    return HttpResponse("Bienvenue sur la page d'accueil des comptes.")