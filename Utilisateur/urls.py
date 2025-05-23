from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('buy/', views.buy, name='buy'),
    path('blog/', views.blog, name='blog'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('index/', views.index, name='index'),
    path('properties/', views.properties, name='properties'),
    path('property/', views.property_details, name='property_details'),
    path('rent/', views.rent, name='rent'),
    path('view/', views.view, name='view'),
   
]
