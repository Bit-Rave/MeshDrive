/**
 * Module HTTP pour les requêtes API
 * Centralise la logique de fetch et la gestion des erreurs
 */

/**
 * Gère les erreurs HTTP de manière centralisée
 */
async function handleResponse(response) {
    if (!response.ok) {
        // Si erreur 401 (non autorisé), ne pas rediriger automatiquement
        // Laisser la fonction appelante gérer la redirection
        // Cela évite les boucles de redirection lors de checkAuth()
        if (response.status === 401) {
            if (typeof clearAuth === 'function') {
                clearAuth();
            }
            const error = await response.json().catch(() => ({ detail: 'Session expirée. Veuillez vous reconnecter.' }));
            throw new Error(error.detail || 'Session expirée. Veuillez vous reconnecter.');
        }
        const error = await response.json().catch(() => ({ detail: 'Erreur inconnue' }));
        throw new Error(error.detail || `Erreur ${response.status}`);
    }
    return response.json();
}

/**
 * Récupère le token depuis le localStorage (fonction helper pour éviter la dépendance circulaire)
 */
function _getTokenFromStorage() {
    if (typeof STORAGE_KEYS !== 'undefined' && STORAGE_KEYS && STORAGE_KEYS.token) {
        return localStorage.getItem(STORAGE_KEYS.token);
    }
    // Fallback si STORAGE_KEYS n'est pas encore défini
    return localStorage.getItem('meshdrive_token');
}

/**
 * Récupère les headers avec authentification pour les requêtes API
 */
function getAuthHeaders(contentType = 'application/json') {
    const token = typeof getToken === 'function' ? getToken() : _getTokenFromStorage();
    const headers = {};
    
    if (contentType) {
        headers['Content-Type'] = contentType;
    }
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    return headers;
}

/**
 * Effectue une requête GET
 */
async function getRequest(url, options = {}) {
    const response = await fetch(url, {
        method: 'GET',
        headers: getAuthHeaders(options.contentType),
        ...options
    });
    return handleResponse(response);
}

/**
 * Effectue une requête POST
 */
async function postRequest(url, body, options = {}) {
    const headers = options.headers || getAuthHeaders();
    
    const response = await fetch(url, {
        method: 'POST',
        headers,
        body: body instanceof FormData ? body : JSON.stringify(body),
        ...options
    });
    
    return handleResponse(response);
}

/**
 * Effectue une requête PUT
 */
async function putRequest(url, body, options = {}) {
    const response = await fetch(url, {
        method: 'PUT',
        headers: options.headers || getAuthHeaders(),
        body: JSON.stringify(body),
        ...options
    });
    
    return handleResponse(response);
}

/**
 * Effectue une requête DELETE
 */
async function deleteRequest(url, options = {}) {
    const response = await fetch(url, {
        method: 'DELETE',
        headers: getAuthHeaders(),
        ...options
    });
    
    return handleResponse(response);
}

/**
 * Télécharge un fichier depuis une URL
 */
async function downloadFileFromUrl(url, filename, options = {}) {
    const headers = options.headers || getAuthHeaders();
    
    const response = await fetch(url, {
        method: 'GET',
        headers,
        ...options
    });

    if (!response.ok) {
        if (response.status === 401) {
            if (typeof clearAuth === 'function') {
                clearAuth();
            }
            window.location.href = '/login.html';
            throw new Error('Session expirée. Veuillez vous reconnecter.');
        }
        const error = await response.json().catch(() => ({ detail: 'Erreur inconnue' }));
        throw new Error(error.detail || `Erreur ${response.status}`);
    }

    // Récupérer le blob
    const blob = await response.blob();
    
    // Récupérer le nom du fichier depuis les headers si disponible
    const contentDisposition = response.headers.get('content-disposition');
    let finalFilename = filename || 'download';
    if (contentDisposition) {
        const matches = /filename="?([^"]+)"?/.exec(contentDisposition);
        if (matches) {
            finalFilename = matches[1];
        }
    }
    
    // Créer un lien de téléchargement
    const urlObject = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = urlObject;
    a.download = finalFilename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(urlObject);

    return { success: true, message: 'Fichier téléchargé avec succès' };
}

// Exposer les fonctions globalement
if (typeof window !== 'undefined') {
    window.handleResponse = handleResponse;
    window.getAuthHeaders = getAuthHeaders;
    window.getRequest = getRequest;
    window.postRequest = postRequest;
    window.putRequest = putRequest;
    window.deleteRequest = deleteRequest;
    window.downloadFileFromUrl = downloadFileFromUrl;
    // Alias pour compatibilité
    window.downloadFile = downloadFileFromUrl;
}

