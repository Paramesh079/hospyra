from sqlalchemy import text
from db import engine
from langchain_community.llms import Ollama

llm = Ollama(
    model="ministral-3:3b",
    temperature=0
)

def get_similar_items_llm(item_name: str, limit: int = 5):
    with engine.connect() as conn:

        # 1️⃣ Get base item + category
        base = conn.execute(
            text("""
                SELECT item, category
                FROM menu
                WHERE item = :item
            """),
            {"item": item_name}
        ).fetchone()

        if not base:
            return None

        base_item, category = base

        # 2️⃣ Get candidate items from SAME category
        rows = conn.execute(
            text("""
                SELECT item
                FROM menu
                WHERE category = :category
                  AND item != :item
            """),
            {
                "category": category,
                "item": base_item
            }
        ).fetchall()

        candidates = [r[0] for r in rows]

        if not candidates:
            return {
                "base_item": base_item,
                "category": category,
                "suggestions": []
            }

        # 3️⃣ Ask LLM to choose similar items
        prompt = f"""
You are a food recommendation expert.

Base food item:
{base_item}

Food items in the same category:
{', '.join(candidates)}

Task:
Select the {limit} most similar food items to "{base_item}".
Return ONLY a comma-separated list of food names.
Do not explain.
"""

        response = llm.invoke(prompt)

        # 4️⃣ Parse LLM response
        suggested_items = [
            item.strip()
            for item in response.split(",")
            if item.strip()
        ][:limit]

        return {
            "base_item": base_item,
            "category": category,
            "suggestions": suggested_items
        }
