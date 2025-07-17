"""LLM tools for querying ee-productivities database collections."""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
import os

from app.core.database_abstraction import (
    get_mongodb_ee_productivities_query_config,
    MetricsQueryDatabase
)
from app.core.models.ee_productivities_models import (
    ApplicationSnapshotFilter, EmployeeRatioFilter, EmployeeTreeFilter,
    EnablerFilter, ManagementSegmentFilter, StatisticFilter,
    ApplicationSnapshotResult, EmployeeRatioResult, EmployeeTreeResult,
    EnablerResult, ManagementSegmentResult, StatisticResult,
    ApplicationSnapshot, EmployeeRatio, EmployeeTreeArchived,
    EnablerCSISnapshots, ManagementSegmentTree, Statistic
)
from app.utils.logging import logger


class QueryApplicationSnapshotsInput(BaseModel):
    """Input for querying application snapshots."""
    year: Optional[int] = Field(None, description="Filter by year")
    month: Optional[int] = Field(None, description="Filter by month")
    status: Optional[str] = Field(None, description="Filter by status (Active, Inactive, Retired)")
    sector: Optional[str] = Field(None, description="Filter by sector")
    criticality: Optional[str] = Field(None, description="Filter by criticality (High, Medium, Low)")
    type: Optional[str] = Field(None, description="Filter by application type")
    organization: Optional[str] = Field(None, description="Filter by organization")
    isRetired: Optional[bool] = Field(None, description="Filter by retirement status")
    developmentModel: Optional[str] = Field(None, description="Filter by development model")
    hostingModel: Optional[str] = Field(None, description="Filter by hosting model")
    limit: Optional[int] = Field(100, description="Maximum number of results")


class QueryEmployeeRatiosInput(BaseModel):
    """Input for querying employee ratios."""
    soeId: Optional[str] = Field(None, description="Filter by SOE ID")
    year: Optional[int] = Field(None, description="Filter by year")
    month: Optional[int] = Field(None, description="Filter by month")
    limit: Optional[int] = Field(100, description="Maximum number of results")


class QueryEmployeeTreesInput(BaseModel):
    """Input for querying employee trees."""
    soeId: Optional[str] = Field(None, description="Filter by SOE ID")
    year: Optional[int] = Field(None, description="Filter by year")
    month: Optional[int] = Field(None, description="Filter by month")
    hierarchy: Optional[int] = Field(None, description="Filter by hierarchy level")
    limit: Optional[int] = Field(100, description="Maximum number of results")


class QueryEnablersInput(BaseModel):
    """Input for querying enablers."""
    csiId: Optional[str] = Field(None, description="Filter by CSI ID")
    year: Optional[int] = Field(None, description="Filter by year")
    month: Optional[int] = Field(None, description="Filter by month")
    limit: Optional[int] = Field(100, description="Maximum number of results")


class QueryManagementSegmentsInput(BaseModel):
    """Input for querying management segments."""
    name: Optional[str] = Field(None, description="Filter by segment name")
    year: Optional[int] = Field(None, description="Filter by year")
    month: Optional[int] = Field(None, description="Filter by month")
    hierarchy: Optional[int] = Field(None, description="Filter by hierarchy level")
    parent: Optional[str] = Field(None, description="Filter by parent segment")
    limit: Optional[int] = Field(100, description="Maximum number of results")


class QueryStatisticsInput(BaseModel):
    """Input for querying statistics."""
    nativeID: Optional[str] = Field(None, description="Filter by native ID")
    nativeIDType: Optional[str] = Field(None, description="Filter by native ID type")
    year: Optional[int] = Field(None, description="Filter by year")
    month: Optional[int] = Field(None, description="Filter by month")
    limit: Optional[int] = Field(100, description="Maximum number of results")


class GetDatabaseSchemaInput(BaseModel):
    """Input for getting database schema."""
    collection_name: Optional[str] = Field(None, description="Specific collection name, or all if not specified")


