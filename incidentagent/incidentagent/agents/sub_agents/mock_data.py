"""
Mock Data Provider

Provides realistic demo data for all sub-agents when real
API connections (K8s, Elasticsearch, Prometheus) are unavailable.

The mock data tells a coherent incident story:
  - payment-service v2.3.1 deployed at 01:15
  - Connection leak introduced in PaymentProcessor.java
  - Connection pool gradually exhausted by 03:10
  - Error rate spikes at 03:12
  - Alert fires at 03:15
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


# ─── Timeline Constants ──────────────────────────────────────────────────────

INCIDENT_TIME = datetime(2026, 2, 22, 3, 15, 0, tzinfo=timezone.utc)
DEPLOY_TIME = datetime(2026, 2, 22, 1, 15, 0, tzinfo=timezone.utc)
POOL_EXHAUST_TIME = datetime(2026, 2, 22, 3, 10, 0, tzinfo=timezone.utc)
ERROR_SPIKE_TIME = datetime(2026, 2, 22, 3, 12, 0, tzinfo=timezone.utc)

AFFECTED_SERVICE = "payment-service"
AFFECTED_NAMESPACE = "payments"


# ─── Deployment Data ─────────────────────────────────────────────────────────

def get_k8s_deployments(
    service: Optional[str] = None,
    namespace: Optional[str] = None,
    since: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Mock Kubernetes deployment history."""
    deployments = [
        {
            "name": "payment-service",
            "namespace": "payments",
            "image": "registry.do/payment-service:v2.3.1",
            "previous_image": "registry.do/payment-service:v2.3.0",
            "replicas": 3,
            "ready_replicas": 3,
            "updated_at": DEPLOY_TIME.isoformat(),
            "status": "Complete",
            "change_cause": "image update to v2.3.1",
            "initiated_by": "ci/github-actions",
            "revision": 47,
            "rollout_duration_seconds": 120,
        },
        {
            "name": "checkout-service",
            "namespace": "payments",
            "image": "registry.do/checkout-service:v1.8.0",
            "previous_image": "registry.do/checkout-service:v1.7.9",
            "replicas": 2,
            "ready_replicas": 2,
            "updated_at": (DEPLOY_TIME - timedelta(days=2)).isoformat(),
            "status": "Complete",
            "change_cause": "image update to v1.8.0",
            "initiated_by": "ci/github-actions",
            "revision": 31,
            "rollout_duration_seconds": 90,
        },
        {
            "name": "user-service",
            "namespace": "users",
            "image": "registry.do/user-service:v3.1.2",
            "previous_image": "registry.do/user-service:v3.1.1",
            "replicas": 2,
            "ready_replicas": 2,
            "updated_at": (DEPLOY_TIME - timedelta(days=5)).isoformat(),
            "status": "Complete",
            "change_cause": "patch: logging fix",
            "initiated_by": "ci/github-actions",
            "revision": 88,
            "rollout_duration_seconds": 60,
        },
    ]

    results = deployments
    if service:
        results = [d for d in results if d["name"] == service]
    if namespace:
        results = [d for d in results if d["namespace"] == namespace]
    if since:
        results = [d for d in results if d["updated_at"] >= since.isoformat()]
    return results


def get_git_commits(
    service: Optional[str] = None,
    hours_back: int = 6,
) -> List[Dict[str, Any]]:
    """Mock Git commit history."""
    return [
        {
            "sha": "a1b2c3d",
            "message": "feat: add retry logic to PaymentProcessor",
            "author": "jane.doe@company.com",
            "timestamp": (DEPLOY_TIME - timedelta(minutes=30)).isoformat(),
            "files_changed": [
                "src/main/java/com/payment/PaymentProcessor.java",
                "src/main/java/com/payment/ConnectionManager.java",
            ],
            "additions": 45,
            "deletions": 12,
            "repo": "payment-service",
        },
        {
            "sha": "e4f5g6h",
            "message": "fix: update connection timeout to 30s",
            "author": "jane.doe@company.com",
            "timestamp": (DEPLOY_TIME - timedelta(minutes=25)).isoformat(),
            "files_changed": [
                "src/main/java/com/payment/ConnectionManager.java",
                "src/main/resources/application.yml",
            ],
            "additions": 8,
            "deletions": 3,
            "repo": "payment-service",
        },
        {
            "sha": "i7j8k9l",
            "message": "chore: bump dependencies",
            "author": "bot@company.com",
            "timestamp": (DEPLOY_TIME - timedelta(minutes=20)).isoformat(),
            "files_changed": ["pom.xml"],
            "additions": 5,
            "deletions": 5,
            "repo": "payment-service",
        },
    ]


