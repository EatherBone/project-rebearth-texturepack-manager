import os
import shutil
import json
import struct
import zipfile
import threading
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image

# --------------------------------------------------
#       Project Rebearth Texture Workshop v1.0
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

# asar engine
class AsarTool:
    @staticmethod
    def extract(asar_path, out_dir, progress_callback=None, filter_path=None):
        unpacked_root = asar_path + ".unpacked"
        with open(asar_path, 'rb', buffering=1024*1024) as f:
            f.seek(12)
            header_size = struct.unpack('<I', f.read(4))[0]
            header_json = f.read(header_size).decode('utf-8')
            header = json.loads(header_json[:header_json.rfind('}')+1])
            base_offset = 16 + ((header_size + 3) & ~3)

            all_files = []
            def collect(files, rel_parts=[]):
                for name, info in files.items():
                    if 'files' in info: collect(info['files'], rel_parts + [name])
                    else:
                        rel_path = "/".join(rel_parts + [name])
                        if filter_path is None or rel_path.startswith(filter_path):
                            all_files.append((rel_parts + [name], info))
            collect(header['files'])

            total = len(all_files)
            if total == 0: return
            last_p = -1
            for i, (parts, info) in enumerate(all_files):
                full_path = os.path.join(out_dir, *parts)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                if info.get('unpacked'):
                    src_unp = os.path.join(unpacked_root, *parts)
                    if os.path.exists(src_unp): shutil.copy2(src_unp, full_path)
                else:
                    f.seek(base_offset + int(info['offset']))
                    with open(full_path, 'wb', buffering=1024*1024) as out:
                        rem = int(info['size'])
                        while rem > 0:
                            chunk = f.read(min(rem, 1024*1024))
                            out.write(chunk); rem -= len(chunk)
                
                curr_p = int((i / total) * 100)
                if curr_p > last_p and progress_callback:
                    progress_callback(curr_p); last_p = curr_p

# progress
class ProgressPopup(ctk.CTkToplevel):
    def __init__(self, parent, title="Processing..."):
        super().__init__(parent)
        self.title(title); self.geometry("400x180")
        self.attributes("-topmost", True); self.grab_set()
        self.resizable(False, False)
        self.label = ctk.CTkLabel(self, text="Please wait...", font=("Arial", 14))
        self.label.pack(pady=20)
        self.bar = ctk.CTkProgressBar(self, width=300); self.bar.set(0); self.bar.pack(pady=10)
        self.pct = ctk.CTkLabel(self, text="0%", font=("Arial", 12, "bold")); self.pct.pack()

    def update_progress(self, val):
        self.bar.set(val / 100); self.pct.configure(text=f"{val}%"); self.update_idletasks()

