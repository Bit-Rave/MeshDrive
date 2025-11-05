/**
 * Configuration centralisée de l'application
 */

// Configuration de l'API
const API_CONFIG = {
    baseUrl: window.location.origin,
    endpoints: {
        auth: {
            register: '/auth/register',
            login: '/auth/login',
            me: '/auth/me'
        },
        files: {
            list: '/api/files',
            get: (fileId) => `/api/files/${fileId}`,
            encrypt: '/api/encrypt',
            decrypt: (fileId) => `/api/decrypt/${fileId}`,
            move: (fileId) => `/api/files/${fileId}/move`,
            delete: (fileId) => `/api/files/${fileId}`
        },
        folders: {
            list: '/api/folders',
            listAll: '/api/folders-all',
            get: (folderPath) => `/api/folders/${encodeURIComponent(folderPath)}`,
            create: '/api/folders',
            delete: (folderPath) => `/api/folders/${encodeURIComponent(folderPath)}`,
            contents: '/api/folder-contents',
            download: (folderPath) => `/api/download-folder/${encodeURIComponent(folderPath)}`
        },
        upload: '/encrypt-folder',
        health: '/health'
    }
};

// Constantes de stockage
const STORAGE_KEYS = {
    token: 'meshdrive_token',
    user: 'meshdrive_user'
};

// Exposer la configuration globalement
if (typeof window !== 'undefined') {
    window.API_CONFIG = API_CONFIG;
    window.STORAGE_KEYS = STORAGE_KEYS;
    window.API_BASE_URL = API_CONFIG.baseUrl; // Pour compatibilité
}

