#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../" && pwd)"

APPNAME="W-Engine Pro"
APPVERSION="1.0.0"
DIST_DIR="$PROJECT_ROOT/dist"
PYINSTALLER_OUT="$DIST_DIR/pyinstaller"
BUILD_DIR="$DIST_DIR/build"

# ============================================================================
# Shared Functions
# ============================================================================

build_pyinstaller() {
    echo ""
    echo "=== Building with PyInstaller ==="
    cd "$PROJECT_ROOT"
    WENGINE_PROJECT_ROOT="$PROJECT_ROOT" pyinstaller \
        packaging/flatpak/wengine.spec \
        --distpath "$PYINSTALLER_OUT" \
        --workpath "$BUILD_DIR" \
        -y
    cd "$SCRIPT_DIR"
    echo "PyInstaller build complete."
}

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
            cp -n "$lib" "$dest/" 2>/dev/null || true
        fi
    done

    for lib in $(ldd "$bin_path" | awk '{print $1}' | sort -u); do
        if [[ "$lib" != "linux-vdso.so"* ]] && [[ "$lib" != "linux-gate.so"* ]]; then
            if [ -f "/lib/$lib" ]; then
                cp -n "/lib/$lib" "$dest/" 2>/dev/null || true
            fi
            if [ -f "/lib64/$lib" ]; then
                cp -n "/lib64/$lib" "$dest/" 2>/dev/null || true
            fi
        fi
    done
}

download_yt_dlp() {
    local dest="$1"
    echo "=== Downloading yt-dlp static binary ==="
    rm -f "$dest/yt-dlp"
    wget -q -O "$dest/yt-dlp" \
        "https://github.com/yt-dlp/yt-dlp/releases/download/2026.03.17/yt-dlp_linux"
    chmod +x "$dest/yt-dlp"
    echo "yt-dlp downloaded."
}

copy_source_code() {
    local dest="$1"
    echo "=== Copying source code ==="
    cd "$PROJECT_ROOT"
    cp -r core data engines render threads ui styles main.py "$dest/"
    cd "$SCRIPT_DIR"
}

# ============================================================================
# Flatpak Build Function
# ============================================================================

