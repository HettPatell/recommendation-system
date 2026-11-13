// Blinkit Vector Embedding Recommendation Engine POC
// Client-side Application Logic

let state = {
  catalog: [],
  categories: [],
  cart: {}, // { productId: quantity }
  currentCategory: 'All',
  searchQuery: '',
  recommendations: [],
  cartVectorSnippet: []
};

// Fallback image in case of network issues
const FALLBACK_IMAGE = 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=400';

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
  await Promise.all([
    loadCategories(),
    loadProducts()
  ]);

  // Initial recommendation call (trending items)
  await updateRecommendations();
});

// API Calls
async function loadProducts(category = null) {
  try {
    const url = category && category !== 'All' 
      ? `/api/products?category=${encodeURIComponent(category)}`
      : '/api/products';
    const res = await fetch(url);
    const data = await res.json();
    if (data.success) {
      state.catalog = data.products;
      renderCatalog();
    }
  } catch (err) {
    console.error('Failed to load products:', err);
  }
}

async function loadCategories() {
  try {
    const res = await fetch('/api/categories');
    const data = await res.json();
    if (data.success) {
      state.categories = data.categories;
      renderCategories();
    }
  } catch (err) {
    console.error('Failed to load categories:', err);
  }
}

async function updateRecommendations() {
  const orderedIds = Object.keys(state.cart);
  try {
    const res = await fetch('/api/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ordered_ids: orderedIds,
        top_k: 6,
        exclude_ordered: true
      })
    });
    const data = await res.json();
    if (data.success) {
      state.recommendations = data.data.recommendations;
      state.cartVectorSnippet = data.data.cart_vector_snippet || [];
      renderRecommendations(data.data);
      renderCartRecommendations();
      renderCartVectorPreview();
    }
  } catch (err) {
    console.error('Failed to update recommendations:', err);
  }
}

// Category Filtering
function renderCategories() {
  const container = document.getElementById('categoryList');
  container.innerHTML = `<button class="cat-pill ${state.currentCategory === 'All' ? 'active' : ''}" onclick="filterCategory('All', this)">All Items</button>`;

  state.categories.forEach(cat => {
    const pill = document.createElement('button');
    pill.className = `cat-pill ${state.currentCategory === cat.name ? 'active' : ''}`;
    pill.textContent = `${cat.name} (${cat.count})`;
    pill.onclick = () => filterCategory(cat.name, pill);
    container.appendChild(pill);
  });
}

function filterCategory(category, buttonElement) {
  state.currentCategory = category;
  document.querySelectorAll('.cat-pill').forEach(btn => btn.classList.remove('active'));
  buttonElement.classList.add('active');
  renderCatalog();
}

function handleSearch() {
  const query = document.getElementById('searchInput').value.trim().toLowerCase();
  state.searchQuery = query;
  renderCatalog();
}

// Render Main Catalog with Real Images
function renderCatalog() {
  const container = document.getElementById('productGrid');
  const countLabel = document.getElementById('catalogItemCount');
  const titleLabel = document.getElementById('catalogTitle');

  let filtered = state.catalog;

  if (state.currentCategory !== 'All') {
    filtered = filtered.filter(p => p.category === state.currentCategory);
    titleLabel.textContent = state.currentCategory;
  } else {
    titleLabel.textContent = 'Explore Quick-Commerce Catalog';
  }

  if (state.searchQuery) {
    filtered = filtered.filter(p => 
      p.name.toLowerCase().includes(state.searchQuery) ||
      p.category.toLowerCase().includes(state.searchQuery) ||
      (p.tags && p.tags.some(t => t.toLowerCase().includes(state.searchQuery)))
    );
  }

  countLabel.textContent = `${filtered.length} products available`;

  container.innerHTML = filtered.map(prod => {
    const inCartQty = state.cart[prod.id] || 0;
    const buttonHtml = inCartQty > 0 
      ? `
        <div class="qty-stepper">
          <button class="stepper-btn" onclick="updateQty('${prod.id}', -1)">-</button>
          <span class="stepper-val">${inCartQty}</span>
          <button class="stepper-btn" onclick="updateQty('${prod.id}', 1)">+</button>
        </div>
      `
      : `
        <button class="btn-add-item" onclick="updateQty('${prod.id}', 1)">ADD</button>
      `;

    return `
      <div class="product-card" id="card-${prod.id}">
        <span class="prod-discount-tag">${prod.discount}</span>
        <div class="prod-image-wrap">
          <img src="${prod.image_url}" 
               alt="${prod.name}" 
               class="prod-img" 
               loading="lazy" 
               onerror="this.onerror=null; this.src='${FALLBACK_IMAGE}';">
        </div>
        <div class="prod-delivery-time">⚡ ${prod.delivery_time}</div>
        <div class="prod-title" title="${prod.name}">${prod.name}</div>
        <div class="prod-weight">${prod.weight}</div>
        <div class="prod-footer">
          <div class="price-group">
            <span class="price-main">₹${prod.price}</span>
            <span class="price-mrp">₹${prod.mrp}</span>
          </div>
          ${buttonHtml}
        </div>
      </div>
    `;
  }).join('');
}

