#!/usr/bin/env python3
"""
Script to set up MongoDB collections for the ee-productivities database
with the specified schema and mock data.
"""

import asyncio
import motor.motor_asyncio
from datetime import datetime, date
from bson import ObjectId
import random
from typing import List, Dict, Any


class MongoDBSetup:
    def __init__(self, connection_string: str = "mongodb://localhost:27017"):
        self.connection_string = connection_string
        self.client = None
        self.database = None
    
    async def connect(self):
        """Connect to MongoDB."""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(self.connection_string)
            await self.client.admin.command('ping')
            self.database = self.client["ee-productivities"]
            print("✅ Connected to MongoDB successfully")
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            print("✅ Disconnected from MongoDB")
    
    def generate_application_snapshot_data(self, count: int = 50) -> List[Dict[str, Any]]:
        """Generate mock data for application_snapshot collection."""
        applications = []
        
        # Sample data for variety
        criticalities = ["High", "Medium", "Low"]
        statuses = ["Active", "Inactive", "Retired"]
        types = ["Web Application", "Mobile App", "API Service", "Database", "Legacy System"]
        sectors = ["Finance", "Healthcare", "Retail", "Technology", "Manufacturing"]
        development_models = ["Agile", "Waterfall", "DevOps", "Scrum"]
        hosting_models = ["Cloud", "On-Premise", "Hybrid"]
        
        for i in range(count):
            year = random.randint(2020, 2024)
            month = random.randint(1, 12)
            
            application = {
                "_id": ObjectId(),
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
                "year": year,
                "month": month,
                "application": {
                    "csiId": random.randint(1000, 9999),
                    "criticality": random.choice(criticalities)
                },
                "level3": f"Department_{random.randint(1, 10)}",
                "level3Head": f"Manager_{random.randint(1, 20)}",
                "level3HeadId": f"EMP{random.randint(1000, 9999)}",
                "level4": f"Team_{random.randint(1, 50)}",
                "level4Head": f"Lead_{random.randint(1, 30)}",
                "level4HeadId": f"EMP{random.randint(1000, 9999)}",
                "level5": f"SubTeam_{random.randint(1, 100)}",
                "level5Head": f"Senior_{random.randint(1, 40)}",
                "level5HeadId": f"EMP{random.randint(1000, 9999)}",
                "name": f"Application_{random.randint(1, 1000)}",
                "organization": f"Org_{random.randint(1, 10)}",
                "orgHead": f"Director_{random.randint(1, 15)}",
                "orgHeadId": f"EMP{random.randint(1000, 9999)}",
                "organizationShort": f"ORG{random.randint(1, 10)}",
                "sector": random.choice(sectors),
                "sectorHead": f"SectorHead_{random.randint(1, 10)}",
                "sectorHeadId": f"EMP{random.randint(1000, 9999)}",
                "sectorShort": f"SECT{random.randint(1, 5)}",
                "status": random.choice(statuses),
                "type": random.choice(types),
                "sox": random.choice(["Yes", "No"]),
                "applicationManager": f"AppManager_{random.randint(1, 25)}",
                "applicationManagerId": f"EMP{random.randint(1000, 9999)}",
                "inceptionDate": datetime(random.randint(2010, 2020), random.randint(1, 12), random.randint(1, 28)),
                "lightspeedRegisteredDate": datetime(random.randint(2020, 2024), random.randint(1, 12), random.randint(1, 28)),
                "isRetired": random.choice([True, False]),
                "apmBSHScore": f"{random.randint(1, 10)}.{random.randint(0, 9)}",
                "developmentModel": random.choice(development_models),
                "hostingModel": random.choice(hosting_models),
                "kpmg": random.choice(["Yes", "No"])
            }
            applications.append(application)
        
        return applications
    
    def generate_employee_ratio_data(self, count: int = 30) -> List[Dict[str, Any]]:
        """Generate mock data for employeed_ratio collection."""
        employee_ratios = []
        
        for i in range(count):
            soe_id = f"SOE{random.randint(1000, 9999)}"
            
            # Generate employee ratio snapshots for multiple years/months
            employee_ratio_snapshots = []
            for year in range(2020, 2025):
                for month in range(1, 13):
                    if random.random() > 0.3:  # 70% chance to have data
                        employee_ratio_snapshots.append({
                            "year": year,
                            "month": month,
                            "engineerNum": random.randint(10, 100),
                            "employeeEngineerNum": random.randint(5, 50),
                            "totalNum": random.randint(20, 200)
                        })
            
            # Generate tools adoption ratio snapshots
            tools_adoption_snapshots = []
            for year in range(2020, 2025):
                for month in range(1, 13):
                    if random.random() > 0.3:  # 70% chance to have data
                        tools_adoption_snapshots.append({
                            "year": year,
                            "month": month,
                            "devhubNum": random.randint(5, 30),
                            "tpaNum": random.randint(3, 20),
                            "totalNum": random.randint(10, 50)
                        })
            
            employee_ratio = {
                "_id": ObjectId(),
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
                "soeId": soe_id,
                "employeeRatioSnapshot": employee_ratio_snapshots,
                "toolsAdoptionRatioSnapshot": tools_adoption_snapshots
            }
            employee_ratios.append(employee_ratio)
        
        return employee_ratios
    
    def generate_employee_tree_archived_data(self, count: int = 100) -> List[Dict[str, Any]]:
        """Generate mock data for employee_tree_archived collection."""
        employee_trees = []
        
        for i in range(count):
            year = random.randint(2020, 2024)
            month = random.randint(1, 12)
            
            # Generate a random reporting path
            path_length = random.randint(2, 5)
            path = []
            for j in range(path_length):
                path.append(f"Level{j+1}_Manager_{random.randint(1, 50)}")
            
            employee_tree = {
                "_id": ObjectId(),
                "archivedKey": f"ARCH_{year}_{month}_{random.randint(1, 1000)}",
                "updatedAt": datetime.now(),
                "version": f"v{random.randint(1, 5)}.{random.randint(0, 9)}",
                "createdAt": datetime.now(),
                "employeeEngineerNum": random.randint(5, 50),
                "employeeNum": random.randint(10, 100),
                "engineerNum": random.randint(8, 80),
                "geId": f"GE{random.randint(1000, 9999)}",
                "hierarchy": random.randint(1, 6),
                "month": month,
                "year": year,
                "parentSoeId": f"SOE{random.randint(1000, 9999)}",
                "path": path,
                "ritsId": f"RITS{random.randint(1000, 9999)}",
                "soeId": f"SOE{random.randint(1000, 9999)}",
                "totalNum": random.randint(20, 200)
            }
            employee_trees.append(employee_tree)
        
        return employee_trees
    
    def generate_enabler_csi_snapshots_data(self, count: int = 40) -> List[Dict[str, Any]]:
        """Generate mock data for enabler_csi_snapsots collection."""
        enabler_snapshots = []
        
        for i in range(count):
            csi_id = f"CSI{random.randint(1000, 9999)}"
            
            # Generate enablers aggregation for multiple years/months
            enablers_aggregation = []
            for year in range(2020, 2025):
                for month in range(1, 13):
                    if random.random() > 0.4:  # 60% chance to have data
                        # Generate multiple enablers per snapshot
                        enablers_summary = []
                        for enabler_id in range(1, random.randint(3, 8)):
                            enablers_summary.append({
                                "enablerId": enabler_id,
                                "totalSE": random.randint(100, 1000),
                                "achievedSE": random.randint(50, 800),
                                "date": datetime(year, month, random.randint(1, 28))
                            })
                        
                        enablers_aggregation.append({
                            "year": year,
                            "month": month,
                            "enablersSummary": enablers_summary
                        })
            
            enabler_snapshot = {
                "_id": ObjectId(),
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
                "csiId": csi_id,
                "enablersAggregation": enablers_aggregation
            }
            enabler_snapshots.append(enabler_snapshot)
        
        return enabler_snapshots
    
    def generate_management_segment_tree_data(self, count: int = 80) -> List[Dict[str, Any]]:
        """Generate mock data for mangement_segment_tree collection."""
        management_trees = []
        
        for i in range(count):
            year = random.randint(2020, 2024)
            month = random.randint(1, 12)
            
            # Generate a random name and hierarchy
            name = f"Segment_{random.randint(1, 50)}"
            hierarchy = random.randint(1, 5)
            
            # Generate path based on hierarchy
            path = [name]
            for level in range(1, hierarchy):
                path.append(f"Parent_{level}_{random.randint(1, 20)}")
            path.reverse()  # Make it hierarchical from top to bottom
            
            management_tree = {
                "_id": ObjectId(),
                "hash": f"hash_{random.randint(100000, 999999)}",
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
                "year": year,
                "month": month,
                "name": name,
                "nameHash": f"namehash_{random.randint(100000, 999999)}",
                "parent": path[-2] if len(path) > 1 else None,
                "version": f"v{random.randint(1, 5)}.{random.randint(0, 9)}",
                "hierarchy": hierarchy,
                "path": path
            }
            management_trees.append(management_tree)
        
        return management_trees
    
    def generate_statistic_data(self, count: int = 25) -> List[Dict[str, Any]]:
        """Generate mock data for statistic collection."""
        statistics = []
        
        statistic_types = ["Performance", "Quality", "Efficiency", "Productivity", "Engagement"]
        statistic_names = ["Response Time", "Error Rate", "Throughput", "Utilization", "Satisfaction"]
        
        for i in range(count):
            native_id = f"NATIVE_{random.randint(1000, 9999)}"
            
            # Generate statistics for multiple years/months
            statistics_data = []
            for year in range(2020, 2025):
                for month in range(1, 13):
                    if random.random() > 0.3:  # 70% chance to have data
                        # Generate multiple data points per snapshot
                        data_points = []
                        for stat_type in random.sample(statistic_types, random.randint(2, 4)):
                            data_points.append({
                                "statisticType": stat_type,
                                "statisticName": random.choice(statistic_names),
                                "number": random.randint(1, 1000),
                                "date": datetime(year, month, random.randint(1, 28))
                            })
                        
                        statistics_data.append({
                            "year": year,
                            "month": month,
                            "data": data_points
                        })
            
            statistic = {
                "_id": native_id,
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
                "checksum": f"checksum_{random.randint(100000, 999999)}",
                "nativeID": native_id,
                "nativeIDType": random.choice(["Application", "Service", "Component"]),
                "statistics": statistics_data
            }
            statistics.append(statistic)
        
        return statistics
    
    async def setup_collections(self):
        """Set up all collections with mock data."""
        try:
            print("🔄 Setting up MongoDB collections...")
            
            # Create collections and insert mock data
            collections_data = {
                "application_snapshot": self.generate_application_snapshot_data(50),
                "employeed_ratio": self.generate_employee_ratio_data(30),
                "employee_tree_archived": self.generate_employee_tree_archived_data(100),
                "enabler_csi_snapsots": self.generate_enabler_csi_snapshots_data(40),
                "mangement_segment_tree": self.generate_management_segment_tree_data(80),
                "statistic": self.generate_statistic_data(25)
            }
            
            for collection_name, data in collections_data.items():
                print(f"📝 Creating collection: {collection_name}")
                
                # Drop existing collection if it exists
                await self.database[collection_name].drop()
                
                # Insert mock data
                if data:
                    await self.database[collection_name].insert_many(data)
                    print(f"✅ Inserted {len(data)} documents into {collection_name}")
                
                # Create indexes for better performance
                await self.create_indexes(collection_name)
            
            print("✅ All collections set up successfully!")
            
        except Exception as e:
            print(f"❌ Failed to set up collections: {e}")
            raise
    
    async def create_indexes(self, collection_name: str):
        """Create indexes for the specified collection."""
        collection = self.database[collection_name]
        
        try:
            if collection_name == "application_snapshot":
                indexes = [
                    [("year", 1), ("month", 1)],
                    [("application.csiId", 1)],
                    [("application.criticality", 1)],
                    [("status", 1)],
                    [("sector", 1)]
                ]
            elif collection_name == "employeed_ratio":
                indexes = [
                    [("soeId", 1)],
                    [("employeeRatioSnapshot.year", 1), ("employeeRatioSnapshot.month", 1)]
                ]
            elif collection_name == "employee_tree_archived":
                indexes = [
                    [("soeId", 1)],
                    [("year", 1), ("month", 1)],
                    [("hierarchy", 1)],
                    [("archivedKey", 1)]
                ]
            elif collection_name == "enabler_csi_snapsots":
                indexes = [
                    [("csiId", 1)],
                    [("enablersAggregation.year", 1), ("enablersAggregation.month", 1)]
                ]
            elif collection_name == "mangement_segment_tree":
                indexes = [
                    [("name", 1)],
                    [("year", 1), ("month", 1)],
                    [("hierarchy", 1)],
                    [("path", 1)]
                ]
            elif collection_name == "statistic":
                indexes = [
                    [("nativeID", 1)],
                    [("nativeIDType", 1)],
                    [("statistics.year", 1), ("statistics.month", 1)]
                ]
            else:
                indexes = []
            
            for index_spec in indexes:
                try:
                    await collection.create_index(index_spec)
                except Exception as e:
                    print(f"⚠️  Index creation skipped for {collection_name}: {e}")
            
            print(f"✅ Indexes created for {collection_name}")
            
        except Exception as e:
            print(f"❌ Failed to create indexes for {collection_name}: {e}")
    
    async def verify_setup(self):
        """Verify that all collections were created with data."""
        try:
            print("\n🔍 Verifying setup...")
            
            collections = await self.database.list_collection_names()
            print(f"📊 Found collections: {collections}")
            
            for collection_name in collections:
                count = await self.database[collection_name].count_documents({})
                print(f"📈 {collection_name}: {count} documents")
            
            print("✅ Setup verification complete!")
            
        except Exception as e:
            print(f"❌ Failed to verify setup: {e}")


async def main():
    """Main function to set up MongoDB collections."""
    setup = MongoDBSetup()
    
    try:
        await setup.connect()
        await setup.setup_collections()
        await setup.verify_setup()
    finally:
        await setup.disconnect()


if __name__ == "__main__":
    asyncio.run(main()) 