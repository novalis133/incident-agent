"""Runtime log-line classifier.

Loads the trained model from ``artifacts/log_classifier.joblib`` and exposes a
simple ``classify(log_line)`` interface.

Usage::

    from models import LogClassifier

    classifier = LogClassifier()
    result = classifier.classify("ERROR OOMKilled container=api pod=xyz")
    # {"category": "resource_exhaustion", "confidence": 0.92}
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Final

import structlog

log = structlog.get_logger(__name__)

_MODULE_DIR: Final[Path] = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH: Final[Path] = _MODULE_DIR / "artifacts" / "log_classifier.joblib"


class LogClassifier:
    """Thin wrapper around the persisted classification pipeline."""

    def __init__(self, model_path: Path | str | None = None) -> None:
        self._model_path = Path(model_path or DEFAULT_MODEL_PATH).resolve()
        self._pipeline: Any = None
        self._backend: str = "unknown"
        self._load_model()

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        """Load the joblib artefact, handling both sklearn and pytorch formats."""
        try:
            import joblib
        except ImportError as exc:
            raise ImportError(
                "joblib is required to load the classifier model. "
                "Install it with: pip install joblib"
            ) from exc

        if not self._model_path.exists():
            raise FileNotFoundError(
                f"Trained model not found at {self._model_path}. "
                "Run `python -m models.train_classifier` first."
            )

        log.info("loading_model", path=str(self._model_path))
        artifact = joblib.load(self._model_path)

        if isinstance(artifact, dict) and artifact.get("type") == "pytorch":
            self._load_pytorch(artifact)
        else:
            # Plain sklearn Pipeline
            self._pipeline = artifact
            self._backend = "sklearn"

        log.info("model_loaded", backend=self._backend)

    def _load_pytorch(self, artifact: dict[str, Any]) -> None:
        """Reconstruct the PyTorch model from the saved state dict."""
        try:
            import numpy as np  # noqa: F401
            import torch
            import torch.nn as nn
        except ImportError as exc:
            raise ImportError(
                "PyTorch is required to load a GPU-trained model. "
                "Install it with: pip install torch"
            ) from exc

        cfg = artifact["model_config"]
        model = nn.Sequential(
            nn.Linear(cfg["n_features"], 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, cfg["n_classes"]),
        )
        model.load_state_dict(artifact["model_state"])
        model.eval()

        self._pipeline = {
            "model": model,
            "tfidf": artifact["tfidf"],
            "label_encoder": artifact["label_encoder"],
        }
        self._backend = "pytorch"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify(self, log_line: str) -> dict[str, str | float]:
        """Classify a single log line.

        Args:
            log_line: Raw log line string.

        Returns:
            Dictionary with ``category`` (str) and ``confidence`` (float 0-1).

        Raises:
            ValueError: If *log_line* is empty or not a string.
            RuntimeError: If the underlying model fails.
        """
        if not isinstance(log_line, str) or not log_line.strip():
            raise ValueError("log_line must be a non-empty string")

        try:
            if self._backend == "sklearn":
                return self._classify_sklearn(log_line)
            elif self._backend == "pytorch":
                return self._classify_pytorch(log_line)
            else:
                raise RuntimeError(f"Unknown backend: {self._backend}")
        except (ValueError, RuntimeError):
            raise
        except Exception as exc:
            log.error("classification_failed", error=str(exc), log_line=log_line[:200])
            raise RuntimeError(
                f"Classification failed: {exc}"
            ) from exc

    def _classify_sklearn(self, log_line: str) -> dict[str, str | float]:
        """Run inference through the sklearn Pipeline."""
        import numpy as np

        proba = self._pipeline.predict_proba([log_line])[0]
        idx = int(np.argmax(proba))
        category = self._pipeline.classes_[idx]
        confidence = float(proba[idx])
        return {"category": category, "confidence": round(confidence, 4)}

    def _classify_pytorch(self, log_line: str) -> dict[str, str | float]:
        """Run inference through the PyTorch model."""
        import numpy as np
        import torch

        tfidf = self._pipeline["tfidf"]
        model = self._pipeline["model"]
        le = self._pipeline["label_encoder"]

        features = tfidf.transform([log_line]).toarray().astype(np.float32)
        tensor = torch.tensor(features)

        with torch.no_grad():
            logits = model(tensor)
            probs = torch.softmax(logits, dim=1).squeeze()

        idx = int(probs.argmax())
        category = le.inverse_transform([idx])[0]
        confidence = float(probs[idx])
        return {"category": category, "confidence": round(confidence, 4)}

    @property
    def backend(self) -> str:
        """Return the active backend name (``sklearn`` or ``pytorch``)."""
        return self._backend

    def __repr__(self) -> str:
        return (
            f"LogClassifier(model_path={str(self._model_path)!r}, "
            f"backend={self._backend!r})"
        )