// Render Top Recommendation Shelf with Real Images
function renderRecommendations(recData) {
  const container = document.getElementById('recommendationCards');
  const shelfHeading = document.getElementById('shelfHeading');
  const shelfSub = document.getElementById('shelfSub');

  const orderedCount = Object.keys(state.cart).length;
  if (orderedCount > 0) {
    const itemNames = Object.keys(state.cart)
      .map(id => state.catalog.find(p => p.id === id)?.name?.split(' ')[0] || '')
      .filter(Boolean)
      .slice(0, 3)
      .join(' & ');
    shelfHeading.textContent = `Frequently Ordered With ${itemNames} (Vector Match)`;
    shelfSub.textContent = `Matching ${orderedCount} item(s) in 24-dimensional semantic embedding space. Showing nearest neighbors.`;
  } else {
    shelfHeading.textContent = `Frequently Ordered Together (Vector Embeddings)`;
    shelfSub.textContent = `Add items to cart or order to see real-time Cosine Similarity recommendations update automatically!`;
  }

  container.innerHTML = state.recommendations.map(rec => {
    const matchPct = rec.match_percentage || 95;
    const reason = rec.primary_reason || "Popular Daily Staple (Trending)";
    return `
      <div class="rec-card">
        <div class="rec-affinity-badge">
          <span>🎯</span> ${matchPct}% MATCH
        </div>
        <div class="rec-img-wrap">
          <img src="${rec.image_url}" 
               alt="${rec.name}" 
               class="rec-img" 
               loading="lazy" 
               onerror="this.onerror=null; this.src='${FALLBACK_IMAGE}';">
        </div>
        <div class="rec-time">⚡ ${rec.delivery_time}</div>
        <div class="rec-name" title="${rec.name}">${rec.name}</div>
        <div class="rec-weight">${rec.weight}</div>
        <div class="rec-reason" title="${reason}">
          ${reason}
        </div>
        <div class="rec-footer">
          <span class="rec-price">₹${rec.price}</span>
          <button class="btn-add-rec" onclick="updateQty('${rec.id}', 1)">
            + ADD
          </button>
        </div>
      </div>
    `;
  }).join('');
}

// Render IN-CART Recommendations (Inside Cart Pop-up)
function renderCartRecommendations() {
  const container = document.getElementById('cartRecGrid');
  const title = document.getElementById('cartRecTitle');
  const sub = document.getElementById('cartRecSub');

  if (!container) return;

  const orderedCount = Object.keys(state.cart).length;
  if (orderedCount > 0) {
    title.textContent = "Frequently Bought Together";
    sub.textContent = "Matching items with your cart via Vector Embeddings";
  } else {
    title.textContent = "Popular Grocery Staples";
    sub.textContent = "High-affinity daily essentials";
  }

  // Display top 4 matching recommendations in cart
  const items = state.recommendations.slice(0, 4);

  if (items.length === 0) {
    container.innerHTML = '<p style="font-size:0.8rem; color:#64748b;">No extra recommendations available.</p>';
    return;
  }

  container.innerHTML = items.map(item => {
    const matchPct = item.match_percentage || 95;
    return `
    <div class="cart-rec-card">
      <div class="cart-rec-left">
        <div class="cart-rec-thumb">
          <img src="${item.image_url}" 
               alt="${item.name}" 
               class="cart-rec-img" 
               loading="lazy" 
               onerror="this.onerror=null; this.src='${FALLBACK_IMAGE}';">
        </div>
        <div class="cart-rec-details">
          <div class="cart-rec-name" title="${item.name}">${item.name}</div>
          <div class="cart-rec-meta">
            <span>₹${item.price} • ${item.weight}</span>
            <span class="cart-rec-score">(${matchPct}% Match)</span>
          </div>
        </div>
      </div>
      <button class="btn-add-cart-rec" onclick="updateQty('${item.id}', 1)">
        + ADD
      </button>
    </div>
  `;
  }).join('');
}

// Cart State & Drawer Operations
function updateQty(productId, delta) {
  const current = state.cart[productId] || 0;
  const newQty = current + delta;

  if (newQty <= 0) {
    delete state.cart[productId];
  } else {
    state.cart[productId] = newQty;
  }

  renderCart();
  renderCatalog();
  updateRecommendations();
}

