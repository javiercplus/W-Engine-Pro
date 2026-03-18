import mpv
import logging
from engines.base_engine import WallpaperEngineInterface

class MpvEngine(WallpaperEngineInterface):
    """
    Video renderer using libmpv.
    """
    
    def __init__(self):
        self.player = None
        self.surface_handle = None
        self.monitor_info = None

    def init(self, surface_handle, monitor_info):
        self.surface_handle = surface_handle
        self.monitor_info = monitor_info
        
        try:
            self.player = mpv.MPV(
                vo="null",
                hwdec="auto",
                loop_playlist="inf",
                ytdl=False,
                terminal=False,
                input_default_bindings=False,
                input_vo_keyboard=False,
                log_handler=logging.debug
            )
        except Exception as e:
            logging.error(f"Failed to initialize MPV: {e}")

    def start(self):
        if self.player:
            self.player.play("null")
            logging.info("MPV Engine started.")

    def stop(self):
        if self.player:
            self.player.terminate()
            self.player = None
            logging.info("MPV Engine stopped.")

    def set_wallpaper(self, path):
        if self.player:
            self.player.play(path)
            logging.info(f"MPV playing: {path}")

    def pause(self):
        if self.player:
            self.player.pause = True

    def resume(self):
        if self.player:
            self.player.pause = False

    def set_transition(self, type):
        pass

    def reload(self):
        if self.player:
            self.player.command("loadfile", self.player.filename)

    def set_option(self, key, value):
        if not self.player: return
        
        try:
            if key == "volume":
                self.player.volume = float(value)
            elif key == "rate":
                self.player.speed = float(value)
            elif key == "loop":
                if value == "Loop":
                    self.player.loop_playlist = "inf"
                else:
                    self.player.loop_playlist = "no"
            elif key == "mute":
                self.player.mute = bool(value)
        except Exception as e:
            logging.error(f"MPV option error: {e}")
