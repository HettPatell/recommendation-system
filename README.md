# ⚡ Blinkit AI: Vector Embedding Recommendation Engine POC

A Proof of Concept (POC) demonstrating how quick-commerce platforms like **Blinkit** use **Dense Vector Embeddings** and **Cosine Similarity** to recommend matching, complementary, and frequently ordered products when a customer adds items to cart or places an order.

---

## 🚀 Live Demo & How to Run

The backend server is already running on `http://127.0.0.1:8000`.

To start it manually at any time:
```bash
cd C:\Users\ADMIN\.gemini\antigravity\scratch\blinkit-recommender
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Then open your browser at:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🧠 How the Vector Embedding System Works

### 1. High-Dimensional Product Vectorization
Every grocery item contains rich semantic metadata:
- Product title & brand (e.g., *Amul Salted Butter 100g*)
- Taxonomy & category (*Dairy, Bread & Eggs > Butter & Spreads*)
- Dietary, usage occasions, & tags (*toast companion, morning breakfast, baking, pav bhaji*)
- Co-occurrence & pairing associations (*bread, pav, paratha, eggs, jam*)

The metadata is transformed via **TF-IDF + Latent Semantic Analysis (Truncated SVD)** into a **24-dimensional dense semantic vector**:
$$\vec{v}_i \in \mathbb{R}^{24}, \quad \|\vec{v}_i\|_2 = 1.0$$

### 2. Multi-Item Order / Cart Vector Aggregation
When a customer orders multiple items $(p_1, p_2, \dots)$, the system creates an aggregate **Cart Centroid Vector** with a recency boost $w_i$:
$$\vec{v}_{\text{cart}} = \frac{\sum_{i \in \text{order}} w_i \vec{v}_i}{\left\|\sum_{i \in \text{order}} w_i \vec{v}_i\right\|_2}$$

### 3. Real-Time Cosine Similarity Search
Because all embeddings are $L_2$-normalized to unit length:
$$\text{Cosine Similarity}(\vec{v}_{\text{cart}}, \vec{v}_j) = \vec{v}_{\text{cart}} \cdot \vec{v}_j = \sum_{k=1}^{24} v_{\text{cart}, k} \cdot v_{j, k}$$

The Top-$K$ nearest neighbors with highest cosine scores are instantly ranked and displayed on the recommendation shelf.

### 4. Interactive 2D Vector Space Visualizer
Using **Principal Component Analysis (PCA)**, the 24-dimensional space is projected onto a 2D coordinate plane $(x, y) \in [-1, 1]$.
- Nodes represent products colored by category clusters.
- When an item is added or ordered, the Cart Vector $\vec{v}_{\text{cart}}$ appears as a pulsing gold star node.
- Vectors shoot out to the nearest recommendations with real-time distance and match percentages.

---

## 📁 Project Architecture

```
blinkit-recommender/
│
├── data/
│   └── catalog.json          # 36 realistic Blinkit grocery items with pricing, tags & pairings
│
├── engine.py                 # Vector embedding generator, LSA, L2-norm, cosine similarity & PCA
├── main.py                   # FastAPI backend server with REST APIs
├── test_api.py               # Automated verification test script
│
└── static/
    ├── index.html            # Blinkit-themed UI with 10-minute delivery header & Vector Lab
    ├── style.css             # Authentic Blinkit colors (#f8cb46, #0c831f), responsive card grid
    └── app.js                # Frontend state, HTML5 Canvas vector visualizer, cart drawer & order flow
```

---

## 🔌 API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `GET /api/products` | GET | List all products with optional `?category=` filter |
| `GET /api/categories` | GET | Returns available categories and product counts |
| `POST /api/recommend` | POST | Takes `{ ordered_ids: ["p2"], top_k: 6 }` and returns nearest vector neighbors |
| `GET /api/vector-map` | GET | Returns 2D coordinates of all items for the Canvas map |
| `GET /api/inspect/{id}` | GET | Returns detailed 24-D embedding weights for a specific product |
| `POST /api/order/simulate` | POST | Simulates placing an order and returns post-order quick suggestions |