class EEProductivitiesDatabaseTool(BaseTool):
    """Base tool for ee-productivities database operations."""
    
    _db: Optional[MetricsQueryDatabase] = PrivateAttr(default=None)
    def __init__(self):
        super().__init__()
        self._db = None
    
    async def _get_database(self) -> MetricsQueryDatabase:
        """Get or initialize the database connection."""
        if self._db is None:
            try:
                logger.info("Initializing ee-productivities database connection...")
                
                # Get connection string from environment or use default
                connection_string = os.getenv("METRICS_MONGODB_URI", "mongodb://localhost:27017")
                database_name = os.getenv("METRICS_MONGODB_DATABASE", "ee-productivities")
                
                logger.info(f"Using connection string: {connection_string}")
                logger.info(f"Using database: {database_name}")
                logger.info("Collections will be selected dynamically by each tool")
                
                config = get_mongodb_ee_productivities_query_config(
                    connection_string=connection_string,
                    database_name=database_name,
                    collection_name=None  # No default collection - tools will switch dynamically
                )
                self._db = MetricsQueryDatabase(config)
                await self._db.initialize()
                logger.info(f"Database initialized. Adapter type: {type(self._db.adapter)}")
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                raise
        return self._db
    
    async def _switch_collection(self, collection_name: str) -> None:
        """Switch to a different collection within the same database."""
        try:
            db = await self._get_database()
            logger.info(f"Switching to collection: {collection_name}")
            logger.info(f"Database adapter: {db.adapter}")
            
            if db.adapter is None:
                raise RuntimeError("Database adapter is None. Database may not be properly initialized.")
            
            if hasattr(db.adapter, 'switch_collection'):
                await db.adapter.switch_collection(collection_name)
                logger.info(f"Successfully switched to collection: {collection_name}")
            else:
                logger.warning(f"Adapter does not support collection switching: {type(db.adapter)}")
                logger.warning(f"Available methods: {dir(db.adapter)}")
        except Exception as e:
            logger.error(f"Failed to switch collection to {collection_name}: {e}")
            raise
    
    async def _close_database(self):
        """Close the database connection."""
        if self._db:
            await self._db.close()
            self._db = None


class QueryApplicationSnapshotsTool(EEProductivitiesDatabaseTool):
    """Tool for querying application snapshots."""
    
    name: str = "query_application_snapshots"
    description: str = "Query application snapshots from the ee-productivities database. Use this to find information about applications, their status, criticality, sector, and other details."
    args_schema: type = QueryApplicationSnapshotsInput
    
    async def _arun(self, **kwargs) -> str:
        """Execute the tool."""
        try:
            db = await self._get_database()
            
            # Switch to application_snapshot collection
            await self._switch_collection("application_snapshot")
            
            # Build filter
            filter_dict = {k: v for k, v in kwargs.items() if v is not None and k != "limit"}
            limit = kwargs.get("limit", 100)
            
            # Execute query using native MongoDB query
            from app.core.database_abstraction import DatabaseQuery
            
            native_query = DatabaseQuery(
                operation="find",
                collection_table="application_snapshot",
                native_query={"filter": filter_dict, "limit": limit}
            )
            
            results = await db.execute_native_query(native_query)
            
            # Convert to structured result
            applications = []
            for doc in results:
                try:
                    app = ApplicationSnapshot(**doc)
                    applications.append(app)
                except Exception as e:
                    logger.warning(f"Failed to parse application document: {e}")
            
            result = ApplicationSnapshotResult(
                total_count=len(applications),
                applications=applications,
                summary={
                    "status_distribution": self._get_status_distribution(applications),
                    "sector_distribution": self._get_sector_distribution(applications),
                    "criticality_distribution": self._get_criticality_distribution(applications)
                }
            )
            
            return result.model_dump_json(indent=2)
            
        except Exception as e:
            logger.error(f"Failed to query application snapshots: {e}")
            return f"Error querying application snapshots: {str(e)}"
    
    def _run(self, *args, **kwargs):
        raise NotImplementedError("Synchronous run is not supported. Use async.")
    
    def _get_status_distribution(self, applications: List[ApplicationSnapshot]) -> Dict[str, int]:
        """Get status distribution."""
        distribution = {}
        for app in applications:
            status = app.status.value
            distribution[status] = distribution.get(status, 0) + 1
        return distribution
    
    def _get_sector_distribution(self, applications: List[ApplicationSnapshot]) -> Dict[str, int]:
        """Get sector distribution."""
        distribution = {}
        for app in applications:
            sector = app.sector
            distribution[sector] = distribution.get(sector, 0) + 1
        return distribution
    
    def _get_criticality_distribution(self, applications: List[ApplicationSnapshot]) -> Dict[str, int]:
        """Get criticality distribution."""
        distribution = {}
        for app in applications:
            criticality = app.application.get("criticality", "Unknown")
            distribution[criticality] = distribution.get(criticality, 0) + 1
        return distribution


