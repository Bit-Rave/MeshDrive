/**
 * Gestion des fichiers
 */

// Charger les fichiers et dossiers depuis l'API
async function loadFiles(folderPath = null) {
    if (isLoading) return;
    
    if (folderPath !== null) {
        if (folderPath !== currentFolderPath && !isNavigatingHistory) {
            addToHistory(folderPath);
        }
        currentFolderPath = folderPath;
    }
    
    isLoading = true;
    showLoading();

    try {
        // Charger le contenu du dossier (fichiers et dossiers)
        const contents = await getFolderContents(currentFolderPath);
        files = contents.files || [];
        folders = contents.folders || [];
        
        const sortBy = document.getElementById('sortSelect').value;

        // Tri des fichiers
        if (sortBy === 'date') {
            files.sort((a, b) => new Date(b.upload_date) - new Date(a.upload_date));
        } else if (sortBy === 'name') {
            files.sort((a, b) => a.original_name.toLowerCase().localeCompare(b.original_name.toLowerCase()));
        } else if (sortBy === 'size') {
            files.sort((a, b) => b.file_size - a.file_size);
        }

        // Tri des dossiers
        folders.sort((a, b) => a.folder_name.toLowerCase().localeCompare(b.folder_name.toLowerCase()));

        updateTree();
        updateStats();
        updateBreadcrumb();
        updateNavigationButtons();
    } catch (error) {
        console.error('Erreur lors du chargement des fichiers:', error);
        showError('Erreur lors du chargement des fichiers: ' + error.message);
    } finally {
        isLoading = false;
        hideLoading();
    }
}

// Mettre à jour le tableau
function updateTree() {
    const fileList = document.getElementById('fileList');
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    fileList.innerHTML = '';

    let filteredFiles = files.filter(file => {
        return !searchTerm || file.original_name.toLowerCase().includes(searchTerm);
    });

    let filteredFolders = folders.filter(folder => {
        return !searchTerm || folder.folder_name.toLowerCase().includes(searchTerm);
    });

    // Afficher les dossiers d'abord
    filteredFolders.forEach(folder => {
        const row = document.createElement('tr');
        row.dataset.folderPath = folder.folder_path;
        row.onclick = (e) => {
            if (e.target.type !== 'checkbox') {
                selectFolder(folder.folder_path);
            }
        };
        row.ondblclick = () => openFolder(folder.folder_path);
        row.oncontextmenu = (e) => showFolderContextMenu(e, folder.folder_path);

        const folderCheckboxId = `checkbox_folder_${folder.folder_path}`;
        row.innerHTML = `
            <td class="col-checkbox"><input type="checkbox" id="${folderCheckboxId}" data-folder-path="${folder.folder_path}" onchange="updateSelectedFiles()"></td>
            <td class="col-name">📁 ${escapeHtml(folder.folder_name)}</td>
            <td class="col-size">—</td>
            <td class="col-date">${formatDate(folder.created_at)}</td>
            <td class="col-id">Dossier</td>
        `;

        fileList.appendChild(row);
    });

    // Puis les fichiers
    filteredFiles.forEach(file => {
        const row = document.createElement('tr');
        row.dataset.fileId = file.file_id;
        const checkboxId = `checkbox_${file.file_id}`;
        row.onclick = (e) => {
            if (e.target.type !== 'checkbox') {
                selectFile(file.file_id);
            }
        };
        row.ondblclick = () => showFileDetails();
        row.oncontextmenu = (e) => showContextMenu(e, file.file_id);

        row.innerHTML = `
            <td class="col-checkbox"><input type="checkbox" id="${checkboxId}" data-file-id="${file.file_id}" onchange="updateSelectedFiles()"></td>
            <td class="col-name">📄 ${escapeHtml(file.original_name)}</td>
            <td class="col-size">${formatSize(file.file_size)}</td>
            <td class="col-date">${formatDate(file.upload_date)}</td>
            <td class="col-id">${file.file_id.substring(0, 20)}...</td>
        `;

        fileList.appendChild(row);
    });

    if (filteredFolders.length === 0 && filteredFiles.length === 0) {
        fileList.innerHTML = `
            <tr>
                <td colspan="5">
                    <div class="empty-state">
                        <div class="empty-state-icon">📁</div>
                        <div class="empty-state-text">Aucun élément trouvé</div>
                    </div>
                </td>
            </tr>
        `;
    }
    
    updateSelectedFiles();
}

