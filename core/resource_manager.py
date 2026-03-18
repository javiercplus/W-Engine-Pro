import os
import subprocess
import hashlib
import logging

class ResourceManager:
    def __init__(self, config=None):
        self.config = config
        self.wallpaper_dir = os.path.expanduser("~/Vídeos/Wallpapers/")
        self.thumb_dir = os.path.expanduser("~/.cache/w-engine-pro/thumbnails/")
        
        os.makedirs(self.wallpaper_dir, exist_ok=True)
        os.makedirs(self.thumb_dir, exist_ok=True)

    def list_local_wallpapers(self):
        """Lista archivos de video en el directorio de wallpapers."""
        valid_exts = {'.mp4', '.webm', '.mkv', '.avi', '.mov'}
        files = []
        if os.path.exists(self.wallpaper_dir):
            try:
                for f in os.listdir(self.wallpaper_dir):
                    if os.path.splitext(f)[1].lower() in valid_exts:
                        files.append(os.path.join(self.wallpaper_dir, f))
            except Exception as e:
                logging.error(f"Error listando wallpapers: {e}")
        return files

    def get_thumbnail(self, video_path):
        """Genera o recupera una miniatura para el video dado."""
        h = hashlib.md5(video_path.encode('utf-8')).hexdigest()
        thumb_path = os.path.join(self.thumb_dir, f"{h}.jpg")
        
        if os.path.exists(thumb_path):
            return thumb_path
            
        try:
            cmd = [
                'ffmpeg', '-y', '-i', video_path,
                '-ss', '00:00:01.000', '-vframes', '1',
                '-vf', 'scale=320:-1',
                thumb_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            return thumb_path if os.path.exists(thumb_path) else None
        except Exception as e:
            logging.error(f"Error generando thumbnail para {video_path}: {e}")
            return None