// static/js/main.js - basic placeholders
document.addEventListener("DOMContentLoaded", () => {
  // Sepet miktar artır/azalt örneği (data-action attributes ile ileride genişletilebilir)
  document.querySelectorAll("[data-qty-btn]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const target = document.querySelector(btn.dataset.target);
      if (!target) return;
      const current = Number(target.value || 0);
      const delta = btn.dataset.qtyBtn === "inc" ? 1 : -1;
      const next = Math.max(0, current + delta);
      target.value = next;
    });
  });
});
