from fastapi import FastAPI, HTTPException
from sql_agent import query_menu

from sql_query_agent import  sql_query_menu


app = FastAPI()

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

@app.post("/recommend")
def run_query(prompt: str):
    return {
        "prompt": prompt,
        "result": query_menu(prompt)
    }