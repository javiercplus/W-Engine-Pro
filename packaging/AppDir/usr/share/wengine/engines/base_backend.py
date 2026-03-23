from abc import ABC, abstractmethod


class BaseBackend(ABC):
    """
    Base interface for environment-specific rendering backends (X11, Wayland, etc.)
    """

    @abstractmethod
    def start(self, config, video_path):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def update_setting(self, key, value):
        pass

    @abstractmethod
    def send_command(self, command, *args):
        pass
