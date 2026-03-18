import subprocess
import os
import time
import shutil
import re
import json
import socket
import logging

class RendererManager:
    """Gestiona el proceso de bajo nivel que renderiza el video (mpv/mpvpaper)."""
    def __init__(self):
        self.bg_proc = None
        self.socket_path = "/tmp/mpv-bg-socket"
        self.deps = {
            "xwinwrap": shutil.which("xwinwrap"),
            "mpv": shutil.which("mpv"),
            "mpvpaper": shutil.which("mpvpaper")
        }
        self.is_wayland = 'WAYLAND_DISPLAY' in os.environ or os.environ.get('XDG_SESSION_TYPE') == 'wayland'

    def send_command(self, command, *args):
        """Sends a JSON-RPC command to the mpv process with retries."""
        if not os.path.exists(self.socket_path):
            print(f"[Renderer] Error: Socket no encontrado en {self.socket_path}")
            return False
            
        for i in range(5):
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                    client.settimeout(0.5)
                    client.connect(self.socket_path)
                    msg = {"command": [command] + list(args)}
                    client.sendall((json.dumps(msg) + "\n").encode())
                return True
            except (socket.error, socket.timeout) as e:
                time.sleep(0.1)
        print(f"[Renderer] Error: No se pudo enviar comando {command} tras 5 intentos.")
        return False

    def update_setting(self, key, value):
        """Intenta actualizar un ajuste dinámicamente sin reiniciar."""
        if not self.bg_proc:
            logging.warning("[Renderer] Cannot update setting: No process running.")
            return False

        logging.info(f"[Renderer] Dynamic update: {key} = {value}")

        if key == "volume":
            return self.send_command("set_property", "volume", value)
        elif key == "mute":
            return self.send_command("set_property", "mute", value)
        elif key == "playback_rate":
            return self.send_command("set_property", "speed", value)
        elif key == "loop":
            if value == "Loop":
                self.send_command("set_property", "play-dir", "forward")
                self.send_command("set_property", "loop-file", "inf")
                self.send_command("set_property", "loop-playlist", "inf")
                self.send_command("set_property", "pause", False)
                return True
            elif value == "Stop":
                return self.send_command("set_property", "pause", True)
            return False
        elif key == "fit":
            if value == "Stretch": 
                self.send_command("set_property", "video-zoom", 0)
                self.send_command("set_property", "keepaspect", False)
                self.send_command("set_property", "panscan", 0.0)
            elif value == "Cover": 
                self.send_command("set_property", "video-zoom", 0)
                self.send_command("set_property", "keepaspect", True)
                self.send_command("set_property", "panscan", 1.0)
            elif value == "Contain":
                self.send_command("set_property", "video-zoom", 0)
                self.send_command("set_property", "keepaspect", True)
                self.send_command("set_property", "panscan", 0.0)
            elif value == "Center":
                self.send_command("set_property", "video-zoom", 0)
                self.send_command("set_property", "panscan", 0.0)
                self.send_command("set_property", "keepaspect", True)
            return True
        return False

    def restart(self, config, video_path):
        print("[Renderer] Reiniciando renderer...")
        self.stop()
        time.sleep(0.3)
        self.start(config, video_path)

    def start(self, config, video_path):
        if not video_path:
            print("[Renderer] Ruta de video inválida.")
            return False

        is_url = video_path.startswith(("http://", "https://", "rtsp://", "udp://"))
        if not is_url and not os.path.exists(video_path):
            print(f"[Renderer] Archivo no encontrado: {video_path}")
            return False

        self.stop()
        time.sleep(0.2)

        if os.path.exists(self.socket_path):
            try: os.remove(self.socket_path)
            except OSError: pass

        if self.is_wayland:
            if not self.deps["mpvpaper"]:
                print("[Renderer] 'mpvpaper' no encontrado. Usando fallback portátil (mpv directo)...")
                cmd = ["mpv"] + self._build_mpv_args(config, wid_needed=False)
                cmd += ["--gpu-context=wayland", "--force-window=yes", "--title=W-Engine-Wallpaper", video_path]
                self.bg_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            
            layout_mode = config.get("layout_mode", "Individual")
            target_monitor = config.get("target_monitor", "Auto")
            
            if layout_mode == "Extendido (Span)":
                outputs = ["*"]
            elif layout_mode == "Duplicado":
                outputs = ["*"] 
            else:
                outputs = ["*"] if target_monitor == "Auto" else [target_monitor]

            mpv_opts = self._build_mpv_args(config, wid_needed=False)
            base_cmd = ["mpvpaper"]
            for opt in mpv_opts:
                if opt: base_cmd.extend(["-o", opt])

            for out in outputs:
                cmd = base_cmd + [out, video_path]
                self.bg_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True

        if not self.deps["xwinwrap"]:
            print("[Renderer] ERROR: 'xwinwrap' no encontrado.")
            return False

        layout_mode = config.get("layout_mode", "Individual")
        target_monitor = config.get("target_monitor", "Auto")
        
        xwin_geometries = []

        try:
            output = subprocess.check_output("xrandr --query", shell=True).decode()
            
            if layout_mode == "Extendido (Span)":
                match = re.search(r"current (\d+) x (\d+)", output)
                if match:
                    xwin_geometries = [(f"{match.group(1)}x{match.group(2)}+0+0", "Combined")]
            
            elif layout_mode == "Duplicado":
                matches = re.finditer(r"(\S+) connected (?:primary )?(\d+x\d+\+\d+\+\d+)", output)
                for m in matches:
                    xwin_geometries.append((m.group(2), m.group(1)))
            
            else:
                if target_monitor == "Auto":
                    match = re.search(r"(\S+) connected primary (\d+x\d+\+\d+\+\d+)", output)
                    if not match:
                        match = re.search(r"(\S+) connected (\d+x\d+\+\d+\+\d+)", output)
                    if match:
                        xwin_geometries = [(match.group(2), match.group(1))]
                else:
                    match = re.search(fr"{re.escape(target_monitor)} connected (?:primary )?(\d+x\d+\+\d+\+\d+)", output)
                    if match:
                        xwin_geometries = [(match.group(1), target_monitor)]

        except Exception as e:
            print(f"[Renderer] Error detecting xrandr geometry: {e}")

        if not xwin_geometries:
            xwin_geometries = [("-fs", "Default")]

        draw_mode = config.get("draw_mode", "Estándar")
        processes = []

        for geo, name in xwin_geometries:
            xwin_args = ["-g", geo] if geo != "-fs" else ["-fs"]
            xwin_cmd = ["xwinwrap"] + xwin_args + ["-ni", "-b", "-nf"]
            if draw_mode == "ARGB (Compositor)": xwin_cmd += ["-ov", "-argb"]
            elif draw_mode == "Forzado": xwin_cmd += ["-sh", "rectangle"]
            else: xwin_cmd += ["-ov"]
            xwin_cmd += ["--"]

            mpv_cmd = ["mpv"] + self._build_mpv_args(config, wid_needed=True)
            mpv_cmd.append(video_path)
            
            p = subprocess.Popen(xwin_cmd + mpv_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            processes.append(p)
        
        if processes:
            self.bg_proc = processes[0]
        
        import threading
        threading.Timer(0.5, lambda: subprocess.run(["xfdesktop", "--reload"], stderr=subprocess.DEVNULL)).start()
        
        return True

    def _build_mpv_args(self, config, wid_needed=True):
        args = []
        if wid_needed: args.append("--wid=%WID")
        
        volume = config.get('volume', 50)
        mute = 'yes' if config.get('mute', False) else 'no'
        loop_val = "inf" if config.get('loop', 'Loop') == 'Loop' else 'no'
        
        args.extend([
            f"--loop-file={loop_val}", f"--volume={volume}", f"--mute={mute}",
            f"--gpu-api={config.get('gpu_api', 'auto')}",
            f"--hwdec={config.get('hwdec', 'auto')}",
            "--vo=gpu",
            "--keep-open=yes",
            f"--input-ipc-server={self.socket_path}",
            "--ytdl=yes",
            "--tls-verify=no",
            "--cache=yes",
            "--demuxer-max-bytes=150M",
            "--demuxer-max-back-bytes=75M",
            "--no-osc", "--no-osd-bar", "--no-input-default-bindings", "--idle"
        ])

        fps = config.get('fps_limit', 60)
        if isinstance(fps, int) and fps > 0:
            args.append(f"--override-display-fps={fps}")

        scaling = config.get("fit", "Cover")
        if scaling == "Stretch": 
            args += ["--keepaspect=no"]
        elif scaling == "Cover": 
            args += ["--panscan=1.0", "--keepaspect=yes"]
        elif scaling == "Center":
            args += ["--panscan=0.0", "--keepaspect=yes"]
        elif scaling == "Contain":
            args += ["--panscan=0.0", "--keepaspect=yes"]
        else: 
            args += ["--keepaspect=yes"]

        res_map = {
            "1080p (Full HD)": "scale=-1:1080",
            "720p (HD)": "scale=-1:720",
            "480p (SD)": "scale=-1:480",
        }
        render_res = config.get("video_resolution", "Nativa")
        if render_res in res_map:
            args += [f"--vf={res_map[render_res]}"]

        return args

    def stop(self):
        if self.bg_proc:
            try:
                self.bg_proc.terminate()
                self.bg_proc.wait(timeout=0.5)
            except: 
                try: self.bg_proc.kill()
                except: pass
            self.bg_proc = None
            
        subprocess.run(["pkill", "-f", "mpvpaper"], stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-f", f"mpv.*{self.socket_path}"], stderr=subprocess.DEVNULL)
