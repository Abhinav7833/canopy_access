export type BBox = [number, number, number, number];

export function bbox(coords: number[][][]): BBox {
  const ring = coords?.[0];
  if (!ring || ring.length === 0) return [0, 0, 0, 0];
  let minLng = Infinity,
    minLat = Infinity,
    maxLng = -Infinity,
    maxLat = -Infinity;
  for (const [lng, lat] of ring) {
    minLng = Math.min(minLng, lng);
    maxLng = Math.max(maxLng, lng);
    minLat = Math.min(minLat, lat);
    maxLat = Math.max(maxLat, lat);
  }
  return [minLng, minLat, maxLng, maxLat];
}

export type Corners = [[number, number], [number, number], [number, number], [number, number]];

export function imageCoords([minLng, minLat, maxLng, maxLat]: BBox): Corners {
  // MapLibre image source order: top-left, top-right, bottom-right, bottom-left
  return [
    [minLng, maxLat],
    [maxLng, maxLat],
    [maxLng, minLat],
    [minLng, minLat],
  ];
}
