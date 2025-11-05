/**
 * Interface utilisateur - Modales, menus contextuels, affichage
 */

// Modal simple
function showModal(title, body) {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalBody').textContent = body;
    document.getElementById('modal').classList.add('show');
}

function closeModal() {
    document.getElementById('modal').classList.remove('show');
}

function closeModalOnBackdrop(event) {
    if (event.target === document.getElementById('modal')) {
        closeModal();
    }
}

// Modal confirmation
function showConfirmModal(title, body, onConfirm) {
    document.getElementById('confirmTitle').textContent = title;
    document.getElementById('confirmBody').textContent = body;
    document.getElementById('confirmBtn').onclick = () => {
        closeConfirmModal();
        onConfirm();
    };
    document.getElementById('confirmModal').classList.add('show');
}

function closeConfirmModal() {
    document.getElementById('confirmModal').classList.remove('show');
}

function closeConfirmModalOnBackdrop(event) {
    if (event.target === document.getElementById('confirmModal')) {
        closeConfirmModal();
    }
}

// Menu contextuel pour les fichiers
function showContextMenu(e, fileId) {
    e.preventDefault();
    selectFile(fileId);
    const menu = document.getElementById('contextMenu');
    
    menu.innerHTML = `
        <div class="context-menu-item" onclick="showFileDetails()">📋 Détails</div>
        <div class="context-menu-item" onclick="downloadSelectedFile()">📥 Télécharger</div>
        <div class="context-menu-item" onclick="showMoveFileDialog()">📦 Déplacer</div>
        <div class="context-menu-separator"></div>
        <div class="context-menu-item" onclick="deleteFile()">🗑️ Supprimer</div>
    `;

    // Positionner le menu en tenant compte des bords de l'écran
    const menuWidth = 180;
    const menuHeight = 180;
    let x = e.pageX;
    let y = e.pageY;

    if (x + menuWidth > window.innerWidth) {
        x = window.innerWidth - menuWidth - 10;
    }
    if (y + menuHeight > window.innerHeight) {
        y = window.innerHeight - menuHeight - 10;
    }

    menu.style.left = x + 'px';
    menu.style.top = y + 'px';
    menu.classList.add('show');
}

// Menu contextuel pour les dossiers
function showFolderContextMenu(e, folderPath) {
    e.preventDefault();
    selectFolder(folderPath);
    const menu = document.getElementById('contextMenu');
    menu.innerHTML = `
        <div class="context-menu-item" onclick="openFolder('${folderPath}')">📂 Ouvrir</div>
        <div class="context-menu-item" onclick="downloadFolderAsZip('${folderPath}')">📦 Télécharger en ZIP</div>
        <div class="context-menu-separator"></div>
        <div class="context-menu-item" onclick="deleteFolder()">🗑️ Supprimer</div>
    `;
    menu.style.left = e.pageX + 'px';
    menu.style.top = e.pageY + 'px';
    menu.classList.add('show');
}

// Cacher le menu contextuel
document.addEventListener('click', () => {
    document.getElementById('contextMenu').classList.remove('show');
});

// Afficher l'état de chargement
function showLoading() {
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = `
        <tr>
            <td colspan="5">
                <div class="loading">
                    <div class="loading-spinner"></div>
                    <div>Chargement...</div>
                </div>
            </td>
        </tr>
    `;
}

// Masquer l'état de chargement
function hideLoading() {
    // Si updateTree n'a pas encore été appelé, réinitialiser la liste
    const fileList = document.getElementById('fileList');
    if (fileList && fileList.innerHTML.includes('Chargement...')) {
        // Si on est toujours en chargement, réinitialiser
        fileList.innerHTML = '';
    }
    // updateTree() sera appelé par la fonction qui utilise hideLoading()
}

// Afficher une erreur
function showError(message) {
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = `
        <tr>
            <td colspan="5">
                <div class="empty-state">
                    <div class="empty-state-icon">⚠️</div>
                    <div class="empty-state-text">${escapeHtml(message)}</div>
                </div>
            </td>
        </tr>
    `;
}

// Mettre à jour les statistiques
function updateStats() {
    const totalFiles = files.length;
    const totalFolders = folders.length;
    const totalSize = files.reduce((sum, f) => sum + f.file_size, 0);
    document.getElementById('stats').textContent =
        `📊 ${totalFiles} fichier(s) • 📁 ${totalFolders} dossier(s) • 💾 ${formatSize(totalSize)} au total`;
}

/**
 * Dialog pour déplacer un fichier
 */
