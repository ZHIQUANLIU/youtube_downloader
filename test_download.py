import yt_dlp
import os
import shutil

def test_download_bilibili():
    url = "https://www.bilibili.com/video/BV1xx411c7m9"
    is_bilibili = "bilibili" in url or "b23.tv" in url
    
    # Simulate the quality map and ydl_opts construction in GUI.py
    quality_map = {
        "最高": "best",
        "1080p": "bestvideo[height<=1080]+bestaudio/best",
        "720p": "bestvideo[height<=720]+bestaudio/best"
    }
    
    video_format = "bestvideo+bestaudio/best" if is_bilibili else quality_map.get("最高", "best")
    
    ydl_opts = {
        'format': video_format,
        'outtmpl': os.path.join('.', '%(title)s.%(ext)s'),
        'quiet': False,
    }
    
    if is_bilibili:
        ydl_opts['http_headers'] = {
            'Referer': 'https://www.bilibili.com/',
            'Origin': 'https://www.bilibili.com'
        }
        
    print("Testing Bilibili download options...")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Unknown')
            # Safe print
            safe_title = title.encode('ascii', 'ignore').decode('ascii')
            print(f"SUCCESS: Downloaded Bilibili video: {safe_title}")
            
            # Clean up the downloaded file(s) without printing filenames
            filename = ydl.prepare_filename(info)
            if os.path.exists(filename):
                os.remove(filename)
            else:
                for file in os.listdir('.'):
                    if 'BV1xx411c7m9' in file or '2012' in file:
                        if file.endswith('.mp4') or file.endswith('.mkv') or file.endswith('.m4a'):
                            try:
                                os.remove(file)
                            except:
                                pass
            return True
    except Exception as e:
        print(f"FAILED: Bilibili download failed with: {e}")
        return False

def test_download_youtube():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    is_bilibili = "bilibili" in url or "b23.tv" in url
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join('.', '%(title)s.%(ext)s'),
        'quiet': False,
        'simulate': True, # Only simulate YouTube to avoid downloading large files
    }
    
    if is_bilibili:
         ydl_opts['http_headers'] = {
            'Referer': 'https://www.bilibili.com/',
            'Origin': 'https://www.bilibili.com'
        }
         
    print("Testing YouTube download options (simulate)...")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Unknown')
            safe_title = title.encode('ascii', 'ignore').decode('ascii')
            print(f"SUCCESS: Simulated YouTube download: {safe_title}")
            return True
    except Exception as e:
        print(f"FAILED: YouTube simulation failed with: {e}")
        return False

if __name__ == "__main__":
    bilibili_ok = test_download_bilibili()
    youtube_ok = test_download_youtube()
    
    if bilibili_ok and youtube_ok:
        print("\nALL TESTS PASSED!")
    else:
        print("\nSOME TESTS FAILED!")