class QueryEmployeeRatiosTool(EEProductivitiesDatabaseTool):
    """Tool for querying employee ratios."""
    
    name: str = "query_employee_ratios"
    description: str = "Query employee ratios from the ee-productivities database. Use this to find information about employee counts, engineer ratios, and tools adoption metrics."
    args_schema: type = QueryEmployeeRatiosInput
    
    async def _arun(self, **kwargs) -> str:
        """Execute the tool."""
        try:
            db = await self._get_database()
            
            # Switch to employee_ratio collection
            await self._switch_collection("employee_ratio")
            
            # Build filter
            filter_dict = {k: v for k, v in kwargs.items() if v is not None and k != "limit"}
            limit = kwargs.get("limit", 100)
            
            # Execute query
            from app.core.database_abstraction import DatabaseQuery
            
            native_query = DatabaseQuery(
                operation="find",
                collection_table="employee_ratio",
                native_query={"filter": filter_dict, "limit": limit}
            )
            
            results = await db.execute_native_query(native_query)
            
            # Convert to structured result
            employee_ratios = []
            for doc in results:
                try:
                    ratio = EmployeeRatio(**doc)
                    employee_ratios.append(ratio)
                except Exception as e:
                    logger.warning(f"Failed to parse employee ratio document: {e}")
            
            result = EmployeeRatioResult(
                total_count=len(employee_ratios),
                employee_ratios=employee_ratios,
                summary={
                    "total_employees": sum(len(ratio.employeeRatioSnapshot) for ratio in employee_ratios),
                    "total_tools_adoption": sum(len(ratio.toolsAdoptionRatioSnapshot) for ratio in employee_ratios)
                }
            )
            
            return result.model_dump_json(indent=2)
            
        except Exception as e:
            logger.error(f"Failed to query employee ratios: {e}")
            return f"Error querying employee ratios: {str(e)}"

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Synchronous run is not supported. Use async.")


