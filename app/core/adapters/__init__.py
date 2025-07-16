"""Database adapters for different storage backends."""

# Write-capable adapters (for read-write operations)
from .sqlite_adapter import SQLiteMetricsAdapter
from .mongodb_adapter import MongoDBMetricsAdapter
from .mongodb_ee_productivities_adapter import MongoDBEEProductivitiesAdapter

# Read-only query adapters (optimized for querying)
from .sqlite_query_adapter import SQLiteQueryAdapter
from .postgresql_query_adapter import PostgreSQLQueryAdapter
from .mongodb_ee_productivities_query_adapter import MongoDBEEProductivitiesQueryAdapter

# MongoDB query adapter will use the same implementation as the write adapter
# since MongoDB handles both read and write operations efficiently
MongoDBQueryAdapter = MongoDBMetricsAdapter 