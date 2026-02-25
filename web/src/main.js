import maplibregl from "maplibre-gl";
import { Protocol } from "pmtiles";
import { LayerControl } from "maplibre-gl-layer-control";
import "maplibre-gl/dist/maplibre-gl.css";
import "maplibre-gl-layer-control/style.css";
import "./style.css";
import protomapsStyle from "./protomaps-style.json";

const CONFIG = {
  terrainTileJson: "https://tunnel.optgeo.org/martin/mapterhorn",
  czPmtilesUrl: "pmtiles://https://tunnel.optgeo.org/cz.pmtiles",
  initialView: {
    center: [15.200776, 49.478176],
    zoom: 13.5,
    pitch: 35,
    bearing: 0
  }
};

const statusEl = document.getElementById("status");
const loadingPane = document.getElementById("loading-pane");
let loadingActive = false;
let loadingHideTimer = null;

const setLoading = (isLoading) => {
  if (!loadingPane || loadingActive === isLoading) {
    return;
  }
  loadingActive = isLoading;
  if (loadingHideTimer) {
    clearTimeout(loadingHideTimer);
    loadingHideTimer = null;
  }
  if (isLoading) {
    loadingPane.classList.add("is-active");
  } else {
    loadingHideTimer = window.setTimeout(() => {
      loadingPane.classList.remove("is-active");
    }, 180);
  }
};

const setStatus = (text) => {
  if (statusEl) {
    statusEl.textContent = text;
  }
};

const pmtilesProtocol = new Protocol();
maplibregl.addProtocol("pmtiles", pmtilesProtocol.tile);

const baseStyle = sanitizeStyle(protomapsStyle);
const map = new maplibregl.Map({
  container: "map",
  style: baseStyle,
  center: CONFIG.initialView.center,
  zoom: CONFIG.initialView.zoom,
  pitch: CONFIG.initialView.pitch,
  bearing: CONFIG.initialView.bearing,
  hash: "map",
  minZoom: 4,
  maxZoom: 22,
  antialias: true
});

map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "bottom-left");

map.on("load", () => {
  setStatus("AMX-26 Czechia Cadastral Map");
  setLoading(true);
  addTerrain(map);
  addCadastralLayers(map);
  addLayerControl(map);
});

map.on("dataloading", (event) => {
  if (event?.dataType === "source" || event?.dataType === "tile") {
    setLoading(true);
  }
});

map.on("idle", () => {
  setLoading(false);
});

map.on("error", () => {
  setLoading(false);
});

function sanitizeStyle(style) {
  const cloned = JSON.parse(JSON.stringify(style));
  return cloned;
}

function addTerrain(mapInstance) {
  mapInstance.addSource("terrain-dem", {
    type: "raster-dem",
    url: CONFIG.terrainTileJson,
    tileSize: 256,
    encoding: "terrarium"
  });

  mapInstance.addSource("terrain-hillshade", {
    type: "raster-dem",
    url: CONFIG.terrainTileJson,
    tileSize: 256,
    encoding: "terrarium"
  });

  // Add hillshade above basemap but below cadastral layers
  mapInstance.addLayer(
    {
      id: "terrain-hillshade",
      type: "hillshade",
      source: "terrain-hillshade",
      paint: {
        "hillshade-exaggeration": 1.0,
        "hillshade-shadow-color": "rgba(0, 0, 0, 0.35)",
        "hillshade-highlight-color": "rgba(255, 255, 255, 0.15)",
        "hillshade-accent-color": "rgba(180, 140, 100, 0.2)",
        "hillshade-illumination-direction": 315
      }
    },
    "buildings"
  );

  mapInstance.setTerrain({
    source: "terrain-dem",
    exaggeration: 1.0
  });
}

