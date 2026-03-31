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
        "gpu_vendor": "GPU Vendor",
        "safe_mode": "Safe Mode",
        "ipc_status": "IPC Status",
        "connected": "CONNECTED",
        "failed": "FAILED",
        "active": "ACTIVE",
        "normal": "Normal",
        "playback_mode": "Playback Mode",
        "resolved_mode": "Resolved Mode",
        "cache_status": "Cache",
        "ram_usage": "RAM Usage",
        "cpu_usage": "CPU Usage",
        "battery": "Battery",
        "export_diagnostic": "Export Diagnostic (JSON)",
        "copied": "Copied to Clipboard!",
        "system_actions": "System Actions",
        "restart_engine": "Restart Engine",
        "force_safe_mode": "Force Safe Mode",
        "label_units": "Units",
        "cache_config": "Cache Config",
        "cpu_load": "CPU Load",
        
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
        "no_selection": "No Selection",
        "type_label": "Type",
        "preview": "Preview",
        "support": "Support",
        "open_folder": "Open folder",
        "selection_tray": "Selected Wallpapers",
        "display_settings": "Display Settings",
        "select_monitor": "Select Monitor",
        "layout_mode": "Layout Mode",
        "mode_label": "Mode",
        "individual": "Individual",
        "duplicate": "Duplicate",
        "extended": "Extended (Span)",
        "design": "Customization",
        "design_style": "Interface Style",
        "theme_default_label": "Default Theme",
        "transparency": "Transparency",
        "font_label": "Font",
        "ui_scale": "UI Scale",
        "enable_animations": "Enable Animations (Transitions)",
        "enable_effects": "Enable Visual Effects (Shadows/Glow)",
        "custom_colors": "Custom Colors",
        "accent_color": "Accent Color",
        "ui_bg_color": "UI Background",
        "ui_text_color": "Text Color",
        "performance_title": "Performance & Video",
        "rendering_engine": "Rendering Engine",
        "engine_mpv": "mpv",
        "engine_web": "web",
        "engine_parallax": "parallax",
        "video_resolution": "Video Resolution",
        "res_native": "Native",
        "res_1080p": "1080p (Full HD)",
        "res_720p": "720p (HD)",
        "res_480p": "480p (SD)",
        "video_cache": "Video Cache",
        "cache_disk": "Disk (Standard)",
        "cache_ram": "RAM (Ultra)",
        "fps_limit": "FPS Limit",
        "fps": "FPS",
        "audio": "Audio",
        "mute_audio": "Mute audio by default",
        "pause_auto": "Pause automatically when:",
        "pause_mode_label": "Pause Mode",
        "pause_window": "Active Window",
        "pause_maximized": "Maximized",
        "pause_fullscreen": "Fullscreen",
        "gnome_opt_title": "GNOME Optimization",
        "gnome_info_requires_extension": "GNOME Wayland requires a small extension for wallpaper support.",
        "install_wallpaper_extension": "Install Wallpaper Extension",
        "reinstall_update_extension": "Reinstall / Update Extension",
        "gnome_helper": "GNOME Helper",
        "extension_installed": "Extension Installed",
        "error_title": "Error",
        "install_error": "Could not install extension",
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
        "fullscreen_tooltip": "Pantalla Completa (F11)",
        "confirm_delete_title": "Confirmar Eliminación",
        "confirm_delete_single": "¿Estás seguro de que deseas eliminar '{name}'?",
        "confirm_delete_multiple": "¿Estás seguro de que deseas eliminar {count} elemento(s)?",
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
        "select_color": "Seleccionar Color",
        "accent_color": "Color Acento",
        "custom_colors": "Colores Personalizados",
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
        "gpu_vendor": "Proveedor de GPU",
        "safe_mode": "Modo Seguro",
        "ipc_status": "Estado IPC",
        "connected": "CONECTADO",
        "failed": "FALLIDO",
        "active": "ACTIVO",
        "normal": "Normal",
        "playback_mode": "Modo de Reproducción",
        "resolved_mode": "Modo Resuelto",
        "cache_status": "Cache",
        "ram_usage": "Uso de RAM",
        "cpu_usage": "Uso de CPU",
        "battery": "Batería",
        "export_diagnostic": "Exportar Diagnóstico (JSON)",
        "copied": "¡Copiado al Portapapeles!",
        "system_actions": "Acciones del Sistema",
        "restart_engine": "Reiniciar Motor",
        "force_safe_mode": "Forzar Modo Seguro",
        "label_units": "Unidades",
        "cache_config": "Configuración de Cache",
        "cpu_load": "Carga de CPU",
        
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
        "no_selection": "Sin Selección",
        "type_label": "Tipo",
        "preview": "Vista previa",
        "support": "Soporte",
        "open_folder": "Abrir carpeta",
        "selection_tray": "Fondos seleccionados",
        "display_settings": "Configuración de Pantalla",
        "select_monitor": "Seleccionar Monitor",
        "layout_mode": "Modo de diseño",
        "mode_label": "Modo",
        "individual": "Individual",
        "duplicate": "Duplicado",
        "extended": "Extendido (Span)",
        "design_style": "Estilo de la Interfaz",
        "theme_default_label": "Tema Predeterminado",
        "transparency": "Transparencia",
        "font_label": "Tipografía",
        "ui_scale": "Escala de Interfaz",
        "enable_animations": "Activar Animaciones (Transiciones)",
        "enable_effects": "Activar Efectos Visuales (Sombras/Glow)",
        "custom_colors": "Colores Personalizados",
        "accent_color": "Color Acento",
        "ui_bg_color": "Fondo de Interfaz",
        "ui_text_color": "Color de Texto",
        "performance_title": "Rendimiento y Video",
        "rendering_engine": "Motor de Renderizado",
        "engine_mpv": "mpv",
        "engine_web": "web",
        "engine_parallax": "parallax",
        "video_resolution": "Resolución de Video",
        "res_native": "Nativa",
        "res_1080p": "1080p (Full HD)",
        "res_720p": "720p (HD)",
        "res_480p": "480p (SD)",
        "video_cache": "Cache de Video",
        "cache_disk": "Disco (Estándar)",
        "cache_ram": "RAM (Ultra)",
        "fps_limit": "Límite de FPS",
        "fps": "FPS",
        "audio": "Audio",
        "mute_audio": "Silenciar audio por defecto",
        "pause_auto": "Pausar automáticamente cuando:",
        "pause_mode_label": "Modo de Pausa",
        "pause_window": "Ventana Activa",
        "pause_maximized": "Ventana Maximizada",
        "pause_fullscreen": "Pantalla Completa",
        "gnome_opt_title": "Optimización GNOME",
        "gnome_info_requires_extension": "GNOME Wayland requiere una pequeña extensión para soportar wallpapers.",
        "install_wallpaper_extension": "Instalar Extensión de Wallpaper",
        "reinstall_update_extension": "Reinstalar / Actualizar Extensión",
        "gnome_helper": "Asistente GNOME",
        "extension_installed": "Extensión Instalada",
        "error_title": "Error",
        "install_error": "No se pudo instalar la extensión",
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
