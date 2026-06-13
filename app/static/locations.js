const TILE_SIZE = 256;
const MAP_ZOOM = 14;
const MAP_CENTER = {
  lat: 42.6618,
  lng: 21.1736,
};

const SCENARIO_STORAGE_KEY = "smart-parking-scenario";
const LIVE_REFRESH_MS = 6000;

const LOCATIONS = [
  {
    id: "center",
    name: "Parkingu Qendror i Prishtin\u00ebs",
    lat: 42.6629,
    lng: 21.1655,
    freeSpots: 15,
    type: "active",
  },
  {
    id: "dardania",
    name: "Dardania",
    lat: 42.6557,
    lng: 21.1697,
    freeSpots: 8,
    type: "demo",
  },
  {
    id: "bregu-i-diellit",
    name: "Bregu i Diellit",
    lat: 42.6688,
    lng: 21.1813,
    freeSpots: 11,
    type: "demo",
  },
  {
    id: "ulpiana",
    name: "Ulpiana",
    lat: 42.6598,
    lng: 21.1778,
    freeSpots: 6,
    type: "demo",
  },
];

function renderFallback(mapEl, message) {
  mapEl.innerHTML = `
    <div class="map-fallback">
      <strong>Harta nuk u ngarkua.</strong>
      <span>${message}</span>
    </div>
  `;
}

function getScenarioFromStorage() {
  try {
    return window.localStorage.getItem(SCENARIO_STORAGE_KEY) || "auto";
  } catch (error) {
    return "auto";
  }
}

function project(lat, lng, zoom) {
  const sinLat = Math.sin((lat * Math.PI) / 180);
  const scale = TILE_SIZE * 2 ** zoom;

  return {
    x: ((lng + 180) / 360) * scale,
    y:
      (0.5 - Math.log((1 + sinLat) / (1 - sinLat)) / (4 * Math.PI)) *
      scale,
  };
}

function createTileUrl(z, x, y) {
  return `https://tile.openstreetmap.org/${z}/${x}/${y}.png`;
}

function updateActiveLocation(snapshot) {
  const activeLocation = LOCATIONS.find((location) => location.id === "center");
  const summary = snapshot?.summary || {};

  if (!activeLocation) {
    return;
  }

  if (snapshot?.parking_name) {
    activeLocation.name = snapshot.parking_name;
  }

  const freeSpots = Number(summary.free_spots);
  if (Number.isFinite(freeSpots)) {
    activeLocation.freeSpots = freeSpots;
  }

  const activeNameEl = document.querySelector("[data-active-parking-name]");
  const activeFreeEl = document.querySelector("[data-active-parking-free]");

  if (activeNameEl) {
    activeNameEl.textContent = activeLocation.name;
  }

  if (activeFreeEl) {
    activeFreeEl.textContent = String(activeLocation.freeSpots);
  }
}

function createMarker(location, x, y, tooltipSide) {
  const marker = document.createElement("div");
  marker.className = `embed-marker ${location.type}`;
  marker.dataset.tooltipSide = tooltipSide;
  marker.style.left = `${x}px`;
  marker.style.top = `${y}px`;

  marker.innerHTML = `
    <button
      type="button"
      class="parking-pin ${
        location.type === "active" ? "parking-pin-active" : "parking-pin-demo"
      }"
      aria-label="${location.name}. Lire ${location.freeSpots} vende te lira."
    >
      <span class="parking-pin-icon" aria-hidden="true">P</span>
    </button>
    <div class="embed-popup ${location.type}">
      <strong>${location.name}</strong>
      <span>Lire: ${location.freeSpots} vende te lira</span>
    </div>
  `;

  const button = marker.querySelector(".parking-pin");
  if (button && location.type === "active") {
    button.addEventListener("click", () => {
      window.location.href = "/dashboard";
    });
  }

  return marker;
}

