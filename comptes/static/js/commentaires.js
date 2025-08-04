/**
 * Gestion des interactions des commentaires côté client
 * - Répondre à un commentaire
 * - Supprimer un commentaire
 * - Afficher les notifications
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialiser le gestionnaire de notifications s'il n'est pas déjà chargé
    if (typeof NotificationManager === 'undefined') {
        console.warn('Le gestionnaire de notifications n\'est pas chargé. Les notifications ne fonctionneront pas correctement.');
        // Charger le script des notifications
        const script = document.createElement('script');
        script.src = '/static/js/notifications.js';
        script.onload = initCommentaires;
        document.head.appendChild(script);
    } else {
        initCommentaires();
    }
});

function initCommentaires() {
    // Déléguer les événements pour gérer le chargement dynamique
    document.body.addEventListener('click', handleCommentActions);
    document.body.addEventListener('submit', handleCommentForms);
    
    // Initialiser les tooltips
    initTooltips();
    
    console.log('Module commentaires initialisé');
}

// Gérer les clics sur les boutons d'action des commentaires
function handleCommentActions(event) {
    const target = event.target.closest('[data-action]');
    if (!target) return;
    
    event.preventDefault();
    
    const action = target.getAttribute('data-action');
    const commentId = target.closest('[data-comment-id]')?.getAttribute('data-comment-id');
    
    if (!commentId) {
        console.error('ID de commentaire non trouvé');
        return;
    }
    
    switch(action) {
        case 'reply':
            toggleReplyForm(commentId, target);
            break;
            
        case 'cancel-reply':
            hideReplyForm(commentId);
            break;
            
        case 'delete':
            if (confirm('Êtes-vous sûr de vouloir supprimer ce commentaire ? Cette action est irréversible.')) {
                deleteComment(commentId, target.closest('[data-comment-id]'));
            }
            break;
    }
}

// Gérer la soumission des formulaires de commentaires
function handleCommentForms(event) {
    const form = event.target.closest('form[data-comment-form]');
    if (!form) return;
    
    event.preventDefault();
    
    const formData = new FormData(form);
    const commentId = form.getAttribute('data-comment-id') || null;
    const isReply = form.closest('[data-comment-id]') !== null;
    
    submitCommentForm(form, formData, commentId, isReply);
}

// Afficher/masquer le formulaire de réponse
function toggleReplyForm(commentId, button) {
    const commentElement = document.querySelector(`[data-comment-id="${commentId}"]`);
    if (!commentElement) return;
    
    // Vérifier si le formulaire existe déjà
    const existingForm = commentElement.querySelector('.reply-form-container');
    if (existingForm) {
        existingForm.remove();
        return;
    }
    
    // Afficher un indicateur de chargement
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'mt-4 text-center py-4';
    loadingIndicator.innerHTML = '<i class="fas fa-spinner fa-spin text-indigo-600"></i> Chargement du formulaire...';
    
    const formContainer = document.createElement('div');
    formContainer.className = 'reply-form-container mt-4';
    formContainer.appendChild(loadingIndicator);
    
    // Trouver la zone de réponse dédiée
    const replyFormContainer = commentElement.querySelector(`#reply-form-${commentId}`);
    if (replyFormContainer) {
        // Vider la zone de réponse et y ajouter le formulaire
        replyFormContainer.innerHTML = '';
        replyFormContainer.appendChild(formContainer);
        replyFormContainer.classList.remove('hidden');
    } else {
        // Si la zone de réponse n'existe pas, ajouter à la fin du commentaire
        const commentContent = commentElement.querySelector('.pl-12');
        if (commentContent) {
            commentContent.appendChild(formContainer);
        } else {
            commentElement.appendChild(formContainer);
        }
    }
    
    // Charger le formulaire via AJAX
    console.log(`DEBUG: Chargement du formulaire pour le commentaire ${commentId}`);
    fetch(`/comptes/commentaires/repondre/?repondre_a=${commentId}`)
        .then(response => {
            console.log(`DEBUG: Réponse reçue, status: ${response.status}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(`DEBUG: Données reçues:`, data);
            if (data.success && data.form_html) {
                formContainer.innerHTML = data.form_html;
                
                // Initialiser les tooltips pour le nouveau contenu
                initTooltips(formContainer);
                
                // Faire défiler jusqu'au formulaire
                formContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            } else {
                throw new Error(data.message || 'Erreur lors du chargement du formulaire');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            formContainer.innerHTML = `
                <div class="bg-red-50 border-l-4 border-red-400 p-4">
                    <div class="flex">
                        <div class="flex-shrink-0">
                            <i class="fas fa-exclamation-circle text-red-400"></i>
                        </div>
                        <div class="ml-3">
                            <p class="text-sm text-red-700">
                                Erreur: ${error.message}
                                <button type="button" class="text-red-700 underline" onclick="this.closest('.reply-form-container').remove()">Fermer</button>
                            </p>
                        </div>
                    </div>
                </div>
            `;
        });
}

// Masquer le formulaire de réponse
function hideReplyForm(commentId) {
    const commentElement = document.querySelector(`[data-comment-id="${commentId}"]`);
    if (!commentElement) return;
    
    const formContainer = commentElement.querySelector('.reply-form-container');
    if (formContainer) {
        formContainer.remove();
    }
}

// Soumettre un formulaire de commentaire (création ou réponse)
async function submitCommentForm(form, formData, commentId, isReply = false) {
    const submitButton = form.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.innerHTML;
    
    // Afficher l'indicateur de chargement
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Publication en cours...';
    
    try {
        // Déterminer l'URL de soumission
        let submitUrl;
        if (isReply) {
            submitUrl = '/comptes/commentaires/repondre/';
        } else {
            submitUrl = form.action || window.location.href;
        }
        
        const response = await fetch(submitUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Gérer la notification si elle est présente
            if (data.notification) {
                const notification = data.notification;
                
                // Afficher la notification
                if (typeof NotificationManager !== 'undefined') {
                    NotificationManager.show(
                        notification.type || 'success',
                        notification.title || 'Succès',
                        notification.message || 'Action effectuée avec succès.'
                    );
                }
                
                // Si c'est une réponse à un commentaire, l'ajouter à la liste
                if (notification.parent_id && notification.html) {
                    const parentComment = document.querySelector(`[data-comment-id="${notification.parent_id}"]`);
                    if (parentComment) {
                        // Créer un conteneur pour les réponses s'il n'existe pas
                        let repliesContainer = parentComment.querySelector('.replies-container');
                        if (!repliesContainer) {
                            repliesContainer = document.createElement('div');
                            repliesContainer.className = 'replies-container mt-4 border-t border-gray-100 pt-4 space-y-4';
                            parentComment.appendChild(repliesContainer);
                        }
                        
                        // Créer un élément temporaire pour parser le HTML
                        const temp = document.createElement('div');
                        temp.innerHTML = notification.html.trim();
                        const newReply = temp.firstChild;
                        
                        // Ajouter la réponse à la liste
                        repliesContainer.appendChild(newReply);
                        
                        // Faire défiler jusqu'à la nouvelle réponse
                        newReply.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                        
                        // Ajouter une classe pour la mise en évidence
                        newReply.classList.add('bg-blue-50', 'border-l-4', 'border-blue-400', 'animate-pulse');
                        
                        // Supprimer la mise en évidence après un délai
                        setTimeout(() => {
                            newReply.classList.remove('bg-blue-50', 'border-l-4', 'border-blue-400', 'animate-pulse');
                        }, 3000);
                    }
                }
            }
            
            // Réinitialiser le formulaire
            if (form) {
                form.reset();
                
                // Si c'est un formulaire de réponse, le masquer
                const formContainer = form.closest('.reply-form-container');
                if (formContainer) {
                    formContainer.remove();
                }
            }
            
        } else {
            // Afficher les erreurs de validation
            if (data.errors) {
                let errorMessage = 'Veuillez corriger les erreurs suivantes :<br>';
                for (const field in data.errors) {
                    errorMessage += `- ${data.errors[field].join('<br>')}<br>`;
                }
                
                if (typeof NotificationManager !== 'undefined') {
                    NotificationManager.error('Erreur de validation', errorMessage);
                }
            } else {
                if (typeof NotificationManager !== 'undefined') {
                    NotificationManager.error('Erreur', data.message || 'Une erreur est survenue lors de la publication.');
                }
            }
        }
    } catch (error) {
        console.error('Erreur lors de la soumission du formulaire :', error);
        if (typeof NotificationManager !== 'undefined') {
            NotificationManager.error('Erreur', 'Une erreur est survenue lors de la communication avec le serveur.');
        }
    } finally {
        // Réactiver le bouton de soumission
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.innerHTML = originalButtonText;
        }
    }
}

// Supprimer un commentaire
async function deleteComment(commentId, commentElement) {
    if (!commentId || !commentElement) return;
    
    // Confirmer la suppression
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce commentaire ? Cette action est irréversible.')) {
        return;
    }
    
    // Afficher un indicateur de chargement
    const originalContent = commentElement.innerHTML;
    commentElement.innerHTML = `
        <div class="p-4 text-center">
            <i class="fas fa-spinner fa-spin text-indigo-600"></i>
            <span class="ml-2 text-gray-600">Suppression en cours...</span>
        </div>
    `;
    
    try {
        const response = await fetch(`/comptes/commentaires/supprimer/${commentId}/`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Afficher une notification de succès
            if (typeof NotificationManager !== 'undefined') {
                NotificationManager.success('Succès', 'Le commentaire a été supprimé avec succès.');
            } else {
                alert('Le commentaire a été supprimé avec succès.');
            }
            
            // Supprimer l'élément du DOM avec une animation
            commentElement.style.opacity = '0';
            commentElement.style.transition = 'opacity 0.3s ease-out';
            
            setTimeout(() => {
                commentElement.remove();
                
                // Vérifier s'il reste des commentaires
                const commentsContainer = document.querySelector('#commentaires-container');
                if (commentsContainer && commentsContainer.children.length === 0) {
                    // Afficher un message si aucun commentaire n'est disponible
                    commentsContainer.innerHTML = `
                        <div class="bg-white p-6 rounded-lg shadow-md text-center">
                            <i class="fas fa-comment-slash text-4xl text-gray-300 mb-3"></i>
                            <p class="text-gray-600">Aucun commentaire pour le moment.</p>
                        </div>
                    `;
                }
            }, 300);
        } else {
            // Afficher un message d'erreur
            const errorMessage = data.message || 'Une erreur est survenue lors de la suppression du commentaire.';
            if (typeof NotificationManager !== 'undefined') {
                NotificationManager.error('Erreur', errorMessage);
            } else {
                alert('Erreur: ' + errorMessage);
            }
            
            // Restaurer le contenu original
            commentElement.innerHTML = originalContent;
        }
    } catch (error) {
        console.error('Erreur lors de la suppression du commentaire :', error);
        
        // Afficher un message d'erreur
        const errorMessage = 'Une erreur est survenue lors de la communication avec le serveur : ' + error.message;
        if (typeof NotificationManager !== 'undefined') {
            NotificationManager.error('Erreur', errorMessage);
        } else {
            alert('Erreur: ' + errorMessage);
        }
        
        // Restaurer le contenu original
        commentElement.innerHTML = originalContent;
    }
}

// Initialiser les tooltips
function initTooltips(container = document) {
    // Utiliser Tippy.js si disponible, sinon utiliser le title natif
    if (typeof tippy !== 'undefined') {
        tippy(container.querySelectorAll('[data-tippy-content]'), {
            allowHTML: true,
            placement: 'top',
            animation: 'scale',
            theme: 'light-border',
            delay: [100, 0],
            duration: [100, 0],
            interactive: true
        });
    }
}

// Récupérer un cookie par son nom
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
