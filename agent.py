import os
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


def ask(user_message: str) -> str:
    agent = create_agent()
    result = agent.invoke({"input": user_message})
    return result["output"]