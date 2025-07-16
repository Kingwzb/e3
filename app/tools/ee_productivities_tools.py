"""LLM tools for querying ee-productivities database collections."""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

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
            config = get_mongodb_ee_productivities_query_config(
                connection_string="mongodb://localhost:27017",
                database_name="ee-productivities",
                collection_name="application_snapshot"
            )
            self._db = MetricsQueryDatabase(config)
            await self._db.initialize()
        return self._db
    
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
            await db.adapter.switch_collection("application_snapshot")
            
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
            
            # Switch to employeed_ratio collection
            await db.adapter.switch_collection("employeed_ratio")
            
            # Build filter
            filter_dict = {k: v for k, v in kwargs.items() if v is not None and k != "limit"}
            limit = kwargs.get("limit", 100)
            
            # Execute query
            from app.core.database_abstraction import DatabaseQuery
            
            native_query = DatabaseQuery(
                operation="find",
                collection_table="employeed_ratio",
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
            await db.adapter.switch_collection("employee_tree_archived")
            
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
                    "total_employees": sum(tree.totalNum for tree in employee_trees),
                    "total_engineers": sum(tree.engineerNum for tree in employee_trees),
                    "hierarchy_distribution": self._get_hierarchy_distribution(employee_trees)
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


class QueryEnablersTool(EEProductivitiesDatabaseTool):
    """Tool for querying enablers."""
    
    name: str = "query_enablers"
    description: str = "Query enabler CSI snapshots from the ee-productivities database. Use this to find information about enablers, their SE metrics, and achievement data."
    args_schema: type = QueryEnablersInput
    
    async def _arun(self, **kwargs) -> str:
        """Execute the tool."""
        try:
            db = await self._get_database()
            
            # Switch to enabler_csi_snapsots collection
            await db.adapter.switch_collection("enabler_csi_snapsots")
            
            # Build filter
            filter_dict = {k: v for k, v in kwargs.items() if v is not None and k != "limit"}
            limit = kwargs.get("limit", 100)
            
            # Execute query
            from app.core.database_abstraction import DatabaseQuery
            
            native_query = DatabaseQuery(
                operation="find",
                collection_table="enabler_csi_snapsots",
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
                    "total_aggregations": sum(len(enabler.enablersAggregation) for enabler in enablers),
                    "total_enablers": sum(
                        len(agg.enablersSummary) 
                        for enabler in enablers 
                        for agg in enabler.enablersAggregation
                    )
                }
            )
            
            return result.model_dump_json(indent=2)
            
        except Exception as e:
            logger.error(f"Failed to query enablers: {e}")
            return f"Error querying enablers: {str(e)}"

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Synchronous run is not supported. Use async.")


class QueryManagementSegmentsTool(EEProductivitiesDatabaseTool):
    """Tool for querying management segments."""
    
    name: str = "query_management_segments"
    description: str = "Query management segment trees from the ee-productivities database. Use this to find organizational segments, their hierarchies, and reporting structures."
    args_schema: type = QueryManagementSegmentsInput
    
    async def _arun(self, **kwargs) -> str:
        """Execute the tool."""
        try:
            db = await self._get_database()
            
            # Switch to mangement_segment_tree collection
            await db.adapter.switch_collection("mangement_segment_tree")
            
            # Build filter
            filter_dict = {k: v for k, v in kwargs.items() if v is not None and k != "limit"}
            limit = kwargs.get("limit", 100)
            
            # Execute query
            from app.core.database_abstraction import DatabaseQuery
            
            native_query = DatabaseQuery(
                operation="find",
                collection_table="mangement_segment_tree",
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
            await db.adapter.switch_collection("statistic")
            
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
                await db.adapter.switch_collection(collection_name)
                schema_info = await db.get_schema_info()
                return schema_info
            else:
                # Get schema for all collections
                collections = await db.adapter.list_collections()
                all_schemas = {}
                
                for collection in collections:
                    try:
                        await db.adapter.switch_collection(collection)
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


def create_ee_productivities_tools() -> List[BaseTool]:
    """Create all ee-productivities database tools."""
    return [
        QueryApplicationSnapshotsTool(),
        QueryEmployeeRatiosTool(),
        QueryEmployeeTreesTool(),
        QueryEnablersTool(),
        QueryManagementSegmentsTool(),
        QueryStatisticsTool(),
        GetDatabaseSchemaTool()
    ] 