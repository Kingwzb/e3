"""Data migration utilities for transitioning from old database schema to new abstraction layer."""

import json
import asyncio
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, MetricsData
from app.core.database_abstraction import MetricTuple
from app.tools.metrics_db_tools import get_metrics_database, insert_metric_direct
from app.utils.logging import logger


async def migrate_legacy_metrics_to_abstraction() -> Dict[str, Any]:
    """Migrate data from the legacy MetricsData table to the new abstraction layer.
    
    This function reads data from the existing SQLAlchemy-based metrics_data table
    and inserts it into the new abstraction layer format.
    """
    migration_stats = {
        "total_records": 0,
        "migrated_records": 0,
        "failed_records": 0,
        "errors": []
    }
    
    try:
        # Get legacy database session
        async for session in get_db():
            # Query all existing metrics
            result = await session.execute(text("SELECT * FROM metrics_data ORDER BY timestamp"))
            legacy_records = result.fetchall()
            migration_stats["total_records"] = len(legacy_records)
            
            logger.info(f"Found {len(legacy_records)} legacy records to migrate")
            
            # Process each record
            for record in legacy_records:
                try:
                    # Convert legacy record to new format
                    # Legacy schema: id, metric_name, metric_value, timestamp, category, meta_data
                    attributes = {
                        "category": record[4],  # category
                        "metric_name": record[1],  # metric_name
                    }
                    
                    # Parse meta_data if it exists
                    if record[5]:  # meta_data
                        try:
                            meta_data = json.loads(record[5])
                            attributes.update(meta_data)
                        except json.JSONDecodeError:
                            # If meta_data is not valid JSON, store as string
                            attributes["meta_data"] = record[5]
                    
                    values = {
                        record[1]: record[2]  # metric_name: metric_value
                    }
                    
                    timestamp = record[3]  # timestamp
                    
                    # Create MetricTuple
                    metric = MetricTuple(
                        attributes=attributes,
                        values=values,
                        timestamp=timestamp
                    )
                    
                    # Insert into new abstraction layer
                    await insert_metric_direct(
                        attributes=attributes,
                        values=values,
                        timestamp=timestamp
                    )
                    
                    migration_stats["migrated_records"] += 1
                    
                    if migration_stats["migrated_records"] % 100 == 0:
                        logger.info(f"Migrated {migration_stats['migrated_records']} records...")
                
                except Exception as e:
                    migration_stats["failed_records"] += 1
                    error_msg = f"Failed to migrate record {record[0]}: {str(e)}"
                    migration_stats["errors"].append(error_msg)
                    logger.error(error_msg)
            
            break  # Exit the async generator
    
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        migration_stats["errors"].append(f"Migration failed: {str(e)}")
    
    logger.info(f"Migration completed. Migrated: {migration_stats['migrated_records']}, "
                f"Failed: {migration_stats['failed_records']}")
    
    return migration_stats


async def generate_sample_metrics_for_testing() -> Dict[str, Any]:
    """Generate sample metrics in the new format for testing purposes."""
    from datetime import timedelta
    import random
    
    logger.info("Generating sample metrics for testing...")
    
    # Sample categories and metrics
    categories = ["engagement", "revenue", "performance", "satisfaction"]
    regions = ["us-east", "us-west", "europe", "asia"]
    teams = ["frontend", "backend", "devops", "product"]
    
    metrics_config = {
        "engagement": {
            "daily_active_users": (1000, 5000),
            "session_duration": (30, 120),
            "page_views": (10000, 50000)
        },
        "revenue": {
            "daily_revenue": (5000, 20000),
            "conversion_rate": (0.02, 0.08),
            "customer_lifetime_value": (200, 1000)
        },
        "performance": {
            "response_time": (50, 300),
            "uptime_percentage": (99.0, 99.99),
            "error_rate": (0.001, 0.05)
        },
        "satisfaction": {
            "nps_score": (30, 80),
            "support_rating": (3.5, 5.0),
            "retention_rate": (0.85, 0.98)
        }
    }
    
    generated_count = 0
    errors = []
    
    # Generate metrics for the last 30 days
    base_date = datetime.utcnow()
    
    for day in range(30):
        day_date = base_date - timedelta(days=day)
        
        for category, metrics in metrics_config.items():
            for metric_name, (min_val, max_val) in metrics.items():
                for region in regions:
                    try:
                        # Generate attributes
                        attributes = {
                            "category": category,
                            "metric_name": metric_name,
                            "region": region,
                            "team": random.choice(teams),
                            "environment": "production"
                        }
                        
                        # Generate values with some variance
                        base_value = random.uniform(min_val, max_val)
                        values = {
                            metric_name: round(base_value, 2),
                            "sample_count": random.randint(50, 500),
                            "confidence": round(random.uniform(0.9, 0.99), 3)
                        }
                        
                        # Insert metric
                        await insert_metric_direct(
                            attributes=attributes,
                            values=values,
                            timestamp=day_date
                        )
                        
                        generated_count += 1
                        
                    except Exception as e:
                        error_msg = f"Failed to generate metric {metric_name}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
    
    stats = {
        "generated_records": generated_count,
        "errors": errors,
        "categories": len(categories),
        "regions": len(regions),
        "days": 30
    }
    
    logger.info(f"Generated {generated_count} sample metrics")
    return stats


async def verify_data_consistency() -> Dict[str, Any]:
    """Verify data consistency between legacy and new formats."""
    verification_stats = {
        "legacy_count": 0,
        "new_count": 0,
        "consistency_issues": []
    }
    
    try:
        # Count legacy records
        async for session in get_db():
            result = await session.execute(text("SELECT COUNT(*) FROM metrics_data"))
            verification_stats["legacy_count"] = result.scalar()
            break
        
        # Count new format records
        db = get_metrics_database()
        new_metrics = await db.query_metrics(
            filters={"limit": None}  # Get all records
        )
        verification_stats["new_count"] = len(new_metrics)
        
        # Check for consistency
        if verification_stats["legacy_count"] != verification_stats["new_count"]:
            verification_stats["consistency_issues"].append(
                f"Record count mismatch: Legacy={verification_stats['legacy_count']}, "
                f"New={verification_stats['new_count']}"
            )
        
    except Exception as e:
        error_msg = f"Verification failed: {str(e)}"
        verification_stats["consistency_issues"].append(error_msg)
        logger.error(error_msg)
    
    return verification_stats


async def cleanup_legacy_data() -> Dict[str, Any]:
    """Clean up legacy data after successful migration (use with caution)."""
    cleanup_stats = {
        "deleted_records": 0,
        "errors": []
    }
    
    try:
        async for session in get_db():
            # Count records before deletion
            result = await session.execute(text("SELECT COUNT(*) FROM metrics_data"))
            count_before = result.scalar()
            
            # Delete all legacy records
            result = await session.execute(text("DELETE FROM metrics_data"))
            await session.commit()
            
            cleanup_stats["deleted_records"] = count_before
            logger.info(f"Deleted {count_before} legacy records")
            break
    
    except Exception as e:
        error_msg = f"Cleanup failed: {str(e)}"
        cleanup_stats["errors"].append(error_msg)
        logger.error(error_msg)
    
    return cleanup_stats 