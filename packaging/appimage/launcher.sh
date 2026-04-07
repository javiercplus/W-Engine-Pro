#!/bin/bash
set -e

# Localizar el directorio base del AppImage
SELF=$(readlink -f "$0")
HERE="${SELF%/*}"
APPDIR="${HERE%/usr/bin}"

# 1. Configurar Entorno para Portabilidad
export PATH="$APPDIR/usr/bin:$PATH"
export LD_LIBRARY_PATH="$APPDIR/usr/lib:$LD_LIBRARY_PATH"

# Usar el Python embebido en el AppImage
PYTHON_BIN="$APPDIR/usr/bin/python3"

# Configurar PYTHONPATH para el código de la app y sus dependencias
# El Python portátil ya conoce su propia site-packages si se ejecuta desde su binario,
# pero añadimos explícitamente el código de la app.
export PYTHONPATH="$APPDIR/usr/share/wengine:$PYTHONPATH"

# 2. Configurar Qt para portabilidad
# PySide6 instala los plugins en site-packages/PySide6/Qt/plugins
# Buscamos dinámicamente para mayor robustez
PYSIDE_PLUGINS=$(find "$APPDIR/usr/lib" -type d -name "plugins" | grep PySide6 | head -n 1)
if [ -n "$PYSIDE_PLUGINS" ]; then
    export QT_PLUGIN_PATH="$PYSIDE_PLUGINS:$QT_PLUGIN_PATH"
fi

# 3. Detectar Entorno Gráfico
if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    export QT_QPA_PLATFORM="wayland;xcb"
else
    export QT_QPA_PLATFORM="xcb"
fi

# 4. Validar mpv (Requisito crítico)
# Intentamos usar libmpv si está bundled, o el del sistema
if ! command -v mpv &> /dev/null && [ ! -f "$APPDIR/usr/lib/libmpv.so" ]; then
    echo "AVISO: 'mpv' no encontrado. Algunas funciones pueden fallar."
fi

# 5. Ejecutar la aplicación usando el Python del bundle
exec "$PYTHON_BIN" "$APPDIR/usr/share/wengine/main.py" "$@"
