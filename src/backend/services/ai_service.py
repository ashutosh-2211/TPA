"""
AI Agent Service using LangGraph and GPT-5-mini
Handles flight, hotel, and news search queries with tool calling

This module provides the core agent functionality using LangGraph.
API routes should import and use the chat() function.
"""

import os
import logging
from typing import Literal
from datetime import datetime, timedelta
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our service functions
try:
    # Try relative imports first (when used as package)
    from .flight_service import get_flight_details, parse_flight_data_to_toon
    from .hotel_service import get_hotel_details, parse_hotel_json
    from .news_service import get_news, parse_news_data
    from .db_checkpointer import PostgresCheckpointer
except ImportError:
    # Fallback to absolute imports (when testing directly)
    from flight_service import get_flight_details, parse_flight_data_to_toon
    from hotel_service import get_hotel_details, parse_hotel_json
    from news_service import get_news, parse_news_data
    from db_checkpointer import PostgresCheckpointer

# Load environment variables
load_dotenv()

# Get current date for the system prompt
def get_current_date_info() -> str:
    """Get current date information for the AI to use"""
    now = datetime.now()
    return f"Today is {now.strftime('%A, %B %d, %Y')} (YYYY-MM-DD: {now.strftime('%Y-%m-%d')})"

# System prompt for the travel agent
SYSTEM_PROMPT = f"""You are a helpful travel planning assistant. Your role is to help users plan their trips by searching for flights, hotels, and travel news.

**CURRENT DATE CONTEXT:**
{get_current_date_info()}

CRITICAL: ALWAYS call get_current_date() FIRST when users mention ANY date, including:
- Relative dates: "tomorrow", "next week", "18th"
- Month names without year: "January 15th", "December 20", "Feb 10"
- ANY date reference that could be ambiguous

You MUST determine if a date is in the past and use the correct future year.

**CRITICAL INSTRUCTIONS FOR USING TOOLS:**

When users mention RELATIVE DATES (tomorrow, next week, 18th, etc.):
1. FIRST call get_current_date() to get today's date
2. Calculate the actual date based on the context
3. Then call the appropriate search tool with the calculated YYYY-MM-DD date

When users ask about FLIGHTS:
1. Extract ONLY the CITY NAMES (never use airport codes) from the user's message
   Examples:
   - "New York to London" → departure="New York", arrival="London"
   - "Mumbai to Delhi" → departure="Mumbai", arrival="Delhi"
   - "flight from Rome to Paris" → departure="Rome", arrival="Paris"
   - "fly to Tokyo from Seoul" → departure="Seoul", arrival="Tokyo"

2. Convert dates to YYYY-MM-DD format:
   - "December 20, 2025" → "2025-12-20"
   - "Dec 20" → "2025-12-20" (assume current year 2025)
   - "Jan 15, 2025" → "2025-01-15"
   - If no year given, assume 2025

3. ALWAYS call search_flights with EXACT city names and YYYY-MM-DD dates

When users ask about HOTELS:
1. Extract the city/location name for the 'location' parameter
   - "hotels in Bali" → location="Bali"
   - "beachside hotels in Goa" → location="beachside hotels in Goa"
   - "Paris city center hotel" → location="Paris city center"

2. Convert check-in and check-out dates to YYYY-MM-DD format
   - "from Dec 1 to Dec 5" → check_in_date="2025-12-01", check_out_date="2025-12-05"

3. Call search_hotels with these parameters

When users ask about NEWS or travel information:
1. Create a descriptive search query
   - "travel news for Italy" → query="travel Italy"
   - "COVID restrictions in Japan" → query="COVID restrictions Japan"

2. Call search_news with this query

**After receiving search results in TOON format:**
- Analyze the data carefully
- Provide a BRIEF conversational response (2-3 sentences max)
- Mention the number of options found and any key highlights
- DO NOT list all details - the UI will display full cards with images, prices, and booking links
- Be conversational, helpful, and friendly
- Ask follow-up questions if needed (budget, preferences, number of guests, etc.)

**Correct Tool Usage Examples:**

User: "Find flights from Mumbai to Delhi on December 20"
→ Step 1: get_current_date() to check if December 20, 2025 is in the past
→ Step 2: search_flights(departure="Mumbai", arrival="Delhi", outbound_date="2025-12-20" or "2026-12-20")

User: "I need a flight to London from New York on Jan 15"
→ Step 1: get_current_date() to determine if January 15 has passed this year
→ Step 2: search_flights(departure="New York", arrival="London", outbound_date="2026-01-15" if Jan already passed)

User: "Show me hotels in Paris from Dec 1 to Dec 5"
→ search_hotels(location="Paris", check_in_date="2025-12-01", check_out_date="2025-12-05")

User: "Find beachside hotels in Bali from November 17 to November 20"
→ search_hotels(location="beachside hotels in Bali", check_in_date="2025-11-17", check_out_date="2025-11-20")

**Examples with RELATIVE DATES:**

User: "Book a hotel in Mumbai tomorrow and check out on 18th"
→ Step 1: get_current_date() to find tomorrow's date and determine which 18th
→ Step 2: search_hotels(location="Mumbai", check_in_date="2025-11-16", check_out_date="2025-11-18")

User: "I need flights to Goa next week"
→ Step 1: get_current_date() to calculate next week's date
→ Step 2: search_flights(departure="[user's city]", arrival="Goa", outbound_date="2025-11-22")

User: "Hotels in Bali from tomorrow to next Friday"
→ Step 1: get_current_date() to calculate tomorrow and next Friday
→ Step 2: search_hotels(location="Bali", check_in_date="[tomorrow]", check_out_date="[next Friday]")
"""

