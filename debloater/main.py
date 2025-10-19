import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading

# PowerShellből appok listázása
def get_packages():
    result = subprocess.run(
        ["powershell", "Get-AppxPackage | Select Name"],
        capture_output=True, text=True
    )
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip() and not line.startswith("Name")]
    return lines

# Appok eltávolítása PowerShell segítségével
def remove_packages(selected):
    for pkg in selected:
        cmd = f'powershell Get-AppxPackage *{pkg}* | Remove-AppxPackage'
        subprocess.run(cmd, shell=True)

# Betölti az appokat a listába
def load_packages():
    load_btn.config(state="disabled")
    packages = get_packages()[1:]
    packages = [package for package in packages if package.split(".")[0] == "Microsoft"]
    for widget in list_frame.winfo_children():
        widget.destroy()
    checkboxes.clear()
    for name in packages:
        var = tk.BooleanVar()
        chk = tk.Checkbutton(list_frame, text=name, variable=var, anchor="w", width=60)
        chk.var = var
        chk.pack(fill="x")
        checkboxes.append((name, var))
    load_btn.config(state="normal")

# Törlés threadben
def start_removal():
    selected = [name for name, var in checkboxes if var.get()]
    if not selected:
        messagebox.showinfo("Info", "Nem pipáltál be semmit.")
    else:
        threading.Thread(target=lambda: remove_packages(selected)).start()
        messagebox.showinfo("Kész", "Eltávolítás folyamatban...")
    subprocess.run("sysdm.cpl", shell=True)

# Preset kiválasztása legördülőből
def apply_preset(*args):
    preset = preset_var.get()
    targets = presets.get(preset, [])
    for name, var in checkboxes:
        var.set(any(t.lower() in name.lower() for t in targets))

# Presetek listája
presets = {
    "potato": ["Xbox", "YourPhone", "People", "ZuneMusic", "BingNews", "Weather", "Edge", "OneDrive"],
    "performance": ["Xbox", "YourPhone", "People", "Cortana", "Copilot", "Edge", "OneDrive"],
    "balanced": ["Cortana", "Copilot", "Edge"],
    "antivirus_only": ["Cortana", "Copilot"]
}

# GUI
root = tk.Tk()
root.title("Windows Debloater GUI")
root.geometry("520x600")

# Preset dropdown
preset_var = tk.StringVar()
preset_var.trace("w", apply_preset)
ttk.Label(root, text="Preset:").pack(pady=3)
preset_combo = ttk.Combobox(root, textvariable=preset_var, values=list(presets.keys()), state="readonly", width=20)
preset_combo.pack(pady=3)

# Betöltés gomb
load_btn = ttk.Button(root, text="Appok betöltése", command=load_packages)
load_btn.pack(pady=5)

# Görgethető lista
canvas = tk.Canvas(root)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollbar.pack(side="right", fill="y")

scrollable_frame = ttk.Frame(canvas)
list_frame = ttk.Frame(scrollable_frame)
list_frame.pack(fill="both", expand=True)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(fill="both", expand=True)

checkboxes = []

def on_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))
scrollable_frame.bind("<Configure>", on_configure)

# Tisztítás indítása gomb
start_btn = ttk.Button(root, text="Tisztítás indítása", command=start_removal)
start_btn.pack(pady=10)

root.mainloop()
