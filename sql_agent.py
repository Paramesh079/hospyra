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
    
    system_prompt = """
                  You are a PostgreSQL Query Generator for a restaurant ordering system.

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

                  KEYWORD & SEMANTIC MAPPING:
                  - "veg", "vegetarian" -> Filter by menu_items.is_vegetarian = true
                  - "vegan" -> Filter by menu_items.is_vegan = true
                  - "spicy" -> Filter by menu_items.spice_level >= 3
                  - "mild" -> Filter by menu_items.spice_level <= 1
                  - Search by name: Use ILIKE on menu_items.name
                  - Search by category: Join with menu_categories and filter by menu_categories.name

                  CUSTOMER RECOMMENDATION SUPPORT:
                  If the user provides a CUSTOMER/USER ID (e.g., "customer 10" or just "1"):
                  - The goal is to recommend items based on the user's historical orders considering:
                    1. CATEGORY: Match the category of their most recently ordered items.
                    2. SPICE LEVEL: Match the spice_level of their ordered items.
                    3. KEYWORDS: Find items with similar keywords in 'name' or 'description'.
                  - SQL Logic Strategy:
                    - Join 'users', 'orders', 'order_items', and 'menu_items' to find the user's preferences.
                    - Recommend other items that share these attributes.
                  - Example SQL for multi-attribute matching:
                    ```sql
                    WITH last_ordered_items AS (
                        SELECT mi.category_id, mi.spice_level, mi.name, mi.description
                        FROM menu_items mi
                        JOIN order_items oi ON mi.id = oi.menu_item_id
                        JOIN orders o ON oi.order_id = o.id
                        WHERE o.user_id = [USER_ID]
                        ORDER BY o.created_at DESC
                        LIMIT 30
                    )
                    SELECT DISTINCT mi.name, mc.name AS category, mi.price, mi.spice_level
                    FROM menu_items mi
                    JOIN menu_categories mc ON mi.category_id = mc.id
                    WHERE (
                        mi.category_id IN (SELECT category_id FROM last_ordered_items)
                        OR mi.spice_level IN (SELECT spice_level FROM last_ordered_items)
                        OR EXISTS (
                            SELECT 1 FROM last_ordered_items loi 
                            WHERE mi.description ILIKE '%' || loi.name || '%' 
                            OR mi.name ILIKE '%' || loi.name || '%'
                        )
                    )
                    AND mi.id NOT IN (
                        SELECT menu_item_id FROM order_items oi2
                        JOIN orders o2 ON oi2.order_id = o2.id
                        WHERE o2.user_id = [USER_ID]
                    )
                    ORDER BY mi.name
                    LIMIT 30;
                    ```

                  CRITICAL RULES:
                  1. Return ONLY the SQL query.
                  2. ALWAYS use JOINs to get category names or filter by user history.
                  3. ALWAYS use ILIKE for case-insensitive search on 'name' columns.
                  4. Limit results to 30.
                  5. NO explanations, markdown, or analysis outside of the SQL code block.
                  6. Use correct table and column names as defined above.

                  Example search: "cheese pizza"
                  ```sql
                  SELECT mi.name, mc.name as category, mi.price 
                  FROM menu_items mi 
                  JOIN menu_categories mc ON mi.category_id = mc.id
                  WHERE mi.name ILIKE '%cheese%' AND mi.name ILIKE '%pizza%'
                  LIMIT 30;
                  ```"""
                
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

