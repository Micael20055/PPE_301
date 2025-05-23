from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='comptes/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('redirect/', views.redirect_user, name='redirect'),
    path('client-dashboard/', views.client_dashboard),
    path('agent-dashboard/', views.agent_dashboard),
    path('proprietaire-dashboard/', views.proprietaire_dashboard),
    path('', views.home, name='comptes_home'),  # Ajoute cette ligne
]