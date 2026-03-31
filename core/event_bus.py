from PySide6.QtCore import QObject, Signal, Slot
from typing import Any
import logging


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
        logging.debug(f"Event emitted: {event_name}")
        self.event_occurred.emit(event_name, data)

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
