import sys
import logging
import os
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt, QSize
from ui.main_window import MainWindow
from core.config_manager import ConfigManager
from core.engine_controller import EngineController
from core.resource_manager import ResourceManager

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("W-Engine Pro")
    app.setDesktopFileName("w-engine-pro") 
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
        icon_path_png = os.path.join(os.path.dirname(__file__), "data", "W-Enginepro.png")
        if os.path.exists(icon_path_png):
            app_icon = QIcon(icon_path_png)
            app.setWindowIcon(app_icon)
        else:
            app_icon = QIcon.fromTheme("video-display")

    config = ConfigManager()
    resources = ResourceManager(config)
    controller = EngineController(config_manager=config)
    
    exit_code = 0
    try:
        window = MainWindow(controller=controller, config=config, resources=resources)
        window.setWindowIcon(app_icon)
        
        tray_icon = QSystemTrayIcon(app_icon, app)
        tray_menu = QMenu()
        
        show_action = QAction("Mostrar Interfaz", app)
        show_action.triggered.connect(window.showNormal)
        
        pause_action = QAction("Pausar/Reanudar", app)
        pause_action.triggered.connect(lambda: controller.pause_all()) 
        
        quit_action = QAction("Salir", app)
        quit_action.triggered.connect(app.quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(pause_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        tray_icon.setContextMenu(tray_menu)
        tray_icon.show()
        
        window.show()
        
        controller.start_all(default_engine="mpv")
        
        exit_code = app.exec()

    except Exception as e:
        logging.error(f"CRITICAL UI ERROR: {e}")
        exit_code = 1
    finally:
        controller.shutdown()

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
