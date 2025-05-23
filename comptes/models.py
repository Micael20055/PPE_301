from django.db import models
from django.contrib.auth.models import AbstractUser


class Utilisateur(AbstractUser):
    PROFESSION_CHOICES = [
        ('client', 'Client'),
        ('agent', 'Agent Immobilier'),
        ('proprietaire', 'Propriétaire'),
    ]

    profession = models.CharField(max_length=20, choices=PROFESSION_CHOICES, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.profession})"
