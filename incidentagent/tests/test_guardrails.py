"""
Guardrails Tests

Tests that dangerous commands are blocked, high-risk commands are flagged,
safe commands pass through, and risk scores are calculated correctly.
"""

from typing import List

import pytest

from incidentagent.agents.remediation import RemediationAgent, RemediationGuardrails
from incidentagent.schemas.remediation import RemediationStep, RiskLevel


def _make_step(
    command: str,
    risk_level: RiskLevel = RiskLevel.LOW,
    step_number: int = 1,
    requires_approval: bool = False,
) -> RemediationStep:
    """Create a RemediationStep with sensible defaults for testing."""
    return RemediationStep(
        step_number=step_number,
        action=f"Test action for: {command}",
        command=command,
        command_type="bash",
        risk_level=risk_level,
        risk_reasoning="Test step",
        requires_approval=requires_approval,
    )


class TestBlockedCommands:
    """Tests that dangerous commands are blocked by guardrails."""

    def setup_method(self) -> None:
        self.guardrails = RemediationGuardrails()

    def test_rm_rf_is_blocked(self) -> None:
        steps = [_make_step("rm -rf /var/data")]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 0

    def test_drop_database_is_blocked(self) -> None:
        steps = [_make_step("psql -c 'DROP DATABASE production'")]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 0

    def test_delete_from_is_blocked(self) -> None:
        steps = [_make_step("mysql -e 'DELETE FROM users'")]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 0

    def test_kubectl_delete_namespace_is_blocked(self) -> None:
        steps = [_make_step("kubectl delete namespace production")]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 0

    def test_terraform_destroy_is_blocked(self) -> None:
        steps = [_make_step("terraform destroy -auto-approve")]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 0

    def test_redirect_to_dev_is_blocked(self) -> None:
        steps = [_make_step("cat data > /dev/sda")]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 0

    def test_mkfs_is_blocked(self) -> None:
        steps = [_make_step("mkfs.ext4 /dev/sda1")]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 0

    def test_dd_is_blocked(self) -> None:
        steps = [_make_step("dd if=/dev/zero of=/dev/sda bs=1M")]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 0

    def test_blocked_command_recorded_in_guardrails(self) -> None:
        steps = [_make_step("rm -rf /tmp/data")]
        self.guardrails.check_steps(steps)
        assert any("blocked" in g for g in self.guardrails.applied_guardrails)

    def test_case_insensitive_blocking(self) -> None:
        steps = [_make_step("psql -c 'drop database mydb'")]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 0

    def test_multiple_blocked_commands_all_removed(self) -> None:
        steps = [
            _make_step("rm -rf /data", step_number=1),
            _make_step("DROP DATABASE prod", step_number=2),
            _make_step("terraform destroy", step_number=3),
        ]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 0


class TestHighRiskCommands:
    """Tests that high-risk commands are flagged but not blocked."""

    def setup_method(self) -> None:
        self.guardrails = RemediationGuardrails()

    def test_kubectl_delete_pod_flagged_high_risk(self) -> None:
        steps = [_make_step("kubectl delete pod my-pod-abc123 -n production")]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 1
        assert result[0].risk_level == RiskLevel.HIGH
        assert result[0].requires_approval is True

    def test_kubectl_scale_to_zero_flagged_high_risk(self) -> None:
        steps = [_make_step("kubectl scale deployment/my-app --replicas=0 -n prod")]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 1
        assert result[0].risk_level == RiskLevel.HIGH

    def test_alter_table_flagged_high_risk(self) -> None:
        steps = [_make_step("psql -c 'ALTER TABLE users ADD COLUMN status varchar(50)'")]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 1
        assert result[0].risk_level == RiskLevel.HIGH

    def test_update_set_flagged_high_risk(self) -> None:
        steps = [_make_step("mysql -e 'UPDATE users SET status=inactive WHERE last_login < now()'")]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 1
        assert result[0].risk_level == RiskLevel.HIGH

    def test_truncate_flagged_high_risk(self) -> None:
        steps = [_make_step("psql -c 'TRUNCATE TABLE temp_logs'")]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 1
        assert result[0].risk_level == RiskLevel.HIGH

    def test_high_risk_requires_approval(self) -> None:
        steps = [_make_step("kubectl delete pod some-pod -n staging")]
        result = self.guardrails.check_steps(steps)
        assert result[0].requires_approval is True

    def test_high_risk_recorded_in_guardrails(self) -> None:
        steps = [_make_step("kubectl delete pod some-pod -n staging")]
        self.guardrails.check_steps(steps)
        assert any("flagged_high_risk" in g for g in self.guardrails.applied_guardrails)


