from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from comptes.models import BienImmobilier, Visite, Paiement, Transaction
from django.db.models import Count, Q

def home(request):
    # Récupérer tous les utilisateurs avec leurs informations détaillées
    User = get_user_model()
    
    # Récupérer les utilisateurs connectés (simplifié pour l'exemple)
    # En production, utilisez une logique plus sophistiquée avec les sessions
    connected_users = User.objects.select_related('profile').all()
    
    # Ajouter un attribut is_online à chaque utilisateur (simulé pour l'exemple)
    from django.utils import timezone
    from datetime import timedelta
    
    for user in connected_users:
        # Simuler des utilisateurs en ligne (dernière connexion < 15 minutes)
        user.is_online = user.last_login and \
                        (timezone.now() - user.last_login) < timedelta(minutes=15)
    
    # Compter les utilisateurs par type
    user_stats = {
        'total': connected_users.count(),
        'online': sum(1 for u in connected_users if hasattr(u, 'is_online') and u.is_online),
        'clients': connected_users.filter(is_client=True).count(),
        'proprietaires': connected_users.filter(est_proprietaire=True).count(),
        'agents': connected_users.filter(est_agent=True).count(),
        'agences': connected_users.filter(est_agence=True).count(),
        'admins': connected_users.filter(is_superuser=True).count()
    }
    
    # Statistiques des biens
    total_properties = BienImmobilier.objects.count()
    
    # Biens ajoutés ce mois-ci
    start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_properties = BienImmobilier.objects.filter(
        date_creation__gte=start_of_month
    ).count()
    
    # Visites à venir (dans les 30 prochains jours)
    upcoming_visits = Visite.objects.filter(
        date_visite__gte=timezone.now(),
        date_visite__lte=timezone.now() + timedelta(days=30)
    ).count()
    
    # Transactions récentes
    recent_transactions = Transaction.objects.select_related('bien', 'client', 'agent').order_by('-date_transaction')[:5]
    
    # Répartition des biens par type
    property_types = BienImmobilier.objects.values('type_bien').annotate(
        count=Count('type_bien')
    )
    
    # Préparer les données pour le graphique des biens par type
    property_type_data = {pt['type_bien']: pt['count'] for pt in property_types}
    
    # Données pour le graphique des inscriptions (30 derniers jours)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    registrations = User.objects.filter(
        date_joined__gte=thirty_days_ago
    ).extra({
        'date': "date(date_joined)"
    }).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Préparer les données pour le graphique des inscriptions
    registration_dates = [str(reg['date']) for reg in registrations]
    registration_counts = [reg['count'] for reg in registrations]
    
    # Préparer les données pour les graphiques
    property_type_data = list(property_type_data.items())
    
    # Préparer les données pour le graphique d'activité des utilisateurs
    activity_data = {
        'labels': registration_dates,
        'datasets': [{
            'label': 'Inscriptions',
            'data': registration_counts,
            'borderColor': '#4f46e5',
            'tension': 0.4,
            'fill': False
        }]
    }
    
    return render(request, 'admin/index.html', {
        'connected_users': connected_users,
        'user_stats': user_stats,
        'total_properties': total_properties,
        'monthly_properties': monthly_properties,
        'upcoming_visits': upcoming_visits,
        'recent_transactions': recent_transactions,
        'property_type_data': property_type_data,
        'activity_data': activity_data,
        'registration_dates': registration_dates,
        'registration_counts': registration_counts
    })

def analytics_variation (request):
    return render(request, 'admin/analytics-variation.html')

def apps_chat (request):
    return render(request, 'admin/apps-chat.html')

def apps_faq_section (request):
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