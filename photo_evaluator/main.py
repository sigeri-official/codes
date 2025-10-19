import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageOps
import numpy as np
import os
from typing import Optional
import shutil

settings = {}

def try_float(val):
    try:
        return float(val)
    except:
        return val

class ImageAnalyzer:
    def __init__(self, display_label: tk.Label, result_vars: dict):
        self.display_label = display_label
        self.result_vars = result_vars
        self.image_path: Optional[str] = None
        self._tk_image = None
        self.pil_image: Optional[Image.Image] = None

    def load_image(self, path: str):
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        self.pil_image = Image.open(path).convert('RGB')
        self.image_path = path
        self._update_thumbnail()
        return self.analyze_image()

    def _update_thumbnail(self, size=(300, 200)):
        if self.pil_image is None:
            self.display_label.config(image='')
            return
        thumb = ImageOps.contain(self.pil_image, size)
        self._tk_image = ImageTk.PhotoImage(thumb)
        self.display_label.config(image=self._tk_image)

    def analyze_image(self, img=None):
        if self.pil_image is None and img is None:
            return
        if self.pil_image is None:
            self.pil_image = img

        arr = np.asarray(self.pil_image.convert('L'), dtype=np.float32) / 255.0
        avg_brightness, contrast = float(arr.mean()), float(arr.std())

        gy, gx = np.gradient(arr)
        sharpness = float(np.hypot(gx, gy).var())

        try:
            if 'brightness' in self.result_vars:
                self.result_vars['brightness'].set(f"{avg_brightness*100:.2f}")
            if 'contrast' in self.result_vars:
                self.result_vars['contrast'].set(f"{contrast*100:.2f}")
            if 'sharpness' in self.result_vars:
                self.result_vars['sharpness'].set(f"{sharpness*100000:.2f}")
        except:
            pass

        return {
            'brightness': avg_brightness * 100,
            'contrast': contrast * 100,
            'sharpness': sharpness * 100000
        }

