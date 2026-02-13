import os
import json
from sqlalchemy import text
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from db import engine

load_dotenv()

# LLM
model_name = os.getenv("OLLAMA_MODEL", "ministral-3:3b")
print(f"[LOG] Initializing Ollama LLM with model: {model_name}")
llm = OllamaLLM(
    model=model_name,
    temperature=0
)
print("[LOG] LLM initialized successfully")

def parse_sql_from_output(output: str):
    """
    Extract SQL query from LLM output
    """
    # Look for SQL between backticks if present
    if "```sql" in output:
        start_idx = output.find("```sql") + 6
        end_idx = output.find("```", start_idx)
        return output[start_idx:end_idx].strip()
    elif "```" in output:
        start_idx = output.find("```") + 3
        end_idx = output.find("```", start_idx)
        return output[start_idx:end_idx].strip()
    return output.strip()

def query_menu(user_prompt: str):
    """
    Converts user prompt into SQL query and executes it against PostgreSQL
    """
    print(f"\n[LOG] query_menu() called with prompt: {user_prompt}")
    
    system_prompt = """You are a PostgreSQL Query Generator.

TABLE SCHEMA:
Table: menu
Columns: 
- item (TEXT) - Name of the food item
- category (TEXT) - Values: 'Veg', 'Non-Veg', 'Beverages'
- price (NUMERIC)

KEYWORD & SEMANTIC MAPPING:
If the user uses specific keywords, use these rules to generate the query:
- "egg" -> Map to 'Non-Veg' category and search for 'egg' in item.
- "chicken", "meat", "mutton", "fish" -> Map to 'Non-Veg' category.
- "paneer", "cheese", "veg", "vegetarian" -> Map to 'Veg' category.
- "drink", "juice", "coffee", "tea", "beverage" -> Map to 'Beverages' category.

MULTI-KEYWORD SUPPORT:
If the user provides MULTIPLE keywords (separated by commas, spaces, or other delimiters):
- Extract all keywords from the input
- Search for items matching ANY of the keywords (use OR logic)
- Include category matches for each keyword
- Order by TIERED RELEVANCE:
  * Priority 1: Items containing ALL keywords in their name
  * Priority 2: Items containing ANY single keyword in their name
  * Priority 3: Items matching only by category

CRITICAL RULES:
1. Return ONLY the SQL query.
2. The query must be a SELECT statement.
3. ALWAYS use ILIKE for case-insensitive search on the 'item' column.
4. Correct spelling mistakes in food names (e.g., "panner" -> "paneer").
5. For multiple keywords, use OR conditions to match ANY keyword.
6. ORDER BY TIERED RELEVANCE using CASE statements:
   - Priority 1 (value 1): Items containing ALL keywords
   - Priority 2 (value 2): Items containing ANY keyword
   - Priority 3 (value 3): Category matches only
   - Within each tier, order alphabetically by item name
7. Limit results to 23.
8. NO explanations, markdown, or analysis outside of the SQL code block.

Example request: "egg chicken"
Example response:
```sql
SELECT item, category, price FROM menu 
WHERE item ILIKE '%egg%' OR item ILIKE '%chicken%' OR category = 'Non-Veg' 
ORDER BY 
  CASE 
    WHEN item ILIKE '%egg%' AND item ILIKE '%chicken%' THEN 1
    WHEN item ILIKE '%egg%' OR item ILIKE '%chicken%' THEN 2
    ELSE 3
  END,
  item
LIMIT 23;
```

Example request: "paneer, burger, pizza"
Example response:
```sql
SELECT item, category, price FROM menu 
WHERE item ILIKE '%paneer%' OR item ILIKE '%burger%' OR item ILIKE '%pizza%' OR category = 'Veg' 
ORDER BY 
  CASE 
    WHEN item ILIKE '%paneer%' AND item ILIKE '%burger%' AND item ILIKE '%pizza%' THEN 1
    WHEN item ILIKE '%paneer%' OR item ILIKE '%burger%' OR item ILIKE '%pizza%' THEN 2
    ELSE 3
  END,
  item
LIMIT 23;
```
"""
    final_prompt = system_prompt + "\n\nUser request: " + user_prompt
    print(f"[LOG] Invoking LLM for SQL Query generation...")
    
    try:
        response = llm.invoke(final_prompt)
        print(f"[LOG] LLM Response: {response}")
        
        sql_query = parse_sql_from_output(response)
        
        # Remove trailing semicolon if present as SQLAlchemy text() can be picky
        if sql_query.endswith(';'):
            sql_query = sql_query[:-1]
            
        print(f"[LOG] Executing SQL Query: {sql_query}")
        
        with engine.connect() as connection:
            result = connection.execute(text(sql_query))
            results = [dict(row) for row in result.mappings()]
            
        print(f"[LOG] Found {len(results)} results")
        return results

    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return {"error": "Internal Server Error", "details": str(e)}

