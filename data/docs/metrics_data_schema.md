# Metrics Data Table Schema

## Table: metrics_data

The `metrics_data` table is the core table in Productivity Insights that stores all quantitative metrics collected from various systems and sources.

### Table Structure

| Column Name | Data Type | Description | Example Values |
|-------------|-----------|-------------|----------------|
| `id` | INTEGER | Primary key, auto-incrementing unique identifier | 1, 2, 3, ... |
| `metric_name` | VARCHAR(255) | Name of the specific metric being measured | "daily_active_users", "response_time", "conversion_rate" |
| `metric_value` | DECIMAL(10,2) | Numerical value of the metric | 1250.50, 0.85, 99.99 |
| `timestamp` | DATETIME | When the metric was recorded (UTC) | "2024-06-07 14:30:00" |
| `category` | VARCHAR(100) | High-level category grouping for the metric | "engagement", "performance", "revenue", "satisfaction" |
| `meta_data` | JSON | Additional contextual information about the metric | {"department": "engineering", "region": "us-west"} |

## Metric Categories

### 1. Engagement Metrics (`category = 'engagement'`)

Metrics related to user engagement and activity levels.

**Common metric_name values:**
- `daily_active_users`: Number of unique users active in a day
- `session_duration`: Average session length in minutes
- `page_views`: Total page views per day
- `feature_usage_rate`: Percentage of users using specific features
- `login_frequency`: Average logins per user per week

**Example meta_data:**
```json
{
  "department": "product",
  "feature": "dashboard",
  "user_segment": "power_users"
}
```

### 2. Performance Metrics (`category = 'performance'`)

Metrics related to system and employee performance.

**Common metric_name values:**
- `response_time`: Average API response time in milliseconds
- `uptime_percentage`: System uptime as a percentage
- `error_rate`: Error rate as a percentage
- `task_completion_rate`: Percentage of tasks completed on time
- `throughput`: Number of transactions processed per hour

**Example meta_data:**
```json
{
  "service": "api_gateway",
  "environment": "production",
  "team": "backend"
}
```

### 3. Revenue Metrics (`category = 'revenue'`)

Metrics related to financial performance and revenue generation.

**Common metric_name values:**
- `monthly_revenue`: Total revenue for the month
- `conversion_rate`: Percentage of leads converted to customers
- `customer_lifetime_value`: Average CLV in dollars
- `revenue_per_employee`: Monthly revenue divided by employee count
- `churn_rate`: Customer churn rate as a percentage

**Example meta_data:**
```json
{
  "product_line": "enterprise",
  "sales_region": "north_america",
  "channel": "direct_sales"
}
```

### 4. Satisfaction Metrics (`category = 'satisfaction'`)

Metrics related to customer and employee satisfaction.

**Common metric_name values:**
- `nps_score`: Net Promoter Score (-100 to 100)
- `support_rating`: Average support ticket rating (1-5)
- `employee_satisfaction`: Employee satisfaction score (1-10)
- `customer_satisfaction`: Customer satisfaction score (1-10)
- `retention_rate`: Employee or customer retention rate as percentage

**Example meta_data:**
```json
{
  "survey_type": "quarterly",
  "department": "customer_success",
  "respondent_count": 150
}
```

## Data Quality Guidelines

### Metric Value Ranges
- **Percentages**: Store as decimal values (0.0 to 1.0), not 0-100
- **Scores**: Use consistent scales (e.g., 1-5, 1-10, -100 to 100)
- **Monetary values**: Store in base currency units (dollars, not cents)
- **Time-based**: Use consistent units (seconds, minutes, hours)

### Timestamp Standards
- All timestamps are stored in UTC
- Use ISO 8601 format: YYYY-MM-DD HH:MM:SS
- Granularity depends on metric frequency (daily, hourly, real-time)

### Meta Data Best Practices
- Use consistent key names across similar metrics
- Include relevant context for filtering and grouping
- Avoid storing sensitive information
- Keep JSON structure flat when possible

## Common Queries

### Get latest engagement metrics
```sql
SELECT metric_name, metric_value, timestamp
FROM metrics_data 
WHERE category = 'engagement' 
  AND timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY timestamp DESC;
```

### Calculate average performance by team
```sql
SELECT 
  JSON_EXTRACT(meta_data, '$.team') as team,
  AVG(metric_value) as avg_performance
FROM metrics_data 
WHERE category = 'performance' 
  AND metric_name = 'task_completion_rate'
  AND timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY JSON_EXTRACT(meta_data, '$.team');
``` 