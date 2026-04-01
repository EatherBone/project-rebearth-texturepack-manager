import os
import shutil
import json
import threading
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import zipfile

# --------------------------------------------------
#       Project Rebearth Texture Workshop v1.2
#                 by EatherBone
#                for community <3
# --------------------------------------------------

CONFIG_FILE = "config.json"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# progress popup
class ProgressPopup(ctk.CTkToplevel):
    def __init__(self, parent, title="Processing..."):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x180")
        self.attributes("-topmost", True)
        self.grab_set()
        self.resizable(False, False)
        
        self.label = ctk.CTkLabel(self, text="Please wait...", font=("Arial", 14))
        self.label.pack(pady=20)
        
        self.bar = ctk.CTkProgressBar(self, width=300)
        self.bar.set(0)
        self.bar.pack(pady=10)
        
        self.pct = ctk.CTkLabel(self, text="0%", font=("Arial", 12, "bold"))
        self.pct.pack()

    def update_progress(self, val):
        self.bar.set(val / 100)
        self.pct.configure(text=f"{val}%")
        self.update_idletasks()

# app
class ModManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Rebearth Texture Manager by  v1.1 by EatherBone")
        self.geometry("1250x850")     
        self.ensure_assets_on_disk()

        # icon
        try:
            icon_p = os.path.join(os.getcwd(), "assets", "icon.ico")
            if os.path.exists(icon_p):
                self.iconbitmap(icon_p)
        except: 
            pass

        self.game_path = ""
        self.res_path = ""
        self.app_folder = "" 
        self.selected_pack_folder = None
        self.packs_dir = os.path.join(os.getcwd(), "packs")
        os.makedirs(self.packs_dir, exist_ok=True)

        self.setup_ui()
        self.load_config()
        self.refresh_pack_list()

    def ensure_assets_on_disk(self):
        local_assets = os.path.join(os.getcwd(), "assets")
        os.makedirs(local_assets, exist_ok=True)
        
        # only icon is really needed now, exe patching is removed!!!!!!!
        files = ["icon.ico"] 
        for f in files:
            target = os.path.join(local_assets, f)
            if not os.path.exists(target):
                try:
                    src = resource_path(os.path.join("assets", f))
                    if os.path.exists(src):
                        shutil.copy2(src, target)
                except Exception as e:
                    print(f"Asset extraction error: {e}")

    def setup_ui(self):
        self.sidebar = ctk.CTkFrame(self, width=260)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)
        
        ctk.CTkLabel(self.sidebar, text="WORKSHOP", font=("Arial", 22, "bold")).pack(pady=20)
        
        ctk.CTkButton(self.sidebar, text="1. Select Game Folder", command=self.browse_game).pack(pady=5, padx=20)
        
        self.btn_unlock = ctk.CTkButton(self.sidebar, text="2. Prepare Modding", state="disabled", fg_color="green", command=self.prepare_modding)
        self.btn_unlock.pack(pady=5, padx=20)
        
        ctk.CTkLabel(self.sidebar, text="Tools", font=("Arial", 13, "bold")).pack(pady=(15, 2))
        ctk.CTkButton(self.sidebar, text="Export Original Textures", command=self.export_originals).pack(pady=5, padx=20)
        ctk.CTkButton(self.sidebar, text="Import Pack from ZIP", command=self.import_zip).pack(pady=5, padx=20)
        ctk.CTkButton(self.sidebar, text="Export Selected to ZIP", command=self.export_to_zip).pack(pady=5, padx=20)
        
        self.label_viewing = ctk.CTkLabel(self.sidebar, text="Viewing: None", text_color="#3498db", font=("Arial", 11, "italic"))
        self.label_viewing.pack(pady=(20, 5))
        
        self.btn_apply_pack = ctk.CTkButton(self.sidebar, text="APPLY SELECTED PACK", fg_color="#e67e22", state="disabled", command=self.apply_selected_pack)
        self.btn_apply_pack.pack(pady=5, padx=20)

        ctk.CTkButton(self.sidebar, text="LAUNCH GAME", fg_color="#27ae60", command=self.launch_game).pack(side="bottom", pady=20, padx=20)

        self.pack_list_frame = ctk.CTkScrollableFrame(self, label_text="My Texture Packs", width=250)
        self.pack_list_frame.pack(side="left", fill="y", padx=5, pady=10)
        
        self.editor_frame = ctk.CTkScrollableFrame(self, label_text="Pack Editor")
        self.editor_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"game_path": self.game_path}, f)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    path = data.get("game_path")
                    if path and os.path.exists(path):
                        self.game_path = path
                        self.res_path = os.path.join(path, "resources")
                        # updated path to .unpacked folder
                        self.app_folder = os.path.join(self.res_path, "app.asar.unpacked")
                        self.update_ui_state()
            except Exception as e:
                print(f"Config load error: {e}")

    def browse_game(self):
        path = filedialog.askdirectory(title="Select Game Root Folder")
        if path:
            self.game_path = path
            self.res_path = os.path.join(path, "resources")
            # updated path to .unpacked folder
            self.app_folder = os.path.join(self.res_path, "app.asar.unpacked")
            self.save_config()
            self.update_ui_state()
            self.refresh_pack_list()

    def update_ui_state(self):
        if not self.res_path: 
            self.btn_unlock.configure(state="disabled", text="Select Game First", fg_color="gray")
            return

        # check if the unpacked folder exists
        if os.path.exists(self.app_folder):
            self.btn_unlock.configure(state="disabled", text="Modding Mode: ACTIVE", fg_color="gray")
        else:
            # check if original asar exists to suggest unpacking/preparing
            asar_file = os.path.join(self.res_path, "app.asar")
            if os.path.exists(asar_file):
                self.btn_unlock.configure(state="normal", text="Prepare Modding (Unpack)", fg_color="green")
            else:
                self.btn_unlock.configure(state="disabled", text="Resources Not Found", fg_color="red")

    def prepare_modding(self):
        
        """
        Since Sam updated the game to expose resources, we mostly just need
        to ensure backups exist and confirm the folder structure is ready.
        No binary extraction or EXE patching needed yaaay :>
        """
        
        asar_path = os.path.join(self.res_path, "app.asar")
        unpacked_path = os.path.join(self.res_path, "app.asar.unpacked")
        
        def task(prog):
            
            if not os.path.exists(unpacked_path):
                raise FileNotFoundError("app.asar.unpacked not found. Ensure you have the latest game update.")

            # backups
            backups = os.path.join(self.res_path, "_backups")
            os.makedirs(backups, exist_ok=True)
            backup_dest = os.path.join(backups, "app.asar.unpacked")
            if not os.path.exists(backup_dest):
                prog(10)
                shutil.copytree(unpacked_path, backup_dest, dirs_exist_ok=False)
                prog(50)
            
            # Also backup the .asar file itself if present
            if os.path.exists(asar_path):
                asar_backup = os.path.join(backups, "app.asar")
                if not os.path.exists(asar_backup):
                    shutil.copy2(asar_path, asar_backup)
            
            prog(100)
            self.after(0, self.update_ui_state)
            self.after(0, self.refresh_pack_list)
        
        self.run_thread(task, "Preparing Modding Environment")

    def select_pack(self, folder_name):
        self.selected_pack_folder = os.path.join(self.packs_dir, folder_name)
        self.label_viewing.configure(text=f"Editing Pack: {folder_name}")
        self.btn_apply_pack.configure(state="normal" if self.app_folder else "disabled")
        self.start_async_editor_refresh()

    def start_async_editor_refresh(self):
        for w in self.editor_frame.winfo_children(): 
            w.destroy()
        if not self.selected_pack_folder: 
            return
        
        img_root = os.path.join(self.selected_pack_folder, "dist", "public", "img")
        if not os.path.exists(img_root):
            ctk.CTkLabel(self.editor_frame, text="No 'dist/public/img' found in pack.", text_color="red").pack(pady=20)
            return

        all_webp = []
        for root, _, files in os.walk(img_root):
            for f in files:
                if f.lower().endswith(".webp"): 
                    all_webp.append(os.path.join(root, f))
        
        self.render_chunks(all_webp, 0, self.selected_pack_folder)

    def render_chunks(self, file_list, index, target_pack):
        if self.selected_pack_folder != target_pack: 
            return
        chunk_size = 15
        end_index = min(index + chunk_size, len(file_list))
        for i in range(index, end_index):
            self.add_editor_item(file_list[i], os.path.basename(file_list[i]))
        if end_index < len(file_list):
            self.after(10, lambda: self.render_chunks(file_list, end_index, target_pack))

    def add_editor_item(self, full_p, name):
        row = ctk.CTkFrame(self.editor_frame)
        row.pack(fill="x", pady=2, padx=5)
        try:
            img = Image.open(full_p)
            img.thumbnail((45, 45))
            ctk_i = ctk.CTkImage(light_image=img, size=(45, 45))
            ctk.CTkLabel(row, image=ctk_i, text="").pack(side="left", padx=5)
        except Exception:
            ctk.CTkLabel(row, text="[Err]", width=45).pack(side="left", padx=5)
        
        ctk.CTkLabel(row, text=name, anchor="w", wraplength=300).pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkButton(row, text="Replace", width=70, command=lambda p=full_p: self.replace_img(p)).pack(side="right", padx=5)

    def replace_img(self, target_path):
        src = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.webp")])
        if src:
            try:
                # Convert and save as WEBP to match game format
                img = Image.open(src)
                if img.mode in ("RGBA", "P"):
                    img.save(target_path, "WEBP", lossless=False, quality=80)
                else:
                    img.convert("RGB").save(target_path, "WEBP", lossless=False, quality=80)
                self.start_async_editor_refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to replace image: {e}")

    def apply_selected_pack(self):
        if not self.selected_pack_folder or not self.app_folder: 
            return
        
        if not messagebox.askyesno("Confirm", "This will overwrite game files in app.asar.unpacked.\nMake sure you have a backup.\nContinue?"):
            return

        def task(prog):
            # Copy contents of pack to the unpacked game folder
            # Assuming the pack structure mirrors the game structure starting from root or specific subdirs
            # Usually packs contain 'dist', 'src', etc.
            
            # We copy everything from the pack root into the app_folder
            shutil.copytree(self.selected_pack_folder, self.app_folder, dirs_exist_ok=True)
            prog(100)
        
        self.run_thread(task, f"Applying {os.path.basename(self.selected_pack_folder)}")

    def export_originals(self):
        # Source is now the unpacked folder
        source_path = os.path.join(self.res_path, "_backups", "app.asar.unpacked")
        if not os.path.exists(source_path):
            source_path = self.app_folder # Fallback to current if no backup
        
        if not os.path.exists(source_path):
            return messagebox.showerror("Error", "Game resources folder not found!")
            
        target = os.path.join(self.packs_dir, "Vanilla_Original")
        
        def task(prog):
            # Extract only images for convenience
            src_img = os.path.join(source_path, "dist", "public", "img")
            dst_img = os.path.join(target, "dist", "public", "img")
            
            if os.path.exists(src_img):
                shutil.copytree(src_img, dst_img, dirs_exist_ok=True)
            else:
                # If structure is different, copy whole thing
                shutil.copytree(source_path, target, dirs_exist_ok=True)
            
            prog(100)
            self.after(0, self.refresh_pack_list)
        
        self.run_thread(task, "Exporting Originals")

    def import_zip(self):
        src = filedialog.askopenfilename(filetypes=[("ZIP Pack", "*.zip")])
        if not src: 
            return
        name = os.path.basename(src)[:-4]
        target = os.path.join(self.packs_dir, name)
        os.makedirs(target, exist_ok=True)
        try:
            with zipfile.ZipFile(src, 'r') as z: 
                z.extractall(target)
            self.refresh_pack_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import ZIP: {e}")

    def export_to_zip(self):
        if not self.selected_pack_folder: 
            return
        name = filedialog.asksaveasfilename(defaultextension=".zip", initialdir=os.getcwd(), initialfile=f"{os.path.basename(self.selected_pack_folder)}.zip")
        if name:
            try:
                with zipfile.ZipFile(name, 'w', zipfile.ZIP_DEFLATED) as z:
                    for r, _, fs in os.walk(self.selected_pack_folder):
                        for f in fs:
                            ap = os.path.join(r, f)
                            arcname = os.path.relpath(ap, self.selected_pack_folder)
                            z.write(ap, arcname)
                messagebox.showinfo("Exported", "ZIP Created Successfully!")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def refresh_pack_list(self):
        for w in self.pack_list_frame.winfo_children(): 
            w.destroy()
        
        ctk.CTkButton(self.pack_list_frame, text="Restore Game Originals", fg_color="gray", hover_color="#555555", command=self.restore_game).pack(pady=5, fill="x", padx=5)
        
        if os.path.exists(self.packs_dir):
            for item in sorted(os.listdir(self.packs_dir)):
                full_path = os.path.join(self.packs_dir, item)
                if os.path.isdir(full_path) and not item.startswith("."):
                    is_sel = (full_path == self.selected_pack_folder)
                    color = "#3498db" if is_sel else "#3b3b3b"
                    ctk.CTkButton(self.pack_list_frame, text=item, fg_color=color, hover_color="#4a4a4a", command=lambda n=item: self.select_pack(n)).pack(pady=2, fill="x", padx=5)

    def restore_game(self):
        backups = os.path.join(self.res_path, "_backups")
        unpacked_backup = os.path.join(backups, "app.asar.unpacked")
        
        if not os.path.exists(unpacked_backup):
            return messagebox.showwarning("Warning", "No backup found in _backups/app.asar.unpacked")
            
        if not messagebox.askyesno("Confirm Restore", "This will revert all texture changes to the original state.\nContinue?"):
            return

        def task(prog):
            if os.path.exists(self.app_folder): 
                shutil.rmtree(self.app_folder)
            
            shutil.copytree(unpacked_backup, self.app_folder)
            prog(100)
            
            self.selected_pack_folder = None
            self.after(0, self.update_ui_state)
            self.after(0, self.refresh_pack_list)
            self.after(0, lambda: messagebox.showinfo("Success", "Game restored to original state."))
        
        self.run_thread(task, "Restoring Original Files")

    def run_thread(self, task_func, title):
        popup = ProgressPopup(self, title)
        def wrapper():
            try:
                task_func(popup.update_progress)
                self.after(0, lambda: [popup.destroy(), messagebox.showinfo("Done", "Operation Finished!")])
            except Exception as e:
                self.after(0, lambda: [popup.destroy(), messagebox.showerror("Error", str(e))])
        
        threading.Thread(target=wrapper, daemon=True).start()

    def launch_game(self):
        exe = os.path.join(self.game_path, "project_rebearth.exe")
        if os.path.exists(exe): 
            os.startfile(exe)
        else:
            messagebox.showerror("Error", "Game executable not found at specified path.")

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    ModManager().mainloop()
