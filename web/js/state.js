/**
 * État global de l'application
 */
let files = [];
let folders = [];
let selectedFileId = null;
let selectedFolderPath = null;
let currentFolderPath = "/";
let isLoading = false;
let selectedFileIds = new Set(); // Pour les checkboxes
let selectedFolderPaths = new Set(); // Pour les checkboxes de dossiers
let dragTargetFolder = null; // Pour détecter le dossier survolé
let navigationHistory = []; // Historique de navigation
let historyIndex = -1; // Index actuel dans l'historique
let isNavigatingHistory = false; // Flag pour éviter d'ajouter à l'historique lors de la navigation

