import os

class CompositorDetector:
    """
    Detects the current windowing system and compositor.
    """
    
    @staticmethod
    def get_session_type():
        """Returns 'wayland' or 'x11'."""
        wayland_display = os.environ.get('WAYLAND_DISPLAY')
        xdg_session_type = os.environ.get('XDG_SESSION_TYPE')
        
        if wayland_display or xdg_session_type == 'wayland':
            return 'wayland'
        return 'x11'

    @staticmethod
    def get_compositor():
        """Detects the current compositor/desktop environment."""
        xdg_current_desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        
        if 'hyprland' in xdg_current_desktop:
            return 'Hyprland'
        if 'sway' in xdg_current_desktop:
            return 'Sway'
        if 'gnome' in xdg_current_desktop:
            return 'GNOME'
        if 'kde' in xdg_current_desktop or 'plasma' in xdg_current_desktop:
            return 'KDE'
        if 'xfce' in xdg_current_desktop:
            return 'XFCE'
        
        return xdg_current_desktop or 'Unknown'

    @staticmethod
    def is_wayland():
        return CompositorDetector.get_session_type() == 'wayland'