class QueryEmployeeTreesTool(EEProductivitiesDatabaseTool):
    """Tool for querying employee trees."""
    
    name: str = "query_employee_trees"
    description: str = "Query employee tree structures from the ee-productivities database. Use this to find organizational hierarchies, reporting structures, and employee counts at different levels."
    args_schema: type = QueryEmployeeTreesInput
    
    async def _arun(self, **kwargs) -> str:
        """Execute the tool."""
        try:
            db = await self._get_database()
            
            # Switch to employee_tree_archived collection
            await self._switch_collection("employee_tree_archived")
            
            # Build filter
            filter_dict = {k: v for k, v in kwargs.items() if v is not None and k != "limit"}
            limit = kwargs.get("limit", 100)
            
            # Execute query
            from app.core.database_abstraction import DatabaseQuery
            
            native_query = DatabaseQuery(
                operation="find",
                collection_table="employee_tree_archived",
                native_query={"filter": filter_dict, "limit": limit}
            )
            
            results = await db.execute_native_query(native_query)
            
            # Convert to structured result
            employee_trees = []
            for doc in results:
                try:
                    tree = EmployeeTreeArchived(**doc)
                    employee_trees.append(tree)
                except Exception as e:
                    logger.warning(f"Failed to parse employee tree document: {e}")
            
            result = EmployeeTreeResult(
                total_count=len(employee_trees),
                employee_trees=employee_trees,
                summary={
                    "hierarchy_distribution": self._get_hierarchy_distribution(employee_trees),
                    "year_distribution": self._get_year_distribution(employee_trees)
                }
            )
            
            return result.model_dump_json(indent=2)
            
        except Exception as e:
            logger.error(f"Failed to query employee trees: {e}")
            return f"Error querying employee trees: {str(e)}"

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Synchronous run is not supported. Use async.")
    
    def _get_hierarchy_distribution(self, employee_trees: List[EmployeeTreeArchived]) -> Dict[int, int]:
        """Get hierarchy distribution."""
        distribution = {}
        for tree in employee_trees:
            hierarchy = tree.hierarchy
            distribution[hierarchy] = distribution.get(hierarchy, 0) + 1
        return distribution
    
    def _get_year_distribution(self, employee_trees: List[EmployeeTreeArchived]) -> Dict[int, int]:
        """Get year distribution."""
        distribution = {}
        for tree in employee_trees:
            year = tree.year
            distribution[year] = distribution.get(year, 0) + 1
        return distribution


class QueryEnablersTool(EEProductivitiesDatabaseTool):
    """Tool for querying enablers."""
    
    name: str = "query_enablers"
    description: str = "Query enabler CSI snapshots from the ee-productivities database. Use this to find information about enablers, their SE metrics, and achievement data."
    args_schema: type = QueryEnablersInput
    
    async def _arun(self, **kwargs) -> str:
        """Execute the tool."""
        try:
            db = await self._get_database()
            
            # Switch to enabler_csi_snapshots collection
            await self._switch_collection("enabler_csi_snapshots")
            
            # Build filter
            filter_dict = {k: v for k, v in kwargs.items() if v is not None and k != "limit"}
            limit = kwargs.get("limit", 100)
            
            # Execute query
            from app.core.database_abstraction import DatabaseQuery
            
            native_query = DatabaseQuery(
                operation="find",
                collection_table="enabler_csi_snapshots",
                native_query={"filter": filter_dict, "limit": limit}
            )
            
            results = await db.execute_native_query(native_query)
            
            # Convert to structured result
            enablers = []
            for doc in results:
                try:
                    enabler = EnablerCSISnapshots(**doc)
                    enablers.append(enabler)
                except Exception as e:
                    logger.warning(f"Failed to parse enabler document: {e}")
            
            result = EnablerResult(
                total_count=len(enablers),
                enablers=enablers,
                summary={
                    "total_snapshots": sum(len(enabler.enablersAggregation) for enabler in enablers),
                    "csi_distribution": self._get_csi_distribution(enablers)
                }
            )
            
            return result.model_dump_json(indent=2)
            
        except Exception as e:
            logger.error(f"Failed to query enablers: {e}")
            return f"Error querying enablers: {str(e)}"

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Synchronous run is not supported. Use async.")
    
    def _get_csi_distribution(self, enablers: List[EnablerCSISnapshots]) -> Dict[str, int]:
        """Get CSI distribution."""
        distribution = {}
        for enabler in enablers:
            csi_id = enabler.csiId
            distribution[csi_id] = distribution.get(csi_id, 0) + 1
        return distribution


