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
    include_tables=["samsgriddle_menu"]
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
Table: samsgriddle_menu
Columns: 
- id (SERIAL PRIMARY KEY)
- item_category (VARCHAR) - Values: 'Vegetarian', 'Vegan', 'Non-Vegetarian', 'Beverage'
- item_name (TEXT) - Name of the food item
- item_price (INTEGER) - Price in rupees
- item_taste (VARCHAR) - Values: 'Spicy', 'Sweet', 'Mild', 'Savory'
- item_quantity (VARCHAR) - Values: 'Light', 'Medium', 'Heavy'
- item_special (VARCHAR) - Values: 'Chef Special', 'Premium', 'Refreshing', 'Bestseller', 'Regular'
- created_at (TIMESTAMP)

CRITICAL RULES FOR MINISTRAL-3B:
1. ALWAYS add LIMIT 23 and OFFSET 0 to queries
2. ALWAYS use SELECT DISTINCT when querying
3. ALWAYS add ORDER BY clause (ORDER BY item_name)
4. Return ONLY valid JSON after "Final Answer:"
5. NO explanations, markdown, or analysis
6. Use column names: item_category, item_name, item_price (not category, item, price)

CUSTOMER PREFERENCE SUPPORT:
If the user provides a CUSTOMER ID (e.g., "customer 10", or JUST A NUMBER like "1"):
- If the input is ONLY a number (e.g., "1"), treat it as "recommend for customer_id 1".
- Use a SELF-JOIN to find items matching the customer's preference (category & taste)
- SQL Pattern:
  SELECT DISTINCT T1.item_name, T1.item_category, T1.item_price, T1.item_taste, T1.item_special, T1.customer_id
  FROM samsgriddle_menu AS T1
  JOIN samsgriddle_menu AS T2 ON T2.customer_id = [CUSTOMER_ID]
  WHERE T1.item_category = T2.item_category 
  AND T1.item_taste = T2.item_taste
  AND (T1.customer_id != 1 OR T2.customer_id = 1) -- PRIVACY RULE: Exclude Customer 1 items unless the user IS Customer 1
  ORDER BY 
    CASE WHEN T1.customer_id = [CUSTOMER_ID] THEN 0 ELSE 1 END,
    T1.item_name
  LIMIT 23 OFFSET 0;

QUERY TEMPLATE (General):
SELECT DISTINCT item_name, item_category, item_price, item_taste, item_special, customer_id
FROM samsgriddle_menu
WHERE [condition]
ORDER BY item_name
LIMIT 23 OFFSET 0;

RESPONSE FORMAT (MANDATORY):
Final Answer:
[
  {"item_name": "string", "item_category": "string", "item_price": number, "item_taste": "string", "item_special": "string", "customer_id": number}
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