# Initialize LLM with GPT-4o-mini
llm = ChatOpenAI(
    model="gpt-5-mini",
    temperature=0.2,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Track data accessed in the current request only
# No need for persistent storage since conversation history is in the database
_current_request_data = {
    "flights": {},
    "hotels": {},
    "news": {}
}


# ===== TOOL DEFINITIONS =====

@tool
def get_current_date() -> str:
    """
    Get the current date and time information. Use this when users mention dates or need date calculations.

    This tool helps you determine the CORRECT YEAR and date when users mention:
    - Specific months without year (e.g., "January 15", "Dec 20")
    - Relative dates (e.g., "tomorrow", "next week", "18th")
    - Any date reference that needs context

    IMPORTANT: Always assume future dates. If a month has already passed this year, use next year.

    Returns:
        String with current date, month information, and date calculation helpers

    Examples:
        Today is Nov 15, 2025. User says "January 15" → Should be 2026-01-15 (not 2025-01-15)
        Today is Nov 15, 2025. User says "December 20" → Should be 2025-12-20 (still in future)
        User says "18th" → Calculate which month's 18th based on current date
    """
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    current_day = now.day

    # Calculate useful dates
    tomorrow = now + timedelta(days=1)
    next_week = now + timedelta(days=7)

    # For each month, determine the correct year to use
    month_year_guide = []
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    for month_num, month_name in enumerate(months, 1):
        # If the month has already passed this year, use next year
        if month_num < current_month:
            year_to_use = current_year + 1
            month_year_guide.append(f"{month_name} → {year_to_use}")
        elif month_num == current_month:
            # Same month - check if we've passed a specific day
            month_year_guide.append(f"{month_name} → {current_year} (if day > {current_day}) or {current_year + 1} (if day <= {current_day})")
        else:
            year_to_use = current_year
            month_year_guide.append(f"{month_name} → {year_to_use}")

    # Calculate 18th of current or next month
    if current_day < 18:
        eighteenth_this_month = now.replace(day=18)
        eighteenth_str = f"18th of this month ({now.strftime('%B')}) is {eighteenth_this_month.strftime('%Y-%m-%d')}"
    else:
        # Move to next month's 18th
        if now.month == 12:
            next_month_18 = now.replace(year=now.year + 1, month=1, day=18)
        else:
            next_month_18 = now.replace(month=now.month + 1, day=18)
        eighteenth_str = f"18th of next month is {next_month_18.strftime('%Y-%m-%d')}"

    month_guide_str = "\n".join([f"  - {guide}" for guide in month_year_guide[:12]])

    return f"""Current Date Information:
- Today: {now.strftime('%A, %B %d, %Y')} ({now.strftime('%Y-%m-%d')})
- Current month: {now.strftime('%B')} {current_year}
- Day of month: {current_day}
- Tomorrow: {tomorrow.strftime('%Y-%m-%d')}
- Next week: {next_week.strftime('%Y-%m-%d')}
- {eighteenth_str}

CRITICAL - Month to Year Mapping (ALWAYS use future dates):
{month_guide_str}

RULE: If user mentions a month without a year:
- If that month has ALREADY PASSED this year → Use NEXT year ({current_year + 1})
- If that month is UPCOMING this year → Use THIS year ({current_year})

Examples:
- Today is Nov 15, 2025. "January 15" → 2026-01-15 (Jan already passed)
- Today is Nov 15, 2025. "December 20" → 2025-12-20 (Dec is upcoming)
- Today is Nov 15, 2025. "October 5" → 2026-10-05 (Oct already passed)"""


@tool
async def search_flights(
    departure: str,
    arrival: str,
    outbound_date: str,
    is_round_trip: bool = False,
    return_date: str | None = None
) -> str:
    """
    Search for flights between two cities on a specific date.

    IMPORTANT: Use CITY NAMES only (not airport codes).
    Date must be in YYYY-MM-DD format (e.g., "2025-12-20").

    Args:
        departure: Departure CITY name (e.g., "Mumbai", "New York", "London")
        arrival: Arrival CITY name (e.g., "Delhi", "Paris", "Tokyo")
        outbound_date: Departure date in YYYY-MM-DD format (e.g., "2025-12-20")
        is_round_trip: Whether this is a round trip booking (default: False)
        return_date: Return date in YYYY-MM-DD format (required if is_round_trip=True)

    Returns:
        TOON formatted string with flight options including price, duration, stops

    Examples:
        search_flights("Mumbai", "Delhi", "2025-12-20")
        search_flights("New York", "London", "2025-01-15")
    """
    logger.info("🛫 TOOL CALLED: search_flights")
    logger.info("   Parameters:")
    logger.info(f"      departure: {departure}")
    logger.info(f"      arrival: {arrival}")
    logger.info(f"      outbound_date: {outbound_date}")
    logger.info(f"      is_round_trip: {is_round_trip}")
    logger.info(f"      return_date: {return_date}")

    try:
        flight_data = await get_flight_details(
            departure=departure,
            arrival=arrival,
            outbound_date=outbound_date,
            is_round_trip=is_round_trip,
            return_date=return_date
        )

        if not flight_data:
            logger.warning("   ⚠️ No flight data returned from API")
            return "No flights found for the given route and dates."

        toon, full_data = parse_flight_data_to_toon(flight_data)

        logger.info("   ✅ Found flights, returning TOON format")
        logger.info(f"   TOON preview: {toon[:200]}...")

        # Track this data for current request only
        request_key = f"{departure}_{arrival}_{outbound_date}"
        _current_request_data["flights"][request_key] = full_data

        return toon
    except Exception as e:
        logger.error(f"   ❌ Error in search_flights: {str(e)}", exc_info=True)
        return f"Error searching flights: {str(e)}"


@tool
async def search_hotels(
    check_in_date: str,
    check_out_date: str,
    location: str
) -> str:
    """
    Search for hotels in a specific location for given dates.

    IMPORTANT: Dates must be in YYYY-MM-DD format.
    Location can include descriptors like "beachside hotels in Bali" or just city name.

    Args:
        check_in_date: Check-in date in YYYY-MM-DD format (e.g., "2025-12-01")
        check_out_date: Check-out date in YYYY-MM-DD format (e.g., "2025-12-05")
        location: Hotel location/city with optional description
                 (e.g., "beachside hotels in Bali", "Paris", "Tokyo city center")

    Returns:
        TOON formatted string with hotel options including name, price, rating

    Examples:
        search_hotels("2025-12-01", "2025-12-05", "Paris")
        search_hotels("2025-11-17", "2025-11-20", "beachside hotels in Bali")
    """
    try:
        hotel_data = await get_hotel_details(
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            q=location
        )

        if not hotel_data:
            return "No hotels found for the given location and dates."

        toon, full_data = parse_hotel_json(hotel_data)

        # Track this data for current request only
        request_key = f"{location}_{check_in_date}_{check_out_date}"
        _current_request_data["hotels"][request_key] = full_data

        return toon
    except Exception as e:
        return f"Error searching hotels: {str(e)}"


@tool
async def search_news(query: str) -> str:
    """
    Search for recent news articles related to travel, destinations, or topics.

    Args:
        query: Search query for news (e.g., "travel restrictions Italy", "best time to visit Japan", "COVID updates Europe")

    Returns:
        TOON formatted string with news articles including title, source, date

    Examples:
        search_news("travel restrictions Italy")
        search_news("best time to visit Japan")
        search_news("COVID travel updates Europe")
    """
    try:
        news_data = await get_news(query)

        if not news_data or not news_data.get('organic_results'):
            return "No news articles found for the given query."

        toon, full_data = parse_news_data(news_data)

        # Track this data for current request only
        _current_request_data["news"][query] = full_data

        return toon
    except Exception as e:
        return f"Error searching news: {str(e)}"


# Bind tools to LLM
tools = [get_current_date, search_flights, search_hotels, search_news]
llm_with_tools = llm.bind_tools(tools)


# ===== GRAPH STATE =====

class AgentState(MessagesState):
    """State for the agent graph"""
    pass


# ===== GRAPH NODES =====

async def agent_node(state: AgentState) -> dict:
    """
    Main agent reasoning node - decides whether to call tools or respond
    """
    messages = state["messages"]

    # Prepend system message if this is the first message
    if len(messages) == 1:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    logger.info("=" * 80)
    logger.info("🤖 AGENT NODE: Invoking LLM to decide next action")
    logger.info(f"   Messages in context: {len(messages)}")

    response = await llm_with_tools.ainvoke(messages)

    # Log what the agent decided to do
    if hasattr(response, "tool_calls") and response.tool_calls:
        logger.info(f"   ✅ Agent decided to call {len(response.tool_calls)} tool(s)")
        for i, tool_call in enumerate(response.tool_calls, 1):
            logger.info(f"   📞 Tool Call #{i}:")
            logger.info(f"      Tool: {tool_call.get('name', 'unknown')}")
            logger.info(f"      Arguments: {tool_call.get('args', {})}")
    else:
        logger.info("   💬 Agent decided to respond directly (no tool calls)")
        logger.info(f"   Response preview: {response.content[:100]}...")

    logger.info("=" * 80)
    return {"messages": [response]}


def should_continue(state: AgentState) -> Literal["tools", "end"]:
    """
    Router function - determines if we should call tools or end
    """
    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, route to tools node
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    # Otherwise, end the conversation
    return "end"


# ===== BUILD GRAPH =====

def create_agent_graph():
    """
    Creates the LangGraph agent with tool calling capability
    
    Uses PostgreSQL-backed checkpointer for persistent chat history.
    """
    # Initialize graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))

    # Add edges
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    workflow.add_edge("tools", "agent")

    # Compile with PostgreSQL checkpointer for persistent storage
    checkpointer = PostgresCheckpointer()
    logger.info("🗄️ Using PostgreSQL checkpointer for persistent chat history")
    return workflow.compile(checkpointer=checkpointer)


# ===== PUBLIC API =====

# Create the agent graph (singleton)
agent = create_agent_graph()


async def chat(user_message: str, thread_id: str = "default") -> dict:
    """
    Main chat interface for the travel planning agent

    Args:
        user_message: User's query/message
        thread_id: Conversation thread ID for maintaining context

    Returns:
        dict with 'response' (agent's message) and 'data_store' (only data accessed in this request)
    """
    global _current_request_data
    
    # Reset current request data at the start of each request
    _current_request_data = {
        "flights": {},
        "hotels": {},
        "news": {}
    }
    
    config = {"configurable": {"thread_id": thread_id}}

    # Invoke the agent
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=user_message)]},
        config=config
    )

    # Extract the final response
    final_message = result["messages"][-1]

    response = {
        "response": final_message.content,
        "tool_calls": [],
        "data_store": _current_request_data  # Return only data accessed in this request
    }

    return response


def get_stored_data(data_type: str, key: str) -> dict:
    """
    Retrieve full data for a specific search from the current request
    
    Note: This only returns data from the current request.
    Historical data is stored in the conversation database.

    Args:
        data_type: One of "flights", "hotels", "news"
        key: The request key used when storing

    Returns:
        Full data dict with all details for UI display, or empty dict if not found
    """
    return _current_request_data.get(data_type, {}).get(key, {})


def clear_data_store():
    """
    Clear current request data
    
    Note: This only clears the current request's data.
    Conversation history in the database is not affected.
    """
    global _current_request_data
    _current_request_data = {
        "flights": {},
        "hotels": {},
        "news": {}
    }


# ===== HELPER FUNCTIONS =====

def get_conversation_history(thread_id: str) -> list:
    """
    Get conversation history for a specific thread

    Args:
        thread_id: The conversation thread ID

    Returns:
        List of messages in the conversation
    """
    config = {"configurable": {"thread_id": thread_id}}
    state = agent.get_state(config)
    return state.values.get("messages", []) if state.values else []
