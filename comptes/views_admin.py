from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from .models import Utilisateur, BienImmobilier, Publication, Visite, Paiement, Transaction

# Vérifie si l'utilisateur est un administrateur
def is_admin(user):
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Statistiques générales
    stats = {
        'total_users': Utilisateur.objects.count(),
        'new_users_this_week': Utilisateur.objects.filter(
            date_joined__gte=timezone.now() - timedelta(days=7)
        ).count(),
        'total_properties': BienImmobilier.objects.count(),
        'total_publications': Publication.objects.count(),
        'total_visits': Visite.objects.count(),
        'total_transactions': Transaction.objects.count(),
        'total_revenue': Paiement.objects.aggregate(Sum('montant'))['montant__sum'] or 0,
    }
    
    # Derniers utilisateurs inscrits
    recent_users = Utilisateur.objects.order_by('-date_joined')[:5]
    
    # Dernières publications
    recent_publications = Publication.objects.select_related('bien').order_by('-date_creation')[:5]
    
    # Dernières visites
    recent_visits = Visite.objects.select_related('bien', 'client').order_by('-date_visite')[:5]
    
    # Dernières transactions
    recent_transactions = Transaction.objects.select_related('bien', 'acheteur').order_by('-date_transaction')[:5]
    
    # Répartition des utilisateurs par profession
    users_by_profession = (
        Utilisateur.objects
        .values('profession')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    context = {
        'stats': stats,
        'recent_users': recent_users,
        'recent_publications': recent_publications,
        'recent_visits': recent_visits,
        'recent_transactions': recent_transactions,
        'users_by_profession': users_by_profession,
        'active_dashboard': True,
    }
    
    return render(request, 'admin_dashboard/index.html', context)

@login_required
@user_passes_test(is_admin)
def admin_users(request):
    users = Utilisateur.objects.all().order_by('-date_joined')
    
    # Filtrage
    query = request.GET.get('q', '')
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
    
    # Filtre par profession
    profession = request.GET.get('profession')
    if profession:
        users = users.filter(profession=profession)
    
    context = {
        'users': users,
        'query': query,
        'profession_filter': profession,
        'active_users': True,
    }
    
    return render(request, 'admin_dashboard/users.html', context)

@login_required
@user_passes_test(is_admin)
def admin_user_detail(request, user_id):
    try:
        user = Utilisateur.objects.get(id=user_id)
    except Utilisateur.DoesNotExist:
        messages.error(request, "Utilisateur introuvable.")
        return redirect('admin_dashboard')
    
    # Récupérer les biens du propriétaire s'il en a
    properties = []
    if user.profession == 'proprietaire':
        properties = BienImmobilier.objects.filter(proprietaire=user)
    
    # Récupérer les visites si c'est un client ou un agent
    visits = Visite.objects.filter(Q(client=user) | Q(agent=user)).select_related('bien')
    
    context = {
        'user_profile': user,
        'properties': properties,
        'visits': visits,
    }
    
    return render(request, 'admin_dashboard/user_detail.html', context)
