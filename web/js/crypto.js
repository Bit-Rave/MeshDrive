/**
 * Module de chiffrement côté client pour architecture Zero-Knowledge
 * Utilise Web Crypto API pour chiffrer les fichiers avant l'envoi au serveur
 */

// Configuration
const AES_GCM_ALGORITHM = 'AES-GCM';
const KEY_SIZE = 256; // bits
const NONCE_SIZE = 12; // bytes pour AES-GCM
const PBKDF2_ITERATIONS = 100000;
const PBKDF2_HASH = 'SHA-256';

/**
 * Dérive une clé maître depuis le mot de passe utilisateur
 * @param {string} password - Mot de passe utilisateur
 * @param {Uint8Array} salt - Salt pour la dérivation
 * @returns {Promise<CryptoKey>} Clé maître dérivée
 */
async function deriveMasterKey(password, salt) {
    const encoder = new TextEncoder();
    const passwordKey = await crypto.subtle.importKey(
        'raw',
        encoder.encode(password),
        'PBKDF2',
        false,
        ['deriveKey']
    );

    const masterKey = await crypto.subtle.deriveKey(
        {
            name: 'PBKDF2',
            salt: salt,
            iterations: PBKDF2_ITERATIONS,
            hash: PBKDF2_HASH
        },
        passwordKey,
        {
            name: AES_GCM_ALGORITHM,
            length: KEY_SIZE
        },
        false,
        ['encrypt', 'decrypt']
    );

    return masterKey;
}

/**
 * Génère une clé AES-GCM aléatoire pour chiffrer un fichier
 * @returns {Promise<CryptoKey>} Clé de chiffrement
 */
async function generateFileKey() {
    return await crypto.subtle.generateKey(
        {
            name: AES_GCM_ALGORITHM,
            length: KEY_SIZE
        },
        true,
        ['encrypt', 'decrypt']
    );
}

/**
 * Génère un nonce aléatoire pour AES-GCM
 * @returns {Uint8Array} Nonce
 */
function generateNonce() {
    return crypto.getRandomValues(new Uint8Array(NONCE_SIZE));
}

/**
 * Chiffre un fichier avec AES-GCM
 * @param {File|Blob} file - Fichier à chiffrer
 * @param {CryptoKey} key - Clé de chiffrement
 * @param {Uint8Array} nonce - Nonce pour AES-GCM
 * @returns {Promise<Blob>} Fichier chiffré
 */
async function encryptFile(file, key, nonce) {
    const fileBuffer = await file.arrayBuffer();
    
    const encryptedBuffer = await crypto.subtle.encrypt(
        {
            name: AES_GCM_ALGORITHM,
            iv: nonce
        },
        key,
        fileBuffer
    );

    return new Blob([encryptedBuffer], { type: 'application/octet-stream' });
}

/**
 * Déchiffre un fichier avec AES-GCM
 * @param {Blob} encryptedBlob - Fichier chiffré
 * @param {CryptoKey} key - Clé de déchiffrement
 * @param {Uint8Array} nonce - Nonce utilisé pour le chiffrement
 * @returns {Promise<Blob>} Fichier déchiffré
 */
async function decryptFile(encryptedBlob, key, nonce) {
    const encryptedBuffer = await encryptedBlob.arrayBuffer();
    
    const decryptedBuffer = await crypto.subtle.decrypt(
        {
            name: AES_GCM_ALGORITHM,
            iv: nonce
        },
        key,
        encryptedBuffer
    );

    return new Blob([decryptedBuffer]);
}

/**
 * Exporte une clé en format JSON Web Key (JWK) puis en base64
 * @param {CryptoKey} key - Clé à exporter
 * @returns {Promise<string>} Clé exportée en base64
 */
async function exportKey(key) {
    const jwk = await crypto.subtle.exportKey('raw', key);
    return arrayBufferToBase64(jwk);
}

/**
 * Importe une clé depuis base64
 * @param {string} keyBase64 - Clé en base64
 * @returns {Promise<CryptoKey>} Clé importée
 */
async function importKey(keyBase64) {
    const keyBuffer = base64ToArrayBuffer(keyBase64);
    return await crypto.subtle.importKey(
        'raw',
        keyBuffer,
        {
            name: AES_GCM_ALGORITHM,
            length: KEY_SIZE
        },
        false,
        ['encrypt', 'decrypt']
    );
}

/**
 * Chiffre une clé de fichier avec le mot de passe utilisateur
 * @param {CryptoKey} fileKey - Clé de fichier à chiffrer
 * @param {string} userPassword - Mot de passe utilisateur
 * @returns {Promise<string>} Clé chiffrée en base64 (salt + nonce + clé chiffrée)
 */
