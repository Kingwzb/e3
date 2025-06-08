"""Database tools using LangChain's tool system for better configurability."""

import asyncio
import time
from typing import Dict, Any, List, Optional, Type
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from app.core.database import MetricsData, ConversationHistory, get_db
from app.models.state import MetricsResult
from app.utils.logging import logger


# Pydantic models for tool inputs
class GetMetricsByCategoryInput(BaseModel):
    """Input for get_metrics_by_category tool."""
    category: str = Field(
        description="The metrics category to filter by. Available categories: engagement, revenue, performance, satisfaction"
    )
    days_back: int = Field(
        default=7,
        description="Number of days to look back from today (1-90 days)",
        ge=1,
        le=90
    )


class GetTopMetricsInput(BaseModel):
    """Input for get_top_metrics tool."""
    metric_name: str = Field(
        description="The specific metric name to query. Examples: daily_active_users, monthly_revenue, response_time"
    )
    limit: int = Field(
        default=10,
        description="Number of top results to return (1-50)",
        ge=1,
        le=50
    )


class ExecuteCustomQueryInput(BaseModel):
    """Input for execute_custom_query tool."""
    sql_query: str = Field(
        description="SQL SELECT query to execute. Only SELECT statements allowed. Available tables: metrics_data (columns: metric_name, metric_value, timestamp, category, meta_data)"
    )


# Tool configuration class
class DatabaseToolsConfig:
    """Configuration for database tools."""
    
    def __init__(
        self,
        max_days_back: int = 90,
        max_limit: int = 50,
        allowed_categories: List[str] = None,
        allowed_metric_names: List[str] = None,
        enable_custom_queries: bool = True
    ):
        self.max_days_back = max_days_back
        self.max_limit = max_limit
        self.allowed_categories = allowed_categories or [
            "engagement", "revenue", "performance", "satisfaction"
        ]
        self.allowed_metric_names = allowed_metric_names or [
            "daily_active_users", "session_duration", "page_views",
            "monthly_revenue", "conversion_rate", "customer_lifetime_value",
            "response_time", "uptime_percentage", "error_rate",
            "nps_score", "support_rating", "churn_rate"
        ]
        self.enable_custom_queries = enable_custom_queries


# LangChain Tools
class GetMetricsByCategoryTool(BaseTool):
    """Tool to get metrics data by category."""
    
    name: str = "get_metrics_by_category"
    description: str = "Get metrics data by category for the last N days. Useful for analyzing trends in specific metric categories."
    args_schema: Type[BaseModel] = GetMetricsByCategoryInput
    db_session: AsyncSession = None
    config: DatabaseToolsConfig = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, db_session: AsyncSession, config: DatabaseToolsConfig = None, **kwargs):
        super().__init__(**kwargs)
        self.db_session = db_session
        self.config = config or DatabaseToolsConfig()
        
        # Update description with available categories
        self.description = f"Get metrics data by category for the last N days. Available categories: {', '.join(self.config.allowed_categories)}"
    
    async def _arun(self, category: str, days_back: int = 7) -> str:
        """Execute the tool asynchronously."""
        start_time = time.time()
        
        try:
            # Validate category
            if category not in self.config.allowed_categories:
                return f"Error: Invalid category '{category}'. Available categories: {', '.join(self.config.allowed_categories)}"
            
            # Validate days_back
            if days_back > self.config.max_days_back:
                days_back = self.config.max_days_back
            
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Build query
            query = select(MetricsData).where(
                MetricsData.category == category,
                MetricsData.timestamp >= start_date,
                MetricsData.timestamp <= end_date
            ).order_by(MetricsData.timestamp.desc())
            
            result = await self.db_session.execute(query)
            metrics = result.scalars().all()
            
            # Process results
            data = {
                "category": category,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "metrics": [
                    {
                        "name": metric.metric_name,
                        "value": metric.metric_value,
                        "timestamp": metric.timestamp.isoformat(),
                        "metadata": metric.meta_data
                    }
                    for metric in metrics
                ],
                "summary": {
                    "total_records": len(metrics),
                    "avg_value": sum(m.metric_value for m in metrics) / len(metrics) if metrics else 0,
                    "max_value": max(m.metric_value for m in metrics) if metrics else 0,
                    "min_value": min(m.metric_value for m in metrics) if metrics else 0
                }
            }
            
            execution_time = time.time() - start_time
            logger.info(f"Retrieved {len(metrics)} metrics for category '{category}' in {execution_time:.2f}s")
            
            return f"Successfully retrieved {len(metrics)} metrics for category '{category}'. Data: {data}"
            
        except Exception as e:
            logger.error(f"Error getting metrics by category: {str(e)}")
            return f"Error retrieving metrics: {str(e)}"
    
    def _run(self, category: str, days_back: int = 7) -> str:
        """Synchronous version (not recommended for async operations)."""
        return "This tool requires async execution. Use _arun instead."


