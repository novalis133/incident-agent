# Deployment Rollback Runbook

## When to Rollback
- Error rate increase > 2x after deployment
- Latency increase > 3x after deployment
- New crash loops after deployment
- Customer-facing feature broken

## Pre-Rollback Checks
1. Confirm deployment is the cause (check timeline correlation)
2. Verify previous version is available
3. Check for database migrations that may not be backward-compatible
4. Notify team in incident channel

## Rollback Procedure
1. `kubectl rollout undo deployment/<service> -n <namespace>`
2. Monitor rollout: `kubectl rollout status deployment/<service> -n <namespace>`
3. Verify error rate returns to normal within 5 minutes
4. Verify latency returns to baseline

## Post-Rollback
1. Update incident timeline
2. Create hotfix branch from last known good version
3. Add regression test for the failure
4. Schedule post-mortem

## Risk Level
Low to Medium - Rollback is generally safe if no breaking DB migrations