function initMap() {
  const mapEl = document.getElementById("prishtinaMap");
  if (!mapEl) return;

  const tilesLayer = document.createElement("div");
  tilesLayer.className = "osm-map__tiles";

  const markersLayer = document.createElement("div");
  markersLayer.className = "osm-map__markers";

  const attribution = document.createElement("div");
  attribution.className = "osm-map__attribution";
  attribution.textContent = "OpenStreetMap contributors";

  mapEl.textContent = "";
  mapEl.append(tilesLayer, markersLayer, attribution);

  const markerButtonsById = new Map();
  let renderFrame = 0;
  let resizeObserver = null;
  let lastLayout = null;

  const getLayout = () => {
    const width = mapEl.clientWidth;
    const height = mapEl.clientHeight;

    if (!width || !height) {
      return null;
    }

    const centerPoint = project(MAP_CENTER.lat, MAP_CENTER.lng, MAP_ZOOM);
    const topLeftX = centerPoint.x - width / 2;
    const topLeftY = centerPoint.y - height / 2;
    const tileCount = 2 ** MAP_ZOOM;

    return {
      width,
      height,
      topLeftX,
      topLeftY,
      tileCount,
      startX: Math.floor(topLeftX / TILE_SIZE) - 1,
      endX: Math.floor((topLeftX + width) / TILE_SIZE) + 1,
      startY: Math.floor(topLeftY / TILE_SIZE) - 1,
      endY: Math.floor((topLeftY + height) / TILE_SIZE) + 1,
    };
  };

  const drawTiles = (layout) => {
    tilesLayer.replaceChildren();
    const tilesFragment = document.createDocumentFragment();

    for (let tileY = layout.startY; tileY <= layout.endY; tileY += 1) {
      if (tileY < 0 || tileY >= layout.tileCount) {
        continue;
      }

      for (let tileX = layout.startX; tileX <= layout.endX; tileX += 1) {
        const wrappedX = ((tileX % layout.tileCount) + layout.tileCount) % layout.tileCount;
        const tile = new Image();
        tile.className = "osm-map__tile";
        tile.alt = "";
        tile.decoding = "async";
        tile.loading = "eager";
        tile.src = createTileUrl(MAP_ZOOM, wrappedX, tileY);
        tile.style.left = `${tileX * TILE_SIZE - layout.topLeftX}px`;
        tile.style.top = `${tileY * TILE_SIZE - layout.topLeftY}px`;
        tile.onerror = () => {
          tile.remove();
        };
        tilesFragment.appendChild(tile);
      }
    }

    tilesLayer.appendChild(tilesFragment);
  };

  const drawMarkers = (layout) => {
    markersLayer.replaceChildren();
    markerButtonsById.clear();

    LOCATIONS.forEach((location) => {
      const point = project(location.lat, location.lng, MAP_ZOOM);
      const x = point.x - layout.topLeftX;
      const y = point.y - layout.topLeftY;
      const tooltipSide = x > layout.width * 0.68 ? "left" : "right";
      const marker = createMarker(location, x, y, tooltipSide);
      const button = marker.querySelector(".parking-pin");

      if (button) {
        markerButtonsById.set(location.id, button);
      }

      markersLayer.appendChild(marker);
    });
  };

  const renderMap = () => {
    const layout = getLayout();
    if (!layout) {
      return;
    }

    lastLayout = layout;
    drawTiles(layout);
    drawMarkers(layout);
  };

  const renderMarkersOnly = () => {
    if (!lastLayout) {
      renderMap();
      return;
    }

    drawMarkers(lastLayout);
  };

  const scheduleRender = () => {
    cancelAnimationFrame(renderFrame);
    renderFrame = requestAnimationFrame(renderMap);
  };

  const loadLiveData = async () => {
    try {
      const scenario = getScenarioFromStorage();
      const response = await fetch(
        `/parking/dashboard-data?scenario=${encodeURIComponent(scenario)}`,
        {
        headers: { Accept: "application/json" },
        },
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const snapshot = await response.json();
      updateActiveLocation(snapshot);
      renderMarkersOnly();
    } catch (error) {
      console.error(error);
    }
  };

  if (window.ResizeObserver) {
    resizeObserver = new ResizeObserver(() => {
      scheduleRender();
    });
    resizeObserver.observe(mapEl);
  }

  window.addEventListener("resize", scheduleRender, { passive: true });
  window.addEventListener("load", scheduleRender, { once: true });
  window.addEventListener("storage", (event) => {
    if (event.key === SCENARIO_STORAGE_KEY) {
      loadLiveData();
    }
  });
  scheduleRender();
  loadLiveData();
  window.setInterval(loadLiveData, LIVE_REFRESH_MS);

  document.querySelectorAll("[data-focus-location]").forEach((control) => {
    control.addEventListener("click", () => {
      const targetId = control.getAttribute("data-focus-location");
      const button = targetId ? markerButtonsById.get(targetId) : null;

      if (button) {
        button.focus({ preventScroll: true });
      }
    });
  });

  return resizeObserver;
}

document.addEventListener("DOMContentLoaded", () => {
  try {
    updateActiveLocation({ summary: { free_spots: LOCATIONS[0].freeSpots } });
    initMap();
  } catch (error) {
    console.error(error);
    const mapEl = document.getElementById("prishtinaMap");
    if (mapEl) {
      renderFallback(mapEl, "Kontrollo konsolen per gabime ose provo perseri.");
    }
  }
});