async function encryptFileKey(fileKey, userPassword) {
    // Exporter la clé de fichier
    const fileKeyBase64 = await exportKey(fileKey);
    const fileKeyBuffer = base64ToArrayBuffer(fileKeyBase64);
    
    // Générer un salt
    const salt = crypto.getRandomValues(new Uint8Array(16));
    
    // Générer un nonce
    const nonce = crypto.getRandomValues(new Uint8Array(NONCE_SIZE));
    
    // Dériver la clé maître depuis le mot de passe
    const masterKey = await deriveMasterKey(userPassword, salt);
    
    // Chiffrer la clé de fichier avec la clé maître
    const encryptedKeyBuffer = await crypto.subtle.encrypt(
        {
            name: AES_GCM_ALGORITHM,
            iv: nonce
        },
        masterKey,
        fileKeyBuffer
    );
    
    // Retourner salt + nonce + clé chiffrée en base64
    const combined = new Uint8Array(salt.length + nonce.length + encryptedKeyBuffer.byteLength);
    combined.set(salt, 0);
    combined.set(nonce, salt.length);
    combined.set(new Uint8Array(encryptedKeyBuffer), salt.length + nonce.length);
    
    return arrayBufferToBase64(combined.buffer);
}

/**
 * Déchiffre une clé de fichier avec le mot de passe utilisateur
 * @param {string} encryptedKeyData - Clé chiffrée en base64 (salt + nonce + clé chiffrée)
 * @param {string} userPassword - Mot de passe utilisateur
 * @returns {Promise<CryptoKey>} Clé de fichier déchiffrée
 */
async function decryptFileKey(encryptedKeyData, userPassword) {
    // Décoder base64
    const combined = base64ToArrayBuffer(encryptedKeyData);
    const combinedArray = new Uint8Array(combined);
    
    // Extraire salt (16 premiers bytes), nonce (12 bytes suivants) et clé chiffrée
    const salt = combinedArray.slice(0, 16);
    const nonce = combinedArray.slice(16, 16 + NONCE_SIZE);
    const encryptedKeyBuffer = combinedArray.slice(16 + NONCE_SIZE).buffer;
    
    // Dériver la clé maître depuis le mot de passe
    const masterKey = await deriveMasterKey(userPassword, salt);
    
    // Déchiffrer la clé de fichier
    try {
        const decryptedKeyBuffer = await crypto.subtle.decrypt(
            {
                name: AES_GCM_ALGORITHM,
                iv: nonce
            },
            masterKey,
            encryptedKeyBuffer
        );
        
        // Importer la clé de fichier
        return await importKey(arrayBufferToBase64(decryptedKeyBuffer));
    } catch (error) {
        throw new Error('Impossible de déchiffrer la clé de fichier. Mot de passe incorrect ou données corrompues.');
    }
}

/**
 * Chiffre les métadonnées sensibles (nom de fichier, chemin)
 * @param {Object} metadata - Métadonnées à chiffrer
 * @param {string} userPassword - Mot de passe utilisateur
 * @returns {Promise<string>} Métadonnées chiffrées en base64 (salt + nonce + métadonnées chiffrées)
 */
async function encryptMetadata(metadata, userPassword) {
    // Convertir en JSON
    const metadataJson = JSON.stringify(metadata);
    const metadataBuffer = new TextEncoder().encode(metadataJson);
    
    // Générer un salt
    const salt = crypto.getRandomValues(new Uint8Array(16));
    
    // Dériver la clé maître depuis le mot de passe
    const masterKey = await deriveMasterKey(userPassword, salt);
    
    // Chiffrer les métadonnées
    const nonce = crypto.getRandomValues(new Uint8Array(NONCE_SIZE));
    const encryptedBuffer = await crypto.subtle.encrypt(
        {
            name: AES_GCM_ALGORITHM,
            iv: nonce
        },
        masterKey,
        metadataBuffer
    );
    
    // Retourner salt + nonce + métadonnées chiffrées en base64
    const combined = new Uint8Array(salt.length + nonce.length + encryptedBuffer.byteLength);
    combined.set(salt, 0);
    combined.set(nonce, salt.length);
    combined.set(new Uint8Array(encryptedBuffer), salt.length + nonce.length);
    
    return arrayBufferToBase64(combined.buffer);
}

/**
 * Déchiffre les métadonnées sensibles
 * @param {string} encryptedMetadataData - Métadonnées chiffrées en base64
 * @param {string} userPassword - Mot de passe utilisateur
 * @returns {Promise<Object>} Métadonnées déchiffrées
 */
async function decryptMetadata(encryptedMetadataData, userPassword) {
    // Décoder base64
    const combined = base64ToArrayBuffer(encryptedMetadataData);
    const combinedArray = new Uint8Array(combined);
    
    // Extraire salt, nonce et métadonnées chiffrées
    const salt = combinedArray.slice(0, 16);
    const nonce = combinedArray.slice(16, 16 + NONCE_SIZE);
    const encryptedBuffer = combinedArray.slice(16 + NONCE_SIZE).buffer;
    
    // Dériver la clé maître depuis le mot de passe
    const masterKey = await deriveMasterKey(userPassword, salt);
    
    // Déchiffrer les métadonnées
    try {
        const decryptedBuffer = await crypto.subtle.decrypt(
            {
                name: AES_GCM_ALGORITHM,
                iv: nonce
            },
            masterKey,
            encryptedBuffer
        );
        
        // Convertir en JSON
        const metadataJson = new TextDecoder().decode(decryptedBuffer);
        return JSON.parse(metadataJson);
    } catch (error) {
        throw new Error('Impossible de déchiffrer les métadonnées. Mot de passe incorrect ou données corrompues.');
    }
}