class TestSafeCommands:
    """Tests that safe commands pass through without modification."""

    def setup_method(self) -> None:
        self.guardrails = RemediationGuardrails()

    def test_kubectl_get_passes_through(self) -> None:
        steps = [_make_step("kubectl get pods -n production")]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 1
        assert result[0].risk_level == RiskLevel.LOW

    def test_kubectl_describe_passes_through(self) -> None:
        steps = [_make_step("kubectl describe pod my-pod -n production")]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 1
        assert result[0].risk_level == RiskLevel.LOW

    def test_kubectl_logs_passes_through(self) -> None:
        steps = [_make_step("kubectl logs deployment/my-app -n production --tail=100")]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 1
        assert result[0].risk_level == RiskLevel.LOW

    def test_kubectl_rollout_status_passes_through(self) -> None:
        steps = [_make_step("kubectl rollout status deployment/my-app -n production")]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 1
        assert result[0].risk_level == RiskLevel.LOW

    def test_kubectl_top_passes_through(self) -> None:
        steps = [_make_step("kubectl top pods -n production")]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 1
        assert result[0].risk_level == RiskLevel.LOW

    def test_curl_health_check_passes_through(self) -> None:
        steps = [_make_step("curl -s http://localhost:8080/health")]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 1
        assert result[0].risk_level == RiskLevel.LOW

    def test_kubectl_rollout_undo_passes_at_medium(self) -> None:
        step = _make_step(
            "kubectl rollout undo deployment/my-app -n production",
            risk_level=RiskLevel.MEDIUM,
        )
        result = self.guardrails.check_steps([step])
        assert len(result) == 1
        assert result[0].risk_level == RiskLevel.MEDIUM

    def test_step_without_command_passes_through(self) -> None:
        step = RemediationStep(
            step_number=1,
            action="Manually review the logs in Grafana",
            command=None,
            risk_level=RiskLevel.LOW,
            risk_reasoning="Manual review only",
            requires_approval=False,
        )
        result = self.guardrails.check_steps([step])
        assert len(result) == 1

    def test_mixed_steps_preserve_safe_ones(self) -> None:
        steps = [
            _make_step("kubectl get pods -n production", step_number=1),
            _make_step("rm -rf /data", step_number=2),
            _make_step("kubectl logs my-pod -n production", step_number=3),
        ]
        result = self.guardrails.check_steps(steps)
        assert len(result) == 2
        assert result[0].step_number == 1
        assert result[1].step_number == 3


