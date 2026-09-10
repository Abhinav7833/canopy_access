"use client";
import "maplibre-gl/dist/maplibre-gl.css";
import maplibregl, { type Map as MlMap, type Marker, type StyleSpecification } from "maplibre-gl";
import { useEffect, useRef } from "react";
import { bbox, imageCoords } from "@/lib/geo";
import type { Boundary } from "@/lib/types";

export interface MapImage {
  id: string;
  url: string;
  opacity: number;
}

/** A single point marker (e.g. the localization screen's located centroid). */
export interface MapMarker {
  lon: number;
  lat: number;
  label?: string;
}

const MAP_BG_FALLBACK = "#eef1f5";
const ACCENT_FALLBACK = "#0a7c4c";

/** Read a CSS custom property's current runtime value (theme-dependent). MapLibre paint
 * properties are plain strings, not CSS — they can't reference var(...) directly, so we
 * resolve the value ourselves at use-time and re-apply it whenever the theme flips. */
function token(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}

// Static fallback only — this object is a module-level singleton evaluated once at import,
// so it can't carry a live token() read (a later mount after a theme change would still see
// whatever was current at first import). The live color is (re)applied every time a map
// actually mounts, inside map.on("load") below, and again on every theme flip.
const EMPTY_STYLE: StyleSpecification = {
  version: 8,
  sources: {},
  layers: [{ id: "bg", type: "background", paint: { "background-color": MAP_BG_FALLBACK } }],
};

// Reconcile image layers in place. `active` maps layer id -> current source url so we
// update opacity for an unchanged layer (smooth swipe), replace the source if its url
// changes, and add/remove only when the set changes. Never recreates the map.
function sync(map: MlMap, boundary: Boundary, images: MapImage[], active: Map<string, string>) {
  const corners = imageCoords(bbox(boundary.geometry.coordinates));
  const wanted = new Set(images.map((i) => i.id));

  const addLayer = (img: MapImage) => {
    map.addSource(img.id, { type: "image", url: img.url, coordinates: corners });
    map.addLayer(
      { id: img.id, type: "raster", source: img.id, paint: { "raster-opacity": img.opacity } },
      "boundary-line",
    );
    active.set(img.id, img.url);
  };
  const removeLayer = (id: string) => {
    if (map.getLayer(id)) map.removeLayer(id);
    if (map.getSource(id)) map.removeSource(id);
    active.delete(id);
  };

  for (const id of Array.from(active.keys())) {
    if (!wanted.has(id)) removeLayer(id);
  }
  for (const img of images) {
    const currentUrl = active.get(img.id);
    if (currentUrl === undefined) {
      addLayer(img);
    } else if (currentUrl !== img.url) {
      removeLayer(img.id);
      addLayer(img);
    } else {
      map.setPaintProperty(img.id, "raster-opacity", img.opacity);
    }
  }
}

/** Add/replace/remove the single point marker in place — a small accent dot, styled to match
 * the design system rather than MapLibre's default pin. */
function syncMarker(map: MlMap, holder: { current: Marker | null }, marker?: MapMarker) {
  holder.current?.remove();
  holder.current = null;
  if (!marker) return;
  const el = document.createElement("div");
  el.className = "h-3.5 w-3.5 rounded-full border-2 border-white bg-accent shadow-raised";
  const instance = new maplibregl.Marker({ element: el }).setLngLat([marker.lon, marker.lat]);
  if (marker.label) {
    instance.setPopup(
      new maplibregl.Popup({ offset: 14, closeButton: false }).setText(marker.label),
    );
  }
  instance.addTo(map);
  holder.current = instance;
}

