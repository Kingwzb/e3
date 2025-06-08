"""Examples of how different teams can configure and use workflows.

This demonstrates the modular workflow structure where:
- Individual node logic is in app/workflows/nodes/
- Workflow assembly is in app/workflows/
- Different configurations allow teams to work independently
"""

import asyncio
from app.workflows.chat_workflow import ChatWorkflowManager
from app.workflows.workflow_factory import (
    WorkflowConfig,
    create_minimal_workflow,
    create_rag_only_workflow,
    create_metrics_only_workflow,
    get_available_workflows
)
from app.models.state import WorkflowState


def demo_workflow_configurations():
    """Demonstrate different workflow configurations for different team needs."""
    
    print("=== Workflow Configuration Examples ===\n")
    
    # Example 1: Default full-featured workflow (Production)
    print("1. Production Workflow (Full Features)")
    production_config = WorkflowConfig(
        enable_rag=True,
        enable_metrics=True,
        enable_conversation_history=True,
        enable_conversation_save=True,
        parallel_processing=True,
        workflow_name="production_workflow"
    )
    production_manager = ChatWorkflowManager(production_config)
    print(f"   - Config: {production_config.workflow_name}")
    print(f"   - RAG: {production_config.enable_rag}")
    print(f"   - Metrics: {production_config.enable_metrics}")
    print(f"   - Parallel: {production_config.parallel_processing}")
    print()
    
    # Example 2: Development/Testing (Minimal workflow)
    print("2. Development/Testing Workflow (Minimal)")
    dev_config = WorkflowConfig(
        enable_rag=False,
        enable_metrics=False,
        enable_conversation_history=False,
        enable_conversation_save=False,
        workflow_name="development_workflow"
    )
    dev_manager = ChatWorkflowManager(dev_config)
    print(f"   - Config: {dev_config.workflow_name}")
    print(f"   - RAG: {dev_config.enable_rag}")
    print(f"   - Metrics: {dev_config.enable_metrics}")
    print(f"   - Fast testing without external dependencies")
    print()
    
    # Example 3: RAG Team Testing
    print("3. RAG Team Workflow (RAG Only)")
    rag_config = WorkflowConfig(
        enable_rag=True,
        enable_metrics=False,
        enable_conversation_history=True,
        enable_conversation_save=True,
        workflow_name="rag_team_workflow"
    )
    rag_manager = ChatWorkflowManager(rag_config)
    print(f"   - Config: {rag_config.workflow_name}")
    print(f"   - Focus on RAG functionality only")
    print(f"   - Conversation history for context testing")
    print()
    
    # Example 4: Database/Metrics Team Testing
    print("4. Database Team Workflow (Metrics Only)")
    db_config = WorkflowConfig(
        enable_rag=False,
        enable_metrics=True,
        enable_conversation_history=True,
        enable_conversation_save=True,
        workflow_name="database_team_workflow"
    )
    db_manager = ChatWorkflowManager(db_config)
    print(f"   - Config: {db_config.workflow_name}")
    print(f"   - Focus on database tool functionality")
    print(f"   - Test metrics extraction and tool calling")
    print()
    
    # Example 5: Sequential Processing (for debugging)
    print("5. Sequential Workflow (Debugging)")
    sequential_config = WorkflowConfig(
        enable_rag=True,
        enable_metrics=True,
        enable_conversation_history=True,
        enable_conversation_save=True,
        parallel_processing=False,
        conversation_history_limit=8,
        workflow_name="sequential_debug_workflow"
    )
    sequential_manager = ChatWorkflowManager(sequential_config)
    print(f"   - Config: {sequential_config.workflow_name}")
    print(f"   - Sequential processing for easier debugging")
    print(f"   - History limit: {sequential_config.conversation_history_limit}")
    print()
    
    # Example 6: Long Context Workflow
    print("6. Long Context Workflow (Complex Conversations)")
    long_context_config = WorkflowConfig(
        enable_rag=True,
        enable_metrics=True,
        enable_conversation_history=True,
        enable_conversation_save=True,
        parallel_processing=True,
        conversation_history_limit=25,
        workflow_name="long_context_workflow"
    )
    long_context_manager = ChatWorkflowManager(long_context_config)
    print(f"   - Config: {long_context_config.workflow_name}")
    print(f"   - Extended history for complex conversations")
    print(f"   - History limit: {long_context_config.conversation_history_limit}")
    print()
    
    # Example 7: Short Context Workflow
    print("7. Short Context Workflow (Quick Responses)")
    short_context_config = WorkflowConfig(
        enable_rag=True,
        enable_metrics=True,
        enable_conversation_history=True,
        enable_conversation_save=True,
        parallel_processing=True,
        conversation_history_limit=3,
        workflow_name="short_context_workflow"
    )
    short_context_manager = ChatWorkflowManager(short_context_config)
    print(f"   - Config: {short_context_config.workflow_name}")
    print(f"   - Minimal history for quick responses")
    print(f"   - History limit: {short_context_config.conversation_history_limit}")
    print()


