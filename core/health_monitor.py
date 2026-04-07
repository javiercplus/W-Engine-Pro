import json
import logging
import os
import socket
import threading
import time

from core.logger import log_event


class HealthMonitor:
    """
    Periodically pings mpv IPC sockets to ensure backends are responsive.
    """

    def __init__(self, renderer_manager):
        self.renderer = renderer_manager
        self._stop_event = threading.Event()
        self._thread = None
        self.fail_count = 0
        self.MAX_FAILS = 3
        self.is_paused = False
        self._grace_period_until = 0  # Timestamp until check is allowed
        self._restart_count = 0  # Track restarts to prevent infinite loops
        self._max_restarts = 5  # Max consecutive restarts before giving up
        self._restart_cooldown = 0  # Timestamp when cooldown ends

    def start(self):
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def set_paused(self, paused: bool):
        self.is_paused = paused
        if paused:
            self.fail_count = 0
            logging.debug("[HealthMonitor] Monitoring suspended (paused).")
        else:
            # Give a small grace period when resuming
            self._grace_period_until = time.time() + 2.0
            logging.debug("[HealthMonitor] Monitoring resumed.")

    def trigger_grace_period(self, seconds=10.0):
        """Sets a grace period during which no health checks are performed."""
        self._grace_period_until = time.time() + seconds
        self.fail_count = 0
        logging.info(f"[HealthMonitor] Grace period active for {seconds}s")

    def stop(self):
        self._stop_event.set()

    def _run(self):
        while not self._stop_event.is_set():
            now = time.time()
            if self.is_paused or now < self._grace_period_until:
                self._stop_event.wait(5.0)
                continue

            active_sockets = self.renderer.get_active_sockets()
            if not active_sockets:
                self.fail_count = 0
                self._stop_event.wait(5.0)
                continue

            all_ok = True
            for socket_path in active_sockets:
                logging.debug(f"[HealthMonitor] Checking IPC socket: {socket_path}")
                if os.path.exists(socket_path):
                    result = self._check_ipc(socket_path)
                    logging.debug(f"[HealthMonitor] IPC check result: {result}")
                    if not result:
                        all_ok = False
                        break
                else:
                    logging.debug(f"[HealthMonitor] Socket file missing: {socket_path}")
                    all_ok = False
                    break

            if not all_ok:
                self.fail_count += 1
                log_event(
                    "WARN",
                    "IPC Health-check failed",
                    attempt=self.fail_count,
                    max=self.MAX_FAILS,
                )

                if self.fail_count >= self.MAX_FAILS:
                    log_event("ERROR", "IPC Dead. Triggering soft restart.")
                    self.renderer.profile.metrics.ipc_failures += 1

                    # Prevent infinite restart loops
                    now = time.time()
                    if now < self._restart_cooldown:
                        remaining = int(self._restart_cooldown - now)
                        log_event(
                            "WARN",
                            f"Restart cooldown active. Skipping restart ({remaining}s remaining).",
                        )
                        self.fail_count = 0
                        self._stop_event.wait(5.0)
                        continue

                    if self._restart_count >= self._max_restarts:
                        log_event(
                            "ERROR",
                            f"Max restart limit reached ({self._max_restarts}). Stopping auto-restart to prevent infinite loop.",
                        )
                        self.fail_count = 0
                        self._restart_count = 0
                        self._restart_cooldown = now + 30  # 30 second cooldown
                        self._stop_event.wait(5.0)
                        continue

                    # Force a restart of the current wallpaper
                    if self.renderer.last_config and self.renderer.last_video:
                        self._restart_count += 1
                        log_event(
                            "INFO",
                            f"Restart attempt {self._restart_count}/{self._max_restarts}",
                        )
                        self.renderer.restart(
                            self.renderer.last_config, self.renderer.last_video
                        )
                    self.fail_count = 0
            else:
                if self.fail_count > 0:
                    log_event("INFO", "IPC recovered.")
                self.fail_count = 0
                self._restart_count = 0  # Reset restart counter on recovery

            self._stop_event.wait(5.0)

    def _check_ipc(self, socket_path, retries=3):
        """Pings a specific mpv IPC socket with retries."""
        for attempt in range(retries):
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                    client.settimeout(1.0)
                    client.connect(socket_path)
                    msg = {"command": ["get_property", "pause"]}
                    client.sendall((json.dumps(msg) + "\n").encode())
                    response = client.recv(4096)
                    if response:
                        try:
                            data = json.loads(response.decode())
                            logging.debug(f"[HealthMonitor] IPC response: {data}")
                            return data.get("error") == "success"
                        except json.JSONDecodeError:
                            logging.debug(
                                f"[HealthMonitor] IPC non-JSON response: {response[:100]}"
                            )
                            return True
                    return False
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(0.1)
                    continue
                logging.debug(f"[HealthMonitor] IPC check failed: {e}")
                return False
        return False
