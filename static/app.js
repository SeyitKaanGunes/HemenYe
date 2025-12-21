const state = {
  role: null,
  restaurants: [],
  selected: null,
  menu: [],
  reviews: [],
  cart: {},
  ownerRestaurantId: null,
  ownerOrders: [],
  ownerMenu: [],
};

const fmtPrice = (value) =>
  new Intl.NumberFormat("tr-TR", {
    style: "currency",
    currency: "TRY",
    maximumFractionDigits: 0,
  }).format(value);

const els = {
  list: document.getElementById("restaurant-list"),
  name: document.getElementById("restaurant-name"),
  description: document.getElementById("restaurant-description"),
  rating: document.getElementById("restaurant-rating"),
  min: document.getElementById("restaurant-min"),
  time: document.getElementById("restaurant-time"),
  menuList: document.getElementById("menu-list"),
  menuHint: document.getElementById("menu-hint"),
  cartItems: document.getElementById("cart-items"),
  cartHint: document.getElementById("cart-hint"),
  cartTotal: document.getElementById("cart-total"),
  orderForm: document.getElementById("order-form"),
  orderStatus: document.getElementById("order-status"),
  orderSubmit: document.getElementById("order-submit"),
  reviewList: document.getElementById("review-list"),
  reviewForm: document.getElementById("review-form"),
  reviewStatus: document.getElementById("review-status"),
  reviewHint: document.getElementById("review-hint"),
  overlay: document.getElementById("role-overlay"),
  overlayCustomer: document.getElementById("overlay-customer"),
  overlayOwner: document.getElementById("overlay-owner"),
  roleCustomerBtn: document.getElementById("role-customer-btn"),
  roleOwnerBtn: document.getElementById("role-owner-btn"),
  customerView: document.getElementById("customer-view"),
  ownerView: document.getElementById("owner-view"),
  ownerSelect: document.getElementById("owner-restaurant-select"),
  ownerOrders: document.getElementById("owner-orders"),
  ownerOrdersHint: document.getElementById("owner-orders-hint"),
  ownerMenuList: document.getElementById("owner-menu-list"),
  ownerMenuHint: document.getElementById("owner-menu-hint"),
  ownerMenuForm: document.getElementById("owner-menu-form"),
  ownerMenuStatus: document.getElementById("owner-menu-status"),
  ownerItemName: document.getElementById("owner-item-name"),
  ownerItemCategory: document.getElementById("owner-item-category"),
  ownerItemPrice: document.getElementById("owner-item-price"),
  ownerItemDesc: document.getElementById("owner-item-desc"),
  ownerItemVegan: document.getElementById("owner-item-vegan"),
  custStatus: document.getElementById("cust-status"),
  ownStatus: document.getElementById("own-status"),
  custName: document.getElementById("cust-name"),
  custEmail: document.getElementById("cust-email"),
  custPass: document.getElementById("cust-pass"),
  ownName: document.getElementById("own-name"),
  ownEmail: document.getElementById("own-email"),
  ownPass: document.getElementById("own-pass"),
  custLoginBtn: document.getElementById("cust-login-btn"),
  ownLoginBtn: document.getElementById("own-login-btn"),
};

const scrollToList = () => {
  const list = document.getElementById("restaurant-list");
  list?.scrollIntoView({ behavior: "smooth", block: "start" });
};

document.getElementById("cta-start")?.addEventListener("click", scrollToList);

const setStatus = (element, message, isError = false) => {
  if (!element) return;
  element.textContent = message || "";
  element.style.color = isError ? "#b91c1c" : "#0f766e";
};

const toggleOverlay = (show) => {
  if (!els.overlay) return;
  els.overlay.classList.toggle("show", show);
};

const setActiveRoleButton = (role) => {
  if (els.roleCustomerBtn && els.roleOwnerBtn) {
    els.roleCustomerBtn.classList.toggle("active", role === "customer");
    els.roleOwnerBtn.classList.toggle("active", role === "owner");
  }
};

