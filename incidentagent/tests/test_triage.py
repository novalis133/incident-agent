"""
Triage Agent Tests

Tests rule-based classification for each alert type and severity detection.
Uses mock data only - no LLM required.
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from incidentagent.agents.triage import TriageAgent
from incidentagent.schemas.alert import AlertSource, UnifiedAlert
from incidentagent.schemas.triage import AlertType


def _make_alert(
    title: str,
    severity: str = "high",
    service: str = "test-service",
    description: str = "",
) -> UnifiedAlert:
    """Create a UnifiedAlert with sensible defaults for testing."""
    return UnifiedAlert(
        id="test-alert-001",
        source=AlertSource.MANUAL,
        title=title,
        description=description,
        severity=severity,
        service=service,
        fired_at=datetime.utcnow(),
    )


class TestRuleBasedClassification:
    """Tests for the rule-based _classify_alert_type fallback."""

    def setup_method(self) -> None:
        self.agent = TriageAgent()

    def test_error_rate_from_error_rate_keyword(self) -> None:
        alert = _make_alert("High error rate on payment-service")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.ERROR_RATE

    def test_error_rate_from_5xx_keyword(self) -> None:
        alert = _make_alert("Elevated 5xx errors on checkout-service")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.ERROR_RATE

    def test_error_rate_from_exception_keyword(self) -> None:
        alert = _make_alert("Exception rate spike on notification-service")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.ERROR_RATE

    def test_error_rate_from_4xx_keyword(self) -> None:
        alert = _make_alert("4xx error surge on user-service")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.ERROR_RATE

    def test_latency_from_latency_keyword(self) -> None:
        alert = _make_alert("Latency spike on order-service")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.LATENCY

    def test_latency_from_slow_keyword(self) -> None:
        alert = _make_alert("Slow response time on user-service")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.LATENCY

    def test_latency_from_timeout_keyword(self) -> None:
        alert = _make_alert("Timeout errors on gateway-service")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.LATENCY

    def test_latency_from_response_time_keyword(self) -> None:
        alert = _make_alert("High response time on API endpoints")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.LATENCY

    def test_crash_from_crash_keyword(self) -> None:
        alert = _make_alert("Pod crash loop on inventory-service")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.CRASH

    def test_crash_from_restart_keyword(self) -> None:
        alert = _make_alert("Container restart storm on cart-service")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.CRASH

    def test_crash_from_oom_keyword(self) -> None:
        alert = _make_alert("OOM killed on recommendation-engine")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.CRASH

    def test_crash_from_terminated_keyword(self) -> None:
        alert = _make_alert("Container terminated on billing-service")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.CRASH

    def test_resource_from_cpu_keyword(self) -> None:
        alert = _make_alert("High CPU usage on search-service")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.RESOURCE

    def test_resource_from_memory_keyword(self) -> None:
        alert = _make_alert("Memory leak detected on analytics-service")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.RESOURCE

    def test_resource_from_disk_keyword(self) -> None:
        alert = _make_alert("Disk space critical on logging-service")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.RESOURCE

    def test_dependency_from_database_keyword(self) -> None:
        alert = _make_alert("Database connection pool exhausted")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.DEPENDENCY

    def test_dependency_from_redis_keyword(self) -> None:
        alert = _make_alert("Redis cluster unreachable")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.DEPENDENCY

    def test_dependency_from_kafka_keyword(self) -> None:
        alert = _make_alert("Kafka consumer lag increasing")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.DEPENDENCY

    def test_config_from_config_keyword(self) -> None:
        alert = _make_alert("Config map update failed on auth-service")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.CONFIG

    def test_config_from_secret_keyword(self) -> None:
        alert = _make_alert("Secret rotation caused service failure")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.CONFIG

    def test_config_from_environment_keyword(self) -> None:
        alert = _make_alert("Environment variable misconfiguration on api-gateway")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.CONFIG

    def test_unknown_for_ambiguous_title(self) -> None:
        alert = _make_alert("Service degradation detected")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.UNKNOWN

    def test_unknown_for_empty_title(self) -> None:
        alert = _make_alert("")
        result = self.agent._classify_alert_type(alert)
        assert result == AlertType.UNKNOWN


class TestSeverityDetection:
    """Tests that triage preserves and correctly handles severity levels."""

    def setup_method(self) -> None:
        self.agent = TriageAgent()

    @pytest.mark.asyncio
    @patch("incidentagent.agents.triage.get_llm_client")
    async def test_critical_severity_preserved(self, mock_llm_factory: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_client.is_available = False
        mock_llm_factory.return_value = mock_client

        alert = _make_alert("High error rate on payment-service", severity="critical")
        result = await self.agent.triage(alert)

        assert result.severity == "critical"

    @pytest.mark.asyncio
    @patch("incidentagent.agents.triage.get_llm_client")
    async def test_high_severity_preserved(self, mock_llm_factory: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_client.is_available = False
        mock_llm_factory.return_value = mock_client

        alert = _make_alert("Latency spike on order-service", severity="high")
        result = await self.agent.triage(alert)

        assert result.severity == "high"

    @pytest.mark.asyncio
    @patch("incidentagent.agents.triage.get_llm_client")
    async def test_medium_severity_preserved(self, mock_llm_factory: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_client.is_available = False
        mock_llm_factory.return_value = mock_client

        alert = _make_alert("Config map update failed", severity="medium")
        result = await self.agent.triage(alert)

        assert result.severity == "medium"

    @pytest.mark.asyncio
    @patch("incidentagent.agents.triage.get_llm_client")
    async def test_low_severity_preserved(self, mock_llm_factory: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_client.is_available = False
        mock_llm_factory.return_value = mock_client

        alert = _make_alert("Minor disk usage warning", severity="low")
        result = await self.agent.triage(alert)

        assert result.severity == "low"

    @pytest.mark.asyncio
    @patch("incidentagent.agents.triage.get_llm_client")
    async def test_critical_requires_immediate_attention(self, mock_llm_factory: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_client.is_available = False
        mock_llm_factory.return_value = mock_client

        alert = _make_alert("Pod crash loop", severity="critical")
        result = await self.agent.triage(alert)

        assert result.requires_immediate_attention is True

    @pytest.mark.asyncio
    @patch("incidentagent.agents.triage.get_llm_client")
    async def test_low_does_not_require_immediate_attention(self, mock_llm_factory: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_client.is_available = False
        mock_llm_factory.return_value = mock_client

        alert = _make_alert("Minor disk usage warning", severity="low")
        result = await self.agent.triage(alert)

        assert result.requires_immediate_attention is False


class TestTriagePriorityQueue:
    """Tests that the priority queue is populated correctly."""

    def setup_method(self) -> None:
        self.agent = TriageAgent()

    @pytest.mark.asyncio
    @patch("incidentagent.agents.triage.get_llm_client")
    async def test_error_rate_priority_starts_with_deploy(self, mock_llm_factory: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_client.is_available = False
        mock_llm_factory.return_value = mock_client

        alert = _make_alert("High error rate on payment-service")
        result = await self.agent.triage(alert)

        assert result.priority_queue[0] == "DeployAgent"

    @pytest.mark.asyncio
    @patch("incidentagent.agents.triage.get_llm_client")
    async def test_crash_priority_starts_with_k8s(self, mock_llm_factory: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_client.is_available = False
        mock_llm_factory.return_value = mock_client

        alert = _make_alert("Pod crash loop on inventory-service")
        result = await self.agent.triage(alert)

        assert result.priority_queue[0] == "K8sAgent"

    @pytest.mark.asyncio
    @patch("incidentagent.agents.triage.get_llm_client")
    async def test_resource_priority_starts_with_metrics(self, mock_llm_factory: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_client.is_available = False
        mock_llm_factory.return_value = mock_client

        alert = _make_alert("High CPU usage on search-service")
        result = await self.agent.triage(alert)

        assert result.priority_queue[0] == "MetricsAgent"

    @pytest.mark.asyncio
    @patch("incidentagent.agents.triage.get_llm_client")
    async def test_dependency_priority_starts_with_logs(self, mock_llm_factory: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_client.is_available = False
        mock_llm_factory.return_value = mock_client

        alert = _make_alert("Database connection pool exhausted")
        result = await self.agent.triage(alert)

        assert result.priority_queue[0] == "LogsAgent"

    @pytest.mark.asyncio
    @patch("incidentagent.agents.triage.get_llm_client")
    async def test_config_priority_starts_with_deploy(self, mock_llm_factory: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_client.is_available = False
        mock_llm_factory.return_value = mock_client

        alert = _make_alert("Config map update failed on auth-service")
        result = await self.agent.triage(alert)

        assert result.priority_queue[0] == "DeployAgent"

    @pytest.mark.asyncio
    @patch("incidentagent.agents.triage.get_llm_client")
    async def test_priority_queue_is_non_empty(self, mock_llm_factory: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_client.is_available = False
        mock_llm_factory.return_value = mock_client

        alert = _make_alert("Something unusual happened")
        result = await self.agent.triage(alert)

        assert len(result.priority_queue) > 0
