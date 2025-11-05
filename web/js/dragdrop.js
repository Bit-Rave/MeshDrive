/**
 * Gestion du drag and drop
 */

// Gérer le drag and drop
function setupDragAndDrop() {
    const dragOverlay = document.getElementById('dragOverlay');
    let dragCounter = 0;

    // Empêcher le comportement par défaut du navigateur
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        document.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    // Afficher l'overlay lors du dragenter
    document.addEventListener('dragenter', (e) => {
        dragCounter++;
        if (e.dataTransfer.types.includes('Files')) {
            dragOverlay.classList.add('active');
        }
    });

    // Masquer l'overlay lors du dragleave
    document.addEventListener('dragleave', (e) => {
        dragCounter--;
        if (dragCounter === 0) {
            dragOverlay.classList.remove('active');
            dragTargetFolder = null;
            document.querySelectorAll('#fileList tr').forEach(row => {
                row.classList.remove('drag-over');
            });
        }
    });

    // Gérer le dragover pour détecter le dossier survolé
    document.addEventListener('dragover', (e) => {
        if (!e.dataTransfer.types.includes('Files')) return;
        
        const folderTarget = e.target.closest('tr[data-folder-path]');
        if (folderTarget) {
            const folderPath = folderTarget.dataset.folderPath;
            if (folderPath) {
                dragTargetFolder = folderPath;
                document.querySelectorAll('#fileList tr').forEach(row => {
                    row.classList.remove('drag-over');
                });
                folderTarget.classList.add('drag-over');
                return;
            }
        }
        
        const fileTarget = e.target.closest('tr[data-file-id]');
        const listTarget = e.target.closest('#fileList');
        if (fileTarget || listTarget) {
            dragTargetFolder = currentFolderPath;
            document.querySelectorAll('#fileList tr[data-folder-path]').forEach(row => {
                row.classList.remove('drag-over');
            });
            return;
        }
        
        dragTargetFolder = null;
        document.querySelectorAll('#fileList tr').forEach(row => {
            row.classList.remove('drag-over');
        });
    });

    // Gérer le drop
    document.addEventListener('drop', async (e) => {
        dragCounter = 0;
        dragOverlay.classList.remove('active');
        
        document.querySelectorAll('#fileList tr').forEach(row => {
            row.classList.remove('drag-over');
        });

        const files = Array.from(e.dataTransfer.files);
        if (files.length === 0) return;

        const targetFolder = dragTargetFolder || currentFolderPath;
        dragTargetFolder = null;

        try {
            await uploadFiles(files, targetFolder);
        } catch (error) {
            console.error('Erreur lors de l\'upload:', error);
            showModal('❌ Erreur', 'Erreur lors de l\'upload: ' + error.message);
        }
    });
}

/**
 * Demande le mot de passe utilisateur pour le chiffrement côté client
 * @returns {Promise<string>} Mot de passe utilisateur
 */
async function promptUserPassword() {
    // Vérifier si le mot de passe est déjà en session
    let password = getPasswordFromSession();
    if (password) {
        return password;
    }
    
    // Demander le mot de passe à l'utilisateur
    return new Promise((resolve, reject) => {
        // Créer un modal pour demander le mot de passe
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.display = 'flex';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 400px;">
                <div class="modal-title">🔐 Chiffrement Zero-Knowledge</div>
                <div class="modal-body">
                    <p>Pour activer le chiffrement côté client (zero-knowledge), veuillez entrer votre mot de passe :</p>
                    <input type="password" id="password-input" placeholder="Mot de passe" style="width: 100%; padding: 8px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px;">
                    <label style="display: flex; align-items: center; margin: 10px 0;">
                        <input type="checkbox" id="remember-password" style="margin-right: 8px;">
                        <span>Se souvenir du mot de passe pendant cette session</span>
                    </label>
                </div>
                <div class="modal-buttons">
                    <button class="btn-modal btn-cancel" onclick="this.closest('.modal').remove()">Annuler</button>
                    <button class="btn-modal btn-ok" id="confirm-password">Confirmer</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const passwordInput = modal.querySelector('#password-input');
        const rememberCheckbox = modal.querySelector('#remember-password');
        const confirmBtn = modal.querySelector('#confirm-password');
        const cancelBtn = modal.querySelector('.btn-cancel');
        
        // Focus sur l'input
        passwordInput.focus();
        
        // Gérer la confirmation
        const confirm = () => {
            const password = passwordInput.value.trim();
            if (!password) {
                alert('Veuillez entrer votre mot de passe');
                return;
            }
            
            // Stocker le mot de passe si demandé
            if (rememberCheckbox.checked) {
                savePasswordForSession(password);
            }
            
            modal.remove();
            resolve(password);
        };
        
        // Gérer l'annulation
        const cancel = () => {
            modal.remove();
            reject(new Error('Chiffrement annulé par l\'utilisateur'));
        };
        
        confirmBtn.onclick = confirm;
        cancelBtn.onclick = cancel;
        
        // Entrée pour confirmer
        passwordInput.onkeypress = (e) => {
            if (e.key === 'Enter') {
                confirm();
            }
        };
    });
}

