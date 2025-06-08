import os
import requests
import json

from agent.tools_and_schemas import SearchQueryList, Reflection
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Send
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langchain_core.runnables import RunnableConfig
from google.genai import Client

from agent.state import (
    OverallState,
    QueryGenerationState,
    ReflectionState,
    WebSearchState,
)
from agent.configuration import Configuration
from agent.prompts import (
    get_current_date,
    query_writer_instructions,
    web_searcher_instructions,
    reflection_instructions,
    answer_instructions,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from agent.utils import (
    get_citations,
    get_research_topic,
    insert_citation_markers,
    resolve_urls,
)

load_dotenv()

if os.getenv("GEMINI_API_KEY") is None:
    raise ValueError("GEMINI_API_KEY is not set")

# Check for OpenRouter API key if we're using OpenRouter models
def check_openrouter_requirements():
    """Check if OpenRouter API key is set when needed."""
    if os.getenv("OPENROUTER_API_KEY") is None:
        print("WARNING: OPENROUTER_API_KEY is not set. OpenRouter models (DeepSeek, GPT-4, etc.) will not work.")
        print("Please add OPENROUTER_API_KEY to your .env file to use non-Gemini models.")

# Run the check on import
check_openrouter_requirements()

# Used for Google Search API
genai_client = Client(api_key=os.getenv("GEMINI_API_KEY"))


def is_openrouter_model(model: str) -> bool:
    """Check if the model should use OpenRouter API."""
    openrouter_prefixes = ["deepseek/", "qwen/", "openai/", "google/"]
    return any(model.startswith(prefix) for prefix in openrouter_prefixes)


def call_openrouter_model(model: str, messages: list, temperature: float = 0.0) -> str:
    """Call OpenRouter API with the given model and messages."""
    try:
        # Convert LangChain message format to OpenRouter format
        openrouter_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                openrouter_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                openrouter_messages.append({"role": "assistant", "content": msg.content})
            else:
                # For string messages, assume they're user messages
                openrouter_messages.append({"role": "user", "content": str(msg)})
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.getenv("YOUR_SITE_URL", "http://localhost:2024"),
                "X-Title": os.getenv("YOUR_SITE_NAME", "LangGraph Research Agent"),
            },
            data=json.dumps({
                "model": model,
                "messages": openrouter_messages,
                "temperature": temperature,
            })
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")
            
    except Exception as e:
        raise Exception(f"Error calling OpenRouter API: {str(e)}")


def call_model_with_structured_output(model: str, prompt: str, schema_class, temperature: float = 1.0):
    """Call model (Gemini or OpenRouter) and return structured output."""
    if is_openrouter_model(model):
        # For OpenRouter models, we'll need to parse the JSON manually
        enhanced_prompt = f"""
{prompt}

Please respond with a valid JSON object that matches this schema:
{schema_class.model_json_schema()}

Return ONLY the JSON object, no additional text.
"""
        
        response_text = call_openrouter_model(model, [enhanced_prompt], temperature)
        
        # Try to extract JSON from the response
        try:
            # Remove any markdown formatting
            cleaned_response = response_text.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response.replace("```json", "").replace("```", "").strip()
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response.replace("```", "").strip()
            
            # Parse JSON
            parsed_json = json.loads(cleaned_response)
            return schema_class(**parsed_json)
        except (json.JSONDecodeError, Exception) as e:
            # Fallback: try to extract meaningful data
            if schema_class == Reflection:
                # For reflection, create a basic response
                return Reflection(
                    is_sufficient=False,
                    knowledge_gap="Unable to parse structured response",
                    follow_up_queries=["Need more information"]
                )
            elif schema_class == SearchQueryList:
                # For search queries, create a basic response
                return SearchQueryList(query=["search query"])
            else:
                raise Exception(f"Failed to parse structured output: {str(e)}")
    else:
        # Use original Gemini approach
        llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            max_retries=2,
            api_key=os.getenv("GEMINI_API_KEY"),
        )
        structured_llm = llm.with_structured_output(schema_class)
        return structured_llm.invoke(prompt)


def call_model_simple(model: str, prompt: str, temperature: float = 0.0) -> str:
    """Call model (Gemini or OpenRouter) and return simple text response."""
    if is_openrouter_model(model):
        return call_openrouter_model(model, [prompt], temperature)
    else:
        # Use original Gemini approach
        llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            max_retries=2,
            api_key=os.getenv("GEMINI_API_KEY"),
        )
        result = llm.invoke(prompt)
        return result.content


