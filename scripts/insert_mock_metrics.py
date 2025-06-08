#!/usr/bin/env python3
"""
Insert mock metrics data for testing the metrics node logic.

This script generates realistic mock data across all metric categories
to test the metrics extraction tools and LLM integration.
"""

import sys
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import random
import json

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_db, MetricsData, AsyncSessionLocal
from app.utils.logging import logger
from sqlalchemy import text


class MockMetricsGenerator:
    """Generate realistic mock metrics data for testing."""
    
    def __init__(self):
        self.departments = ["engineering", "product", "sales", "marketing", "customer_success", "hr"]
        self.regions = ["us-west", "us-east", "europe", "asia-pacific", "canada"]
        self.products = ["enterprise", "professional", "starter", "mobile_app"]
        self.teams = ["backend", "frontend", "data", "platform", "security", "qa"]
        
    def generate_engagement_metrics(self, base_date: datetime) -> list:
        """Generate engagement metrics data."""
        metrics = []
        
        for i in range(30):  # 30 days of data
            date = base_date - timedelta(days=i)
            
            # Daily active users with trend
            base_dau = 15000 + (i * 50) + random.randint(-500, 500)
            metrics.append({
                "metric_name": "daily_active_users",
                "metric_value": float(base_dau),
                "timestamp": date,
                "category": "engagement",
                "meta_data": {
                    "department": "product",
                    "region": "global",
                    "measurement_type": "daily"
                }
            })
            
            # Session duration
            session_duration = 45.0 + random.uniform(-10, 15)
            metrics.append({
                "metric_name": "session_duration",
                "metric_value": session_duration,
                "timestamp": date,
                "category": "engagement", 
                "meta_data": {
                    "department": "product",
                    "unit": "minutes",
                    "platform": "web"
                }
            })
            
            # Feature usage rate
            for feature in ["dashboard", "reports", "analytics", "export"]:
                usage_rate = random.uniform(0.3, 0.8)
                metrics.append({
                    "metric_name": "feature_usage_rate",
                    "metric_value": usage_rate,
                    "timestamp": date,
                    "category": "engagement",
                    "meta_data": {
                        "feature": feature,
                        "department": "product",
                        "measurement_type": "daily"
                    }
                })
        
        return metrics
    
    def generate_performance_metrics(self, base_date: datetime) -> list:
        """Generate performance metrics data."""
        metrics = []
        
        for i in range(30):
            date = base_date - timedelta(days=i)
            
            # Response time
            response_time = 150.0 + random.uniform(-50, 100)
            metrics.append({
                "metric_name": "response_time",
                "metric_value": response_time,
                "timestamp": date,
                "category": "performance",
                "meta_data": {
                    "service": "api_gateway",
                    "environment": "production",
                    "team": random.choice(self.teams),
                    "unit": "milliseconds"
                }
            })
            
            # Uptime percentage
            uptime = random.uniform(99.5, 99.99)
            metrics.append({
                "metric_name": "uptime_percentage",
                "metric_value": uptime,
                "timestamp": date,
                "category": "performance",
                "meta_data": {
                    "service": "main_application",
                    "environment": "production",
                    "team": "platform"
                }
            })
            
            # Error rate
            error_rate = random.uniform(0.001, 0.05)
            metrics.append({
                "metric_name": "error_rate",
                "metric_value": error_rate,
                "timestamp": date,
                "category": "performance",
                "meta_data": {
                    "service": "user_service",
                    "environment": "production",
                    "team": "backend"
                }
            })
            
            # Task completion rate
            completion_rate = random.uniform(0.85, 0.98)
            metrics.append({
                "metric_name": "task_completion_rate",
                "metric_value": completion_rate,
                "timestamp": date,
                "category": "performance",
                "meta_data": {
                    "department": random.choice(self.departments),
                    "team": random.choice(self.teams),
                    "measurement_type": "daily"
                }
            })
    
        return metrics
    
    def generate_revenue_metrics(self, base_date: datetime) -> list:
        """Generate revenue metrics data."""
        metrics = []
        
        for i in range(30):
            date = base_date - timedelta(days=i)
            
            # Daily revenue
            daily_revenue = 50000 + random.uniform(-5000, 10000)
            metrics.append({
                "metric_name": "daily_revenue",
                "metric_value": daily_revenue,
                "timestamp": date,
                "category": "revenue",
                "meta_data": {
                    "department": "sales",
                    "region": "global",
                    "currency": "USD"
                }
            })
            
            # Conversion rate by region
            for region in self.regions:
                conversion_rate = random.uniform(0.02, 0.08)
                metrics.append({
                    "metric_name": "conversion_rate",
                    "metric_value": conversion_rate,
                    "timestamp": date,
                    "category": "revenue",
                    "meta_data": {
                        "region": region,
                        "department": "sales",
                        "channel": "direct_sales"
                    }
                })
            
            # Customer lifetime value
            for product in self.products:
                clv = random.uniform(1200, 5000)
                metrics.append({
                    "metric_name": "customer_lifetime_value",
                    "metric_value": clv,
                    "timestamp": date,
                    "category": "revenue",
                    "meta_data": {
                        "product_line": product,
                        "department": "sales",
                        "currency": "USD"
                    }
                })
        
        return metrics
    
    def generate_satisfaction_metrics(self, base_date: datetime) -> list:
        """Generate satisfaction metrics data."""
        metrics = []
        
        for i in range(30):
            date = base_date - timedelta(days=i)
            
            # Net Promoter Score
            nps_score = random.uniform(30, 70)
            metrics.append({
                "metric_name": "nps_score",
                "metric_value": nps_score,
                "timestamp": date,
                "category": "satisfaction",
                "meta_data": {
                    "survey_type": "monthly",
                    "department": "customer_success",
                    "respondent_count": random.randint(100, 500)
                }
            })
            
            # Customer satisfaction by product
            for product in self.products:
                csat = random.uniform(3.5, 4.8)
                metrics.append({
                    "metric_name": "customer_satisfaction",
                    "metric_value": csat,
                    "timestamp": date,
                    "category": "satisfaction",
                    "meta_data": {
                        "product_line": product,
                        "department": "customer_success",
                        "scale": "1-5",
                        "respondent_count": random.randint(50, 200)
                    }
                })
            
            # Support rating
            support_rating = random.uniform(4.0, 4.9)
            metrics.append({
                "metric_name": "support_rating",
                "metric_value": support_rating,
                "timestamp": date,
                "category": "satisfaction",
                "meta_data": {
                    "department": "customer_success",
                    "channel": "email_support",
                    "scale": "1-5"
                }
            })
            
            # Employee satisfaction
            emp_satisfaction = random.uniform(3.8, 4.5)
            metrics.append({
                "metric_name": "employee_satisfaction",
                "metric_value": emp_satisfaction,
                "timestamp": date,
                "category": "satisfaction",
                "meta_data": {
                    "department": "hr",
                    "survey_type": "weekly",
                    "scale": "1-5"
                }
            })
        
        return metrics
    
    def generate_all_metrics(self) -> list:
        """Generate all categories of mock metrics."""
        base_date = datetime.now()
        
        all_metrics = []
        all_metrics.extend(self.generate_engagement_metrics(base_date))
        all_metrics.extend(self.generate_performance_metrics(base_date))
        all_metrics.extend(self.generate_revenue_metrics(base_date))
        all_metrics.extend(self.generate_satisfaction_metrics(base_date))
        
        logger.info(f"Generated {len(all_metrics)} mock metrics")
        return all_metrics


