// Pinpoint checkout widget — drop-in address picker for a merchant checkout.
// Usage: <div id="pinpoint-widget" data-api-key="pk_test_..."></div> + this script.
// On selection it sets a hidden field and fires a `pinpoint:selected` event whose
// detail carries the verified address (the `code` is the token the merchant stores).
(function () {
  const container = document.getElementById("pinpoint-widget");
  if (!container) return;
  const apiKey = container.getAttribute("data-api-key") || "";

  container.innerHTML = `
    <input data-testid="pp-input" placeholder="Type your address or a landmark" autocomplete="off" />
    <ul data-testid="pp-suggestions" style="list-style:none;padding:0;margin:4px 0;"></ul>
    <input type="hidden" data-testid="pp-token" />
    <div data-testid="pp-selected"></div>`;

  const input = container.querySelector('[data-testid="pp-input"]');
  const suggestions = container.querySelector('[data-testid="pp-suggestions"]');
  const token = container.querySelector('[data-testid="pp-token"]');
  const selected = container.querySelector('[data-testid="pp-selected"]');

  let timer;
  input.addEventListener("input", () => {
    clearTimeout(timer);
    const q = input.value.trim();
    if (q.length < 3) {
      suggestions.innerHTML = "";
      return;
    }
    timer = setTimeout(() => runSearch(q), 200); // debounce type-ahead
  });

  async function runSearch(q) {
    const r = await fetch("/v1/geocode", {
      method: "POST",
      headers: { Authorization: "Bearer " + apiKey, "Content-Type": "application/json" },
      body: JSON.stringify({ query: q, limit: 5 }),
    });
    suggestions.innerHTML = "";
    if (!r.ok) return;
    const data = await r.json();
    for (const res of data.results) {
      const li = document.createElement("li");
      li.setAttribute("data-testid", "pp-suggestion");
      li.setAttribute("data-code", res.code);
      li.style.cursor = "pointer";
      li.textContent = `${res.landmark || res.code} — ${res.code}`;
      li.addEventListener("click", () => select(res));
      suggestions.appendChild(li);
    }
  }

  function select(res) {
    token.value = res.code;
    selected.textContent = "Selected: " + res.code;
    input.value = res.landmark || res.code;
    suggestions.innerHTML = "";
    container.dispatchEvent(new CustomEvent("pinpoint:selected", { detail: res, bubbles: true }));
  }
})();
