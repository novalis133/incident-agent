# OOM Kill Runbook

## Symptoms
- Pods restarting frequently with OOMKilled status
- Memory usage at 100% of limits
- Application becoming unresponsive before restart

## Investigation Steps
1. Check pod status: `kubectl get pods -n <namespace> --sort-by='.status.containerStatuses[0].restartCount'`
2. Check memory limits: `kubectl describe pod <pod> -n <namespace>`
3. Check memory usage: `kubectl top pods -n <namespace>`
4. Review heap dumps if available
5. Check for memory leaks in recent deployments

## Common Causes
- Memory leak in application code
- Insufficient memory limits set
- Large payload processing without streaming
- Cache not bounded

## Remediation
1. **Immediate**: Increase memory limits by 50%
2. **Short-term**: Identify and fix memory leak
3. **Long-term**: Implement memory profiling in CI/CD

## Risk Level
Medium - Scaling up is safe, root cause fix needed