def get_configmap_changes(
    service: Optional[str] = None,
    namespace: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Mock ConfigMap change history."""
    return [
        {
            "name": "payment-service-config",
            "namespace": "payments",
            "changed_at": (DEPLOY_TIME - timedelta(minutes=5)).isoformat(),
            "changed_keys": ["POOL_SIZE", "POOL_TIMEOUT_MS"],
            "previous_values": {"POOL_SIZE": "20", "POOL_TIMEOUT_MS": "5000"},
            "new_values": {"POOL_SIZE": "20", "POOL_TIMEOUT_MS": "30000"},
            "changed_by": "jane.doe@company.com",
        },
    ]


# ─── Log Data ────────────────────────────────────────────────────────────────

def get_error_logs(
    service: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    level: str = "error",
) -> List[Dict[str, Any]]:
    """Mock Elasticsearch error log entries."""
    base_time = ERROR_SPIKE_TIME
    return [
        {
            "@timestamp": base_time.isoformat(),
            "level": "ERROR",
            "service": "payment-service",
            "pod": "payment-service-7d4b8c6f9-x2k4m",
            "message": "java.lang.NullPointerException: Cannot invoke method on null connection",
            "logger": "com.payment.PaymentProcessor",
            "stack_trace": (
                "java.lang.NullPointerException: Cannot invoke method on null connection\n"
                "  at com.payment.PaymentProcessor.processPayment(PaymentProcessor.java:142)\n"
                "  at com.payment.PaymentController.handlePayment(PaymentController.java:58)\n"
                "  at org.springframework.web.servlet.FrameworkServlet.service(FrameworkServlet.java:97)"
            ),
            "trace_id": "abc123def456",
            "span_id": "span-001",
        },
        {
            "@timestamp": (base_time + timedelta(seconds=5)).isoformat(),
            "level": "ERROR",
            "service": "payment-service",
            "pod": "payment-service-7d4b8c6f9-r8n3p",
            "message": "HikariPool-1 - Connection is not available, request timed out after 30000ms",
            "logger": "com.zaxxer.hikari.pool.HikariPool",
            "stack_trace": (
                "java.sql.SQLTransientConnectionException: HikariPool-1 - Connection is not available\n"
                "  at com.zaxxer.hikari.pool.HikariPool.createTimeoutException(HikariPool.java:695)\n"
                "  at com.zaxxer.hikari.pool.HikariPool.getConnection(HikariPool.java:197)"
            ),
            "trace_id": "ghi789jkl012",
            "span_id": "span-002",
        },
        {
            "@timestamp": (base_time + timedelta(seconds=12)).isoformat(),
            "level": "ERROR",
            "service": "payment-service",
            "pod": "payment-service-7d4b8c6f9-x2k4m",
            "message": "Failed to process payment: connection pool exhausted",
            "logger": "com.payment.PaymentProcessor",
            "stack_trace": (
                "com.payment.exceptions.PaymentProcessingException: connection pool exhausted\n"
                "  at com.payment.PaymentProcessor.getConnection(PaymentProcessor.java:89)\n"
                "  at com.payment.PaymentProcessor.processPayment(PaymentProcessor.java:138)"
            ),
            "trace_id": "mno345pqr678",
            "span_id": "span-003",
        },
        {
            "@timestamp": (base_time + timedelta(seconds=18)).isoformat(),
            "level": "WARN",
            "service": "checkout-service",
            "pod": "checkout-service-5c7d9e1f2-q4w6e",
            "message": "Downstream payment-service returning 503 errors",
            "logger": "com.checkout.PaymentClient",
            "stack_trace": "",
            "trace_id": "stu901vwx234",
            "span_id": "span-004",
        },
        {
            "@timestamp": (base_time + timedelta(seconds=25)).isoformat(),
            "level": "ERROR",
            "service": "payment-service",
            "pod": "payment-service-7d4b8c6f9-m5n7o",
            "message": "java.lang.NullPointerException: Cannot invoke method on null connection",
            "logger": "com.payment.PaymentProcessor",
            "stack_trace": (
                "java.lang.NullPointerException: Cannot invoke method on null connection\n"
                "  at com.payment.PaymentProcessor.processPayment(PaymentProcessor.java:142)"
            ),
            "trace_id": "yza567bcd890",
            "span_id": "span-005",
        },
    ]


def get_log_error_count(
    service: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Mock Elasticsearch aggregation for error counts over time."""
    base = POOL_EXHAUST_TIME - timedelta(hours=2)
    buckets = []
    for i in range(25):
        ts = base + timedelta(minutes=i * 5)
        if ts < POOL_EXHAUST_TIME:
            count = 2 if i % 3 == 0 else 0
        elif ts < ERROR_SPIKE_TIME:
            count = 15
        else:
            count = 85 + (i * 3)
        buckets.append({"timestamp": ts.isoformat(), "count": count})
    return {"service": service, "buckets": buckets, "total_errors": sum(b["count"] for b in buckets)}


# ─── Metrics Data ────────────────────────────────────────────────────────────

def get_prometheus_metrics(
    query: str,
    service: Optional[str] = None,
) -> Dict[str, Any]:
    """Mock Prometheus query results."""
    metric_responses = {
        "cpu": {
            "metric": "container_cpu_usage_seconds_total",
            "service": service or AFFECTED_SERVICE,
            "values": [
                {"timestamp": (INCIDENT_TIME - timedelta(hours=2)).isoformat(), "value": 0.35},
                {"timestamp": (INCIDENT_TIME - timedelta(hours=1)).isoformat(), "value": 0.42},
                {"timestamp": (INCIDENT_TIME - timedelta(minutes=30)).isoformat(), "value": 0.68},
                {"timestamp": (INCIDENT_TIME - timedelta(minutes=15)).isoformat(), "value": 0.82},
                {"timestamp": (INCIDENT_TIME - timedelta(minutes=5)).isoformat(), "value": 0.91},
                {"timestamp": INCIDENT_TIME.isoformat(), "value": 0.95},
            ],
            "current": 0.95,
            "threshold": 0.80,
            "is_anomalous": True,
            "anomaly_type": "sustained_increase",
        },
        "memory": {
            "metric": "container_memory_usage_bytes",
            "service": service or AFFECTED_SERVICE,
            "values": [
                {"timestamp": (INCIDENT_TIME - timedelta(hours=2)).isoformat(), "value": 512_000_000},
                {"timestamp": (INCIDENT_TIME - timedelta(hours=1)).isoformat(), "value": 580_000_000},
                {"timestamp": (INCIDENT_TIME - timedelta(minutes=30)).isoformat(), "value": 720_000_000},
                {"timestamp": (INCIDENT_TIME - timedelta(minutes=15)).isoformat(), "value": 890_000_000},
                {"timestamp": INCIDENT_TIME.isoformat(), "value": 980_000_000},
            ],
            "current": 980_000_000,
            "limit": 1_073_741_824,
            "usage_percent": 91.2,
            "is_anomalous": True,
            "anomaly_type": "memory_leak_pattern",
        },
        "error_rate": {
            "metric": "http_requests_total{status=~'5..'}",
            "service": service or AFFECTED_SERVICE,
            "values": [
                {"timestamp": (INCIDENT_TIME - timedelta(hours=2)).isoformat(), "value": 0.002},
                {"timestamp": (INCIDENT_TIME - timedelta(hours=1)).isoformat(), "value": 0.003},
                {"timestamp": (INCIDENT_TIME - timedelta(minutes=30)).isoformat(), "value": 0.008},
                {"timestamp": (INCIDENT_TIME - timedelta(minutes=15)).isoformat(), "value": 0.12},
                {"timestamp": (INCIDENT_TIME - timedelta(minutes=5)).isoformat(), "value": 0.38},
                {"timestamp": INCIDENT_TIME.isoformat(), "value": 0.67},
            ],
            "current": 0.67,
            "threshold": 0.05,
            "is_anomalous": True,
            "anomaly_type": "spike",
        },
        "latency": {
            "metric": "http_request_duration_seconds",
            "service": service or AFFECTED_SERVICE,
            "values": [
                {"timestamp": (INCIDENT_TIME - timedelta(hours=2)).isoformat(), "value": 0.12},
                {"timestamp": (INCIDENT_TIME - timedelta(hours=1)).isoformat(), "value": 0.15},
                {"timestamp": (INCIDENT_TIME - timedelta(minutes=30)).isoformat(), "value": 0.85},
                {"timestamp": (INCIDENT_TIME - timedelta(minutes=15)).isoformat(), "value": 2.4},
                {"timestamp": (INCIDENT_TIME - timedelta(minutes=5)).isoformat(), "value": 8.5},
                {"timestamp": INCIDENT_TIME.isoformat(), "value": 30.0},
            ],
            "current_p50": 2.4,
            "current_p99": 30.0,
            "baseline_p50": 0.12,
            "baseline_p99": 0.45,
            "is_anomalous": True,
            "anomaly_type": "latency_degradation",
        },
        "connections": {
            "metric": "hikaricp_connections_active",
            "service": service or AFFECTED_SERVICE,
            "values": [
                {"timestamp": (INCIDENT_TIME - timedelta(hours=2)).isoformat(), "value": 5},
                {"timestamp": (INCIDENT_TIME - timedelta(hours=1)).isoformat(), "value": 8},
                {"timestamp": (INCIDENT_TIME - timedelta(minutes=30)).isoformat(), "value": 14},
                {"timestamp": (INCIDENT_TIME - timedelta(minutes=15)).isoformat(), "value": 18},
                {"timestamp": (INCIDENT_TIME - timedelta(minutes=5)).isoformat(), "value": 20},
                {"timestamp": INCIDENT_TIME.isoformat(), "value": 20},
            ],
            "current": 20,
            "max_pool_size": 20,
            "usage_percent": 100.0,
            "is_anomalous": True,
            "anomaly_type": "pool_exhaustion",
        },
    }

    for key, data in metric_responses.items():
        if key in query.lower() or data["metric"] in query:
            return data

    return metric_responses["error_rate"]


# ─── Kubernetes Events Data ──────────────────────────────────────────────────

def get_k8s_pod_status(
    service: Optional[str] = None,
    namespace: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Mock Kubernetes pod status."""
    return [
        {
            "name": "payment-service-7d4b8c6f9-x2k4m",
            "namespace": "payments",
            "status": "Running",
            "ready": True,
            "restarts": 3,
            "last_restart_reason": "OOMKilled",
            "last_restart_at": (INCIDENT_TIME - timedelta(minutes=2)).isoformat(),
            "cpu_request": "250m",
            "cpu_limit": "500m",
            "memory_request": "512Mi",
            "memory_limit": "1Gi",
            "node": "worker-node-03",
            "age": "4h 15m",
            "image": "registry.do/payment-service:v2.3.1",
        },
        {
            "name": "payment-service-7d4b8c6f9-r8n3p",
            "namespace": "payments",
            "status": "Running",
            "ready": True,
            "restarts": 2,
            "last_restart_reason": "OOMKilled",
            "last_restart_at": (INCIDENT_TIME - timedelta(minutes=5)).isoformat(),
            "cpu_request": "250m",
            "cpu_limit": "500m",
            "memory_request": "512Mi",
            "memory_limit": "1Gi",
            "node": "worker-node-01",
            "age": "4h 15m",
            "image": "registry.do/payment-service:v2.3.1",
        },
        {
            "name": "payment-service-7d4b8c6f9-m5n7o",
            "namespace": "payments",
            "status": "CrashLoopBackOff",
            "ready": False,
            "restarts": 5,
            "last_restart_reason": "OOMKilled",
            "last_restart_at": (INCIDENT_TIME - timedelta(seconds=30)).isoformat(),
            "cpu_request": "250m",
            "cpu_limit": "500m",
            "memory_request": "512Mi",
            "memory_limit": "1Gi",
            "node": "worker-node-02",
            "age": "4h 15m",
            "image": "registry.do/payment-service:v2.3.1",
        },
    ]


def get_k8s_events(
    service: Optional[str] = None,
    namespace: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Mock Kubernetes events."""
    return [
        {
            "type": "Warning",
            "reason": "OOMKilling",
            "object": "pod/payment-service-7d4b8c6f9-m5n7o",
            "namespace": "payments",
            "message": "Memory cgroup out of memory: Killed process 1 (java) total-vm:2048000kB",
            "timestamp": (INCIDENT_TIME - timedelta(seconds=30)).isoformat(),
            "count": 5,
            "first_seen": (INCIDENT_TIME - timedelta(minutes=10)).isoformat(),
            "last_seen": (INCIDENT_TIME - timedelta(seconds=30)).isoformat(),
        },
        {
            "type": "Warning",
            "reason": "BackOff",
            "object": "pod/payment-service-7d4b8c6f9-m5n7o",
            "namespace": "payments",
            "message": "Back-off restarting failed container",
            "timestamp": (INCIDENT_TIME - timedelta(seconds=15)).isoformat(),
            "count": 3,
            "first_seen": (INCIDENT_TIME - timedelta(minutes=5)).isoformat(),
            "last_seen": (INCIDENT_TIME - timedelta(seconds=15)).isoformat(),
        },
        {
            "type": "Warning",
            "reason": "Unhealthy",
            "object": "pod/payment-service-7d4b8c6f9-x2k4m",
            "namespace": "payments",
            "message": "Readiness probe failed: HTTP probe failed with statuscode: 503",
            "timestamp": (INCIDENT_TIME - timedelta(minutes=3)).isoformat(),
            "count": 8,
            "first_seen": (INCIDENT_TIME - timedelta(minutes=8)).isoformat(),
            "last_seen": (INCIDENT_TIME - timedelta(minutes=1)).isoformat(),
        },
        {
            "type": "Normal",
            "reason": "Pulling",
            "object": "pod/payment-service-7d4b8c6f9-m5n7o",
            "namespace": "payments",
            "message": "Pulling image 'registry.do/payment-service:v2.3.1'",
            "timestamp": DEPLOY_TIME.isoformat(),
            "count": 1,
            "first_seen": DEPLOY_TIME.isoformat(),
            "last_seen": DEPLOY_TIME.isoformat(),
        },
        {
            "type": "Normal",
            "reason": "ScalingReplicaSet",
            "object": "deployment/payment-service",
            "namespace": "payments",
            "message": "Scaled up replica set payment-service-7d4b8c6f9 to 3",
            "timestamp": DEPLOY_TIME.isoformat(),
            "count": 1,
            "first_seen": DEPLOY_TIME.isoformat(),
            "last_seen": DEPLOY_TIME.isoformat(),
        },
    ]


# ─── Runbook Data ────────────────────────────────────────────────────────────

def get_runbooks(query: str, service: Optional[str] = None) -> List[Dict[str, Any]]:
    """Mock knowledge base search for runbooks."""
    runbooks = [
        {
            "id": "rb-001",
            "title": "Connection Pool Exhaustion Runbook",
            "service_tags": ["payment-service", "checkout-service", "any-jdbc-service"],
            "symptoms": [
                "Error rate spike > 5%",
                "Connection pool at 100%",
                "NullPointerException in connection handling",
                "Slow response times",
            ],
            "immediate_actions": [
                "Scale up replicas: kubectl scale deployment/<SERVICE> --replicas=<N>",
                "Restart pods: kubectl rollout restart deployment/<SERVICE>",
                "Rollback if recent deploy: kubectl rollout undo deployment/<SERVICE>",
            ],
            "investigation_steps": [
                "Check connection pool metrics: hikaricp_connections_active",
                "Check for connection leaks in application logs",
                "Check database performance for long-running queries",
            ],
            "relevance_score": 0.95,
            "content_path": "knowledge/runbooks/connection-pool-exhaustion.md",
        },
        {
            "id": "rb-002",
            "title": "High Error Rate Investigation",
            "service_tags": ["any"],
            "symptoms": [
                "Error rate exceeds threshold",
                "5xx responses increasing",
                "Downstream services reporting failures",
            ],
            "immediate_actions": [
                "Check recent deployments",
                "Check dependency health",
                "Check resource utilization",
            ],
            "investigation_steps": [
                "Identify error signatures in logs",
                "Check if error rate correlates with deployments",
                "Verify external dependencies are healthy",
            ],
            "relevance_score": 0.78,
            "content_path": None,
        },
    ]

    query_lower = query.lower()
    scored = []
    for rb in runbooks:
        score = rb["relevance_score"]
        if any(kw in query_lower for kw in ["connection", "pool", "hikari", "exhaustion"]):
            if "connection" in rb["title"].lower():
                score = min(1.0, score + 0.05)
        if service and service in rb["service_tags"]:
            score = min(1.0, score + 0.05)
        scored.append({**rb, "relevance_score": score})

    scored.sort(key=lambda x: x["relevance_score"], reverse=True)
    return scored


# ─── Past Incidents Data ─────────────────────────────────────────────────────

def get_past_incidents(
    query: str,
    alert_type: Optional[str] = None,
    service: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Mock knowledge base search for past incidents."""
    incidents = [
        {
            "incident_id": "INC-2024-0892",
            "title": "Payment service connection pool exhaustion",
            "created_at": "2024-11-15T03:15:00Z",
            "resolved_at": "2024-11-15T03:45:00Z",
            "severity": "critical",
            "alert_type": "error_rate",
            "affected_services": ["payment-service", "checkout-service"],
            "root_cause": "Connection leak in PaymentProcessor.java introduced in v2.3.1",
            "root_cause_category": "deployment",
            "remediation_that_worked": {
                "summary": "Rollback to v2.3.0 and increase connection pool size",
                "steps": ["Rollback deployment", "Increase pool size from 20 to 50", "Monitor error rate"],
                "success_rate": 1.0,
            },
            "resolution_time_seconds": 1800,
            "similarity_score": 0.92,
            "tags": ["payment", "connection-pool", "deployment"],
        },
        {
            "incident_id": "INC-2024-0756",
            "title": "Checkout service OOM crash loop",
            "created_at": "2024-09-03T14:22:00Z",
            "resolved_at": "2024-09-03T15:10:00Z",
            "severity": "critical",
            "alert_type": "crash",
            "affected_services": ["checkout-service"],
            "root_cause": "Memory leak in session cache after v1.7.5 upgrade",
            "root_cause_category": "deployment",
            "remediation_that_worked": {
                "summary": "Rollback and add memory limits to session cache",
                "steps": ["Rollback to v1.7.4", "Set session cache max size to 10000", "Add eviction policy"],
                "success_rate": 1.0,
            },
            "resolution_time_seconds": 2880,
            "similarity_score": 0.74,
            "tags": ["checkout", "oom", "memory-leak", "deployment"],
        },
        {
            "incident_id": "INC-2025-0201",
            "title": "Payment gateway timeout during peak traffic",
            "created_at": "2025-06-18T18:45:00Z",
            "resolved_at": "2025-06-18T19:30:00Z",
            "severity": "high",
            "alert_type": "latency",
            "affected_services": ["payment-service", "gateway-service"],
            "root_cause": "Database connection pool too small for peak traffic volume",
            "root_cause_category": "resource",
            "remediation_that_worked": {
                "summary": "Increase connection pool and add horizontal pod autoscaler",
                "steps": ["Increase pool to 50 connections", "Add HPA with CPU target 70%", "Scale to 5 replicas"],
                "success_rate": 1.0,
            },
            "resolution_time_seconds": 2700,
            "similarity_score": 0.68,
            "tags": ["payment", "latency", "connection-pool", "scaling"],
        },
    ]

    results = incidents
    if alert_type:
        results = [i for i in results if i["alert_type"] == alert_type]
    if service:
        results = [i for i in results if service in i["affected_services"]]

    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results
