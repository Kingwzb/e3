#!/usr/bin/env python3
"""
Test script for LLM agent integration with ee-productivities database tools.
This script simulates how an LLM would use the tools to answer questions.
"""

import asyncio
import sys
import os
import json
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.tools.ee_productivities_tools import create_ee_productivities_tools
from app.utils.logging import logger


class LLMAgentSimulator:
    """Simulates an LLM agent that uses the ee-productivities tools."""
    
    def __init__(self):
        self.tools = create_ee_productivities_tools()
        self.tool_map = {tool.name: tool for tool in self.tools}
        
        # Define question-to-tool mappings for demonstration
        self.question_patterns = {
            "application": {
                "keywords": ["application", "app", "system", "software", "criticality", "status", "sector"],
                "tool": "query_application_snapshots",
                "examples": [
                    "How many active applications do we have?",
                    "What are the high criticality applications?",
                    "Show me Technology sector applications",
                    "Which applications are using Agile development?",
                    "What applications are hosted in the cloud?"
                ]
            },
            "employee": {
                "keywords": ["employee", "ratio", "engineer", "staff", "team", "organization"],
                "tool": "query_employee_ratios",
                "examples": [
                    "What are our employee ratios?",
                    "How many engineers do we have?",
                    "Show me employee data for 2023"
                ]
            },
            "hierarchy": {
                "keywords": ["hierarchy", "tree", "organization", "structure", "reporting"],
                "tool": "query_employee_trees",
                "examples": [
                    "Show me the organizational hierarchy",
                    "What's our reporting structure?",
                    "How many employees are at the top level?"
                ]
            },
            "enabler": {
                "keywords": ["enabler", "csi", "se", "achievement"],
                "tool": "query_enablers",
                "examples": [
                    "What enablers do we have?",
                    "Show me CSI data",
                    "What are our SE achievements?"
                ]
            },
            "segment": {
                "keywords": ["segment", "management", "department", "division"],
                "tool": "query_management_segments",
                "examples": [
                    "Show me management segments",
                    "What departments do we have?",
                    "What's our organizational structure?"
                ]
            },
            "statistics": {
                "keywords": ["statistics", "metrics", "performance", "data", "numbers"],
                "tool": "query_statistics",
                "examples": [
                    "What statistics are available?",
                    "Show me performance metrics",
                    "What data do we have?"
                ]
            },
            "schema": {
                "keywords": ["schema", "structure", "fields", "database", "collection"],
                "tool": "get_database_schema",
                "examples": [
                    "What's the database schema?",
                    "Show me the data structure",
                    "What fields are available?"
                ]
            }
        }
    
    def _classify_question(self, question: str) -> Dict[str, Any]:
        """Classify a question to determine which tool to use."""
        question_lower = question.lower()
        
        for category, info in self.question_patterns.items():
            for keyword in info["keywords"]:
                if keyword in question_lower:
                    return {
                        "category": category,
                        "tool": info["tool"],
                        "confidence": 0.8
                    }
        
        # Default to schema tool if no specific pattern matches
        return {
            "category": "schema",
            "tool": "get_database_schema",
            "confidence": 0.3
        }
    
    def _extract_parameters(self, question: str, tool_name: str) -> Dict[str, Any]:
        """Extract parameters from a natural language question."""
        question_lower = question.lower()
        params = {"limit": 10}  # Default limit
        
        # Extract status
        if "active" in question_lower:
            params["status"] = "Active"
        elif "inactive" in question_lower:
            params["status"] = "Inactive"
        elif "retired" in question_lower:
            params["status"] = "Retired"
        
        # Extract criticality
        if "high" in question_lower and "critical" in question_lower:
            params["criticality"] = "High"
        elif "medium" in question_lower and "critical" in question_lower:
            params["criticality"] = "Medium"
        elif "low" in question_lower and "critical" in question_lower:
            params["criticality"] = "Low"
        
        # Extract sector
        if "technology" in question_lower:
            params["sector"] = "Technology"
        elif "finance" in question_lower:
            params["sector"] = "Finance"
        elif "healthcare" in question_lower:
            params["sector"] = "Healthcare"
        elif "retail" in question_lower:
            params["sector"] = "Retail"
        elif "manufacturing" in question_lower:
            params["sector"] = "Manufacturing"
        
        # Extract development model
        if "agile" in question_lower:
            params["developmentModel"] = "Agile"
        elif "waterfall" in question_lower:
            params["developmentModel"] = "Waterfall"
        elif "devops" in question_lower:
            params["developmentModel"] = "DevOps"
        elif "scrum" in question_lower:
            params["developmentModel"] = "Scrum"
        
        # Extract hosting model
        if "cloud" in question_lower:
            params["hostingModel"] = "Cloud"
        elif "on-premise" in question_lower or "on premise" in question_lower:
            params["hostingModel"] = "On-Premise"
        elif "hybrid" in question_lower:
            params["hostingModel"] = "Hybrid"
        
        # Extract hierarchy level
        if "top level" in question_lower or "top-level" in question_lower:
            params["hierarchy"] = 1
        elif "level 2" in question_lower:
            params["hierarchy"] = 2
        elif "level 3" in question_lower:
            params["hierarchy"] = 3
        
        # Extract year
        if "2024" in question:
            params["year"] = 2024
        elif "2023" in question:
            params["year"] = 2023
        elif "2022" in question:
            params["year"] = 2022
        elif "2021" in question:
            params["year"] = 2021
        elif "2020" in question:
            params["year"] = 2020
        
        # Extract month
        for month_num in range(1, 13):
            month_names = [
                "january", "february", "march", "april", "may", "june",
                "july", "august", "september", "october", "november", "december"
            ]
            if month_names[month_num - 1] in question_lower:
                params["month"] = month_num
                break
        
        return params
    
    async def answer_question(self, question: str) -> Dict[str, Any]:
        """Answer a natural language question using the appropriate tool."""
        print(f"\n🤔 Question: {question}")
        
        # Classify the question
        classification = self._classify_question(question)
        tool_name = classification["tool"]
        confidence = classification["confidence"]
        
        print(f"🔧 Selected tool: {tool_name} (confidence: {confidence})")
        
        try:
            # Get the appropriate tool
            tool = self.tool_map[tool_name]
            
            # Extract parameters from the question
            params = self._extract_parameters(question, tool_name)
            print(f"📋 Extracted parameters: {params}")
            
            # Execute the tool
            result = await tool._arun(**params)
            data = json.loads(result)
            
            # Generate a natural language response
            response = self._generate_response(question, data, tool_name)
            
            return {
                "question": question,
                "tool_used": tool_name,
                "confidence": confidence,
                "parameters": params,
                "data": data,
                "response": response
            }
            
        except Exception as e:
            logger.error(f"Failed to answer question: {e}")
            return {
                "question": question,
                "error": str(e),
                "response": f"Sorry, I encountered an error while trying to answer your question: {str(e)}"
            }
    
    def _generate_response(self, question: str, data: Dict[str, Any], tool_name: str) -> str:
        """Generate a natural language response based on the data."""
        total_count = data.get("total_count", 0)
        
        if tool_name == "query_application_snapshots":
            if total_count == 0:
                return "I found no applications matching your criteria."
            
            summary = data.get("summary", {})
            status_dist = summary.get("status_distribution", {})
            sector_dist = summary.get("sector_distribution", {})
            criticality_dist = summary.get("criticality_distribution", {})
            
            response = f"I found {total_count} applications matching your criteria."
            
            if status_dist:
                response += f" Status distribution: {status_dist}. "
            if sector_dist:
                response += f" Sector distribution: {sector_dist}. "
            if criticality_dist:
                response += f" Criticality distribution: {criticality_dist}. "
            
            return response
            
        elif tool_name == "query_employee_ratios":
            if total_count == 0:
                return "I found no employee ratio data matching your criteria."
            
            summary = data.get("summary", {})
            total_employees = summary.get("total_employees", 0)
            total_tools = summary.get("total_tools_adoption", 0)
            
            response = f"I found {total_count} employee ratio records."
            if total_employees > 0:
                response += f" Total employee snapshots: {total_employees}. "
            if total_tools > 0:
                response += f" Total tools adoption snapshots: {total_tools}. "
            
            return response
            
        elif tool_name == "query_employee_trees":
            if total_count == 0:
                return "I found no employee tree data matching your criteria."
            
            summary = data.get("summary", {})
            total_employees = summary.get("total_employees", 0)
            total_engineers = summary.get("total_engineers", 0)
            hierarchy_dist = summary.get("hierarchy_distribution", {})
            
            response = f"I found {total_count} employee tree records."
            if total_employees > 0:
                response += f" Total employees: {total_employees}. "
            if total_engineers > 0:
                response += f" Total engineers: {total_engineers}. "
            if hierarchy_dist:
                response += f" Hierarchy distribution: {hierarchy_dist}. "
            
            return response
            
        elif tool_name == "query_enablers":
            if total_count == 0:
                return "I found no enabler data matching your criteria."
            
            summary = data.get("summary", {})
            total_aggregations = summary.get("total_aggregations", 0)
            total_enablers = summary.get("total_enablers", 0)
            
            response = f"I found {total_count} enabler records."
            if total_aggregations > 0:
                response += f" Total aggregations: {total_aggregations}. "
            if total_enablers > 0:
                response += f" Total enablers: {total_enablers}. "
            
            return response
            
        elif tool_name == "query_management_segments":
            if total_count == 0:
                return "I found no management segment data matching your criteria."
            
            summary = data.get("summary", {})
            hierarchy_dist = summary.get("hierarchy_distribution", {})
            version_dist = summary.get("version_distribution", {})
            
            response = f"I found {total_count} management segment records."
            if hierarchy_dist:
                response += f" Hierarchy distribution: {hierarchy_dist}. "
            if version_dist:
                response += f" Version distribution: {version_dist}. "
            
            return response
            
        elif tool_name == "query_statistics":
            if total_count == 0:
                return "I found no statistics matching your criteria."
            
            summary = data.get("summary", {})
            total_snapshots = summary.get("total_snapshots", 0)
            type_dist = summary.get("type_distribution", {})
            
            response = f"I found {total_count} statistic records."
            if total_snapshots > 0:
                response += f" Total snapshots: {total_snapshots}. "
            if type_dist:
                response += f" Type distribution: {type_dist}. "
            
            return response
            
        elif tool_name == "get_database_schema":
            if isinstance(data, dict):
                collections = list(data.keys())
                response = f"I found {len(collections)} collections in the database: {', '.join(collections)}."
                
                # Add document counts if available
                for collection, schema in data.items():
                    if isinstance(schema, dict) and "document_count" in schema:
                        count = schema["document_count"]
                        response += f" {collection}: {count} documents. "
                
                return response
            else:
                return f"Database schema information: {data}"
        
        else:
            return f"I found {total_count} records matching your criteria."
    
    async def run_demo_questions(self):
        """Run a demonstration with various questions."""
        print("🚀 Starting LLM Agent Integration Demo")
        print("="*60)
        
        demo_questions = [
            "How many active applications do we have?",
            "What are the high criticality applications?",
            "Show me Technology sector applications",
            "Which applications are using Agile development?",
            "What applications are hosted in the cloud?",
            "What are our employee ratios?",
            "Show me the organizational hierarchy",
            "What enablers do we have?",
            "Show me management segments",
            "What statistics are available?",
            "What's the database schema?",
            "Show me applications from 2023",
            "What are the top-level employee trees?",
            "Which applications are retired?"
        ]
        
        results = []
        
        for i, question in enumerate(demo_questions, 1):
            print(f"\n{'='*60}")
            print(f"Question {i}/{len(demo_questions)}")
            
            result = await self.answer_question(question)
            results.append(result)
            
            print(f"✅ Response: {result['response']}")
            
            # Show some sample data if available
            if "data" in result and "applications" in result["data"]:
                apps = result["data"]["applications"]
                if apps:
                    print(f"📋 Sample application: {apps[0].get('name', 'Unknown')}")
            
            elif "data" in result and "employee_ratios" in result["data"]:
                ratios = result["data"]["employee_ratios"]
                if ratios:
                    print(f"📋 Sample SOE ID: {ratios[0].get('soeId', 'Unknown')}")
            
            elif "data" in result and "employee_trees" in result["data"]:
                trees = result["data"]["employee_trees"]
                if trees:
                    print(f"📋 Sample tree: {trees[0].get('soeId', 'Unknown')} - {trees[0].get('totalNum', 0)} employees")
        
        print(f"\n{'='*60}")
        print("🎉 Demo completed successfully!")
        print(f"📊 Processed {len(results)} questions")
        
        # Summary statistics
        successful_answers = len([r for r in results if "error" not in r])
        print(f"✅ Successful answers: {successful_answers}")
        print(f"❌ Failed answers: {len(results) - successful_answers}")
        
        return results


async def main():
    """Main function."""
    agent = LLMAgentSimulator()
    await agent.run_demo_questions()


if __name__ == "__main__":
    asyncio.run(main()) 