from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, Q, Sum, F, Case, When, Value, IntegerField
from django.views.generic import ListView, DetailView, UpdateView, CreateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.conf import settings

from comptes.models import BienImmobilier, Visite, Paiement, Transaction, Commentaire, Utilisateur
from comptes.forms import CustomUserChangeForm

# Récupérer le modèle utilisateur personnalisé
User = get_user_model()

def admin_required(user):
    """Vérifie si l'utilisateur est un administrateur."""
    return user.is_authenticated and user.is_staff

@login_required
def dashboard_home(request):
    """Vue pour la page d'accueil du tableau de bord d'administration."""
    if not request.user.is_staff:
        return redirect('comptes:login')
    
    # Récupérer les statistiques des utilisateurs
    users = User.objects.all()
    today = timezone.now().date()
    last_week = today - timedelta(days=7)
    
    # Statistiques des utilisateurs
    user_stats = {
        'total': users.count(),
        'new_this_week': users.filter(date_joined__date__gte=last_week).count(),
        'clients': users.filter(profession='client').count(),
        'proprietaires': users.filter(profession='proprietaire').count(),
        'agents': users.filter(profession='agent').count(),
        'admins': users.filter(is_superuser=True).count(),
    }
    
    # Statistiques des biens immobiliers
    properties = BienImmobilier.objects.all()
    total_properties = properties.count()
    
    # Biens par type
    properties_by_type = properties.values('type_bien').annotate(
        count=Count('id')
    ).order_by('type_bien')
    
    # Statistiques des transactions
    transactions = Transaction.objects.all()
    total_revenue = transactions.aggregate(total=Sum('montant'))['total'] or 0
    
    # Dernières visites programmées
    recent_visits = Visite.objects.select_related('bien', 'client', 'proprietaire').order_by('-date_visite')[:5]
    
    # Derniers utilisateurs inscrits
    recent_users = users.order_by('-date_joined')[:5]
    
    # Dernières transactions
    recent_transactions = transactions.select_related('bien', 'acheteur', 'vendeur').order_by('-date_transaction')[:5]
    
    # Préparer les données pour les graphiques
    # Utilisateurs par jour des 30 derniers jours
    thirty_days_ago = today - timedelta(days=30)
    users_by_day = users.filter(date_joined__date__gte=thirty_days_ago).extra(
        select={'day': "date(date_joined)"}
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    # Préparer les données pour le graphique d'utilisateurs par jour
    user_dates = []
    user_counts = []
    
    for i in range(30):
        date = thirty_days_ago + timedelta(days=i)
        count = sum(1 for u in users_by_day if u['day'] == date)
        user_dates.append(date.strftime('%Y-%m-%d'))
        user_counts.append(count)
    
    # Préparer les données pour le graphique des utilisateurs par type
    users_by_type = users.values('profession').annotate(
        count=Count('id')
    ).order_by('profession')
    
    user_types = []
    user_type_counts = []
    
    for ut in users_by_type:
        profession = ut['profession']
        if profession is None:
            display_name = 'Non spécifié'
        else:
            display_name = dict(User.PROFESSION_CHOICES).get(profession, profession.capitalize() if profession else 'Non spécifié')
        user_types.append(display_name)
        user_type_counts.append(ut['count'])
    
    # Préparer le contexte
    context = {
        'stats': {
            'total_users': user_stats['total'],
            'new_users_this_week': user_stats['new_this_week'],
            'total_properties': total_properties,
            'total_revenue': total_revenue,
            'upcoming_visits': recent_visits.count(),
        },
        'recent_users': recent_users,
        'recent_visits': recent_visits,
        'recent_transactions': recent_transactions,
        'chart_data': {
            'user_dates': user_dates,
            'user_counts': user_counts,
            'user_types': user_types,
            'user_type_counts': user_type_counts,
        },
        'users_by_profession': dict(zip(user_types, user_type_counts)),
    }
    
    return render(request, 'admin_dashboard/index.html', context)


class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Vue pour afficher la liste des utilisateurs."""
    model = User
    template_name = 'admin_dashboard/users.html'
    context_object_name = 'users'
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        
        # Filtrage par recherche
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(username__icontains=query) |
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )
        
        # Filtrage par type d'utilisateur
        profession = self.request.GET.get('profession')
        if profession:
            queryset = queryset.filter(profession=profession)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        # Statistiques
        context['profession_filter'] = self.request.GET.get('profession', '')
        context['query'] = self.request.GET.get('q', '')
        context['proprietaires_count'] = User.objects.filter(profession='proprietaire').count()
        context['clients_count'] = User.objects.filter(profession='client').count()
        context['agents_count'] = User.objects.filter(profession='agent').count()
        
        return context


class BienImmobilierListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Vue pour afficher la liste des biens immobiliers."""
    model = BienImmobilier
    template_name = 'admin_dashboard/biens.html'
    context_object_name = 'biens'
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        queryset = BienImmobilier.objects.select_related('proprietaire').order_by('-id')
        
        # Filtrage par recherche
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(description__icontains=query) |
                Q(type_bien__icontains=query) |
                Q(proprietaire__username__icontains=query) |
                Q(proprietaire__email__icontains=query)
            )
        
        # Filtrage par type de bien
        type_bien = self.request.GET.get('type_bien')
        if type_bien:
            queryset = queryset.filter(type_bien=type_bien)
            
        # Filtrage par propriétaire
        proprietaire_id = self.request.GET.get('proprietaire')
        if proprietaire_id:
            queryset = queryset.filter(proprietaire_id=proprietaire_id)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        context['type_filter'] = self.request.GET.get('type_bien', '')
        context['proprietaire_filter'] = self.request.GET.get('proprietaire', '')
        context['query'] = self.request.GET.get('q', '')
        
        # Compteurs par type de bien
        context['total_biens'] = BienImmobilier.objects.count()
        context['maisons_count'] = BienImmobilier.objects.filter(type_bien='Maison').count()
        context['appartements_count'] = BienImmobilier.objects.filter(type_bien='Appartement').count()
        context['terrains_count'] = BienImmobilier.objects.filter(type_bien='Terrain').count()
        
        # Liste des propriétaires pour le filtre
        context['proprietaires'] = Utilisateur.objects.filter(
            profession='proprietaire'
        ).values('id', 'username', 'email')
        
        return context