class GetTopMetricsTool(BaseTool):
    """Tool to get top metrics by value."""
    
    name: str = "get_top_metrics"
    description: str = "Get top N metrics by value for a specific metric name. Useful for finding highest performing metrics."
    args_schema: Type[BaseModel] = GetTopMetricsInput
    db_session: AsyncSession = None
    config: DatabaseToolsConfig = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, db_session: AsyncSession, config: DatabaseToolsConfig = None, **kwargs):
        super().__init__(**kwargs)
        self.db_session = db_session
        self.config = config or DatabaseToolsConfig()
        
        # Update description with available metrics
        self.description = f"Get top N metrics by value. Available metric names: {', '.join(self.config.allowed_metric_names[:5])}... (and more)"
    
    async def _arun(self, metric_name: str, limit: int = 10) -> str:
        """Execute the tool asynchronously."""
        start_time = time.time()
        
        try:
            # Validate limit
            if limit > self.config.max_limit:
                limit = self.config.max_limit
            
            query = select(MetricsData).where(
                MetricsData.metric_name == metric_name
            ).order_by(MetricsData.metric_value.desc()).limit(limit)
            
            result = await self.db_session.execute(query)
            metrics = result.scalars().all()
            
            if not metrics:
                return f"No metrics found for metric name '{metric_name}'. Available metrics: {', '.join(self.config.allowed_metric_names[:10])}"
            
            data = {
                "metric_name": metric_name,
                "top_values": [
                    {
                        "value": metric.metric_value,
                        "timestamp": metric.timestamp.isoformat(),
                        "category": metric.category,
                        "metadata": metric.meta_data
                    }
                    for metric in metrics
                ],
                "summary": {
                    "total_records": len(metrics),
                    "highest_value": metrics[0].metric_value if metrics else 0,
                    "lowest_in_top": metrics[-1].metric_value if metrics else 0
                }
            }
            
            execution_time = time.time() - start_time
            logger.info(f"Retrieved top {len(metrics)} metrics for '{metric_name}' in {execution_time:.2f}s")
            
            return f"Successfully retrieved top {len(metrics)} values for '{metric_name}'. Data: {data}"
            
        except Exception as e:
            logger.error(f"Error getting top metrics: {str(e)}")
            return f"Error retrieving top metrics: {str(e)}"
    
    def _run(self, metric_name: str, limit: int = 10) -> str:
        """Synchronous version (not recommended for async operations)."""
        return "This tool requires async execution. Use _arun instead."


class ExecuteCustomQueryTool(BaseTool):
    """Tool to execute custom SQL queries."""
    
    name: str = "execute_custom_query"
    description: str = "Execute a custom SQL SELECT query on the metrics database. Only SELECT statements allowed for security."
    args_schema: Type[BaseModel] = ExecuteCustomQueryInput
    db_session: AsyncSession = None
    config: DatabaseToolsConfig = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, db_session: AsyncSession, config: DatabaseToolsConfig = None, **kwargs):
        super().__init__(**kwargs)
        self.db_session = db_session
        self.config = config or DatabaseToolsConfig()
        
        if not self.config.enable_custom_queries:
            self.description = "Custom queries are disabled in this configuration."
    
    async def _arun(self, sql_query: str) -> str:
        """Execute the tool asynchronously."""
        if not self.config.enable_custom_queries:
            return "Error: Custom queries are disabled in this configuration."
        
        start_time = time.time()
        
        try:
            # Safety check - only allow SELECT statements
            query_upper = sql_query.upper().strip()
            if not query_upper.startswith('SELECT'):
                return "Error: Only SELECT statements are allowed"
            
            # Prevent dangerous operations
            dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
            if any(keyword in query_upper for keyword in dangerous_keywords):
                return f"Error: Query contains prohibited keywords: {dangerous_keywords}"
            
            result = await self.db_session.execute(text(sql_query))
            rows = result.fetchall()
            columns = result.keys()
            
            data = {
                "query": sql_query,
                "columns": list(columns),
                "rows": [dict(zip(columns, row)) for row in rows[:100]],  # Limit to 100 rows
                "row_count": len(rows),
                "limited": len(rows) > 100
            }
            
            execution_time = time.time() - start_time
            logger.info(f"Executed custom query returning {len(rows)} rows in {execution_time:.2f}s")
            
            return f"Query executed successfully. Returned {len(rows)} rows. Data: {data}"
            
        except Exception as e:
            logger.error(f"Error executing custom query: {str(e)}")
            return f"Error executing query: {str(e)}"
    
    def _run(self, sql_query: str) -> str:
        """Synchronous version (not recommended for async operations)."""
        return "This tool requires async execution. Use _arun instead."


# Factory functions
def create_langchain_db_tools(
    db_session: AsyncSession, 
    config: DatabaseToolsConfig = None
) -> List[BaseTool]:
    """Create LangChain database tools with configuration."""
    config = config or DatabaseToolsConfig()
    
    tools = [
        GetMetricsByCategoryTool(db_session, config),
        GetTopMetricsTool(db_session, config),
    ]
    
    if config.enable_custom_queries:
        tools.append(ExecuteCustomQueryTool(db_session, config))
    
    return tools


def create_tool_config_for_environment(environment: str = "production") -> DatabaseToolsConfig:
    """Create tool configuration based on environment."""
    if environment == "development":
        return DatabaseToolsConfig(
            max_days_back=30,
            max_limit=20,
            enable_custom_queries=True
        )
    elif environment == "testing":
        return DatabaseToolsConfig(
            max_days_back=7,
            max_limit=10,
            enable_custom_queries=False
        )
    elif environment == "production":
        return DatabaseToolsConfig(
            max_days_back=90,
            max_limit=50,
            enable_custom_queries=False  # Disable for security
        )
    else:
        return DatabaseToolsConfig()  # Default configuration 