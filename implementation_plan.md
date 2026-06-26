# 修复哔哩哔哩无法下载的实现方案

最近 Bilibili 升级了反爬虫机制，针对媒体流和视频元数据的请求，如果缺少特定的头部信息（如 `Origin` 和 `Referer`）或者 `yt-dlp` 版本过旧，服务器会返回 `HTTP Error 412: Precondition Failed` 错误，导致下载失败。

本方案旨在升级 `yt-dlp` 依赖，并在 `GUI.py` 中为下载请求添加必要的 HTTP 头部，从而绕过此限制。

## 已完成的调查与准备工作

1. **升级依赖**：已成功在当前 Python 环境中将 `yt-dlp` 从 `2026.03.17` 升级到最新版本 `2026.06.09`。
2. **测试验证**：
   - 升级前：下载 Bilibili 链接抛出 `HTTP Error 412: Precondition Failed`。
   - 升级后（不加头部）：仍抛出 412 错误。
   - 升级后（显式添加 `Origin` 和 `Referer` 头部）：**测试下载成功**，媒体文件可正常合并为最终的 MP4 视频。

---

## 拟定修改内容

我们将修改 `GUI.py` 中的 `ydl_opts` 字典定义，根据视频链接是否属于 Bilibili，动态为其注入必要的 `http_headers`（`Referer` 和 `Origin`）。

### 1. 核心下载逻辑组件

#### [MODIFY] [GUI.py](file:///c:/OpenCode/YoutubeDownloader/GUI.py)

- 在 `start_download` 方法中，当检测到是 Bilibili 链接时，或者在构建 `ydl_opts` 时，注入以下头部：
  ```python
  'http_headers': {
      'Referer': 'https://www.bilibili.com/',
      'Origin': 'https://www.bilibili.com'
  }
  ```
- 同样在 `batch_download`（批量下载）方法中，也做相同的逻辑判断与头部注入，确保批量下载功能对于 Bilibili 视频依然有效。

为了避免代码重复，我们可以编写一个辅助方法来生成或调整 `ydl_opts`，或者直接在各处定义 `ydl_opts` 时根据条件添加头部。由于当前定义处只有 4 处，我们可直接在这 4 处或者利用辅助字典来按需注入头部。

例如，我们可以在 `start_download` 和 `batch_download` 的最开始定义一个通用的 `headers` 处理逻辑：
```python
is_bilibili = "bilibili" in url or "b23.tv" in url
```
对于每个 `ydl_opts` 字典，如果 `is_bilibili` 为 `True`，我们就添加：
```python
'http_headers': {
    'Referer': 'https://www.bilibili.com/',
    'Origin': 'https://www.bilibili.com'
}
```

---

## 验证方案

### 手动验证
1. 运行 `python GUI.py` 启动下载器。
2. 在“单文件下载”中输入一个 Bilibili 视频链接（如：`https://www.bilibili.com/video/BV1xx411c7m9`），选择下载路径，并点击“下载视频”。
3. 验证是否能够成功下载并合并为 MP4 文件，界面状态是否显示“下载完成!”。
4. 在“批量下载”中选择一个包含 Bilibili 视频链接的文本文件，测试批量下载。
5. 验证 YouTube 视频的下载是否仍可正常进行。
