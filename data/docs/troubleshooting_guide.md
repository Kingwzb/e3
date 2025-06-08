# Productivity Insights Troubleshooting Guide

## Common Issues and Solutions

### Data Collection Issues

#### Problem: Metrics not appearing in dashboard
**Symptoms:**
- Recent metrics data is missing from dashboards
- API returns empty results for recent time periods
- Data ingestion appears successful but no data visible

**Possible Causes:**
1. **Timezone mismatch**: Data ingested with incorrect timezone
2. **Category mismatch**: Metrics stored with wrong category name
3. **Caching issues**: Dashboard cache not refreshed
4. **Permission issues**: User lacks access to specific metric categories

**Solutions:**
1. **Check timezone settings**:
   ```sql
   SELECT metric_name, timestamp, 
          CONVERT_TZ(timestamp, '+00:00', 'SYSTEM') as local_time
   FROM metrics_data 
   WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
   ORDER BY timestamp DESC;
   ```

2. **Verify category names**:
   ```sql
   SELECT DISTINCT category, COUNT(*) as count
   FROM metrics_data 
   WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
   GROUP BY category;
   ```

3. **Clear dashboard cache**:
   ```bash
   curl -X POST "https://api.productivityinsights.com/v1/cache/clear" \
        -H "Authorization: Bearer YOUR_API_KEY"
   ```

#### Problem: Duplicate metrics data
**Symptoms:**
- Same metric appears multiple times for the same timestamp
- Aggregated values are higher than expected
- Data inconsistencies in reports

**Possible Causes:**
1. **Multiple data sources**: Same metric ingested from different systems
2. **Retry logic**: Failed requests being retried and succeeding multiple times
3. **Clock synchronization**: Multiple servers with slightly different times

**Solutions:**
1. **Identify duplicates**:
   ```sql
   SELECT metric_name, timestamp, category, COUNT(*) as duplicate_count
   FROM metrics_data 
   GROUP BY metric_name, timestamp, category
   HAVING COUNT(*) > 1
   ORDER BY duplicate_count DESC;
   ```

2. **Implement deduplication**:
   ```sql
   DELETE m1 FROM metrics_data m1
   INNER JOIN metrics_data m2 
   WHERE m1.id > m2.id 
     AND m1.metric_name = m2.metric_name 
     AND m1.timestamp = m2.timestamp 
     AND m1.category = m2.category;
   ```

### Performance Issues

#### Problem: Slow query performance
**Symptoms:**
- Dashboard takes long time to load
- API requests timeout
- Database CPU usage is high

**Possible Causes:**
1. **Missing indexes**: Queries scanning full table
2. **Large time ranges**: Querying too much historical data
3. **Complex aggregations**: Heavy computational queries
4. **Concurrent access**: Too many simultaneous queries

**Solutions:**
1. **Add database indexes**:
   ```sql
   CREATE INDEX idx_metrics_category_timestamp 
   ON metrics_data(category, timestamp);
   
   CREATE INDEX idx_metrics_name_timestamp 
   ON metrics_data(metric_name, timestamp);
   
   CREATE INDEX idx_conversation_id_timestamp 
   ON conversation_history(conversation_id, timestamp);
   ```

2. **Optimize queries with LIMIT**:
   ```sql
   -- Instead of this:
   SELECT * FROM metrics_data WHERE category = 'engagement';
   
   -- Use this:
   SELECT * FROM metrics_data 
   WHERE category = 'engagement' 
     AND timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
   ORDER BY timestamp DESC 
   LIMIT 1000;
   ```

3. **Use pagination for large datasets**:
   ```python
   # Python SDK example
   page_size = 100
   offset = 0
   all_metrics = []
   
   while True:
       metrics = client.metrics.list(
           category="engagement",
           limit=page_size,
           offset=offset
       )
       if not metrics.data:
           break
       all_metrics.extend(metrics.data)
       offset += page_size
   ```

### API Issues

#### Problem: Authentication failures
**Symptoms:**
- 401 Unauthorized responses
- "Invalid API key" errors
- Intermittent authentication issues

**Possible Causes:**
1. **Expired API key**: Key has reached expiration date
2. **Incorrect key format**: Key not properly formatted in request
3. **Rate limiting**: Too many requests causing temporary blocks
4. **Permission changes**: API key permissions have been modified

