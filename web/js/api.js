/**
 * Module pour les appels API FastAPI
 * Utilise les modules config.js et http.js pour centraliser la logique
 */

/**
 * Liste tous les fichiers chiffrés
 */
async function listFiles(folderPath = "/") {
    const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.files.list}?folder_path=${encodeURIComponent(folderPath)}`;
    return getRequest(url);
}

/**
 * Obtient les informations détaillées d'un fichier
 */
async function getFileInfo(fileId) {
    const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.files.get(fileId)}`;
    return getRequest(url);
}

/**
 * Chiffre et upload un fichier
 */
async function encryptFile(file, folderPath = "/") {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('folder_path', folderPath);

    const headers = getAuthHeaders(null); // null pour FormData (le navigateur définit Content-Type)
    
    const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.files.encrypt}`;
    const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData
    });
    
    return handleResponse(response);
}

/**
 * Déchiffre et télécharge un fichier
 * Détecte automatiquement si c'est un fichier chiffré côté client
 */
async function decryptFileAPI(fileId, originalName, fileMetadata = null) {
    // Vérifier d'abord si on sait déjà que c'est un fichier chiffré côté client
    // Pour éviter une requête inutile si on sait déjà que c'est un fichier chiffré serveur
    let isClientEncrypted = false;
    
    // Si on a les métadonnées du fichier, vérifier si c'est chiffré côté client
    if (fileMetadata && fileMetadata.client_encrypted === true) {
        isClientEncrypted = true;
    }
    
    // Si c'est un fichier chiffré côté client, récupérer les données et déchiffrer
    if (isClientEncrypted) {
        try {
            const response = await fetch(`${API_CONFIG.baseUrl}/api/client-decrypt/${fileId}`, {
                method: 'GET',
                headers: getAuthHeaders()
            });
            
            if (response.ok) {
                const clientData = await response.json();
                if (clientData && clientData.encrypted_file) {
                    return await decryptClientEncryptedFile(clientData, originalName);
                }
            } else {
                // Erreur inattendue pour un fichier chiffré côté client
                const errorData = await response.json().catch(() => ({ detail: `Erreur ${response.status}` }));
                throw new Error(errorData.detail || `Erreur ${response.status}`);
            }
        } catch (error) {
            console.error(`Erreur lors de la récupération des données chiffrées côté client: ${error.message}`);
            throw error;
        }
    } else {
        // Si on ne sait pas encore (pas de métadonnées), essayer l'endpoint client-decrypt
        // Si ça retourne 404/400, c'est un fichier chiffré serveur
        try {
            const response = await fetch(`${API_CONFIG.baseUrl}/api/client-decrypt/${fileId}`, {
                method: 'GET',
                headers: getAuthHeaders()
            });
            
            if (response.ok) {
                const clientData = await response.json();
                
                // Si c'est un fichier chiffré côté client, déchiffrer côté client
                if (clientData && clientData.encrypted_file) {
                    return await decryptClientEncryptedFile(clientData, originalName);
                }
            } else if (response.status === 404 || response.status === 400) {
                // C'est un fichier chiffré serveur, continuer avec le déchiffrement serveur normal
                // Ne pas logger pour éviter le spam dans la console
                isClientEncrypted = false;
            } else {
                // Autre erreur, la propager
                const errorData = await response.json().catch(() => ({ detail: `Erreur ${response.status}` }));
                throw new Error(errorData.detail || `Erreur ${response.status}`);
            }
        } catch (error) {
            // Si c'est une erreur réseau ou autre, vérifier si c'est 404/400
            const errorMessage = error.message || String(error) || '';
            if (errorMessage.includes('Not Found') || errorMessage.includes('404') || 
                errorMessage.includes('Erreur 404') || errorMessage.includes('400') ||
                errorMessage.includes('Erreur 400') || errorMessage.includes('n\'est pas chiffré côté client')) {
                // C'est un fichier chiffré serveur, continuer avec le déchiffrement serveur normal
                // Ne pas logger pour éviter le spam dans la console
                isClientEncrypted = false;
            } else {
                // C'est une autre erreur, la propager
                console.error(`Erreur lors de la récupération des données chiffrées: ${errorMessage}`);
                throw error;
            }
        }
    }
    
    // Si on a réussi à déchiffrer côté client, ne pas continuer
    if (isClientEncrypted) {
        return;
    }
    
    // Déchiffrement serveur normal - utiliser directement l'URL de téléchargement
    const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.files.decrypt(fileId)}?download=true`;
    // Utiliser downloadFileFromUrl de http.js (pas celle de files.js)
    return await downloadFileFromUrl(url, originalName || `file_${fileId}`);
}

