"""
Remediation Agent

Generates safe remediation suggestions with guardrails.
"""

from datetime import datetime
from typing import List, Optional
import uuid

import structlog

try:
    from gradient_adk import trace_tool
except ImportError:
    def trace_tool(name):
        def decorator(fn):
            return fn
        return decorator

from incidentagent.schemas.evidence import AgentEvidence
from incidentagent.schemas.remediation import (
    Remediation,
    RemediationStep,
    RiskLevel,
)
from incidentagent.schemas.root_cause import RootCauseHypothesis, RootCauseCategory

logger = structlog.get_logger()


class RemediationAgent:
    """
    Remediation Agent - Generates safe fix suggestions.
    
    Responsibilities:
    - Generate remediation steps based on root cause
    - Apply guardrails for safety
    - Calculate risk scores
    - Require approval for high-risk actions
    - Include rollback plans
    """
    
    def __init__(self):
        self.logger = logger.bind(agent="RemediationAgent")
        self.guardrails = RemediationGuardrails()
    
    @trace_tool("generate-remediation")
    async def generate(
        self,
        root_cause: Optional[RootCauseHypothesis],
        evidence: List[AgentEvidence],
        memory_findings: Optional[AgentEvidence] = None,
    ) -> Remediation:
        """
        Generate remediation plan.
        
        Args:
            root_cause: Root cause hypothesis
            evidence: All evidence collected
            memory_findings: Optional past incident learnings
        
        Returns:
            Safe remediation plan with guardrails applied
        """
        self.logger.info(
            "generating_remediation",
            root_cause=root_cause.hypothesis if root_cause else "unknown",
        )
        
        if not root_cause:
            return self._generate_unknown_remediation()
        
        # Generate steps based on root cause category
        steps = self._generate_steps(root_cause, evidence)
        
        # Apply guardrails
        steps = self.guardrails.check_steps(steps)
        
        # Calculate total risk
        total_risk = self._calculate_risk_score(steps)
        requires_approval = any(
            s.requires_approval for s in steps
        )
        
        remediation = Remediation(
            id=f"rem-{uuid.uuid4().hex[:8]}",
            investigation_id=evidence[0].investigation_id if evidence else "unknown",
            root_cause_id=root_cause.id,
            summary=self._generate_summary(root_cause, steps),
            detailed_explanation=self._generate_explanation(root_cause),
            steps=steps,
            total_steps=len(steps),
            total_risk_score=total_risk,
            highest_risk_step=self._find_highest_risk_step(steps),
            requires_human_approval=requires_approval,
            estimated_resolution_time=self._estimate_time(steps),
            guardrails_applied=self.guardrails.applied_guardrails,
        )
        
        self.logger.info(
            "remediation_generated",
            steps=len(steps),
            risk_score=total_risk,
            requires_approval=requires_approval,
        )
        
        return remediation
    
    def _generate_steps(
        self,
        root_cause: RootCauseHypothesis,
        evidence: List[AgentEvidence],
    ) -> List[RemediationStep]:
        """Generate remediation steps based on root cause category."""
        
        # Category-specific remediation templates
        if root_cause.category == RootCauseCategory.DEPLOYMENT:
            return self._deployment_remediation(root_cause)
        elif root_cause.category == RootCauseCategory.RESOURCE:
            return self._resource_remediation(root_cause)
        elif root_cause.category == RootCauseCategory.DEPENDENCY:
            return self._dependency_remediation(root_cause)
        elif root_cause.category == RootCauseCategory.CONFIG:
            return self._config_remediation(root_cause)
        else:
            return self._generic_remediation(root_cause)
    
    def _deployment_remediation(self, root_cause: RootCauseHypothesis) -> List[RemediationStep]:
        """Remediation steps for deployment-related issues."""
        return [
            RemediationStep(
                step_number=1,
                action="Verify current deployment state",
                command="kubectl get deployments -n <namespace>",
                command_type="kubectl",
                risk_level=RiskLevel.LOW,
                risk_reasoning="Read-only operation",
                requires_approval=False,
                estimated_time="1 minute",
            ),
            RemediationStep(
                step_number=2,
                action="Rollback to previous version",
                command="kubectl rollout undo deployment/<service> -n <namespace>",
                command_type="kubectl",
                risk_level=RiskLevel.MEDIUM,
                risk_reasoning="Rollback is generally safe but may cause brief interruption",
                requires_approval=False,
                rollback_plan="Re-apply the current version if rollback fails",
                rollback_command="kubectl rollout undo deployment/<service> -n <namespace>",
                pre_conditions=["Verify previous version is available"],
                post_validation="Check error rate returns to normal within 5 minutes",
                estimated_time="2-5 minutes",
            ),
            RemediationStep(
                step_number=3,
                action="Monitor for stabilization",
                command="kubectl rollout status deployment/<service> -n <namespace>",
                command_type="kubectl",
                risk_level=RiskLevel.LOW,
                risk_reasoning="Read-only operation",
                requires_approval=False,
                estimated_time="5 minutes",
                depends_on=[2],
            ),
        ]
    
    def _resource_remediation(self, root_cause: RootCauseHypothesis) -> List[RemediationStep]:
        """Remediation steps for resource exhaustion."""
        return [
            RemediationStep(
                step_number=1,
                action="Check current resource usage",
                command="kubectl top pods -n <namespace>",
                command_type="kubectl",
                risk_level=RiskLevel.LOW,
                risk_reasoning="Read-only operation",
                requires_approval=False,
                estimated_time="1 minute",
            ),
            RemediationStep(
                step_number=2,
                action="Scale up replicas if needed",
                command="kubectl scale deployment/<service> --replicas=<N> -n <namespace>",
                command_type="kubectl",
                risk_level=RiskLevel.LOW,
                risk_reasoning="Scaling up is safe",
                requires_approval=False,
                rollback_plan="Scale back down to original replica count",
                estimated_time="2-3 minutes",
            ),
            RemediationStep(
                step_number=3,
                action="Increase resource limits if needed",
                command="kubectl edit deployment/<service> -n <namespace>",
                command_type="kubectl",
                risk_level=RiskLevel.MEDIUM,
                risk_reasoning="Resource changes require pod restart",
                requires_approval=True,
                rollback_plan="Revert resource limits to previous values",
                estimated_time="5-10 minutes",
            ),
        ]
    
    def _dependency_remediation(self, root_cause: RootCauseHypothesis) -> List[RemediationStep]:
        """Remediation for dependency failures."""
        return [
            RemediationStep(
                step_number=1,
                action="Check dependency status",
                command="curl -s <dependency-health-endpoint>",
                command_type="bash",
                risk_level=RiskLevel.LOW,
                risk_reasoning="Health check only",
                requires_approval=False,
                estimated_time="1 minute",
            ),
            RemediationStep(
                step_number=2,
                action="Enable circuit breaker or fallback",
                command="kubectl set env deployment/<service> ENABLE_FALLBACK=true -n <namespace>",
                command_type="kubectl",
                risk_level=RiskLevel.MEDIUM,
                risk_reasoning="Behavior change, may affect functionality",
                requires_approval=True,
                rollback_plan="Disable fallback: kubectl set env deployment/<service> ENABLE_FALLBACK=false",
                estimated_time="2-3 minutes",
            ),
        ]
    
    def _config_remediation(self, root_cause: RootCauseHypothesis) -> List[RemediationStep]:
        """Remediation for configuration issues."""
        return [
            RemediationStep(
                step_number=1,
                action="Review current configuration",
                command="kubectl get configmap <configmap> -n <namespace> -o yaml",
                command_type="kubectl",
                risk_level=RiskLevel.LOW,
                risk_reasoning="Read-only operation",
                requires_approval=False,
                estimated_time="1 minute",
            ),
            RemediationStep(
                step_number=2,
                action="Revert to known good configuration",
                command="kubectl apply -f <previous-config.yaml>",
                command_type="kubectl",
                risk_level=RiskLevel.MEDIUM,
                risk_reasoning="Configuration change may require restart",
                requires_approval=True,
                rollback_plan="Re-apply current configuration",
                estimated_time="3-5 minutes",
            ),
        ]
    
    def _generic_remediation(self, root_cause: RootCauseHypothesis) -> List[RemediationStep]:
        """Generic remediation for unknown issues."""
        return [
            RemediationStep(
                step_number=1,
                action="Investigate further with detailed logging",
                command="kubectl logs -f deployment/<service> -n <namespace> --tail=100",
                command_type="kubectl",
                risk_level=RiskLevel.LOW,
                risk_reasoning="Read-only operation",
                requires_approval=False,
                estimated_time="5-10 minutes",
            ),
            RemediationStep(
                step_number=2,
                action="Restart affected pods",
                command="kubectl rollout restart deployment/<service> -n <namespace>",
                command_type="kubectl",
                risk_level=RiskLevel.MEDIUM,
                risk_reasoning="Restart causes brief interruption",
                requires_approval=True,
                rollback_plan="No specific rollback - pods will restart automatically",
                estimated_time="2-5 minutes",
            ),
        ]
    
    def _generate_unknown_remediation(self) -> Remediation:
        """Generate remediation when root cause is unknown."""
        return Remediation(
            id=f"rem-{uuid.uuid4().hex[:8]}",
            investigation_id="unknown",
            root_cause_id="unknown",
            summary="Unable to determine root cause. Manual investigation recommended.",
            detailed_explanation="The investigation could not determine a root cause with sufficient confidence. Please review the evidence and investigate manually.",
            steps=[
                RemediationStep(
                    step_number=1,
                    action="Review investigation evidence manually",
                    risk_level=RiskLevel.LOW,
                    risk_reasoning="Manual review only",
                    requires_approval=False,
                    estimated_time="30-60 minutes",
                ),
            ],
            total_steps=1,
            total_risk_score=0.1,
            requires_human_approval=True,
            estimated_resolution_time="Unknown - manual investigation required",
            warnings=["Root cause could not be determined automatically"],
        )
    
    def _calculate_risk_score(self, steps: List[RemediationStep]) -> float:
        """Calculate overall risk score."""
        if not steps:
            return 0.0
        
        risk_values = {
            RiskLevel.LOW: 0.1,
            RiskLevel.MEDIUM: 0.4,
            RiskLevel.HIGH: 0.7,
            RiskLevel.CRITICAL: 0.95,
        }
        
        max_risk = max(risk_values.get(s.risk_level, 0.5) for s in steps)
        avg_risk = sum(risk_values.get(s.risk_level, 0.5) for s in steps) / len(steps)
        
        # Weight towards max risk
        return 0.7 * max_risk + 0.3 * avg_risk
    
    def _find_highest_risk_step(self, steps: List[RemediationStep]) -> Optional[int]:
        """Find step number with highest risk."""
        if not steps:
            return None
        
        risk_order = [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW]
        for risk_level in risk_order:
            for step in steps:
                if step.risk_level == risk_level:
                    return step.step_number
        return None
    
    def _estimate_time(self, steps: List[RemediationStep]) -> str:
        """Estimate total remediation time."""
        # Simple estimation - would be more sophisticated in production
        if len(steps) <= 2:
            return "5-10 minutes"
        elif len(steps) <= 4:
            return "10-20 minutes"
        else:
            return "20-45 minutes"
    
    def _generate_summary(self, root_cause: RootCauseHypothesis, steps: List[RemediationStep]) -> str:
        """Generate remediation summary."""
        action_summary = ", ".join(s.action.lower() for s in steps[:2])
        return f"To address {root_cause.category.value} issue: {action_summary}"
    
    def _generate_explanation(self, root_cause: RootCauseHypothesis) -> str:
        """Generate detailed explanation."""
        return f"Based on the root cause analysis ({root_cause.hypothesis}), we recommend the following remediation steps. Each step has been reviewed for safety and includes rollback procedures where applicable."


