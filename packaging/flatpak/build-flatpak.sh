#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../" && pwd)"

APPNAME="W-Engine Pro"
APPVERSION="1.0.0"
FLATPAK_DIR="$SCRIPT_DIR"
PYINSTALLER_OUT="$PROJECT_ROOT/dist/pyinstaller"

clean() {
    echo "=== Cleaning previous build ==="
    rm -rf "$FLATPAK_DIR/files"
    rm -rf "$FLATPAK_DIR/build"
    rm -rf "$FLATPAK_DIR/repo"
    rm -rf "$FLATPAK_DIR/.flatpak-builder"
    rm -f "$FLATPAK_DIR"/*.flatpak
    echo "Clean complete."
}

if [ "$1" = "clean" ]; then
    clean
    exit 0
fi

echo "=== $APPNAME Flatpak Builder ==="
echo "Version: $APPVERSION"

mkdir -p "$FLATPAK_DIR/files/bin"
mkdir -p "$FLATPAK_DIR/files/lib"
mkdir -p "$FLATPAK_DIR/files/share/wengine"
mkdir -p "$FLATPAK_DIR/files/share/applications"
mkdir -p "$FLATPAK_DIR/files/share/icons/hicolor/scalable/apps"

echo "=== Step 1: Build Python with PyInstaller ==="
cd "$PROJECT_ROOT"
WENGINE_PROJECT_ROOT="$PROJECT_ROOT" pyinstaller packaging/flatpak/wengine.spec --distpath "$PYINSTALLER_OUT" --workpath "$PROJECT_ROOT/dist/build" -y
cd "$SCRIPT_DIR"

echo "=== Step 2: Copy Python binaries ==="
mkdir -p "$FLATPAK_DIR/files/wengine"
cp -r "$PYINSTALLER_OUT/wengine/"* "$FLATPAK_DIR/files/wengine/"
mv "$FLATPAK_DIR/files/wengine/wengine" "$FLATPAK_DIR/files/wengine/wengine.bin"

echo "=== Removing conflicting libraries ==="
cd "$FLATPAK_DIR/files/wengine/_internal"
rm -f libglib-2.0.so* libgobject-2.0.so* libgio-2.0.so* libgmodule-2.0.so*
rm -f libmount.so* libblkid.so* libsystemd.so* libcap.so*
rm -f libgcrypt.so* libgpg-error.so* libdbus-1.so*
rm -f libgnutls.so* libmp3lame.so* libm.so* libc.so* librt.so* libpthread.so*
rm -f ld-linux-x86-64.so* libdl.so* libutil.so* libnsl.so* libnss_*
cd "$SCRIPT_DIR"

echo "=== Step 3: Copy source code ==="
cd "$PROJECT_ROOT"
cp -r core data engines render threads ui styles main.py "$FLATPAK_DIR/files/share/wengine/"
cd "$SCRIPT_DIR"

copy_binary_with_deps() {
    local bin="$1"
    local dest="$2"
    local bin_path=$(which "$bin" 2>/dev/null)
    if [ -z "$bin_path" ]; then
        echo "Warning: $bin not found in system"
        return 1
    fi
    echo "Bundling $bin..."
    cp "$bin_path" "$dest/"
    for lib in $(ldd "$bin_path" | grep "=>" | awk '{print $3}' | sort -u); do
        if [ -f "$lib" ]; then
            cp -n "$lib" "$FLATPAK_DIR/files/lib/" 2>/dev/null || true
        fi
    done
    for lib in $(ldd "$bin_path" | awk '{print $1}' | sort -u); do
        if [[ "$lib" != "linux-vdso.so"* ]] && [[ "$lib" != "linux-gate.so"* ]]; then
            if [ -f "/lib/$lib" ]; then
                cp -n "/lib/$lib" "$FLATPAK_DIR/files/lib/" 2>/dev/null || true
            fi
            if [ -f "/lib64/$lib" ]; then
                cp -n "/lib64/$lib" "$FLATPAK_DIR/files/lib/" 2>/dev/null || true
            fi
        fi
    done
}

echo "=== Downloading yt-dlp static binary ==="
if [ ! -f "$FLATPAK_DIR/files/bin/yt-dlp" ]; then
    wget -q -O "$FLATPAK_DIR/files/bin/yt-dlp" "https://github.com/yt-dlp/yt-dlp/releases/download/2026.03.17/yt-dlp_linux"
    chmod +x "$FLATPAK_DIR/files/bin/yt-dlp"
fi

copy_binary_with_deps mpv "$FLATPAK_DIR/files/bin"
copy_binary_with_deps mpvpaper "$FLATPAK_DIR/files/bin"

echo "=== Step 5: Copy desktop files and icons ==="
cp "$FLATPAK_DIR/wengine.desktop" "$FLATPAK_DIR/files/share/applications/org.wengine.Pro.desktop"
cp -n "$PROJECT_ROOT/data/W-Enginepro.svg" "$FLATPAK_DIR/files/share/icons/hicolor/scalable/apps/" 2>/dev/null || true
cp -n "$PROJECT_ROOT/data/W-Enginepro.svg" "$FLATPAK_DIR/wengine.svg" 2>/dev/null || true

echo "=== Step 6: Create AppRun ==="
cat > "$FLATPAK_DIR/AppRun" << 'APPRUN_EOF'
#!/bin/bash

# Wrappers are already installed during build via host-bin-wrappers module
# Just set PATH and library paths
export PATH="/app/bin:/run/host/usr/bin:/usr/bin:$PATH"
export LD_LIBRARY_PATH="/app/lib:/app/lib/x86_64-linux-gnu:/app/bin/wengine/_internal:$LD_LIBRARY_PATH"

for dir in "/app/bin/wengine/_internal"; do
    if [ -d "$dir" ]; then
        export PYTHONPATH="$dir:$PYTHONPATH"
        break
    fi
done

for dir in "/app/lib"/PySide6/Qt; do
    if [ -d "$dir" ]; then
        export QT_PLUGIN_PATH="$dir/plugins:$QT_PLUGIN_PATH"
        export QT_QPA_PLATFORM_PLUGIN_PATH="$dir/plugins/platforms:$QT_QPA_PLATFORM_PLUGIN_PATH"
        export QML2_IMPORT_PATH="$dir/qml:$QML2_IMPORT_PATH"
        break
    fi
done

export PATH="/app/bin:$PATH"

if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    export QT_QPA_PLATFORM="wayland;xcb"
else
    export QT_QPA_PLATFORM="xcb"
fi

exec /app/bin/wengine/wengine "$@"
APPRUN_EOF
chmod +x "$FLATPAK_DIR/AppRun"

echo "=== Step 8: Build Flatpak ==="
if ! command -v flatpak-builder &> /dev/null; then
    echo "flatpak-builder not found. Please install it."
    return 1
fi

mkdir -p "$FLATPAK_DIR/build"
cd "$FLATPAK_DIR"

# Build with force-clean to avoid stale cache issues
flatpak-builder --force-clean --user \
    "$FLATPAK_DIR/build/org.wengine.Pro" \
    "$FLATPAK_DIR/org.wengine.Pro.json"

# Create local repo and export .flatpak bundle
echo ""
echo "=== Creating .flatpak bundle ==="
flatpak build-init "$FLATPAK_DIR/repo" 2>/dev/null || true

# Export built app to local repo
flatpak build-export "$FLATPAK_DIR/repo" "$FLATPAK_DIR/build/org.wengine.Pro" --no-update-summary 2>/dev/null || \
flatpak build-export "$FLATPAK_DIR/repo" "$FLATPAK_DIR/build/org.wengine.Pro"

# Create single-file bundle
BUNDLE_NAME="W-Engine-Pro-$APPVERSION-x86_64.flatpak"
flatpak build-bundle "$FLATPAK_DIR/repo" "$FLATPAK_DIR/$BUNDLE_NAME" org.wengine.Pro

echo ""
echo "=== Flatpak Build Complete ==="
echo "Bundle: $FLATPAK_DIR/$BUNDLE_NAME"
echo "To install bundle: flatpak install $FLATPAK_DIR/$BUNDLE_NAME"
echo "To run: flatpak run org.wengine.Pro"
