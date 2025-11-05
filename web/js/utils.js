/**
 * Fonctions utilitaires
 */

/**
 * Échapper le HTML pour éviter les injections XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Formater la taille de fichier en unités lisibles
 */
function formatSize(size) {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    return `${size.toFixed(2)} ${units[unitIndex]}`;
}

/**
 * Formater la date en format français
 */
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

/**
 * Construire un arbre de dossiers basé sur les relations parent-enfant
 */
function buildFolderTree(folders) {
    const folderMap = new Map();
    const rootFolders = [];
    
    // Créer une map de tous les dossiers par leur chemin
    folders.forEach(folder => {
        folderMap.set(folder.folder_path, {
            ...folder,
            children: []
        });
    });
    
    // Construire l'arbre en reliant les enfants aux parents
    folders.forEach(folder => {
        const folderNode = folderMap.get(folder.folder_path);
        if (!folderNode) return;
        
        if (folder.parent_path === '/' || !folder.parent_path) {
            rootFolders.push(folderNode);
        } else {
            const parent = folderMap.get(folder.parent_path);
            if (parent) {
                parent.children.push(folderNode);
            } else {
                rootFolders.push(folderNode);
            }
        }
    });
    
    // Trier récursivement
    function sortTree(node) {
        if (node.children && node.children.length > 0) {
            node.children.sort((a, b) => a.folder_name.localeCompare(b.folder_name));
            node.children.forEach(child => sortTree(child));
        }
    }
    
    rootFolders.forEach(root => sortTree(root));
    rootFolders.sort((a, b) => a.folder_name.localeCompare(b.folder_name));
    
    return rootFolders;
}

/**
 * Afficher l'arbre de dossiers de manière récursive
 */
function renderFolderTree(tree, indent = 0) {
    let html = '';
    tree.forEach(node => {
        const indentStr = '    '.repeat(indent);
        const displayPath = node.folder_path === '/' ? '/' : node.folder_path + '/';
        html += `<option value="${escapeHtml(node.folder_path)}">${indentStr}📁 ${escapeHtml(displayPath)}</option>`;
        
        if (node.children && node.children.length > 0) {
            html += renderFolderTree(node.children, indent + 1);
        }
    });
    return html;
}

// Exposer les fonctions utilitaires globalement
if (typeof window !== 'undefined') {
    window.escapeHtml = escapeHtml;
    window.formatSize = formatSize;
    window.formatDate = formatDate;
    window.buildFolderTree = buildFolderTree;
    window.renderFolderTree = renderFolderTree;
}
