/**
 * Module pour les appels API FastAPI
 */

const API_BASE_URL = 'http://localhost:8000';

/**
 * Gère les erreurs HTTP
 */
async function handleResponse(response) {
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Erreur inconnue' }));
        throw new Error(error.detail || `Erreur ${response.status}`);
    }
    return response.json();
}

/**
 * Liste tous les fichiers chiffrés
 */
async function listFiles() {
    try {
        const response = await fetch(`${API_BASE_URL}/files`);
        return await handleResponse(response);
    } catch (error) {
        console.error('Erreur lors de la récupération des fichiers:', error);
        throw error;
    }
}

/**
 * Obtient les informations détaillées d'un fichier
 */
async function getFileInfo(fileId) {
    try {
        const response = await fetch(`${API_BASE_URL}/files/${fileId}`);
        return await handleResponse(response);
    } catch (error) {
        console.error('Erreur lors de la récupération des infos:', error);
        throw error;
    }
}

/**
 * Chiffre et upload un fichier
 */
async function encryptFile(file) {
    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/encrypt`, {
            method: 'POST',
            body: formData
        });

        return await handleResponse(response);
    } catch (error) {
        console.error('Erreur lors du chiffrement:', error);
        throw error;
    }
}

/**
 * Déchiffre et télécharge un fichier
 */
async function decryptFileAPI(fileId, originalName) {
    try {
        const response = await fetch(`${API_BASE_URL}/decrypt/${fileId}?download=true`, {
            method: 'GET'
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Erreur inconnue' }));
            throw new Error(error.detail || `Erreur ${response.status}`);
        }

        // Récupérer le blob
        const blob = await response.blob();
        
        // Créer un lien de téléchargement
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = originalName || `file_${fileId}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        return { success: true, message: 'Fichier téléchargé avec succès' };
    } catch (error) {
        console.error('Erreur lors du déchiffrement:', error);
        throw error;
    }
}

/**
 * Supprime un fichier
 */
async function moveFileAPI(fileId, newFolderPath) {
    const API_BASE_URL = 'http://localhost:8000';
    const response = await fetch(`${API_BASE_URL}/files/${fileId}/move`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            new_folder_path: newFolderPath
        })
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Erreur inconnue' }));
        throw new Error(error.detail || `Erreur ${response.status}`);
    }

    return await response.json();
}

async function deleteFileAPI(fileId, deleteChunks = true) {
    try {
        const response = await fetch(`${API_BASE_URL}/files/${fileId}?delete_chunks=${deleteChunks}`, {
            method: 'DELETE'
        });

        return await handleResponse(response);
    } catch (error) {
        console.error('Erreur lors de la suppression:', error);
        throw error;
    }
}

/**
 * Vérifie l'état de l'API
 */
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        return await handleResponse(response);
    } catch (error) {
        console.error('L\'API n\'est pas accessible:', error);
        throw error;
    }
}

/**
 * Crée un nouveau dossier
 */
async function createFolder(folderName, parentPath = "/") {
    try {
        const response = await fetch(`${API_BASE_URL}/folders`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                folder_name: folderName,
                parent_path: parentPath
            })
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('Erreur lors de la création du dossier:', error);
        throw error;
    }
}

/**
 * Liste les dossiers dans un dossier parent
 */
async function listFolders(parentPath = "/") {
    try {
        const response = await fetch(`${API_BASE_URL}/folders?parent_path=${encodeURIComponent(parentPath)}`);
        return await handleResponse(response);
    } catch (error) {
        console.error('Erreur lors de la récupération des dossiers:', error);
        throw error;
    }
}

/**
 * Liste tous les dossiers du système
 */
async function listAllFoldersAPI() {
    try {
        const response = await fetch(`${API_BASE_URL}/folders-all`);
        return await handleResponse(response);
    } catch (error) {
        console.error('Erreur lors de la récupération de tous les dossiers:', error);
        throw error;
    }
}

/**
 * Récupère le contenu d'un dossier (fichiers et sous-dossiers)
 */
async function getFolderContents(folderPath = "/") {
    try {
        const response = await fetch(`${API_BASE_URL}/folder-contents?folder_path=${encodeURIComponent(folderPath)}`);
        return await handleResponse(response);
    } catch (error) {
        console.error('Erreur lors de la récupération du contenu:', error);
        throw error;
    }
}

/**
 * Supprime un dossier
 */
async function deleteFolderAPI(folderPath, recursive = false) {
    try {
        const response = await fetch(`${API_BASE_URL}/folders/${encodeURIComponent(folderPath)}?recursive=${recursive}`, {
            method: 'DELETE'
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('Erreur lors de la suppression du dossier:', error);
        throw error;
    }
}