export function EvidenceMap({
  boundary,
  images = [],
  marker,
  className = "h-80 w-full overflow-hidden rounded-card border border-border",
}: {
  boundary: Boundary;
  images?: MapImage[];
  marker?: MapMarker;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MlMap | null>(null);
  const loadedRef = useRef(false);
  const imagesRef = useRef<MapImage[]>(images);
  const activeRef = useRef<Map<string, string>>(new Map());
  const markerPropRef = useRef<MapMarker | undefined>(marker);
  const markerInstanceRef = useRef<Marker | null>(null);

  // Create the map once per boundary; draw the outline.
  useEffect(() => {
    if (!ref.current) return;
    const box = bbox(boundary.geometry.coordinates);
    const map = new maplibregl.Map({
      container: ref.current,
      style: EMPTY_STYLE,
      bounds: [box[0], box[1], box[2], box[3]],
      fitBoundsOptions: { padding: 48 },
      attributionControl: false,
    });
    mapRef.current = map;
    loadedRef.current = false;
    activeRef.current = new Map();
    const fitToAoi = () => {
      try {
        map.fitBounds([[box[0], box[1]], [box[2], box[3]]], { padding: 48, animate: false });
      } catch {
        /* the construction-time bounds already stand; never let a refit break rendering */
      }
    };
    map.on("load", () => {
      // Re-apply the live background token now — EMPTY_STYLE only carries the static fallback.
      map.setPaintProperty("bg", "background-color", token("--c-map-bg", MAP_BG_FALLBACK));
      map.addSource("boundary", {
        type: "geojson",
        data: boundary as unknown as GeoJSON.Feature,
      });
      const accent = token("--c-accent", ACCENT_FALLBACK);
      map.addLayer({
        id: "boundary-fill",
        type: "fill",
        source: "boundary",
        paint: { "fill-color": accent, "fill-opacity": 0.06 },
      });
      map.addLayer({
        id: "boundary-line",
        type: "line",
        source: "boundary",
        paint: { "line-color": accent, "line-width": 2 },
      });
      loadedRef.current = true;
      // The container often sizes only after map creation (inside a card/flex), which leaves
      // the initial fitBounds computed against a near-0 box — the AOI then shows as a tiny
      // speck. Draw the imagery first, then resize and refit to the AOI now that we have real
      // dimensions (fit last, so a fit hiccup can never skip the imagery).
      map.resize();
      sync(map, boundary, imagesRef.current, activeRef.current);
      syncMarker(map, markerInstanceRef, markerPropRef.current);
      fitToAoi();
    });
    // Keep the canvas sized to its container; the first time it gains real width, refit the AOI
    // once (covers layout settling after the load handler already ran).
    let didFit = false;
    const ro = new ResizeObserver(() => {
      map.resize();
      if (!didFit && (ref.current?.clientWidth ?? 0) > 0) {
        fitToAoi();
        didFit = true;
      }
    });
    ro.observe(ref.current);

    // Recolor the no-tile background and AOI boundary when the theme flips. MapLibre paint
    // values are resolved once at addLayer time, so a plain CSS var(...) swap in globals.css
    // wouldn't reach them — re-read the tokens and push new paint values on every data-theme
    // mutation instead.
    const themeObserver = new MutationObserver(() => {
      if (!map.isStyleLoaded()) return;
      map.setPaintProperty("bg", "background-color", token("--c-map-bg", MAP_BG_FALLBACK));
      const accent = token("--c-accent", ACCENT_FALLBACK);
      if (map.getLayer("boundary-fill")) {
        map.setPaintProperty("boundary-fill", "fill-color", accent);
      }
      if (map.getLayer("boundary-line")) {
        map.setPaintProperty("boundary-line", "line-color", accent);
      }
    });
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });

    return () => {
      ro.disconnect();
      themeObserver.disconnect();
      markerInstanceRef.current?.remove();
      markerInstanceRef.current = null;
      map.remove();
      mapRef.current = null;
      loadedRef.current = false;
    };
  }, [boundary]);

  // Reconcile whenever images change (opacity updates in place -> smooth swipe).
  useEffect(() => {
    imagesRef.current = images;
    if (mapRef.current && loadedRef.current) {
      sync(mapRef.current, boundary, images, activeRef.current);
    }
  }, [images, boundary]);

  // Reconcile the marker whenever its position/label actually changes. Depend on the
  // primitive fields, not the `marker` object — callers pass a fresh { lon, lat, label }
  // literal every render, so keying on object identity would tear down and rebuild the DOM
  // marker + popup on every unrelated re-render (e.g. each React Query state change).
  useEffect(() => {
    markerPropRef.current = marker;
    if (mapRef.current && loadedRef.current) {
      syncMarker(mapRef.current, markerInstanceRef, marker);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [marker?.lon, marker?.lat, marker?.label, boundary]);

  return <div ref={ref} className={className} />;
}