# Nodes
def generate_query(state: OverallState, config: RunnableConfig) -> QueryGenerationState:
    """LangGraph node that generates a search queries based on the User's question.

    Uses Gemini 2.0 Flash to create an optimized search query for web research based on
    the User's question.

    Args:
        state: Current graph state containing the User's question
        config: Configuration for the runnable, including LLM provider settings

    Returns:
        Dictionary with state update, including search_query key containing the generated query
    """
    configurable = Configuration.from_runnable_config(config)

    # check for custom initial search query count
    if state.get("initial_search_query_count") is None:
        state["initial_search_query_count"] = configurable.number_of_initial_queries

    # init Gemini 2.0 Flash
    llm = ChatGoogleGenerativeAI(
        model=configurable.query_generator_model,
        temperature=1.0,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    structured_llm = llm.with_structured_output(SearchQueryList)

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = query_writer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        number_queries=state["initial_search_query_count"],
    )
    # Generate the search queries
    result = structured_llm.invoke(formatted_prompt)
    return {"query_list": result.query}


def continue_to_web_research(state: QueryGenerationState):
    """LangGraph node that sends the search queries to the web research node.

    This is used to spawn n number of web research nodes, one for each search query.
    """
    return [
        Send("web_research", {"search_query": search_query, "id": int(idx)})
        for idx, search_query in enumerate(state["query_list"])
    ]


def web_research(state: WebSearchState, config: RunnableConfig) -> OverallState:
    """LangGraph node that performs web research using the native Google Search API tool.

    Executes a web search using the native Google Search API tool in combination with Gemini 2.0 Flash.

    Args:
        state: Current graph state containing the search query and research loop count
        config: Configuration for the runnable, including search API settings

    Returns:
        Dictionary with state update, including sources_gathered, research_loop_count, and web_research_results
    """
    # Configure
    configurable = Configuration.from_runnable_config(config)
    formatted_prompt = web_searcher_instructions.format(
        current_date=get_current_date(),
        research_topic=state["search_query"],
    )

    # Uses the google genai client as the langchain client doesn't return grounding metadata
    response = genai_client.models.generate_content(
        model=configurable.query_generator_model,
        contents=formatted_prompt,
        config={
            "tools": [{"google_search": {}}],
            "temperature": 0,
        },
    )
    # resolve the urls to short urls for saving tokens and time
    resolved_urls = resolve_urls(
        response.candidates[0].grounding_metadata.grounding_chunks, state["id"]
    )
    # Gets the citations and adds them to the generated text
    citations = get_citations(response, resolved_urls)
    modified_text = insert_citation_markers(response.text, citations)
    sources_gathered = [item for citation in citations for item in citation["segments"]]

    return {
        "sources_gathered": sources_gathered,
        "search_query": [state["search_query"]],
        "web_research_result": [modified_text],
    }


def reflection(state: OverallState, config: RunnableConfig) -> ReflectionState:
    """LangGraph node that identifies knowledge gaps and generates potential follow-up queries.

    Analyzes the current summary to identify areas for further research and generates
    potential follow-up queries. Uses structured output to extract
    the follow-up query in JSON format.

    Args:
        state: Current graph state containing the running summary and research topic
        config: Configuration for the runnable, including LLM provider settings

    Returns:
        Dictionary with state update, including search_query key containing the generated follow-up query
    """
    configurable = Configuration.from_runnable_config(config)
    # Increment the research loop count and get the reasoning model
    state["research_loop_count"] = state.get("research_loop_count", 0) + 1
    reasoning_model = state.get("reasoning_model") or configurable.reasoning_model

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = reflection_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        summaries="\n\n---\n\n".join(state["web_research_result"]),
    )
    
    # Use the new unified model calling function
    result = call_model_with_structured_output(
        model=reasoning_model,
        prompt=formatted_prompt,
        schema_class=Reflection,
        temperature=1.0
    )

    return {
        "is_sufficient": result.is_sufficient,
        "knowledge_gap": result.knowledge_gap,
        "follow_up_queries": result.follow_up_queries,
        "research_loop_count": state["research_loop_count"],
        "number_of_ran_queries": len(state["search_query"]),
    }


