"""Generate synthetic log line training data for a log anomaly classifier.

Produces 800+ labeled log lines across six categories:
  normal, error_rate, resource_exhaustion, dependency_failure,
  config_error, deployment_issue

Usage:
    python -m models.generate_training_data
"""

from __future__ import annotations

import csv
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Final

import structlog

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_PATH: Final[Path] = Path(__file__).resolve().parent / "training_data.csv"

CATEGORIES: Final[list[str]] = [
    "normal",
    "error_rate",
    "resource_exhaustion",
    "dependency_failure",
    "config_error",
    "deployment_issue",
]

SERVICES: Final[list[str]] = [
    "api-gateway",
    "auth-service",
    "payment-service",
    "order-service",
    "inventory-service",
    "notification-service",
    "user-service",
    "search-service",
    "analytics-service",
    "billing-service",
    "cdn-proxy",
    "scheduler",
    "worker-pool",
    "cache-manager",
    "event-bus",
]

LOG_LEVELS: Final[list[str]] = ["DEBUG", "INFO", "WARN", "ERROR", "FATAL"]

HOSTS: Final[list[str]] = [
    "prod-node-01",
    "prod-node-02",
    "prod-node-03",
    "staging-node-01",
    "k8s-worker-1a",
    "k8s-worker-2b",
    "k8s-worker-3c",
]

NAMESPACES: Final[list[str]] = [
    "default",
    "production",
    "staging",
    "monitoring",
    "kube-system",
]

PODS: Final[list[str]] = [
    "api-gateway-7f8b6c-xk9mz",
    "auth-service-5d4e3f-qr7ws",
    "payment-service-9a8b7c-lm2np",
    "order-service-3c2d1e-jk5gh",
    "worker-pool-6e5f4g-vw8xy",
]

ENDPOINTS: Final[list[str]] = [
    "/api/v1/users",
    "/api/v1/orders",
    "/api/v1/payments",
    "/api/v2/search",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/inventory",
    "/api/v1/notifications",
    "/healthz",
    "/readyz",
    "/metrics",
]

HTTP_METHODS: Final[list[str]] = ["GET", "POST", "PUT", "DELETE", "PATCH"]

DB_NAMES: Final[list[str]] = [
    "postgres-primary",
    "postgres-replica-1",
    "mysql-orders",
    "mongodb-analytics",
    "redis-cache-01",
    "redis-cache-02",
    "elasticsearch-cluster",
]