class Filter:
    def filter_folder(self, path):
        global save_path
        image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tif')
        image_paths = [(os.path.join(path, f)).replace("\\", "/") for f in os.listdir(path) if f.lower().endswith(image_extensions)]
        for image in image_paths:
            if self.filter_pic(Image.open(image)):
                try:
                    shutil.copy2(image, save_path)
                except:
                    print(image)
                    print(save_path)
            else:
                pass
                print(save_path)
                shutil.copy2(image, save_path+"fos\\")

    def filter_pic(self, pic):
        global settings
        self.res_brightness = tk.StringVar(value='-')
        self.res_contrast = tk.StringVar(value='-')
        self.res_sharpness = tk.StringVar(value='-')
        result = ImageAnalyzer(pic, {
            'brightness': self.res_brightness,
            'contrast': self.res_contrast,
            'sharpness': self.res_sharpness,
        }).analyze_image(pic)
        #print(settings)
        #print(result)
        if (settings["min_expo"]() < result["brightness"] < settings["max_expo"]()
            and settings["min_contrast"]() < result["contrast"] < settings["max_contrast"]()
            and result["sharpness"] > settings["sharpness_limit"]()
            and settings["save_type"]() == "Jó képek mentése"):
            return True
        return False

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Photo evaluator by Sigeri')
        self.geometry('1000x450')

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=2)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=99999)

        self._create_settings_frame()
        self._create_main_frame()
        self._create_test_frame()
        self._create_log_frame()

    def _create_settings_frame(self):
        global save_path, settings
        frame = ttk.Frame(self, padding=8, relief='ridge')
        frame.grid(row=0, column=0, sticky='nsew')

        expo_frame = ttk.Frame(frame)
        expo_frame.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)
        ttk.Label(expo_frame, text='Expo', font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        self.expo = {"low": ttk.Entry(expo_frame), "high": ttk.Entry(expo_frame)}
        self.expo["low"].insert(0, 5); self.expo["low"].pack(fill='x')
        self.expo["high"].insert(0, 50); self.expo["high"].pack(fill='x')

        contrast_frame = ttk.Frame(frame)
        contrast_frame.grid(row=1, column=0, sticky='nsew', padx=4, pady=4)
        ttk.Label(contrast_frame, text='Constrast', font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        self.contrast = {"low": ttk.Entry(contrast_frame), "high": ttk.Entry(contrast_frame)}
        self.contrast["low"].insert(0, 5); self.contrast["low"].pack(fill='x')
        self.contrast["high"].insert(0, 30); self.contrast["high"].pack(fill='x')

        sharpness_frame = ttk.Frame(frame)
        sharpness_frame.grid(row=2, column=0, sticky='nsew', padx=4, pady=4)
        ttk.Label(sharpness_frame, text='Élesség', font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        self.sharpness = ttk.Entry(sharpness_frame)
        self.sharpness.insert(0, 10); self.sharpness.pack(fill='x')

        save_frame = ttk.Frame(frame)
        save_frame.grid(row=3, column=0, sticky='nsew', padx=4, pady=4)
        ttk.Label(save_frame, text='Mentés', font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        self.combo_var = tk.StringVar(value='Jó képek mentése')
        ttk.Combobox(save_frame, textvariable=self.combo_var,
                     values=['Rossz képek törlése', 'Jó képek mentése']).pack(anchor='w')
        def get_path():
            global save_path
            save_path = filedialog.askdirectory(title="Mentési mappa kiválasztása")
        ttk.Button(save_frame, text='Mentési mappa kiválasztása', command=get_path).pack(anchor='w', pady=4)

        self.ask_del = tk.BooleanVar(value=True)
        ttk.Checkbutton(save_frame, text='Kérdés törlésnél', variable=self.ask_del).pack(anchor='w')

        settings = {
            "min_expo": lambda: try_float(self.expo["low"].get()),
            "max_expo": lambda: try_float(self.expo["high"].get()),
            "min_contrast": lambda: try_float(self.contrast["low"].get()),
            "max_contrast": lambda: try_float(self.contrast["high"].get()),
            "sharpness_limit": lambda: try_float(self.sharpness.get()),
            "save_type": lambda: self.combo_var.get(),
            "save_path": lambda: save_path,
            "ask_before_del": lambda: self.ask_del.get()
        }

    def _create_main_frame(self):
        global settings
        frame = ttk.Frame(self, padding=8, relief='ridge')
        frame.grid(row=0, column=1, sticky='nsew')
        frame.columnconfigure(0, weight=1)

        read_btn = ttk.Frame(frame)
        read_btn.pack(anchor='w', pady=4)
        self.read_path = ""
        def get_path():
            self.read_path = tk.StringVar(value=str(filedialog.askdirectory(title="Olvasási mappa kiválasztása")))
            ttk.Label(read_btn, text=f'Olvasási mappa: {self.read_path.get()}').grid(row=1, column=0, sticky='w')
            settings["read_path"] = self.read_path.get()
            print(settings["read_path"])
        ttk.Button(read_btn, text='Olvasási mappa kiválasztása', command=get_path).grid(row=0, column=0, padx=2)
        ttk.Label(read_btn, textvariable=self.read_path).grid(row=1, column=1, sticky='w')
        ttk.Label(read_btn, text='Olvasási mappa:').grid(row=1, column=0, sticky='w')
    
        ttk.Button(frame, text='Szűrés futtatása', command=self.run).pack(anchor='w', pady=6)

    def _create_log_frame(self):
        frame = ttk.Frame(self, padding=8, relief='ridge')
        frame.grid(row=1, column=0, columnspan=3, sticky='nsew')
        frame.columnconfigure(0, weight=1)
        self.log = tk.Text(frame)
        self.log.pack(fill='both', expand=True)

    def _create_test_frame(self):
        frame = ttk.Frame(self, padding=8, relief='ridge')
        frame.grid(row=0, column=2, sticky='nsew')
        img_panel = ttk.Frame(frame); img_panel.pack(fill='both', expand=True)
        ttk.Label(img_panel, text='Kép betöltés és elemzés', font=('Segoe UI', 11, 'bold')).pack(anchor='w')

        self.thumb_label = ttk.Label(img_panel, text='(nincs kép)')
        self.thumb_label.pack(anchor='center', pady=6)

        results = ttk.Frame(img_panel); results.pack(anchor='w', pady=4, fill='x')
        self.res_brightness, self.res_contrast, self.res_sharpness = tk.StringVar(value='-'), tk.StringVar(value='-'), tk.StringVar(value='-')
        ttk.Label(results, text='Átlag fényerő:').grid(row=0, column=0, sticky='w')
        ttk.Label(results, textvariable=self.res_brightness).grid(row=0, column=1, sticky='w')
        ttk.Label(results, text='Kontraszt (std):').grid(row=1, column=0, sticky='w')
        ttk.Label(results, textvariable=self.res_contrast).grid(row=1, column=1, sticky='w')
        ttk.Label(results, text='Sharpness (var grad):').grid(row=2, column=0, sticky='w')
        ttk.Label(results, textvariable=self.res_sharpness).grid(row=2, column=1, sticky='w')

        self.image_analyzer = ImageAnalyzer(self.thumb_label, {
            'brightness': self.res_brightness,
            'contrast': self.res_contrast,
            'sharpness': self.res_sharpness,
        })

        ttk.Button(img_panel, text='Tallóz', command=self.browse_image).pack(anchor='center', pady=6)

    def run(self):
        Filter().filter_folder(settings["read_path"])
        self._log("Started")

    def browse_image(self):
        filetypes = [('Image files', '*.png *.jpg *.jpeg *.bmp *.tif'), ('All files', '*.*'), ('Köszi, hogy használod!', 'by.Sigeri')]
        path = filedialog.askopenfilename(title='Válassz egy képet', filetypes=filetypes)
        if not path:
            self._log('Kép tallózás megszakítva')
            return
        try:
            self.image_analyzer.load_image(path)
        except Exception as e:
            messagebox.showerror('Hiba', f'Hiba a kép betöltésekor:\n{e}')
            self._log(f'Hiba: {e}')

    def _log(self, text: str, level: str = 'info'):
        self.log.insert('end', f'[{level}] {text}\n')
        self.log.see('end')


if __name__ == '__main__':
    MainApp().mainloop()
