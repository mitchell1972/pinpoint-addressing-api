// Pinpoint field capture — queues captures in the browser (works offline) and
// uploads the queue when online. The server is authoritative: each capture has a
// client capture_id, so re-syncing never duplicates.
const $ = (sel) => document.querySelector(sel);
const KEY = "pinpoint_key";
const QUEUE = "pinpoint_capture_queue";

const getQueue = () => JSON.parse(localStorage.getItem(QUEUE) || "[]");
function setQueue(q) {
  localStorage.setItem(QUEUE, JSON.stringify(q));
  $("#queueCount").textContent = q.length;
}
const key = () => localStorage.getItem(KEY) || "";

window.addEventListener("DOMContentLoaded", () => {
  if (key()) $("#apiKey").value = key();
  $("#queueCount").textContent = getQueue().length;
});

$("#saveKey").onclick = () => localStorage.setItem(KEY, $("#apiKey").value.trim());

$("#gps").onclick = () => {
  if (!navigator.geolocation) return;
  navigator.geolocation.getCurrentPosition((p) => {
    $("#lat").value = p.coords.latitude;
    $("#lng").value = p.coords.longitude;
  });
};

$("#queueBtn").onclick = () => {
  const cap = {
    capture_id: crypto.randomUUID(),
    lat: parseFloat($("#lat").value),
    lng: parseFloat($("#lng").value),
    landmark: $("#landmark").value || null,
    captured_at: new Date().toISOString(),
  };
  const q = getQueue();
  q.push(cap);
  setQueue(q);
  $("#lat").value = "";
  $("#lng").value = "";
  $("#landmark").value = "";
};

$("#syncBtn").onclick = async () => {
  const q = getQueue();
  if (!q.length) {
    $("#syncStatus").textContent = "nothing to sync";
    return;
  }
  let r;
  try {
    r = await fetch("/v1/sync", {
      method: "POST",
      headers: { Authorization: "Bearer " + key(), "Content-Type": "application/json" },
      body: JSON.stringify({ captures: q }),
    });
  } catch (e) {
    $("#syncStatus").textContent = "offline — will retry later";
    return;
  }
  if (!r.ok) {
    $("#syncStatus").textContent = "error " + r.status;
    return;
  }
  const data = await r.json();
  const ul = $("#syncResults");
  ul.innerHTML = "";
  for (const res of data.results) {
    const li = document.createElement("li");
    li.setAttribute("data-testid", "sync-result");
    li.textContent = `${res.code} (${res.status})`;
    ul.appendChild(li);
  }
  $("#syncStatus").textContent = "synced " + data.results.length;
  setQueue([]); // server is authoritative — clear the local queue on success
};