async function showMoveFileDialog() {
    if (!selectedFileId) return;
    
    const file = files.find(f => f.file_id === selectedFileId);
    if (!file) return;

    try {
        // Récupérer tous les dossiers disponibles
        let allFolders = [];
        try {
            allFolders = await listAllFolders();
        } catch (error) {
            console.error('Erreur lors du chargement des dossiers:', error);
            try {
                const rootFolders = await listFolders("/");
                allFolders = rootFolders;
            } catch (e) {
                throw new Error('Impossible de charger les dossiers: ' + error.message);
            }
        }
        
        // S'assurer qu'on a au moins la racine
        if (!allFolders.some(f => f.folder_path === '/')) {
            allFolders.unshift({
                folder_id: 'root',
                folder_name: '/',
                folder_path: '/',
                parent_path: '',
                created_at: ''
            });
        }
        
        // Filtrer les dossiers valides et exclure le dossier actuel
        const validFolders = allFolders.filter(f => 
            f && 
            f.folder_path && 
            f.folder_name &&
            f.folder_path !== '/' &&
            f.folder_path !== file.folder_path
        );
        
        // Construire l'arbre de dossiers
        const folderTree = buildFolderTree(validFolders);
        let folderOptions = '<option value="/">📁 / (Racine)</option>';
        folderOptions += renderFolderTree(folderTree);
        
        // Créer le contenu de la modal
        const modalContent = `
            <div style="margin-bottom: 15px;">
                <label style="display: block; margin-bottom: 8px; color: #cdd6f4;">Déplacer "${escapeHtml(file.original_name)}" vers :</label>
                <select id="moveFolderSelect" style="width: 100%; padding: 8px; background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #45475a; border-radius: 5px; font-size: 14px;">
                    ${folderOptions}
                </select>
            </div>
        `;
        
        // Afficher la modal
        const modal = document.getElementById('modal');
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = document.getElementById('modalBody');
        const modalButtons = modal.querySelector('.modal-buttons');
        
        modalTitle.textContent = '📦 Déplacer le fichier';
        modalBody.innerHTML = modalContent;
        modalButtons.innerHTML = `
            <button class="btn-modal btn-cancel" onclick="closeModal()">Annuler</button>
            <button class="btn-modal btn-ok" onclick="executeMoveFile()">Déplacer</button>
        `;
        
        modal.classList.add('show');
        
    } catch (error) {
        console.error('Erreur lors du chargement des dossiers:', error);
        showModal('❌ Erreur', 'Impossible de charger les dossiers: ' + error.message);
    }
}

/**
 * Exécuter le déplacement d'un fichier
 */
async function executeMoveFile() {
    if (!selectedFileId) return;
    
    const select = document.getElementById('moveFolderSelect');
    if (!select) return;
    
    const newFolderPath = select.value;
    
    try {
        await moveFileAPI(selectedFileId, newFolderPath);
        closeModal();
        await loadFiles();
    } catch (error) {
        console.error('Erreur lors du déplacement:', error);
        showModal('❌ Erreur', 'Erreur lors du déplacement: ' + error.message);
    }
}

/**
 * Récupérer tous les dossiers
 */
async function listAllFolders() {
    try {
        const allFolders = await listAllFoldersAPI();
        
        // Valider et nettoyer les données
        const validFolders = allFolders.filter(f => 
            f && 
            f.folder_path && 
            f.folder_name && 
            typeof f.folder_path === 'string' &&
            typeof f.folder_name === 'string'
        );
        
        // Ajouter la racine si elle n'est pas déjà présente
        if (!validFolders.some(f => f.folder_path === '/')) {
            validFolders.unshift({
                folder_id: 'root',
                folder_name: '/',
                folder_path: '/',
                parent_path: '',
                created_at: ''
            });
        }
        
        return validFolders;
    } catch (error) {
        console.error('Erreur lors de la récupération des dossiers:', error);
        return [{
            folder_id: 'root',
            folder_name: '/',
            folder_path: '/',
            parent_path: '',
            created_at: ''
        }];
    }
}

/**
 * Mettre à jour le fil d'Ariane
 */
function updateBreadcrumb() {
    const currentPathEl = document.getElementById('currentPath');
    
    if (currentFolderPath === "/") {
        currentPathEl.innerHTML = '📁 /';
    } else {
        const parts = currentFolderPath.split('/').filter(p => p);
        let breadcrumbHtml = '<span onclick="loadFiles(\'/\')" style="cursor: pointer; color: #89b4fa;">📁 /</span>';
        
        let currentPath = "";
        parts.forEach((part, index) => {
            currentPath += "/" + part;
            breadcrumbHtml += ` / <span onclick="loadFiles('${currentPath}')" style="cursor: pointer; color: ${index === parts.length - 1 ? '#cdd6f4' : '#89b4fa'};">${escapeHtml(part)}</span>`;
        });
        
        currentPathEl.innerHTML = breadcrumbHtml;
    }
}