EXTERNAL_DEPS: Final[list[str]] = [
    "stripe-api",
    "twilio-sms",
    "sendgrid-email",
    "aws-s3",
    "aws-sqs",
    "cloudflare-dns",
    "datadog-agent",
    "vault-server",
    "consul-cluster",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rand_ts() -> str:
    """Return a random ISO-8601 timestamp within the last 7 days."""
    base = datetime.now(tz=timezone.utc) - timedelta(days=random.randint(0, 7))
    offset = timedelta(
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
        milliseconds=random.randint(0, 999),
    )
    return (base - offset).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _rand_id() -> str:
    return uuid.uuid4().hex[:12]


def _rand_latency() -> int:
    return random.randint(1, 350)


def _rand_status_ok() -> int:
    return random.choice([200, 201, 204, 301, 304])


def _rand_status_err() -> int:
    return random.choice([400, 401, 403, 404, 429, 500, 502, 503, 504])


def _svc() -> str:
    return random.choice(SERVICES)


def _host() -> str:
    return random.choice(HOSTS)


def _ep() -> str:
    return random.choice(ENDPOINTS)


def _method() -> str:
    return random.choice(HTTP_METHODS)


def _db() -> str:
    return random.choice(DB_NAMES)


def _dep() -> str:
    return random.choice(EXTERNAL_DEPS)


def _ns() -> str:
    return random.choice(NAMESPACES)


def _pod() -> str:
    return random.choice(PODS)


# ---------------------------------------------------------------------------
# Template generators per category
# ---------------------------------------------------------------------------


def _normal_templates() -> list[str]:
    """Return a pool of normal log line templates."""
    templates: list[str] = []
    for _ in range(200):
        ts = _rand_ts()
        svc = _svc()
        rid = _rand_id()
        lat = _rand_latency()
        status = _rand_status_ok()
        ep = _ep()
        method = _method()
        host = _host()

        variants = [
            f"{ts} INFO  [{svc}] {method} {ep} completed status={status} latency={lat}ms request_id={rid}",
            f"{ts} INFO  [{svc}] Successfully processed request request_id={rid} duration={lat}ms",
            f"{ts} DEBUG [{svc}] Connection pool stats: active=5 idle=15 total=20 host={host}",
            f"{ts} INFO  [{svc}] Health check passed endpoint=/healthz status=ok uptime=34521s",
            f"{ts} INFO  [{svc}] Cache hit ratio=0.{random.randint(85, 99)} keys={random.randint(100, 5000)} host={host}",
            f"{ts} INFO  [{svc}] Scheduled job cron.cleanup completed in {lat}ms removed={random.randint(0, 50)} records",
            f"{ts} DEBUG [{svc}] TLS handshake completed peer={host}:443 protocol=TLSv1.3 cipher=TLS_AES_256_GCM_SHA384",
            f"{ts} INFO  [{svc}] Message consumed topic=orders partition={random.randint(0, 11)} offset={random.randint(1000, 999999)} lag=0",
            f"{ts} INFO  [{svc}] Deployment readiness probe succeeded pod={_pod()} namespace={_ns()}",
            f"{ts} INFO  [{svc}] Graceful shutdown initiated pid={random.randint(1, 65535)} signal=SIGTERM",
            f"{ts} INFO  [{svc}] Worker thread started thread_id={random.randint(1, 64)} pool_size=16",
            f"{ts} DEBUG [{svc}] DNS resolution host={host} resolved_in={random.randint(1, 15)}ms ttl={random.randint(30, 300)}s",
            f"{ts} INFO  [{svc}] Rate limiter token_bucket refilled bucket={svc} tokens=100 interval=60s",
            f"{ts} INFO  [{svc}] Metrics exported datapoints={random.randint(50, 500)} target=prometheus",
            f"{ts} INFO  [{svc}] Session created user_id={_rand_id()} ip=10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)} ttl=3600s",
        ]
        templates.append(random.choice(variants))
    return templates


def _error_rate_templates() -> list[str]:
    templates: list[str] = []
    for _ in range(150):
        ts = _rand_ts()
        svc = _svc()
        rid = _rand_id()
        status = _rand_status_err()
        ep = _ep()
        method = _method()

        variants = [
            f"{ts} ERROR [{svc}] {method} {ep} failed status={status} error=\"Internal Server Error\" request_id={rid}",
            f"{ts} ERROR [{svc}] Unhandled exception in request handler: NullPointerException at com.{svc}.handler.process(Handler.java:142) request_id={rid}",
            f"{ts} WARN  [{svc}] Error rate threshold exceeded: 15.3% errors in last 60s (threshold=5%) endpoint={ep}",
            f"{ts} ERROR [{svc}] Circuit breaker OPEN for {ep} failures=23/25 window=30s",
            f"{ts} ERROR [{svc}] Request timeout after 30000ms {method} {ep} request_id={rid}",
            f"{ts} FATAL [{svc}] Panic recovered: runtime error: index out of range [5] with length 3 goroutine={random.randint(1, 500)}",
            f"{ts} ERROR [{svc}] HTTP 503 Service Unavailable upstream={_dep()} retries=3/3 request_id={rid}",
            f"{ts} ERROR [{svc}] Response validation failed: expected 200, got {status} body=\"{{\\\"error\\\":\\\"service degraded\\\"}}\" request_id={rid}",
            f"{ts} WARN  [{svc}] Retry attempt 3/5 for {method} {ep} last_error=\"connection reset by peer\"",
            f"{ts} ERROR [{svc}] Traceback (most recent call last):\\n  File \"/app/{svc}/views.py\", line {random.randint(50, 300)}, in handle_request\\n    result = process(data)\\nValueError: invalid literal for int() with base 10: 'abc'",
            f"{ts} ERROR [{svc}] gRPC call failed code=UNAVAILABLE desc=\"transport is closing\" method=/{svc}.Service/Process",
            f"{ts} ERROR [{svc}] 500 errors spiking: count={random.randint(50, 500)} window=5m baseline={random.randint(1, 10)}",
        ]
        templates.append(random.choice(variants))
    return templates


def _resource_exhaustion_templates() -> list[str]:
    templates: list[str] = []
    for _ in range(150):
        ts = _rand_ts()
        svc = _svc()
        host = _host()
        pod = _pod()
        ns = _ns()

        variants = [
            f"{ts} ERROR [{svc}] OOMKilled container={svc} pod={pod} namespace={ns} memory_limit=512Mi usage=511Mi",
            f"{ts} WARN  [{svc}] Memory usage critical: 94.7% used (heap=1847MB/1952MB) GC overhead=38% host={host}",
            f"{ts} ERROR [{svc}] java.lang.OutOfMemoryError: Java heap space at java.util.Arrays.copyOf(Arrays.java:3236)",
            f"{ts} WARN  [{svc}] Disk space warning: /var/log usage=91% available=2.3GB threshold=85% host={host}",
            f"{ts} ERROR [{svc}] Connection pool exhausted: active={random.randint(95, 100)}/100 waiting={random.randint(10, 50)} timeout=5000ms db={_db()}",
            f"{ts} FATAL [{svc}] Cannot fork new process: errno=12 (Cannot allocate memory) host={host} pid={random.randint(1, 65535)}",
            f"{ts} WARN  [{svc}] CPU throttling detected: {random.randint(60, 95)}% throttled periods pod={pod} cpu_limit=500m",
            f"{ts} ERROR [{svc}] Too many open files: ulimit={random.randint(1024, 4096)} current={random.randint(1020, 4096)} host={host}",
            f"{ts} WARN  [{svc}] Thread pool saturated: active={random.randint(95, 200)}/200 queue={random.randint(100, 1000)} rejected={random.randint(1, 50)}",
            f"{ts} ERROR [{svc}] ENOMEM: mmap failed size={random.randint(100, 4096)}MB host={host} available_memory={random.randint(10, 100)}MB",
            f"{ts} WARN  [{svc}] Swap usage high: {random.randint(70, 95)}% used ({random.randint(3, 7)}GB/{random.randint(4, 8)}GB) host={host}",
            f"{ts} ERROR [{svc}] Evicted pod={pod} namespace={ns} reason=The node was low on resource: memory",
            f"{ts} WARN  [{svc}] File descriptor leak detected: open_fds={random.randint(900, 4000)} baseline={random.randint(100, 300)} host={host}",
            f"{ts} ERROR [{svc}] inode exhaustion: used=99.8% filesystem=/dev/sda1 host={host}",
        ]
        templates.append(random.choice(variants))
    return templates


def _dependency_failure_templates() -> list[str]:
    templates: list[str] = []
    for _ in range(150):
        ts = _rand_ts()
        svc = _svc()
        dep = _dep()
        db = _db()
        rid = _rand_id()

        variants = [
            f"{ts} ERROR [{svc}] Connection refused to {db} host=10.0.{random.randint(1, 50)}.{random.randint(1, 254)}:5432 errno=ECONNREFUSED",
            f"{ts} ERROR [{svc}] DNS resolution failed for {dep}.internal: NXDOMAIN query_time={random.randint(1000, 5000)}ms",
            f"{ts} ERROR [{svc}] Redis READONLY: You can't write against a read only replica host={db} command=SET",
            f"{ts} WARN  [{svc}] Upstream {dep} responding slowly: p99={random.randint(2000, 15000)}ms p50={random.randint(500, 2000)}ms threshold=1000ms",
            f"{ts} ERROR [{svc}] Database connection lost: {db} error=\"server closed the connection unexpectedly\" retry_in=5s",
            f"{ts} ERROR [{svc}] Kafka broker unreachable: broker_id={random.randint(0, 5)} host=kafka-{random.randint(0, 5)}.internal:9092 errno=ETIMEDOUT",
            f"{ts} ERROR [{svc}] S3 GetObject failed: bucket=prod-assets key=config/{svc}.yaml error=NoSuchBucket request_id={rid}",
            f"{ts} WARN  [{svc}] Circuit breaker half-open for {dep} testing with 1 request after 30s cooldown",
            f"{ts} ERROR [{svc}] TLS handshake failed: {dep}:443 error=\"certificate has expired\" not_after=2025-12-01T00:00:00Z",
            f"{ts} ERROR [{svc}] gRPC connection to {dep} failed: code=UNAVAILABLE desc=\"dns resolution failed for {dep}.svc.cluster.local\"",
            f"{ts} ERROR [{svc}] MongoDB replica set election in progress: {db} error=\"not primary\" retrying in {random.randint(1, 10)}s",
            f"{ts} WARN  [{svc}] Consul health check failing for {dep}: status=critical output=\"TCP connection timeout\"",
            f"{ts} ERROR [{svc}] Vault sealed: unable to retrieve secret secret/{svc}/db-creds error=\"Vault is sealed\"",
        ]
        templates.append(random.choice(variants))
    return templates


def _config_error_templates() -> list[str]:
    templates: list[str] = []
    for _ in range(100):
        ts = _rand_ts()
        svc = _svc()
        host = _host()

        variants = [
            f"{ts} ERROR [{svc}] Configuration validation failed: required key 'database.url' not found in /etc/{svc}/config.yaml",
            f"{ts} FATAL [{svc}] Environment variable DATABASE_URL is not set, cannot start service",
            f"{ts} ERROR [{svc}] Invalid configuration: max_connections must be > 0, got -1 source=/etc/{svc}/config.yaml",
            f"{ts} ERROR [{svc}] Feature flag parsing error: invalid JSON in flag 'enable_new_checkout' value='tru' expected boolean",
            f"{ts} WARN  [{svc}] Deprecated config key 'ssl_verify' used, migrate to 'tls.verify_certificates' before v3.0",
            f"{ts} ERROR [{svc}] ConfigMap {svc}-config not found in namespace production, using defaults",
            f"{ts} ERROR [{svc}] Secret mount failed: /var/run/secrets/{svc}/api-key: no such file or directory",
            f"{ts} FATAL [{svc}] Port conflict: bind 0.0.0.0:8080 failed: address already in use host={host}",
            f"{ts} ERROR [{svc}] YAML parse error in /etc/{svc}/config.yaml: line 47: mapping values are not allowed here",
            f"{ts} ERROR [{svc}] Invalid log level 'TRACE' in config, falling back to INFO",
            f"{ts} WARN  [{svc}] TLS certificate path /etc/ssl/{svc}/tls.crt does not exist, disabling TLS",
            f"{ts} ERROR [{svc}] Schema migration version mismatch: expected=42 got=39 database={_db()}",
            f"{ts} ERROR [{svc}] Helm values override conflict: both 'replicas' and 'autoscaling.enabled' are set",
        ]
        templates.append(random.choice(variants))
    return templates


def _deployment_issue_templates() -> list[str]:
    templates: list[str] = []
    for _ in range(100):
        ts = _rand_ts()
        svc = _svc()
        pod = _pod()
        ns = _ns()
        host = _host()
        image_tag = f"v{random.randint(1, 5)}.{random.randint(0, 30)}.{random.randint(0, 99)}"

        variants = [
            f"{ts} ERROR [{svc}] CrashLoopBackOff pod={pod} namespace={ns} restart_count={random.randint(5, 50)} back_off=5m",
            f"{ts} ERROR [{svc}] ImagePullBackOff: failed to pull image registry.internal/{svc}:{image_tag} error=\"manifest unknown\"",
            f"{ts} WARN  [{svc}] Rollout stalled: deployment/{svc} 2/5 replicas available deadline=600s namespace={ns}",
            f"{ts} ERROR [{svc}] Liveness probe failed: HTTP probe failed with statuscode 503 pod={pod} consecutive_failures=3",
            f"{ts} ERROR [{svc}] Init container failed: exit code 1 container=db-migration pod={pod} reason=\"migration failed\"",
            f"{ts} WARN  [{svc}] Canary deployment {svc}-canary error rate 12.5% exceeds threshold 5%, initiating rollback",
            f"{ts} ERROR [{svc}] Node scheduling failed: 0/{random.randint(3, 10)} nodes available: insufficient cpu pod={pod}",
            f"{ts} ERROR [{svc}] PersistentVolumeClaim {svc}-data pending: no persistent volumes available for this claim namespace={ns}",
            f"{ts} WARN  [{svc}] Rolling update paused: maxUnavailable reached deployment/{svc} unavailable={random.randint(2, 5)}",
            f"{ts} ERROR [{svc}] Container runtime error: runc create failed: unable to start container process: exec: \"/app/start.sh\": permission denied",
            f"{ts} ERROR [{svc}] HPA unable to scale: unable to get metrics for resource cpu: no metrics returned from resource metrics API",
            f"{ts} WARN  [{svc}] Blue-green switch aborted: new version health check failed endpoint=/readyz host={host}",
            f"{ts} ERROR [{svc}] Helm release failed: upgrade \"{svc}\" failed: timed out waiting for the condition namespace={ns}",
            f"{ts} ERROR [{svc}] ArgoCD sync failed: application {svc} sync status=OutOfSync health=Degraded",
        ]
        templates.append(random.choice(variants))
    return templates


# ---------------------------------------------------------------------------
# Main generation logic
# ---------------------------------------------------------------------------


def generate_training_data(output_path: Path | None = None) -> Path:
    """Generate synthetic training data and write to CSV.

    Args:
        output_path: Where to write the CSV. Defaults to ``training_data.csv``
            next to this module.

    Returns:
        The resolved path of the written CSV file.
    """
    dest = (output_path or OUTPUT_PATH).resolve()
    log.info("generating_training_data", output_path=str(dest))

    generators: dict[str, list[str]] = {
        "normal": _normal_templates(),
        "error_rate": _error_rate_templates(),
        "resource_exhaustion": _resource_exhaustion_templates(),
        "dependency_failure": _dependency_failure_templates(),
        "config_error": _config_error_templates(),
        "deployment_issue": _deployment_issue_templates(),
    }

    rows: list[dict[str, str]] = []
    for category, lines in generators.items():
        for line in lines:
            rows.append({"log_line": line, "category": category})

    random.shuffle(rows)

    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["log_line", "category"])
        writer.writeheader()
        writer.writerows(rows)

    log.info(
        "training_data_generated",
        total_rows=len(rows),
        categories={cat: len(lines) for cat, lines in generators.items()},
        output_path=str(dest),
    )
    return dest


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
    )
    path = generate_training_data()
    log.info("done", path=str(path))
