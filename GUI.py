import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import yt_dlp
import os
import shutil
import sys

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("视频下载器")
        self.root.geometry("700x600")
        
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
        self.batch_status_label = None
        
        self.setup_ui()
        
    def setup_ui(self):
        self.root.title("视频下载器")
        
        tabview = ctk.CTkTabview(self.root, fg_color="transparent")
        tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.single_tab = tabview.add("单文件下载")
        self.batch_tab = tabview.add("批量下载")
        
        self.setup_single_ui()
        self.setup_batch_ui()
        
    def setup_single_ui(self):
        title_label = ctk.CTkLabel(self.single_tab, text="视频下载器", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(20, 30))
        
        url_frame = ctk.CTkFrame(self.single_tab, fg_color="transparent")
        url_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(url_frame, text="视频链接:", font=ctk.CTkFont(size=14)).pack(side="left")
        
        self.url_entry = ctk.CTkEntry(url_frame, placeholder_text="输入 YouTube 或 B站 链接", height=40, font=ctk.CTkFont(size=13))
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        format_frame = ctk.CTkFrame(self.single_tab, fg_color="transparent")
        format_frame.pack(pady=15)
        
        ctk.CTkLabel(format_frame, text="下载格式:", font=ctk.CTkFont(size=14)).pack(side="left")
        
        self.format_var = ctk.StringVar(value="mp4")
        formats = [
            ("MP4视频", "mp4"),
            ("MP3音频", "mp3"),
            ("WEBM视频", "webm"),
        ]
        for text, value in formats:
            ctk.CTkRadioButton(format_frame, text=text, variable=self.format_var, value=value, command=self.update_quality_options, font=ctk.CTkFont(size=13)).pack(side="left", padx=15)
        
        quality_frame = ctk.CTkFrame(self.single_tab, fg_color="transparent")
        quality_frame.pack(pady=10)
        
        ctk.CTkLabel(quality_frame, text="视频质量:", font=ctk.CTkFont(size=14)).pack(side="left")
        
        self.quality_var = ctk.StringVar(value="最高")
        self.quality_combo = ctk.CTkComboBox(quality_frame, values=["最高", "1080p", "720p", "480p", "360p", "最低"], variable=self.quality_var, width=120, state="readonly")
        self.quality_combo.pack(side="left", padx=10)
        
        ctk.CTkLabel(quality_frame, text="MP3码率:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(20, 0))
        
        self.bitrate_var = ctk.StringVar(value="192")
        self.bitrate_combo = ctk.CTkComboBox(quality_frame, values=["320", "256", "192", "128", "64"], variable=self.bitrate_var, width=80, state="readonly")
        self.bitrate_combo.pack(side="left", padx=10)
        
        self.progress_bar = ctk.CTkProgressBar(self.single_tab, width=400)
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(self.single_tab, text="就绪", font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=5)
        
        btn_frame = ctk.CTkFrame(self.single_tab, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="下载视频", command=self.start_download, width=150, height=40, font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="清空", command=self.clear_input, width=100, height=40).pack(side="left", padx=10)
        
    def setup_batch_ui(self):
        title_label = ctk.CTkLabel(self.batch_tab, text="批量下载", font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=(20, 15))
        
        info_label = ctk.CTkLabel(self.batch_tab, text="选择包含下载地址的txt文件（每行一个地址）", font=ctk.CTkFont(size=12))
        info_label.pack(pady=5)
        
        ctk.CTkButton(self.batch_tab, text="选择文件", command=self.select_batch_file, width=150, height=35).pack(pady=10)
        
        self.batch_listbox = ctk.CTkTextbox(self.batch_tab, height=200, width=500, font=ctk.CTkFont(size=12))
        self.batch_listbox.pack(pady=10)
        
        self.batch_progress = ctk.CTkProgressBar(self.batch_tab, width=400)
        self.batch_progress.pack(pady=10)
        self.batch_progress.set(0)
        
        self.batch_status_label = ctk.CTkLabel(self.batch_tab, text="未选择文件", font=ctk.CTkFont(size=12))
        self.batch_status_label.pack(pady=5)
        
        btn_frame = ctk.CTkFrame(self.batch_tab, fg_color="transparent")
        btn_frame.pack(pady=15)
        
        ctk.CTkButton(btn_frame, text="开始批量下载", command=self.start_batch_download, width=150, height=40, font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="清空列表", command=self.clear_batch_list, width=100, height=40).pack(side="left", padx=10)
        
    def update_quality_options(self):
        selected = self.format_var.get()
        if selected == "mp3":
            self.quality_combo.configure(state="disabled")
            self.bitrate_combo.configure(state="readonly")
        else:
            self.quality_combo.configure(state="readonly")
            self.bitrate_combo.configure(state="disabled")
    
    def clear_input(self):
        self.url_entry.delete(0, "end")
        self.progress_bar.set(0)
        self.status_label.configure(text="就绪")
        
    def select_batch_file(self):
        file_path = filedialog.askopenfilename(title="选择下载地址文件", filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if file_path:
            self.batch_listbox.delete("1.0", "end")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    urls = [line.strip() for line in f if line.strip()]
                for url in urls:
                    self.batch_listbox.insert("end", url + "\n")
                self.batch_status_label.configure(text=f"已加载 {len(urls)} 个地址")
            except Exception as e:
                messagebox.showerror("错误", f"读取文件失败: {e}")
    
    def clear_batch_list(self):
        self.batch_listbox.delete("1.0", "end")
        self.batch_progress.set(0)
        self.batch_status_label.configure(text="未选择文件")
    
    def start_download(self):
        url = self.url_entry.get().strip()
        selected_format = self.format_var.get()
        
        if not url:
            messagebox.showwarning("警告", "请输入视频链接")
            return
        
        def is_valid_url(url):
            valid_sites = ["youtube.com", "youtu.be", "bilibili.com", "b23.tv"]
            return any(site in url for site in valid_sites)
        
        if not is_valid_url(url):
            messagebox.showwarning("警告", "请输入有效的YouTube或B站链接")
            return
        
        folder_selected = filedialog.askdirectory(title="选择保存位置")
        if not folder_selected:
            return
        
        self.status_label.configure(text="下载中...")
        self.progress_bar.set(0)
        
        quality_map = {"最高": "best", "1080p": "bestvideo[height<=1080]+bestaudio/best", "720p": "bestvideo[height<=720]+bestaudio/best", "480p": "bestvideo[height<=480]+bestaudio/best", "360p": "bestvideo[height<=360]+bestaudio/best", "最低": "worst"}
        
        def download_thread():
            try:
                if selected_format == "mp3":
                    ffmpeg_path = self.download_and_extract_ffmpeg() if not self.find_ffmpeg() else self.find_ffmpeg()
                    if not ffmpeg_path:
                        self.root.after(0, messagebox.showerror, "错误", "下载 MP3 需要 FFmpeg")
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
                    if "bilibili" in url:
                        ffmpeg_path = self.download_and_extract_ffmpeg() if not self.find_ffmpeg() else self.find_ffmpeg()
                        video_format = "bestvideo+bestaudio/best"
                    else:
                        ffmpeg_path = self.find_ffmpeg()
                        video_format = quality_map.get(quality, "best")
                    ydl_opts = {
                        'format': video_format,
                        'outtmpl': os.path.join(folder_selected, '%(title)s.%(ext)s'),
                        'ffmpeg_location': ffmpeg_path,
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
    
    def download_complete(self, success, message):
        self.progress_bar.set(1)
        if success:
            self.status_label.configure(text="下载完成!")
            messagebox.showinfo("成功", f"视频已下载: {message}")
        else:
            self.status_label.configure(text="下载失败")
            messagebox.showerror("错误", f"下载失败: {message}")
        self.progress_bar.set(0)
    
    def start_batch_download(self):
        content = self.batch_listbox.get("1.0", "end").strip()
        urls = content.split("\n") if content else []
        
        if not urls or not urls[0]:
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
        
        quality_map = {"最高": "best", "1080p": "bestvideo[height<=1080]+bestaudio/best", "720p": "bestvideo[height<=720]+bestaudio/best", "480p": "bestvideo[height<=480]+bestaudio/best", "360p": "bestvideo[height<=360]+bestaudio/best", "最低": "worst"}
        
        for idx, url in enumerate(urls):
            if not url.strip():
                continue
            
            self.root.after(0, self.batch_status_label.configure, {"text": f"正在下载 {idx+1}/{total}: {url[:50]}..."})
            self.root.after(0, self.batch_progress.set, (idx / total))
            
            try:
                selected_format = self.format_var.get()
                
                if selected_format == "mp3":
                    ffmpeg_path = self.download_and_extract_ffmpeg() if not self.find_ffmpeg() else self.find_ffmpeg()
                    if not ffmpeg_path:
                        raise Exception("需要 FFmpeg")
                    bitrate = self.bitrate_var.get()
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': bitrate,
                        }],
                        'ffmpeg_location': ffmpeg_path,
                        'quiet': True,
                    }
                else:
                    if "bilibili" in url:
                        ffmpeg_path = self.download_and_extract_ffmpeg() if not self.find_ffmpeg() else self.find_ffmpeg()
                        video_format = "bestvideo+bestaudio/best"
                    else:
                        ffmpeg_path = self.find_ffmpeg()
                        quality = self.quality_var.get()
                        video_format = quality_map.get(quality, "best")
                    ydl_opts = {
                        'format': video_format,
                        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                        'ffmpeg_location': ffmpeg_path,
                        'quiet': True,
                    }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url.strip()])
                success_count += 1
            except Exception as e:
                failed_count += 1
                print(f"下载失败 {url}: {e}")
        
        self.root.after(0, self.batch_status_label.configure, {"text": f"完成: 成功 {success_count}, 失败 {failed_count}"})
        self.root.after(0, self.batch_progress.set, 1)
        self.root.after(0, messagebox.showinfo, "完成", f"批量下载完成!\n成功: {success_count}\n失败: {failed_count}")
    
    def find_ffmpeg(self):
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
    
    def download_and_extract_ffmpeg(self):
        import zipfile
        
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
        else:
            exe_dir = os.path.dirname(os.path.abspath(__file__))
        
        ffmpeg_dir = os.path.join(exe_dir, "ffmpeg_bin")
        ffmpeg_exe = os.path.join(ffmpeg_dir, "ffmpeg.exe")
        
        if os.path.exists(ffmpeg_exe):
            return ffmpeg_dir
        
        try:
            self.root.after(0, self.status_label.configure, {"text": "正在下载 FFmpeg..."})
            
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

if __name__ == "__main__":
    root = ctk.CTk()
    app = YouTubeDownloader(root)
    root.mainloop()