// Sélectionner un fichier
function selectFile(fileId) {
    document.querySelectorAll('#fileList tr').forEach(row => {
        row.classList.remove('selected');
    });
    const row = document.querySelector(`tr[data-file-id="${fileId}"]`);
    if (row) {
        row.classList.add('selected');
        selectedFileId = fileId;
        selectedFolderPath = null;
    }
}

// Sélectionner un dossier
function selectFolder(folderPath) {
    document.querySelectorAll('#fileList tr').forEach(row => {
        row.classList.remove('selected');
    });
    const row = document.querySelector(`tr[data-folder-path="${folderPath}"]`);
    if (row) {
        row.classList.add('selected');
        selectedFolderPath = folderPath;
        selectedFileId = null;
    }
}

// Filtrer les fichiers
function filterFiles() {
    updateTree();
}

// Gérer les checkboxes
function updateSelectedFiles() {
    selectedFileIds.clear();
    selectedFolderPaths.clear();
    
    // Collecter les fichiers et dossiers sélectionnés
    document.querySelectorAll('#fileList input[type="checkbox"]:checked').forEach(checkbox => {
        const fileId = checkbox.dataset.fileId;
        const folderPath = checkbox.dataset.folderPath;
        if (fileId) {
            selectedFileIds.add(fileId);
        }
        if (folderPath) {
            selectedFolderPaths.add(folderPath);
        }
    });

    // Afficher/masquer les boutons selon la sélection
    const hasSelection = selectedFileIds.size > 0 || selectedFolderPaths.size > 0;
    const downloadBtn = document.getElementById('downloadSelectedBtn');
    const deleteBtn = document.getElementById('deleteSelectedBtn');
    
    if (hasSelection) {
        downloadBtn.style.display = selectedFileIds.size > 0 ? 'inline-block' : 'none';
        deleteBtn.style.display = 'inline-block';
    } else {
        downloadBtn.style.display = 'none';
        deleteBtn.style.display = 'none';
    }

    // Mettre à jour la checkbox "Sélectionner tout"
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const allFileCheckboxes = document.querySelectorAll('#fileList input[type="checkbox"]:not([disabled])');
    const checkedFileCheckboxes = document.querySelectorAll('#fileList input[type="checkbox"]:not([disabled]):checked');
    
    if (allFileCheckboxes.length > 0) {
        selectAllCheckbox.checked = allFileCheckboxes.length === checkedFileCheckboxes.length;
        selectAllCheckbox.indeterminate = checkedFileCheckboxes.length > 0 && checkedFileCheckboxes.length < allFileCheckboxes.length;
    } else {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    }
}

function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const allFileCheckboxes = document.querySelectorAll('#fileList input[type="checkbox"]:not([disabled])');
    
    allFileCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
    
    updateSelectedFiles();
}

// Télécharger les fichiers sélectionnés
async function downloadSelectedFiles() {
    if (selectedFileIds.size === 0) return;

    try {
        // Télécharger chaque fichier sélectionné
        for (const fileId of selectedFileIds) {
            const file = files.find(f => f.file_id === fileId);
            if (file) {
                try {
                    await decryptFileAPI(fileId, file.original_name);
                } catch (error) {
                    console.error(`Erreur lors du téléchargement de ${file.original_name}:`, error);
                    showModal('❌ Erreur', `Erreur lors du téléchargement de ${file.original_name}: ${error.message}`);
                }
            }
        }
        
        // Désélectionner après le téléchargement
        selectedFileIds.clear();
        document.querySelectorAll('#fileList input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = false;
        });
        updateSelectedFiles();
    } catch (error) {
        console.error('Erreur lors du téléchargement des fichiers:', error);
        showModal('❌ Erreur', 'Erreur lors du téléchargement: ' + error.message);
    }
}

