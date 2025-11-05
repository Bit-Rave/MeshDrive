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
 */
async function decryptFileAPI(fileId, originalName) {
    const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.files.decrypt(fileId)}?download=true`;
    return downloadFile(url, originalName || `file_${fileId}`);
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