const ensureOwnerRestaurant = () => {
  if (state.ownerRestaurantId || state.restaurants.length === 0) return;
  state.ownerRestaurantId = state.restaurants[0].id;
};

const renderRestaurants = () => {
  els.list.innerHTML = "";
  state.restaurants.forEach((restaurant) => {
    const card = document.createElement("div");
    card.className = "restaurant-card";
    if (state.selected?.id === restaurant.id) {
      card.classList.add("active");
    }
    card.innerHTML = `
      <div class="title">
        <div class="name">${restaurant.name}</div>
        <span class="pill">${restaurant.cuisine}</span>
      </div>
      <div class="meta-small">
        <span>⭐ ${restaurant.avg_rating ?? "-"} (${restaurant.review_count} yorum)</span>
        <span>${restaurant.delivery_time}</span>
        <span>Min ${fmtPrice(restaurant.min_order)}</span>
      </div>
      <p>${restaurant.description}</p>
    `;
    card.addEventListener("click", () => selectRestaurant(restaurant.id));
    els.list.appendChild(card);
  });
};

const updateHeader = (restaurant) => {
  if (!restaurant) {
    els.name.textContent = "Önce bir restoran seçin";
    els.description.textContent = "Menü, yorum ve sipariş için listeden seçim yapın.";
    els.rating.textContent = "-";
    els.min.textContent = "-";
    els.time.textContent = "-";
    return;
  }
  els.name.textContent = restaurant.name;
  els.description.textContent = restaurant.description;
  els.rating.textContent = `${restaurant.avg_rating ?? "-"} (${restaurant.review_count} yorum)`;
  els.min.textContent = fmtPrice(restaurant.min_order);
  els.time.textContent = restaurant.delivery_time;
};

const groupByCategory = (items) => {
  return items.reduce((acc, item) => {
    if (!acc[item.category]) acc[item.category] = [];
    acc[item.category].push(item);
    return acc;
  }, {});
};

const renderMenu = () => {
  if (!state.selected) {
    els.menuList.classList.add("muted");
    els.menuList.textContent = "Menüyü görmek için bir restoran seçin.";
    return;
  }
  const hasItems = state.menu.length > 0;
  els.menuList.classList.toggle("muted", !hasItems);
  els.menuHint.textContent = hasItems ? `${state.menu.length} ürün` : "Henüz menü eklenmedi";
  els.menuList.innerHTML = "";
  const grouped = groupByCategory(state.menu);
  Object.entries(grouped).forEach(([category, items]) => {
    const wrapper = document.createElement("div");
    wrapper.className = "menu-category";
    const list = document.createElement("div");
    list.className = "menu-items";
    list.innerHTML = `<p class="eyebrow">${category}</p>`;

    items.forEach((item) => {
      const node = document.createElement("div");
      node.className = "menu-item";
      node.innerHTML = `
        <div class="info">
          <h4>${item.name}</h4>
          <p>${item.description || ""}</p>
          <div class="tags">
            ${item.is_vegan ? '<span class="tag vegan">Vegan</span>' : ""}
          </div>
        </div>
        <div class="actions">
          <span class="price">${fmtPrice(item.price)}</span>
          <button class="pill primary" data-menu-id="${item.id}">Sepete ekle</button>
        </div>
      `;
      node.querySelector("button")?.addEventListener("click", () => addToCart(item.id));
      list.appendChild(node);
    });

    wrapper.appendChild(list);
    els.menuList.appendChild(wrapper);
  });
};

