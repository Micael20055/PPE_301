from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='comptes/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('redirect/', views.redirect_user, name='redirect'),
    path('client-dashboard/', views.client_dashboard, name='client_dashboard'),
    path('agent-dashboard/', views.agent_dashboard, name='agent_dashboard'),
    path('proprietaire-dashboard/', views.proprietaire_dashboard, name='proprietaire_dashboard'),
    path('', views.home, name='comptes_home'),  # Ajoute cette ligne
    path('index/', views.register, name='index'),
    path('agent-index/', views.agent_index, name='agent_index'),
    path('proprietaire-index/', views.proprietaire_index, name='proprietaire_index'),
    path('', views.dashboard_home, name='dashboard_home'),
    path('profil/', views.profil_view, name='dashboard_profil'),
    path('publications/', views.publications_view, name='mes_publications'),
    path('publications/ajouter/', views.ajouter_publication, name='ajouter_publication'),
    path('publications/choix-type/', views.choix_type_publication, name='choix_type_publication'),
    path('publications/choix-bien/', views.choix_bien, name='choix_bien'),
    path('commentaires/', views.commentaires_view, name='commentaires_proprietaire'),
    path('transactions/', views.transactions_view, name='transactions_proprietaire'),
    path('paiements/', views.paiements_view, name='paiements_proprietaire'),
    path('visites/', views.visites_view, name='visites_programmees'),
    path('publications/modifier/<int:pk>/', views.modifier_publication, name='modifier_publication'),
    path('publications/supprimer/<int:pk>/', views.supprimer_publication, name='supprimer_publication'),
]