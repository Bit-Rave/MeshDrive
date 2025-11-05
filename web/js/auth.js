/**
 * Module d'authentification
 * Gère le login, register, et le stockage du token JWT
 */

/**
 * Stocke le token JWT dans le localStorage
 */
function saveToken(token) {
    localStorage.setItem(STORAGE_KEYS.token, token);
}

/**
 * Récupère le token JWT depuis le localStorage
 */
function getToken() {
    return localStorage.getItem(STORAGE_KEYS.token);
}

/**
 * Stocke les informations utilisateur dans le localStorage
 */
function saveUser(user) {
    localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(user));
}

/**
 * Récupère les informations utilisateur depuis le localStorage
 */
function getUser() {
    const userJson = localStorage.getItem(STORAGE_KEYS.user);
    return userJson ? JSON.parse(userJson) : null;
}

/**
 * Supprime le token et les informations utilisateur
 */
function clearAuth() {
    localStorage.removeItem(STORAGE_KEYS.token);
    localStorage.removeItem(STORAGE_KEYS.user);
}

/**
 * Vérifie si l'utilisateur est connecté
 */
function isAuthenticated() {
    return getToken() !== null;
}

/**
 * Enregistre un nouvel utilisateur
 */
async function register(username, email, password) {
    const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.auth.register}`;
    const response = await postRequest(url, {
        username: username,
        email: email,
        password: password
    });

    // Après l'enregistrement, connecter automatiquement l'utilisateur
    return await login(username, password);
}

/**
 * Connecte un utilisateur
 */
async function login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.auth.login}`;
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Identifiants incorrects');
    }

    const data = await response.json();
    saveToken(data.access_token);
    
    // Récupérer les informations de l'utilisateur
    const userUrl = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.auth.me}`;
    try {
        const user = await getRequest(userUrl);
        saveUser(user);
    } catch (error) {
        // Si l'erreur est 401, on continue quand même (le token est valide)
        console.warn('Impossible de récupérer les infos utilisateur:', error);
    }
    
    return data;
}

/**
 * Déconnecte l'utilisateur
 */
function logout() {
    clearAuth();
    window.location.href = '/';
}

/**
 * Vérifie si le token est valide et récupère les infos utilisateur
 */
async function checkAuth() {
    const token = getToken();
    if (!token) {
        return false;
    }

    try {
        const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.auth.me}`;
        const user = await getRequest(url);
        saveUser(user);
        return true;
    } catch (error) {
        console.error('Erreur lors de la vérification de l\'authentification:', error);
        clearAuth();
        return false;
    }
}
