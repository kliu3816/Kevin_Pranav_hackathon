import os
import math
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from snowleopard import SnowLeopardClient
from dotenv import load_dotenv

load_dotenv()

_client = None

def get_client():
    global _client
    if _client is None:
        _client = SnowLeopardClient(api_key=os.getenv("SNOWLEOPARD_API_KEY"))
    return _client


@tool
def query_restaurants(natural_language_query: str) -> str:
    """Search the Philadelphia restaurant database using natural language.
    Use this to find restaurants by cuisine, price, location, rating, or any combination."""
    client = get_client()
    response = client.retrieve(
        datafile_id=os.getenv("SNOWLEOPARD_DATAFILE_ID"),
        user_query=natural_language_query
    )

    if response.responseStatus != "SUCCESS":
        return f"Error querying restaurants: {response.responseStatus}"

    if not response.data or not response.data[0].rows:
        return "No restaurants found matching that request."

    rows = response.data[0].rows
    lines = []
    for r in rows[:8]:
        name = r.get("name", "Unknown")
        address = r.get("address", "")
        stars = r.get("stars", "")
        reviews = r.get("review_count", "")
        categories = r.get("categories", "")
        attrs = r.get("attributes") or {}
        price = attrs.get("RestaurantsPriceRange2", "")
        price_str = ("$" * int(price)) if str(price).isdigit() else ""
        noise = attrs.get("NoiseLevel", "").replace("u'", "").replace("'", "")
        lines.append(
            f"- {name} | {stars}★ | {reviews} reviews | {address} | {categories}"
            + (f" | Price: {price_str}" if price_str else "")
            + (f" | Noise: {noise}" if noise else "")
        )

    return "\n".join(lines)


def create_agent():
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    tools = [query_restaurants]

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a friendly Philadelphia restaurant recommender. "
         "Always use the query_restaurants tool to look up real data before answering. "
         "Present results in a warm, conversational way — mention name, stars, and address. "
         "If the user asks a follow-up, call the tool again with a refined query."),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)

    return AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=5)


def search_restaurants_raw(query: str) -> list:
    client = get_client()
    response = client.retrieve(
        datafile_id=os.getenv("SNOWLEOPARD_DATAFILE_ID"),
        user_query=query
    )
    if response.responseStatus != "SUCCESS":
        return []
    if not response.data or not response.data[0].rows:
        return []
    return list(response.data[0].rows[:8])


def _haversine(lat1, lon1, lat2, lon2):
    """Distance in miles between two lat/lon points."""
    R = 3959
    p = math.pi / 180
    a = (0.5 - math.cos((lat2 - lat1) * p) / 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lon2 - lon1) * p)) / 2)
    return R * 2 * math.asin(math.sqrt(a))


def _retrieve(query):
    client = get_client()
    response = client.retrieve(
        datafile_id=os.getenv("SNOWLEOPARD_DATAFILE_ID"),
        user_query=query
    )
    if response.responseStatus != "SUCCESS" or not response.data or not response.data[0].rows:
        return []
    return response.data[0].rows


def _nearest(rows, lat, lon):
    """Return the row closest to lat/lon, ignoring rows missing coordinates."""
    def dist(r):
        try:
            return _haversine(lat, lon, float(r["latitude"]), float(r["longitude"]))
        except (TypeError, ValueError, KeyError):
            return float("inf")
    return min(rows, key=dist)


def plan_night(user_message: str) -> dict:
    # Step 1: dinner
    dinner_rows = _retrieve(f"dinner restaurant {user_message}")
    if not dinner_rows:
        return {"error": "Couldn't find dinner spots for that vibe."}
    dinner = dinner_rows[0]

    try:
        lat = float(dinner["latitude"])
        lon = float(dinner["longitude"])
        has_coords = True
    except (TypeError, ValueError, KeyError):
        has_coords = False

    # Step 2: cocktail bar / drinks near dinner
    bar_rows = _retrieve(f"cocktail bar nightlife drinks {user_message}")
    bar = _nearest(bar_rows, lat, lon) if has_coords and bar_rows else (bar_rows[0] if bar_rows else None)

    # Step 3: dessert near dinner
    dessert_rows = _retrieve(f"dessert cafe bakery sweets {user_message}")
    dessert = _nearest(dessert_rows, lat, lon) if has_coords and dessert_rows else (dessert_rows[0] if dessert_rows else None)

    steps = []
    if dinner:
        steps.append({"category": "Dinner",  "emoji": "🍽️",  "time": "7:00 PM",  "restaurant": dinner})
    if bar:
        steps.append({"category": "Drinks",  "emoji": "🍹",  "time": "9:00 PM",  "restaurant": bar})
    if dessert:
        steps.append({"category": "Dessert", "emoji": "🍰", "time": "10:30 PM", "restaurant": dessert})

    return {"steps": steps}


def ask(user_message: str) -> str:
    agent = create_agent()
    result = agent.invoke({"input": user_message})
    return result["output"]