"""Database adapters for different storage backends."""

# Write-capable adapters (for read-write operations)
from .sqlite_adapter import SQLiteMetricsAdapter
from .mongodb_ee_productivities_adapter import MongoDBEEProductivitiesAdapter

# Read-only query adapters (optimized for querying)
from .sqlite_query_adapter import SQLiteQueryAdapter
from .postgresql_query_adapter import PostgreSQLQueryAdapter
from .mongodb_ee_productivities_query_adapter import MongoDBEEProductivitiesQueryAdapter

# For backward compatibility, alias the ee-productivities adapter as the general MongoDB adapter
MongoDBMetricsAdapter = MongoDBEEProductivitiesAdapter
MongoDBQueryAdapter = MongoDBEEProductivitiesQueryAdapter 