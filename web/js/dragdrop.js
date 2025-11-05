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
 * Upload de fichiers (utilisé pour drag and drop et upload de dossier)
 */
async function uploadFiles(fileList, targetFolder = null) {
    const folderPath = targetFolder || currentFolderPath;
    const formData = new FormData();
    
    // Ajouter tous les fichiers
    Array.from(fileList).forEach(file => {
        formData.append('files', file);
    });

    try {
        const token = getToken();
        if (!token) {
            throw new Error('Vous devez être connecté pour uploader des fichiers');
        }
        
        // Ajouter le token dans FormData comme solution de secours
        formData.append('token', token);
        
        // Headers avec Authorization
        const headers = {
            'Authorization': `Bearer ${token}`
        };
        
        const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.upload}?folder_path=${encodeURIComponent(folderPath)}`;
        const response = await fetch(url, {
            method: 'POST',
            headers: headers,
            body: formData
        });

        if (!response.ok) {
            if (response.status === 401) {
                clearAuth();
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