build_flatpak() {
    echo ""
    echo "========================================"
    echo "=== $APPNAME Flatpak Builder ==="
    echo "========================================"

    local FLATPAK_DIR="$SCRIPT_DIR/flatpak"

    echo "=== Cleaning previous Flatpak build ==="
    rm -rf "$FLATPAK_DIR/files" "$FLATPAK_DIR/build" "$FLATPAK_DIR/repo" "$FLATPAK_DIR/.flatpak-builder"
    rm -f "$FLATPAK_DIR"/*.flatpak
    echo "Clean complete."

    mkdir -p "$FLATPAK_DIR/files/bin"
    mkdir -p "$FLATPAK_DIR/files/lib"
    mkdir -p "$FLATPAK_DIR/files/share/wengine"
    mkdir -p "$FLATPAK_DIR/files/share/applications"
    mkdir -p "$FLATPAK_DIR/files/share/icons/hicolor/scalable/apps"

    build_pyinstaller

    echo "=== Copying Python binaries ==="
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

    copy_source_code "$FLATPAK_DIR/files/share/wengine"

    echo "=== Bundling binaries ==="
    download_yt_dlp "$FLATPAK_DIR/files/bin"
    copy_binary_with_deps mpv "$FLATPAK_DIR/files/bin"
    copy_binary_with_deps mpvpaper "$FLATPAK_DIR/files/bin"

    echo "=== Copying desktop files and icons ==="
    cp "$FLATPAK_DIR/wengine.desktop" "$FLATPAK_DIR/files/share/applications/org.wengine.Pro.desktop"
    cp -n "$PROJECT_ROOT/data/W-Enginepro.svg" "$FLATPAK_DIR/files/share/icons/hicolor/scalable/apps/" 2>/dev/null || true
    cp -n "$PROJECT_ROOT/data/W-Enginepro.svg" "$FLATPAK_DIR/wengine.svg" 2>/dev/null || true

    echo "=== Creating AppRun ==="
    cat > "$FLATPAK_DIR/AppRun" << 'APPRUN_EOF'
#!/bin/bash
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

    echo "=== Building Flatpak ==="
    if ! command -v flatpak-builder &> /dev/null; then
        echo "ERROR: flatpak-builder not found. Please install it."
        return 1
    fi

    mkdir -p "$FLATPAK_DIR/build"
    cd "$FLATPAK_DIR"
    flatpak-builder --force-clean --user \
        "$FLATPAK_DIR/build/org.wengine.Pro" \
        "$FLATPAK_DIR/org.wengine.Pro.json"

    echo ""
    # Export to local repo and create .flatpak bundle
    echo ""
    echo "=== Creating .flatpak bundle ==="
    flatpak build-export "$FLATPAK_DIR/repo" "$FLATPAK_DIR/build/org.wengine.Pro" 2>/dev/null || \
    flatpak build-export "$FLATPAK_DIR/repo" "$FLATPAK_DIR/build/org.wengine.Pro"

    BUNDLE_NAME="W-Engine-Pro-$APPVERSION-x86_64.flatpak"
    flatpak build-bundle "$FLATPAK_DIR/repo" "$FLATPAK_DIR/$BUNDLE_NAME" org.wengine.Pro

    echo ""
    echo "=== Flatpak Build Complete ==="
    echo "Bundle: $FLATPAK_DIR/$BUNDLE_NAME"
    echo "To install: flatpak install $FLATPAK_DIR/$BUNDLE_NAME"
    echo "To run: flatpak run org.wengine.Pro"
}

# ============================================================================
# AppImage Build Function
# ============================================================================

build_appimage() {
    echo ""
    echo "========================================"
    echo "=== $APPNAME AppImage Builder ==="
    echo "========================================"

    local APPIMAGE_DIR="$SCRIPT_DIR/appimage"
    local APPDIR="$APPIMAGE_DIR/AppDir"

    echo "=== Cleaning previous AppImage build ==="
    rm -rf "$APPDIR" "$DIST_DIR"/*.AppImage
    echo "Clean complete."

    mkdir -p "$APPDIR/usr/lib"
    mkdir -p "$APPDIR/usr/bin"
    mkdir -p "$APPDIR/usr/share/wengine"
    mkdir -p "$APPDIR/usr/share/applications"
    mkdir -p "$APPDIR/usr/share/icons/hicolor/scalable/apps"

    build_pyinstaller

    echo "=== Copying Python binaries to AppDir ==="
    cp -r "$PYINSTALLER_OUT/"* "$APPDIR/usr/"

    echo "=== Removing system libraries from PyInstaller output ==="
    cd "$APPDIR/usr"
    rm -f libglib-2.0.so* libgobject-2.0.so* libgio-2.0.so* libgmodule-2.0.so*
    rm -f libmount.so* libblkid.so* libsystemd.so* libcap.so*
    rm -f libgcrypt.so* libgpg-error.so* libdbus-1.so*
    rm -f libgnutls.so* libmp3lame.so* libm.so* libc.so* librt.so* libpthread.so*
    rm -f ld-linux-x86-64.so* libdl.so* libutil.so* libnsl.so* libnss_*
    cd "$SCRIPT_DIR"

    copy_source_code "$APPDIR/usr/share/wengine"

    echo "=== Bundling binaries ==="
    download_yt_dlp "$APPDIR/usr/bin"
    copy_binary_with_deps mpv "$APPDIR/usr/bin"
    copy_binary_with_deps mpvpaper "$APPDIR/usr/bin"

    echo "=== Removing system libraries from bundled binaries ==="
    cd "$APPDIR/usr/bin"
    rm -f libglib-2.0.so* libgobject-2.0.so* libgio-2.0.so* libgmodule-2.0.so*
    rm -f libmount.so* libblkid.so* libsystemd.so* libcap.so*
    rm -f libgcrypt.so* libgpg-error.so* libdbus-1.so*
    rm -f libgnutls.so* libmp3lame.so* libm.so* libc.so* librt.so* libpthread.so*
    rm -f ld-linux-x86-64.so* libdl.so* libutil.so* libnsl.so* libnss_*
    cd "$SCRIPT_DIR"

    echo "=== Creating Python symlinks ==="
    PYTHON_BASE=$(ls -d "$APPDIR"/usr/lib/python3.* 2>/dev/null | head -1)
    if [ -n "$PYTHON_BASE" ]; then
        ln -sf "$PYTHON_BASE" "$APPDIR/usr/lib/python3"
    fi

    echo "=== Copying desktop files and icons ==="
    cp "$APPIMAGE_DIR/wengine.desktop" "$APPDIR/usr/share/applications/"
    cp "$APPIMAGE_DIR/wengine.desktop" "$APPDIR/wengine.desktop"
    cp -n "$PROJECT_ROOT/data/W-Enginepro.svg" "$APPDIR/usr/share/icons/hicolor/scalable/apps/wengine.svg" 2>/dev/null || true
    cp -n "$PROJECT_ROOT/data/W-Enginepro.svg" "$APPDIR/wengine.svg" 2>/dev/null || true
    cp -n "$PROJECT_ROOT/data/W-Enginepro.svg" "$APPDIR/.DirIcon" 2>/dev/null || true

    echo "=== Creating AppRun ==="
    cat > "$APPDIR/AppRun" << 'APPRUN_EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"

export LD_LIBRARY_PATH="$HERE/usr/lib:$HERE/usr/lib/x86_64-linux-gnu:$HERE/usr/wengine/_internal:$LD_LIBRARY_PATH"

for dir in "$HERE/usr/lib"/python3.*; do
    if [ -d "$dir" ]; then
        export PYTHONHOME="$HERE/usr"
        export PYTHONPATH="$HERE/usr/share/wengine:$dir/site-packages"
        break
    fi
done

for dir in "$HERE/usr/wengine/_internal"; do
    if [ -d "$dir" ]; then
        export PYTHONPATH="$dir:$PYTHONPATH"
        break
    fi
done

for dir in "$HERE/usr/lib"/PySide6/Qt; do
    if [ -d "$dir" ]; then
        export QT_PLUGIN_PATH="$dir/plugins:$QT_PLUGIN_PATH"
        export QT_QPA_PLATFORM_PLUGIN_PATH="$dir/plugins/platforms:$QT_QPA_PLATFORM_PLUGIN_PATH"
        export QML2_IMPORT_PATH="$dir/qml:$QML2_IMPORT_PATH"
        break
    fi
done

export PATH="$HERE/usr/bin:$PATH"

if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    export QT_QPA_PLATFORM="wayland;xcb"
else
    export QT_QPA_PLATFORM="xcb"
fi

exec "$HERE/usr/wengine/wengine.bin" "$@"
APPRUN_EOF
    chmod +x "$APPDIR/AppRun"

    echo "=== Creating launcher symlink ==="
    cp "$PYINSTALLER_OUT/wengine/wengine" "$APPDIR/usr/wengine/wengine.bin"
    ln -sf "../AppRun" "$APPDIR/usr/bin/wengine"

    echo "=== Building AppImage ==="
    local APPIMAGETOOL="$APPIMAGE_DIR/appimagetool"
    local LINUXDEPLOY="$APPIMAGE_DIR/linuxdeploy"

    if [ -x "$APPIMAGETOOL" ]; then
        cd "$DIST_DIR"
        "$APPIMAGETOOL" "$APPDIR" "W-Engine-Pro-$APPVERSION-x86_64.AppImage"
        echo "AppImage created: $DIST_DIR/W-Engine-Pro-$APPVERSION-x86_64.AppImage"
    elif [ -x "$LINUXDEPLOY" ]; then
        cd "$DIST_DIR"
        set +e
        "$LINUXDEPLOY" --appdir="$APPDIR" --output=appimage \
            -i "$APPDIR/usr/share/icons/hicolor/scalable/apps/wengine.svg" \
            -d "$APPDIR/usr/share/applications/wengine.desktop" 2>&1
        set -e
        if [ -f "$DIST_DIR/W-Engine-Pro-$APPVERSION-x86_64.AppImage" ]; then
            echo "AppImage created: $DIST_DIR/W-Engine-Pro-$APPVERSION-x86_64.AppImage"
        else
            echo "AppImage not created. Checking alternatives..."
            ls -la "$DIST_DIR"/*.AppImage 2>/dev/null || echo "No AppImage found"
        fi
    else
        echo "WARNING: No packaging tool found. AppImage not created."
    fi

    echo ""
    echo "=== AppImage Build Complete ==="
    echo "AppDir: $APPDIR"
    echo "Output: $DIST_DIR"
}

# ============================================================================
# Main Entry Point
# ============================================================================

clean_all() {
    echo "=== Cleaning all builds ==="
    rm -rf "$DIST_DIR"
    rm -rf "$SCRIPT_DIR/flatpak/files" "$SCRIPT_DIR/flatpak/build" \
           "$SCRIPT_DIR/flatpak/repo" "$SCRIPT_DIR/flatpak/.flatpak-builder"
    rm -rf "$SCRIPT_DIR/appimage/AppDir"
    rm -f "$SCRIPT_DIR/flatpak"/*.flatpak "$DIST_DIR"/*.AppImage
    echo "Clean complete."
}

usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  flatpak    Build Flatpak package"
    echo "  appimage   Build AppImage package"
    echo "  clean      Clean all build artifacts"
    echo "  help       Show this help message"
    echo ""
    echo "If no command is given, builds both Flatpak and AppImage."
}

case "${1:-all}" in
    flatpak)
        build_flatpak
        ;;
    appimage)
        build_appimage
        ;;
    clean)
        clean_all
        ;;
    all)
        build_flatpak
        build_appimage
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        echo "ERROR: Unknown command '$1'"
        usage
        exit 1
        ;;
esac
