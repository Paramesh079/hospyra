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

KEYWORD & SEMANTIC MAPPING:
If the user uses specific keywords, use these rules to generate the query:
- "egg" -> Map to 'Non-Vegetarian' category and search for 'egg' in item_name.
- "chicken", "meat", "mutton", "fish", "seafood" -> Map to 'Non-Vegetarian' category.
- "paneer", "cheese", "veg", "vegetarian" -> Map to 'Vegetarian' category.
- "vegan" -> Map to 'Vegan' category.
- "drink", "juice", "coffee", "tea", "beverage", "mocktail" -> Map to 'Beverage' category.
- "spicy", "hot", "chilli" -> Filter by item_taste = 'Spicy'
- "sweet" -> Filter by item_taste = 'Sweet'
- "light" -> Filter by item_quantity = 'Light'
- "heavy" -> Filter by item_quantity = 'Heavy'
- "special", "chef special" -> Filter by item_special = 'Chef Special'
- "premium" -> Filter by item_special = 'Premium'

CUSTOMER PREFERENCE SUPPORT:
If the user provides a CUSTOMER ID (e.g., "customer 10", "recommend for id 5", or JUST A NUMBER like "1"):
- Identify the customer_id from the input.
- If the input is ONLY a number (e.g., "1"), treat it as "recommend for customer_id 1".
- The goal is to recommend items based on THAT customer's preference
- Use a SELF-JOIN logic:
  1. Find the preference (item_category and item_taste) of the customer with the given ID
  2. Recommend OTHER items that match this category and taste
- SQL Pattern:
  ```sql
  SELECT T1.item_name, T1.item_category, T1.item_special, T1.customer_id
  FROM samsgriddle_menu AS T1
  JOIN samsgriddle_menu AS T2 ON T2.customer_id = [CUSTOMER_ID]
  WHERE T1.item_category = T2.item_category 
  AND T1.item_taste = T2.item_taste
  AND (T1.customer_id != 1 OR T2.customer_id = 1) -- PRIVACY RULE: Exclude Customer 1 items unless the user IS Customer 1
  ORDER BY 
    CASE WHEN T1.customer_id = [CUSTOMER_ID] THEN 0 ELSE 1 END, -- Prioritize the customer's own item
    T1.item_name
  LIMIT 23;
  ```

MULTI-KEYWORD SUPPORT:
If the user provides MULTIPLE keywords (separated by commas, spaces, or other delimiters):
- Extract all keywords from the input
- PRIMARY BEHAVIOR: Return items containing ALL keywords in their name (use AND logic in WHERE clause)
- FALLBACK: If no items contain ALL keywords, then return items matching ANY keyword (use OR logic)
- Order by TIERED RELEVANCE:
  * Priority 1 (HIGHEST): Items containing ALL keywords in their name
  * Priority 2: Items containing ANY single keyword in their name
  * Priority 3 (LOWEST): Items matching only by category or attributes

CRITICAL RULES:
1. Return ONLY the SQL query.
2. The query must be a SELECT statement.
3. ALWAYS use ILIKE for case-insensitive search on the 'item_name' column.
4. Correct spelling mistakes in food names (e.g., "panner" -> "paneer").
5. For multiple keywords, PRIORITIZE items with ALL keywords by using AND conditions in WHERE clause.
6. ORDER BY TIERED RELEVANCE using CASE statements to ensure items with ALL keywords appear FIRST:
   - Priority 1 (value 1): Items containing ALL keywords in item_name
   - Priority 2 (value 2): Items containing ANY keyword in item_name
   - Priority 3 (value 3): Category/attribute matches only
   - Within each tier, order alphabetically by item_name
7. Limit results to 23.
8. NO explanations, markdown, or analysis outside of the SQL code block.
9. Use column names: item_category, item_name, item_price (not category, item, price)

Example request: "cheese soup"
Example response (ONLY items with BOTH "cheese" AND "soup"):
```sql
SELECT item_name, item_category, item_price, item_taste, item_special FROM samsgriddle_menu 
WHERE item_name ILIKE '%cheese%' AND item_name ILIKE '%soup%'
ORDER BY item_name
LIMIT 23;
```
Expected results:
- "Broccoli Cheddar Cheese Soup"
- "Jalapeno Cheese Soup"
(Only items containing BOTH "cheese" AND "soup" in the name)

Example request: "chicken pizza"
Example response (ONLY items with BOTH "chicken" AND "pizza"):
```sql
SELECT item_name, item_category, item_price, item_taste, item_special FROM samsgriddle_menu 
WHERE item_name ILIKE '%chicken%' AND item_name ILIKE '%pizza%'
ORDER BY item_name
LIMIT 23;
```
Expected results:
- "BBQ Chicken Pizza"
- "Grilled Chicken Pizza"
(Only items containing BOTH "chicken" AND "pizza" in the name)

Example request: "paneer tikka"
Example response (ONLY items with BOTH "paneer" AND "tikka"):
```sql
SELECT item_name, item_category, item_price, item_taste, item_special FROM samsgriddle_menu 
WHERE item_name ILIKE '%paneer%' AND item_name ILIKE '%tikka%'
ORDER BY item_name
LIMIT 23;
```
Expected results:
- "Paneer Tikka"
(Only items containing BOTH "paneer" AND "tikka" in the name)

Example request: "spicy chicken"
Example response (filter by attribute):
```sql
SELECT item_name, item_category, item_price, item_taste, item_special FROM samsgriddle_menu 
WHERE (item_name ILIKE '%chicken%' OR item_category = 'Non-Vegetarian') AND item_taste = 'Spicy'
ORDER BY item_name
LIMIT 23;
```

Example request: "recommend for customer 12"
Example response (based on customer 12's preference):
```sql
SELECT T1.item_name, T1.item_category, T1.item_special, T1.customer_id
FROM samsgriddle_menu AS T1
JOIN samsgriddle_menu AS T2 ON T2.customer_id = 12
WHERE T1.item_category = T2.item_category 
AND T1.item_taste = T2.item_taste
ORDER BY 
  CASE WHEN T1.customer_id = 12 THEN 0 ELSE 1 END,
  T1.item_name
LIMIT 23;
```

Example request: "1"
Example response (treats "1" as customer_id 1):
```sql
SELECT T1.item_name, T1.item_category, T1.item_special, T1.customer_id
FROM samsgriddle_menu AS T1
JOIN samsgriddle_menu AS T2 ON T2.customer_id = 1
WHERE T1.item_category = T2.item_category 
AND T1.item_taste = T2.item_taste
AND (T1.customer_id != 1 OR T2.customer_id = 1) -- PRIVACY RULE: Exclude Customer 1 items unless the user IS Customer 1
ORDER BY 
  CASE WHEN T1.customer_id = 1 THEN 0 ELSE 1 END,
  T1.item_name
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

