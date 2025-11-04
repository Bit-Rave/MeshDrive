/**
 * Gestion des dossiers
 */

// Ouvrir un dossier
function openFolder(folderPath) {
    // Ne pas ajouter à l'historique ici, loadFiles le fera
    loadFiles(folderPath);
}

// Créer un nouveau dossier
async function createNewFolder() {
    const folderName = prompt('Nom du nouveau dossier:');
    if (!folderName || !folderName.trim()) {
        return;
    }

    try {
        await createFolder(folderName.trim(), currentFolderPath);
        
        // Recharger la liste
        await loadFiles();
    } catch (error) {
        console.error('Erreur lors de la création du dossier:', error);
        showModal('❌ Erreur', 'Erreur lors de la création du dossier: ' + error.message);
    }
}

// Supprimer un dossier
async function deleteFolder() {
    if (!selectedFolderPath) return;
    
    const folder = folders.find(f => f.folder_path === selectedFolderPath);
    if (!folder) return;

    showConfirmModal(
        '⚠️ Confirmation',
        `Supprimer définitivement le dossier?\n\n${folder.folder_name}\n\n(Le contenu sera également supprimé)`,
        async () => {
            try {
                const folderPathToDelete = selectedFolderPath;
                await deleteFolderAPI(folderPathToDelete, true);
                // Nettoyer l'historique de navigation
                removePathFromHistory(folderPathToDelete);
                selectedFolderPath = null;
                await loadFiles();
            } catch (error) {
                console.error('Erreur lors de la suppression:', error);
                showModal('❌ Erreur', 'Erreur lors de la suppression: ' + error.message);
            }
        }
    );
}

// Télécharger un dossier en ZIP
async function downloadFolderAsZip(folderPath) {
    try {
        const API_BASE_URL = 'http://localhost:8000';
        const response = await fetch(`${API_BASE_URL}/download-folder/${encodeURIComponent(folderPath)}`, {
            method: 'GET'
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Erreur inconnue' }));
            throw new Error(error.detail || `Erreur ${response.status}`);
        }

        // Récupérer le blob
        const blob = await response.blob();
        
        // Récupérer le nom du fichier depuis les headers
        const contentDisposition = response.headers.get('content-disposition');
        let filename = 'folder.zip';
        if (contentDisposition) {
            const matches = /filename="?([^"]+)"?/.exec(contentDisposition);
            if (matches) {
                filename = matches[1];
            }
        }
        
        // Créer un lien de téléchargement
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Erreur lors du téléchargement du dossier:', error);
        showModal('❌ Erreur', 'Erreur lors du téléchargement du dossier: ' + error.message);
    }
}

