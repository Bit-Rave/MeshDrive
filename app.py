#!/usr/bin/env python3
"""
MyDrive - Interface Graphique avec Tkinter
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime
from cryptolib import CryptoSystem

class MyDriveApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔐 MyDrive - Stockage Sécurisé")
        self.root.geometry("1000x600")
        self.root.configure(bg='#1e1e2e')

        self.crypto = CryptoSystem()
        self.files = []

        self.setup_ui()
        self.load_files()

    def setup_ui(self):
        """Créer l'interface"""

        # === HEADER ===
        header = tk.Frame(self.root, bg='#2d2d44', height=80)
        header.pack(fill='x', padx=10, pady=(10, 0))
        header.pack_propagate(False)

        tk.Label(
            header, 
            text="🔐 MyDrive", 
            font=('Arial', 24, 'bold'),
            fg='#89b4fa',
            bg='#2d2d44'
        ).pack(side='left', padx=20)

        # Boutons d'action
        btn_frame = tk.Frame(header, bg='#2d2d44')
        btn_frame.pack(side='right', padx=20)

        tk.Button(
            btn_frame,
            text="📤 Upload",
            command=self.upload_file,
            bg='#89b4fa',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10,
            relief='flat',
            cursor='hand2'
        ).pack(side='left', padx=5)

        tk.Button(
            btn_frame,
            text="🔄 Actualiser",
            command=self.load_files,
            bg='#585b70',
            fg='white',
            font=('Arial', 12),
            padx=15,
            pady=10,
            relief='flat',
            cursor='hand2'
        ).pack(side='left', padx=5)

        # === STATISTIQUES ===
        stats_frame = tk.Frame(self.root, bg='#1e1e2e')
        stats_frame.pack(fill='x', padx=10, pady=10)

        self.stats_label = tk.Label(
            stats_frame,
            text="📊 Statistiques: ...",
            font=('Arial', 11),
            fg='#cdd6f4',
            bg='#1e1e2e',
            anchor='w'
        )
        self.stats_label.pack(fill='x', padx=10)

        # === BARRE DE RECHERCHE ===
        search_frame = tk.Frame(self.root, bg='#2d2d44', height=50)
        search_frame.pack(fill='x', padx=10, pady=(0, 10))
        search_frame.pack_propagate(False)

        tk.Label(
            search_frame,
            text="🔍",
            font=('Arial', 16),
            bg='#2d2d44',
            fg='#cdd6f4'
        ).pack(side='left', padx=(15, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_files())

        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=('Arial', 12),
            bg='#1e1e2e',
            fg='#cdd6f4',
            insertbackground='#cdd6f4',
            relief='flat',
            bd=0
        )
        search_entry.pack(side='left', fill='both', expand=True, padx=10, pady=8)

        # Tri
        tk.Label(
            search_frame,
            text="Trier par:",
            font=('Arial', 10),
            bg='#2d2d44',
            fg='#cdd6f4'
        ).pack(side='left', padx=(10, 5))

        self.sort_var = tk.StringVar(value='date')
        sort_combo = ttk.Combobox(
            search_frame,
            textvariable=self.sort_var,
            values=['date', 'name', 'size'],
            state='readonly',
            width=10,
            font=('Arial', 10)
        )
        sort_combo.pack(side='left', padx=(0, 15))
        sort_combo.bind('<<ComboboxSelected>>', lambda e: self.load_files())

        # === LISTE DES FICHIERS (Treeview) ===
        tree_frame = tk.Frame(self.root, bg='#1e1e2e')
        tree_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')

        # Treeview
        columns = ('Nom', 'Taille', 'Date', 'ID')
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            yscrollcommand=scrollbar.set,
            selectmode='browse'
        )
        scrollbar.config(command=self.tree.yview)

        # Colonnes
        self.tree.heading('Nom', text='📄 Nom du fichier')
        self.tree.heading('Taille', text='💾 Taille')
        self.tree.heading('Date', text='📅 Date')
        self.tree.heading('ID', text='🔑 ID')

        self.tree.column('Nom', width=400)
        self.tree.column('Taille', width=100)
        self.tree.column('Date', width=180)
        self.tree.column('ID', width=200)

        self.tree.pack(fill='both', expand=True)

        # Style du Treeview
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            'Treeview',
            background='#2d2d44',
            foreground='#cdd6f4',
            fieldbackground='#2d2d44',
            font=('Arial', 10)
        )
        style.configure('Treeview.Heading', font=('Arial', 11, 'bold'))
        style.map('Treeview', background=[('selected', '#89b4fa')])

        # Menu contextuel
        self.tree.bind('<Button-3>', self.show_context_menu)
        self.tree.bind('<Double-1>', self.show_file_details)

    def load_files(self):
        """Charger les fichiers"""
        try:
            self.files = self.crypto.list_files()

            # ✅ Trier (tous les fichiers sont des dicts)
            sort_by = self.sort_var.get()
            if sort_by == 'date':
                self.files.sort(key=lambda f: f.get('upload_date', ''), reverse=True)
            elif sort_by == 'name':
                self.files.sort(key=lambda f: f.get('original_name', '').lower())
            elif sort_by == 'size':
                self.files.sort(key=lambda f: f.get('file_size', 0), reverse=True)  # ✅ Corrigé: file_size au lieu de original_size

            self.update_tree()
            self.update_stats()

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Impossible de charger les fichiers:\n{e}")

    def update_tree(self):
        """Mettre à jour le Treeview"""
        # Vider
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Remplir
        search_term = self.search_var.get().lower()

        for file in self.files:
            # ✅ Tous les fichiers sont des dicts
            name = file.get('original_name', 'Inconnu')
            size = self.format_size(file.get('file_size', 0))
            date = self.format_date(file.get('upload_date', ''))
            file_id = file.get('file_id', '')

            # Filtrer par recherche
            if search_term and search_term not in name.lower():
                continue

            # Insérer
            self.tree.insert('', 'end', values=(
                name, 
                size, 
                date, 
                file_id[:16] + '...' if file_id else 'N/A'
            ), tags=(file_id,))

    def filter_files(self):
        """Filtrer les fichiers (recherche)"""
        self.update_tree()

    def update_stats(self):
        """Mettre à jour les statistiques"""
        total = len(self.files)
        # ✅ Corrigé: file_size au lieu de original_size
        total_size = sum(f.get('file_size', 0) for f in self.files)

        self.stats_label.config(
            text=f"📊 {total} fichier(s) • 💾 {self.format_size(total_size)} au total"
        )

    def upload_file(self):
        """Upload un fichier"""
        filepath = filedialog.askopenfilename(
            title="Sélectionner un fichier à uploader",
            filetypes=[
                ("Tous les fichiers", "*.*"),
                ("Images", "*.jpg *.jpeg *.png *.gif"),
                ("Documents", "*.pdf *.doc *.docx"),
                ("Vidéos", "*.mp4 *.avi *.mkv")
            ]
        )

        if not filepath:
            return

        try:
            result = self.crypto.encrypt_file(filepath)

            # ✅ Gérer le retour (objet FileMetadata)
            if hasattr(result, 'file_id'):
                file_id = result.file_id
                name = result.original_name
            else:
                # Format dict (au cas où)
                file_id = result.get('file_id', 'Inconnu')
                name = result.get('original_name', Path(filepath).name)

            messagebox.showinfo(
                "✅ Upload réussi",
                f"Fichier uploadé avec succès!\n\n"
                f"Nom: {name}\n"
                f"ID: {file_id}"
            )
            self.load_files()

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("❌ Erreur", f"Erreur lors de l'upload:\n{e}")

    def show_context_menu(self, event):
        """Menu contextuel (clic droit)"""
        item = self.tree.identify_row(event.y)
        if not item:
            return

        self.tree.selection_set(item)

        menu = tk.Menu(self.root, tearoff=0, bg='#2d2d44', fg='#cdd6f4')
        menu.add_command(label="📋 Détails", command=self.show_file_details)
        menu.add_command(label="📥 Télécharger", command=self.download_file)
        menu.add_separator()
        menu.add_command(label="🗑️ Supprimer", command=self.delete_file)

        menu.post(event.x_root, event.y_root)

    def show_file_details(self, event=None):
        """Afficher les détails d'un fichier"""
        selection = self.tree.selection()
        if not selection:
            return

        file_id = self.tree.item(selection[0])['tags'][0]
        file = next((f for f in self.files if f.get('file_id') == file_id), None)

        if not file:
            return

        details = (
            f"📄 Nom: {file.get('original_name', 'Inconnu')}\n"
            f"💾 Taille: {self.format_size(file.get('file_size', 0))}\n"
            f"📅 Date: {self.format_date(file.get('upload_date', ''))}\n"
            f"🔑 ID: {file.get('file_id', '')}\n"
            f"📦 Chunks: {file.get('chunk_count', 0)}\n"
            f"🔐 Algorithme: AES-256-GCM"
        )

        messagebox.showinfo("Détails du fichier", details)

    def download_file(self):
        """Télécharger un fichier"""
        selection = self.tree.selection()
        if not selection:
            return

        file_id = self.tree.item(selection[0])['tags'][0]
        file = next((f for f in self.files if f.get('file_id') == file_id), None)

        if not file:
            return

        save_path = filedialog.asksaveasfilename(
            title="Enregistrer le fichier",
            initialfile=file.get('original_name', 'fichier'),
            defaultextension=Path(file.get('original_name', '')).suffix
        )

        if not save_path:
            return

        try:
            self.crypto.decrypt_file(file_id, save_path)
            messagebox.showinfo("✅ Téléchargement réussi", f"Fichier enregistré:\n{save_path}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("❌ Erreur", f"Erreur lors du téléchargement:\n{e}")

    def delete_file(self):
        """Supprimer un fichier"""
        selection = self.tree.selection()
        if not selection:
            return

        file_id = self.tree.item(selection[0])['tags'][0]
        file = next((f for f in self.files if f.get('file_id') == file_id), None)

        if not file:
            return

        confirm = messagebox.askyesno(
            "⚠️ Confirmation",
            f"Supprimer définitivement le fichier?\n\n{file.get('original_name', 'Inconnu')}"
        )

        if not confirm:
            return

        try:
            self.crypto.delete_file(file_id)
            messagebox.showinfo("✅ Suppression réussie", "Fichier supprimé")
            self.load_files()
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("❌ Erreur", f"Erreur lors de la suppression:\n{e}")

    @staticmethod
    def format_size(size):
        """Formater la taille"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

    @staticmethod
    def format_date(date_str):
        """Formater la date"""
        if not date_str:
            return "Inconnue"
        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date.strftime('%d/%m/%Y %H:%M')
        except:
            return date_str[:19] if date_str else "Inconnue"

def main():
    root = tk.Tk()
    app = MyDriveApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
