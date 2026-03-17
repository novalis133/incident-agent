"""Log classification models for incident detection."""

try:
    from models.log_classifier import LogClassifier
except ImportError:
    try:
        from .log_classifier import LogClassifier
    except ImportError:
        LogClassifier = None

__all__ = ["LogClassifier"]
