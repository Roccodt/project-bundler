#!/usr/bin/env python3
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES
from tkinter import filedialog, messagebox
import tarfile, gzip, base64, io, threading, subprocess, hashlib
import sys
from pathlib import Path
import shutil

LIBRARY_FOLDER = Path.home() / "MyProjectBundles"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ─────────────────────────────────────────────────────────────
# NATIVE FILE PICKERS  (zenity → fallback to tkinter)
# ─────────────────────────────────────────────────────────────

def zenity_select_folder(title="Select Folder"):
    try:
        proc = subprocess.run(
            ["zenity", "--file-selection", "--directory",
             f"--title={title}"],
            capture_output=True, text=True
        )
        return proc.stdout.strip() if proc.returncode == 0 else None
    except FileNotFoundError:
        return None


def zenity_select_file(title="Select Bundle"):
    try:
        proc = subprocess.run(
            ["zenity", "--file-selection",
             "--file-filter=Bundle files | *.bundle.txt",
             f"--title={title}"],
            capture_output=True, text=True
        )
        return proc.stdout.strip() if proc.returncode == 0 else None
    except FileNotFoundError:
        return None


# ─────────────────────────────────────────────────────────────
# SAFE DIALOG HELPERS
# Zenity is tried first. If it fails or isn't installed, we
# fall back to tkinter dialogs. The root window is withdrawn
# before opening tkinter dialogs so they get focus correctly
# when running as a PyInstaller bundle.
# ─────────────────────────────────────────────────────────────

def pick_folder(root, title="Select Folder"):
    result = zenity_select_folder(title)
    if result:
        return result
    root.withdraw()
    try:
        path = filedialog.askdirectory(title=title, parent=root)
    finally:
        root.deiconify()
        root.lift()
        root.focus_force()
    return path or None


def pick_file(root, title="Select Bundle"):
    result = zenity_select_file(title)
    if result:
        return result
    root.withdraw()
    try:
        path = filedialog.askopenfilename(
            title=title,
            parent=root,
            filetypes=[("Bundle files", "*.bundle.txt"), ("All files", "*.*")]
        )
    finally:
        root.deiconify()
        root.lift()
        root.focus_force()
    return path or None


# ─────────────────────────────────────────────────────────────
# HASHING
# ─────────────────────────────────────────────────────────────

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# ─────────────────────────────────────────────────────────────
# DROP ZONE
# Both the frame AND the label are registered as DnD targets
# so every pixel of the visible zone accepts drops.
# ─────────────────────────────────────────────────────────────

def make_drop_zone(parent, text, height=90):
    zone = ctk.CTkFrame(
        parent,
        height=height,
        fg_color="#1A2030",
        border_color="#2A4060",
        border_width=2,
        corner_radius=12
    )
    zone.pack(fill="x", padx=0, pady=8)
    zone.pack_propagate(False)

    lbl = ctk.CTkLabel(
        zone,
        text=text,
        font=ctk.CTkFont(size=14),
        text_color="#5090C0"
    )
    lbl.place(relx=0.5, rely=0.5, anchor="center")

    return zone, lbl


def register_drop_zone(zone, lbl, handler):
    """Register both frame and label so the full area accepts drops."""
    zone.drop_target_register(DND_FILES)
    zone.dnd_bind("<<Drop>>", handler)
    lbl.drop_target_register(DND_FILES)
    lbl.dnd_bind("<<Drop>>", handler)


# ─────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────

