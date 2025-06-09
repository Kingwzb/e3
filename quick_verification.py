import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

async def quick_test():
    from app.tools.langchain_db_tools import create_langchain_db_tools, create_tool_config_for_environment
    from app.core.database import get_db
    from app.tools.vector_store import VectorStore
    from app.core.llm import llm_client
    
    print('🔄 Quick verification test...')
    
    # Test metrics extraction
    config = create_tool_config_for_environment('production')
    async for db_session in get_db():
        tools = create_langchain_db_tools(db_session, config)
        tool = next(t for t in tools if t.name == 'get_metrics_by_category')
        data = await tool._arun(category='satisfaction', days_back=3)
        print(f'✅ Extracted {len(data)} chars of satisfaction metrics data')
        break
    
    # Test vector store
    vs = VectorStore()
    doc_result = vs.search('customer satisfaction metrics', k=2)
    print(f'✅ Retrieved {len(doc_result.context)} chars of documentation')
    
    # Test LLM with metrics context
    messages = [
        {'role': 'system', 'content': 'You are a metrics analyst.'},
        {'role': 'user', 'content': f'Analyze this data: {data[:200]}... What insights can you provide?'}
    ]
    response = await llm_client.generate_response(messages=messages, max_tokens=150)
    print(f'✅ LLM generated {len(response["content"])} chars analysis')
    print(f'Sample analysis: {response["content"][:100]}...')
    
    print('\n🎉 All components working perfectly!')
    print('✅ Database extraction tools')
    print('✅ Vector store documentation retrieval') 
    print('✅ LLM analysis and insights generation')

if __name__ == "__main__":
    asyncio.run(quick_test()) 