W-Engine-Pro
Motor nativo de wallpapers animados para Linux. Alto rendimiento (Python 3.14 + Qt6), bajo consumo y formato AppImage universal. Pausa automática en juegos/pantalla completa.

<img width="1368" height="768" alt="Captura de pantalla_2026-03-17_22-51-53" src="https://github.com/user-attachments/assets/6fa054fb-7709-4970-980a-38535e39e4d8" />

<img width="1368" height="768" alt="Captura de pantalla_2026-03-17_22-51-31" src="https://github.com/user-attachments/assets/29d0edb9-62ac-42a5-b904-aac108a557c3" />

<img width="1091" height="731" alt="Captura de pantalla_2026-03-17_22-52-09" src="https://github.com/user-attachments/assets/aa990bf3-2a93-4177-b9c2-eb86596c8492" />

W-Engine Pro es un motor de wallpapers dinámicos para Linux, diseñado para ofrecer una experiencia moderna, fluida y altamente personalizable, similar a Wallpaper Engine pero optimizado para entornos Linux.

Descripción:

W-Engine Pro nace con el objetivo de llevar la personalización del escritorio Linux a otro nivel, permitiendo el uso de fondos animados, contenido multimedia y wallpapers por URL sin sacrificar rendimiento.

El motor implementa un sistema inteligente de optimización que adapta el consumo de recursos según la actividad del sistema.

Características:
Soporte para wallpapers en video
Wallpapers mediante URL (streaming)
Cambios en tiempo real (sin reiniciar)
UI dinámica con Qt6
Motor reactivo (event-driven)
Auto-guardado inteligente
Soporte multi-monitor
Optimización de CPU/GPU

Funciones experimentales:
Integración como fondo real del escritorio (sin cubrir iconos)
Compatibilidad avanzada con distintos entornos
Soporte parcial en Wayland (limitaciones del compositor)

Compatibilidad:
Entorno	Estado
KDE Plasma (X11) Estable
XFCE Estable
GNOME (X11) Parcial
Wayland Experimental

Tecnologías:
Python 3.14
Qt6 (PyQt / PySide)
OpenGL / Video backend
Arquitectura modular (Engine + UI desacoplados)

Arquitectura:
El proyecto está dividido en módulos principales:

core/
 ├── engine_controller.py
 ├── surface_manager.py
 └── config_manager.py

ui/
 └── main_window.py

EngineController → controla el motor de wallpapers
SurfaceManager → renderizado y gestión de ventanas
ConfigManager → configuración y estado
UI (Qt) → interfaz gráfica

:Estado actual
En desarrollo activo

Se están implementando:
Sistema de perfiles
Mejor sincronización UI ↔ motor
Soporte extendido para Wayland
Optimización avanzada del render

Roadmap:
Sistema de perfiles tipo Wallpaper Engine
Plugins / extensiones
Mejor integración con escritorios Linux
UI más avanzada y personalizable

Autor:
Desarrollado por Alexander

Licencia:
Este proyecto está bajo la licencia GPLv3.

Contribuciones:
Las contribuciones son bienvenidas.
Puedes abrir issues o pull requests para mejorar el proyecto.