**Solutions:**
1. **Verify API key format**:
   ```bash
   # Correct format
   curl -H "Authorization: Bearer pi_live_1234567890abcdef" \
        https://api.productivityinsights.com/v1/metrics
   
   # Check key status
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        https://api.productivityinsights.com/v1/auth/verify
   ```

2. **Check rate limits**:
   ```bash
   curl -I https://api.productivityinsights.com/v1/metrics \
        -H "Authorization: Bearer YOUR_API_KEY"
   # Look for X-RateLimit-* headers
   ```

3. **Regenerate API key** if expired or compromised

#### Problem: Data validation errors
**Symptoms:**
- 400 Bad Request responses
- "Invalid metric value" errors
- Data not being accepted by API

**Common validation rules:**
1. **Metric names**: Must be alphanumeric with underscores only
2. **Categories**: Must be one of: engagement, performance, revenue, satisfaction
3. **Metric values**: Must be numeric (integer or decimal)
4. **Timestamps**: Must be valid ISO 8601 format
5. **Meta data**: Must be valid JSON object

**Example validation fixes**:
```json
// ❌ Invalid
{
  "metric_name": "daily-active-users",  // hyphens not allowed
  "metric_value": "1250",              // string instead of number
  "category": "user_engagement",       // invalid category
  "timestamp": "2024-06-07 14:30:00"   // wrong timestamp format
}

// ✅ Valid
{
  "metric_name": "daily_active_users",
  "metric_value": 1250.0,
  "category": "engagement",
  "timestamp": "2024-06-07T14:30:00Z",
  "meta_data": {
    "department": "product"
  }
}
```

### AI Assistant Issues

#### Problem: Assistant not understanding queries
**Symptoms:**
- Generic responses to specific questions
- "I don't understand" messages
- Incorrect metric data returned

**Possible Causes:**
1. **Ambiguous queries**: User requests are too vague
2. **Missing context**: Insufficient conversation history
3. **Outdated training**: AI model needs updates
4. **RAG data issues**: Documentation not properly indexed

**Solutions:**
1. **Improve query specificity**:
   ```
   ❌ Vague: "Show me some data"
   ✅ Specific: "Show me daily active users for the last 7 days"
   
   ❌ Ambiguous: "How are we doing?"
   ✅ Clear: "What's our customer satisfaction score this month?"
   ```

2. **Provide context in queries**:
   ```
   ❌ No context: "Compare to last time"
   ✅ With context: "Compare this month's revenue to last month"
   ```

3. **Update RAG documentation**:
   ```bash
   python scripts/update_vector_db.py --rebuild
   ```

#### Problem: Slow assistant responses
**Symptoms:**
- Long delays before receiving responses
- Timeout errors in chat interface
- Partial responses being cut off

**Possible Causes:**
1. **Large context window**: Too much conversation history
2. **Complex queries**: Requiring multiple database operations
3. **RAG retrieval issues**: Vector search taking too long
4. **LLM API limits**: Rate limiting from OpenAI/other providers

**Solutions:**
1. **Optimize conversation history**:
   ```python
   # Limit context to recent messages
   conversation_history_limit = 10  # Instead of 50
   ```

2. **Implement streaming responses**:
   ```javascript
   // Frontend implementation
   const response = await fetch('/api/chat', {
     method: 'POST',
     headers: { 'Accept': 'text/event-stream' },
     body: JSON.stringify({ message: userMessage })
   });
   ```

### Monitoring and Alerts

#### Setting up health checks
```bash
# API health check
curl https://api.productivityinsights.com/health

# Database connectivity
curl https://api.productivityinsights.com/health/database

# AI assistant status
curl https://api.productivityinsights.com/health/assistant
```

#### Key metrics to monitor
1. **API response times**: Should be < 500ms for 95th percentile
2. **Database query performance**: Monitor slow query log
3. **Error rates**: Should be < 1% for all endpoints
4. **Data freshness**: Latest metrics should be < 1 hour old
5. **Assistant response quality**: Monitor user satisfaction ratings

#### Alert thresholds
- **Critical**: API down, database unreachable, error rate > 5%
- **Warning**: Response time > 1s, data delay > 2 hours, error rate > 2%
- **Info**: New data ingested, successful deployments, usage milestones 