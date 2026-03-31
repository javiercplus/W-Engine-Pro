import logging
from typing import Any

from PySide6.QtCore import QObject, Signal, Slot


class EventBus(QObject):
    """
    Central Event Bus for the application.
    Allows loose coupling between components using signals.
    """

    event_occurred = Signal(str, Any)

    _instance = None

    def __init__(self):
        super().__init__()
        self.subscribers = {}

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def emit(self, event_name, data=None):
        """Emits an event to all subscribers."""
        logging.debug(f"[EventBus] Event emitted: {event_name} - {data}")

        # Safely attempt to introspect the number of receivers.
        # Some Signal/SignalInstance implementations (PySide6) don't expose a
        # `receivers` method directly or may behave differently; avoid calling
        # it unsafely to prevent AttributeError/TypeError at runtime.
        connections = "unknown"
        try:
            recv_fn = getattr(self.event_occurred, "receivers", None)
            if callable(recv_fn):
                try:
                    connections = recv_fn(self.event_occurred)
                except Exception:
                    connections = "unknown"
        except Exception:
            connections = "unknown"
        logging.debug(f"[EventBus] Signal connections: {connections} receivers")

        # Emit the Qt signal, guarding against unexpected exceptions so the
        # application can continue even if a subscriber misbehaves.
        try:
            self.event_occurred.emit(event_name, data)
        except Exception as e:
            logging.error(f"[EventBus] Error emitting event '{event_name}': {e}")

    def subscribe(self, event_name, callback):
        """
        Subscribes a callback to a specific event.
        Note: For QObjects, prefer connecting directly to signals if possible,
        but this allows dynamic event names.
        """
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(callback)
        self.event_occurred.connect(lambda name, data: self._dispatch(name, data))

    def _dispatch(self, event_name, data):
        """Dispatches event to all subscribed callbacks."""
        if event_name in self.subscribers:
            for callback in self.subscribers[event_name]:
                try:
                    callback(data)
                except Exception as e:
                    logging.error(f"Error in event callback for {event_name}: {e}")
