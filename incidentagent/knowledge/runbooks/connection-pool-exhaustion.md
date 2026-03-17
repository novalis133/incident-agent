# Connection Pool Exhaustion Runbook

## Alert
- High error rate
- Database connection errors
- NullPointerException in connection handling

## Symptoms
- Error rate spike > 5%
- Connection pool at 100% capacity
- Slow response times
- Database timeout errors

## Common Causes
1. Connection leak in application code
2. Long-running queries holding connections
3. Traffic spike exceeding pool capacity
4. Database performance issues

## Investigation Steps

### 1. Check Connection Pool Metrics
```bash
# Prometheus query
sum(hikaricp_connections_active{service="<SERVICE>"}) by (pod)
sum(hikaricp_connections_max{service="<SERVICE>"}) by (pod)
```

### 2. Check for Connection Leaks
```bash
# Look for connections not being released
kubectl logs deployment/<SERVICE> | grep -i "connection"
```

### 3. Check Database Performance
```sql
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '1 minute';
```

## Remediation

### Immediate
1. Scale up replicas to distribute load
   ```bash
   kubectl scale deployment/<SERVICE> --replicas=<N>
   ```

2. Restart affected pods
   ```bash
   kubectl rollout restart deployment/<SERVICE>
   ```

### Long-term
1. Fix connection leak in code
2. Implement connection pool monitoring
3. Set appropriate pool sizes
4. Add circuit breaker for database calls

## Prevention
- Monitor connection pool utilization
- Set alerts at 80% capacity
- Regular code reviews for connection handling
- Load testing before deployments
