/**
 * Initialisation de l'application
 */

// Initialisation
document.addEventListener('DOMContentLoaded', async () => {
    // Vérifier l'authentification avant d'initialiser
    if (typeof checkAuth === 'function') {
        try {
            const isAuth = await checkAuth();
            if (!isAuth) {
                // Éviter les redirections multiples
                if (window.location.pathname !== '/login.html') {
                    window.location.href = '/login.html';
                }
                return;
            }
        } catch (error) {
            console.error('Erreur lors de la vérification de l\'authentification:', error);
            // En cas d'erreur, rediriger vers login seulement si on n'est pas déjà sur login
            if (window.location.pathname !== '/login.html') {
                window.location.href = '/login.html';
            }
            return;
        }
    }
    
    navigationHistory.push("/");
    historyIndex = 0;
    updateBreadcrumb(); // Afficher le chemin au démarrage
    updateNavigationButtons(); // Mettre à jour les boutons de navigation
    loadFiles();
    setupDragAndDrop();

    // Recharger au redimensionnement pour adapter l'affichage
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            updateTree();
        }, 250);
    });

    // Support tactile pour mobile
    let touchStartX = 0;
    let touchStartY = 0;

    document.addEventListener('touchstart', (e) => {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
    });

    document.addEventListener('touchend', (e) => {
        const touchEndX = e.changedTouches[0].clientX;
        const touchEndY = e.changedTouches[0].clientY;
        const diffX = touchStartX - touchEndX;
        const diffY = touchStartY - touchEndY;

        // Swipe horizontal pour actualiser
        if (Math.abs(diffX) > 100 && Math.abs(diffY) < 50) {
            if (diffX < 0) {
                loadFiles();
            }
        }
    });

    // Fermer les modaux avec la touche Échap
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
            closeConfirmModal();
            document.getElementById('contextMenu').classList.remove('show');
        }
    });
});

