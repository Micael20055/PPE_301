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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('Utilisateur.urls')),  # Utilise le nom exact de ton dossier/app
    path('comptes/', include('comptes.urls')),  # pour les comptes
    path('accounts/login/', RedirectView.as_view(url='/comptes/login/')),  # Redirection vers notre page de connexion
    path('accounts/', include('django.contrib.auth.urls')),  # Pour les autres URLs d'authentification
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
