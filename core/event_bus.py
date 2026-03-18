from PySide6.QtCore import QObject, Signal, Slot
import logging

class EventBus(QObject):
    """
    Central Event Bus for the application.
    Allows loose coupling between components using signals.
    """
    
    event_occurred = Signal(str, object)

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
        pass
