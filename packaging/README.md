# W-Engine Pro Packaging

This directory contains build scripts and packaging configuration for W-Engine Pro.

## Build Scripts

### Main Build Script: `build.sh`

The main entry point for building all package formats.

```bash
# Build both Flatpak and AppImage
./build.sh

# Build only Flatpak
./build.sh flatpak

# Build only AppImage
./build.sh appimage

# Clean all build artifacts
./build.sh clean

# Show help
./build.sh help
```

## Package Formats

### 1. Flatpak

**Location:** `flatpak/`

Flatpak is the recommended distribution format for Linux applications. It provides:
- Sandboxed execution
- Cross-distribution compatibility
- Easy installation via Flathub

**Build Requirements:**
- `flatpak` and `flatpak-builder`
- PyInstaller (`pip install pyinstaller`)
- Free disk space: ~5GB

**Build Steps:**
```bash
# Install dependencies (Ubuntu/Debian)
sudo apt install flatpak flatpak-builder

# Add Flathub remote
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# Install runtime and SDK
flatpak install flathub org.freedesktop.Platform//24.08
flatpak install flathub org.freedesktop.Sdk//24.08

# Build
./build.sh flatpak
```

**Output:** `flatpak/W-Engine-Pro-1.0.0-x86_64.flatpak`

**Installation:**
```bash
flatpak install flatpak/W-Engine-Pro-1.0.0-x86_64.flatpak
flatpak run org.wengine.Pro
```

### 2. AppImage

**Location:** `appimage/`

AppImage provides a portable, self-contained executable that runs on most Linux distributions.

**Build Requirements:**
- Ubuntu 22.04 or compatible (for glibc compatibility)
- PyInstaller
- `linuxdeploy` or `appimagetool`
- System libraries: mpv, libpulse, etc.

**Build Steps:**
```bash
# Install dependencies (Ubuntu 22.04)
sudo apt install wget fuse libfuse2 desktop-file-utils \
  libglib2.0-dev libxcb-xinerama0 libxcb-cursor0 \
  libxkbcommon-x11-0 libpulse0 libmpv2 mpv

# Install Python dependencies
pip install pyinstaller

# Download packaging tools (first time only)
# The build script will download linuxdeploy and appimagetool automatically

# Build
./build.sh appimage
```

**Output:** `dist/W-Engine-Pro-1.0.0-x86_64.AppImage`

**Installation:**
```bash
chmod +x dist/W-Engine-Pro-1.0.0-x86_64.AppImage
./dist/W-Engine-Pro-1.0.0-x86_64.AppImage
```

## GitHub Actions Workflow

The CI/CD pipeline is defined in `.github/workflows/build-packages.yml`.

**Triggers:**
- Push to `main` or `master` branches
- Git tags matching `v*` pattern
- Manual trigger via `workflow_dispatch`
- Pull requests to main branches

**Jobs:**

1. **flatpak** - Builds Flatpak package using the packaging script
2. **appimage** - Builds AppImage package using the packaging script
3. **release** - Creates GitHub Release with artifacts (only on version tags)

**Artifacts:**
- Built packages are uploaded as workflow artifacts
- On version tags, packages are attached to GitHub Releases

## Directory Structure

```
packaging/
├── build.sh                    # Main build orchestration script
├── README.md                   # This file
├── flatpak/
│   ├── org.wengine.Pro.json   # Flatpak manifest
│   ├── org.wengine.Pro.appdata.xml  # AppStream metadata
│   ├── AppRun                 # Flatpak entry point script
│   ├── wengine.desktop        # Desktop entry file
│   ├── wengine.svg            # Application icon
│   └── build-flatpak.sh       # Legacy Flatpak build script
└── appimage/
    ├── AppDir/                # AppImage root filesystem
    │   ├── AppRun             # AppImage entry point
    │   ├── wengine.desktop    # Desktop entry
    │   ├── wengine.svg        # Application icon
    │   └── usr/               # Application files
    └── [packaging tools]      # linuxdeploy, appimagetool (downloaded during build)
```

## Version Management

Update the version number in:
1. `packaging/build.sh` - `APPVERSION` variable
2. Git tag: `git tag v1.0.0 && git push origin v1.0.0`

## Troubleshooting

### Flatpak build fails
- Ensure you have the correct runtime and SDK installed
- Try cleaning the build: `./build.sh clean`
- Check that `flatpak-builder` version is >= 1.2

### AppImage doesn't run on target system
- AppImage is built on Ubuntu 22.04 for maximum compatibility
- Older systems may need to be built on an older base (Ubuntu 20.04)
- Ensure FUSE is installed: `sudo apt install libfuse2`

### PyInstaller build fails
- Install all Python dependencies: `pip install -r requirements.txt`
- Ensure PyInstaller is installed: `pip install pyinstaller`
- Check the spec file: `packaging/flatpak/wengine.spec`

### Missing tray icon in GNOME
GNOME requires the AppIndicator extension. See the application warning for details.

## Contributing

When updating packaging:
1. Test builds locally before committing
2. Update this README if build process changes
3. Ensure CI workflow reflects local build scripts
4. Test the resulting packages on multiple distributions