const renderCart = () => {
  const entries = Object.values(state.cart);
  if (entries.length === 0) {
    els.cartItems.textContent = "Menüden ürün ekleyin.";
    els.cartItems.classList.add("muted");
    els.cartHint.textContent = "Sepet boş";
    els.cartTotal.textContent = fmtPrice(0);
    els.orderSubmit.disabled = true;
    return;
  }

  els.cartItems.innerHTML = "";
  els.cartItems.classList.remove("muted");
  els.cartHint.textContent = `${entries.length} ürün eklendi`;

  entries.forEach((item) => {
    const row = document.createElement("div");
    row.className = "cart-item";
    row.innerHTML = `
      <header>
        <div>
          <strong>${item.name}</strong>
          <p class="muted">${fmtPrice(item.price)} • ${item.category || ""}</p>
        </div>
        <div class="cart-controls">
          <button class="control-btn" aria-label="Eksilt">-</button>
          <span>${item.quantity}</span>
          <button class="control-btn" aria-label="Arttır">+</button>
        </div>
      </header>
    `;
    const buttons = row.querySelectorAll("button");
    buttons[0].addEventListener("click", () => updateQuantity(item.id, item.quantity - 1));
    buttons[1].addEventListener("click", () => updateQuantity(item.id, item.quantity + 1));
    els.cartItems.appendChild(row);
  });

  const total = entries.reduce((sum, item) => sum + item.price * item.quantity, 0);
  els.cartTotal.textContent = fmtPrice(total);
  els.orderSubmit.disabled = !state.selected;
};

const addToCart = (menuItemId) => {
  const item = state.menu.find((m) => m.id === menuItemId);
  if (!item) return;
  const current = state.cart[menuItemId] || { ...item, quantity: 0 };
  state.cart[menuItemId] = { ...current, quantity: current.quantity + 1 };
  renderCart();
};

const updateQuantity = (menuItemId, quantity) => {
  if (quantity <= 0) {
    delete state.cart[menuItemId];
  } else {
    state.cart[menuItemId].quantity = quantity;
  }
  renderCart();
};

const renderReviews = () => {
  if (!state.selected) {
    els.reviewList.textContent = "Henüz bir restoran seçmediniz.";
    els.reviewList.classList.add("muted");
    return;
  }
  const hasReviews = state.reviews.length > 0;
  els.reviewHint.textContent = hasReviews ? `${state.reviews.length} yorum` : "İlk yorumu sen ekle";
  els.reviewList.innerHTML = "";
  els.reviewList.classList.toggle("muted", !hasReviews);

  if (!hasReviews) {
    els.reviewList.textContent = "Bu restoran için yorum yok. İlk yorumu sen yaz!";
    return;
  }

  state.reviews.forEach((review) => {
    const node = document.createElement("div");
    node.className = "review-item";
    node.innerHTML = `
      <header>
        <strong>${review.user_name}</strong>
        <span class="rating">⭐ ${review.rating}</span>
      </header>
      <p>${review.comment}</p>
      <p class="muted">${new Date(review.created_at).toLocaleString("tr-TR")}</p>
    `;
    els.reviewList.appendChild(node);
  });
};

const selectRestaurant = async (id) => {
  const restaurant = state.restaurants.find((r) => r.id === id);
  if (!restaurant) return;
  state.selected = restaurant;
  state.cart = {};
  renderRestaurants();
  updateHeader(restaurant);
  setStatus(els.orderStatus, "");
  setStatus(els.reviewStatus, "");
  els.orderSubmit.disabled = true;
  els.menuHint.textContent = "Menü yükleniyor...";
  els.menuList.textContent = "Yükleniyor...";
  els.reviewHint.textContent = "Yorumlar yükleniyor...";
  els.reviewList.textContent = "Yükleniyor...";

  await Promise.all([loadMenu(id), loadReviews(id)]);
  renderMenu();
  renderCart();
  renderReviews();
};

const loadRestaurants = async () => {
  const res = await fetch("/api/restaurants");
  if (!res.ok) {
    els.list.textContent = "Restoranlar yüklenirken hata oluştu.";
    return;
  }
  const data = await res.json();
  const list = data.restaurants || [];
  state.restaurants = list.map((r) => ({
    id: r.restaurant_id,
    name: r.name,
    cuisine: r.cuisines?.[0] || "Genel",
    avg_rating: "-",
    review_count: 0,
    delivery_time: "30-45 dk",
    min_order: r.min_order_amount || 0,
    description: r.phone ? `Tel: ${r.phone}` : "Restoran",
  }));
  renderRestaurants();
};

