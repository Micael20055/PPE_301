from django.urls import path
from . import views_admin

app_name = 'admin_dashboard'

urlpatterns = [
    path('dashboard/', views_admin.admin_dashboard, name='dashboard'),
    path('users/', views_admin.admin_users, name='users'),
    path('users/<int:user_id>/', views_admin.admin_user_detail, name='user_detail'),
]