class QueryManagementSegmentsTool(EEProductivitiesDatabaseTool):
    """Tool for querying management segments."""
    
    name: str = "query_management_segments"
    description: str = "Query management segment trees from the ee-productivities database. Use this to find organizational segments, their hierarchies, and reporting structures."
    args_schema: type = QueryManagementSegmentsInput
    
    async def _arun(self, **kwargs) -> str:
        """Execute the tool."""
        try:
            db = await self._get_database()
            
            # Switch to management_segment_tree collection
            await self._switch_collection("management_segment_tree")
            
            # Build filter
            filter_dict = {k: v for k, v in kwargs.items() if v is not None and k != "limit"}
            limit = kwargs.get("limit", 100)
            
            # Execute query
            from app.core.database_abstraction import DatabaseQuery
            
            native_query = DatabaseQuery(
                operation="find",
                collection_table="management_segment_tree",
                native_query={"filter": filter_dict, "limit": limit}
            )
            
            results = await db.execute_native_query(native_query)
            
            # Convert to structured result
            segments = []
            for doc in results:
                try:
                    segment = ManagementSegmentTree(**doc)
                    segments.append(segment)
                except Exception as e:
                    logger.warning(f"Failed to parse management segment document: {e}")
            
            result = ManagementSegmentResult(
                total_count=len(segments),
                segments=segments,
                summary={
                    "hierarchy_distribution": self._get_hierarchy_distribution(segments),
                    "version_distribution": self._get_version_distribution(segments)
                }
            )
            
            return result.model_dump_json(indent=2)
            
        except Exception as e:
            logger.error(f"Failed to query management segments: {e}")
            return f"Error querying management segments: {str(e)}"

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Synchronous run is not supported. Use async.")
    
    def _get_hierarchy_distribution(self, segments: List[ManagementSegmentTree]) -> Dict[int, int]:
        """Get hierarchy distribution."""
        distribution = {}
        for segment in segments:
            hierarchy = segment.hierarchy
            distribution[hierarchy] = distribution.get(hierarchy, 0) + 1
        return distribution
    
    def _get_version_distribution(self, segments: List[ManagementSegmentTree]) -> Dict[str, int]:
        """Get version distribution."""
        distribution = {}
        for segment in segments:
            version = segment.version
            distribution[version] = distribution.get(version, 0) + 1
        return distribution


class QueryStatisticsTool(EEProductivitiesDatabaseTool):
    """Tool for querying statistics."""
    
    name: str = "query_statistics"
    description: str = "Query statistics from the ee-productivities database. Use this to find performance metrics, quality indicators, and other statistical data."
    args_schema: type = QueryStatisticsInput
    
    async def _arun(self, **kwargs) -> str:
        """Execute the tool."""
        try:
            db = await self._get_database()
            
            # Switch to statistic collection
            await self._switch_collection("statistic")
            
            # Build filter
            filter_dict = {k: v for k, v in kwargs.items() if v is not None and k != "limit"}
            limit = kwargs.get("limit", 100)
            
            # Execute query
            from app.core.database_abstraction import DatabaseQuery
            
            native_query = DatabaseQuery(
                operation="find",
                collection_table="statistic",
                native_query={"filter": filter_dict, "limit": limit}
            )
            
            results = await db.execute_native_query(native_query)
            
            # Convert to structured result
            statistics = []
            for doc in results:
                try:
                    stat = Statistic(**doc)
                    statistics.append(stat)
                except Exception as e:
                    logger.warning(f"Failed to parse statistic document: {e}")
            
            result = StatisticResult(
                total_count=len(statistics),
                statistics=statistics,
                summary={
                    "total_snapshots": sum(len(stat.statistics) for stat in statistics),
                    "type_distribution": self._get_type_distribution(statistics)
                }
            )
            
            return result.model_dump_json(indent=2)
            
        except Exception as e:
            logger.error(f"Failed to query statistics: {e}")
            return f"Error querying statistics: {str(e)}"

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Synchronous run is not supported. Use async.")
    
    def _get_type_distribution(self, statistics: List[Statistic]) -> Dict[str, int]:
        """Get native ID type distribution."""
        distribution = {}
        for stat in statistics:
            stat_type = stat.nativeIDType
            distribution[stat_type] = distribution.get(stat_type, 0) + 1
        return distribution


