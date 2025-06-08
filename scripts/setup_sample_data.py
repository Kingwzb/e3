#!/usr/bin/env python3
"""Script to setup sample data for testing and demonstration."""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import random

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import create_tables, MetricsData, AsyncSessionLocal
from app.core.config import settings
from app.tools.vector_store import vector_store
from app.utils.logging import logger


async def setup_sample_metrics_data():
    """Setup sample metrics data in the database."""
    logger.info("Setting up sample metrics data...")
    
    async with AsyncSessionLocal() as session:
        # Sample metrics categories and names
        metrics_data = [
            # User engagement metrics
            {"category": "engagement", "name": "daily_active_users", "values": [15000, 16200, 15800, 17100, 16500]},
            {"category": "engagement", "name": "session_duration", "values": [45.2, 48.1, 42.7, 50.3, 47.8]},
            {"category": "engagement", "name": "page_views", "values": [125000, 132000, 128000, 140000, 135000]},
            
            # Revenue metrics
            {"category": "revenue", "name": "monthly_revenue", "values": [85000, 92000, 88000, 98000, 94000]},
            {"category": "revenue", "name": "conversion_rate", "values": [3.2, 3.8, 3.5, 4.1, 3.9]},
            {"category": "revenue", "name": "customer_lifetime_value", "values": [450, 478, 462, 495, 481]},
            
            # System performance metrics
            {"category": "performance", "name": "response_time", "values": [185, 172, 198, 165, 179]},
            {"category": "performance", "name": "uptime_percentage", "values": [99.9, 99.8, 99.9, 99.95, 99.87]},
            {"category": "performance", "name": "error_rate", "values": [0.8, 0.6, 0.9, 0.5, 0.7]},
            
            # Customer satisfaction metrics
            {"category": "satisfaction", "name": "nps_score", "values": [72, 75, 73, 78, 76]},
            {"category": "satisfaction", "name": "support_rating", "values": [4.6, 4.8, 4.7, 4.9, 4.8]},
            {"category": "satisfaction", "name": "churn_rate", "values": [2.1, 1.8, 2.3, 1.6, 1.9]},
        ]
        
        # Generate data for the last 30 days
        base_date = datetime.utcnow() - timedelta(days=30)
        
        for metric_info in metrics_data:
            category = metric_info["category"]
            name = metric_info["name"]
            values = metric_info["values"]
            
            # Create multiple data points over time
            for i in range(30):
                timestamp = base_date + timedelta(days=i)
                
                # Use predefined values with some random variation
                base_value = values[i % len(values)]
                # Add 10% random variation
                variation = random.uniform(0.9, 1.1)
                value = base_value * variation
                
                metric = MetricsData(
                    metric_name=name,
                    metric_value=value,
                    timestamp=timestamp,
                    category=category,
                    meta_data=f'{{"source": "sample_data", "day": {i}}}'
                )
                session.add(metric)
        
        await session.commit()
        logger.info("Sample metrics data created successfully")


async def setup_sample_vector_data():
    """Setup sample vector data for RAG."""
    logger.info("Setting up sample vector data...")
    
    # This will use the existing initialize_sample_documents function
    from app.tools.vector_store import initialize_sample_documents
    initialize_sample_documents()
    
    logger.info("Sample vector data setup completed")


async def main():
    """Main function to setup all sample data."""
    try:
        logger.info("Starting sample data setup...")
        
        # Create database tables
        logger.info(f"Database URL: {settings.database_url}")
        await create_tables()
        logger.info("Database tables created/verified")
        
        # Setup sample metrics data
        await setup_sample_metrics_data()
        
        # Setup sample vector data
        await setup_sample_vector_data()
        
        logger.info("Sample data setup completed successfully!")
        print("\nSample data has been created:")
        print("- Metrics data: 30 days of sample metrics across multiple categories")
        print("- Vector data: Sample documents for RAG functionality")
        print("\nYou can now start the application and test the chat endpoint.")
        
    except Exception as e:
        logger.error(f"Error setting up sample data: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        print(f"Error: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 