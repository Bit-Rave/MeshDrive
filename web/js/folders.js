/**
 * Gestion des dossiers
 */

/**
 * Ouvrir un dossier
 */
function openFolder(folderPath) {
    loadFiles(folderPath);
}

/**
 * Créer un nouveau dossier
 */
async function createNewFolder() {
    const folderName = prompt('Nom du nouveau dossier:');
    if (!folderName || !folderName.trim()) {
        return;
    }

    try {
        await createFolder(folderName.trim(), currentFolderPath);
        await loadFiles();
    } catch (error) {
        console.error('Erreur lors de la création du dossier:', error);
        showModal('❌ Erreur', 'Erreur lors de la création du dossier: ' + error.message);
    }
}

/**
 * Supprimer un dossier
 */
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

/**
 * Télécharger un dossier en ZIP
 */
async function downloadFolderAsZip(folderPath) {
    try {
        const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.folders.download(folderPath)}`;
        await downloadFile(url, 'folder.zip');
    } catch (error) {
        console.error('Erreur lors du téléchargement du dossier:', error);
        showModal('❌ Erreur', 'Erreur lors du téléchargement du dossier: ' + error.message);
    }
}