async def insert_mock_metrics():
    """Insert mock metrics data into the database."""
    logger.info("Starting mock metrics data insertion...")
    
    generator = MockMetricsGenerator()
    metrics_data = generator.generate_all_metrics()
    
    async with AsyncSessionLocal() as session:
        try:
            # Clear existing metrics (optional)
            logger.info("Clearing existing metrics data...")
            await session.execute(text("DELETE FROM metrics_data"))
            await session.commit()
            
            # Insert new mock data
            logger.info(f"Inserting {len(metrics_data)} mock metrics...")
            
            for metric_data in metrics_data:
                metric = MetricsData(
                    metric_name=metric_data["metric_name"],
                    metric_value=metric_data["metric_value"],
                    timestamp=metric_data["timestamp"],
                    category=metric_data["category"],
                    meta_data=json.dumps(metric_data["meta_data"])
                )
                session.add(metric)
            
            await session.commit()
            logger.info("Mock metrics data inserted successfully!")
            
            # Show summary
            result = await session.execute(text("""
                SELECT category, COUNT(*) as count, 
                       MIN(timestamp) as earliest, 
                       MAX(timestamp) as latest
                FROM metrics_data 
                GROUP BY category
                ORDER BY category
            """))
            
            logger.info("Inserted metrics summary:")
            for row in result.fetchall():
                logger.info(f"  {row[0]}: {row[1]} records ({row[2]} to {row[3]})")
                
        except Exception as e:
            logger.error(f"Error inserting mock metrics: {e}")
            await session.rollback()
            raise


async def main():
    """Main function."""
    try:
        await insert_mock_metrics()
        logger.info("Mock metrics insertion completed successfully!")
    except Exception as e:
        logger.error(f"Mock metrics insertion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 