class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Vue pour afficher les détails d'un utilisateur."""
    model = User
    template_name = 'admin_dashboard/user_detail.html'
    context_object_name = 'user_profile'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Récupérer les biens de l'utilisateur
        properties = BienImmobilier.objects.filter(proprietaire=user)
        
        # Récupérer les visites liées à l'utilisateur
        visits = Visite.objects.filter(Q(client=user) | Q(proprietaire=user))
        
        # Récupérer les transactions liées à l'utilisateur
        transactions = Transaction.objects.filter(Q(acheteur=user) | Q(vendeur=user))
        
        # Compter les biens par type
        properties_by_type = properties.values('type_bien').annotate(
            count=Count('id')
        ).order_by('type_bien')
        
        # Préparer les statistiques
        stats = {
            'total_properties': properties.count(),
            'properties_by_type': dict(properties_by_type.values_list('type_bien', 'count')),
            'visits_count': visits.count(),
            'transactions_count': transactions.count(),
        }
        
        context.update({
            'properties': properties.order_by('-id')[:5],  # Tri par ID au lieu de date_creation
            'properties_by_type': properties_by_type,
            'visits': visits.order_by('-date_visite')[:5],
            'transactions': transactions.order_by('-date_transaction')[:5],
            'stats': stats,
        })
        
        return context


class BienImmobilierListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Vue pour afficher la liste des biens immobiliers."""
    model = BienImmobilier
    template_name = 'admin_dashboard/biens.html'
    context_object_name = 'properties'
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrage par recherche
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(adresse__icontains=search_query) |
                Q(description__icontains=search_query)
            )
            
        # Filtrage par type de bien
        type_bien = self.request.GET.get('type_bien')
        if type_bien:
            queryset = queryset.filter(type_bien=type_bien)
            
        # Filtrage par statut de publication
        statut = self.request.GET.get('statut')
        if statut == 'publie':
            queryset = queryset.filter(est_publie=True)
        elif statut == 'brouillon':
            queryset = queryset.filter(est_publie=False)
            
        return queryset.order_by('-id')  # Tri par ID au lieu de date_creation
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        context['total_properties'] = self.get_queryset().count()
        context['published_properties'] = self.get_queryset().filter(est_publie=True).count()
        context['draft_properties'] = self.get_queryset().filter(est_publie=False).count()
        
        # Filtres
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_type'] = self.request.GET.get('type_bien', '')
        context['selected_status'] = self.request.GET.get('statut', '')
        
        return context


class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Vue pour modifier un utilisateur."""
    model = User
    form_class = CustomUserChangeForm
    template_name = 'admin_dashboard/user_edit.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_success_url(self):
        return reverse('admin_dashboard:user_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Les modifications ont été enregistrées avec succès.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_editing'] = True
        return context
    
    # Cette méthode ne fait plus rien car la logique a été déplacée dans dashboard_home
    pass

def analytics_variation(request):
    return render(request, 'admin/analytics-variation.html')

def apps_chat(request):
    return render(request, 'admin/apps-chat.html')

def apps_faq_section(request):
    return render(request, 'admin/apps-faq-section.html')

def apps_forum_discussion (request):
    return render(request, 'admin/apps-forum-discussion.html')
def apps_forum_list (request):
    return render(request, 'admin/apps-forum-list.html')
def apps_forum_threads (request):
    return render(request, 'admin/apps-forum-threads.html')
def apps_mailbox (request):
    return render(request, 'admin/apps-mailbox.html')
def charts_apexchart (request):
    return render(request, 'admin/charts-apexchart.html')
def charts_chartjs (request):
    return render(request, 'admin/charts-chartjs.html')
def charts_sparklines (request):
    return render(request, 'admin/charts-sparklines.html')
def components_accordions(request):
    return render(request, 'admin/components-accordions.html')
def components_calendar(request):
    return render(request, 'admin/components-calendar.html')
def components_carousel(request):
    return render(request, 'admin/components-carousel.html')
def components_count_up(request):
    return render(request, 'admin/components-count-up.html')
def components_guided_tours(request):
    return render(request, 'admin/components-guided-tours.html')
def components_image_crop(request):
    return render(request, 'admin/components-image-crop.html')
def components_loading_blocks(request):
    return render(request, 'admin/components-loading-blocks.html')
def components_maps(request):
    return render(request, 'admin/components-maps.html')
def components_modals(request):
    return render(request, 'admin/components-modals.html')
def components_notifications(request):
    return render(request, 'admin/components-notifications.html')
def components_pagination(request):
    return render(request, 'admin/components-pagination.html')
def components_progress_bar(request):
    return render(request, 'admin/components-progress-bar.html')
def components_rating(request):
    return render(request, 'admin/components-rating.html')
def components_scrollable_elements(request):
    return render(request, 'admin/components-scrollable-elements.html')
def components_tabs(request):
    return render(request, 'admin/components-tabs.html')
def components_tooltips_popovers(request):
    return render(request, 'admin/components-tooltips-popovers.html')
def components_tree_view (request):
    return render(request, 'admin/components-tree-view.html')
def dashbords_commerce_variation (request):
    return render(request, 'admin/dashbords-commerce-variation.html')
def dashbords_commerce (request):
    return render(request, 'admin/dashbords-commerce.html')
def dashbords_crm_variation (request):
    return render(request, 'admin/dashbords-crm-variation.html')
def dashbords_crm (request):
    return render(request, 'admin/dashbords-crm.html')
