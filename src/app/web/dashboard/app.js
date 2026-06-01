// Pinpoint dispatch dashboard — talks to the same-origin /v1 API with a saved key.
const $ = (sel) => document.querySelector(sel);
const key = () => localStorage.getItem("pinpoint_key") || "";

function authHeaders() {
  return { Authorization: "Bearer " + key(), "Content-Type": "application/json" };
}

window.addEventListener("DOMContentLoaded", () => {
  if (key()) {
    $("#apiKey").value = key();
    $("#keyStatus").textContent = "saved";
  }
});

$("#saveKey").onclick = () => {
  localStorage.setItem("pinpoint_key", $("#apiKey").value.trim());
  $("#keyStatus").textContent = "saved";
};

$("#searchBtn").onclick = async () => {
  const tbody = $("#results");
  tbody.innerHTML = "";
  const r = await fetch("/v1/geocode", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ query: $("#q").value }),
  });
  if (!r.ok) {
    tbody.innerHTML = `<tr><td colspan="3">error ${r.status}</td></tr>`;
    return;
  }
  const data = await r.json();
  for (const res of data.results) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${res.code}</td><td>${res.landmark || ""}</td><td>${res.confidence}</td>`;
    tbody.appendChild(tr);
  }
};

$("#loadAnalytics").onclick = async () => {
  const s = await (await fetch("/v1/analytics/summary", { headers: authHeaders() })).json();
  $("#summary").textContent =
    `Total ${s.total} · delivered ${s.delivered} · failed ${s.failed} · fail rate ${(s.failed_rate * 100).toFixed(1)}%`;
  const h = await (await fetch("/v1/analytics/hotspots", { headers: authHeaders() })).json();
  const tbody = $("#hotspots");
  tbody.innerHTML = "";
  for (const row of h.hotspots) {
    const tr = document.createElement("tr");
    tr.innerHTML =
      `<td>${row.lga || ""}</td><td>${row.total}</td><td>${row.failed}</td><td>${(row.failed_rate * 100).toFixed(1)}%</td>`;
    tbody.appendChild(tr);
  }
};

$("#recordBtn").onclick = async () => {
  const r = await fetch("/v1/deliveries", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ code: $("#delCode").value.trim(), status: $("#delStatus").value }),
  });
  $("#recordStatus").textContent = r.ok ? "recorded" : `error ${r.status}`;
};
