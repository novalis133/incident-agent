"""
Evaluation Runner

Reads eval_dataset.csv, runs each test case through the investigation pipeline,
and reports accuracy, confidence, latency, and root cause precision metrics.
"""

import asyncio
import csv
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import structlog

from incidentagent.main import investigate_alert
from incidentagent.schemas.alert import UnifiedAlert
from datetime import datetime

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class EvalCase:
    """Single evaluation test case loaded from CSV."""

    alert_title: str
    alert_description: str
    severity: str
    service: str
    expected_alert_type: str
    expected_root_cause_category: str
    expected_confidence_min: float


@dataclass
class EvalResult:
    """Result from running a single evaluation case."""

    case: EvalCase
    actual_alert_type: Optional[str] = None
    actual_root_cause_category: Optional[str] = None
    actual_confidence: float = 0.0
    latency_seconds: float = 0.0
    alert_type_match: bool = False
    root_cause_match: bool = False
    confidence_pass: bool = False
    error: Optional[str] = None


@dataclass
class EvalMetrics:
    """Aggregated evaluation metrics."""

    total_cases: int = 0
    alert_type_correct: int = 0
    root_cause_correct: int = 0
    confidence_pass_count: int = 0
    avg_confidence: float = 0.0
    latencies: List[float] = field(default_factory=list)

    @property
    def alert_type_accuracy(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.alert_type_correct / self.total_cases

    @property
    def root_cause_precision(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.root_cause_correct / self.total_cases

    @property
    def confidence_pass_rate(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.confidence_pass_count / self.total_cases

    @property
    def p95_latency(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_lats = sorted(self.latencies)
        idx = int(len(sorted_lats) * 0.95)
        return sorted_lats[min(idx, len(sorted_lats) - 1)]

    @property
    def avg_latency(self) -> float:
        if not self.latencies:
            return 0.0
        return statistics.mean(self.latencies)


def load_dataset(csv_path: Path) -> List[EvalCase]:
    """Load evaluation dataset from CSV file."""
    cases: List[EvalCase] = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            cases.append(
                EvalCase(
                    alert_title=row["alert_title"],
                    alert_description=row["alert_description"],
                    severity=row["severity"],
                    service=row["service"],
                    expected_alert_type=row["expected_alert_type"],
                    expected_root_cause_category=row["expected_root_cause_category"],
                    expected_confidence_min=float(row["expected_confidence_min"]),
                )
            )
    logger.info("dataset_loaded", count=len(cases), path=str(csv_path))
    return cases


async def run_single_case(case: EvalCase, case_index: int) -> EvalResult:
    """Run a single evaluation case through the investigation pipeline."""
    logger.info(
        "eval_case_started",
        index=case_index,
        title=case.alert_title,
        service=case.service,
    )

    alert = UnifiedAlert(
        id=f"eval-{case_index:03d}",
        source="manual",
        title=case.alert_title,
        description=case.alert_description,
        severity=case.severity,
        service=case.service,
        fired_at=datetime.utcnow(),
    )

    start = time.monotonic()
    try:
        result = await investigate_alert(alert)
        elapsed = time.monotonic() - start

        actual_alert_type = result.root_cause.category.value if result.root_cause else None
        # The triage alert_type is captured in the investigation pipeline;
        # we access it via the evidence or re-triage. For simplicity we check
        # the root cause category and also look for the triage data stored on
        # the result object.
        actual_alert_type_str: Optional[str] = None
        if hasattr(result, "evidence_summary"):
            # Attempt to pull triage alert_type from the investigation state
            pass

        # Fallback: use the investigation's agents_used to infer or read
        # from the full_evidence if triage metadata is present.
        # For a robust approach, re-run triage alone:
        from incidentagent.agents.triage import TriageAgent

        triage_agent = TriageAgent()
        triage_result = await triage_agent.triage(alert)
        actual_alert_type_str = triage_result.alert_type.value

        actual_rc_category = result.root_cause.category.value if result.root_cause else "unknown"
        actual_confidence = result.confidence_score

        alert_type_match = actual_alert_type_str == case.expected_alert_type
        root_cause_match = actual_rc_category == case.expected_root_cause_category
        confidence_pass = actual_confidence >= case.expected_confidence_min

        eval_result = EvalResult(
            case=case,
            actual_alert_type=actual_alert_type_str,
            actual_root_cause_category=actual_rc_category,
            actual_confidence=actual_confidence,
            latency_seconds=elapsed,
            alert_type_match=alert_type_match,
            root_cause_match=root_cause_match,
            confidence_pass=confidence_pass,
        )

        logger.info(
            "eval_case_completed",
            index=case_index,
            alert_type_match=alert_type_match,
            root_cause_match=root_cause_match,
            confidence=actual_confidence,
            latency=round(elapsed, 2),
        )

        return eval_result

    except Exception as exc:
        elapsed = time.monotonic() - start
        logger.error(
            "eval_case_failed",
            index=case_index,
            error=str(exc),
        )
        return EvalResult(
            case=case,
            latency_seconds=elapsed,
            error=str(exc),
        )


def compute_metrics(results: List[EvalResult]) -> EvalMetrics:
    """Compute aggregate metrics from individual evaluation results."""
    metrics = EvalMetrics(total_cases=len(results))

    confidences: List[float] = []
    for r in results:
        if r.error:
            continue
        if r.alert_type_match:
            metrics.alert_type_correct += 1
        if r.root_cause_match:
            metrics.root_cause_correct += 1
        if r.confidence_pass:
            metrics.confidence_pass_count += 1
        confidences.append(r.actual_confidence)
        metrics.latencies.append(r.latency_seconds)

    metrics.avg_confidence = statistics.mean(confidences) if confidences else 0.0
    return metrics


def format_results_table(results: List[EvalResult], metrics: EvalMetrics) -> str:
    """Format evaluation results as a readable table string."""
    sep = "-" * 120
    header = (
        f"{'#':<4} {'Title':<45} {'Expected Type':<14} {'Actual Type':<14} "
        f"{'RC Match':<10} {'Conf':<6} {'Latency':<8} {'Status':<8}"
    )

    lines: List[str] = [
        "",
        "=" * 120,
        "EVALUATION RESULTS",
        "=" * 120,
        header,
        sep,
    ]

    for idx, r in enumerate(results):
        status = "ERROR" if r.error else ("PASS" if (r.alert_type_match and r.root_cause_match and r.confidence_pass) else "FAIL")
        lines.append(
            f"{idx + 1:<4} {r.case.alert_title[:44]:<45} {r.case.expected_alert_type:<14} "
            f"{(r.actual_alert_type or 'N/A'):<14} "
            f"{'Y' if r.root_cause_match else 'N':<10} "
            f"{r.actual_confidence:<6.2f} "
            f"{r.latency_seconds:<8.2f} "
            f"{status:<8}"
        )

    lines.append(sep)
    lines.append("")
    lines.append("=" * 60)
    lines.append("AGGREGATE METRICS")
    lines.append("=" * 60)
    lines.append(f"  Total cases:            {metrics.total_cases}")
    lines.append(f"  Alert type accuracy:    {metrics.alert_type_accuracy:.2%}")
    lines.append(f"  Root cause precision:   {metrics.root_cause_precision:.2%}")
    lines.append(f"  Confidence pass rate:   {metrics.confidence_pass_rate:.2%}")
    lines.append(f"  Avg confidence:         {metrics.avg_confidence:.3f}")
    lines.append(f"  Avg latency:            {metrics.avg_latency:.2f}s")
    lines.append(f"  P95 latency:            {metrics.p95_latency:.2f}s")
    lines.append("=" * 60)
    lines.append("")

    return "\n".join(lines)


async def run_evaluation() -> None:
    """Run the full evaluation benchmark."""
    dataset_path = Path(__file__).parent / "eval_dataset.csv"
    cases = load_dataset(dataset_path)

    logger.info("evaluation_started", total_cases=len(cases))

    results: List[EvalResult] = []
    for idx, case in enumerate(cases):
        result = await run_single_case(case, idx)
        results.append(result)

    metrics = compute_metrics(results)
    table = format_results_table(results, metrics)

    logger.info(
        "evaluation_completed",
        alert_type_accuracy=round(metrics.alert_type_accuracy, 4),
        root_cause_precision=round(metrics.root_cause_precision, 4),
        avg_confidence=round(metrics.avg_confidence, 4),
        p95_latency=round(metrics.p95_latency, 2),
        confidence_pass_rate=round(metrics.confidence_pass_rate, 4),
    )

    # Output the results table to stderr for visibility
    import sys
    sys.stderr.write(table)
    sys.stderr.write("\n")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