class GetDatabaseSchemaTool(EEProductivitiesDatabaseTool):
    """Tool for getting database schema information."""
    
    name: str = "get_database_schema"
    description: str = "Get schema information about the ee-productivities database collections. Use this to understand the available data structures and fields."
    args_schema: type = GetDatabaseSchemaInput
    
    async def _arun(self, **kwargs) -> str:
        """Execute the tool."""
        try:
            db = await self._get_database()
            
            collection_name = kwargs.get("collection_name")
            
            if collection_name:
                # Get schema for specific collection
                await self._switch_collection(collection_name)
                schema_info = await db.get_schema_info()
                return schema_info
            else:
                # Get schema for all collections
                collections = await db.adapter.list_collections()
                all_schemas = {}
                
                for collection in collections:
                    try:
                        await self._switch_collection(collection)
                        schema_info = await db.get_schema_info()
                        all_schemas[collection] = schema_info
                    except Exception as e:
                        logger.warning(f"Failed to get schema for collection {collection}: {e}")
                        all_schemas[collection] = {"error": str(e)}
                
                return all_schemas
            
        except Exception as e:
            logger.error(f"Failed to get database schema: {e}")
            return f"Error getting database schema: {str(e)}"

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Synchronous run is not supported. Use async.")


class GetFieldPathsInput(BaseModel):
    """Input for getting field paths."""
    collection_name: Optional[str] = Field(None, description="Specific collection name, or all if not specified")


class GetFieldValuesInput(BaseModel):
    """Input for getting field values."""
    collection_name: str = Field(..., description="Collection name")
    field_path: str = Field(..., description="Field path (e.g., 'application.criticality', 'status', 'year')")
    limit: Optional[int] = Field(100, description="Maximum number of unique values to return")


class GetFieldPathsTool(EEProductivitiesDatabaseTool):
    """Tool for getting available field paths in collections."""
    
    name: str = "get_field_paths"
    description: str = "Get all available field paths in the ee-productivities database collections. Use this to understand the data structure and available fields for querying."
    args_schema: type = GetFieldPathsInput
    
    def _map_collection_name(self, collection_name: str) -> str:
        """Map collection names to handle plural/singular variations."""
        collection_mapping = {
            "employee_ratios": "employee_ratio",
            "application_snapshots": "application_snapshot",
            "management_segments": "management_segment_tree",
            "enabler_snapshots": "enabler_csi_snapshots",
            "employee_trees": "employee_tree_archived"
        }
        return collection_mapping.get(collection_name, collection_name)
    
    async def _arun(self, **kwargs) -> str:
        """Execute the tool."""
        try:
            db = await self._get_database()
            
            collection_name = kwargs.get("collection_name")
            
            if collection_name:
                # Map collection name to handle plural/singular variations
                mapped_collection_name = self._map_collection_name(collection_name)
                logger.info(f"Mapping collection name from '{collection_name}' to '{mapped_collection_name}'")
                
                # Get field paths for specific collection
                await self._switch_collection(mapped_collection_name)
                field_paths = await self._get_collection_field_paths(mapped_collection_name)
                result = {
                    "collection": mapped_collection_name,
                    "original_collection": collection_name,
                    "field_paths": field_paths
                }
                return str(result)
            else:
                # Get field paths for all collections
                collections = await db.adapter.list_collections()
                all_field_paths = {}
                
                for collection in collections:
                    try:
                        await self._switch_collection(collection)
                        field_paths = await self._get_collection_field_paths(collection)
                        all_field_paths[collection] = field_paths
                    except Exception as e:
                        logger.warning(f"Failed to get field paths for collection {collection}: {e}")
                        all_field_paths[collection] = {"error": str(e)}
                
                return str(all_field_paths)
            
        except Exception as e:
            logger.error(f"Failed to get field paths: {e}")
            return f"Error getting field paths: {str(e)}"
    
    async def _get_collection_field_paths(self, collection_name: str) -> List[str]:
        """Get field paths for a specific collection."""
        try:
            db = await self._get_database()
            # Get a sample document to analyze structure
            sample_doc = await db.adapter.collection.find_one()
            if not sample_doc:
                return []
            
            field_paths = self._extract_field_paths(sample_doc)
            return sorted(field_paths)
            
        except Exception as e:
            logger.error(f"Failed to get field paths for {collection_name}: {e}")
            return []
    
    def _extract_field_paths(self, obj: Any, prefix: str = "") -> List[str]:
        """Recursively extract field paths from a document."""
        field_paths = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{prefix}.{key}" if prefix else key
                field_paths.append(current_path)
                
                # Recursively extract nested fields
                if isinstance(value, (dict, list)):
                    nested_paths = self._extract_field_paths(value, current_path)
                    field_paths.extend(nested_paths)
        
        elif isinstance(obj, list) and obj:
            # For arrays, get paths from the first element
            if isinstance(obj[0], dict):
                nested_paths = self._extract_field_paths(obj[0], prefix)
                field_paths.extend(nested_paths)
        
        return field_paths

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Synchronous run is not supported. Use async.")


