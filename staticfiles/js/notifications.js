/**
 * Gestion centralisée des notifications
 * 
 * Utilisation :
 * - Notification.show('success', 'Titre', 'Message', { action: 'Voir', url: '/lien' })
 * - Notification.show('error', 'Erreur', 'Une erreur est survenue')
 * - Notification.show('info', 'Information', 'Voici une information')
 * - Notification.show('warning', 'Attention', 'Ceci est un avertissement')
 */

const Notification = (function() {
    // Compteur pour les IDs uniques
    let counter = 0;
    
    // Configuration par défaut
    const defaults = {
        autoDismiss: true,
        duration: 5000,
        position: 'top-right',
        showClose: true,
        showAction: true
    };
    
    // Initialisation du conteneur de notifications
    function initContainer() {
        let container = document.getElementById('notification-container');
        
        // Créer le conteneur s'il n'existe pas
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'fixed top-4 right-4 z-50 space-y-4';
            container.style.maxWidth = '24rem';
            document.body.appendChild(container);
        }
        
        return container;
    }
    
    // Créer une notification
    function createNotification(type, title, message, options = {}) {
        // Fusionner les options avec les valeurs par défaut
        const config = { ...defaults, ...options };
        const container = initContainer();
        
        // Créer un ID unique pour la notification
        const id = `notification-${Date.now()}-${counter++}`;
        
        // Déterminer l'icône en fonction du type
        let icon = 'info-circle';
        switch (type) {
            case 'success':
                icon = 'check-circle';
                break;
            case 'error':
                icon = 'exclamation-circle';
                break;
            case 'warning':
                icon = 'exclamation-triangle';
                break;
            default:
                icon = 'info-circle';
        }
        
        // Créer l'élément de notification
        const notification = document.createElement('div');
        notification.className = `notification ${type} transform transition-all duration-300 ease-in-out translate-x-0 opacity-100`;
        notification.role = 'alert';
        notification.id = id;
        
        // Construire le HTML de la notification
        notification.innerHTML = `
            <div class="px-6 py-4 rounded-md shadow-lg flex items-start">
                <div class="flex-shrink-0">
                    <i class="fas fa-${icon} text-xl"></i>
                </div>
                <div class="ml-4 flex-1">
                    <div class="flex justify-between items-start">
                        <p class="font-medium text-gray-900">${title}</p>
                        ${config.showClose ? `
                        <button type="button" class="text-gray-400 hover:text-gray-500 focus:outline-none notification-close">
                            <span class="sr-only">Fermer</span>
                            <i class="fas fa-times"></i>
                        </button>
                        ` : ''}
                    </div>
                    <p class="mt-1 text-sm text-gray-600">
                        ${message}
                    </p>
                    ${config.showAction && config.action ? `
                    <div class="mt-2 flex justify-end">
                        <a href="${config.url || '#'}" class="text-sm font-medium text-indigo-600 hover:text-indigo-500">
                            ${config.action}
                        </a>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        // Ajouter la notification au conteneur
        container.insertBefore(notification, container.firstChild);
        
        // Démarrer le minuteur pour la fermeture automatique
        let dismissTimeout;
        if (config.autoDismiss) {
            dismissTimeout = setTimeout(() => {
                dismiss(notification);
            }, config.duration);
        }
        
        // Gérer le clic sur le bouton de fermeture
        const closeButton = notification.querySelector('.notification-close');
        if (closeButton) {
            closeButton.addEventListener('click', (e) => {
                e.preventDefault();
                if (dismissTimeout) clearTimeout(dismissTimeout);
                dismiss(notification);
            });
        }
        
        // Gérer le clic sur le bouton d'action
        const actionButton = notification.querySelector('a');
        if (actionButton) {
            actionButton.addEventListener('click', () => {
                if (config.onAction && typeof config.onAction === 'function') {
                    config.onAction();
                }
                if (dismissTimeout) clearTimeout(dismissTimeout);
                dismiss(notification);
            });
        }
        
        // Fonction pour fermer la notification
        function dismiss(notificationElement) {
            if (!notificationElement) return;
            
            // Animation de sortie
            notificationElement.style.transform = 'translateX(100%)';
            notificationElement.style.opacity = '0';
            
            // Supprimer l'élément après l'animation
            setTimeout(() => {
                if (notificationElement.parentNode) {
                    notificationElement.parentNode.removeChild(notificationElement);
                }
            }, 300);
        }
        
        // Exposer la méthode de fermeture
        notification.dismiss = () => dismiss(notification);
        
        return notification;
    }
    
    // Méthodes publiques
    return {
        /**
         * Affiche une notification
         * @param {string} type - Type de notification (success, error, warning, info)
         * @param {string} title - Titre de la notification
         * @param {string} message - Message de la notification
         * @param {Object} options - Options supplémentaires
         * @param {string} options.action - Texte du bouton d'action
         * @param {string} options.url - URL du bouton d'action
         * @param {Function} options.onAction - Fonction à exécuter lors du clic sur le bouton d'action
         * @param {boolean} options.autoDismiss - Fermeture automatique (défaut: true)
         * @param {number} options.duration - Durée avant fermeture automatique en ms (défaut: 5000)
         * @returns {HTMLElement} L'élément de notification créé
         */
        show: function(type, title, message, options = {}) {
            return createNotification(type, title, message, options);
        },
        
        /**
         * Affiche une notification de succès
         * @param {string} title - Titre de la notification
         * @param {string} message - Message de la notification
         * @param {Object} options - Options supplémentaires
         * @returns {HTMLElement} L'élément de notification créé
         */
        success: function(title, message, options = {}) {
            return this.show('success', title, message, options);
        },
        
        /**
         * Affiche une notification d'erreur
         * @param {string} title - Titre de la notification
         * @param {string} message - Message de la notification
         * @param {Object} options - Options supplémentaires
         * @returns {HTMLElement} L'élément de notification créé
         */
        error: function(title, message, options = {}) {
            return this.show('error', title, message, options);
        },
        
        /**
         * Affiche une notification d'avertissement
         * @param {string} title - Titre de la notification
         * @param {string} message - Message de la notification
         * @param {Object} options - Options supplémentaires
         * @returns {HTMLElement} L'élément de notification créé
         */
        warning: function(title, message, options = {}) {
            return this.show('warning', title, message, options);
        },
        
        /**
         * Affiche une notification d'information
         * @param {string} title - Titre de la notification
         * @param {string} message - Message de la notification
         * @param {Object} options - Options supplémentaires
         * @returns {HTMLElement} L'élément de notification créé
         */
        info: function(title, message, options = {}) {
            return this.show('info', title, message, options);
        },
        
        /**
         * Ferme toutes les notifications
         */
        dismissAll: function() {
            const notifications = document.querySelectorAll('.notification');
            notifications.forEach(notification => {
                const dismissBtn = notification.querySelector('.notification-close');
                if (dismissBtn) {
                    dismissBtn.click();
                }
            });
        }
    };
})();

// Exposer la fonction globale
window.NotificationManager = Notification;
