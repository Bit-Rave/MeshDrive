/**
 * Gestion de la navigation et de l'historique
 */

// Navigation dans l'historique
function addToHistory(folderPath) {
    // Supprimer les éléments après l'index actuel si on navigue dans le passé
    if (historyIndex < navigationHistory.length - 1) {
        navigationHistory = navigationHistory.slice(0, historyIndex + 1);
    }
    
    // Ajouter le nouveau chemin
    navigationHistory.push(folderPath);
    historyIndex = navigationHistory.length - 1;
    
    updateNavigationButtons();
}

async function navigateBack() {
    if (historyIndex > 0) {
        historyIndex--;
        isNavigatingHistory = true;
        
        // Vérifier que le dossier existe avant de naviguer
        const targetPath = navigationHistory[historyIndex];
        if (await folderExists(targetPath)) {
            await loadFiles(targetPath);
        } else {
            // Le dossier n'existe plus, nettoyer l'historique et aller à un dossier valide
            cleanHistoryFromInvalidPath(targetPath);
            // Aller au dossier valide le plus proche (ou à la racine)
            if (historyIndex >= 0 && historyIndex < navigationHistory.length) {
                await loadFiles(navigationHistory[historyIndex]);
            } else {
                await loadFiles("/");
            }
        }
        
        isNavigatingHistory = false;
        updateNavigationButtons();
    }
}

async function navigateForward() {
    if (historyIndex < navigationHistory.length - 1) {
        historyIndex++;
        isNavigatingHistory = true;
        
        // Vérifier que le dossier existe avant de naviguer
        const targetPath = navigationHistory[historyIndex];
        if (await folderExists(targetPath)) {
            await loadFiles(targetPath);
        } else {
            // Le dossier n'existe plus, nettoyer l'historique et aller à un dossier valide
            cleanHistoryFromInvalidPath(targetPath);
            // Aller au dossier valide le plus proche (ou à la racine)
            if (historyIndex >= 0 && historyIndex < navigationHistory.length) {
                await loadFiles(navigationHistory[historyIndex]);
            } else {
                await loadFiles("/");
            }
        }
        
        isNavigatingHistory = false;
        updateNavigationButtons();
    }
}

// Vérifier si un dossier existe
async function folderExists(folderPath) {
    // La racine existe toujours
    if (folderPath === "/") {
        return true;
    }
    
    try {
        const contents = await getFolderContents(folderPath);
        // Si on peut récupérer le contenu, le dossier existe
        return true;
    } catch (error) {
        // Si on obtient une erreur 404 ou similaire, le dossier n'existe pas
        return false;
    }
}

// Nettoyer l'historique en retirant un chemin invalide et tous ses sous-chemins
function cleanHistoryFromInvalidPath(invalidPath) {
    // Retirer le chemin invalide et tous les chemins qui commencent par ce chemin
    navigationHistory = navigationHistory.filter(path => {
        // Garder la racine et les chemins qui ne sont pas sous le chemin invalide
        if (path === "/") return true;
        if (invalidPath === "/") return path === "/";
        return !path.startsWith(invalidPath + "/") && path !== invalidPath;
    });
    
    // Ajuster l'index pour qu'il reste valide
    if (historyIndex >= navigationHistory.length) {
        historyIndex = navigationHistory.length - 1;
    }
    if (historyIndex < 0 && navigationHistory.length > 0) {
        historyIndex = 0;
    }
    
    updateNavigationButtons();
}

// Nettoyer l'historique quand un dossier est supprimé
function removePathFromHistory(deletedPath) {
    cleanHistoryFromInvalidPath(deletedPath);
    
    // Si le dossier actuel est supprimé, aller à la racine ou au dossier parent valide
    if (currentFolderPath === deletedPath || currentFolderPath.startsWith(deletedPath + "/")) {
        // Trouver le dossier parent valide le plus proche
        let validPath = "/";
        for (let i = navigationHistory.length - 1; i >= 0; i--) {
            const path = navigationHistory[i];
            if (path !== deletedPath && !path.startsWith(deletedPath + "/")) {
                validPath = path;
                break;
            }
        }
        historyIndex = navigationHistory.indexOf(validPath);
        if (historyIndex < 0) {
            historyIndex = 0;
            navigationHistory = ["/"];
        }
        loadFiles(validPath);
    }
}

function updateNavigationButtons() {
    const backBtn = document.getElementById('backBtn');
    const forwardBtn = document.getElementById('forwardBtn');
    
    backBtn.disabled = historyIndex <= 0;
    forwardBtn.disabled = historyIndex >= navigationHistory.length - 1;
}

