# Context Grounding Guide

How to use UiPath's Context Grounding Service to ground LLM responses in your organization's specific information through semantic document search.

## Overview

**Context Grounding** enables you to search through indexed documents using natural language queries and ground LLM responses in your organization's specific knowledge. This is essential for building accurate, information-rich agents that reference real organizational data.

## Index Creation

Before using context grounding, you must first create an index in your Orchestrator organization:

1. Navigate to the desired folder in Orchestrator
2. Select **Indexes** from the sidebar
3. Create a **new index** from a storage bucket containing your documents
4. Documents will be indexed and made searchable via semantic search

Once indexed, you can reference the index by name in your agent code.

## Core Components

### ContextGroundingRetriever

A document retrieval system using vector search to find relevant information based on natural language queries.

```python
from uipath_langchain.agent.tools import ContextGroundingRetriever

retriever = ContextGroundingRetriever(index_name="my_index")
documents = await retriever.ainvoke("What is our return policy?")
```

**Features:**
- Vector search for semantic relevance
- Async operations for performance
- Integration with LangChain chains and agents
- Returns document results with relevance scores

### ContextGroundingVectorStore

A vector store enabling semantic searches and retrieval chains with language models.

```python
from uipath_langchain.agent.tools import ContextGroundingVectorStore

vector_store = ContextGroundingVectorStore(index_name="my_index")
results = await vector_store.asimilarity_search(query="company policies", k=5)
```

**Search Methods:**
- `similarity_search()` - Find similar documents
- `similarity_search_with_score()` - Get documents with similarity scores
- `asimilarity_search()` - Async similarity search

## LangGraph Integration

### Using Retriever as an Agent Tool

Incorporate context grounding into your LangGraph agent by adding it as a tool that nodes can invoke:

```python
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.types import Command
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from uipath_langchain.chat.models import UiPathAzureChatOpenAI
from uipath_langchain.agent.tools import ContextGroundingRetriever

class GraphState(MessagesState):
    query: str
    answer: str | None = None

retriever = ContextGroundingRetriever(index_name="company_docs")

async def retrieve_context(state: GraphState) -> Command:
    """Retrieve relevant documents from context grounding."""
    documents = await retriever.ainvoke(state["query"])
    context = "\n".join([doc.page_content for doc in documents])
    return Command(update={
        "messages": state["messages"] + [
            ToolMessage(content=f"Retrieved context: {context}", tool_call_id="retrieve")
        ]
    })

async def respond_with_context(state: GraphState) -> Command:
    """Generate response using retrieved context."""
    llm = UiPathAzureChatOpenAI()
    messages = [
        SystemMessage(content="Answer based on the provided context."),
        *state["messages"],
    ]
    response = await llm.ainvoke(messages)
    return Command(update={"answer": response.content})

builder = StateGraph(GraphState)
builder.add_node("retrieve", retrieve_context)
builder.add_node("respond", respond_with_context)
builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "respond")
builder.add_edge("respond", END)

graph = builder.compile()
```

### Retrieval-Augmented Generation (RAG) Pattern

Combine context grounding with an LLM for more accurate responses:

```python
from langchain.chains import RetrievalQA
from uipath_langchain.chat.models import UiPathAzureChatOpenAI
from uipath_langchain.agent.tools import ContextGroundingVectorStore

llm = UiPathAzureChatOpenAI()
vector_store = ContextGroundingVectorStore(index_name="company_docs")
retriever = vector_store.as_retriever(search_kwargs={"k": 5})

rag_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever
)

result = await rag_chain.ainvoke("What are our current policies?")
```

## Agent Integration

Add context grounding as a tool to agents for autonomous document-based reasoning:

```python
from uipath_langchain.agent.tools import ContextGroundingRetriever
from langchain_core.tools import tool

@tool
async def search_company_docs(query: str) -> str:
    """Search company documentation for relevant information.

    Args:
        query: Natural language question to search for in company docs

    Returns:
        Relevant documents matching the query
    """
    retriever = ContextGroundingRetriever(index_name="company_docs")
    documents = await retriever.ainvoke(query)
    return "\n".join([doc.page_content for doc in documents])

# Use with agent tools
tools = [search_company_docs]
```

## Best Practices

### Document Preparation

- **Clear Structure**: Organize documents with clear titles, sections, and metadata
- **Chunking**: Keep document chunks focused on single topics for better relevance
- **Metadata**: Add metadata fields to help with filtering and relevance scoring
- **Updates**: Regularly update indexes when documents change

### Query Optimization

- **Specific Queries**: Use specific, natural language questions for better results
- **Context Setting**: Include context in your query ("according to company policy...")
- **Multiple Searches**: Use multiple queries to cover different aspects

### Response Grounding

- **Include Sources**: Always mention which documents the response references
- **Confidence Scores**: Check similarity scores to gauge result confidence
- **Fallback Handling**: Handle cases where no relevant documents are found

## Common Patterns

### Question-Answer System

```python
async def qa_system(question: str) -> dict:
    retriever = ContextGroundingRetriever(index_name="faq_docs")
    docs = await retriever.ainvoke(question)

    if not docs:
        return {"answer": "No relevant documents found.", "sources": []}

    context = "\n".join([doc.page_content for doc in docs])

    llm = UiPathAzureChatOpenAI()
    response = await llm.ainvoke([
        SystemMessage(content=f"Answer this question using the provided context: {context}"),
        HumanMessage(content=question)
    ])

    return {
        "answer": response.content,
        "sources": [doc.metadata.get("source", "Unknown") for doc in docs]
    }
```

### Document Summarization

```python
async def summarize_documents(topic: str) -> str:
    vector_store = ContextGroundingVectorStore(index_name="docs")
    results = await vector_store.asimilarity_search(topic, k=10)

    combined_content = "\n\n".join([doc.page_content for doc in results])

    llm = UiPathAzureChatOpenAI()
    summary = await llm.ainvoke([
        SystemMessage(content="Summarize these documents concisely."),
        HumanMessage(content=combined_content)
    ])

    return summary.content
```

## Performance Considerations

- **Async Operations**: Use async methods (`asimilarity_search`, `ainvoke`) for better performance
- **Result Limit**: Set appropriate `k` values to limit returned documents
- **Caching**: Cache retriever results when the same query is used multiple times
- **Index Selection**: Use specific index names to avoid unnecessary searches across all data

## Troubleshooting

**"Index not found" errors:**
- Verify the index name matches exactly what's in Orchestrator
- Ensure the index has been fully indexed (check Orchestrator UI)
- Confirm you have access to the index in your organization

**"No results found":**
- Try rephrasing your query with different keywords
- Check if documents are properly uploaded and indexed
- Verify document content is searchable (not just images/binary)

**Low relevance results:**
- Use more specific, natural language queries
- Check document chunking and quality
- Consider using multiple search queries to broaden coverage
- Review metadata to ensure proper categorization

## Reference

For detailed API documentation, see the [UiPath Context Grounding documentation](https://uipath.github.io/uipath-python/langchain/context_grounding/).