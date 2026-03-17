# High Latency Runbook

## Symptoms
- P99 latency > SLO threshold
- Increasing response times
- Possible timeout errors downstream

## Investigation Steps
1. Check service metrics: latency percentiles, request rate, error rate
2. Review recent deployments
3. Check database query performance
4. Analyze network latency between services
5. Review connection pool utilization

## Common Causes
- Database query regression (missing index, N+1 queries)
- Connection pool exhaustion
- Garbage collection pauses
- Network congestion
- Downstream dependency slowdown

## Remediation
1. **Immediate**: Scale up replicas if load-related
2. **Short-term**: Optimize slow queries, tune connection pools
3. **Long-term**: Implement caching, optimize architecture

## Risk Level
Medium - Latency affects user experience directly