const loadMenu = async (restaurantId) => {
  const res = await fetch(`/api/restaurants/${restaurantId}/menu`);
  if (!res.ok) {
    els.menuList.textContent = "Menü yüklenemedi.";
    return;
  }
  const data = await res.json();
  const categories = data.categories || [];
  state.menu = categories.flatMap((cat) =>
    (cat.products || []).map((p) => ({
      id: p.product_id,
      name: p.name,
      description: p.description || "",
      price: Number(p.base_price) || 0,
      category: cat.name,
      is_vegan: false,
    }))
  );
};

const loadReviews = async (restaurantId) => {
  const res = await fetch(`/api/restaurants/${restaurantId}/reviews`);
  if (!res.ok) {
    state.reviews = [];
    return;
  }
  state.reviews = await res.json();
};

const handleOrderSubmit = async (event) => {
  event.preventDefault();
  if (!state.selected) return;
  const items = Object.values(state.cart);
  if (items.length === 0) {
    setStatus(els.orderStatus, "Sepet boş, önce ürün ekleyin.", true);
    return;
  }
  const payload = {
    restaurant_id: state.selected.id,
    customer_name: document.getElementById("customer-name").value.trim(),
    address: document.getElementById("address").value.trim(),
    phone: document.getElementById("phone").value.trim(),
    notes: document.getElementById("notes").value.trim(),
    items: items.map((item) => ({ menu_item_id: item.id, quantity: item.quantity })),
  };
  const res = await fetch("/api/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    setStatus(els.orderStatus, data.error || "Sipariş kaydedilemedi", true);
    return;
  }
  setStatus(els.orderStatus, `Sipariş alındı (#${data.order_id}) • Toplam ${fmtPrice(data.total)}`);
  state.cart = {};
  els.orderForm.reset();
  renderCart();
};

const handleReviewSubmit = async (event) => {
  event.preventDefault();
  if (!state.selected) {
    setStatus(els.reviewStatus, "Önce restoran seçin.", true);
    return;
  }
  const payload = {
    user_name: document.getElementById("reviewer-name").value.trim(),
    rating: document.getElementById("review-rating").value,
    comment: document.getElementById("review-comment").value.trim(),
  };
  const res = await fetch(`/api/restaurants/${state.selected.id}/reviews`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    setStatus(els.reviewStatus, data.error || "Yorum kaydedilemedi", true);
    return;
  }
  setStatus(els.reviewStatus, "Yorum eklendi!");
  els.reviewForm.reset();
  document.getElementById("review-rating").value = 5;
  state.reviews = [data, ...state.reviews];
  renderReviews();
};

const renderOwnerSelect = () => {
  if (!els.ownerSelect) return;
  els.ownerSelect.innerHTML = "";
  state.restaurants.forEach((r) => {
    const option = document.createElement("option");
    option.value = r.id;
    option.textContent = r.name;
    if (state.ownerRestaurantId === r.id) option.selected = true;
    els.ownerSelect.appendChild(option);
  });
};

const loadOwnerOrders = async () => {
  if (!state.ownerRestaurantId) return;
  const res = await fetch(`/api/orders?restaurant_id=${state.ownerRestaurantId}`);
  if (!res.ok) {
    els.ownerOrders.textContent = "Siparişler yüklenemedi.";
    return;
  }
  state.ownerOrders = await res.json();
};