def dashbords_minimal_1 (request):
    return render(request, 'admin/dashbords-minimal-1.html')
def dashbords_minimal_2 (request):
    return render(request, 'admin/dashbords-minimal-2.html')
def dashbords_sales (request):
    return render(request, 'admin/dashbords-sales.html')
def dashbords_babges_labels (request):
    return render(request, 'admin/dashbords-babges-labels.html')
def elements_badges_labels (request):
    return render(request, 'admin/elements-badges-labels.html')
def elements_buttons_icons (request):
    return render(request, 'admin/elements-buttons-icons.html')
def elements_buttons_pills (request):
    return render(request, 'admin/elements-buttons-pills.html')
def elements_buttons_shadow (request):
    return render(request, 'admin/elements-buttons-shadow.html')
def elements_buttons_square (request):
    return render(request, 'admin/elements-buttons-square.html')    
def elements_standard (request):
    return render(request, 'admin/elements-standard.html')
def elements_crads (request):
    return render(request, 'admin/elements-crads.html')
def elements_dropdowns (request):
    return render(request, 'admin/elements-dropdowns.html')
def elements_icons (request):
    return render(request, 'admin/elements-icons.html')
def elements_list_group (request):
    return render(request, 'admin/elements-list-group.html')
def elements_loaders (request):
    return render(request, 'admin/elements-loaders.html')
def elements_navigation (request):
    return render(request, 'admin/elements-navigation.html')
def elements_timelines (request):
    return render(request, 'admin/elements-timelines.html')
def elements_utilities (request):
    return render(request, 'admin/elements-utilities.html')
def forms_clipboard (request):
    return render(request, 'admin/forms-clipboard.html')
def forms_controls (request):
    return render(request, 'admin/forms-controls.html')
def forms_datepicker (request):
    return render(request, 'admin/forms-datepicker.html')
def forms_input_masks (request):
    return render(request, 'admin/forms-input-masks.html')
def forms_input_selects (request):
    return render(request, 'admin/forms-input-selects.html')
def forms_layouts (request):
    return render(request, 'admin/forms-layouts.html')
def forms_range_slider (request):
    return render(request, 'admin/forms-range-slider.html')
def forms_textarea_autosize (request):
    return render(request, 'admin/forms-textarea-autosize.html')
def forms_toggle_switch (request):
    return render(request, 'admin/forms-toggle-switch.html')
def forms_validation (request):
    return render(request, 'admin/forms-validation.html')
def forms_wizard (request):
    return render(request, 'admin/forms-wizard.html')
def forms_wysiwyg_editor (request):
    return render(request, 'admin/forms-wysiwyg-editor.html')
def pages_forgot_password (request):
    return render(request, 'admin/pages-forgot-password.html')
def pages_forgot_password_boxed (request):
    return render(request, 'admin/pages-forgot-password-boxed.html')
def pages_login_boxed (request):
    return render(request, 'admin/pages-login-boxed.html')
def pages_login (request):
    return render(request, 'admin/pages-login.html')
def pages_register_boxed (request):
    return render(request, 'admin/pages-register-boxed.html')
def pages_register (request):
    return render(request, 'admin/pages-register.html')
def pages_register_boxed (request):
    return render(request, 'admin/pages-register-boxed.html')
def pages_register (request):
    return render(request, 'admin/pages-register.html')
def tables_data_tables (request):
    return render(request, 'admin/tables-data-tables.html')
def tables_grid (request):
    return render(request, 'admin/tables-grid.html')
def tables_grid (request):
    return render(request, 'admin/tables-grid.html')
def tables_regular (request):
    return render(request, 'admin/tables-regular.html')
def widgets_chart_boxes_2 (request):
    return render(request, 'admin/widgets-chart-boxes-2.html')
def widgets_chart_boxes_3 (request):
    return render(request, 'admin/widgets-chart-boxes-3.html')
def widgets_profile_boxes (request):
    return render(request, 'admin/widgets-profile-boxes.html')