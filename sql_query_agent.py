import os
import json
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_ollama import OllamaLLM
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
from db import engine

load_dotenv()

# LLM
model_name = os.getenv("OLLAMA_MODEL", "ministral-3:3b")
temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0"))
print(f"[LOG] Initializing Ollama LLM with model: {model_name}")
llm = OllamaLLM(
    model=model_name,
    temperature=temperature
)
print("[LOG] LLM initialized successfully")

# Connect DB
print("[LOG] Connecting to database...")
db = SQLDatabase(
    engine,
    include_tables=["menu_items", "menu_categories", "orders", "order_items", "users"]
)
print("[LOG] Database connected successfully")
print(f"[LOG] Available tables: {db.get_usable_table_names()}")

# SQL Agent
print("[LOG] Creating SQL Agent...")
sql_agent = create_sql_agent(
    llm=llm,
    db=db,
    verbose=True,
    handle_parsing_errors=True
)
print("[LOG] SQL Agent created successfully")


def parse_json_from_output(output: str):
    """
    Post-process and extract JSON from LLM output
    """
    print(f"[LOG] Post-processing output...")
    try:
        # Try to find JSON array in the output
        start_idx = output.find('[')
        end_idx = output.rfind(']') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = output[start_idx:end_idx]
            print(f"[LOG] Extracted JSON: {json_str}")
            parsed = json.loads(json_str)
            print(f"[LOG] Successfully parsed JSON")
            return parsed
        else:
            print(f"[LOG] No JSON array found in output")
            return None
    except json.JSONDecodeError as e:
        print(f"[LOG] JSON parsing error: {e}")
        return None


def sql_query_menu(user_prompt: str):
    """
    Converts user prompt into SQL and executes it with ministral-3b optimizations
    """
    print(f"\n[LOG] sql_query_menu() called with prompt: {user_prompt}")
    
    system_prompt = """You are a LangChain SQL Agent optimized for ministral-3b.

DATABASE SCHEMA:
Table: menu_items
- id (INTEGER PRIMARY KEY)
- category_id (INTEGER) - Foreign Key to menu_categories.id
- name (VARCHAR) - Name of the food item
- description (TEXT)
- price (NUMERIC)
- is_vegetarian (BOOLEAN)
- is_vegan (BOOLEAN)
- spice_level (INTEGER) - 0 (mild) to 5 (very spicy)

Table: menu_categories
- id (INTEGER PRIMARY KEY)
- name (VARCHAR) - Category name (e.g., 'Starters', 'Main Course', 'Beverages')

Table: orders
- id (INTEGER PRIMARY KEY)
- user_id (INTEGER) - Foreign Key to users.id
- status (VARCHAR) - (e.g., 'PENDING', 'COMPLETED')

Table: order_items
- id (INTEGER PRIMARY KEY)
- order_id (INTEGER) - Foreign Key to orders.id
- menu_item_id (INTEGER) - Foreign Key to menu_items.id
- price (NUMERIC)

Table: users
- id (INTEGER PRIMARY KEY)
- name (VARCHAR)

CRITICAL RULES FOR MINISTRAL-3B:
1. ALWAYS add LIMIT 23 and OFFSET 0 to queries
2. ALWAYS use SELECT DISTINCT when querying
3. ALWAYS add ORDER BY clause (ORDER BY mi.name)
4. Return ONLY valid JSON after "Final Answer:"
5. NO explanations, markdown, or analysis
6. Use correct table and column names: menu_items, menu_categories, etc.

CUSTOMER PREFERENCE SUPPORT:
If the user provides a CUSTOMER/USER ID (e.g., "customer 10" or just "1"):
- Join menu_items, menu_categories, orders, and order_items to find user's history.
- Match items based on:
  1. CATEGORY: Same category as recently ordered items.
  2. SPICE LEVEL: Same spice level as ordered items.
  3. DESCRIPTION/NAME: Similar keywords in name or description.
- SQL Example:
  WITH last_ordered AS (
      SELECT mi.category_id, mi.spice_level, mi.name 
      FROM menu_items mi 
      JOIN order_items oi ON mi.id = oi.menu_item_id 
      JOIN orders o ON oi.order_id = o.id 
      WHERE o.user_id = [USER_ID] 
      ORDER BY o.created_at DESC LIMIT 5
  )
  SELECT DISTINCT mi.name, mc.name as category, mi.price
  FROM menu_items AS mi
  JOIN menu_categories AS mc ON mi.category_id = mc.id
  WHERE (mi.category_id IN (SELECT category_id FROM last_ordered) OR mi.spice_level IN (SELECT spice_level FROM last_ordered))
  AND mi.id NOT IN (SELECT menu_item_id FROM order_items oi2 JOIN orders o2 ON oi2.order_id = o2.id WHERE o2.user_id = [USER_ID])
  ORDER BY mi.name
  LIMIT 23 OFFSET 0;

QUERY TEMPLATE (General Search):
SELECT DISTINCT mi.name, mc.name as category, mi.price, mi.description, mi.spice_level
FROM menu_items AS mi
JOIN menu_categories AS mc ON mi.category_id = mc.id
WHERE mi.name ILIKE '%[query]%' OR mi.description ILIKE '%[query]%'
ORDER BY mi.name
LIMIT 23 OFFSET 0;

RESPONSE FORMAT (MANDATORY):
Final Answer:
[
  {"name": "string", "category": "string", "price": number}
]"""

    print(f"[LOG] System prompt loaded")
    print(f"[LOG] Temperature setting: 0 (fixed for ministral-3b)")
    
    final_prompt = system_prompt + "\n\nUser question: " + user_prompt
    print(f"[LOG] Invoking SQL agent...")
    
    try:
        result = sql_agent.invoke({"input": final_prompt})
        print(f"[LOG] SQL agent execution completed")
        print(f"[LOG] Raw result type: {type(result)}")
        print(f"[LOG] Raw result: {result}")
        
        # Extract the output from the agent's response
        if isinstance(result, dict) and "output" in result:
            raw_output = result["output"]
        else:
            raw_output = str(result)
        
        print(f"[LOG] Raw output: {raw_output}")
        
        # Post-process JSON output
        parsed_json = parse_json_from_output(raw_output)
        
        if parsed_json is not None:
            print(f"[LOG] Post-processing successful")
            print(f"[LOG] Final parsed result: {parsed_json}")
            return parsed_json
        else:
            print(f"[LOG] Could not parse JSON, returning raw output")
            return {"raw_output": raw_output, "status": "unparsed"}
            
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        print(f"[ERROR] Error type: {type(e).__name__}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return {"error": "Internal Server Error", "details": str(e)}