# app
class ModManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Project Rebearth Texture Workshop v1.2")
        self.geometry("1250x850")     
        self.ensure_assets_on_disk()

        # get icon
        try:
            icon_p = os.path.join(os.getcwd(), "assets", "icon.ico")
            self.iconbitmap(icon_p)
        except: pass

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
        
        # file list to unpack
        files = ["project_rebearth.exe", "icon.ico"]
        for f in files:
            target = os.path.join(local_assets, f)
            if not os.path.exists(target):
                try:
                    src = resource_path(os.path.join("assets", f))
                    if os.path.exists(src):
                        shutil.copy2(src, target)
                except Exception as e:
                    print(f"Extraction error: {e}")

    def setup_ui(self):
        self.sidebar = ctk.CTkFrame(self, width=260)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)
        ctk.CTkLabel(self.sidebar, text="WORKSHOP", font=("Arial", 22, "bold")).pack(pady=20)
        
        ctk.CTkButton(self.sidebar, text="1. Select Game Folder", command=self.browse_game).pack(pady=5, padx=20)
        self.btn_unlock = ctk.CTkButton(self.sidebar, text="2. Unlock Modding Mode", state="disabled", fg_color="green", command=self.unlock_game)
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
                        self.app_folder = os.path.join(self.res_path, "app")
                        self.update_ui_state()
            except: pass

    def browse_game(self):
        path = filedialog.askdirectory(title="Select Game Root Folder")
        if path:
            self.game_path = path
            self.res_path = os.path.join(path, "resources")
            self.app_folder = os.path.join(self.res_path, "app")
            self.save_config()
            self.update_ui_state()
            self.refresh_pack_list()

    def update_ui_state(self):
        if not self.res_path: return
        asar_exists = os.path.exists(os.path.join(self.res_path, "app.asar"))
        if not asar_exists and os.path.exists(self.app_folder):
            self.btn_unlock.configure(state="disabled", text="Modding Mode: ACTIVE", fg_color="gray")
        else:
            self.btn_unlock.configure(state="normal", text="Unlock Modding Mode", fg_color="green")

    def patch_exe(self):
        p_src = os.path.join(os.getcwd(), "assets", "project_rebearth.exe")
        p_dst = os.path.join(self.game_path, "project_rebearth.exe")
        
        if not os.path.exists(p_src):
            messagebox.showerror("Error", "Source assets/project_rebearth.exe not found!")
            return False

        try:
            # cp via cmd lol case my last attemts trying to do this stuff with python failed idk why      
            cmd = f'cmd /c taskkill /f /im project_rebearth.exe & del /f /q "{p_dst}" & copy /y "{p_src}" "{p_dst}"'
            os.system(cmd)
            return True
        except Exception as e:
            print(f"PATCH ERROR: {e}")
            return False

    def unlock_game(self):
        asar_path = os.path.join(self.res_path, "app.asar")
        def task(prog):
            # unpacking
            AsarTool.extract(asar_path, self.app_folder, prog)
            
            # backup
            backups = os.path.join(self.res_path, "_backups"); os.makedirs(backups, exist_ok=True)
            for item in os.listdir(self.res_path):
                if item.startswith("app.asar") and item != "app" and item != "_backups":
                    src = os.path.join(self.res_path, item)
                    dst = os.path.join(backups, item)
                    if os.path.exists(dst):
                        if os.path.isdir(dst): shutil.rmtree(dst)
                        else: os.remove(dst)
                    shutil.move(src, dst)
            
            # exe patch
            if not self.patch_exe():
                self.after(0, lambda: messagebox.showwarning("Warning", "EXE Patch failed. Please replace it manually from /assets folder."))
            
            self.after(0, self.update_ui_state)
            self.after(0, self.refresh_pack_list)
        
        self.run_thread(task, "Unlocking Game")

    def select_pack(self, folder_name):
        self.selected_pack_folder = os.path.join(self.packs_dir, folder_name)
        self.label_viewing.configure(text=f"Editing Pack: {folder_name}")
        self.btn_apply_pack.configure(state="normal" if self.app_folder else "disabled")
        self.start_async_editor_refresh()

    def start_async_editor_refresh(self):
        for w in self.editor_frame.winfo_children(): w.destroy()
        if not self.selected_pack_folder: return
        img_root = os.path.join(self.selected_pack_folder, "dist", "public", "img")
        all_webp = []
        for root, _, files in os.walk(img_root):
            for f in files:
                if f.lower().endswith(".webp"): all_webp.append(os.path.join(root, f))
        self.render_chunks(all_webp, 0, self.selected_pack_folder)

    def render_chunks(self, file_list, index, target_pack):
        if self.selected_pack_folder != target_pack: return
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
            img = Image.open(full_p); img.thumbnail((45, 45))
            ctk_i = ctk.CTkImage(light_image=img, size=(45, 45))
            ctk.CTkLabel(row, image=ctk_i, text="").pack(side="left", padx=5)
        except:
            ctk.CTkLabel(row, text="[Err]", width=45).pack(side="left", padx=5)
        ctk.CTkLabel(row, text=name, anchor="w").pack(side="left", padx=10)
        ctk.CTkButton(row, text="Replace", width=70, command=lambda p=full_p: self.replace_img(p)).pack(side="right", padx=5)

    def replace_img(self, target_path):
        src = filedialog.askopenfilename()
        if src:
            Image.open(src).save(target_path, "WEBP")
            self.start_async_editor_refresh()

    def apply_selected_pack(self):
        if not self.selected_pack_folder or not self.app_folder: return
        def task(prog):
            shutil.copytree(self.selected_pack_folder, self.app_folder, dirs_exist_ok=True)
        self.run_thread(task, f"Applying {os.path.basename(self.selected_pack_folder)}")

    def export_originals(self):
        asar_path = os.path.join(self.res_path, "_backups", "app.asar")
        if not os.path.exists(asar_path): asar_path = os.path.join(self.res_path, "app.asar")
        if not os.path.exists(asar_path): return messagebox.showerror("Error", "Original app.asar not found!")
        target = os.path.join(self.packs_dir, "Vanilla_Original")
        def task(prog):
            AsarTool.extract(asar_path, target, prog, filter_path="dist/public/img")
            self.after(0, self.refresh_pack_list)
        self.run_thread(task, "Exporting Originals")

    def import_zip(self):
        src = filedialog.askopenfilename(filetypes=[("ZIP Pack", "*.zip")])
        if not src: return
        name = os.path.basename(src)[:-4]
        target = os.path.join(self.packs_dir, name)
        os.makedirs(target, exist_ok=True)
        with zipfile.ZipFile(src, 'r') as z: z.extractall(target)
        self.refresh_pack_list()

    def export_to_zip(self):
        if not self.selected_pack_folder: return
        name = filedialog.asksaveasfilename(defaultextension=".zip", initialdir=os.getcwd())
        if name:
            with zipfile.ZipFile(name, 'w') as z:
                for r, _, fs in os.walk(self.selected_pack_folder):
                    for f in fs:
                        ap = os.path.join(r, f)
                        z.write(ap, os.path.relpath(ap, self.selected_pack_folder))
            messagebox.showinfo("Exported", "ZIP Created!")

    def refresh_pack_list(self):
        for w in self.pack_list_frame.winfo_children(): w.destroy()
        ctk.CTkButton(self.pack_list_frame, text="Restore Game Originals", fg_color="gray", command=self.restore_game).pack(pady=5, fill="x", padx=5)
        if os.path.exists(self.packs_dir):
            for item in os.listdir(self.packs_dir):
                full_path = os.path.join(self.packs_dir, item)
                if os.path.isdir(full_path):
                    is_sel = (full_path == self.selected_pack_folder)
                    color = "#3498db" if is_sel else "#3b3b3b"
                    ctk.CTkButton(self.pack_list_frame, text=item, fg_color=color, command=lambda n=item: self.select_pack(n)).pack(pady=2, fill="x", padx=5)

    def restore_game(self):
        backups = os.path.join(self.res_path, "_backups")
        if os.path.exists(backups):
            if os.path.exists(self.app_folder): shutil.rmtree(self.app_folder)
            for item in os.listdir(backups):
                shutil.move(os.path.join(backups, item), os.path.join(self.res_path, item))
            shutil.rmtree(backups)
            self.selected_pack_folder = None
            self.update_ui_state()
            self.refresh_pack_list()

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
        if os.path.exists(exe): os.startfile(exe)

if __name__ == "__main__":
    ModManager().mainloop()