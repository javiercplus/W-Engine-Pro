import logging
import json
import sys
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """Formats logs with context as JSON or structured strings."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }
        # Add extra context if available
        if hasattr(record, "extra_context"):
            log_data.update(record.extra_context)

        return json.dumps(log_data)


def setup_logger(name="W-Engine"):
    """Configures and returns a structured logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(StructuredFormatter())
        logger.addHandler(ch)

    return logger


def log_event(level, message, **context):
    """Helper for structured event logging."""
    logger = logging.getLogger("W-Engine")
    extra = {"extra_context": context}

    if level == "INFO":
        logger.info(message, extra=extra)
    elif level == "WARN":
        logger.warning(message, extra=extra)
    elif level == "ERROR":
        logger.error(message, extra=extra)
    elif level == "DEBUG":
        logger.debug(message, extra=extra)


class MpvErrorParser:
    """Classifies mpv stderr lines into actionable error types."""

    ERROR_PATTERNS = {
        "gpu_fail": [
            "vo/gpu",
            "failed to initialize",
            "failed to create",
            "vulkan",
            "opengl",
        ],
        "file_error": ["No such file", "cannot open file", "Failed to open"],
        "codec_error": ["Failed to initialize decoder", "codec"],
        "ipc_fail": ["ipc", "connection refused", "socket error"],
        "wayland_fail": ["wayland", "failed", "protocol error"],
        "x11_fail": ["x11", "display error", "X11 error"],
    }

    @classmethod
    def classify(cls, line):
        line_lower = line.lower()
        for key, patterns in cls.ERROR_PATTERNS.items():
            if any(p.lower() in line_lower for p in patterns):
                return key
        return None
