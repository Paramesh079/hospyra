import json
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_ollama import OllamaLLM
from langchain_core.output_parsers import JsonOutputParser
from db import engine

# LLM
print("[LOG] Initializing Ollama LLM with model: ministral-3:3b")
llm = OllamaLLM(
    model="ministral-3:3b",
    temperature=0
)
print("[LOG] LLM initialized successfully")

# Connect DB
print("[LOG] Connecting to database...")
db = SQLDatabase(
    engine,
    include_tables=["menu"]
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


def query_menu(user_prompt: str):
    """
    Converts user prompt into SQL and executes it with ministral-3b optimizations
    """
    print(f"\n[LOG] query_menu() called with prompt: {user_prompt}")
    
    system_prompt = """You are a LangChain SQL Agent optimized for ministral-3b.

DATABASE SCHEMA:
Table: menu
Columns: item, category, price

CRITICAL RULES FOR MINISTRAL-3B:
1. ALWAYS add LIMIT 23 and OFFSET 0 to queries
2. ALWAYS use SELECT DISTINCT when querying
3. ALWAYS add ORDER BY clause (ORDER BY item)
4. Return ONLY valid JSON after "Final Answer:"
5. NO explanations, markdown, or analysis



QUERY TEMPLATE:
SELECT DISTINCT item, category, price
FROM menu
WHERE [condition]
ORDER BY item
LIMIT 23 OFFSET 0;

RESPONSE FORMAT (MANDATORY):
Final Answer:
[
  {"item": "string", "category": "string", "price": number}
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