// Supprimer les fichiers et dossiers sélectionnés
async function deleteSelectedFiles() {
    const filesToDelete = Array.from(selectedFileIds);
    const foldersToDelete = Array.from(selectedFolderPaths);
    
    if (filesToDelete.length === 0 && foldersToDelete.length === 0) return;

    const fileNames = filesToDelete.map(id => {
        const file = files.find(f => f.file_id === id);
        return file ? file.original_name : id;
    }).join('\n');
    
    const folderNames = foldersToDelete.map(path => {
        const folder = folders.find(f => f.folder_path === path);
        return folder ? folder.folder_name : path;
    }).join('\n');
    
    const items = [];
    if (fileNames) items.push(`Fichiers:\n${fileNames}`);
    if (folderNames) items.push(`Dossiers:\n${folderNames}`);
    
    showConfirmModal(
        '⚠️ Confirmation',
        `Supprimer définitivement les éléments sélectionnés?\n\n${items.join('\n\n')}`,
        async () => {
            try {
                // Supprimer les fichiers
                for (const fileId of filesToDelete) {
                    try {
                        await deleteFileAPI(fileId);
                    } catch (error) {
                        console.error(`Erreur lors de la suppression du fichier ${fileId}:`, error);
                    }
                }
                
                // Supprimer les dossiers (récursif)
                for (const folderPath of foldersToDelete) {
                    try {
                        await deleteFolderAPI(folderPath, true);
                        // Nettoyer l'historique de navigation
                        removePathFromHistory(folderPath);
                    } catch (error) {
                        console.error(`Erreur lors de la suppression du dossier ${folderPath}:`, error);
                    }
                }
                
                // Désélectionner
                selectedFileIds.clear();
                selectedFolderPaths.clear();
                document.querySelectorAll('#fileList input[type="checkbox"]').forEach(checkbox => {
                    checkbox.checked = false;
                });
                updateSelectedFiles();
                
                await loadFiles();
            } catch (error) {
                console.error('Erreur lors de la suppression:', error);
                showModal('❌ Erreur', 'Erreur lors de la suppression: ' + error.message);
            }
        }
    );
}

// Afficher les détails
async function showFileDetails() {
    if (!selectedFileId) return;
    const file = files.find(f => f.file_id === selectedFileId);
    if (!file) return;

    try {
        // Récupérer les détails complets depuis l'API
        const details = await getFileInfo(selectedFileId);
        
        const detailsText = `📄 Nom: ${details.name}
💾 Taille: ${formatSize(details.size)}
💾 Taille chiffrée: ${formatSize(details.encrypted_size)}
📅 Date: ${formatDate(details.created_at)}
🔑 ID: ${details.file_id}
📦 Chunks: ${details.chunks}
🔐 Algorithme: ${details.algorithm}`;

        showModal('Détails du fichier', detailsText);
    } catch (error) {
        console.error('Erreur lors de la récupération des détails:', error);
        showModal('❌ Erreur', 'Impossible de récupérer les détails: ' + error.message);
    }
}

// Télécharger fichier
async function downloadFile() {
    if (!selectedFileId) return;
    const file = files.find(f => f.file_id === selectedFileId);
    if (!file) return;

    try {
        await decryptFileAPI(selectedFileId, file.original_name);
    } catch (error) {
        console.error('Erreur lors du téléchargement:', error);
        showModal('❌ Erreur', 'Erreur lors du téléchargement: ' + error.message);
    }
}

// Supprimer fichier
async function deleteFile() {
    if (!selectedFileId) return;
    const file = files.find(f => f.file_id === selectedFileId);
    if (!file) return;

    showConfirmModal(
        '⚠️ Confirmation',
        `Supprimer définitivement le fichier?\n\n${file.original_name}`,
        async () => {
            try {
                await deleteFileAPI(selectedFileId);
                selectedFileId = null;
                await loadFiles();
            } catch (error) {
                console.error('Erreur lors de la suppression:', error);
                showModal('❌ Erreur', 'Erreur lors de la suppression: ' + error.message);
            }
        }
    );
}

