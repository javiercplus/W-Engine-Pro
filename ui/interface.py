from abc import ABC, abstractmethod

class WallpaperEngineInterface(ABC):
    """
    Interfaz abstracta que todos los motores de wallpaper deben implementar.
    """

    def __init__(self, config, surface_manager, monitor_id):
        """
        Inicializa el motor con la configuración y una superficie de renderizado.
        
        :param config: Instancia de ConfigManager.
        :param surface_manager: Instancia de SurfaceManager para este motor.
        :param monitor_id: El ID del monitor que este motor controlará.
        """
        self.config = config
        self.surface = surface_manager
        self.monitor_id = monitor_id

    @abstractmethod
    def start(self):
        """Inicia el renderizado en la superficie."""
        pass

    @abstractmethod
    def stop(self):
        """Detiene el renderizado y libera recursos."""
        pass

    @abstractmethod
    def set_wallpaper(self, path: str, properties: dict = None):
        """Establece un nuevo wallpaper para renderizar."""
        pass

    def pause(self): pass
    def resume(self): pass
    def set_transition(self, transition_type: str): pass
    def reload(self): pass