# Bilibili 视频下载问题修复说明

我们已经成功修复了 Bilibili 视频无法下载的问题。

## 修改内容

### 1. 升级底层依赖 `yt-dlp`
由于 Bilibili 会频繁更新其 API 和签名方式（如 WBI 签名），旧版的 `yt-dlp` 会导致视频特征提取不匹配。我们已将 `yt-dlp` 从 `2026.03.17` 成功升级到了最新版本 `2026.06.09`。

### 2. 动态注入 `Referer` 和 `Origin` HTTP 头部
Bilibili 的播放 API (`playurl`) 增加了严格的反爬虫限制。如果客户端没有传递合法的浏览器来源头，Bilibili 会拒接请求并返回 `HTTP Error 412: Precondition Failed`。

我们在 [GUI.py](file:///c:/OpenCode/YoutubeDownloader/GUI.py) 中进行了以下修改：
- 在 `start_download`（单视频下载）和 `batch_download`（批量视频下载）中检测到下载地址来自 Bilibili (包含 `bilibili` 或 `b23.tv`) 时，动态往 `ydl_opts` 的 `http_headers` 注入 `Referer: https://www.bilibili.com/` 和 `Origin: https://www.bilibili.com`。

修改涉及的关键代码块如下：

```diff
                 quality = self.quality_var.get()
-                if "bilibili" in url:
+                if is_bilibili:
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
+            
+            if is_bilibili:
+                ydl_opts['http_headers'] = {
+                    'Referer': 'https://www.bilibili.com/',
+                    'Origin': 'https://www.bilibili.com'
+                }
```

---

## 验证结果

我们在测试目录中运行了编写的自动化验证脚本 [test_download.py](file:///C:/Users/zhiqu/.gemini/antigravity-ide/brain/7c98352f-1f3d-403d-9d59-d7078ff5a4b5/scratch/test_download.py)，结果如下：

### 1. Bilibili 单文件与批量下载流程验证
```
[BiliBili] Extracting URL: https://www.bilibili.com/video/BV1xx411c7m9
Testing Bilibili download options...
[BiliBili] 1xx411c7m9: Downloading webpage
[BiliBili] BV1xx411c7m9: Extracting videos in anthology
[BiliBili] BV1xx411c7m9: Downloading wbi sign
[BiliBili] BV1xx411c7m9: Downloading video formats for cid 3625120
[info] BV1xx411c7m9: Downloading 1 format(s): 100022+30216
[download] Destination: 2012.f100022.mp4
[download] 100% of 1.48MiB in 00:00:00 at 10.72MiB/s
[download] Destination: 2012.f30216.m4a
[download] 100% of 1.37MiB in 00:00:00 at 15.55MiB/s
[Merger] Merging formats into "2012.mp4"
SUCCESS: Downloaded Bilibili video: 2012
```
Bilibili 的分流音视频下载无报错，且 `ffmpeg` 合并流程运转正常。

### 2. YouTube 兼容性模拟验证
```
Testing YouTube download options (simulate)...
[youtube] dQw4w9WgXcQ: Downloading webpage
[info] dQw4w9WgXcQ: Downloading 1 format(s): 18
SUCCESS: Simulated YouTube download: Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)
```
YouTube 链接的解析和下载机制没有受到负面影响。

---

## 总结
目前，修复已经完全应用至 `GUI.py`。您现在可以重新运行您的下载工具 GUI 客户端，输入哔哩哔哩视频链接，即可流畅地进行单视频或批量视频下载。