function addCadastralLayers(mapInstance) {
  mapInstance.addSource("cz", {
    type: "vector",
    url: CONFIG.czPmtilesUrl
  });

  // Add layers in reverse order (bottom to top) to maintain proper stacking
  // Bottom: Fill layers, Top: Line layers
  
  mapInstance.addLayer({
    id: "cz-boundaries",
    type: "line",
    source: "cz",
    "source-layer": "CadastralBoundary",
    minzoom: 13,
    maxzoom: 23,
    paint: {
      "line-color": "#ff4747",
      "line-width": ["interpolate", ["linear"], ["zoom"], 13, 0.4, 22, 2.2],
      "line-opacity": 0.9
    }
  });

  mapInstance.addLayer({
    id: "cz-parcels-outline",
    type: "line",
    source: "cz",
    "source-layer": "CadastralParcel",
    minzoom: 13,
    maxzoom: 23,
    paint: {
      "line-color": "#ff4747",
      "line-width": ["interpolate", ["linear"], ["zoom"], 13, 0.5, 22, 1.4],
      "line-opacity": 0.8
    }
  }, "cz-boundaries");

  mapInstance.addLayer({
    id: "cz-zoning-outline",
    type: "line",
    source: "cz",
    "source-layer": "CadastralZoning",
    minzoom: 5,
    maxzoom: 14,
    paint: {
      "line-color": "#ff4747",
      "line-width": ["interpolate", ["linear"], ["zoom"], 5, 0.3, 14, 0.8],
      "line-opacity": 0.8
    }
  }, "cz-parcels-outline");

  mapInstance.addLayer({
    id: "cz-parcels-fill",
    type: "fill",
    source: "cz",
    "source-layer": "CadastralParcel",
    minzoom: 13,
    maxzoom: 23,
    paint: {
      "fill-color": "#f3d37b",
      "fill-opacity": 0
    }
  }, "cz-zoning-outline");

  mapInstance.addLayer({
    id: "cz-zoning-fill",
    type: "fill",
    source: "cz",
    "source-layer": "CadastralZoning",
    minzoom: 5,
    maxzoom: 14,
    paint: {
      "fill-color": "#f3d37b",
      "fill-opacity": 0
    }
  }, "cz-parcels-fill");

  mapInstance.addLayer({
    id: "cz-zoning-labels",
    type: "symbol",
    source: "cz",
    "source-layer": "CadastralZoning",
    minzoom: 12,
    maxzoom: 14,
    layout: {
      "text-field": ["get", "label"],
      "text-font": ["sans-serif"],
      "text-size": 10,
      "text-allow-overlap": false,
      "symbol-placement": "point",
      "symbol-z-order": "auto"
    },
    paint: {
      "text-color": "#ff4747",
      "text-halo-color": "#0b0d12",
      "text-halo-width": 1.0
    }
  });

  mapInstance.addLayer({
    id: "cz-parcels-labels",
    type: "symbol",
    source: "cz",
    "source-layer": "CadastralParcel",
    minzoom: 16.5,
    maxzoom: 23,
    layout: {
      "text-field": ["get", "label"],
      "text-font": ["sans-serif"],
      "text-size": 11,
      "text-allow-overlap": false,
      "symbol-placement": "point",
      "symbol-z-order": "auto"
    },
    paint: {
      "text-color": "#ff4747",
      "text-halo-color": "#0b0d12",
      "text-halo-width": 1.0
    }
  });

  mapInstance.on("mouseenter", "cz-parcels-fill", () => {
    mapInstance.getCanvas().style.cursor = "pointer";
  });

  mapInstance.on("mouseleave", "cz-parcels-fill", () => {
    mapInstance.getCanvas().style.cursor = "";
    setStatus("AMX-26 Czechia Cadastral Map");
  });

  mapInstance.on("mousemove", "cz-parcels-fill", (event) => {
    const features = mapInstance.queryRenderedFeatures(event.point, {
      layers: ["cz-parcels-fill"]
    });
    if (features.length > 0) {
      const feature = features[0];
      const label = feature.properties?.label || "";
      const areaLabel = getAreaLabel(feature.properties);
      const refLabel = getNationalRef(feature.properties);
      const parts = [label].filter(Boolean);
      if (areaLabel) parts.push(`Area: ${areaLabel}`);
      if (refLabel) parts.push(`Ref: ${refLabel}`);
      setStatus(parts.join(" · "));
    } else {
      setStatus("AMX-26 Czechia Cadastral Map");
    }
  });

  mapInstance.on("click", "cz-parcels-fill", (event) => {
    const feature = event.features?.[0];
    const label = feature?.properties?.label || "(label unavailable)";
    const areaLabel = getAreaLabel(feature?.properties);
    const areaLine = areaLabel ? `<div class="popup-meta">Area: ${escapeHtml(areaLabel)}</div>` : "";
    const refLabel = getNationalRef(feature?.properties);
    const refLine = refLabel ? `<div class="popup-meta">Ref: ${escapeHtml(refLabel)}</div>` : "";

    new maplibregl.Popup({ closeButton: true, closeOnClick: true })
      .setLngLat(event.lngLat)
      .setHTML(
        `<div class="popup-label">${escapeHtml(String(label))}</div>` + areaLine + refLine
      )
      .addTo(mapInstance);
  });
}

