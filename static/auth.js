function setStatus(el, message, isError = false) {
  if (!el) return;
  el.textContent = message || "";
  el.style.color = isError ? "#b91c1c" : "#0f766e";
}

async function postJSON(url, payload) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, data };
}

function setupAuth(role) {
  const isCustomer = role === "customer";
  const form = document.getElementById(isCustomer ? "customer-register-form" : "owner-register-form");
  const statusEl = document.getElementById(isCustomer ? "cust-status" : "own-status");
  const nameEl = document.getElementById(isCustomer ? "cust-name" : "own-name");
  const emailEl = document.getElementById(isCustomer ? "cust-email" : "own-email");
  const passEl = document.getElementById(isCustomer ? "cust-pass" : "own-pass");
  const loginBtn = document.getElementById(isCustomer ? "cust-login-btn" : "own-login-btn");

  const register = async (event) => {
    event.preventDefault();
    const payload = {
      name: nameEl?.value?.trim(),
      email: emailEl?.value?.trim(),
      password: passEl?.value,
    };
    const { ok, data } = await postJSON(`/api/${isCustomer ? "customer" : "owner"}/register`, payload);
    setStatus(statusEl, ok ? "Kayıt başarılı, giriş yapıldı." : data.error || "Hata oluştu", !ok);
    if (ok) {
      window.location.href = "/";
    }
  };

  const login = async () => {
    const payload = {
      email: emailEl?.value?.trim(),
      password: passEl?.value,
    };
    const { ok, data } = await postJSON(`/api/${isCustomer ? "customer" : "owner"}/login`, payload);
    setStatus(statusEl, ok ? "Giriş başarılı" : data.error || "Hatalı giriş", !ok);
    if (ok) {
      window.location.href = "/";
    }
  };

  form?.addEventListener("submit", register);
  loginBtn?.addEventListener("click", login);
}