/**
 * Déchiffre un fichier chiffré côté client
 */
async function decryptClientEncryptedFile(clientData, originalName) {
    // Obtenir le mot de passe utilisateur
    let userPassword = getPasswordFromSession();
    if (!userPassword) {
        // Demander le mot de passe (fonction définie dans dragdrop.js)
        if (typeof promptUserPassword === 'function') {
            userPassword = await promptUserPassword();
        } else {
            throw new Error('Impossible de déchiffrer le fichier: mot de passe requis. Veuillez recharger la page.');
        }
    }
    
    // Décoder le fichier chiffré
    const encryptedFileBlob = base64ToBlob(clientData.encrypted_file);
    
    // Déchiffrer le fichier
    const result = await window.clientCrypto.decryptFileWithPassword(
        encryptedFileBlob,
        clientData.encrypted_key,
        clientData.nonce,
        userPassword,
        clientData.integrity_hash
    );
    
    // Déchiffrer les métadonnées pour obtenir le nom original
    let finalName = originalName || `file_${clientData.file_id}`;
    if (clientData.encrypted_metadata) {
        try {
            const metadata = await window.clientCrypto.decryptMetadata(
                clientData.encrypted_metadata,
                userPassword
            );
            finalName = metadata.original_name || finalName;
        } catch (error) {
            console.warn('Impossible de déchiffrer les métadonnées:', error);
        }
    }
    
    // Télécharger le fichier déchiffré
    const url = window.URL.createObjectURL(result.decryptedFile);
    const a = document.createElement('a');
    a.href = url;
    a.download = finalName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    return { success: true, message: 'Fichier déchiffré et téléchargé avec succès' };
}

/**
 * Utilitaires
 */
function base64ToBlob(base64) {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return new Blob([bytes], { type: 'application/octet-stream' });
}

/**
 * Déplace un fichier vers un nouveau dossier
 */
async function moveFileAPI(fileId, newFolderPath) {
    const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.files.move(fileId)}`;
    return putRequest(url, { new_folder_path: newFolderPath });
}

/**
 * Supprime un fichier
 */
async function deleteFileAPI(fileId, deleteChunks = true) {
    const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.files.delete(fileId)}?delete_chunks=${deleteChunks}`;
    return deleteRequest(url);
}

/**
 * Vérifie l'état de l'API
 */
async function checkHealth() {
    const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.health}`;
    return getRequest(url);
}

/**
 * Crée un nouveau dossier
 */
async function createFolder(folderName, parentPath = "/") {
    const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.folders.create}`;
    return postRequest(url, {
        folder_name: folderName,
        parent_path: parentPath
    });
}

/**
 * Liste les dossiers dans un dossier parent
 */
async function listFolders(parentPath = "/") {
    const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.folders.list}?parent_path=${encodeURIComponent(parentPath)}`;
    return getRequest(url);
}

/**
 * Liste tous les dossiers du système
 */
async function listAllFoldersAPI() {
    const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.folders.listAll}`;
    return getRequest(url);
}

/**
 * Récupère le contenu d'un dossier (fichiers et sous-dossiers)
 */
async function getFolderContents(folderPath = "/") {
    const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.folders.contents}?folder_path=${encodeURIComponent(folderPath)}`;
    return getRequest(url);
}

/**
 * Supprime un dossier
 */
async function deleteFolderAPI(folderPath, recursive = false) {
    const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.folders.delete(folderPath)}?recursive=${recursive}`;
    return deleteRequest(url);
}

// Exposer toutes les fonctions API globalement
if (typeof window !== 'undefined') {
    window.getFolderContents = getFolderContents;
    window.listFiles = listFiles;
    window.getFileInfo = getFileInfo;
    window.encryptFile = encryptFile;
    window.decryptFileAPI = decryptFileAPI;
    window.moveFileAPI = moveFileAPI;
    window.deleteFileAPI = deleteFileAPI;
    window.createFolder = createFolder;
    window.listFolders = listFolders;
    window.listAllFoldersAPI = listAllFoldersAPI;
    window.deleteFolderAPI = deleteFolderAPI;
}
