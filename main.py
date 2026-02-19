from fastapi import FastAPI, HTTPException
from sql_agent import query_menu, semantic_search_similar_items

from sql_query_agent import  sql_query_menu


app = FastAPI(name="hospyra", version="1.0.0", title="ai_menu_recommender", description="AI Menu Recommender for Hospyra")

# @app.post("/query")
# def run_query(prompt: str):
#     return {
#         "prompt": prompt,
#         "result": sql_query_menu(prompt)
#     }

# @app.post("/suggest")
# def suggest_items(item: str):
#     result = get_similar_items_llm(item)

#     if not result:
#         raise HTTPException(status_code=404, detail="Item not found")

#     return result

@app.get("/recommend",tags=["ai-menu"])
async def run_query(prompt: str):
    return {
        "prompt": prompt,
        "result": semantic_search_similar_items(prompt)
    }