def evaluate_research(
    state: ReflectionState,
    config: RunnableConfig,
) -> OverallState:
    """LangGraph routing function that determines the next step in the research flow.

    Controls the research loop by deciding whether to continue gathering information
    or to finalize the summary based on the configured maximum number of research loops.

    Args:
        state: Current graph state containing the research loop count
        config: Configuration for the runnable, including max_research_loops setting

    Returns:
        String literal indicating the next node to visit ("web_research" or "finalize_summary")
    """
    configurable = Configuration.from_runnable_config(config)
    max_research_loops = (
        state.get("max_research_loops")
        if state.get("max_research_loops") is not None
        else configurable.max_research_loops
    )
    if state["is_sufficient"] or state["research_loop_count"] >= max_research_loops:
        return "finalize_answer"
    else:
        return [
            Send(
                "web_research",
                {
                    "search_query": follow_up_query,
                    "id": state["number_of_ran_queries"] + int(idx),
                },
            )
            for idx, follow_up_query in enumerate(state["follow_up_queries"])
        ]


def finalize_answer(state: OverallState, config: RunnableConfig):
    """LangGraph node that finalizes the research summary.

    Prepares the final output by deduplicating and formatting sources, then
    combining them with the running summary to create a well-structured
    research report with proper citations.

    Args:
        state: Current graph state containing the running summary and sources gathered

    Returns:
        Dictionary with state update, including running_summary key containing the formatted final summary with sources
    """
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = state.get("reasoning_model") or configurable.answer_model

    # Format the prompt - Include sources information for better context
    current_date = get_current_date()
    
    # Add source information to the prompt for better context
    sources_context = ""
    if state.get("sources_gathered"):
        sources_context = "\n\nAvailable sources to reference:\n"
        for i, source in enumerate(state["sources_gathered"][:10]):  # Limit to top 10 sources
            sources_context += f"[{i+1}] {source.get('title', 'Source')} - {source.get('short_url', source.get('value', ''))}\n"
        sources_context += "\nPlease reference these sources in your answer using the format [title](url) where appropriate.\n"
    
    formatted_prompt = answer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        summaries="\n---\n\n".join(state["web_research_result"]) + sources_context,
    )

    # Use the new unified model calling function
    result_content = call_model_simple(
        model=reasoning_model,
        prompt=formatted_prompt,
        temperature=0.0
    )
    
    # Ensure we have valid content before proceeding
    if not result_content or not result_content.strip():
        result_content = "I apologize, but I encountered an issue generating the response. Please try again."
    
    # Create an AIMessage with the result
    result = AIMessage(content=result_content)

    # Replace the short urls with the original urls and add all used urls to the sources_gathered
    unique_sources = []
    if state.get("sources_gathered"):
        for source in state["sources_gathered"]:
            # Check if the source URL appears in the result (both short and original)
            short_url = source.get("short_url", "")
            original_url = source.get("value", "")
            
            if short_url and short_url in result.content:
                result.content = result.content.replace(short_url, original_url)
                unique_sources.append(source)
            elif original_url and original_url in result.content:
                unique_sources.append(source)
            # Also check if source title/label is referenced
            elif source.get("label") and f"[{source.get('label')}]" in result.content:
                unique_sources.append(source)

    # If no sources were found in the content but we have sources, append them at the end
    if not unique_sources and state.get("sources_gathered"):
        # Take the first few sources as they're likely most relevant
        unique_sources = state["sources_gathered"][:5]
        
        # Add a sources section if the response doesn't already include sources
        if not any(marker in result.content.lower() for marker in ["source", "reference", "[", "http"]):
            sources_text = "\n\n**Sources:**\n"
            for i, source in enumerate(unique_sources, 1):
                title = source.get("label", source.get("title", f"Source {i}"))
                url = source.get("value", source.get("short_url", ""))
                if url:
                    sources_text += f"{i}. [{title}]({url})\n"
            result.content += sources_text

    return {
        "messages": [AIMessage(content=result.content)],
        "sources_gathered": unique_sources,
    }


# Create our Agent Graph
builder = StateGraph(OverallState, config_schema=Configuration)

# Define the nodes we will cycle between
builder.add_node("generate_query", generate_query)
builder.add_node("web_research", web_research)
builder.add_node("reflection", reflection)
builder.add_node("finalize_answer", finalize_answer)

# Set the entrypoint as `generate_query`
# This means that this node is the first one called
builder.add_edge(START, "generate_query")
# Add conditional edge to continue with search queries in a parallel branch
builder.add_conditional_edges(
    "generate_query", continue_to_web_research, ["web_research"]
)
# Reflect on the web research
builder.add_edge("web_research", "reflection")
# Evaluate the research
builder.add_conditional_edges(
    "reflection", evaluate_research, ["web_research", "finalize_answer"]
)
# Finalize the answer
builder.add_edge("finalize_answer", END)

graph = builder.compile(name="pro-search-agent")
