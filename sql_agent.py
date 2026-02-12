from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.llms import Ollama
from db import engine

# LLM
llm = Ollama(
    model="ministral-3:3b",
    temperature=0
)

# Connect DB
db = SQLDatabase(
    engine,
    include_tables=["menu"]
)

# SQL Agent
sql_agent = create_sql_agent(
    llm=llm,
    db=db,
    verbose=True
)

def query_menu(user_prompt: str):
    """
    Converts user prompt into SQL and executes it
    """
    system_prompt = f"""
    You are a SQL expert.
    Table name: menu
    Columns: itemid, item, category, price

    Rules:
    - Use only SELECT queries
    - Do not modify data
    - Return only requested columns
    """

    final_prompt = system_prompt + "\nUser question: " + user_prompt
    return sql_agent.run(final_prompt)
