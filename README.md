# ⚡ Blinkit AI: Vector Embedding Recommendation Engine POC

A Proof of Concept (POC) demonstrating how quick-commerce platforms like **Blinkit** use **Dense Vector Embeddings** and **Cosine Similarity** to recommend matching, complementary, and frequently ordered products when a customer adds items to cart or places an order.

---

## 🚀 Live Local Demo

The backend server runs locally on:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

To run it locally at any time:
```bash
cd C:\Users\ADMIN\.gemini\antigravity\scratch\blinkit-recommender
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

---

## ☁️ Deploy on Vercel

This project is configured and ready for 1-click deployment on **Vercel** with:
- `vercel.json` (rewrites `/api/*` to serverless Python function)
- `api/index.py` (Vercel Serverless Function entry point)
- `public/` (Static frontend served via Vercel Edge CDN)
- `requirements.txt` (Python runtime dependencies)

### Method 1: Deploy with Vercel CLI (Fastest)

Open PowerShell / Terminal in this project directory and run:

```bash
cd C:\Users\ADMIN\.gemini\antigravity\scratch\blinkit-recommender
npx vercel
```

1. Log in to your Vercel account when prompted in the browser.
2. Confirm the project settings (press `Enter` for defaults).
3. Vercel will build and give you a live production URL (e.g. `https://blinkit-recommender.vercel.app`)!

To deploy straight to production later:
```bash
npx vercel --prod
```

---

### Method 2: Deploy with GitHub & Vercel Dashboard

1. Initialize a git repo and push to your GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of Blinkit Recommender POC"
   git remote add origin https://github.com/<your-username>/blinkit-recommender.git
   git push -u origin main
   ```
2. Go to [vercel.com/new](https://vercel.com/new).
3. Import your GitHub repository.
4. Leave all build settings as default (Vercel automatically detects `vercel.json` and `api/index.py`).
5. Click **Deploy**!

---

## 🧠 How the Vector Embedding System Works

1. **High-Dimensional Product Vectorization**:
   Every grocery item is transformed via **TF-IDF + Latent Semantic Analysis (Truncated SVD)** into a **24-dimensional dense semantic vector** ($\|\vec{v}_i\|_2 = 1.0$).
2. **Order / Cart Vector Aggregation**:
   When a customer adds multiple items, an aggregate normalized centroid vector $\vec{v}_{\text{cart}}$ is generated.
3. **Real-Time Cosine Similarity**:
   Because all vectors are unit length, cosine similarity is calculated via dot product:
   $$\text{Cosine Similarity}(\vec{v}_{\text{cart}}, \vec{v}_j) = \vec{v}_{\text{cart}} \cdot \vec{v}_j$$
4. **In-Cart Dynamic Recommendations**:
   The cart drawer features a **"Frequently Bought Together"** shelf that re-calculates nearest neighbors instantly whenever an item is added or removed.

---

## 📁 Project Architecture

```
blinkit-recommender/
│
├── api/
│   └── index.py              # Vercel Serverless Function entry point
│
├── data/
│   └── catalog.json          # 36 products with pricing, tags, pairings & precomputed vectors
│
├── public/                   # Static assets served via Vercel Edge CDN
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── static/                   # Static assets for local development
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── engine.py                 # Vector embedding generator & cosine similarity engine
├── main.py                   # FastAPI backend server
├── requirements.txt          # Python dependencies for Vercel
├── vercel.json               # Vercel routing configuration
└── .gitignore
```
