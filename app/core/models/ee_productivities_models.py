"""Data models for ee-productivities database collections."""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from pydantic import BaseModel, Field
from enum import Enum


class ApplicationCriticality(str, Enum):
    """Application criticality levels."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ApplicationStatus(str, Enum):
    """Application status."""
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    RETIRED = "Retired"


class ApplicationType(str, Enum):
    """Application types."""
    WEB_APPLICATION = "Web Application"
    MOBILE_APP = "Mobile App"
    API_SERVICE = "API Service"
    DATABASE = "Database"
    LEGACY_SYSTEM = "Legacy System"


class DevelopmentModel(str, Enum):
    """Development models."""
    AGILE = "Agile"
    WATERFALL = "Waterfall"
    DEVOPS = "DevOps"
    SCRUM = "Scrum"


class HostingModel(str, Enum):
    """Hosting models."""
    CLOUD = "Cloud"
    ON_PREMISE = "On-Premise"
    HYBRID = "Hybrid"


class ApplicationSnapshot(BaseModel):
    """Application snapshot document."""
    id: Optional[str] = Field(None, alias="_id")
    createdAt: datetime
    updatedAt: datetime
    year: int
    month: int
    application: Dict[str, Any] = Field(..., description="Application details with csiId and criticality")
    level3: str
    level3Head: str
    level3HeadId: str
    level4: str
    level4Head: str
    level4HeadId: str
    level5: str
    level5Head: str
    level5HeadId: str
    name: str
    organization: str
    orgHead: str
    orgHeadId: str
    organizationShort: str
    sector: str
    sectorHead: str
    sectorHeadId: str
    sectorShort: str
    status: ApplicationStatus
    type: ApplicationType
    sox: str
    applicationManager: str
    applicationManagerId: str
    inceptionDate: datetime
    lightspeedRegisteredDate: datetime
    isRetired: bool
    apmBSHScore: str
    developmentModel: DevelopmentModel
    hostingModel: HostingModel
    kpmg: str

    class Config:
        validate_by_name = True


class EmployeeRatioSnapshot(BaseModel):
    """Employee ratio snapshot."""
    year: int
    month: int
    engineerNum: int
    employeeEngineerNum: int
    totalNum: int


class ToolsAdoptionSnapshot(BaseModel):
    """Tools adoption snapshot."""
    year: int
    month: int
    devhubNum: int
    tpaNum: int
    totalNum: int


class EmployeeRatio(BaseModel):
    """Employee ratio document."""
    id: Optional[str] = Field(None, alias="_id")
    createdAt: datetime
    updatedAt: datetime
    soeId: str
    employeeRatioSnapshot: List[EmployeeRatioSnapshot]
    toolsAdoptionRatioSnapshot: List[ToolsAdoptionSnapshot]

    class Config:
        validate_by_name = True


class EmployeeTreeArchived(BaseModel):
    """Employee tree archived document."""
    id: Optional[str] = Field(None, alias="_id")
    archivedKey: str
    updatedAt: datetime
    version: str
    createdAt: datetime
    employeeEngineerNum: int
    employeeNum: int
    engineerNum: int
    geId: str
    hierarchy: int
    month: int
    year: int
    parentSoeId: str
    path: List[str]
    ritsId: str
    soeId: str
    totalNum: int

    class Config:
        validate_by_name = True


class EnablerSummary(BaseModel):
    """Enabler summary."""
    enablerId: int
    totalSE: int
    achievedSE: int
    date: datetime


class EnablersAggregation(BaseModel):
    """Enablers aggregation."""
    year: int
    month: int
    enablersSummary: List[EnablerSummary]


class EnablerCSISnapshots(BaseModel):
    """Enabler CSI snapshots document."""
    id: Optional[str] = Field(None, alias="_id")
    createdAt: datetime
    updatedAt: datetime
    csiId: str
    enablersAggregation: List[EnablersAggregation]

    class Config:
        validate_by_name = True


class ManagementSegmentTree(BaseModel):
    """Management segment tree document."""
    id: Optional[str] = Field(None, alias="_id")
    hash: str
    createdAt: datetime
    updatedAt: datetime
    year: int
    month: int
    name: str
    nameHash: str
    parent: Optional[str]
    version: str
    hierarchy: int
    path: List[str]

    class Config:
        validate_by_name = True


class StatisticData(BaseModel):
    """Statistic data."""
    statisticType: str
    statisticName: str
    number: int
    date: datetime


class StatisticsSnapshot(BaseModel):
    """Statistics snapshot."""
    year: int
    month: int
    data: List[StatisticData]


class Statistic(BaseModel):
    """Statistic document."""
    id: str = Field(..., alias="_id")
    createdAt: datetime
    updatedAt: datetime
    checksum: str
    nativeID: str
    nativeIDType: str
    statistics: List[StatisticsSnapshot]

    class Config:
        validate_by_name = True


# Collection-specific query results
class ApplicationSnapshotResult(BaseModel):
    """Result wrapper for application snapshot queries."""
    total_count: int
    applications: List[ApplicationSnapshot]
    summary: Dict[str, Any] = Field(default_factory=dict)


class EmployeeRatioResult(BaseModel):
    """Result wrapper for employee ratio queries."""
    total_count: int
    employee_ratios: List[EmployeeRatio]
    summary: Dict[str, Any] = Field(default_factory=dict)


class EmployeeTreeResult(BaseModel):
    """Result wrapper for employee tree queries."""
    total_count: int
    employee_trees: List[EmployeeTreeArchived]
    summary: Dict[str, Any] = Field(default_factory=dict)


class EnablerResult(BaseModel):
    """Result wrapper for enabler queries."""
    total_count: int
    enablers: List[EnablerCSISnapshots]
    summary: Dict[str, Any] = Field(default_factory=dict)


class ManagementSegmentResult(BaseModel):
    """Result wrapper for management segment queries."""
    total_count: int
    segments: List[ManagementSegmentTree]
    summary: Dict[str, Any] = Field(default_factory=dict)


class StatisticResult(BaseModel):
    """Result wrapper for statistic queries."""
    total_count: int
    statistics: List[Statistic]
    summary: Dict[str, Any] = Field(default_factory=dict)


# Query filters for specific collections
class ApplicationSnapshotFilter(BaseModel):
    """Filter for application snapshot queries."""
    year: Optional[int] = None
    month: Optional[int] = None
    status: Optional[ApplicationStatus] = None
    sector: Optional[str] = None
    criticality: Optional[ApplicationCriticality] = None
    type: Optional[ApplicationType] = None
    organization: Optional[str] = None
    isRetired: Optional[bool] = None
    developmentModel: Optional[DevelopmentModel] = None
    hostingModel: Optional[HostingModel] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0


class EmployeeRatioFilter(BaseModel):
    """Filter for employee ratio queries."""
    soeId: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0


class EmployeeTreeFilter(BaseModel):
    """Filter for employee tree queries."""
    soeId: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    hierarchy: Optional[int] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0


class EnablerFilter(BaseModel):
    """Filter for enabler queries."""
    csiId: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0


class ManagementSegmentFilter(BaseModel):
    """Filter for management segment queries."""
    name: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    hierarchy: Optional[int] = None
    parent: Optional[str] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0


class StatisticFilter(BaseModel):
    """Filter for statistic queries."""
    nativeID: Optional[str] = None
    nativeIDType: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0 