class ProjectBundler(TkinterDnD.Tk):

    def __init__(self):
        super().__init__()
        self.title("Project Bundler v3")
        self.geometry("860x680")
        self.resizable(True, True)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.current_folder = None
        self.restore_bundle = None
        self.restore_dest   = None

        ctk.CTkLabel(
            self,
            text="PROJECT BUNDLER",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#00B4FF"
        ).pack(pady=(14, 4))

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(0, 14))

        for name in ("Archive", "Restore", "Library"):
            self.tabview.add(name)

        self.build_archive_tab()
        self.build_restore_tab()
        self.build_library_tab()

        LIBRARY_FOLDER.mkdir(exist_ok=True)

    # ══════════════════════════════════════════════════════════
    # ARCHIVE TAB
    # ══════════════════════════════════════════════════════════

    def build_archive_tab(self):
        tab   = self.tabview.tab("Archive")
        frame = ctk.CTkFrame(tab)
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        self.archive_drop_zone, self.archive_drop_lbl = make_drop_zone(
            frame, "➕  Drop project folder here"
        )
        register_drop_zone(
            self.archive_drop_zone,
            self.archive_drop_lbl,
            self.on_archive_drop
        )

        folder_row = ctk.CTkFrame(frame, fg_color="transparent")
        folder_row.pack(fill="x", pady=(0, 4))

        self.folder_label = ctk.CTkLabel(
            folder_row,
            text="No folder selected",
            text_color="#8899AA",
            anchor="w"
        )
        self.folder_label.pack(side="left", fill="x", expand=True, padx=4)

        ctk.CTkButton(
            folder_row,
            text="Browse…",
            width=100,
            command=self._browse_archive_folder
        ).pack(side="right", padx=4)

        self.delete_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            frame,
            text="Delete original folder ONLY after successful verification",
            variable=self.delete_var
        ).pack(anchor="w", padx=4, pady=6)

        self.go_btn = ctk.CTkButton(
            frame,
            text="🚀  Archive Project",
            height=44,
            state="disabled",
            command=self.start_archive_thread
        )
        self.go_btn.pack(fill="x", pady=8)

        self.progress = ctk.CTkProgressBar(frame)
        self.progress.set(0)
        self.progress.pack(fill="x", pady=(0, 4))

        self.status = ctk.CTkLabel(frame, text="Ready", text_color="#8899AA")
        self.status.pack(anchor="w", padx=4)

    def on_archive_drop(self, event):
        path = event.data.strip("{}")
        if Path(path).is_dir():
            self._set_archive_folder(path)

    def _browse_archive_folder(self):
        # Delay 10ms so button-press fully resolves before dialog opens
        self.after(10, self._do_browse_archive_folder)

    def _do_browse_archive_folder(self):
        folder = pick_folder(self, "Select project folder to archive")
        if folder:
            self._set_archive_folder(folder)

    def _set_archive_folder(self, path):
        self.current_folder = path
        short = path if len(path) < 72 else "…" + path[-70:]
        self.folder_label.configure(text=short, text_color="#CCDDEE")
        self.archive_drop_lbl.configure(text=f"📁  {Path(path).name}")
        self.go_btn.configure(state="normal")

    # ── archive engine ────────────────────────────────────────

    def start_archive_thread(self):
        self.go_btn.configure(state="disabled")
        threading.Thread(target=self._archive, daemon=True).start()

    def update_status(self, text, prog):
        self.after(0, lambda: (
            self.status.configure(text=text),
            self.progress.set(prog)
        ))

    def _archive(self):
        folder = Path(self.current_folder)
        files  = [f for f in folder.rglob("*") if f.is_file()]

        self.update_status("Scanning files…", 0.05)
        original_hashes = {
            str(f.relative_to(folder)): sha256_file(f) for f in files
        }

        tar_buf = io.BytesIO()
        self.update_status("Creating archive…", 0.3)
        with tarfile.open(fileobj=tar_buf, mode="w") as tar:
            for f in files:
                tar.add(f, arcname=f.relative_to(folder))

        self.update_status("Compressing…", 0.55)
        gzipped = gzip.compress(tar_buf.getvalue())
        encoded = base64.b64encode(gzipped).decode()

        self.update_status("Verifying integrity…", 0.75)
        decoded = gzip.decompress(base64.b64decode(encoded))
        with tarfile.open(fileobj=io.BytesIO(decoded)) as tar:
            for member in tar.getmembers():
                ex = tar.extractfile(member)
                if ex:
                    h = hashlib.sha256(ex.read()).hexdigest()
                    if original_hashes.get(member.name) != h:
                        self.after(0, lambda: messagebox.showerror(
                            "Error", "Verification FAILED — archive not saved."))
                        self.after(0, lambda: self.go_btn.configure(state="normal"))
                        return

        bundle_path = LIBRARY_FOLDER / f"{folder.name}.bundle.txt"
        counter = 2
        while bundle_path.exists():
            bundle_path = LIBRARY_FOLDER / f"{folder.name}_v{counter}.bundle.txt"
            counter += 1
        bundle_path.write_text(encoded)

        self.update_status("Verified ✓", 1.0)
        self.after(0, lambda: self.go_btn.configure(state="normal"))

        if self.delete_var.get():
            shutil.rmtree(folder)

        self.after(0, lambda: messagebox.showinfo(
            "Success", f"Archive verified 100%.\nSaved to:\n{bundle_path}"))
        self.after(0, self.load_library)

    # ══════════════════════════════════════════════════════════
    # RESTORE TAB
    # ══════════════════════════════════════════════════════════

    def build_restore_tab(self):
        tab   = self.tabview.tab("Restore")
        frame = ctk.CTkFrame(tab)
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(frame, text="Step 1 — Select Bundle",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=4)

        self.restore_drop_zone, self.restore_drop_lbl = make_drop_zone(
            frame, "📦  Drop .bundle.txt here"
        )
        register_drop_zone(
            self.restore_drop_zone,
            self.restore_drop_lbl,
            self.on_restore_drop
        )

        bundle_row = ctk.CTkFrame(frame, fg_color="transparent")
        bundle_row.pack(fill="x", pady=(0, 12))

        self.restore_bundle_label = ctk.CTkLabel(
            bundle_row,
            text="No bundle selected",
            text_color="#8899AA",
            anchor="w"
        )
        self.restore_bundle_label.pack(side="left", fill="x", expand=True, padx=4)

        ctk.CTkButton(
            bundle_row,
            text="Browse…",
            width=100,
            command=self._browse_restore_bundle
        ).pack(side="right", padx=4)

        ctk.CTkLabel(frame, text="Step 2 — Select Destination",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=4)

        dest_row = ctk.CTkFrame(frame, fg_color="transparent")
        dest_row.pack(fill="x", pady=4)

        self.restore_dest_label = ctk.CTkLabel(
            dest_row,
            text="No destination selected",
            text_color="#8899AA",
            anchor="w"
        )
        self.restore_dest_label.pack(side="left", fill="x", expand=True, padx=4)

        ctk.CTkButton(
            dest_row,
            text="Browse…",
            width=100,
            command=self._browse_restore_dest
        ).pack(side="right", padx=4)

        self.restore_go_btn = ctk.CTkButton(
            frame,
            text="📂  Restore Project",
            height=44,
            state="disabled",
            command=self.do_restore
        )
        self.restore_go_btn.pack(fill="x", pady=12)

        self.restore_status = ctk.CTkLabel(
            frame, text="", text_color="#8899AA")
        self.restore_status.pack(anchor="w", padx=4)

    def on_restore_drop(self, event):
        path = event.data.strip("{}")
        if path.endswith(".bundle.txt") and Path(path).is_file():
            self._set_restore_bundle(Path(path))

    def _browse_restore_bundle(self):
        self.after(10, self._do_browse_restore_bundle)

    def _do_browse_restore_bundle(self):
        f = pick_file(self, "Select bundle to restore")
        if f:
            self._set_restore_bundle(Path(f))

    def _browse_restore_dest(self):
        self.after(10, self._do_browse_restore_dest)

    def _do_browse_restore_dest(self):
        d = pick_folder(self, "Select destination folder")
        if d:
            self._set_restore_dest(d)

    def _set_restore_bundle(self, path):
        self.restore_bundle = path
        short = str(path) if len(str(path)) < 72 else "…" + str(path)[-70:]
        self.restore_bundle_label.configure(text=short, text_color="#CCDDEE")
        self.restore_drop_lbl.configure(text=f"📦  {path.name}")
        self._check_restore_ready()

    def _set_restore_dest(self, path):
        self.restore_dest = path
        short = path if len(path) < 72 else "…" + path[-70:]
        self.restore_dest_label.configure(text=short, text_color="#CCDDEE")
        self._check_restore_ready()

    def _check_restore_ready(self):
        if self.restore_bundle and self.restore_dest:
            self.restore_go_btn.configure(state="normal")

    def do_restore(self):
        self.restore_go_btn.configure(state="disabled")
        threading.Thread(
            target=self._restore,
            args=(self.restore_bundle, self.restore_dest),
            daemon=True
        ).start()

    def restore_specific(self, bundle):
        self._set_restore_bundle(bundle)
        self.tabview.set("Restore")

    def _restore(self, bundle, dest):
        try:
            self.after(0, lambda: self.restore_status.configure(
                text="Decoding…", text_color="#8899AA"))
            decoded = gzip.decompress(base64.b64decode(bundle.read_text()))
            out = Path(dest) / bundle.stem.replace(".bundle", "")
            out.mkdir(exist_ok=True)
            self.after(0, lambda: self.restore_status.configure(text="Extracting…"))
            with tarfile.open(fileobj=io.BytesIO(decoded)) as tar:
                tar.extractall(out)
            self.after(0, lambda: self.restore_status.configure(
                text="Done ✓", text_color="#44CC88"))
            self.after(0, lambda: messagebox.showinfo(
                "Restored", f"Restored to:\n{out}"))
        except Exception as e:
            self.after(0, lambda: self.restore_status.configure(
                text=f"Error: {e}", text_color="#FF4444"))
            self.after(0, lambda: messagebox.showerror("Restore Failed", str(e)))
        finally:
            self.after(0, lambda: self.restore_go_btn.configure(state="normal"))

    # ══════════════════════════════════════════════════════════
    # LIBRARY TAB
    # ══════════════════════════════════════════════════════════

    def build_library_tab(self):
        tab = self.tabview.tab("Library")

        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(10, 0))
        ctk.CTkLabel(top, text="Saved Bundles",
                     font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(top, text="⟳ Refresh", width=90,
                      command=self.load_library).pack(side="right")

        self.library = ctk.CTkScrollableFrame(tab)
        self.library.pack(fill="both", expand=True, padx=10, pady=8)
        self.load_library()

    def load_library(self):
        for w in self.library.winfo_children():
            w.destroy()

        bundles = sorted(
            LIBRARY_FOLDER.glob("*.bundle.txt"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        if not bundles:
            ctk.CTkLabel(
                self.library,
                text="No bundles yet — archive a project first.",
                text_color="#8899AA"
            ).pack(pady=30)
            return

        for bundle in bundles:
            self._library_row(bundle)

    def _library_row(self, bundle):
        row = ctk.CTkFrame(self.library, corner_radius=8)
        row.pack(fill="x", pady=3)

        size_kb = bundle.stat().st_size // 1024
        ctk.CTkLabel(
            row, text=f"  📦  {bundle.name}", anchor="w"
        ).pack(side="left", fill="x", expand=True, padx=6, pady=8)

        ctk.CTkLabel(
            row, text=f"{size_kb} KB", text_color="#8899AA", width=70
        ).pack(side="left")

        ctk.CTkButton(
            row, text="Restore", width=80,
            command=lambda b=bundle: self.restore_specific(b)
        ).pack(side="right", padx=4, pady=6)

        ctk.CTkButton(
            row, text="🗑", width=36,
            fg_color="#3A1A1A", hover_color="#6A2A2A", text_color="#FF6666",
            command=lambda b=bundle, r=row: self._delete_bundle(b, r)
        ).pack(side="right", padx=(0, 2), pady=6)

    def _delete_bundle(self, bundle, row):
        if messagebox.askyesno(
            "Delete Bundle",
            f"Permanently delete:\n{bundle.name}?\n\nThis cannot be undone."
        ):
            try:
                bundle.unlink()
                row.destroy()
            except Exception as e:
                messagebox.showerror("Delete Failed", str(e))


# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ProjectBundler()
    app.mainloop()
