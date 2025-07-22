from django.urls import path
from . import views

# Définition de l'espace de noms de l'application
app_name = 'utilisateur'

urlpatterns = [
    # Pages principales
    path('', views.index, name='index'),
    path('biens/', views.biens, name='biens'),
    path('biens/<int:bien_id>/', views.detail_bien, name='detail_bien'),
    path('contact/', views.contact, name='contact'),
    path('a-propos/', views.a_propos, name='a_propos'),
    
    # Pages secondaires (à implémenter si nécessaire)
    path('blog/', views.blog, name='blog'),
    path('mentions-legales/', views.mentions_legales, name='mentions_legales'),
    path('conditions-generales/', views.conditions_generales, name='conditions_generales'),
    
    # Redirections pour compatibilité avec les anciennes URLs
    path('home/', views.index, name='home'),
    path('index/', views.index, name='index_old'),
    path('properties/', views.biens, name='properties'),
    path('property/<int:bien_id>/', views.detail_bien, name='property_details'),
]
