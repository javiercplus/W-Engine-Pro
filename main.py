import logging
import os
import sys

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from core import i18n
from core.config_manager import ConfigManager
from core.desktop_helper import DesktopHelper
from core.engine_controller import EngineController
from core.resource_manager import ResourceManager
from ui.main_window import MainWindow


def main():
    # Soporte para modo debug vía flag antes de iniciar
    log_level = logging.DEBUG if "--debug" in sys.argv else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    if "--debug" in sys.argv:
        logging.debug("Debug mode enabled.")

    app = QApplication(sys.argv)
    app.setApplicationName("W-Engine Pro")
    app.setDesktopFileName("org.wengine.Pro")
    app.setQuitOnLastWindowClosed(False)

    icon_path_svg = os.path.join(os.path.dirname(__file__), "data", "W-Enginepro.svg")
    app_icon = QIcon()

    if os.path.exists(icon_path_svg):
        app_icon.addFile(icon_path_svg, QSize(16, 16))
        app_icon.addFile(icon_path_svg, QSize(32, 32))
        app_icon.addFile(icon_path_svg, QSize(64, 64))
        app_icon.addFile(icon_path_svg, QSize(128, 128))
        app_icon.addFile(icon_path_svg, QSize(256, 256))
        app.setWindowIcon(app_icon)
    else:
        icon_path_png = os.path.join(
            os.path.dirname(__file__), "data", "W-Enginepro.png"
        )
        if os.path.exists(icon_path_png):
            app_icon = QIcon(icon_path_png)
            app.setWindowIcon(app_icon)
        else:
            app_icon = QIcon.fromTheme("video-display")

    config = ConfigManager()

    # Gestionar Autostart según configuración
    DesktopHelper.setup_autostart(
        config.get_setting("autostart", False),
        config.get_setting("start_minimized", False),
    )

    resources = ResourceManager(config)
    controller = EngineController(config_manager=config)

    exit_code = 0
    try:
        window = MainWindow(controller=controller, config=config, resources=resources)
        window.setWindowIcon(app_icon)

        # Check if should start minimized
        start_minimized_flag = "--minimized" in sys.argv
        start_minimized_config = config.get_setting("start_minimized", False)
        should_start_minimized = start_minimized_flag or start_minimized_config

        tray_icon = QSystemTrayIcon(app_icon, app)
        tray_menu = QMenu()

        def update_tray_menu_style():
            tray_menu.setStyleSheet(app.styleSheet())

        window.theme_changed.connect(update_tray_menu_style)

        show_action = QAction(
            i18n.t("show_interface") if hasattr(i18n, "t") else "Show Interface", app
        )
        show_action.triggered.connect(window.showNormal)

        pause_action = QAction(
            i18n.t("pause_resume") if hasattr(i18n, "t") else "Pause/Resume", app
        )
        pause_action.triggered.connect(lambda: controller.pause_all())

        quit_action = QAction(i18n.t("exit") if hasattr(i18n, "t") else "Exit", app)
        quit_action.triggered.connect(app.quit)

        tray_menu.addAction(show_action)
        tray_menu.addAction(pause_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        tray_icon.setContextMenu(tray_menu)
        tray_icon.setToolTip("W-Engine Pro")

        # Check if system tray is available
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logging.warning(
                "[Tray] System tray is NOT available (common in GNOME Wayland)"
            )

            # Check if we're on GNOME Wayland
            profile = DesktopHelper.get_profile()
            is_gnome = "gnome" in profile.compositor.lower()
            is_wayland = profile.protocol.lower() == "wayland"

            if is_gnome and is_wayland:
                logging.warning(
                    "[Tray] GNOME Wayland detected - AppIndicator extension required"
                )
                logging.warning(
                    "[Tray] Install 'AppIndicator and KStatusNotifierItem Support' GNOME extension for tray icon"
                )
                # Don't show QMessageBox here - event loop isn't ready yet
                # The warning will be shown in MainWindow after UI is ready
        else:
            logging.info("[Tray] System tray is available")

        tray_icon.show()

        # Show window normally or hide if start minimized
        if should_start_minimized:
            logging.info("[Main] Starting minimized (system tray only)")
            # Don't call window.show() - keep it hidden
        else:
            window.show()

        # FORCE START IMMEDIATELY FOR DEBUGGING
        last_wp = config.get_setting("last_wallpaper")
        if last_wp:
            logging.info(f"[DEBUG] Forcing start with: {last_wp}")
            controller.set_wallpaper_for_monitor(0, last_wp)

        exit_code = app.exec()

    except KeyboardInterrupt:
        logging.info("Received KeyboardInterrupt, shutting down...")
    except Exception as e:
        logging.error(f"CRITICAL UI ERROR: {e}")
        exit_code = 1
    finally:
        # Ensure configuration is flushed to disk before shutting down controllers.
        # This forces any pending playback/settings to be persisted.
        try:
            if config:
                # Prefer calling the internal save routine to guarantee immediate write.
                # Fallback to a generic 'save' if present.
                if hasattr(config, "_save") and callable(getattr(config, "_save")):
                    config._save()
                elif hasattr(config, "save") and callable(getattr(config, "save")):
                    config.save()
        except Exception as e:
            logging.error(f"Error saving config on shutdown: {e}")
        controller.shutdown()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
