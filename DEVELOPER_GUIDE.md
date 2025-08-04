# 🛠️ GUIDE DÉVELOPPEUR - APPLICATION IMMOBILIÈRE

## 📋 **STRUCTURE DU PROJET**

```
PPE_301/
├── comptes/                 # Application principale
│   ├── models.py           # Modèles de données
│   ├── views.py            # Vues (à refactoriser)
│   ├── forms.py            # Formulaires
│   ├── urls.py             # URLs
│   ├── utils.py            # Utilitaires et validations
│   ├── tests.py            # Tests unitaires
│   └── templates/          # Templates HTML
├── PPE_301/                # Configuration Django
│   ├── settings.py         # Configuration
│   └── urls.py            # URLs principales
├── static/                 # Fichiers statiques
├── media/                  # Fichiers uploadés
└── requirements.txt        # Dépendances
```

## 🚀 **INSTALLATION ET CONFIGURATION**

### 1. **Environnement virtuel**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### 2. **Installation des dépendances**
```bash
pip install -r requirements.txt
```

### 3. **Configuration des variables d'environnement**
```bash
# Copier le fichier d'exemple
cp env_example.txt .env

# Éditer le fichier .env avec vos valeurs
SECRET_KEY=votre-clé-secrète
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 4. **Base de données**
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. **Créer un superutilisateur**
```bash
python manage.py createsuperuser
```

## 🧪 **TESTS**

### **Lancer tous les tests**
```bash
python manage.py test
```

### **Lancer les tests d'une app spécifique**
```bash
python manage.py test comptes.tests
```

### **Lancer un test spécifique**
```bash
python manage.py test comptes.tests.UtilisateurModelTest
```

## 🔧 **DÉVELOPPEMENT**

### **Validation des formulaires**
```python
# Dans forms.py
def clean_field_name(self):
    value = self.cleaned_data.get('field_name')
    if value <= 0:
        raise forms.ValidationError("La valeur doit être positive")
    return value
```

### **Validation des modèles**
```python
# Dans models.py
from .utils import validate_superficie

superficie = models.FloatField(
    validators=[validate_superficie],
    help_text="Superficie en m²"
)
```

### **Gestion d'erreurs dans les vues**
```python
try:
    # Logique métier
    pass
except ValueError as e:
    return render(request, 'template.html', {
        'error_message': str(e)
    })
except Exception as e:
    logger.error(f"Erreur: {str(e)}")
    return render(request, 'template.html', {
        'error_message': "Une erreur inattendue s'est produite"
    })
```

## 📊 **BONNES PRATIQUES**

### **1. Sécurité**
- ✅ Toujours valider les données côté serveur
- ✅ Utiliser les décorateurs de sécurité (`@login_required`, `@user_passes_test`)
- ✅ Protéger contre les injections SQL (Django ORM)
- ✅ Valider les fichiers uploadés

### **2. Performance**
- ✅ Utiliser `select_related()` et `prefetch_related()` pour les requêtes
- ✅ Paginer les listes longues
- ✅ Optimiser les images avant upload
- ✅ Utiliser le cache pour les données statiques

### **3. Code Quality**
- ✅ Écrire des tests pour chaque fonctionnalité
- ✅ Documenter les fonctions complexes
- ✅ Utiliser des noms de variables explicites
- ✅ Suivre les conventions PEP 8

### **4. Interface utilisateur**
- ✅ Validation côté client ET serveur
- ✅ Messages d'erreur clairs et informatifs
- ✅ Design responsive
- ✅ Accessibilité (ARIA labels, etc.)

## 🐛 **DÉBOGAGE**

### **Logs Django**
```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Message de debug")
logger.info("Message d'information")
logger.warning("Avertissement")
logger.error("Erreur")
```

### **Django Debug Toolbar**
```bash
pip install django-debug-toolbar
```

### **Tests de performance**
```python
from django.test import TestCase
from django.db import connection

class PerformanceTest(TestCase):
    def test_query_count(self):
        with self.assertNumQueries(3):  # Vérifier le nombre de requêtes
            # Votre code ici
            pass
```

## 📝 **COMMANDES UTILES**

### **Django Management**
```bash
# Vérifier la configuration
python manage.py check

# Collecter les fichiers statiques
python manage.py collectstatic

# Créer des migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Shell Django
python manage.py shell

# Créer un superutilisateur
python manage.py createsuperuser
```

### **Base de données**
```bash
# Sauvegarder la base
python manage.py dumpdata > backup.json

# Restaurer la base
python manage.py loaddata backup.json

# Réinitialiser la base
python manage.py flush
```

## 🔄 **WORKFLOW DE DÉVELOPPEMENT**

### **1. Nouvelle fonctionnalité**
```bash
# 1. Créer une branche
git checkout -b feature/nouvelle-fonctionnalite

# 2. Développer
# - Modifier les modèles si nécessaire
# - Créer les vues
# - Écrire les tests
# - Mettre à jour la documentation

# 3. Tester
python manage.py test
python manage.py check

# 4. Commiter
git add .
git commit -m "feat: ajouter nouvelle fonctionnalité"

# 5. Merger
git checkout main
git merge feature/nouvelle-fonctionnalite
```

### **2. Correction de bug**
```bash
# 1. Reproduire le bug
# 2. Écrire un test qui échoue
# 3. Corriger le bug
# 4. Vérifier que le test passe
# 5. Commiter la correction
```

## 📚 **RESSOURCES**

### **Documentation Django**
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)

### **Outils recommandés**
- **IDE**: VS Code, PyCharm
- **Base de données**: SQLite (dev), PostgreSQL (prod)
- **Tests**: pytest-django
- **Linting**: flake8, black
- **Type checking**: mypy

### **Sécurité**
- [Django Security](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

---

**Dernière mise à jour** : Décembre 2024
**Version** : 1.0.0 