import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import yt_dlp
import os
import shutil
import sys
import urllib.request
import zipfile

FFMPEG_URL = "https://github.com/btbn/ffmpeg-builds/releases/download/autobuild-2026-03-17-13-11/ffmpeg-master-latest-win64-gpl.zip"

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube视频下载器")
        self.root.geometry("650x550")
        self.root.resizable(False, False)

        self.url_entry = None
        self.progress_bar = None
        self.status_label = None
        self.download_thread = None
        self.format_var = None
        self.quality_var = None
        self.bitrate_var = None
        self.quality_combo = None
        self.bitrate_combo = None
        self.batch_listbox = None
        self.batch_progress = None

        self.ffmpeg_path = self.find_ffmpeg()
        self.setup_ui()

    def setup_ui(self):
        self.root.title("YouTube视频下载器")
        
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.single_frame = ttk.Frame(self.root, padding="10")
        self.batch_frame = ttk.Frame(self.root, padding="10")
        
        notebook.add(self.single_frame, text="单文件下载")
        notebook.add(self.batch_frame, text="批量下载")
        
        self.setup_single_ui()
        self.setup_batch_ui()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_single_ui(self):
        title_label = ttk.Label(self.single_frame, text="YouTube视频下载器", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 15))

        url_frame = ttk.Frame(self.single_frame)
        url_frame.pack(fill=tk.X, pady=8)

        ttk.Label(url_frame, text="视频链接:", font=("Arial", 11)).pack(side=tk.LEFT)

        self.url_entry = ttk.Entry(url_frame, font=("Arial", 11), width=40)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        format_frame = ttk.Frame(self.single_frame)
        format_frame.pack(pady=8)

        ttk.Label(format_frame, text="下载格式:", font=("Arial", 11)).pack(side=tk.LEFT)

        self.format_var = tk.StringVar(value="mp4")
        formats = [
            ("MP4视频", "mp4"),
            ("MP3音频", "mp3"),
            ("WEBM视频", "webm"),
        ]
        for text, value in formats:
            ttk.Radiobutton(format_frame, text=text, variable=self.format_var, value=value, command=self.update_quality_options).pack(side=tk.LEFT, padx=8)

        quality_frame = ttk.Frame(self.single_frame)
        quality_frame.pack(pady=8)

        ttk.Label(quality_frame, text="视频质量:", font=("Arial", 11)).pack(side=tk.LEFT)
        
        self.quality_var = tk.StringVar(value="best")
        self.quality_combo = ttk.Combobox(quality_frame, textvariable=self.quality_var, width=15, state="readonly")
        self.quality_combo['values'] = ("最高", "1080p", "720p", "480p", "360p", "最低")
        self.quality_combo.current(0)
        self.quality_combo.pack(side=tk.LEFT, padx=10)

        ttk.Label(quality_frame, text="MP3码率:", font=("Arial", 11)).pack(side=tk.LEFT, padx=(20, 0))
        
        self.bitrate_var = tk.StringVar(value="192")
        self.bitrate_combo = ttk.Combobox(quality_frame, textvariable=self.bitrate_var, width=10, state="readonly")
        self.bitrate_combo['values'] = ("320", "256", "192", "128", "64")
        self.bitrate_combo.current(2)
        self.bitrate_combo.pack(side=tk.LEFT, padx=10)
        self.quality_combo.bind("<<ComboboxSelected>>", lambda e: self.update_quality_options())

        self.progress_bar = ttk.Progressbar(self.single_frame, mode='determinate', length=400)
        self.progress_bar.pack(pady=10)

        self.status_label = ttk.Label(self.single_frame, text="就绪", font=("Arial", 10))
        self.status_label.pack(pady=5)

        btn_frame = ttk.Frame(self.single_frame)
        btn_frame.pack(pady=10)

        download_btn = ttk.Button(btn_frame, text="下载视频", command=self.start_download)
        download_btn.pack(side=tk.LEFT, padx=10)

        clear_btn = ttk.Button(btn_frame, text="清空", command=self.clear_input)
        clear_btn.pack(side=tk.LEFT, padx=10)

    def update_quality_options(self):
        selected = self.format_var.get()
        if selected == "mp3":
            self.quality_combo.config(state="disabled")
            self.bitrate_combo.config(state="readonly")
        else:
            self.quality_combo.config(state="readonly")
            self.bitrate_combo.config(state="disabled")

    def setup_batch_ui(self):
        title_label = ttk.Label(self.batch_frame, text="批量下载", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        info_label = ttk.Label(self.batch_frame, text="选择包含下载地址的txt文件（每行一个地址）", font=("Arial", 9))
        info_label.pack(pady=5)
        
        select_file_btn = ttk.Button(self.batch_frame, text="选择文件", command=self.select_batch_file)
        select_file_btn.pack(pady=5)
        
        self.batch_listbox = tk.Listbox(self.batch_frame, height=10, width=60, font=("Arial", 9))
        self.batch_listbox.pack(pady=5)
        
        scrollbar = ttk.Scrollbar(self.batch_frame, orient=tk.VERTICAL, command=self.batch_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.batch_listbox.config(yscrollcommand=scrollbar.set)
        
        self.batch_progress = ttk.Progressbar(self.batch_frame, mode='determinate', length=400)
        self.batch_progress.pack(pady=10)
        
        self.batch_status_label = ttk.Label(self.batch_frame, text="未选择文件", font=("Arial", 10))
        self.batch_status_label.pack(pady=5)
        
        btn_frame = ttk.Frame(self.batch_frame)
        btn_frame.pack(pady=10)
        
        batch_download_btn = ttk.Button(btn_frame, text="开始批量下载", command=self.start_batch_download)
        batch_download_btn.pack(side=tk.LEFT, padx=10)
        
        clear_batch_btn = ttk.Button(btn_frame, text="清空列表", command=self.clear_batch_list)
        clear_batch_btn.pack(side=tk.LEFT, padx=10)

    def clear_input(self):
        self.url_entry.delete(0, tk.END)
        self.progress_bar['value'] = 0
        self.status_label.config(text="就绪")

    def start_download(self):
        url = self.url_entry.get().strip()
        selected_format = self.format_var.get()
        
        if not url:
            messagebox.showwarning("警告", "请输入视频链接")
            return

        if "youtube.com" not in url and "youtu.be" not in url:
            messagebox.showwarning("警告", "请输入有效的YouTube链接")
            return

        folder_selected = filedialog.askdirectory(title="选择保存位置")
        
        if not folder_selected:
            return

        self.status_label.config(text="下载中...")
        
        quality_map = {"最高": "best", "1080p": "bestvideo[height<=1080]+bestaudio/best", "720p": "bestvideo[height<=720]+bestaudio/best", "480p": "bestvideo[height<=480]+bestaudio/best", "360p": "bestvideo[height<=360]+bestaudio/best", "最低": "worst"}
        bitrate_map = {"320": "320", "256": "256", "192": "192", "128": "128", "64": "64"}
        
        def download_thread():
            try:
                if selected_format == "mp3":
                    ffmpeg_path = self.download_and_extract_ffmpeg() if not self.find_ffmpeg() else self.find_ffmpeg()
                    if not ffmpeg_path:
                        self.root.after(0, messagebox.showerror, "错误", "下载 MP3 需要 FFmpeg。请安装 FFmpeg 或将 ffmpeg.exe 放到程序目录的 ffmpeg_bin 文件夹中。")
                        return
                    bitrate = self.bitrate_var.get()
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': os.path.join(folder_selected, '%(title)s.%(ext)s'),
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': bitrate,
                        }],
                        'ffmpeg_location': ffmpeg_path,
                        'quiet': True,
                    }
                else:
                    quality = self.quality_var.get()
                    video_format = quality_map.get(quality, "best")
                    ydl_opts = {
                        'format': video_format,
                        'outtmpl': os.path.join(folder_selected, '%(title)s.%(ext)s'),
                        'quiet': True,
                    }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    video_title = info.get('title', '视频')
                    self.root.after(0, self.download_complete, True, video_title)
            except Exception as e:
                self.root.after(0, self.download_complete, False, str(e))

        self.download_thread = threading.Thread(target=download_thread)
        self.download_thread.daemon = True
        self.download_thread.start()

    def download_video(self, url, output_path, selected_format):
        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    percent = (downloaded / total) * 100
                    self.root.after(0, self.update_progress, percent)
                    self.root.after(0, self.update_status, f"下载中: {percent:.1f}%")
            elif d['status'] == 'finished':
                self.root.after(0, self.update_status, "处理中...")

        if selected_format == "mp3":
            ffmpeg_path = self.download_and_extract_ffmpeg() if not self.find_ffmpeg() else self.find_ffmpeg()
            if not ffmpeg_path:
                self.root.after(0, messagebox.showerror, "错误", "下载 MP3 需要 FFmpeg。\n请将 ffmpeg.exe 和 ffprobe.exe 放到程序同目录的 ffmpeg_bin 文件夹中，或安装 FFmpeg。")
                self.root.after(0, self.update_status, "需要 FFmpeg")
                return
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'ffmpeg_location': ffmpeg_path,
                'quiet': True,
            }
        else:
            ffmpeg_path = self.find_ffmpeg()
            ydl_opts = {
                'format': 'best',
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'ffmpeg_location': ffmpeg_path,
                'quiet': True,
            }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_title = info.get('title', '视频')
                self.root.after(0, self.download_complete, True, video_title)
        except Exception as e:
            self.root.after(0, self.download_complete, False, str(e))

    def update_progress(self, value):
        self.progress_bar['value'] = value

    def update_status(self, text):
        self.status_label.config(text=text)

    def download_complete(self, success, message):
        self.progress_bar['value'] = 100
        if success:
            self.status_label.config(text="下载完成!")
            messagebox.showinfo("成功", f"视频已下载: {message}")
        else:
            self.status_label.config(text="下载失败")
            messagebox.showerror("错误", f"下载失败: {message}")
        self.progress_bar['value'] = 0

    def select_batch_file(self):
        file_path = filedialog.askopenfilename(
            title="选择下载地址文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            self.batch_listbox.delete(0, tk.END)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    urls = [line.strip() for line in f if line.strip()]
                for url in urls:
                    self.batch_listbox.insert(tk.END, url)
                self.batch_status_label.config(text=f"已加载 {len(urls)} 个地址")
            except Exception as e:
                messagebox.showerror("错误", f"读取文件失败: {e}")

    def clear_batch_list(self):
        self.batch_listbox.delete(0, tk.END)
        self.batch_progress['value'] = 0
        self.batch_status_label.config(text="未选择文件")

    def start_batch_download(self):
        urls = self.batch_listbox.get(0, tk.END)
        if not urls:
            messagebox.showwarning("警告", "请先选择下载地址文件")
            return
        
        folder_selected = filedialog.askdirectory(title="选择保存位置")
        if not folder_selected:
            return
        
        self.download_thread = threading.Thread(target=self.batch_download, args=(urls, folder_selected))
        self.download_thread.daemon = True
        self.download_thread.start()

    def batch_download(self, urls, output_path):
        total = len(urls)
        success_count = 0
        failed_count = 0
        
        for idx, url in enumerate(urls):
            if not url.strip():
                continue
            
            self.root.after(0, self.batch_status_label.config, {"text": f"正在下载 {idx+1}/{total}: {url[:50]}..."})
            self.root.after(0, self.batch_progress.config, {"value": (idx / total) * 100})
            
            try:
                self.download_single_video(url.strip(), output_path)
                success_count += 1
            except Exception as e:
                failed_count += 1
                print(f"下载失败 {url}: {e}")
        
        self.root.after(0, self.batch_status_label.config, {"text": f"完成: 成功 {success_count}, 失败 {failed_count}"})
        self.root.after(0, self.batch_progress.config, {"value": 100})
        self.root.after(0, messagebox.showinfo, "完成", f"批量下载完成!\n成功: {success_count}\n失败: {failed_count}")

    def download_single_video(self, url, output_path):
        selected_format = self.format_var.get()
        quality_map = {"最高": "best", "1080p": "bestvideo[height<=1080]+bestaudio/best", "720p": "bestvideo[height<=720]+bestaudio/best", "480p": "bestvideo[height<=480]+bestaudio/best", "360p": "bestvideo[height<=360]+bestaudio/best", "最低": "worst"}
        
        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    percent = (downloaded / total) * 100
                    pass

        if selected_format == "mp3":
            ffmpeg_path = self.download_and_extract_ffmpeg() if not self.find_ffmpeg() else self.find_ffmpeg()
            if not ffmpeg_path:
                raise Exception("需要 FFmpeg 才能下载 MP3。请安装 FFmpeg 或将 ffmpeg.exe 放到程序目录的 ffmpeg_bin 文件夹中。")
            bitrate = self.bitrate_var.get()
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': bitrate,
                }],
                'ffmpeg_location': ffmpeg_path,
                'quiet': True,
            }
        else:
            quality = self.quality_var.get()
            video_format = quality_map.get(quality, "best")
            ydl_opts = {
                'format': video_format,
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'quiet': True,
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    def download_and_extract_ffmpeg(self):
        import sys
        import zipfile
        import shutil
        
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
        else:
            exe_dir = os.path.dirname(os.path.abspath(__file__))
        
        ffmpeg_dir = os.path.join(exe_dir, "ffmpeg_bin")
        ffmpeg_exe = os.path.join(ffmpeg_dir, "ffmpeg.exe")
        
        if os.path.exists(ffmpeg_exe):
            return ffmpeg_dir
        
        try:
            self.root.after(0, self.update_status, "正在下载 FFmpeg...")
            
            import urllib.request
            zip_path = os.path.join(ffmpeg_dir, "ffmpeg.zip")
            os.makedirs(ffmpeg_dir, exist_ok=True)
            
            url = "https://github.com/btbn/ffmpeg-builds/releases/download/autobuild-2024-12-09-12-38/ffmpeg-master-latest-win64-gpl.zip"
            urllib.request.urlretrieve(url, zip_path)
            
            with zipfile.ZipFile(zip_path, 'r') as z:
                for member in z.namelist():
                    if member.endswith('ffmpeg.exe') or member.endswith('ffprobe.exe'):
                        source = z.open(member)
                        target_path = os.path.join(ffmpeg_dir, os.path.basename(member))
                        with open(target_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
            
            os.remove(zip_path)
            return ffmpeg_dir
        except Exception as e:
            print(f"下载 FFmpeg 失败: {e}")
            return None

    def find_ffmpeg(self):
        import sys
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg:
            return os.path.dirname(ffmpeg)
        
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
        else:
            exe_dir = os.path.dirname(os.path.abspath(__file__))
        
        local_ffmpeg = os.path.join(exe_dir, "ffmpeg_bin", "ffmpeg.exe")
        if os.path.exists(local_ffmpeg):
            return os.path.join(exe_dir, "ffmpeg_bin")
        return None

    def on_closing(self):
        if self.download_thread and self.download_thread.is_alive():
            messagebox.showwarning("提示", "下载正在进行中，请稍后...")
        else:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()