/**
 * Calcule un hash SHA-256 pour vérifier l'intégrité
 * @param {Blob|ArrayBuffer} data - Données à hasher
 * @returns {Promise<string>} Hash SHA-256 en hexadécimal
 */
async function calculateIntegrityHash(data) {
    let buffer;
    if (data instanceof Blob) {
        buffer = await data.arrayBuffer();
    } else {
        buffer = data;
    }
    
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Vérifie l'intégrité des données
 * @param {Blob|ArrayBuffer} data - Données à vérifier
 * @param {string} expectedHash - Hash attendu
 * @returns {Promise<boolean>} True si l'intégrité est vérifiée
 * @throws {Error} Si l'intégrité n'est pas vérifiée
 */
async function verifyIntegrity(data, expectedHash) {
    const calculatedHash = await calculateIntegrityHash(data);
    if (calculatedHash !== expectedHash) {
        throw new Error(
            `Intégrité des données compromise ! ` +
            `Hash calculé: ${calculatedHash.substring(0, 16)}..., ` +
            `Hash attendu: ${expectedHash.substring(0, 16)}...`
        );
    }
    return true;
}

/**
 * Utilitaires de conversion
 */
function arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
}

function base64ToArrayBuffer(base64) {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
}

/**
 * Chiffre un fichier complet avec le mot de passe utilisateur
 * @param {File} file - Fichier à chiffrer
 * @param {string} userPassword - Mot de passe utilisateur
 * @returns {Promise<{encryptedFile: Blob, fileKey: string, nonce: string, integrityHash: string, encryptedMetadata: string}>}
 */
async function encryptFileWithPassword(file, userPassword) {
    // 1. Générer une clé de fichier aléatoire
    const fileKey = await generateFileKey();
    
    // 2. Générer un nonce
    const nonce = generateNonce();
    
    // 3. Chiffrer le fichier
    const encryptedFile = await encryptFile(file, fileKey, nonce);
    
    // 4. Calculer le hash d'intégrité du fichier original
    const integrityHash = await calculateIntegrityHash(file);
    
    // 5. Chiffrer la clé de fichier avec le mot de passe
    const encryptedKey = await encryptFileKey(fileKey, userPassword);
    
    // 6. Chiffrer les métadonnées sensibles
    const metadata = {
        original_name: file.name,
        original_size: file.size,
        mime_type: file.type || 'application/octet-stream'
    };
    const encryptedMetadata = await encryptMetadata(metadata, userPassword);
    
    return {
        encryptedFile: encryptedFile,
        fileKey: encryptedKey,
        nonce: arrayBufferToBase64(nonce.buffer),
        integrityHash: integrityHash,
        encryptedMetadata: encryptedMetadata,
        encryptedSize: encryptedFile.size
    };
}

/**
 * Déchiffre un fichier avec le mot de passe utilisateur
 * @param {Blob} encryptedFile - Fichier chiffré
 * @param {string} encryptedKeyData - Clé chiffrée en base64
 * @param {string} nonceBase64 - Nonce en base64
 * @param {string} userPassword - Mot de passe utilisateur
 * @param {string} expectedHash - Hash d'intégrité attendu (optionnel)
 * @returns {Promise<{decryptedFile: Blob, metadata: Object}>}
 */
async function decryptFileWithPassword(encryptedFile, encryptedKeyData, nonceBase64, userPassword, expectedHash = null) {
    // 1. Déchiffrer la clé de fichier
    const fileKey = await decryptFileKey(encryptedKeyData, userPassword);
    
    // 2. Décoder le nonce
    const nonce = new Uint8Array(base64ToArrayBuffer(nonceBase64));
    
    // 3. Déchiffrer le fichier
    const decryptedFile = await decryptFile(encryptedFile, fileKey, nonce);
    
    // 4. Vérifier l'intégrité si fournie
    if (expectedHash) {
        await verifyIntegrity(decryptedFile, expectedHash);
    }
    
    return {
        decryptedFile: decryptedFile
    };
}

// Exporter les fonctions pour utilisation globale
window.clientCrypto = {
    encryptFileWithPassword,
    decryptFileWithPassword,
    encryptMetadata,
    decryptMetadata,
    calculateIntegrityHash,
    verifyIntegrity,
    encryptFileKey,
    decryptFileKey,
    generateFileKey,
    generateNonce,
    encryptFile,
    decryptFile
};