class GetFieldValuesTool(EEProductivitiesDatabaseTool):
    """Tool for getting unique values for a specific field path."""
    
    name: str = "get_field_values"
    description: str = "Get all unique values for a specific field path in a collection. Use this to understand what values are available for filtering and querying."
    args_schema: type = GetFieldValuesInput
    
    def _map_collection_name(self, collection_name: str) -> str:
        """Map collection names to handle plural/singular variations."""
        collection_mapping = {
            "employee_ratios": "employee_ratio",
            "application_snapshots": "application_snapshot",
            "management_segments": "management_segment_tree",
            "enabler_snapshots": "enabler_csi_snapshots",
            "employee_trees": "employee_tree_archived"
        }
        return collection_mapping.get(collection_name, collection_name)
    
    async def _arun(self, **kwargs) -> str:
        """Execute the tool."""
        try:
            db = await self._get_database()
            
            collection_name = kwargs["collection_name"]
            field_path = kwargs["field_path"]
            limit = kwargs.get("limit", 100)
            
            # Map collection name to handle plural/singular variations
            mapped_collection_name = self._map_collection_name(collection_name)
            logger.info(f"Mapping collection name from '{collection_name}' to '{mapped_collection_name}'")
            
            # Switch to the specified collection
            await self._switch_collection(mapped_collection_name)
            
            # Get unique values for the field path
            values = await self._get_field_values(mapped_collection_name, field_path, limit)
            
            result = {
                "collection": mapped_collection_name,
                "original_collection": collection_name,
                "field_path": field_path,
                "unique_values": values,
                "total_count": len(values)
            }
            return str(result)
            
        except Exception as e:
            logger.error(f"Failed to get field values: {e}")
            return f"Error getting field values: {str(e)}"
    
    async def _get_field_values(self, collection_name: str, field_path: str, limit: int) -> List[Any]:
        """Get unique values for a field path."""
        try:
            db = await self._get_database()
            # Use MongoDB's distinct operation to get unique values
            distinct_values = await db.adapter.collection.distinct(field_path)
            
            # Sort and limit the results
            sorted_values = sorted(distinct_values)
            limited_values = sorted_values[:limit]
            
            # Convert values to strings for consistent output
            string_values = []
            for value in limited_values:
                if value is None:
                    string_values.append("null")
                elif isinstance(value, (dict, list)):
                    string_values.append(str(value))
                else:
                    string_values.append(str(value))
            
            return string_values
            
        except Exception as e:
            logger.error(f"Failed to get values for field {field_path}: {e}")
            return []

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Synchronous run is not supported. Use async.")


def create_ee_productivities_tools() -> List[BaseTool]:
    """Create all ee-productivities database tools."""
    return [
        QueryApplicationSnapshotsTool(),
        QueryEmployeeRatiosTool(),
        QueryEmployeeTreesTool(),
        QueryEnablersTool(),
        QueryManagementSegmentsTool(),
        QueryStatisticsTool(),
        GetDatabaseSchemaTool(),
        GetFieldPathsTool(),
        GetFieldValuesTool()
    ] 