class RemediationGuardrails:
    """
    Safety guardrails for remediation suggestions.
    
    Blocks dangerous commands and flags high-risk operations.
    """
    
    BLOCKED_PATTERNS = [
        "rm -rf",
        "DROP DATABASE",
        "DELETE FROM",
        "kubectl delete namespace",
        "terraform destroy",
        "> /dev/",
        "mkfs",
        "dd if=",
    ]
    
    HIGH_RISK_PATTERNS = [
        "kubectl delete",
        "kubectl scale.*replicas=0",
        "ALTER TABLE",
        "UPDATE.*SET",
        "TRUNCATE",
    ]
    
    def __init__(self):
        self.applied_guardrails = []
    
    def check_steps(self, steps: List[RemediationStep]) -> List[RemediationStep]:
        """Apply guardrails to remediation steps."""
        import re
        
        safe_steps = []
        
        for step in steps:
            if step.command:
                # Check blocked patterns
                is_blocked = False
                for pattern in self.BLOCKED_PATTERNS:
                    if pattern.lower() in step.command.lower():
                        self.applied_guardrails.append(f"blocked:{pattern}")
                        is_blocked = True
                        break
                
                if is_blocked:
                    continue  # Skip this step
                
                # Check high-risk patterns
                for pattern in self.HIGH_RISK_PATTERNS:
                    if re.search(pattern, step.command, re.IGNORECASE):
                        step.risk_level = RiskLevel.HIGH
                        step.requires_approval = True
                        self.applied_guardrails.append(f"flagged_high_risk:{pattern}")
            
            # Require rollback for high-risk steps
            if step.risk_level == RiskLevel.HIGH and not step.rollback_plan:
                step.requires_approval = True
                self.applied_guardrails.append("require_rollback_plan")
            
            safe_steps.append(step)
        
        return safe_steps
