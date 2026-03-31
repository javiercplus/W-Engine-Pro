import logging
import os
import socket
import json


ENV_VARS_TO_STRIP = [
    "LD_LIBRARY_PATH",
    "PYTHONPATH",
    "PYTHONHOME",
    "QT_PLUGIN_PATH",
    "LD_PRELOAD",
]

RESOLUTION_MAP = {
    "1080p (Full HD)": "scale=-1:1080",
    "720p (HD)": "scale=-1:720",
    "480p (SD)": "scale=-1:480",
}

GAMMA_UPPER_RANGE = 4.0
GAMMA_LOWER_RANGE = 0.9
GAMMA_SCALE = 100


def clean_environment(env=None):
    """Return a copy of environment with packaging variables removed."""
    clean_env = (env or os.environ).copy()
    for var in ENV_VARS_TO_STRIP:
        clean_env.pop(var, None)
    return clean_env


def gamma_ui_to_mpv(gamma_ui):
    """Convert UI gamma (0.1-5.0, neutral 1.0) to MPV gamma (-100 to 100, neutral 0)."""
    try:
        gamma_ui = float(gamma_ui)
        if gamma_ui > 1.0:
            return int((gamma_ui - 1.0) / GAMMA_UPPER_RANGE * GAMMA_SCALE)
        else:
            return int((gamma_ui - 1.0) / GAMMA_LOWER_RANGE * GAMMA_SCALE)
    except (ValueError, TypeError):
        return 0


def build_common_mpv_args(config, socket_path, wid_needed=False):
    """Build the common set of mpv arguments used by all backends."""
    args = []

    if wid_needed:
        args.append("--wid=%WID")

    loop = "inf" if config.get_setting("loop", "Loop") == "Loop" else "no"
    args.extend([
        f"--loop-file={loop}",
        f"--mute={'yes' if config.get_setting('mute', True) else 'no'}",
        f"--hwdec={config.get_setting('hwdec', 'auto-safe')}",
        "--vo=gpu",
        "--gpu-context=auto",
        "--profile=low-latency",
        "--untimed",
        "--panscan=1.0",
        "--keep-open=yes",
        f"--input-ipc-server={socket_path}",
        "--no-osc",
        "--no-osd-bar",
        "--no-input-default-bindings",
        "--idle",
    ])

    if config.get_setting("no_audio", True):
        args.append("--no-audio")

    # Video resolution filter
    res_setting = config.get_setting("video_resolution", "Nativa")
    if res_setting in RESOLUTION_MAP:
        args.append(f"--vf={RESOLUTION_MAP[res_setting]}")

    # FPS limit
    fps_limit = config.get_setting("fps_limit", 60)
    args.append(f"--override-display-fps={fps_limit}")

    # GPU API
    gpu_api = config.get_setting("gpu_api", "auto")
    if gpu_api != "auto":
        args.append(f"--gpu-api={gpu_api}")

    # Cache flags
    cache_flags = config.get_setting("_mpv_cache_flags", [])
    args.extend(cache_flags)

    # Live properties
    for prop in ["brightness", "contrast", "saturation"]:
        val = config.get_setting(prop, 0)
        args.append(f"--{prop}={val}")

    # Gamma
    gamma_ui = config.get_setting("gamma", 1.0)
    args.append(f"--gamma={gamma_ui_to_mpv(gamma_ui)}")

    return args


def send_ipc_command(socket_paths, command, *args, timeout=0.05):
    """Send a command to one or more mpv IPC sockets."""
    if not socket_paths:
        return False

    success = True
    for socket_path in socket_paths:
        if not os.path.exists(socket_path):
            success = False
            continue

        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(timeout)
                client.connect(socket_path)
                msg = {"command": [command] + list(args)}
                client.sendall((json.dumps(msg) + "\n").encode())
        except (socket.error, socket.timeout, BrokenPipeError, ConnectionRefusedError):
            success = False

    return success


def wait_for_ipc(sockets, attempts=10, interval=0.1):
    """Wait for all IPC sockets to appear."""
    for _ in range(attempts):
        if sockets and all(os.path.exists(s) for s in sockets):
            return True
        import time
        time.sleep(interval)
    return False


def prepare_mpv_binary():
    """Find the mpv binary, preferring bundled version if in AppImage."""
    import shutil

    appdir = os.environ.get("APPDIR")
    if appdir:
        bundled = os.path.join(appdir, "usr/bin/mpv")
        if os.path.exists(bundled):
            return bundled, os.environ.copy()

    system = shutil.which("mpv")
    if system:
        return system, clean_environment()

    return None, None