const renderOwnerOrders = () => {
  if (!els.ownerOrders) return;
  if (!state.ownerRestaurantId) {
    els.ownerOrders.textContent = "Restoran seçin.";
    els.ownerOrders.classList.add("muted");
    return;
  }
  const hasOrders = state.ownerOrders.length > 0;
  els.ownerOrders.classList.toggle("muted", !hasOrders);
  els.ownerOrdersHint.textContent = hasOrders
    ? `${state.ownerOrders.length} sipariş`
    : "Sipariş bulunamadı";
  els.ownerOrders.innerHTML = hasOrders
    ? ""
    : "Bu restoran için henüz sipariş yok.";

  state.ownerOrders.forEach((order) => {
    const node = document.createElement("div");
    node.className = "review-item";
    const items = (order.items || [])
      .map(
        (i) =>
          `<li><span>${i.quantity} x ${i.item_name}</span><span>${fmtPrice(
            i.price * i.quantity
          )}</span></li>`
      )
      .join("");
    node.innerHTML = `
      <header>
        <strong>#${order.id} • ${order.customer_name}</strong>
        <span class="badge ghost">${new Date(order.placed_at).toLocaleString("tr-TR")}</span>
      </header>
      <p class="muted">${order.address} • ${order.phone}</p>
      <ul class="order-items">${items}</ul>
      <div class="total-line"><span>Toplam</span><strong>${fmtPrice(order.total)}</strong></div>
      <p class="muted">Not: ${order.notes || "-"}</p>
    `;
    els.ownerOrders.appendChild(node);
  });
};

const loadOwnerMenu = async () => {
  if (!state.ownerRestaurantId) return;
  const res = await fetch(`/api/restaurants/${state.ownerRestaurantId}/menu`);
  if (!res.ok) {
    els.ownerMenuList.textContent = "Menü yüklenemedi.";
    return;
  }
  state.ownerMenu = await res.json();
};

const renderOwnerMenu = () => {
  if (!els.ownerMenuList) return;
  const hasMenu = state.ownerMenu.length > 0;
  els.ownerMenuList.classList.toggle("muted", !hasMenu);
  els.ownerMenuHint.textContent = hasMenu ? `${state.ownerMenu.length} ürün` : "Ürün ekleyin";
  els.ownerMenuList.innerHTML = hasMenu ? "" : "Henüz ürün yok, eklemeye başlayın.";
  state.ownerMenu.forEach((item) => {
    const row = document.createElement("div");
    row.className = "menu-item";
    row.innerHTML = `
      <div class="info">
        <h4>${item.name}</h4>
        <p>${item.description || ""}</p>
        <div class="tags">${item.is_vegan ? '<span class="tag vegan">Vegan</span>' : ""}</div>
      </div>
      <div class="actions">
        <span class="pill">${item.category}</span>
        <span class="price">${fmtPrice(item.price)}</span>
      </div>
    `;
    els.ownerMenuList.appendChild(row);
  });
};

const handleOwnerMenuSubmit = async (event) => {
  event.preventDefault();
  if (!state.ownerRestaurantId) return;
  const payload = {
    name: els.ownerItemName.value.trim(),
    category: els.ownerItemCategory.value.trim(),
    price: els.ownerItemPrice.value,
    description: els.ownerItemDesc.value.trim(),
    is_vegan: els.ownerItemVegan.checked,
  };
  const res = await fetch(`/api/restaurants/${state.ownerRestaurantId}/menu`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    setStatus(els.ownerMenuStatus, data.error || "Ürün eklenemedi", true);
    return;
  }
  setStatus(els.ownerMenuStatus, "Ürün eklendi");
  els.ownerMenuForm.reset();
  await loadOwnerMenu();
  renderOwnerMenu();
  if (state.selected?.id === state.ownerRestaurantId) {
    await loadMenu(state.ownerRestaurantId);
    renderMenu();
  }
};


const postJSON = async (url, payload) => {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, data };
};

