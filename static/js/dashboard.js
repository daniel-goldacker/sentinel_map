const map = L.map("map", { worldCopyJump: true, zoomControl: false }).setView([5, 0], 2);
L.control.zoom({ position: "bottomright" }).addTo(map);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 18,
  attribution: "&copy; OpenStreetMap"
}).addTo(map);

const pingIcon = L.divIcon({ className: "", html: '<div class="ping"></div>', iconSize: [12, 12], iconAnchor: [6, 6] });
const targetIcon = L.divIcon({ className: "", html: '<div class="target"></div>', iconSize: [14, 14], iconAnchor: [7, 7] });

const wsStatusEl = document.getElementById("wsStatus");
const totalEventsEl = document.getElementById("totalEvents");
const epmEl = document.getElementById("epm");
const countryListEl = document.getElementById("countryList");
const pathListEl = document.getElementById("pathList");
const feedListEl = document.getElementById("feedList");

let socket = null;
let reconnectDelay = 1200;
let targetMarker = null;

function formatList(el, obj, fallback) {
  const entries = Object.entries(obj || {});
  el.innerHTML = entries.length
    ? entries.map(([k, v]) => `<li>${k}: ${v}</li>`).join("")
    : `<li>${fallback}</li>`;
}

function updateStats(stats) {
  totalEventsEl.textContent = String(stats.total_events || 0);
  epmEl.textContent = String(stats.events_per_minute || 0);
  formatList(countryListEl, stats.top_countries, "Sem eventos ainda.");
  formatList(pathListEl, stats.top_paths, "Sem eventos ainda.");
}

function ensureTarget(target) {
  if (!target) {
    return;
  }

  const latlng = [target.lat, target.lon];
  if (targetMarker) {
    targetMarker.setLatLng(latlng);
    return;
  }

  targetMarker = L.marker(latlng, { icon: targetIcon }).addTo(map);
  targetMarker.bindPopup(`<b>${target.name || "Alvo protegido"}</b>`);
}

function pushFeed(eventMsg) {
  const geo = eventMsg.geo || {};
  const where = geo.city ? `${geo.city}, ${geo.country || "Desconhecido"}` : (geo.country || "Desconhecido");
  const at = new Date(eventMsg.ts).toLocaleString("pt-BR");

  const node = document.createElement("div");
  node.className = "feed-item";
  node.innerHTML = `
    <div><b>${eventMsg.type}</b> | ${eventMsg.ip}</div>
    <div>${where}</div>
    <div class="pill">${eventMsg.path} | ${at}</div>
  `;

  feedListEl.prepend(node);
  while (feedListEl.childElementCount > 30) {
    feedListEl.removeChild(feedListEl.lastChild);
  }
}

function drawEvent(eventMsg) {
  const geo = eventMsg.geo;
  if (!geo || geo.lat === undefined || geo.lon === undefined) {
    return;
  }

  const marker = L.marker([geo.lat, geo.lon], { icon: pingIcon }).addTo(map);
  const where = geo.city ? `${geo.city}, ${geo.country || "Desconhecido"}` : (geo.country || "Desconhecido");

  marker.bindPopup(`
    <b>${eventMsg.type}</b><br/>
    IP: ${eventMsg.ip}<br/>
    ${where}<br/>
    ${new Date(eventMsg.ts).toLocaleString("pt-BR")}
  `);

  ensureTarget(eventMsg.target);
  if (eventMsg.target) {
    const line = L.polyline([[geo.lat, geo.lon], [eventMsg.target.lat, eventMsg.target.lon]], {
      color: "#ff946d",
      weight: 1,
      opacity: 0.55,
      dashArray: "7,6"
    }).addTo(map);
    setTimeout(() => map.removeLayer(line), 9000);
  }

  setTimeout(() => map.removeLayer(marker), 8500);
  pushFeed(eventMsg);
}

function handleMessage(raw) {
  const msg = JSON.parse(raw.data);

  if (msg.kind === "snapshot") {
    ensureTarget(msg.target);
    updateStats(msg.stats || {});

    (msg.recent_events || []).slice().reverse().forEach((ev) => {
      pushFeed(ev);
    });
    return;
  }

  if (msg.kind === "stats") {
    updateStats(msg.stats || {});
    return;
  }

  if (msg.kind === "event") {
    drawEvent(msg);
  }
}

function connect() {
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  socket = new WebSocket(`${protocol}://${location.host}/ws`);

  socket.onopen = () => {
    wsStatusEl.textContent = "online";
    wsStatusEl.style.color = "#4ad3a1";
    reconnectDelay = 1200;
  };

  socket.onmessage = handleMessage;

  socket.onclose = () => {
    wsStatusEl.textContent = "reconectando...";
    wsStatusEl.style.color = "#ffd38d";
    setTimeout(connect, reconnectDelay);
    reconnectDelay = Math.min(reconnectDelay * 1.6, 8000);
  };

  socket.onerror = () => {
    wsStatusEl.textContent = "erro de conexao";
    wsStatusEl.style.color = "#ff9a9a";
  };
}

connect();