/**
 * Upload de fichiers avec chiffrement côté client (Zero-Knowledge)
 */
async function uploadFiles(fileList, targetFolder = null) {
    const folderPath = targetFolder || currentFolderPath;
    
    try {
        const token = getToken();
        if (!token) {
            throw new Error('Vous devez être connecté pour uploader des fichiers');
        }
        
        // Obtenir le mot de passe utilisateur pour le chiffrement
        let userPassword;
        try {
            userPassword = await promptUserPassword();
        } catch (error) {
            if (error.message === 'Chiffrement annulé par l\'utilisateur') {
                return; // L'utilisateur a annulé
            }
            throw error;
        }
        
        // Afficher un indicateur de progression
        showLoading('Chiffrement des fichiers...');
        
        // Chiffrer tous les fichiers côté client
        const encryptedFiles = [];
        for (const file of Array.from(fileList)) {
            try {
                const encrypted = await window.clientCrypto.encryptFileWithPassword(file, userPassword);
                
                // Créer un nouveau fichier avec le contenu chiffré
                const encryptedFile = new File(
                    [encrypted.encryptedFile],
                    `${file.name}.enc`,
                    { type: 'application/octet-stream' }
                );
                
                encryptedFiles.push({
                    file: encryptedFile,
                    encryptedKey: encrypted.fileKey,
                    nonce: encrypted.nonce,
                    integrityHash: encrypted.integrityHash,
                    encryptedMetadata: encrypted.encryptedMetadata,
                    originalSize: file.size,
                    encryptedSize: encrypted.encryptedSize
                });
            } catch (error) {
                console.error(`Erreur lors du chiffrement de ${file.name}:`, error);
                throw new Error(`Erreur lors du chiffrement de ${file.name}: ${error.message}`);
            }
        }
        
        hideLoading();
        
        // Préparer FormData avec les fichiers chiffrés et les métadonnées
        const formData = new FormData();
        
        // Ajouter les fichiers chiffrés
        encryptedFiles.forEach((encrypted, index) => {
            formData.append('files', encrypted.file);
            
            // Ajouter les métadonnées de chiffrement
            formData.append(`file_key_${index}`, encrypted.encryptedKey);
            formData.append(`file_nonce_${index}`, encrypted.nonce);
            formData.append(`file_integrity_${index}`, encrypted.integrityHash);
            formData.append(`file_metadata_${index}`, encrypted.encryptedMetadata);
            formData.append(`file_original_size_${index}`, encrypted.originalSize.toString());
        });
        
        // Ajouter le token dans FormData comme solution de secours
        formData.append('token', token);
        
        // Indiquer que les fichiers sont déjà chiffrés côté client
        formData.append('client_encrypted', 'true');
        
        // Headers avec Authorization
        const headers = {
            'Authorization': `Bearer ${token}`
        };
        
        showLoading('Upload des fichiers chiffrés...');
        
        const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.upload}?folder_path=${encodeURIComponent(folderPath)}`;
        const response = await fetch(url, {
            method: 'POST',
            headers: headers,
            body: formData
        });

        hideLoading();

        if (!response.ok) {
            if (response.status === 401) {
                clearAuth();
                clearPasswordFromSession();
                window.location.href = '/login.html';
                throw new Error('Session expirée. Veuillez vous reconnecter.');
            }
            const error = await response.json().catch(() => ({ detail: 'Erreur inconnue' }));
            throw new Error(error.detail || `Erreur ${response.status}`);
        }

        const result = await response.json();
        
        // Afficher les erreurs s'il y en a
        if (result.errors > 0 && result.error_details && result.error_details.length > 0) {
            const errorMessages = result.error_details.map(e => `${e.filename}: ${e.error}`).join('\n');
            showModal('❌ Erreurs lors de l\'upload', errorMessages);
        }
        
        // Recharger la liste des fichiers
        await loadFiles();
    } catch (error) {
        console.error('Erreur lors de l\'upload:', error);
        hideLoading();
        throw error;
    }
}

/**
 * Modifier uploadFile pour utiliser uploadFiles
 */
function uploadFile() {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.style.display = 'none';
    
    input.onchange = async (e) => {
        const fileList = e.target.files;
        if (!fileList || fileList.length === 0) return;

        try {
            await uploadFiles(fileList);
        } catch (error) {
            console.error('Erreur lors de l\'upload:', error);
            showModal('❌ Erreur', 'Erreur lors de l\'upload: ' + error.message);
        } finally {
            document.body.removeChild(input);
        }
    };

    document.body.appendChild(input);
    input.click();
}
