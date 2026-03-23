import mpv
import logging
from ui.interface import WallpaperEngineInterface


class MpvEngine(WallpaperEngineInterface):
    """
    Motor de video basado en libmpv.
    Renderiza directamente en la superficie proporcionada sin procesos externos.
    """

    def __init__(self, config, surface_manager, monitor_id):
        super().__init__(config, surface_manager, monitor_id)
        self.player = None
        self.current_path = None

        wid = self.surface.get_surface_handle()
        if not wid:
            raise ValueError("SurfaceManager no proporcionó un Window ID válido.")

        try:
            self.player = mpv.MPV(
                wid=int(wid),
                vo="x11",
                hwdec="auto",
                input_default_bindings=False,
                input_vo_keyboard=False,
                osc=False,
            )
            logging.info(
                f"[MpvEngine] Instancia de libmpv creada y adjuntada a la ventana {wid}"
            )
        except Exception as e:
            logging.error(
                f"[MpvEngine] No se pudo inicializar libmpv. ¿Está instalada la librería? Error: {e}"
            )
            raise

    def set_wallpaper(self, path: str, properties: dict = None):
        if not self.player:
            return
        self.current_path = path

        resolution_map = {
            "1080p (Full HD)": "scale=-1:1080",
            "720p (HD)": "scale=-1:720",
            "480p (SD)": "scale=-1:480",
        }
        resolution_setting = self.config.get("video_resolution", "Nativa")
        video_filter = resolution_map.get(resolution_setting)

        self.player.vf = ""
        if video_filter:
            self.player.vf_add(video_filter)

        self.player.play(self.current_path)
        self.player.loop = "inf"
        self.player.volume = self.config.get("volume", 50)
        logging.info(f"[MpvEngine] Reproduciendo {path}")

    def start(self):
        self.resume()

    def stop(self):
        if self.player:
            try:
                self.player.terminate()
            except Exception as e:
                logging.warning(f"Error terminando mpv: {e}")
            self.player = None
            logging.info("[MpvEngine] Motor detenido y recursos liberados.")

    def pause(self):
        if self.player:
            self.player.pause = True

    def resume(self):
        if self.player:
            self.player.pause = False
