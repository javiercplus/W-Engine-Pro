from PySide6.QtCore import QThread, Signal
import logging


class WorkerThread(QThread):
    """
    A generic safe QThread wrapper.
    Ensures threads are stopped correctly.
    """

    finished_task = Signal()
    error_occurred = Signal(str)

    def __init__(self, target=None, *args, **kwargs):
        super().__init__()
        self._target = target
        self._args = args
        self._kwargs = kwargs
        self._is_running = True

    def run(self):
        try:
            if self._target:
                self._target(*self._args, **self._kwargs)
            self.finished_task.emit()
        except Exception as e:
            logging.error(f"Thread error: {e}")
            self.error_occurred.emit(str(e))

    def stop(self):
        """Safely stops the thread."""
        self._is_running = False
        self.quit()
        self.wait()
