import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from engine import VectorRecommenderEngine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "catalog.json")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(
    title="Blinkit Vector Embedding Recommendation Engine POC",
    description="Quick-commerce recommendation system powered by dense vector embeddings and cosine similarity.",
    version="1.0.0"
)

# Initialize Vector Recommender Engine
engine = VectorRecommenderEngine(catalog_path=DATA_PATH, embedding_dim=24)

# Models
class RecommendRequest(BaseModel):
    ordered_ids: List[str]
    top_k: Optional[int] = 6
    exclude_ordered: Optional[bool] = True

class OrderSimulationRequest(BaseModel):
    items: List[str]
    customer_name: Optional[str] = "Customer"
    address: Optional[str] = "Flat 402, Green Glen Layout, Bengaluru"

@app.get("/")
def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Blinkit Recommender Backend Running. Frontend index.html not yet found."}

@app.get("/api/products")
def get_products(category: Optional[str] = Query(None, description="Filter by category")):
    return {
        "success": True,
        "count": len(engine.get_all_products(category)),
        "products": engine.get_all_products(category)
    }

@app.get("/api/categories")
def get_categories():
    return {
        "success": True,
        "categories": engine.get_categories()
    }

@app.post("/api/recommend")
def get_recommendations(req: RecommendRequest):
    result = engine.recommend_for_order(
        ordered_ids=req.ordered_ids,
        top_k=req.top_k or 6,
        exclude_ordered=req.exclude_ordered if req.exclude_ordered is not None else True
    )
    return {
        "success": True,
        "data": result
    }

@app.get("/api/vector-map")
def get_vector_map():
    return {
        "success": True,
        "data": engine.get_vector_map()
    }

@app.get("/api/inspect/{product_id}")
def inspect_product(product_id: str):
    res = engine.inspect_product(product_id)
    if not res:
        raise HTTPException(status_code=404, detail="Product not found")
    return {
        "success": True,
        "data": res
    }

@app.post("/api/order/simulate")
def simulate_order(req: OrderSimulationRequest):
    if not req.items:
        raise HTTPException(status_code=400, detail="Cannot place order with empty cart")

    recs = engine.recommend_for_order(
        ordered_ids=req.items,
        top_k=4,
        exclude_ordered=True
    )

    ordered_items_meta = [engine.product_map[pid] for pid in req.items if pid in engine.product_map]
    total_amount = sum(item["price"] for item in ordered_items_meta)

    return {
        "success": True,
        "order_id": f"ORD-BLK-{os.urandom(3).hex().upper()}",
        "delivery_time": "8-10 mins",
        "total_amount": total_amount,
        "ordered_count": len(req.items),
        "ordered_items": ordered_items_meta,
        "post_order_recommendations": recs["recommendations"],
        "cart_vector_snippet": recs["cart_vector_snippet"],
        "message": "Order placed successfully! Delivery partner arriving in 9 mins."
    }

# Mount static folder
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    print("[Server] Starting Blinkit Vector Recommender on http://127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
