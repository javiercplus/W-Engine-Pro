import subprocess
import logging
import time
import os
import signal
import threading
from core.logger import log_event, MpvErrorParser


class ProcessManager:
    """
    Centralized manager for child processes.
    Includes non-blocking stderr reading and event-driven error handling.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProcessManager, cls).__new__(cls)
            cls._instance.processes = {}  # {name: proc_obj}
            cls._instance.commands = {}  # {name: (cmd, env)}
            cls._instance.restart_counts = {}  # {name: count}
            cls._instance.on_error_cb = None  # Callback(name, error_type)
            cls._instance._stop_event = threading.Event()
            cls._instance._start_monitor()
        return cls._instance

    def _start_monitor(self):
        self._monitor_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self._monitor_thread.start()

    def _watchdog_loop(self):
        while not self._stop_event.is_set():
            for name in list(self.processes.keys()):
                proc = self.processes.get(name)
                if proc and proc.poll() is not None:
                    self._handle_process_failure(name)
            self._stop_event.wait(2.0)

    def set_error_callback(self, callback):
        """Sets a callback for critical errors found in stderr."""
        self.on_error_cb = callback

    def start(self, name, cmd, env=None):
        self.stop(name)
        self.commands[name] = (cmd, env)
        logging.debug(f"[ProcessManager] Starting {name}: {' '.join(cmd)}")

        # Aislamiento de entorno si se provee uno específico
        final_env = env if env is not None else os.environ.copy()

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                env=final_env,
                preexec_fn=os.setsid,
                text=True,
                bufsize=1,  # Line buffered
            )
            self.processes[name] = proc

            # Non-blocking stderr reader
            threading.Thread(
                target=self._read_stderr, args=(name, proc), daemon=True
            ).start()
            return proc
        except Exception as e:
            import traceback
            error_msg = f"Failed to start {name}: {e}\n{traceback.format_exc()}"
            log_event("ERROR", error_msg)
            return None

    def _read_stderr(self, name, proc):
        """Monitors stderr for critical patterns and logs everything on failure."""
        if not proc.stderr:
            return

        for line in proc.stderr:
            line = line.strip()
            if not line:
                continue

            # Print everything to console for debugging
            logging.debug(f"[{name} stderr] {line}")

            error_type = MpvErrorParser.classify(line)
            if error_type:
                log_event(
                    "ERROR",
                    f"Critical error detected in {name}",
                    type=error_type,
                    detail=line,
                )
                if self.on_error_cb:
                    self.on_error_cb(name, error_type)

            if self._stop_event.is_set() or proc.poll() is not None:
                break

    def _handle_process_failure(self, name):
        count = self.restart_counts.get(name, 0)
        if count >= 3:
            log_event("ERROR", f"Giving up on {name} after 3 attempts.")
            del self.processes[name]
            return

        self.restart_counts[name] = count + 1
        time.sleep(1.0 * (2**count))
        cmd, env = self.commands.get(name, (None, None))
        if cmd:
            self.start(name, cmd, env)

    def stop(self, name):
        if name in self.restart_counts:
            del self.restart_counts[name]
        if name in self.processes:
            proc = self.processes.pop(name)
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                proc.wait(timeout=1.0)
            except:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except:
                    pass

    def stop_all(self):
        for name in list(self.processes.keys()):
            self.stop(name)

    def cleanup(self):
        self._stop_event.set()
        self.stop_all()
