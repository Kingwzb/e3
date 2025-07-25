#!/usr/bin/env python3
"""
Test metrics detection with database-related subquery keys.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.state import MultiHopState
from app.workflows.nodes.metrics_node import _should_extract_metrics
from app.workflows.nodes.orchestration_node import should_route_to_metrics


def test_metrics_detection():
    """Test that metrics detection works with various subquery keys."""
    
    print("🧪 Testing Metrics Detection with Database-Related Subquery Keys")
    print("=" * 70)
    
    # Test cases
    test_cases = [
        {
            "name": "Database key",
            "subqueries": {"Database": ["query1", "query2"]},
            "expected_metrics": True,
            "expected_routing": "metrics_extraction"
        },
        {
            "name": "employee_ratio Collection key",
            "subqueries": {"employee_ratio Collection": ["Retrieve the toolsAdoptionRatioSnapshot data for SOE3200."]},
            "expected_metrics": True,
            "expected_routing": "metrics_extraction"
        },
        {
            "name": "application_snapshot key",
            "subqueries": {"application_snapshot": ["Get application data"]},
            "expected_metrics": True,
            "expected_routing": "metrics_extraction"
        },
        {
            "name": "No database subqueries",
            "subqueries": {"General_Documentation": ["Find information"]},
            "expected_metrics": False,
            "expected_routing": "rag_extraction"
        },
        {
            "name": "Mixed database and non-database",
            "subqueries": {
                "employee_ratio": ["Get employee data"],
                "General_Documentation": ["Find information"]
            },
            "expected_metrics": True,
            "expected_routing": "both"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print("-" * 50)
        
        # Create test state
        state = MultiHopState(
            request_id="test",
            session_id="test",
            user_query="test query",
            formatted_user_query="",
            subqueries=test_case["subqueries"],
            retrieved_docs={},
            db_schema="",
            subquery_responses={},
            final_answer={},
            detected_docs=[],
            conversation_history=""
        )
        
        # Test metrics detection
        metrics_needed = _should_extract_metrics(state)
        print(f"Subqueries: {test_case['subqueries']}")
        print(f"Expected metrics: {test_case['expected_metrics']}")
        print(f"Actual metrics: {metrics_needed}")
        
        if metrics_needed == test_case['expected_metrics']:
            print("✅ Metrics detection: PASS")
        else:
            print("❌ Metrics detection: FAIL")
        
        # Test routing
        routing_result = should_route_to_metrics(state)
        print(f"Expected routing: {test_case['expected_routing']}")
        print(f"Actual routing: {routing_result}")
        
        if routing_result == test_case['expected_routing']:
            print("✅ Routing: PASS")
        else:
            print("❌ Routing: FAIL")
    
    print("\n🎉 Test completed!")


if __name__ == "__main__":
    test_metrics_detection() 