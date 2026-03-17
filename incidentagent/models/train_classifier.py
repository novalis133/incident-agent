"""Train a log-line anomaly classifier.

Loads ``training_data.csv``, fits a TF-IDF + LogisticRegression pipeline
(scikit-learn), prints a classification report, and persists the model to
``artifacts/log_classifier.joblib``.

Optionally leverages a PyTorch GPU model when ``--use-gpu`` is passed *and*
CUDA is available; otherwise falls back to scikit-learn.

Usage:
    python -m models.train_classifier            # scikit-learn (default)
    python -m models.train_classifier --use-gpu  # attempt GPU training
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Final

import structlog

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_MODULE_DIR: Final[Path] = Path(__file__).resolve().parent
DATA_PATH: Final[Path] = _MODULE_DIR / "training_data.csv"
ARTIFACT_DIR: Final[Path] = _MODULE_DIR / "artifacts"
MODEL_PATH: Final[Path] = ARTIFACT_DIR / "log_classifier.joblib"


# ---------------------------------------------------------------------------
# scikit-learn training
# ---------------------------------------------------------------------------


def _train_sklearn(data_path: Path, model_path: Path) -> None:
    """Train with TF-IDF + LogisticRegression and save with joblib."""
    import joblib
    import pandas as pd
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline

    log.info("loading_data", path=str(data_path))
    df = pd.read_csv(data_path)
    log.info("data_loaded", rows=len(df), categories=df["category"].nunique())

    x_train, x_test, y_train, y_test = train_test_split(
        df["log_line"],
        df["category"],
        test_size=0.2,
        random_state=42,
        stratify=df["category"],
    )

    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    max_features=10_000,
                    ngram_range=(1, 2),
                    sublinear_tf=True,
                    strip_accents="unicode",
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=1000,
                    C=1.0,
                    solver="lbfgs",
                    n_jobs=-1,
                ),
            ),
        ]
    )

    log.info("training_sklearn_pipeline")
    pipeline.fit(x_train, y_train)

    y_pred = pipeline.predict(x_test)
    report = classification_report(y_test, y_pred)
    log.info("classification_report", report="\n" + report)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    log.info("model_saved", path=str(model_path))


# ---------------------------------------------------------------------------
# Optional GPU (PyTorch) training
# ---------------------------------------------------------------------------


def _gpu_available() -> bool:
    """Check whether CUDA is usable."""
    try:
        import torch  # noqa: F401

        return torch.cuda.is_available()
    except ImportError:
        return False


def _train_gpu(data_path: Path, model_path: Path) -> None:
    """Train a simple PyTorch text classifier on GPU, then wrap it for
    inference and save alongside a fitted TF-IDF vectorizer.

    Falls back to scikit-learn if CUDA is not available.
    """
    if not _gpu_available():
        log.warn("cuda_not_available_falling_back_to_sklearn")
        _train_sklearn(data_path, model_path)
        return

    import joblib
    import numpy as np
    import pandas as pd
    import torch
    import torch.nn as nn
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics import classification_report
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder

    log.info("loading_data", path=str(data_path))
    df = pd.read_csv(data_path)

    le = LabelEncoder()
    labels = le.fit_transform(df["category"])

    tfidf = TfidfVectorizer(
        max_features=10_000,
        ngram_range=(1, 2),
        sublinear_tf=True,
        strip_accents="unicode",
    )
    features = tfidf.fit_transform(df["log_line"]).toarray().astype(np.float32)

    x_train, x_test, y_train, y_test = train_test_split(
        features, labels, test_size=0.2, random_state=42, stratify=labels
    )

    device = torch.device("cuda")
    x_train_t = torch.tensor(x_train, device=device)
    y_train_t = torch.tensor(y_train, dtype=torch.long, device=device)
    x_test_t = torch.tensor(x_test, device=device)

    n_classes = len(le.classes_)
    n_features = x_train.shape[1]

    model = nn.Sequential(
        nn.Linear(n_features, 256),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(256, 64),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(64, n_classes),
    ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()

    log.info("training_gpu_model", device=str(device), epochs=50)
    model.train()
    for epoch in range(50):
        optimizer.zero_grad()
        logits = model(x_train_t)
        loss = criterion(logits, y_train_t)
        loss.backward()
        optimizer.step()
        if (epoch + 1) % 10 == 0:
            log.info("epoch", epoch=epoch + 1, loss=f"{loss.item():.4f}")

    model.eval()
    with torch.no_grad():
        preds = model(x_test_t).argmax(dim=1).cpu().numpy()

    report = classification_report(y_test, preds, target_names=le.classes_)
    log.info("classification_report", report="\n" + report)

    # Save artefacts bundled together so the classifier loader can pick them up.
    model_cpu = model.cpu()
    artifact = {
        "type": "pytorch",
        "model_state": model_cpu.state_dict(),
        "model_config": {
            "n_features": n_features,
            "n_classes": n_classes,
        },
        "tfidf": tfidf,
        "label_encoder": le,
    }
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, model_path)
    log.info("model_saved", path=str(model_path), backend="pytorch")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train log-line classifier")
    parser.add_argument(
        "--use-gpu",
        action="store_true",
        default=False,
        help="Attempt GPU training via PyTorch (falls back to sklearn)",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=DATA_PATH,
        help="Path to training CSV",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=MODEL_PATH,
        help="Where to save the trained model",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry-point for training."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
    )

    args = _parse_args(argv)

    if not args.data.exists():
        log.error("training_data_not_found", path=str(args.data))
        sys.exit(1)

    if args.use_gpu:
        _train_gpu(args.data, args.output)
    else:
        _train_sklearn(args.data, args.output)


if __name__ == "__main__":
    main()