async def demo_workflow_execution():
    """Demonstrate executing different workflows."""
    
    print("=== Workflow Execution Examples ===\n")
    
    # Use different workflow types
    workflows = {
        "minimal": ChatWorkflowManager(WorkflowConfig(
            enable_rag=False,
            enable_metrics=False,
            enable_conversation_history=False,
            enable_conversation_save=False,
            workflow_name="minimal_demo"
        )),
        "rag_only": ChatWorkflowManager(WorkflowConfig(
            enable_rag=True,
            enable_metrics=False,
            enable_conversation_history=True,
            enable_conversation_save=False,
            workflow_name="rag_demo"
        ))
    }
    
    test_message = "What is the weather like today?"
    test_conversation_id = "demo_conversation_123"
    
    for workflow_name, manager in workflows.items():
        print(f"Testing {workflow_name} workflow:")
        try:
            # Note: This would fail in real execution without proper setup
            # This is just to show the interface
            result = await manager.process_message(test_message, test_conversation_id)
            print(f"   - Success: {result['success']}")
            print(f"   - Response length: {len(result['response'])}")
            print(f"   - Metadata: {result['metadata']}")
        except Exception as e:
            print(f"   - Expected error (no setup): {type(e).__name__}")
        print()


def demo_team_workflows():
    """Examples for different teams working on the project."""
    
    print("=== Team-Specific Workflow Examples ===\n")
    
    print("Frontend/API Team:")
    print("   - Use minimal workflow for UI testing")
    print("   - Focus on request/response format")
    print("   - Quick iterations without external dependencies")
    print("   Example:")
    api_config = WorkflowConfig(
        enable_rag=False,
        enable_metrics=False,
        enable_conversation_history=False,
        enable_conversation_save=False,
        workflow_name="api_team_testing"
    )
    print(f"     ChatWorkflowManager({api_config.__dict__})")
    print()
    
    print("RAG/AI Team:")
    print("   - Use RAG-only workflow for vector store testing")
    print("   - Test embedding and retrieval quality")
    print("   - Conversation history for context evaluation")
    print("   Example:")
    rag_config = WorkflowConfig(
        enable_rag=True,
        enable_metrics=False,
        enable_conversation_history=True,
        enable_conversation_save=False,
        workflow_name="rag_team_testing"
    )
    print(f"     ChatWorkflowManager({rag_config.__dict__})")
    print()
    
    print("Database/Tools Team:")
    print("   - Use metrics-only workflow for tool testing")
    print("   - Test database connections and queries")
    print("   - LLM tool calling functionality")
    print("   Example:")
    db_config = WorkflowConfig(
        enable_rag=False,
        enable_metrics=True,
        enable_conversation_history=True,
        enable_conversation_save=True,
        workflow_name="database_team_testing"
    )
    print(f"     ChatWorkflowManager({db_config.__dict__})")
    print()
    
    print("DevOps/Infrastructure Team:")
    print("   - Use full workflow for integration testing")
    print("   - Test all components working together")
    print("   - Performance and reliability testing")
    print("   Example:")
    infra_config = WorkflowConfig(
        enable_rag=True,
        enable_metrics=True,
        enable_conversation_history=True,
        enable_conversation_save=True,
        parallel_processing=True,
        workflow_name="infrastructure_testing"
    )
    print(f"     ChatWorkflowManager({infra_config.__dict__})")
    print()


def main():
    """Run all workflow configuration examples."""
    demo_workflow_configurations()
    print("\n" + "="*50 + "\n")
    demo_team_workflows()
    
    print("\n" + "="*50 + "\n")
    print("Available Factory Functions:")
    available_workflows = get_available_workflows()
    for name, factory_func in available_workflows.items():
        print(f"   - {name}: {factory_func.__name__}")
    
    print(f"\nTo run async demo: asyncio.run(demo_workflow_execution())")
    
    print("\n" + "="*50 + "\n")
    print("Custom Configuration Examples:")
    print()
    
    # Custom configuration examples
    print("# Example: Customer Support Workflow (Long History)")
    print("support_config = WorkflowConfig(")
    print("    enable_rag=True,")
    print("    enable_metrics=True,") 
    print("    enable_conversation_history=True,")
    print("    enable_conversation_save=True,")
    print("    conversation_history_limit=20,  # Long history for support context")
    print("    workflow_name='customer_support'")
    print(")")
    print()
    
    print("# Example: Quick FAQ Workflow (Short History)")
    print("faq_config = WorkflowConfig(")
    print("    enable_rag=True,")
    print("    enable_metrics=False,")
    print("    enable_conversation_history=True,")
    print("    enable_conversation_save=True,")
    print("    conversation_history_limit=2,  # Minimal history for quick answers")
    print("    workflow_name='quick_faq'")
    print(")")
    print()
    
    print("# Example: Analytics Dashboard Workflow (Extended History)")
    print("analytics_config = WorkflowConfig(")
    print("    enable_rag=False,")
    print("    enable_metrics=True,")
    print("    enable_conversation_history=True,")
    print("    enable_conversation_save=True,")
    print("    conversation_history_limit=30,  # Extended history for data analysis")
    print("    metrics_context_limit=15,  # More context for complex metrics queries")
    print("    workflow_name='analytics_dashboard'")
    print(")")
    print()
    
    print("# Example: Performance Monitoring (Optimized for Speed)")
    print("performance_config = WorkflowConfig(")
    print("    enable_rag=False,")
    print("    enable_metrics=True,")
    print("    enable_conversation_history=True,")
    print("    enable_conversation_save=True,")
    print("    conversation_history_limit=5,  # Minimal history for speed")
    print("    metrics_context_limit=3,  # Quick metrics context")
    print("    workflow_name='performance_monitoring'")
    print(")")


if __name__ == "__main__":
    main() 