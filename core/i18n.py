"""
Internationalization module for W-Engine Pro.
Default language is English. Auto-detects system locale.
This module exposes t(key) for translations and allows runtime language switching.
"""

import os
import locale

TRANSLATIONS = {
    "en": {
        # General
        "app_name": "W-Engine Pro",
        "show_interface": "Show Interface",
        "pause_resume": "Pause/Resume",
        "exit": "Exit",
        
        # Sidebar
        "library": "Library",
        "monitors": "Monitors",
        "design": "Customization",
        "diagnostics": "Diagnostics",
        "settings": "Settings",
        "about": "About",
        
        # Library
        "select_wallpaper": "Select a wallpaper",
        "no_wallpapers": "No wallpapers found",
        "add_url": "Add URL",
        "remove": "Remove",
        "apply": "Apply",
        "apply_now": "Apply Now",
        "stop": "Stop",
        "stop_all": "Stop All",
        
        # Properties Panel
        "playback_settings": "Playback Settings",
        "volume": "Volume",
        "brightness": "Brightness",
        "contrast": "Contrast",
        "saturation": "Saturation",
        "gamma": "Gamma",
        "loop": "Loop",
        "loop_one": "Loop",
        "stop_loop": "Stop",
        "slideshow_settings": "Slideshow Settings",
        "random_themes": "Random Themes",
        "change_every": "Change every",
        "minutes": "min",
        
        # Settings
        "general": "General",
        "audio": "Audio",
        "mute_audio": "Mute audio by default",
        "customization": "Customization",
        "language": "Language",
        "theme": "Theme",
        "autostart": "Start with system",
        "pause_on_activity": "Pause on fullscreen",
        "gpu_api": "GPU API",
        "hardware_decoding": "Hardware Decoding",
        "video_resolution": "Video Resolution",
        "cache_mode": "Cache Mode",
        "auto": "Auto",
        "memory": "Memory",
        "disk": "Disk",
        "engine_settings": "Wallpaper Engine",
        "interface_settings": "Interface",
        "language_changed": "Language changed",
        "language_changed_msg": "Some labels were updated. Restart may be required for all changes.",
        "disabled": "Disabled",
        "pause_window": "Window Active",
        "pause_maximized": "Maximized",
        "pause_fullscreen": "Fullscreen",
        
        # Themes
        "dark": "Dark",
        "light": "Light",
        "material_dark": "Material Dark",
        "fusion_v15": "Fusion V1.5",
        
        # Diagnostics
        "backend": "Backend",
        "protocol": "Protocol",
        "compositor": "Compositor",
        "gpu": "GPU",
        "safe_mode": "Safe Mode",
        "ipc_status": "IPC Status",
        "connected": "CONNECTED",
        "failed": "FAILED",
        "active": "ACTIVE",
        "normal": "Normal",
        "playback_mode": "Playback Mode",
        "cache_status": "Cache",
        "ram_usage": "RAM Usage",
        "cpu_usage": "CPU",
        "battery": "Battery",
        "export_diagnostic": "Export Diagnostic (JSON)",
        "copied": "Copied to Clipboard!",
        
        # Monitor
        "display": "Display",
        "layout_mode": "Layout Mode",
        "individual": "Individual",
        "extended": "Extended (Span)",
        "duplicate": "Duplicate",
        "target_monitor": "Target Monitor",
        "auto_detect": "Auto",
        "draw_mode": "Draw Mode",
        "standard": "Standard",
        "fit": "Fit",
        "stretch": "Stretch",
        "cover": "Cover",
        
        # Messages
        "wallpaper_applied": "Wallpaper applied successfully",
        "wallpaper_removed": "Wallpaper removed",
        "settings_saved": "Settings saved",
        "error_loading": "Error loading wallpaper",
        
        # About
        "version": "Version",
        "author": "Developed by Alexander",
        "license": "License",
        "description": "Native animated wallpaper engine for Linux",
        "github": "View on GitHub",
        "discord": "Join Discord",
        "features": "Features",
        "support": "Support",
    },
    "es": {
        # General
        "app_name": "W-Engine Pro",
        "show_interface": "Mostrar Interfaz",
        "pause_resume": "Pausar/Reanudar",
        "exit": "Salir",
        
        # Sidebar
        "library": "Biblioteca",
        "monitors": "Monitores",
        "design": "Personalización",
        "diagnostics": "Diagnóstico",
        "settings": "Ajustes",
        "about": "Acerca de",
        
        # Library
        "select_wallpaper": "Selecciona un fondo",
        "no_wallpapers": "No se encontraron wallpapers",
        "add_url": "Agregar URL",
        "remove": "Eliminar",
        "apply": "Aplicar",
        "apply_now": "Aplicar Ahora",
        "stop": "Detener",
        "stop_all": "Detener Todo",
        
        # Properties Panel
        "playback_settings": "Ajustes de Reproducción",
        "volume": "Volumen",
        "brightness": "Brillo",
        "contrast": "Contraste",
        "saturation": "Saturación",
        "gamma": "Gamma",
        "loop": "Bucle",
        "loop_one": "Loop",
        "stop_loop": "Detener",
        "slideshow_settings": "Configuración de Slideshow",
        "random_themes": "Temas Aleatorios",
        "change_every": "Cambiar cada",
        "minutes": "min",
        
        # Settings
        "general": "General",
        "audio": "Audio",
        "mute_audio": "Silenciar audio por defecto",
        "customization": "Personalización",
        "language": "Idioma",
        "theme": "Tema",
        "autostart": "Iniciar con el sistema",
        "pause_on_activity": "Pausar en pantalla completa",
        "gpu_api": "API de GPU",
        "hardware_decoding": "Decodificación por Hardware",
        "video_resolution": "Resolución de Video",
        "cache_mode": "Modo de Cache",
        "auto": "Auto",
        "memory": "Memoria",
        "disk": "Disco",
        "engine_settings": "Motor de Wallpaper",
        "interface_settings": "Interfaz",
        "language_changed": "Idioma cambiado",
        "language_changed_msg": "Algunas etiquetas se actualizaron. Reinicie para aplicar todos los cambios.",
        "disabled": "Desactivado",
        "pause_window": "Ventana Activa",
        "pause_maximized": "Ventana Maximizada",
        "pause_fullscreen": "Pantalla Completa",
        
        # Themes
        "dark": "Oscuro",
        "light": "Claro",
        "material_dark": "Material Oscuro",
        "fusion_v15": "Fusion V1.5",
        
        # Diagnostics
        "backend": "Backend",
        "protocol": "Protocolo",
        "compositor": "Compositor",
        "gpu": "GPU",
        "safe_mode": "Modo Seguro",
        "ipc_status": "Estado IPC",
        "connected": "CONECTADO",
        "failed": "FALLIDO",
        "active": "ACTIVO",
        "normal": "Normal",
        "playback_mode": "Modo de Reproducción",
        "cache_status": "Cache",
        "ram_usage": "Uso de RAM",
        "cpu_usage": "CPU",
        "battery": "Batería",
        "export_diagnostic": "Exportar Diagnóstico (JSON)",
        "copied": "¡Copiado al Portapapeles!",
        
        # Monitor
        "display": "Pantalla",
        "layout_mode": "Modo de Diseño",
        "individual": "Individual",
        "extended": "Extendido (Span)",
        "duplicate": "Duplicado",
        "target_monitor": "Monitor Objetivo",
        "auto_detect": "Auto",
        "draw_mode": "Modo de Dibujo",
        "standard": "Estándar",
        "fit": "Ajustar",
        "stretch": "Estirar",
        "cover": "Cubrir",
        
        # Messages
        "wallpaper_applied": "Wallpaper aplicado correctamente",
        "wallpaper_removed": "Wallpaper eliminado",
        "settings_saved": "Configuración guardada",
        "error_loading": "Error al cargar wallpaper",
        
        # About
        "version": "Versión",
        "author": "Desarrollado por Alexander",
        "license": "Licencia",
        "description": "Motor nativo de wallpapers animados para Linux",
        "github": "Ver en GitHub",
        "discord": "Unirse a Discord",
        "features": "Características",
        "support": "Soporte",
    },
}


def get_system_locale():
    """Detect system locale and return language code."""
    try:
        lang = locale.getlocale()[0] or locale.getdefaultlocale()[0] or "en"
        if lang:
            return lang.split("_")[0].lower()
    except:
        pass
    return "en"


def get_current_language():
    """Get current language from config or system locale."""
    from core.config_manager import ConfigManager
    
    config = ConfigManager()
    lang = config.get_setting("language", None)
    
    if lang is None:
        lang = get_system_locale()
        if lang not in TRANSLATIONS:
            lang = "en"
        config.set_setting("language", lang)
    
    return lang


# runtime current language cache
_current_lang = None


def set_language(lang_code):
    """Set the current language (updates runtime cache and config)."""
    global _current_lang
    from core.config_manager import ConfigManager
    
    config = ConfigManager()
    config.set_setting("language", lang_code)
    _current_lang = lang_code
    return _current_lang


def t(key, lang=None):
    """Translate a key to the current language. Uses runtime cache if set."""
    if lang is None:
        if _current_lang:
            lang = _current_lang
        else:
            lang = get_current_language()
    
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)


def init_language():
    global _current_lang
    _current_lang = get_current_language()
    return _current_lang


init_language()