function addLayerControl(mapInstance) {
  const layerControl = new LayerControl({
    collapsed: true,
    layers: [
      "cz-zoning-fill",
      "cz-zoning-outline",
      "cz-zoning-labels",
      "cz-parcels-fill",
      "cz-parcels-outline",
      "cz-parcels-labels",
      "cz-boundaries",
      "terrain-hillshade"
    ],
    layerStates: {
      "cz-zoning-fill": { name: "Cadastral Zoning", visible: true, opacity: 0.2 },
      "cz-zoning-outline": { name: "Zoning Outlines", visible: true, opacity: 0.8 },
      "cz-zoning-labels": { name: "Zoning Labels", visible: true, opacity: 1.0 },
      "cz-parcels-fill": { name: "Cadastral Parcels", visible: true, opacity: 0.15 },
      "cz-parcels-outline": { name: "Parcel Outlines", visible: true, opacity: 0.8 },
      "cz-parcels-labels": { name: "Parcel Labels", visible: true, opacity: 1.0 },
      "cz-boundaries": { name: "Cadastral Boundaries", visible: true, opacity: 0.9 },
      "terrain-hillshade": { name: "Terrain Hillshade", visible: true, opacity: 0.8 }
    },
    panelWidth: 320,
    panelMinWidth: 240,
    panelMaxWidth: 380,
    showStyleEditor: false
  });

  mapInstance.addControl(layerControl, "bottom-left");
}

function escapeHtml(value) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function getAreaLabel(properties) {
  if (!properties) {
    return null;
  }

  // Czech cadastral format: areaValue and areaValue_uom
  const areaValue = Number(properties.areaValue);
  const areaUnit = properties.areaValue_uom || "";
  if (Number.isFinite(areaValue)) {
    return `${areaValue.toLocaleString(undefined, { maximumFractionDigits: 1 })}${areaUnit}`;
  }

  // Fallback to other common area field names
  const areaFields = ["area", "area_m2", "area_m", "area_sq_m", "area_sq_meters"];
  for (const key of areaFields) {
    const value = Number(properties[key]);
    if (Number.isFinite(value)) {
      return `${value.toLocaleString(undefined, { maximumFractionDigits: 1 })} m2`;
    }
  }

  const areaHa = Number(properties.area_ha);
  if (Number.isFinite(areaHa)) {
    return `${areaHa.toLocaleString(undefined, { maximumFractionDigits: 2 })} ha`;
  }

  return null;
}

function getNationalRef(properties) {
  if (!properties) {
    return null;
  }

  const ref = properties.nationalCadastralReference;
  if (typeof ref === "string" && ref.trim()) {
    return ref.trim();
  }

  return null;
}
