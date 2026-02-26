import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import yt_dlp
import threading
import os
import sys
import subprocess
import concurrent.futures
import urllib.request
import zipfile
import io
import time
from datetime import datetime

class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader Pro v6.0 Ultimate")
        self.root.geometry("1100x750")
        self.root.minsize(1000, 700)
        
        # Tema Ayarları
        self.style = ttk.Style()
        self.configure_styles()
        
        # Değişkenler
        self.download_path = os.path.join(os.path.expanduser("~"), "Desktop", "YouTube_Indirilenler")
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
            
        self.var_quality = tk.StringVar(value="720p (Standart)")
        self.var_subtitles = tk.BooleanVar(value=False)
        self.var_clipboard = tk.BooleanVar(value=True) # Otomatik Pano Takibi
        self.var_threads = tk.StringVar(value="3")     # Eşzamanlılık
        self.var_speed = tk.StringVar(value="Limitsiz") # Hız Limiti
        self.var_metadata = tk.BooleanVar(value=True)  # MP3 Meta Verisi
        self.var_schedule = tk.BooleanVar(value=False) # Zamanlayıcı
        self.var_schedule_time = tk.StringVar(value="03:00") # Zaman
        
        self.is_downloading = False
        self.queue_items = {} 
        self.last_clipboard = ""
        
        # Gelişmiş Motor Değişkenleri
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
        self.abort_flags = {}
        self.active_tasks = 0
        self.lock = threading.Lock()
        
        self.create_widgets()
        self.create_context_menu()
        
        # Pano (Clipboard) İzleyicisini Başlat
        self.root.after(1000, self.check_clipboard)

    def configure_styles(self):
        self.bg_color = "#f4f4f9"
        self.accent_color = "#d32f2f"
        self.root.configure(bg=self.bg_color)
        
        # KESİN ÇÖZÜM 1: Sadece clam teması kullanıldı. Vista'nın kırpma hataları önlendi.
        self.style.theme_use('clam')
            
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("TLabel", background=self.bg_color, font=("Segoe UI", 11))
        
        # Başlıklar için özel stiller
        self.style.configure("Header.TLabel", background=self.bg_color, font=("Segoe UI", 26, "bold"), foreground=self.accent_color)
        self.style.configure("SubHeader.TLabel", background=self.bg_color, font=("Segoe UI", 13), foreground="gray")
        self.style.configure("Status.TLabel", background=self.bg_color, font=("Segoe UI", 11, "italic"), foreground="#555")
        
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        self.style.configure("TLabelframe", background=self.bg_color)
        self.style.configure("TLabelframe.Label", background=self.bg_color, font=("Segoe UI", 11, "bold"), foreground="#444")
        self.style.configure("Treeview", font=("Segoe UI", 10), rowheight=30)
        self.style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"))
        
        # Checkbox'ların ezilmesini önleyen özel stil ayarı
        self.style.configure("TCheckbutton", background=self.bg_color, font=("Segoe UI", 10), padding=4)
        self.style.map("TCheckbutton", background=[("active", self.bg_color)])

    def create_widgets(self):
        # KESİN ÇÖZÜM 2: GÖMÜLME/EZİLME HATASINI ÖNLEYEN YERLEŞİM SIRASI (PACK ORDER)
        # Önce ÜST paneli, sonra ALT paneli ekrana sabitliyoruz. Kalan alanı (expand=True) tabloya veriyoruz.
        
        # --- 1. ÜST BAŞLIK (İlk Sırada Sabit) ---
        header_frame = ttk.Frame(self.root, padding="20 20 20 10")
        header_frame.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Label(header_frame, text="YouTube Downloader", style="Header.TLabel").pack(side=tk.LEFT)
        ttk.Label(header_frame, text="Pro v6.0 Ultimate", style="SubHeader.TLabel").pack(side=tk.LEFT, padx=15, pady=(10,0))
        
        ttk.Button(header_frame, text="🗗 Mini Moda Geç", command=self.enable_mini_mode).pack(side=tk.RIGHT)

        # --- 2. LINK EKLEME ALANI (İkinci Sırada Sabit) ---
        add_frame = ttk.Frame(self.root, padding="20 10 20 10")
        add_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.url_entry = ttk.Entry(add_frame, font=("Segoe UI", 12))
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15))
        self.url_entry.bind('<Return>', lambda event: self.add_to_queue())
        
        ttk.Button(add_frame, text="Kuyruğa Ekle", command=self.add_to_queue, width=15).pack(side=tk.RIGHT)
        ttk.Button(add_frame, text="Yapıştır", command=self.paste_link, width=10).pack(side=tk.RIGHT, padx=10)

        # --- 3. ALT KONTROL PANELİ (Üçüncü Sırada EN ALTA Sabitlendi! Asla ezilmez) ---
        bottom_frame = ttk.Frame(self.root, padding="15 20")
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        status_container = ttk.Frame(bottom_frame)
        status_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.global_status_label = ttk.Label(status_container, text="Kuyruğa video veya oynatma listesi ekleyin.", style="Status.TLabel")
        self.global_status_label.pack(anchor=tk.W, pady=(0, 5))
        
        sched_frame = ttk.Frame(status_container)
        sched_frame.pack(anchor=tk.W)
        ttk.Checkbutton(sched_frame, text="Zamanlanmış İndirme (Saat):", variable=self.var_schedule).pack(side=tk.LEFT)
        ttk.Entry(sched_frame, textvariable=self.var_schedule_time, width=8, font=("Segoe UI", 11)).pack(side=tk.LEFT, padx=5)

        btn_container = ttk.Frame(bottom_frame)
        btn_container.pack(side=tk.RIGHT, fill=tk.Y)

        self.download_btn = ttk.Button(btn_container, text="▶ Kuyruğu İndir", command=self.start_queue_download, style="TButton")
        self.download_btn.pack(side=tk.RIGHT, padx=(10, 0), ipadx=10, ipady=3)
        
        ttk.Button(btn_container, text="Klasörü Aç", command=self.open_download_folder).pack(side=tk.RIGHT, ipadx=5, ipady=3)

        # --- 4. ORTA BÖLÜM (AYARLAR VE KUYRUK TABLOSU) ---
        # Bu alan kalan tüm boşluğu (expand=True) alacak, böylece diğer paneller güvende olacak.
        main_frame = ttk.Frame(self.root, padding="20 10 20 10")
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # SOL PANEL: Ayarlar
        settings_panel = ttk.Frame(main_frame, width=300)
        settings_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 20))
        
        # Konum
        folder_frame = ttk.LabelFrame(settings_panel, text="Kayıt Yeri", padding="10")
        folder_frame.pack(fill=tk.X, pady=(0, 10))
        self.path_label = ttk.Label(folder_frame, text=self.get_short_path(self.download_path), foreground="#1976D2", cursor="hand2")
        self.path_label.pack(fill=tk.X, pady=(0, 5))
        self.path_label.bind("<Button-1>", lambda e: self.browse_folder())
        ttk.Button(folder_frame, text="Değiştir...", command=self.browse_folder).pack(anchor=tk.W)

        # Çözünürlük ve Format
        quality_frame = ttk.LabelFrame(settings_panel, text="Çözünürlük / Format", padding="10")
        quality_frame.pack(fill=tk.X, pady=(0, 10))
        
        qualities = ["En İyi (1080p+)", "720p (Standart)", "480p (Düşük Boyut)", "Sadece Ses (M4A)"]
        self.quality_combo = ttk.Combobox(quality_frame, textvariable=self.var_quality, values=qualities, state="readonly", font=("Segoe UI", 11))
        self.quality_combo.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(quality_frame, text="* 1080p birleştirme için FFmpeg gereklidir.", font=("Segoe UI", 9), foreground="gray").pack(anchor=tk.W)

        # Sistem ve Performans Ayarları
        sys_frame = ttk.LabelFrame(settings_panel, text="Sistem ve Performans", padding="10")
        sys_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(sys_frame, text="Eşzamanlı İndirme:", font=("Segoe UI", 10)).pack(anchor=tk.W)
        self.threads_combo = ttk.Combobox(sys_frame, textvariable=self.var_threads, values=["1", "2", "3", "5"], state="readonly", width=10)
        self.threads_combo.pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Label(sys_frame, text="Hız Limiti:", font=("Segoe UI", 10)).pack(anchor=tk.W)
        self.speed_combo = ttk.Combobox(sys_frame, textvariable=self.var_speed, values=["Limitsiz", "500 KB/s", "1 MB/s", "5 MB/s", "10 MB/s"], state="readonly", width=15)
        self.speed_combo.pack(anchor=tk.W, pady=(0, 5))
        
        btn_frame = ttk.Frame(sys_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(btn_frame, text="⟳ Motoru Güncelle", command=self.update_motor).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(btn_frame, text="⚙️ FFmpeg Kur", command=self.install_ffmpeg).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Ekstra Ayarlar
        extra_frame = ttk.LabelFrame(settings_panel, text="Ekstra Seçenekler", padding="10")
        extra_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Checkbutton(extra_frame, text="Altyazıları İndir (TR/EN)", variable=self.var_subtitles).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(extra_frame, text="Müzik Meta Verisi (Albüm)", variable=self.var_metadata).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(extra_frame, text="Otomatik Link Yakala (Pano)", variable=self.var_clipboard).pack(anchor=tk.W, pady=2)

        # SAĞ PANEL: Kuyruk Tablosu
        queue_frame = ttk.LabelFrame(main_frame, text="İndirme Kuyruğu (Sağ tık menüsü mevcuttur)", padding="10")
        queue_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tree_btn_frame = ttk.Frame(queue_frame)
        tree_btn_frame.pack(fill=tk.X, pady=(10, 0), side=tk.BOTTOM)
        ttk.Button(tree_btn_frame, text="Seçileni Sil/İptal Et", command=self.remove_selected).pack(side=tk.LEFT)
        ttk.Button(tree_btn_frame, text="Kuyruğu Temizle", command=self.clear_queue).pack(side=tk.LEFT, padx=10)

        tree_container = ttk.Frame(queue_frame)
        tree_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        columns = ("title", "status", "size", "progress", "speed")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="headings")
        
        self.tree.heading("title", text="Video Başlığı")
        self.tree.heading("status", text="Durum")
        self.tree.heading("size", text="Boyut")
        self.tree.heading("progress", text="İlerleme")
        self.tree.heading("speed", text="Hız")
        
        self.tree.column("title", minwidth=250, anchor=tk.W)
        self.tree.column("status", width=120, minwidth=120, anchor=tk.CENTER, stretch=False)
        self.tree.column("size", width=90, minwidth=90, anchor=tk.CENTER, stretch=False)
        self.tree.column("progress", width=90, minwidth=90, anchor=tk.CENTER, stretch=False)
        self.tree.column("speed", width=90, minwidth=90, anchor=tk.CENTER, stretch=False)
        
        scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.tree.bind("<Configure>", self.resize_tree_columns)

    def resize_tree_columns(self, event):
        # Toplam genişlikten diğer sütunların genişliğini çıkar, kalanı Video Başlığına ver
        other_widths = 120 + 90 + 90 + 90
        available_width = event.width - other_widths - 10
        if available_width > 200:
            self.tree.column("title", width=available_width)

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0, font=("Segoe UI", 10))
        self.context_menu.add_command(label="İptal Et / Durdur", command=self.cancel_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Listeden Sil", command=self.remove_selected)
        self.tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def check_clipboard(self):
        if self.var_clipboard.get():
            try:
                current_clip = self.root.clipboard_get().strip()
                if current_clip != self.last_clipboard:
                    self.last_clipboard = current_clip
                    valid_domains = ["youtu", "instagram", "tiktok", "twitter", "x.com", "facebook", "vimeo"]
                    if current_clip.startswith("http") and any(domain in current_clip for domain in valid_domains):
                        if messagebox.askyesno("Yeni Link Algılandı", f"Panoda desteklenen bir video bağlantısı algılandı.\nKuyruğa eklemek ister misiniz?\n\n{current_clip[:60]}..."):
                            self.url_entry.delete(0, tk.END)
                            self.url_entry.insert(0, current_clip)
                            self.add_to_queue()
            except:
                pass
        self.root.after(1500, self.check_clipboard)

    def update_motor(self):
        self.global_status_label.config(text="İndirme motoru güncelleniyor, lütfen bekleyin...", foreground="orange")
        threading.Thread(target=self._update_motor_thread, daemon=True).start()

    def _update_motor_thread(self):
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"], check=True, startupinfo=startupinfo)
            self.root.after(0, lambda: messagebox.showinfo("Başarılı", "İndirme motoru (yt-dlp) başarıyla en güncel sürüme yükseltildi!"))
            self.root.after(0, lambda: self.global_status_label.config(text="Motor güncel.", foreground="green"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Hata", f"Güncelleme başarısız oldu:\n{e}"))
            self.root.after(0, lambda: self.global_status_label.config(text="Güncelleme hatası.", foreground="red"))

    def install_ffmpeg(self):
        if os.path.exists("ffmpeg/bin/ffmpeg.exe"):
            messagebox.showinfo("Bilgi", "FFmpeg zaten sisteminizde (ffmpeg/bin/) kurulu ve hazır!")
            return
            
        if not messagebox.askyesno("FFmpeg Kurulumu", "1080p birleştirme ve MP3 dönüşümleri için FFmpeg indirilecek. Bu işlem internet hızınıza bağlı olarak birkaç dakika sürebilir.\n\nOnaylıyor musunuz?"):
            return
            
        self.global_status_label.config(text="FFmpeg indiriliyor, lütfen programı kapatmayın...", foreground="blue")
        threading.Thread(target=self._install_ffmpeg_thread, daemon=True).start()

    def _install_ffmpeg_thread(self):
        try:
            url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            
            with urllib.request.urlopen(req) as response:
                total_length = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunk_size = 8192
                data = bytearray()
                
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk: break
                    data.extend(chunk)
                    downloaded += len(chunk)
                    if total_length:
                        percent = (downloaded / total_length) * 100
                        self.root.after(0, lambda p=percent: self.global_status_label.config(text=f"FFmpeg İndiriliyor: %{p:.1f}", foreground="orange"))
            
            self.root.after(0, lambda: self.global_status_label.config(text="Arşiv çıkartılıyor...", foreground="orange"))
            
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                os.makedirs("ffmpeg/bin", exist_ok=True)
                for file_info in z.infolist():
                    if file_info.filename.endswith("ffmpeg.exe") or file_info.filename.endswith("ffprobe.exe"):
                        file_info.filename = os.path.basename(file_info.filename)
                        z.extract(file_info, "ffmpeg/bin")
                        
            self.root.after(0, lambda: messagebox.showinfo("Başarılı", "FFmpeg başarıyla kuruldu! Artık 1080p videolar ve MP3'ler sorunsuz işlenebilir."))
            self.root.after(0, lambda: self.global_status_label.config(text="FFmpeg hazır.", foreground="green"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Hata", f"FFmpeg indirilirken hata oluştu:\n{e}\n\nLütfen manuel olarak kurmayı deneyin."))
            self.root.after(0, lambda: self.global_status_label.config(text="FFmpeg kurulum hatası.", foreground="red"))

    def enable_mini_mode(self):
        self.root.withdraw()
        
        self.mini_win = tk.Toplevel(self.root)
        self.mini_win.title("Mini Mod")
        self.mini_win.geometry("150x150")
        self.mini_win.attributes("-topmost", True)
        self.mini_win.configure(bg=self.bg_color)
        self.mini_win.protocol("WM_DELETE_WINDOW", self.disable_mini_mode)
        
        frame = ttk.Frame(self.mini_win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        lbl = ttk.Label(frame, text="Universal\nDropzone", font=("Segoe UI", 12, "bold"), foreground=self.accent_color, justify=tk.CENTER)
        lbl.pack(pady=(10, 5))
        
        ttk.Label(frame, text="Panodaki Linki\nEklemek İçin Tıkla", font=("Segoe UI", 9), justify=tk.CENTER).pack(pady=5)
        
        btn = ttk.Button(frame, text="Tam Ekran", command=self.disable_mini_mode)
        btn.pack(side=tk.BOTTOM, fill=tk.X)
        
        lbl.bind("<Button-1>", lambda e: self._mini_mode_add())
        frame.bind("<Button-1>", lambda e: self._mini_mode_add())

    def _mini_mode_add(self):
        try:
            clip = self.root.clipboard_get()
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, clip)
            self.add_to_queue()
            messagebox.showinfo("Mini Mod", "Link başarıyla kuyruğa eklendi!", parent=self.mini_win)
        except:
            messagebox.showwarning("Hata", "Panoda metin bulunamadı.", parent=self.mini_win)

    def disable_mini_mode(self):
        self.mini_win.destroy()
        self.root.deiconify()

    def get_short_path(self, path):
        return "..." + path[-40:] if len(path) > 43 else path

    def paste_link(self):
        try:
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, self.root.clipboard_get())
        except:
            pass

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_path = folder
            self.path_label.config(text=self.get_short_path(self.download_path))

    def cancel_selected(self):
        for selected_id in self.tree.selection():
            status = self.tree.item(selected_id, "values")[1]
            if status in ["İndiriliyor...", "Kuyrukta", "Bekliyor", "İşleniyor..."]:
                self.abort_flags[selected_id] = True
                self.update_tree_item(selected_id, status="İptal Edildi", progress="-", speed="-")

    def remove_selected(self):
        for selected_id in self.tree.selection():
            self.abort_flags[selected_id] = True
            self.tree.delete(selected_id)
            if selected_id in self.queue_items:
                del self.queue_items[selected_id]

    def clear_queue(self):
        for item_id in self.tree.get_children():
            self.abort_flags[item_id] = True
            self.tree.delete(item_id)
        self.queue_items.clear()

    def add_to_queue(self):
        url = self.url_entry.get().strip()
        if not url: return
        
        self.url_entry.delete(0, tk.END)
        self.global_status_label.config(text="Link analiz ediliyor (Oynatma listesi ise biraz sürebilir)...", foreground="blue")
        
        threading.Thread(target=self.analyze_link_thread, args=(url,), daemon=True).start()

    def analyze_link_thread(self, url):
        ydl_opts = {'quiet': True, 'extract_flat': True, 'no_warnings': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'entries' in info:
                    entries = list(info['entries'])
                    for entry in entries:
                        if entry:
                            self.root.after(0, self.insert_to_tree, entry.get('url') or entry.get('webpage_url', url), entry.get('title', 'Bilinmeyen Video'))
                    self.root.after(0, lambda: self.global_status_label.config(text=f"{len(entries)} video kuyruğa eklendi.", foreground="green"))
                else:
                    title = info.get('title', 'Bilinmeyen Video')
                    self.root.after(0, self.insert_to_tree, url, title)
                    self.root.after(0, lambda: self.global_status_label.config(text="Video kuyruğa eklendi.", foreground="green"))
                    
        except Exception as e:
            self.root.after(0, lambda: self.global_status_label.config(text=f"Analiz Hatası: Link geçersiz veya gizli.", foreground="red"))

    def insert_to_tree(self, url, title):
        item_id = self.tree.insert("", tk.END, values=(title, "Bekliyor", "-", "%0", "-"))
        self.abort_flags[item_id] = False
        self.queue_items[item_id] = {'url': url, 'title': title}

    def start_queue_download(self, bypass_schedule=False):
        if self.var_schedule.get() and not bypass_schedule:
            target_time = self.var_schedule_time.get()
            self.download_btn.config(state="disabled", text=f"⏳ {target_time} Bekleniyor")
            self.global_status_label.config(text=f"İndirme işlemleri saat {target_time} olduğunda otomatik başlayacak.", foreground="orange")
            threading.Thread(target=self._scheduler_thread, args=(target_time,), daemon=True).start()
            return

        if self.active_tasks == 0:
            workers = int(self.var_threads.get())
            self.executor.shutdown(wait=False)
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=workers)

        pending = [item for item in self.tree.get_children() if self.tree.item(item, "values")[1] in ["Bekliyor", "Hata"]]
        if not pending:
            messagebox.showinfo("Bilgi", "İndirilecek video bulunamadı veya tümü tamamlandı.")
            return

        self.download_btn.config(state="disabled", text="⏳ İşlemde...")
        self.global_status_label.config(text="Kuyruk arka planda eşzamanlı olarak işleniyor...", foreground="blue")
        
        for item_id in pending:
            self.update_tree_item(item_id, status="Kuyrukta")
            self.abort_flags[item_id] = False
            
            with self.lock:
                self.active_tasks += 1
            self.executor.submit(self.download_single_item, item_id)

    def _scheduler_thread(self, target_time):
        while self.var_schedule.get():
            current_time = datetime.now().strftime("%H:%M")
            if current_time == target_time:
                self.root.after(0, lambda: self.start_queue_download(bypass_schedule=True))
                break
            time.sleep(10)

    def download_single_item(self, item_id):
        if item_id not in self.queue_items:
            self.finalize_task()
            return
            
        if self.abort_flags.get(item_id):
            self.finalize_task()
            return

        url = self.queue_items[item_id]['url']
        self.root.after(0, lambda: self.update_tree_item(item_id, status="İndiriliyor...", progress="%0"))
        
        try:
            ydl_opts = self.build_ydl_options(item_id)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if not self.abort_flags.get(item_id):
                self.root.after(0, lambda: self.update_tree_item(item_id, status="Tamamlandı", progress="%100", speed="-"))
        except Exception as e:
            if "ABORTED_BY_USER" not in str(e):
                self.root.after(0, lambda: self.update_tree_item(item_id, status="Hata!", progress="-", speed="-"))
        finally:
            self.finalize_task() # GÜVENLİK KİLİDİ: Hata çıksa bile kuyruğun donmasını engeller ve sıradakine geçer

    def finalize_task(self):
        with self.lock:
            self.active_tasks -= 1
            if self.active_tasks == 0:
                self.root.after(0, self.finish_queue)

    def build_ydl_options(self, item_id):
        opts = {
            'outtmpl': f'{self.download_path}/%(title)s [%(id)s].%(ext)s',
            'progress_hooks': [self.get_progress_hook(item_id)],
            'ignoreerrors': True,
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [] # DÜZELTME: Bu satır eklendi (Sessiz çökme buradan kaynaklanıyordu)
        }

        if os.path.exists("ffmpeg/bin"):
            opts['ffmpeg_location'] = "ffmpeg/bin"

        quality = self.var_quality.get()
        if "Sadece Ses" in quality:
            opts['format'] = 'bestaudio/best'
        elif "1080p" in quality:
            opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        elif "720p" in quality:
            opts['format'] = 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best'
        elif "480p" in quality:
            opts['format'] = 'bestvideo[ext=mp4][height<=480]+bestaudio[ext=m4a]/best[ext=mp4][height<=480]/best'

        limit_str = self.var_speed.get()
        if limit_str == "500 KB/s": opts['ratelimit'] = 500 * 1024
        elif limit_str == "1 MB/s": opts['ratelimit'] = 1024 * 1024
        elif limit_str == "5 MB/s": opts['ratelimit'] = 5 * 1024 * 1024
        elif limit_str == "10 MB/s": opts['ratelimit'] = 10 * 1024 * 1024

        if self.var_subtitles.get():
            opts['writesubtitles'] = True
            opts['writeautomaticsub'] = True
            opts['subtitleslangs'] = ['tr', 'en']
            opts['subtitlesformat'] = 'srt/vtt/best'

        if self.var_metadata.get():
            opts['postprocessors'].append({'key': 'FFmpegMetadata', 'add_metadata': True})

        return opts

    def get_progress_hook(self, item_id):
        def hook(d):
            if self.abort_flags.get(item_id, False):
                raise Exception("ABORTED_BY_USER")

            if d['status'] == 'downloading':
                try:
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    downloaded = d.get('downloaded_bytes', 0)
                    
                    percent = (downloaded / total) * 100 if total > 0 else 0
                    speed = d.get('_speed_str', '-')
                    size_str = self.format_bytes(total) if total > 0 else "-"
                    
                    self.root.after(0, lambda: self.update_tree_item(item_id, size=size_str, progress=f"%{percent:.1f}", speed=speed))
                except:
                    pass
            elif d['status'] == 'finished':
                self.root.after(0, lambda: self.update_tree_item(item_id, status="İşleniyor...", speed="-"))
        return hook

    def update_tree_item(self, item_id, status=None, size=None, progress=None, speed=None):
        if not self.tree.exists(item_id): return
        
        current_values = list(self.tree.item(item_id, "values"))
        if status is not None: current_values[1] = status
        if size is not None: current_values[2] = size
        if progress is not None: current_values[3] = progress
        if speed is not None: current_values[4] = speed
        
        self.tree.item(item_id, values=current_values)

    def format_bytes(self, size):
        power = 2**10
        n = 0
        labels = {0: '', 1: 'KB', 2: 'MB', 3: 'GB'}
        while size > power and n < 3:
            size /= power
            n += 1
        return f"{size:.1f} {labels.get(n, '')}"

    def finish_queue(self):
        self.download_btn.config(state="normal", text="▶ Kuyruğu İndir")
        
        pending = [item for item in self.tree.get_children() if self.tree.item(item, "values")[1] in ["Bekliyor", "Kuyrukta"]]
        if not pending:
            self.global_status_label.config(text="✅ Tüm indirme işlemleri tamamlandı!", foreground="green")
        else:
            self.global_status_label.config(text="Bazı işlemler iptal edildi veya bekliyor.", foreground="gray")

    def open_download_folder(self):
        try:
            os.startfile(self.download_path)
        except:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()