const handleCustomerRegister = async (event) => {
  event.preventDefault();
  const payload = {
    name: els.custName?.value?.trim(),
    email: els.custEmail?.value?.trim(),
    password: els.custPass?.value,
  };
  const { ok, data } = await postJSON("/api/customer/register", payload);
  setStatus(els.custStatus, ok ? "Kayıt başarılı, giriş yapıldı." : data.error || "Hata oluştu", !ok);
  if (ok) {
    await setRole("customer");
  }
};

const handleCustomerLogin = async () => {
  const payload = {
    email: els.custEmail?.value?.trim(),
    password: els.custPass?.value,
  };
  const { ok, data } = await postJSON("/api/customer/login", payload);
  setStatus(els.custStatus, ok ? "Giriş başarılı" : data.error || "Hatalı giriş", !ok);
  if (ok) {
    await setRole("customer");
  }
};

const handleOwnerRegister = async (event) => {
  event.preventDefault();
  const payload = {
    name: els.ownName?.value?.trim(),
    email: els.ownEmail?.value?.trim(),
    password: els.ownPass?.value,
  };
  const { ok, data } = await postJSON("/api/owner/register", payload);
  setStatus(els.ownStatus, ok ? "Kayıt başarılı, giriş yapıldı." : data.error || "Hata oluştu", !ok);
  if (ok) {
    await setRole("owner");
  }
};

const handleOwnerLogin = async () => {
  const payload = {
    email: els.ownEmail?.value?.trim(),
    password: els.ownPass?.value,
  };
  const { ok, data } = await postJSON("/api/owner/login", payload);
  setStatus(els.ownStatus, ok ? "Giriş başarılı" : data.error || "Hatalı giriş", !ok);
  if (ok) {
    await setRole("owner");
  }
};

const setRole = async (role) => {
  state.role = role;
  toggleOverlay(false);
  setActiveRoleButton(role);
  if (els.customerView && els.ownerView) {
    els.customerView.classList.toggle("hidden", role !== "customer");
    els.ownerView.classList.toggle("hidden", role !== "owner");
  }
  if (role === "customer") {
    if (!state.selected && state.restaurants.length > 0) {
      await selectRestaurant(state.restaurants[0].id);
    } else {
      renderRestaurants();
      updateHeader(state.selected);
      renderMenu();
      renderCart();
      renderReviews();
    }
  } else if (role === "owner") {
    ensureOwnerRestaurant();
    renderOwnerSelect();
    await Promise.all([loadOwnerOrders(), loadOwnerMenu()]);
    renderOwnerOrders();
    renderOwnerMenu();
  }
};

els.orderForm?.addEventListener("submit", handleOrderSubmit);
els.reviewForm?.addEventListener("submit", handleReviewSubmit);
els.overlayCustomer?.addEventListener("click", () => setRole("customer"));
els.overlayOwner?.addEventListener("click", () => setRole("owner"));
els.roleCustomerBtn?.addEventListener("click", () => setRole("customer"));
els.roleOwnerBtn?.addEventListener("click", () => setRole("owner"));
els.ownerSelect?.addEventListener("change", async (event) => {
  state.ownerRestaurantId = Number(event.target.value);
  await Promise.all([loadOwnerOrders(), loadOwnerMenu()]);
  renderOwnerOrders();
  renderOwnerMenu();
});
els.ownerMenuForm?.addEventListener("submit", handleOwnerMenuSubmit);

document.getElementById("customer-register-form")?.addEventListener("submit", handleCustomerRegister);
els.custLoginBtn?.addEventListener("click", handleCustomerLogin);
document.getElementById("owner-register-form")?.addEventListener("submit", handleOwnerRegister);
els.ownLoginBtn?.addEventListener("click", handleOwnerLogin);

const bootstrap = async () => {
  await loadRestaurants();
  if (state.restaurants.length > 0) {
    await selectRestaurant(state.restaurants[0].id);
    ensureOwnerRestaurant();
    renderOwnerSelect();
  }
  toggleOverlay(true);
};

bootstrap().catch(() => {
  els.list.textContent = "Restoranlar yüklenirken hata oluştu.";
});

