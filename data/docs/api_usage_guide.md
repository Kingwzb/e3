# Productivity Insights API Usage Guide

## Overview

The Productivity Insights API provides programmatic access to all system functionality, including data ingestion, querying, and analytics. This guide covers the most commonly used endpoints and provides examples for integration.

## Authentication

All API requests require authentication using API keys:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     https://api.productivityinsights.com/v1/metrics
```

## Core Endpoints

### 1. Metrics Data Endpoints

#### GET /api/v1/metrics
Retrieve metrics data with filtering options.

**Query Parameters:**
- `category`: Filter by metric category (engagement, performance, revenue, satisfaction)
- `metric_name`: Filter by specific metric name
- `start_date`: Start date for time range (ISO 8601 format)
- `end_date`: End date for time range (ISO 8601 format)
- `limit`: Maximum number of results (default: 100, max: 1000)
- `offset`: Pagination offset

**Example Request:**
```bash
curl "https://api.productivityinsights.com/v1/metrics?category=engagement&start_date=2024-06-01&limit=50" \
     -H "Authorization: Bearer YOUR_API_KEY"
```

**Example Response:**
```json
{
  "data": [
    {
      "id": 1234,
      "metric_name": "daily_active_users",
      "metric_value": 1250.0,
      "timestamp": "2024-06-07T14:30:00Z",
      "category": "engagement",
      "meta_data": {
        "department": "product",
        "region": "us-west"
      }
    }
  ],
  "pagination": {
    "total": 500,
    "limit": 50,
    "offset": 0,
    "has_more": true
  }
}
```

#### POST /api/v1/metrics
Submit new metrics data to the system.

**Request Body:**
```json
{
  "metrics": [
    {
      "metric_name": "daily_active_users",
      "metric_value": 1250.0,
      "category": "engagement",
      "meta_data": {
        "department": "product",
        "region": "us-west"
      }
    }
  ]
}
```

### 2. Analytics Endpoints

#### GET /api/v1/analytics/summary
Get aggregated metrics summary for a time period.

**Query Parameters:**
- `period`: Time period (day, week, month, quarter, year)
- `category`: Metric category to summarize
- `group_by`: Group results by meta_data field

**Example Request:**
```bash
curl "https://api.productivityinsights.com/v1/analytics/summary?period=week&category=performance" \
     -H "Authorization: Bearer YOUR_API_KEY"
```

#### GET /api/v1/analytics/trends
Analyze trends and patterns in metrics data.

**Query Parameters:**
- `metric_name`: Specific metric to analyze
- `period`: Analysis period
- `trend_type`: Type of trend analysis (linear, seasonal, anomaly)

### 3. Dashboard Endpoints

#### GET /api/v1/dashboards
List available dashboards and their configurations.

#### GET /api/v1/dashboards/{dashboard_id}/data
Get data for a specific dashboard widget.

## Data Ingestion Patterns

### Real-time Ingestion
For high-frequency metrics, use the streaming endpoint:

```bash
curl -X POST "https://api.productivityinsights.com/v1/metrics/stream" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "metric_name": "response_time",
       "metric_value": 125.5,
       "category": "performance",
       "timestamp": "2024-06-07T14:30:00Z"
     }'
```

### Batch Ingestion
For bulk data uploads, use the batch endpoint:

```bash
curl -X POST "https://api.productivityinsights.com/v1/metrics/batch" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d @metrics_batch.json
```

## Error Handling

The API uses standard HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Invalid or missing API key
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

**Error Response Format:**
```json
{
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "The 'category' parameter must be one of: engagement, performance, revenue, satisfaction",
    "details": {
      "parameter": "category",
      "provided_value": "invalid_category"
    }
  }
}
```

## Rate Limits

- **Standard tier**: 1,000 requests per hour
- **Premium tier**: 10,000 requests per hour
- **Enterprise tier**: 100,000 requests per hour

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1623456789
```

## SDKs and Libraries

Official SDKs are available for:
- Python: `pip install productivity-insights-sdk`
- JavaScript/Node.js: `npm install productivity-insights-sdk`
- Java: Maven/Gradle dependency available
- Go: `go get github.com/productivity-insights/go-sdk`

### Python SDK Example
```python
from productivity_insights import Client

client = Client(api_key="YOUR_API_KEY")

# Get engagement metrics
metrics = client.metrics.list(
    category="engagement",
    start_date="2024-06-01",
    limit=100
)

# Submit new metric
client.metrics.create(
    metric_name="daily_active_users",
    metric_value=1250.0,
    category="engagement",
    meta_data={"department": "product"}
)
```

## Webhooks

Configure webhooks to receive real-time notifications:

### Webhook Events
- `metric.created`: New metric data received
- `alert.triggered`: Alert threshold exceeded
- `dashboard.updated`: Dashboard configuration changed

### Webhook Configuration
```json
{
  "url": "https://your-app.com/webhooks/productivity-insights",
  "events": ["metric.created", "alert.triggered"],
  "secret": "your_webhook_secret"
}
``` 