function renderCart() {
  const cartBadge = document.getElementById('cartCountBadge');
  const cartTotalHeader = document.getElementById('cartTotalHeader');
  const drawerCount = document.getElementById('drawerCartCount');
  const emptyState = document.getElementById('emptyCartState');
  const cartList = document.getElementById('cartItemsList');
  const cartFooter = document.getElementById('cartFooter');
  const cartVectorPreview = document.getElementById('cartVectorPreview');

  const itemIds = Object.keys(state.cart);
  const totalCount = Object.values(state.cart).reduce((a, b) => a + b, 0);

  let itemTotal = 0;
  itemIds.forEach(id => {
    const prod = state.catalog.find(p => p.id === id);
    if (prod) {
      itemTotal += prod.price * state.cart[id];
    }
  });

  const grandTotal = itemTotal > 0 ? itemTotal + 5 : 0; // ₹5 handling fee

  cartBadge.textContent = `${totalCount} item${totalCount === 1 ? '' : 's'}`;
  cartTotalHeader.textContent = `₹${grandTotal}`;
  drawerCount.textContent = totalCount;

  if (totalCount === 0) {
    emptyState.style.display = 'block';
    cartList.style.display = 'none';
    cartFooter.style.display = 'none';
    cartVectorPreview.style.display = 'none';
    return;
  }

  emptyState.style.display = 'none';
  cartList.style.display = 'flex';
  cartFooter.style.display = 'block';
  cartVectorPreview.style.display = 'block';

  cartList.innerHTML = itemIds.map(id => {
    const prod = state.catalog.find(p => p.id === id);
    if (!prod) return '';
    const qty = state.cart[id];
    return `
      <div class="cart-item-row">
        <div class="cart-item-info">
          <div class="cart-item-thumb">
            <img src="${prod.image_url}" 
                 alt="${prod.name}" 
                 class="cart-item-img" 
                 onerror="this.onerror=null; this.src='${FALLBACK_IMAGE}';">
          </div>
          <div>
            <div class="cart-item-title">${prod.name}</div>
            <div class="cart-item-price">₹${prod.price} × ${qty} = ₹${prod.price * qty}</div>
          </div>
        </div>
        <div class="qty-stepper">
          <button class="stepper-btn" onclick="updateQty('${prod.id}', -1)">-</button>
          <span class="stepper-val">${qty}</span>
          <button class="stepper-btn" onclick="updateQty('${prod.id}', 1)">+</button>
        </div>
      </div>
    `;
  }).join('');

  document.getElementById('billItemTotal').textContent = `₹${itemTotal}`;
  document.getElementById('billGrandTotal').textContent = `₹${grandTotal}`;
  document.getElementById('checkoutBtnTotal').textContent = `₹${grandTotal}`;
}

function renderCartVectorPreview() {
  const container = document.getElementById('cartVectorBars');
  if (!container) return;
  if (!state.cartVectorSnippet || state.cartVectorSnippet.length === 0) {
    container.innerHTML = '<span class="empty-hint" style="font-size:0.7rem; color:#94a3b8;">Add items to compute vector</span>';
    return;
  }

  container.innerHTML = state.cartVectorSnippet.map(val => {
    const height = Math.max(3, Math.min(22, Math.abs(val) * 22));
    const isNeg = val < 0;
    return `
      <div class="vec-bar-col" 
           style="height: ${height}px; background: ${isNeg ? '#ef4444' : '#0c831f'};" 
           title="Dimension weight: ${val}">
      </div>
    `;
  }).join('');
}

// Drawer Toggles
function toggleCartDrawer() {
  const drawer = document.getElementById('cartDrawer');
  const backdrop = document.getElementById('drawerBackdrop');
  drawer.classList.toggle('open');
  backdrop.classList.toggle('active');

  // When drawer opens, ensure recommendations are fresh
  if (drawer.classList.contains('open')) {
    renderCartRecommendations();
  }
}

// Order Simulation
async function simulateOrderPlacement() {
  const itemIds = Object.keys(state.cart);
  if (itemIds.length === 0) return;

  try {
    const res = await fetch('/api/order/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items: itemIds })
    });
    const data = await res.json();
    if (data.success) {
      document.getElementById('confirmedOrderId').textContent = data.order_id;
      renderPostOrderRecommendations(data.post_order_recommendations);

      // Close cart drawer & open order confirmation
      toggleCartDrawer();
      document.getElementById('orderModalBackdrop').classList.add('active');
    }
  } catch (err) {
    console.error('Order simulation error:', err);
  }
}

function renderPostOrderRecommendations(recs) {
  const container = document.getElementById('postOrderGrid');
  container.innerHTML = (recs || []).slice(0, 4).map(rec => `
    <div class="post-item-card">
      <div class="post-item-thumb">
        <img src="${rec.image_url}" 
             alt="${rec.name}" 
             class="post-item-img" 
             onerror="this.onerror=null; this.src='${FALLBACK_IMAGE}';">
      </div>
      <div class="post-item-name" title="${rec.name}">${rec.name}</div>
      <div class="post-item-sim">${rec.match_percentage}% Match</div>
      <button class="btn-post-add" onclick="quickAddPostOrder('${rec.id}')">+ ₹${rec.price}</button>
    </div>
  `).join('');
}

function quickAddPostOrder(productId) {
  updateQty(productId, 1);
  alert('Added item to your live order! Delivery partner notified.');
}

function closeOrderModal() {
  document.getElementById('orderModalBackdrop').classList.remove('active');
  state.cart = {};
  renderCart();
  renderCatalog();
  updateRecommendations();
}
