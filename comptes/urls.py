from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'comptes'

urlpatterns = [
    # Authentification
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('redirect_user/', views.redirect_user, name='redirect_user'),
    
    # Tableaux de bord
    path('proprietaire/dashboard/', views.proprietaire_dashboard, name='proprietaire_dashboard'),
    path('dashboard/', views.dashboard_home, name='dashboard_home'),
    path('client-dashboard/', views.client_dashboard, name='client_dashboard'),
    path('dashboard-agence/', views.dashboard_agence, name='dashboard_agence'),
    
    # Pages principales
    path('', views.home, name='home'),
    
    # Profil utilisateur
    path('profil/', views.profil_view, name='profil'),
    path('mes-favoris/', views.mes_favoris, name='mes_favoris'),
    
    path('client/', views.client_home, name='client_home'),
    path('about/', views.about, name='about'),
    path('blog/', views.blog, name='blog'),
    path('contact/', views.contact, name='contact'),
    path('search/', views.search, name='search'),
    path('index/', views.register, name='index'),
    path('agent-index/', views.agent_index, name='agent_index'),
    
    # Gestion des biens
    path('biens/', views.listings, name='listings'),
    path('biens/condos/', views.condos, name='condos'),
    path('biens/maisons/', views.houses, name='houses'),
    path('biens/terrains/', views.lands, name='lands'),
    path('detail-bien/<int:pk>/', views.detail_bien, name='detail_bien'),
    
    # Publications
    path('mes-publications/', views.mes_publications, name='mes_publications'),
    path('publications/', views.publications_view, name='publications'),
    path('publications/ajouter/', views.ajouter_publication, name='ajouter_publication'),
    path('publications/choix-type/', views.choix_type_publication, name='choix_type_publication'),
    path('publications/choix-bien/', views.choix_bien, name='choix_bien'),
    path('publications/modifier/<int:pk>/', views.modifier_publication, name='modifier_publication'),
    path('publications/supprimer/<int:pk>/', views.supprimer_publication, name='supprimer_publication'),
    
    # Gestion des visites et contacts
    path('visites/', views.visites_view, name='visites'),
    path('visites/programmer/<int:pk>/', views.programmer_visite, name='programmer_visite'),
    path('visites/annuler/<int:pk>/', views.annuler_visite, name='annuler_visite'),
    path('bien/<int:pk>/contacter/', views.contacter_proprietaire, name='contacter_proprietaire'),
    
    # Gestion des transactions
    path('transactions/', views.transactions_view, name='transactions'),
    
    # Gestion des paiements
    path('paiements/', views.paiements_view, name='paiements'),
    path('paiements/nouveau/', views.paiement_form, name='paiement_form'),
    
    # Profil et commentaires
    path('profil/', views.profil_view, name='profil_view'),
    path('profil/modifier/', views.modifier_profil, name='modifier_profil'),
    path('commentaires/', views.commentaires_view, name='commentaires'),
    path('commentaires/ajouter/<int:bien_id>/', views.ajouter_commentaire, name='ajouter_commentaire'),
]