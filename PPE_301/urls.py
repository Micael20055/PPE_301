"""
URL configuration for PPE_301 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.views.decorators.http import require_GET
from dashboard import views as dashboard_views

# Désactiver l'accès à l'admin Django
@require_GET
def admin_redirect(request):
    return HttpResponseRedirect('/admin-dashboard/')

# Configuration de l'interface d'administration moderne
def admin_required(user):
    return user.is_authenticated and user.is_staff

admin_site_patterns = [
    path('', login_required(
        user_passes_test(admin_required, login_url='comptes:login')(dashboard_views.dashboard_home),
        login_url='comptes:login'
    ), name='admin_dashboard'),
    path('users/', include([
        path('', dashboard_views.UserListView.as_view(), name='user_list'),
        path('<int:pk>/', dashboard_views.UserDetailView.as_view(), name='user_detail'),
        path('<int:pk>/edit/', dashboard_views.UserUpdateView.as_view(), name='user_edit'),
    ])),
]

# Désactiver l'interface admin par défaut
admin.site.site_header = "Administration (désactivée)"
admin.site.site_title = "Administration (désactivée)"
admin.site.index_title = "Veuillez utiliser le tableau de bord d'administration moderne"
admin.site.site_url = "/admin-dashboard/"

urlpatterns = [
    # Rediriger l'ancienne URL admin vers le nouveau tableau de bord
    path('admin/', admin_redirect, name='admin_redirect'),
    path('admin-dashboard/', include((admin_site_patterns, 'admin_dashboard'), namespace='admin_dashboard')),
    path('', include('Utilisateur.urls')),  # Utilise le nom exact de ton dossier/app
    path('comptes/', include('comptes.urls')),  # pour les comptes
    path('accounts/login/', RedirectView.as_view(url='/comptes/login/')),  # Redirection vers notre page de connexion
    path('accounts/', include('django.contrib.auth.urls')),  # Pour les autres URLs d'authentification
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
