import os
import subprocess
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gdk, Adw, GObject


class ThemeManager(GObject.Object):
    """
    Gestiona la apariencia de la aplicación para GTK4/Libadwaita.
    Soporta: Dark, Light, Auto (System).
    """

    __gsignals__ = {"theme-changed": (GObject.SignalFlags.RUN_FIRST, None, (str,))}

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager

        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        self.theme_path = os.path.join(project_root, "ui", "themes")

        self.style_manager = Adw.StyleManager.get_default()
        self.provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.config_manager.connect("setting-changed", self.on_setting_changed)
        self.apply_theme()

    def on_setting_changed(self, manager, key, value):
        if key in [
            "theme",
            "interface_style",
            "accent_color",
            "blur_intensity",
            "transparency_level",
            "border_radius",
        ]:
            self.apply_theme()

    def get_system_theme(self) -> str:
        if self.style_manager.get_dark():
            return "dark"
        return "light"

    def apply_theme(self):
        theme_name = self.config_manager.get("theme", "Material Dark")
        accent_color = self.config_manager.get("accent_color", "#bb86fc")

        if theme_name == "Auto":
            self.style_manager.set_color_scheme(Adw.ColorScheme.PREFER_DARK)
        elif "Dark" in theme_name:
            self.style_manager.set_color_scheme(Adw.ColorScheme.PREFER_DARK)
        else:
            self.style_manager.set_color_scheme(Adw.ColorScheme.PREFER_LIGHT)

        css = ""
        if theme_name == "Material Dark":
            css = self.generate_material_css(accent_color)

        self.provider.load_from_data(css.encode("utf-8"))
        self.emit("theme-changed", "dark" if "Dark" in theme_name else "light")

    def generate_material_css(self, accent_color):
        return f"""
        @define-color accent_color {accent_color};
        @define-color accent_bg_color {accent_color};
        @define-color window_bg_color #121212;
        @define-color window_fg_color #e1e1e1;
        @define-color view_bg_color #1e1e1e;
        @define-color view_fg_color #e1e1e1;
        @define-color headerbar_bg_color #1a1a1a;
        @define-color headerbar_fg_color #ffffff;
        @define-color card_bg_color #1e1e1e;
        @define-color card_fg_color #e1e1e1;

        window {{
            background-color: @window_bg_color;
            color: @window_fg_color;
        }}

        .sidebar {{
            background-color: #1a1a1a;
        }}

        button.suggested-action {{
            background-color: @accent_color;
            color: #121212;
            font-weight: bold;
        }}
        
        /* Minimalist cleanup */
        headerbar {{
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        """
