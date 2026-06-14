import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useNavigate } from "react-router-dom";

// Custom terracotta marker matching design palette
const makeIcon = (label, isOrigin = false) =>
  L.divIcon({
    className: "fx-marker",
    iconSize: [40, 50],
    iconAnchor: [20, 50],
    popupAnchor: [0, -48],
    html: `
      <div style="position:relative;width:40px;height:50px;">
        <svg viewBox="0 0 40 50" width="40" height="50" xmlns="http://www.w3.org/2000/svg">
          <path d="M20 0 C9 0 0 9 0 20 C0 33 20 50 20 50 C20 50 40 33 40 20 C40 9 31 0 20 0 Z"
            fill="${isOrigin ? "#2A1B24" : "#C85A40"}" />
          <circle cx="20" cy="20" r="7" fill="#FDFBF7"/>
        </svg>
        ${
          label
            ? `<div style="position:absolute;top:8px;left:0;right:0;text-align:center;color:#C85A40;font-weight:700;font-size:11px;font-family:Outfit,sans-serif;">${label}</div>`
            : ""
        }
      </div>
    `,
  });

export default function MapView({
  listings = [],
  origin = null, // { lat, lng, label }
  height = 520,
  zoom = 12,
  interactive = true,
  onMarkerClick,
}) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const layerRef = useRef(null);
  const nav = useNavigate();

  // Initialize map once
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    // Hyderabad default center
    const center = origin
      ? [origin.lat, origin.lng]
      : listings.find((l) => l.lat && l.lng)
      ? [listings[0].lat, listings[0].lng]
      : [17.4239, 78.4738];

    const map = L.map(containerRef.current, {
      center,
      zoom,
      zoomControl: interactive,
      scrollWheelZoom: interactive,
      dragging: interactive,
      doubleClickZoom: interactive,
      touchZoom: interactive,
    });

    // Carto Voyager — soft, editorial map style that pairs well with the terracotta palette
    L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    }).addTo(map);

    mapRef.current = map;
    layerRef.current = L.layerGroup().addTo(map);

    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Re-render markers when data changes
  useEffect(() => {
    const map = mapRef.current;
    const layer = layerRef.current;
    if (!map || !layer) return;
    layer.clearLayers();

    const bounds = [];

    if (origin && origin.lat != null && origin.lng != null) {
      L.marker([origin.lat, origin.lng], { icon: makeIcon("", true) })
        .bindTooltip(origin.label || "You are here", { direction: "top", offset: [0, -40] })
        .addTo(layer);
      bounds.push([origin.lat, origin.lng]);
    }

    listings.forEach((l, idx) => {
      if (l.lat == null || l.lng == null) return;
      const marker = L.marker([l.lat, l.lng], { icon: makeIcon(idx + 1) });
      marker.bindPopup(
        `<div style="font-family:Outfit,sans-serif;min-width:200px;">
          <div style="font-size:11px;letter-spacing:0.14em;text-transform:uppercase;color:#695A62;">${l.donor_name || ""}</div>
          <div style="font-family:'Cormorant Garamond',serif;font-size:18px;color:#2A1B24;line-height:1.2;margin-top:4px;">${l.name}</div>
          <div style="font-size:12px;color:#695A62;margin-top:6px;">${l.remaining_quantity ?? l.quantity} ${l.unit} · ${(l.category || "").replace("_", " ")}</div>
          ${l.distance_km != null ? `<div style="font-size:11px;color:#C85A40;margin-top:6px;font-weight:600;">${l.distance_km} km away</div>` : ""}
          <a href="#" data-listing="${l.id}" class="fx-popup-link" style="display:inline-block;margin-top:10px;color:#C85A40;font-weight:600;font-size:13px;text-decoration:none;">View listing →</a>
        </div>`
      );
      marker.on("click", () => {
        if (onMarkerClick) onMarkerClick(l);
      });
      marker.addTo(layer);
      bounds.push([l.lat, l.lng]);
    });

    if (bounds.length > 1) {
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
    } else if (bounds.length === 1) {
      map.setView(bounds[0], zoom);
    }

    // Delegate popup link clicks → router navigation
    const handler = (e) => {
      const a = e.target.closest && e.target.closest(".fx-popup-link");
      if (a) {
        e.preventDefault();
        const id = a.getAttribute("data-listing");
        if (id) nav(`/listings/${id}`);
      }
    };
    map.getContainer().addEventListener("click", handler);
    return () => map.getContainer().removeEventListener("click", handler);
  }, [listings, origin, zoom, onMarkerClick, nav]);

  return (
    <div
      ref={containerRef}
      data-testid="map-view"
      style={{
        width: "100%",
        height,
        borderRadius: "1.5rem",
        overflow: "hidden",
        border: "1px solid rgba(42,27,36,0.1)",
        background: "#F4EFE6",
      }}
    />
  );
}