class TestRiskScoreCalculation:
    """Tests for the RemediationAgent risk score calculation."""

    def setup_method(self) -> None:
        self.agent = RemediationAgent()

    def test_empty_steps_returns_zero(self) -> None:
        score = self.agent._calculate_risk_score([])
        assert score == 0.0

    def test_all_low_risk(self) -> None:
        steps = [
            _make_step("kubectl get pods", risk_level=RiskLevel.LOW, step_number=1),
            _make_step("kubectl describe pod", risk_level=RiskLevel.LOW, step_number=2),
        ]
        score = self.agent._calculate_risk_score(steps)
        # max=0.1, avg=0.1 => 0.7*0.1 + 0.3*0.1 = 0.1
        assert abs(score - 0.1) < 0.01

    def test_all_critical_risk(self) -> None:
        steps = [
            _make_step("dangerous-cmd-1", risk_level=RiskLevel.CRITICAL, step_number=1),
            _make_step("dangerous-cmd-2", risk_level=RiskLevel.CRITICAL, step_number=2),
        ]
        score = self.agent._calculate_risk_score(steps)
        # max=0.95, avg=0.95 => 0.7*0.95 + 0.3*0.95 = 0.95
        assert abs(score - 0.95) < 0.01

    def test_mixed_risk_weights_towards_max(self) -> None:
        steps = [
            _make_step("kubectl get pods", risk_level=RiskLevel.LOW, step_number=1),
            _make_step("kubectl delete pod x", risk_level=RiskLevel.HIGH, step_number=2),
        ]
        score = self.agent._calculate_risk_score(steps)
        # max=0.7, avg=(0.1+0.7)/2=0.4 => 0.7*0.7 + 0.3*0.4 = 0.49+0.12 = 0.61
        assert abs(score - 0.61) < 0.01

    def test_single_medium_step(self) -> None:
        steps = [_make_step("kubectl rollout undo", risk_level=RiskLevel.MEDIUM)]
        score = self.agent._calculate_risk_score(steps)
        # max=0.4, avg=0.4 => 0.7*0.4 + 0.3*0.4 = 0.4
        assert abs(score - 0.4) < 0.01

    def test_risk_score_within_bounds(self) -> None:
        steps = [
            _make_step("cmd1", risk_level=RiskLevel.LOW, step_number=1),
            _make_step("cmd2", risk_level=RiskLevel.MEDIUM, step_number=2),
            _make_step("cmd3", risk_level=RiskLevel.HIGH, step_number=3),
            _make_step("cmd4", risk_level=RiskLevel.CRITICAL, step_number=4),
        ]
        score = self.agent._calculate_risk_score(steps)
        assert 0.0 <= score <= 1.0


class TestHighestRiskStepDetection:
    """Tests for finding the highest risk step."""

    def setup_method(self) -> None:
        self.agent = RemediationAgent()

    def test_finds_critical_step(self) -> None:
        steps = [
            _make_step("cmd1", risk_level=RiskLevel.LOW, step_number=1),
            _make_step("cmd2", risk_level=RiskLevel.CRITICAL, step_number=2),
            _make_step("cmd3", risk_level=RiskLevel.MEDIUM, step_number=3),
        ]
        result = self.agent._find_highest_risk_step(steps)
        assert result == 2

    def test_finds_high_when_no_critical(self) -> None:
        steps = [
            _make_step("cmd1", risk_level=RiskLevel.LOW, step_number=1),
            _make_step("cmd2", risk_level=RiskLevel.HIGH, step_number=2),
            _make_step("cmd3", risk_level=RiskLevel.MEDIUM, step_number=3),
        ]
        result = self.agent._find_highest_risk_step(steps)
        assert result == 2

    def test_returns_none_for_empty_steps(self) -> None:
        result = self.agent._find_highest_risk_step([])
        assert result is None

    def test_returns_first_highest_when_tied(self) -> None:
        steps = [
            _make_step("cmd1", risk_level=RiskLevel.HIGH, step_number=1),
            _make_step("cmd2", risk_level=RiskLevel.HIGH, step_number=2),
        ]
        result = self.agent._find_highest_risk_step(steps)
        assert result == 1


class TestRequireRollbackGuardrail:
    """Tests that high-risk steps without rollback plans trigger guardrails."""

    def setup_method(self) -> None:
        self.guardrails = RemediationGuardrails()

    def test_high_risk_without_rollback_requires_approval(self) -> None:
        step = RemediationStep(
            step_number=1,
            action="Dangerous action without rollback",
            command="kubectl delete pod my-pod",
            command_type="kubectl",
            risk_level=RiskLevel.MEDIUM,  # Will be elevated to HIGH by pattern match
            risk_reasoning="Test step",
            requires_approval=False,
            rollback_plan=None,
        )
        result = self.guardrails.check_steps([step])
        assert len(result) == 1
        assert result[0].requires_approval is True

    def test_high_risk_with_rollback_still_passes(self) -> None:
        step = RemediationStep(
            step_number=1,
            action="Delete pod with rollback plan",
            command="kubectl delete pod my-pod",
            command_type="kubectl",
            risk_level=RiskLevel.MEDIUM,
            risk_reasoning="Test step",
            requires_approval=False,
            rollback_plan="Recreate the pod from deployment",
        )
        result = self.guardrails.check_steps([step])
        assert len(result) == 1
        # Still flagged as HIGH by pattern, but rollback plan is present
        assert result[0].risk_level == RiskLevel.HIGH
