import json
import os
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD, PCA
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity

class VectorRecommenderEngine:
    """
    Production-grade Vector Embedding Recommendation Engine for Quick-Commerce (Blinkit style).
    Transforms product metadata, catalog taxonomies, usage occasions, and pairing graph
    into dense L2-normalized vectors and computes cosine similarity in real time.
    """

    def __init__(self, catalog_path: str, embedding_dim: int = 24):
        self.catalog_path = catalog_path
        self.embedding_dim = embedding_dim
        self.products: List[Dict[str, Any]] = []
        self.product_map: Dict[str, Dict[str, Any]] = {}
        self.embeddings: np.ndarray = np.array([])
        self.pca_2d: np.ndarray = np.array([])
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.svd: Optional[TruncatedSVD] = None
        self.pca: Optional[PCA] = None

        self._load_and_index()

    def _load_and_index(self):
        if not os.path.exists(self.catalog_path):
            raise FileNotFoundError(f"Catalog file not found at {self.catalog_path}")

        with open(self.catalog_path, "r", encoding="utf-8") as f:
            self.products = json.load(f)

        for i, prod in enumerate(self.products):
            prod["catalog_index"] = i
            self.product_map[prod["id"]] = prod

        has_precomputed = len(self.products) > 0 and all("embedding" in p for p in self.products)
        if has_precomputed:
            self.embeddings = normalize(np.array([p["embedding"] for p in self.products], dtype=np.float32), norm="l2")
            self.pca = PCA(n_components=2, random_state=42)
            coords_2d = self.pca.fit_transform(self.embeddings)
            max_abs = np.max(np.abs(coords_2d)) if np.max(np.abs(coords_2d)) > 0 else 1.0
            self.pca_2d = coords_2d / max_abs
            actual_dims = self.embeddings.shape[1]
        else:
            # Construct rich semantic contextual documents
            corpus = []
            for p in self.products:
                pairings_str = " ".join(p.get("pairings", [])) * 3
                tags_str = " ".join(p.get("tags", [])) * 2
                doc = (
                    f"{p['name']} {p['brand']} {p['category']} {p['subcategory']} "
                    f"{tags_str} {pairings_str} {p.get('description', '')}"
                )
                corpus.append(doc)

            # 1. TF-IDF feature extraction
            self.vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                sublinear_tf=True,
                stop_words="english",
                min_df=1
            )
            tfidf_matrix = self.vectorizer.fit_transform(corpus)

            # 2. Dense Latent Semantic Analysis (Truncated SVD)
            actual_dims = min(self.embedding_dim, tfidf_matrix.shape[1] - 1, len(corpus) - 1)
            self.svd = TruncatedSVD(n_components=actual_dims, random_state=42)
            dense_vectors = self.svd.fit_transform(tfidf_matrix)

            # 3. L2 Normalization (so dot product equals cosine similarity)
            self.embeddings = normalize(dense_vectors, norm="l2")

            # 4. 2D PCA Projection
            self.pca = PCA(n_components=2, random_state=42)
            coords_2d = self.pca.fit_transform(self.embeddings)
            max_abs = np.max(np.abs(coords_2d)) if np.max(np.abs(coords_2d)) > 0 else 1.0
            self.pca_2d = coords_2d / max_abs

        # Store vector representations in product metadata
        for i, p in enumerate(self.products):
            p["vector_snippet"] = [round(float(v), 3) for v in self.embeddings[i][:8]]
            p["coords_2d"] = {
                "x": round(float(self.pca_2d[i, 0]), 3),
                "y": round(float(self.pca_2d[i, 1]), 3)
            }

        print(f"[VectorEngine] Indexed {len(self.products)} products into {actual_dims}-dimensional vector space.")

    def get_all_products(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        if not category or category.lower() == "all":
            return self.products
        return [p for p in self.products if p.get("category", "").lower() == category.lower()]

    def get_categories(self) -> List[Dict[str, Any]]:
        counts = {}
        for p in self.products:
            cat = p.get("category", "General")
            counts[cat] = counts.get(cat, 0) + 1
        return [{"name": cat, "count": count} for cat, count in counts.items()]

    def compute_cart_vector(self, ordered_ids: List[str]) -> np.ndarray:
        """
        Calculates aggregate Cart Vector as normalized weighted sum of item vectors.
        Most recent item receives a recency weight boost.
        """
        valid_indices = []
        weights = []
        for idx, pid in enumerate(ordered_ids):
            if pid in self.product_map:
                c_idx = self.product_map[pid]["catalog_index"]
                valid_indices.append(c_idx)
                # Boost most recently added item slightly
                weight = 1.3 if idx == len(ordered_ids) - 1 else 1.0
                weights.append(weight)

        if not valid_indices:
            # Fallback to zero vector
            return np.zeros((self.embeddings.shape[1],))

        vecs = self.embeddings[valid_indices]
        weights = np.array(weights).reshape(-1, 1)
        cart_vec = np.sum(vecs * weights, axis=0, keepdims=True)
        return normalize(cart_vec, norm="l2")[0]

    def recommend_for_order(
        self,
        ordered_ids: List[str],
        top_k: int = 6,
        exclude_ordered: bool = True
    ) -> Dict[str, Any]:
        """
        Core Recommendation Method:
        Given an order or cart (list of product IDs), computes the user order vector,
        finds nearest neighbors in latent vector space using Cosine Similarity,
        and provides transparent mathematical explanations.
        """
        if not ordered_ids:
            # Fallback to popular staples
            popular = sorted(self.products, key=lambda x: x.get("rating", 0), reverse=True)[:top_k]
            popular_recs = []
            for p in popular:
                p_copy = dict(p)
                p_copy["match_percentage"] = int(p_copy.get("rating", 4.8) * 20)
                p_copy["similarity_score"] = 0.95
                p_copy["primary_reason"] = "Popular Daily Staple (Trending)"
                p_copy["all_reasons"] = ["Frequently ordered daily essential"]
                popular_recs.append(p_copy)
            return {
                "recommendations": popular_recs,
                "cart_vector_snippet": [],
                "cart_coords_2d": {"x": 0.0, "y": 0.0},
                "ordered_products": [],
                "mode": "trending_fallback"
            }

        ordered_products = [self.product_map[pid] for pid in ordered_ids if pid in self.product_map]
        cart_vector = self.compute_cart_vector(ordered_ids)

        # 2D projection of the cart vector
        cart_coords_raw = self.pca.transform(cart_vector.reshape(1, -1))[0]
        max_abs = np.max(np.abs(self.pca_2d)) if np.max(np.abs(self.pca_2d)) > 0 else 1.0
        cart_coords_2d = {
            "x": round(float(cart_coords_raw[0] / max_abs), 3),
            "y": round(float(cart_coords_raw[1] / max_abs), 3)
        }

        # Calculate Cosine Similarities against ALL items
        # Since both cart_vector and embeddings are L2 normalized, dot product == cosine similarity
        cosine_sims = np.dot(self.embeddings, cart_vector)

        ranked_indices = np.argsort(cosine_sims)[::-1]

        ordered_set = set(ordered_ids) if exclude_ordered else set()
        recommendations = []

        # Collect ordered keywords & tags for reasoning
        ordered_tags = set()
        ordered_pairings = set()
        for op in ordered_products:
            ordered_tags.update(t.lower() for t in op.get("tags", []))
            ordered_pairings.update(p.lower() for p in op.get("pairings", []))

        for idx in ranked_indices:
            prod = self.products[idx]
            pid = prod["id"]

            if pid in ordered_set:
                continue

            raw_cos = float(cosine_sims[idx])

            # Percentage match calculation:
            # Transform cosine [-1, 1] into positive affinity percentage
            # Cosine > 0.8 is extremely strong in high-dim space
            match_pct = max(15, min(99, int((raw_cos + 1.0) / 2.0 * 100)))

            # Semantic reasoning
            reasons = []
            prod_tags = set(t.lower() for t in prod.get("tags", []))
            prod_pairings = set(p.lower() for p in prod.get("pairings", []))

            # Check pairing match
            shared_pairings = ordered_pairings.intersection(prod_tags) or prod_pairings.intersection(ordered_tags)
            if shared_pairings:
                reasons.append(f"Frequently paired with your ordered item ({', '.join(list(shared_pairings)[:2])})")

            # Check category match
            if any(op.get("category") == prod.get("category") for op in ordered_products):
                reasons.append(f"Matches category '{prod['category']}'")

            if not reasons:
                reasons.append(f"Strong semantic vector correlation ({raw_cos:+.2f} cos similarity)")

            rec_item = dict(prod)
            rec_item["similarity_score"] = round(raw_cos, 4)
            rec_item["match_percentage"] = match_pct
            rec_item["primary_reason"] = reasons[0]
            rec_item["all_reasons"] = reasons
            recommendations.append(rec_item)

            if len(recommendations) >= top_k:
                break

        return {
            "recommendations": recommendations,
            "cart_vector_snippet": [round(float(v), 3) for v in cart_vector[:8]],
            "cart_coords_2d": cart_coords_2d,
            "ordered_products": ordered_products,
            "vector_dimension": int(self.embeddings.shape[1]),
            "mode": "vector_embedding_cosine"
        }

    def get_vector_map(self) -> Dict[str, Any]:
        """
        Returns all catalog items with their 2D coordinates for interactive vector space canvas.
        """
        items = []
        for p in self.products:
            items.append({
                "id": p["id"],
                "name": p["name"],
                "category": p["category"],
                "icon": p.get("icon", "📦"),
                "color": p.get("color", "#fff"),
                "coords": p["coords_2d"],
                "vector_snippet": p["vector_snippet"]
            })
        return {
            "total_items": len(items),
            "dimensions": int(self.embeddings.shape[1]),
            "items": items
        }

    def inspect_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns detailed vector breakdown for a single product.
        """
        if product_id not in self.product_map:
            return None
        prod = self.product_map[product_id]
        idx = prod["catalog_index"]
        vec = self.embeddings[idx]

        # Find nearest 3 neighbors
        sims = np.dot(self.embeddings, vec)
        top_indices = np.argsort(sims)[::-1][1:5]
        neighbors = []
        for n_idx in top_indices:
            neighbors.append({
                "id": self.products[n_idx]["id"],
                "name": self.products[n_idx]["name"],
                "similarity": round(float(sims[n_idx]), 3),
                "icon": self.products[n_idx]["icon"]
            })

        return {
            "product": prod,
            "full_vector": [round(float(v), 4) for v in vec],
            "norm": round(float(np.linalg.norm(vec)), 4),
            "nearest_neighbors": neighbors
        }
