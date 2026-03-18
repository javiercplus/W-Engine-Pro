from abc import ABC, abstractmethod

class WallpaperEngineInterface(ABC):
    """
    Abstract interface for all W-Engine Pro engines.
    """
    
    @abstractmethod
    def init(self, surface_handle, monitor_info):
        """
        Initialize the engine with the surface handle and monitor info.
        surface_handle: Window ID or surface pointer where it will render.
        monitor_info: Dict containing 'resolution', 'position', 'name'.
        """
        pass

    @abstractmethod
    def start(self):
        """Start the wallpaper rendering."""
        pass

    @abstractmethod
    def stop(self):
        """Stop the wallpaper rendering and release resources."""
        pass

    @abstractmethod
    def set_wallpaper(self, path):
        """Load a new wallpaper from the given path."""
        pass

    @abstractmethod
    def pause(self):
        """Pause the rendering to save resources."""
        pass

    @abstractmethod
    def resume(self):
        """Resume the rendering."""
        pass

    @abstractmethod
    def set_transition(self, type):
        """Configure the transition type."""
        pass

    @abstractmethod
    def reload(self):
        """Reload the current wallpaper engine configuration."""
        pass
    
    def set_option(self, key, value):
        """
        Optional: Set a specific engine option (volume, rate, loop).
        """
        pass
