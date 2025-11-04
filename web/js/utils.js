/**
 * Fonctions utilitaires
 */

// Échapper le HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Formater la taille
function formatSize(size) {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    return `${size.toFixed(2)} ${units[unitIndex]}`;
}

// Formater la date
function formatDate(dateStr) {
    if (!dateStr) return 'Inconnue';
    try {
        const date = new Date(dateStr);
        const isMobile = window.innerWidth <= 768;
        return date.toLocaleString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: isMobile ? '2-digit' : 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return dateStr.substring(0, 19);
    }
}

