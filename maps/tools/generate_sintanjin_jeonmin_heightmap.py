"""Generate CS2 playable + worldmap heightmaps, overlays, and guides for the
focused Sintanjin / Daedeok Ind. / Gwanpyeong / Jeonmin-dong / Venture Coop
corridor (~9.89 km x 9.89 km scaled 1.45x to CS2's 14.336 km x 14.336 km).
"""

from concurrent.futures import ThreadPoolExecutor
import argparse
import io
import json
import math
import os
import struct
import urllib.parse
import urllib.request
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Target real-world framing: 9.887 km x 9.887 km (1.45x -> 14.336 km CS2)
CENTER_LAT = 36.4200
CENTER_LON = 127.4045
SCALE_FACTOR = 1.45
CS2_SIDE_M = 14336.0
REAL_SIDE_M = CS2_SIDE_M / SCALE_FACTOR  # 9886.8965 m

WORLD_MULTIPLIER = 4  # CS2 WorldMap = 4x Playable width (57,344 m)
WATER_SEA_LEVEL_M = 24.0
START_AQUIFER = ("지하수: 시작 지역 신탄진·석봉동", 36.4510, 127.4235, 620.0, 520.0, 1.0)

M_PER_DEG_LAT = 111132.95
M_PER_DEG_LON = (
    111412.84 * math.cos(math.radians(CENTER_LAT))
    - 93.5 * math.cos(3.0 * math.radians(CENTER_LAT))
)


def compute_bounds(center_lat: float, center_lon: float, side_m: float):
    """Return (lat_n, lat_s, lon_w, lon_e) for a square of side_m meters."""
    dlat = (side_m * 0.5) / M_PER_DEG_LAT
    dlon = (side_m * 0.5) / M_PER_DEG_LON
    return center_lat + dlat, center_lat - dlat, center_lon - dlon, center_lon + dlon


def deg2num_f(lat_deg: float, lon_deg: float, zoom: int):
    """Fractional Web Mercator slippy-map tile coordinates."""
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    x = (lon_deg + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
    return x, y


def fetch_url_cached(url: str, cache_path: str, data: bytes | None = None, timeout: int = 25) -> bytes:
    """Download URL with disk caching."""
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            return f.read()
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "CitiesSimulatorHeightmap/2.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    with open(cache_path, "wb") as f:
        f.write(raw)
    return raw


def fetch_terrarium_grid(lat_n: float, lat_s: float, lon_w: float, lon_e: float, zoom: int, cache_dir: str):
    """Fetch and assemble AWS Terrarium tiles plus exact fractional pixel window."""
    x0f, y0f = deg2num_f(lat_n, lon_w, zoom)
    x1f, y1f = deg2num_f(lat_s, lon_e, zoom)
    tx0, ty0 = int(math.floor(x0f)), int(math.floor(y0f))
    tx1, ty1 = int(math.floor(x1f)), int(math.floor(y1f))

    nx, ny = tx1 - tx0 + 1, ty1 - ty0 + 1
    dem = np.zeros((ny * 256, nx * 256), dtype=np.float32)

    def _load(tx_ty):
        tx, ty = tx_ty
        url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{zoom}/{tx}/{ty}.png"
        cpath = os.path.join(cache_dir, f"terrarium_z{zoom}", f"{tx}_{ty}.png")
        raw = fetch_url_cached(url, cpath, timeout=15)
        arr = np.array(Image.open(io.BytesIO(raw)).convert("RGB"), dtype=np.float32)
        elev = (arr[:, :, 0] * 256.0 + arr[:, :, 1] + arr[:, :, 2] / 256.0) - 32768.0
        return tx, ty, elev

    coords = [(tx, ty) for ty in range(ty0, ty1 + 1) for tx in range(tx0, tx1 + 1)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        for tx, ty, elev in pool.map(_load, coords):
            iy, ix = ty - ty0, tx - tx0
            dem[iy * 256 : (iy + 1) * 256, ix * 256 : (ix + 1) * 256] = elev

    px0, py0 = (x0f - tx0) * 256.0, (y0f - ty0) * 256.0
    px1, py1 = (x1f - tx0) * 256.0, (y1f - ty0) * 256.0
    return dem, (px0, py0, px1, py1)


def repair_dem_voids(
    dem: np.ndarray, min_valid_m: float = 18.0, spike_thresh_m: float = 8.0, dilate_px: int = 3
) -> tuple[np.ndarray, int]:
    """Repair Terrarium nodata/bathymetry glitches and their interpolated halos via neighbor inpainting."""
    out = dem.copy()
    bad = (~np.isfinite(out)) | (out < min_valid_m)
    if spike_thresh_m > 0:
        med_approx = np.median(
            np.stack(
                [
                    np.roll(np.roll(out, dy, axis=0), dx, axis=1)
                    for dy in (-2, 0, 2)
                    for dx in (-2, 0, 2)
                    if not (dy == 0 and dx == 0)
                ],
                axis=0,
            ),
            axis=0,
        )
        bad |= (med_approx - out) > spike_thresh_m

    # Dilate bad mask to discard bilinearly-corrupted halo pixels surrounding -2500m voids
    if bad.any() and dilate_px > 0:
        bad_u8 = Image.fromarray((bad.astype(np.uint8) * 255))
        bad_u8 = bad_u8.filter(ImageFilter.MaxFilter(2 * dilate_px + 1))
        bad = np.array(bad_u8) > 127

    n_bad = int(bad.sum())
    if n_bad == 0:
        return out, 0

    valid = ~bad
    out[bad] = 0.0
    for _ in range(60):
        if valid.all():
            break
        vp = np.pad(valid.astype(np.float32), 1, mode="edge")
        op = np.pad(out, 1, mode="edge")
        cnt = (
            vp[:-2, :-2] + vp[:-2, 1:-1] + vp[:-2, 2:]
            + vp[1:-1, :-2] + vp[1:-1, 2:]
            + vp[2:, :-2] + vp[2:, 1:-1] + vp[2:, 2:]
        )
        acc = (
            op[:-2, :-2] + op[:-2, 1:-1] + op[:-2, 2:]
            + op[1:-1, :-2] + op[1:-1, 2:]
            + op[2:, :-2] + op[2:, 1:-1] + op[2:, 2:]
        )
        fill = (~valid) & (cnt > 0)
        if not fill.any():
            break
        out[fill] = acc[fill] / cnt[fill]
        valid[fill] = True
    return out, n_bad


def resample_mercator_window(
    grid: np.ndarray, px_box: tuple[float, float, float, float],
    lat_n: float, lat_s: float, lon_w: float, lon_e: float,
    tx0: float, ty0: float, zoom: int, out_size: int = 4096
) -> np.ndarray:
    """Resample DEM onto an exact equirectangular linear meter grid using Mercator coords."""
    lats = np.linspace(lat_n, lat_s, out_size, dtype=np.float64)
    lons = np.linspace(lon_w, lon_e, out_size, dtype=np.float64)

    n = 2.0 ** zoom
    lat_rad = np.radians(lats)
    y_tile = (1.0 - np.arcsinh(np.tan(lat_rad)) / math.pi) / 2.0 * n
    x_tile = (lons + 180.0) / 360.0 * n

    py = (y_tile - ty0) * 256.0
    px = (x_tile - tx0) * 256.0

    h, w = grid.shape
    ix = np.clip(np.floor(px).astype(np.int32), 0, w - 2)
    iy = np.clip(np.floor(py).astype(np.int32), 0, h - 2)
    fx = (px - ix).astype(np.float32)[None, :]
    fy = (py - iy).astype(np.float32)[:, None]

    # Sample in row strips to keep peak memory small
    out = np.empty((out_size, out_size), dtype=np.float32)
    strip = 512
    for r0 in range(0, out_size, strip):
        r1 = min(out_size, r0 + strip)
        y_idx = iy[r0:r1][:, None]
        x_idx = ix[None, :]
        v00 = grid[y_idx, x_idx]
        v01 = grid[y_idx, x_idx + 1]
        v10 = grid[y_idx + 1, x_idx]
        v11 = grid[y_idx + 1, x_idx + 1]
        fy_s = fy[r0:r1]
        out[r0:r1] = (
            v00 * (1.0 - fx) * (1.0 - fy_s)
            + v01 * fx * (1.0 - fy_s)
            + v10 * (1.0 - fx) * fy_s
            + v11 * fx * fy_s
        )
    return out


def gaussian_blur_f32(arr: np.ndarray, sigma: float) -> np.ndarray:
    """Fast O(N) 3-pass separable box blur approximating a Gaussian of std=sigma."""
    if sigma <= 0.25:
        return arr.copy()
    w_ideal = math.sqrt((12.0 * sigma * sigma / 3.0) + 1.0)
    wl = int(math.floor(w_ideal))
    if wl % 2 == 0:
        wl -= 1
    r = max(1, wl // 2)
    k = 2 * r + 1
    out = arr.astype(np.float32, copy=True)
    for _ in range(3):
        p = np.pad(out, ((0, 0), (r + 1, r)), mode="edge")
        cs = np.cumsum(p, axis=1, dtype=np.float64)
        out = ((cs[:, k:] - cs[:, :-k]) / k).astype(np.float32)
        p = np.pad(out, ((r + 1, r), (0, 0)), mode="edge")
        cs = np.cumsum(p, axis=0, dtype=np.float64)
        out = ((cs[k:, :] - cs[:-k, :]) / k).astype(np.float32)
    return out


def exact_gaussian_f32(arr: np.ndarray, sigma: float) -> np.ndarray:
    """Isotropic separable Gaussian smoothing in float32 with reflect boundary padding."""
    if sigma <= 0.1:
        return arr.astype(np.float32, copy=True)
    if sigma >= 14.0:
        h, w = arr.shape
        small = np.array(Image.fromarray(arr, mode="F").resize((w // 2, h // 2), Image.BILINEAR), dtype=np.float32)
        bl = exact_gaussian_f32(small, sigma * 0.5)
        return np.array(Image.fromarray(bl, mode="F").resize((w, h), Image.BICUBIC), dtype=np.float32)

    r = int(math.ceil(3.0 * sigma))
    x = np.arange(-r, r + 1, dtype=np.float32)
    kernel = np.exp(-0.5 * (x / sigma) ** 2)
    kernel /= kernel.sum()

    px = np.pad(arr.astype(np.float32, copy=False), ((0, 0), (r, r)), mode="reflect")
    out_x = np.zeros_like(arr, dtype=np.float32)
    for i, w in enumerate(kernel):
        out_x += w * px[:, i : i + arr.shape[1]]

    py = np.pad(out_x, ((r, r), (0, 0)), mode="reflect")
    out = np.zeros_like(arr, dtype=np.float32)
    for i, w in enumerate(kernel):
        out += w * py[i : i + arr.shape[0], :]
    return out


def cubic_bspline_resample(src: np.ndarray, rows_f: np.ndarray, cols_f: np.ndarray) -> np.ndarray:
    """Resample 2D float32 array onto (rows_f, cols_f) with separable C2 cubic B-spline interpolation."""
    def _weights(t: np.ndarray):
        omt = 1.0 - t
        return (
            (omt ** 3) / 6.0,
            (3.0 * t ** 3 - 6.0 * t ** 2 + 4.0) / 6.0,
            (-3.0 * t ** 3 + 3.0 * t ** 2 + 3.0 * t + 1.0) / 6.0,
            (t ** 3) / 6.0,
        )

    iy = np.clip(np.floor(rows_f).astype(np.int32), 1, src.shape[0] - 3)
    fy = np.clip(rows_f - iy, 0.0, 1.0).astype(np.float32)
    ix = np.clip(np.floor(cols_f).astype(np.int32), 1, src.shape[1] - 3)
    fx = np.clip(cols_f - ix, 0.0, 1.0).astype(np.float32)

    r_min = max(0, int(iy.min()) - 1)
    r_max = min(src.shape[0] - 1, int(iy.max()) + 2)
    sub = src[r_min : r_max + 1]

    wx0, wx1, wx2, wx3 = _weights(fx)
    horiz = (
        sub[:, ix - 1] * wx0[None, :]
        + sub[:, ix] * wx1[None, :]
        + sub[:, ix + 1] * wx2[None, :]
        + sub[:, ix + 2] * wx3[None, :]
    )

    iy_rel = iy - r_min
    wy0, wy1, wy2, wy3 = _weights(fy)
    return (
        horiz[iy_rel - 1] * wy0[:, None]
        + horiz[iy_rel] * wy1[:, None]
        + horiz[iy_rel + 1] * wy2[:, None]
        + horiz[iy_rel + 2] * wy3[:, None]
    ).astype(np.float32)


def fetch_copernicus_glo30_window(
    lat_n: float, lat_s: float, lon_w: float, lon_e: float, cache_dir: str,
    out_size: int = 4096, row_shift: float = 0.16, col_shift: float = 0.19
) -> np.ndarray:
    """Fetch Copernicus GLO-30 COG float32 tiles (N36_00_E127_00) via HTTP Range and C2 B-spline resample."""
    if not (36.0 <= lat_s <= lat_n <= 37.0 and 127.0 <= lon_w <= lon_e <= 128.0):
        raise ValueError("Bounds fall outside Copernicus N36_00_E127_00 tile")

    url = (
        "https://copernicus-dem-30m.s3.amazonaws.com/"
        "Copernicus_DSM_COG_10_N36_00_E127_00_DEM/"
        "Copernicus_DSM_COG_10_N36_00_E127_00_DEM.tif"
    )
    cop_cache = os.path.join(cache_dir, "copernicus_glo30")
    os.makedirs(cop_cache, exist_ok=True)

    def _fetch_range(start: int, length: int, cpath: str) -> bytes:
        if os.path.exists(cpath):
            with open(cpath, "rb") as f:
                return f.read()
        req = urllib.request.Request(
            url,
            headers={"Range": f"bytes={start}-{start + length - 1}", "User-Agent": "CitiesSimulatorHeightmap/2.0"},
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw = resp.read()
        with open(cpath, "wb") as f:
            f.write(raw)
        return raw

    hdr = _fetch_range(0, 32768, os.path.join(cop_cache, "N36_E127_hdr.bin"))
    ifd_off = struct.unpack("<I", hdr[4:8])[0]
    num_tags = struct.unpack("<H", hdr[ifd_off : ifd_off + 2])[0]
    tags = {}
    for i in range(num_tags):
        pos = ifd_off + 2 + i * 12
        tag, typ, cnt, val = struct.unpack("<HHII", hdr[pos : pos + 12])
        tags[tag] = (typ, cnt, val)
    tile_offs = struct.unpack("<16I", hdr[tags[324][2] : tags[324][2] + 64])
    tile_lens = struct.unpack("<16I", hdr[tags[325][2] : tags[325][2] + 64])

    gr0, gr1 = (37.0 - lat_n) * 3600.0, (37.0 - lat_s) * 3600.0
    gc0, gc1 = (lon_w - 127.0) * 3600.0, (lon_e - 127.0) * 3600.0
    tr0 = max(0, int(math.floor(gr0 - 3)) // 1024)
    tr1 = min(3, int(math.floor(gr1 + 3)) // 1024)
    tc0 = max(0, int(math.floor(gc0 - 3)) // 1024)
    tc1 = min(3, int(math.floor(gc1 + 3)) // 1024)

    def _decode_tile(tr_tc):
        tr, tc = tr_tc
        idx = tr * 4 + tc
        raw_z = _fetch_range(tile_offs[idx], tile_lens[idx], os.path.join(cop_cache, f"N36_E127_t{idx}.zlib"))
        raw = zlib.decompress(raw_z)
        u = np.frombuffer(raw, dtype=np.uint8).reshape(1024, 1024 * 4)
        acc = np.cumsum(u, axis=1, dtype=np.uint8)
        planes = acc.reshape(1024, 4, 1024)
        return tr, tc, planes.transpose(0, 2, 1)[:, :, ::-1].copy().view("<f4").reshape(1024, 1024)

    mosaic = np.zeros(((tr1 - tr0 + 1) * 1024, (tc1 - tc0 + 1) * 1024), dtype=np.float32)
    tile_coords = [(tr, tc) for tr in range(tr0, tr1 + 1) for tc in range(tc0, tc1 + 1)]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for tr, tc, arr in pool.map(_decode_tile, tile_coords):
            ry, rx = (tr - tr0) * 1024, (tc - tc0) * 1024
            mosaic[ry : ry + 1024, rx : rx + 1024] = arr

    rows_f = np.linspace(gr0 - tr0 * 1024.0, gr1 - tr0 * 1024.0, out_size, dtype=np.float64) + row_shift
    cols_f = np.linspace(gc0 - tc0 * 1024.0, gc1 - tc0 * 1024.0, out_size, dtype=np.float64) + col_shift
    return cubic_bspline_resample(mosaic, rows_f, cols_f)


def fetch_osm_features(lat_n: float, lat_s: float, lon_w: float, lon_e: float, osm_cache_path: str):
    """Load cached or fetch Overpass OSM water/landuse/highway/railway geometry."""
    for candidate in (osm_cache_path, os.path.join(os.path.dirname(osm_cache_path), "osm_collage_area.json")):
        if os.path.exists(candidate):
            with open(candidate, "r", encoding="utf-8") as f:
                return json.load(f)

    pad = 0.015
    bbox = f"{lat_s - pad:.4f},{lon_w - pad:.4f},{lat_n + pad:.4f},{lon_e + pad:.4f}"
    q = f"""[out:json][timeout:35];
(
  way["waterway"~"river|canal"]({bbox});
  relation["waterway"="river"]({bbox});
  way["natural"="water"]({bbox});
  relation["natural"="water"]({bbox});
  way["highway"~"motorway|motorway_link|trunk|trunk_link|primary"]({bbox});
  way["railway"="rail"]({bbox});
  way["landuse"~"industrial|residential|commercial|railway"]({bbox});
  relation["landuse"~"industrial|residential|railway"]({bbox});
);
out body;
>;
out skel qt;
"""
    raw = None
    for endpoint in ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"):
        try:
            body = urllib.parse.urlencode({"data": q}).encode("utf-8")
            req = urllib.request.Request(endpoint, data=body, headers={"User-Agent": "CitiesSimulatorHeightmap/2.0"})
            with urllib.request.urlopen(req, timeout=40) as resp:
                raw = resp.read().decode("utf-8")
            break
        except Exception as exc:
            print(f"Overpass fallback from {endpoint}: {exc}")
    if raw is None:
        raise RuntimeError("Unable to fetch OSM data from Overpass")
    data = json.loads(raw)
    os.makedirs(os.path.dirname(osm_cache_path), exist_ok=True)
    with open(osm_cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return data


def stitch_ring_segments(way_node_lists: list[list[int]]) -> list[list[int]]:
    """Stitch open OSM way node lists into closed rings when possible."""
    unused = [list(w) for w in way_node_lists if len(w) >= 2]
    rings = []
    while unused:
        cur = unused.pop(0)
        changed = True
        while cur[0] != cur[-1] and changed:
            changed = False
            for idx, seg in enumerate(unused):
                if seg[0] == cur[-1]:
                    cur.extend(seg[1:])
                    unused.pop(idx)
                    changed = True
                    break
                if seg[-1] == cur[-1]:
                    cur.extend(reversed(seg[:-1]))
                    unused.pop(idx)
                    changed = True
                    break
                if seg[-1] == cur[0]:
                    cur = seg[:-1] + cur
                    unused.pop(idx)
                    changed = True
                    break
                if seg[0] == cur[0]:
                    cur = list(reversed(seg[1:])) + cur
                    unused.pop(idx)
                    changed = True
                    break
        rings.append(cur)
    return rings


def rasterize_osm_masks(osm: dict, lat_n: float, lat_s: float, lon_w: float, lon_e: float, size: int = 4096):
    """Build pixel-aligned masks (Geumgang, Gapcheon, ponds, urban flats, forest, highways, rail)."""
    nodes = {e["id"]: (e["lat"], e["lon"]) for e in osm["elements"] if e["type"] == "node"}
    ways = {e["id"]: e for e in osm["elements"] if e["type"] == "way"}

    def to_px(lat: float, lon: float):
        x = (lon - lon_w) / (lon_e - lon_w) * (size - 1)
        y = (lat_n - lat) / (lat_n - lat_s) * (size - 1)
        return (x, y)

    def pts_from_nids(nids):
        return [to_px(*nodes[n]) for n in nids if n in nodes]

    def draw_multipolygon(draw: ImageDraw.ImageDraw, rel: dict):
        outers, inners = [], []
        for m in rel.get("members", []):
            if m.get("type") == "way" and m["ref"] in ways:
                w = ways[m["ref"]]
                role = m.get("role", "outer")
                (inners if role == "inner" else outers).append(w.get("nodes", []))
        for ring in stitch_ring_segments(outers):
            pts = pts_from_nids(ring)
            if len(pts) >= 3:
                draw.polygon(pts, fill=255)
        for ring in stitch_ring_segments(inners):
            pts = pts_from_nids(ring)
            if len(pts) >= 3:
                draw.polygon(pts, fill=0)

    im_geum = Image.new("L", (size, size), 0)
    im_gap = Image.new("L", (size, size), 0)
    im_urban = Image.new("L", (size, size), 0)
    im_forest = Image.new("L", (size, size), 0)
    im_hwy = Image.new("L", (size, size), 0)
    im_rail = Image.new("L", (size, size), 0)

    d_geum = ImageDraw.Draw(im_geum)
    d_gap = ImageDraw.Draw(im_gap)
    d_urb = ImageDraw.Draw(im_urban)
    d_for = ImageDraw.Draw(im_forest)
    d_hwy = ImageDraw.Draw(im_hwy)
    d_rail = ImageDraw.Draw(im_rail)

    # First draw explicit river water polygons (separating Gapcheon south/west vs Geumgang north)
    for e in osm["elements"]:
        t = e.get("tags", {})
        if e["type"] == "relation" and t.get("natural") == "water" and t.get("water") == "river":
            # Rel 67488 & 17344592 are Gapcheon; split/classify by centroid latitude
            sample_lats = [
                nodes[nid][0]
                for m in e.get("members", [])
                if m["ref"] in ways
                for nid in ways[m["ref"]].get("nodes", [])[:5]
                if nid in nodes
            ]
            if not sample_lats:
                continue
            avg_lat = sum(sample_lats) / len(sample_lats)
            draw_multipolygon(d_geum if avg_lat > 36.448 else d_gap, e)

        elif e["type"] == "way" and t.get("natural") == "water":
            if t.get("reservoir_type") == "waste_water" or t.get("golf"):
                continue
            if t.get("water") == "river" or "금강" in t.get("name", ""):
                pts = pts_from_nids(e.get("nodes", []))
                if len(pts) >= 3:
                    lats = [nodes[n][0] for n in e.get("nodes", []) if n in nodes]
                    lons = [nodes[n][1] for n in e.get("nodes", []) if n in nodes]
                    avg_lat = sum(lats) / len(lats)
                    avg_lon = sum(lons) / len(lons)
                    # Gapcheon flows NW up to ~36.453, 127.392; Geumgang stays along north > 36.447 east of 127.392
                    is_geum = ("금강" in t.get("name", "")) or (avg_lat > 36.447 and avg_lon > 127.390) or (avg_lat > 36.4535)
                    (d_geum if is_geum else d_gap).polygon(pts, fill=255)

        elif e["type"] == "way" and t.get("waterway") == "river":
            name = t.get("name", "")
            pts = pts_from_nids(e.get("nodes", []))
            if len(pts) >= 2:
                if "금강" in name:
                    d_geum.line(pts, fill=255, width=max(14, int(size * 0.005)))
                elif "갑천" in name:
                    d_gap.line(pts, fill=255, width=max(10, int(size * 0.004)))

        elif t.get("landuse") in ("industrial", "residential", "commercial", "railway"):
            if e["type"] == "way":
                pts = pts_from_nids(e.get("nodes", []))
                if len(pts) >= 3:
                    d_urb.polygon(pts, fill=255)
            elif e["type"] == "relation":
                draw_multipolygon(d_urb, e)

        elif t.get("landuse") == "forest" or t.get("natural") == "wood":
            if e["type"] == "way":
                pts = pts_from_nids(e.get("nodes", []))
                if len(pts) >= 3:
                    d_for.polygon(pts, fill=255)
            elif e["type"] == "relation":
                draw_multipolygon(d_for, e)

        if e["type"] == "way" and t.get("highway") in ("motorway", "motorway_link", "trunk", "trunk_link", "primary"):
            pts = pts_from_nids(e.get("nodes", []))
            if len(pts) >= 2:
                d_hwy.line(pts, fill=255, width=max(6, int(size * 0.0025)))

        if e["type"] == "way" and t.get("railway") == "rail":
            pts = pts_from_nids(e.get("nodes", []))
            if len(pts) >= 2:
                d_rail.line(pts, fill=255, width=max(4, int(size * 0.0018)))

    # Smooth OSM way 30143681 abrupt floodplain notch near Wonchon Wastewater Plant (lat 36.380..36.386)
    # so the west bank tapers naturally past Wonchon-gyo without a sudden horizontal constriction
    d_gap.polygon(
        [
            (2263.0 * (size / 4096.0), 3590.0 * (size / 4096.0)),
            (2266.0 * (size / 4096.0), 3675.0 * (size / 4096.0)),
            (2273.0 * (size / 4096.0), 3745.0 * (size / 4096.0)),
            (2277.0 * (size / 4096.0), 3820.0 * (size / 4096.0)),
            (2270.0 * (size / 4096.0), 3890.0 * (size / 4096.0)),
            (2253.0 * (size / 4096.0), 3926.0 * (size / 4096.0)),
            (2285.0 * (size / 4096.0), 3926.0 * (size / 4096.0)),
            (2315.0 * (size / 4096.0), 3815.0 * (size / 4096.0)),
            (2315.0 * (size / 4096.0), 3590.0 * (size / 4096.0)),
        ],
        fill=255,
    )

    # Isotropic Gaussian level-set curvature smoothing (eliminates square morphological facets & thin weir spurs)
    def _clean_river_mask(im: Image.Image) -> Image.Image:
        arr_f = (np.array(im) > 127).astype(np.float32)
        sm = exact_gaussian_f32(arr_f, 7.5 * (size / 4096.0))
        return Image.fromarray(((sm >= 0.48).astype(np.uint8) * 255), mode="L")

    im_geum = _clean_river_mask(im_geum)
    im_gap = _clean_river_mask(im_gap)

    # Close interior isolated islands inside union (completely surrounded by river water)
    u_geum = np.array(im_geum) > 127
    u_gap = np.array(im_gap) > 127
    inv_u = Image.fromarray(((~(u_geum | u_gap)).astype(np.uint8) * 255), mode="L")
    pad = Image.new("L", (size + 2, size + 2), 255)
    pad.paste(inv_u, (1, 1))
    ImageDraw.floodfill(pad, (0, 0), 128)
    holes = np.array(pad)[1:-1, 1:-1] == 255
    if holes.any():
        # Assign closed holes to whichever river channel encloses them
        geum_dil = np.array(im_geum.filter(ImageFilter.MaxFilter(9))) > 127
        u_geum[holes & geum_dil] = True
        u_gap[holes & (~geum_dil)] = True
        im_geum = Image.fromarray((u_geum.astype(np.uint8) * 255), mode="L")
        im_gap = Image.fromarray((u_gap.astype(np.uint8) * 255), mode="L")

    return {
        "geumgang": im_geum,
        "gapcheon": im_gap,
        "urban": im_urban,
        "forest": im_forest,
        "highways": im_hwy,
        "rail": im_rail,
    }


def _smooth_max(a: np.ndarray, b: np.ndarray | float, k: float = 1.2) -> np.ndarray:
    """C-infinity smooth maximum max(a, b) without derivative kinks."""
    return 0.5 * (a + b + np.sqrt((a - b) ** 2 + k * k))


def _smoothstep(t: np.ndarray) -> np.ndarray:
    """Standard C1 cubic Hermite smoothstep clamped to [0, 1]."""
    c = np.clip(t, 0.0, 1.0)
    return c * c * (3.0 - 2.0 * c)


def _signed_distance_px4096(mask_4096: np.ndarray, max_half_iters: int = 32) -> np.ndarray:
    """High-smooth pure-NumPy Chamfer signed distance field using full-res near-bank SDF + Gaussian C2 smoothing."""
    half = mask_4096.shape[0] // 2
    m_small = np.array(
        Image.fromarray((mask_4096.astype(np.uint8) * 255), mode="L").resize((half, half), Image.BILINEAR)
    ) > 127

    def _edt(seed: np.ndarray, iters: int, cap: float) -> np.ndarray:
        d = np.where(seed, 0.0, cap).astype(np.float32)
        diag = 1.41421356
        for _ in range(iters):
            p = np.pad(d, 1, mode="edge")
            d = np.minimum(d, p[1:-1, :-2] + 1.0)
            d = np.minimum(d, p[1:-1, 2:] + 1.0)
            d = np.minimum(d, p[:-2, 1:-1] + 1.0)
            d = np.minimum(d, p[2:, 1:-1] + 1.0)
            d = np.minimum(d, p[:-2, :-2] + diag)
            d = np.minimum(d, p[:-2, 2:] + diag)
            d = np.minimum(d, p[2:, :-2] + diag)
            d = np.minimum(d, p[2:, 2:] + diag)
        return d

    d_out_h = _edt(m_small, max_half_iters, float(max_half_iters * 2))
    d_in_h = _edt(~m_small, min(20, max_half_iters), float(max_half_iters * 2))
    sdf_far = np.array(
        Image.fromarray((d_out_h - d_in_h) * 2.0, mode="F").resize(mask_4096.shape[::-1], Image.BICUBIC),
        dtype=np.float32,
    )

    # Compute exact full-4096 near-bank Chamfer (eliminates 2048px 7m shoreline stair-stepping)
    near_iters = 18
    d_out_n = _edt(mask_4096, near_iters, float(near_iters + 4))
    d_in_n = _edt(~mask_4096, near_iters, float(near_iters + 4))
    sdf_near = d_out_n - d_in_n

    far_w = np.clip((np.abs(sdf_far) - 11.0) / 6.0, 0.0, 1.0)
    sdf_blended = sdf_near * (1.0 - far_w) + sdf_far * far_w
    return exact_gaussian_f32(sdf_blended, 5.5)


def apply_river_and_terrace_engineering(elev: np.ndarray, masks: dict) -> tuple[np.ndarray, np.ndarray]:
    """Carve C1-smooth Geumgang/Gapcheon channels with zero cliffs/potholes and continuous plain terracing."""
    size = elev.shape[0]
    out = exact_gaussian_f32(elev, 1.5)

    geum_u8 = np.array(masks["geumgang"]) > 127
    gap_u8 = np.array(masks["gapcheon"]) > 127
    river_u8 = geum_u8 | gap_u8
    sdf = _signed_distance_px4096(river_u8, max_half_iters=32)  # <0 river, 0 shoreline, >0 land (1 px = 3.5m CS2)

    # Target riverbed elevation: downstream gentle gradient well below 24.0m Sea Level
    y_norm = np.linspace(0.0, 1.0, size, dtype=np.float32)[:, None]
    x_norm = np.linspace(0.0, 1.0, size, dtype=np.float32)[None, :]
    bed_gap = 17.2 + 3.8 * np.clip((y_norm - 0.12) / 0.88, 0.0, 1.0)
    bed_geum = 16.5 + 3.8 * np.clip(x_norm, 0.0, 1.0) * np.clip((y_norm + 0.15), 0.0, 1.0)

    geum_f = np.array(masks["geumgang"].filter(ImageFilter.GaussianBlur(radius=10.0)), dtype=np.float32) / 255.0
    gap_f = np.array(masks["gapcheon"].filter(ImageFilter.GaussianBlur(radius=10.0)), dtype=np.float32) / 255.0
    tot = np.maximum(geum_f + gap_f, 1e-5)
    target_bed = np.where((geum_f + gap_f) < 0.02, 18.0, (geum_f * bed_geum + gap_f * bed_gap) / tot)

    # Ensure NO dry inland floodplain anywhere on the map falls below 26.2m (> 24.0m Sea Level)
    dry_zone_w = _smoothstep((sdf - 1.5) / 6.0)
    out = out * (1.0 - dry_zone_w) + _smooth_max(out, 26.2, k=1.2) * dry_zone_w

    # Smooth reference ground outside river: strictly >=27.0m along levees, untouched on hillslopes
    sm_ground = exact_gaussian_f32(out, 10.0)
    bank_floor = _smooth_max(sm_ground, 27.0, k=1.5)

    # C1 smooth channel embankment across sdf in [-9.0 .. +11.0] px (~70m CS2):
    bank_u = _smoothstep((sdf + 9.0) / 20.0)
    river_profile = target_bed * (1.0 - bank_u) + bank_floor * bank_u

    # Blend smoothly back to dry land over sdf in [+11 .. +41] px
    near_river_w = 1.0 - _smoothstep((sdf - 11.0) / 30.0)
    out = out * (1.0 - near_river_w) + river_profile * near_river_w

    # Smooth continuous terracing for low-slope buildable industrial/urban parcels (NO hard threshold!)
    macro_elev = exact_gaussian_f32(out, 18.0)
    gy, gx = np.gradient(macro_elev)
    slope = np.hypot(gx, gy) / (REAL_SIDE_M / size)
    urb_mask_im = masks["urban"].filter(ImageFilter.MaxFilter(11)).filter(ImageFilter.GaussianBlur(radius=12.0))
    urb_w = np.array(urb_mask_im, dtype=np.float32) / 255.0
    flat_ok = np.clip((0.12 - slope) / 0.06, 0.0, 1.0) * np.clip((75.0 - macro_elev) / 14.0, 0.0, 1.0)
    no_river = _smoothstep((sdf - 4.0) / 16.0)
    terrace_w = np.clip(urb_w * flat_ok * no_river * 0.78, 0.0, 0.80)

    out_terraced = _smooth_max(macro_elev, 26.8, k=1.2)
    out = out * (1.0 - terrace_w) + out_terraced * terrace_w

    # Subtle highway corridor smoothing on non-mountain sections
    hwy_w = np.array(masks["highways"].filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(radius=6.0)), dtype=np.float32) / 255.0
    hwy_w *= no_river * np.clip((0.12 - slope) / 0.06, 0.0, 1.0) * 0.5
    out_hwy = exact_gaussian_f32(out, 8.0)
    out = out * (1.0 - hwy_w) + out_hwy * hwy_w

    water_mask = out < WATER_SEA_LEVEL_M
    return out.astype(np.float32), water_mask


def polish_mountain_terrain(
    elev: np.ndarray, masks: dict,
    lat_n: float, lat_s: float, lon_w: float, lon_e: float, cache_dir: str
) -> np.ndarray:
    """Apply subtle C2 isotropic polish to mountain ridges while preserving smooth floodplains and riverbeds."""
    size = elev.shape[0]
    macro = exact_gaussian_f32(elev, 16.0)
    gy_m, gx_m = np.gradient(macro, REAL_SIDE_M / size)
    slope_m = np.hypot(gx_m, gy_m)

    # Strictly continuous protection near rivers, urban flats, and highways (zero hard steps!)
    geum_u8 = np.array(masks["geumgang"]) > 127
    gap_u8 = np.array(masks["gapcheon"]) > 127
    river_union = Image.fromarray(((geum_u8 | gap_u8).astype(np.uint8) * 255), mode="L")
    river_prot = np.clip(
        np.array(river_union.filter(ImageFilter.MaxFilter(41)).filter(ImageFilter.GaussianBlur(radius=24.0)), dtype=np.float32)
        / 255.0
        * 1.5,
        0.0,
        1.0,
    )

    urb_prot = np.array(masks["urban"].filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(radius=12.0)), dtype=np.float32) / 255.0
    urb_prot *= np.clip((0.12 - slope_m) / 0.06, 0.0, 1.0) * np.clip((72.0 - macro) / 14.0, 0.0, 1.0)
    hwy_prot = np.array(masks["highways"].filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(radius=8.0)), dtype=np.float32) / 255.0
    hwy_prot *= np.clip((0.12 - slope_m) / 0.06, 0.0, 1.0)

    elev_hill = np.clip((macro - 40.0) / 20.0, 0.0, 1.0)
    slope_hill = np.clip((slope_m - 0.06) / 0.06, 0.0, 1.0) * np.clip((macro - 32.0) / 10.0, 0.0, 1.0)
    w_mtn = np.maximum(elev_hill, slope_hill)
    w_mtn *= (1.0 - np.clip(urb_prot, 0.0, 1.0)) * (1.0 - np.clip(hwy_prot, 0.0, 1.0)) * (1.0 - river_prot)
    w_mtn = exact_gaussian_f32(w_mtn, 12.0)

    try:
        cop_bs = fetch_copernicus_glo30_window(lat_n, lat_s, lon_w, lon_e, cache_dir, out_size=size)
        cop_smooth = exact_gaussian_f32(cop_bs, 4.5)
        mtn_target = exact_gaussian_f32(elev, 20.0) + (cop_smooth - exact_gaussian_f32(cop_smooth, 20.0))
        print("  Mountain polish: Copernicus GLO-30 C2 B-spline + sigma=4.5 frequency-split applied")
    except Exception as exc:
        print(f"  Mountain polish fallback (isotropic smoothing): {exc}")
        mtn_target = exact_gaussian_f32(elev, 6.5)

    return (elev * (1.0 - w_mtn) + mtn_target * w_mtn).astype(np.float32)


def fetch_satellite_overlay(lat_n: float, lat_s: float, lon_w: float, lon_e: float, cache_dir: str, out_size: int = 4096, zoom: int | None = None) -> Image.Image:
    """Fetch Esri World Imagery tiles and resample onto the exact linear-meter playable grid."""
    if not (lat_n > lat_s and lon_e > lon_w and 0 < out_size <= 16384):
        raise ValueError("Invalid bounds or output size (1..16384)")
    if zoom is None:
        zoom = min(19, max(0, math.ceil(math.log2(out_size * 360 / ((lon_e - lon_w) * 256)))))
    if not 0 <= zoom <= 19:
        raise ValueError("Imagery zoom must be 0..19")
    x0f, y0f = deg2num_f(lat_n, lon_w, zoom)
    x1f, y1f = deg2num_f(lat_s, lon_e, zoom)
    tx0, ty0 = int(math.floor(x0f)), int(math.floor(y0f))
    tx1, ty1 = int(math.floor(x1f)), int(math.floor(y1f))

    nx, ny = tx1 - tx0 + 1, ty1 - ty0 + 1
    mosaic = Image.new("RGB", (nx * 256, ny * 256))

    def _load(tx_ty):
        tx, ty = tx_ty
        url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{ty}/{tx}"
        cpath = os.path.join(cache_dir, f"esri_z{zoom}", f"{tx}_{ty}.jpg")
        raw = fetch_url_cached(url, cpath, timeout=15)
        return tx, ty, Image.open(io.BytesIO(raw)).convert("RGB")

    coords = [(tx, ty) for ty in range(ty0, ty1 + 1) for tx in range(tx0, tx1 + 1)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        for tx, ty, tile in pool.map(_load, coords):
            mosaic.paste(tile, ((tx - tx0) * 256, (ty - ty0) * 256))

    arr = np.asarray(mosaic)
    lats = np.linspace(lat_n, lat_s, out_size, dtype=np.float64)
    lons = np.linspace(lon_w, lon_e, out_size, dtype=np.float64)
    n = 2.0 ** zoom
    y_tile = (1.0 - np.arcsinh(np.tan(np.radians(lats))) / math.pi) / 2.0 * n
    x_tile = (lons + 180.0) / 360.0 * n
    px = (x_tile - tx0) * 256.0
    py = (y_tile - ty0) * 256.0

    ix = np.clip(np.floor(px).astype(np.int32), 0, arr.shape[1] - 2)
    iy = np.clip(np.floor(py).astype(np.int32), 0, arr.shape[0] - 2)
    fx = (px - ix).astype(np.float32)[None, :, None]
    fy = (py - iy).astype(np.float32)[:, None, None]

    out = np.empty((out_size, out_size, 3), dtype=np.uint8)
    strip = 512
    for r0 in range(0, out_size, strip):
        r1 = min(out_size, r0 + strip)
        y_idx = iy[r0:r1][:, None]
        x_idx = ix[None, :]
        fy_s = fy[r0:r1]
        blended = (
            arr[y_idx, x_idx] * (1.0 - fx) * (1.0 - fy_s)
            + arr[y_idx, x_idx + 1] * fx * (1.0 - fy_s)
            + arr[y_idx + 1, x_idx] * (1.0 - fx) * fy_s
            + arr[y_idx + 1, x_idx + 1] * fx * fy_s
        )
        out[r0:r1] = np.clip(np.round(blended), 0, 255).astype(np.uint8)
    return Image.fromarray(out, mode="RGB")


def save_uint16_png(arr_m: np.ndarray, max_height_m: float, out_path: str):
    """Quantize meters into 16-bit PNG scaled to [0, max_height_m]."""
    raw = np.clip(np.round(arr_m / max_height_m * 65535.0), 0, 65535).astype(np.uint16)
    Image.fromarray(raw).save(out_path)


def _fbm_2d(size: int, seed: int = 42) -> np.ndarray:
    """Multi-octave smooth 2D noise in [0, 1] using pure NumPy/Pillow."""
    rng = np.random.default_rng(seed)
    acc = np.zeros((size, size), dtype=np.float32)
    weight_sum = 0.0
    for grid_n, w in ((8, 0.45), (16, 0.30), (32, 0.17), (64, 0.08)):
        base = rng.random((grid_n, grid_n), dtype=np.float32)
        up = np.array(Image.fromarray(base, mode="F").resize((size, size), Image.BICUBIC), dtype=np.float32)
        acc += np.clip(up, 0.0, 1.0) * w
        weight_sum += w
    return np.clip(acc / max(1e-5, weight_sum), 0.0, 1.0)


def _geo_blob_field(
    specs: list[tuple[str, float, float, float, float, float]],
    lat_n: float, lat_s: float, lon_w: float, lon_e: float, size: int
) -> tuple[np.ndarray, list[tuple[str, float, float]]]:
    """Build smooth elliptical resource pockets from (label, lat, lon, rx_m, ry_m, strength)."""
    m_lat = M_PER_DEG_LAT
    m_lon = M_PER_DEG_LON
    lats = np.linspace(lat_n, lat_s, size, dtype=np.float32)[:, None]
    lons = np.linspace(lon_w, lon_e, size, dtype=np.float32)[None, :]
    field = np.zeros((size, size), dtype=np.float32)
    anchors = []
    for label, lat, lon, rx_m, ry_m, strength in specs:
        dy_m = (lats - lat) * m_lat
        dx_m = (lons - lon) * m_lon
        r2 = (dx_m / rx_m) ** 2 + (dy_m / ry_m) ** 2
        blob = np.exp(-1.8 * r2) * strength
        field = np.maximum(field, blob.astype(np.float32))
        anchors.append((label, lat, lon))
    return field, anchors


def generate_resources(
    elev: np.ndarray, water_mask: np.ndarray, masks: dict,
    lat_n: float, lat_s: float, lon_w: float, lon_e: float, out_dir: str
) -> tuple[dict[str, np.ndarray], list[tuple[str, tuple[int, int, int], float, float]]]:
    """Export balanced 256x256 & 4096x4096 CS2 resource maps and return summary + labels."""
    work = 512
    el_w = np.array(Image.fromarray(elev, mode="F").resize((work, work), Image.BILINEAR), dtype=np.float32)
    wat_w = np.array(Image.fromarray((water_mask.astype(np.uint8) * 255)).resize((work, work), Image.NEAREST)) > 127
    dry = ~wat_w

    gy, gx = np.gradient(el_w, REAL_SIDE_M / work)
    slope = np.hypot(gx, gy)
    urb = np.array(masks["urban"].resize((work, work), Image.BILINEAR), dtype=np.float32) / 255.0
    hwy = np.array(masks["highways"].resize((work, work), Image.BILINEAR), dtype=np.float32) / 255.0
    for_mask = np.array(masks["forest"].resize((work, work), Image.BILINEAR), dtype=np.float32) / 255.0

    river_near = np.array(
        Image.fromarray((wat_w.astype(np.uint8) * 255))
        .filter(ImageFilter.MaxFilter(19))
        .filter(ImageFilter.GaussianBlur(radius=9.0)),
        dtype=np.float32,
    ) / 255.0

    n_f = _fbm_2d(work, seed=101)
    n_o = _fbm_2d(work, seed=202)
    n_r = _fbm_2d(work, seed=303)
    n_g = _fbm_2d(work, seed=404)
    n_w = _fbm_2d(work, seed=505)

    # 1. Fertile soil: river alluvial plains & outer paddies (Miho, Geumgang N bend, Geumgo, Songgang, Jeonmin-Taplip)
    fertile_specs = [
        ("비옥: 미호·신탄진 동측 평야", 36.4565, 127.4485, 1120.0, 800.0, 1.00),
        ("비옥: 금강 북안 충적평야", 36.4605, 127.4045, 920.0, 480.0, 0.96),
        ("비옥: 구즉·금고 서북 구릉농지", 36.4525, 127.3645, 1050.0, 850.0, 0.96),
        ("비옥: 송강·관평 서측 농지", 36.4255, 127.3720, 760.0, 820.0, 0.96),
        ("비옥: 전민·갑천변 수변평야", 36.3955, 127.4090, 580.0, 840.0, 0.96),
    ]
    fertile_field, f_pts = _geo_blob_field(fertile_specs, lat_n, lat_s, lon_w, lon_e, work)
    fertile = fertile_field * (0.70 + 0.48 * n_f) + river_near * 0.22 * (1.0 - urb)
    fertile *= np.clip((0.14 - slope) / 0.07, 0.0, 1.0) * np.clip((132.0 - el_w) / 28.0, 0.0, 1.0)
    fertile *= (1.0 - 0.50 * urb) * (1.0 - 0.70 * hwy)
    fertile = np.where(dry, np.clip((fertile - 0.14) / 0.66, 0.0, 1.0), 0.0)

    # 2. Oil / petrochemical heavy industrial zones (Daedeok Ind 3/4, Pyeongchon Ind, Taplip/Gwanpyeong East, Venture Coop)
    oil_specs = [
        ("석유: 목상·문평 대덕3·4산단", 36.4408, 127.4025, 980.0, 800.0, 1.00),
        ("석유: 평촌·신일 중소기업단지", 36.4355, 127.4305, 650.0, 740.0, 0.96),
        ("석유: 탑립·관평 동측 산단", 36.4165, 127.4100, 600.0, 640.0, 0.94),
        ("석유: 벤처협동화·원촌 북측", 36.3865, 127.3995, 580.0, 440.0, 0.95),
    ]
    oil_field, o_pts = _geo_blob_field(oil_specs, lat_n, lat_s, lon_w, lon_e, work)
    oil = oil_field * (0.68 + 0.48 * n_o) * np.clip((0.11 - slope) / 0.06, 0.0, 1.0) * np.clip((88.0 - el_w) / 24.0, 0.0, 1.0)
    oil = np.where(dry & (el_w > 25.0), np.clip((oil - 0.15) / 0.66, 0.0, 1.0), 0.0)

    # 3. Ore / mineral veins along rocky mountain ridges (Bulmusan, Gyejoksan W ridges, Jaun/Hwaam ridge)
    ore_specs = [
        ("광물: 불무산 능선", 36.4538, 127.3900, 740.0, 620.0, 0.98),
        ("광물: 신탄진 동측 능선", 36.4360, 127.4465, 740.0, 920.0, 0.95),
        ("광물: 계족산 서사면 채석축", 36.4120, 127.4485, 840.0, 1200.0, 1.00),
        ("광물: 회덕 동측 암반능선", 36.3900, 127.4470, 840.0, 1080.0, 0.95),
        ("광물: 화암·자운 배후능선", 36.4040, 127.3620, 800.0, 980.0, 0.92),
        ("광물: 송강 서측 구릉", 36.4305, 127.3625, 720.0, 740.0, 0.88),
    ]
    ore_field, r_pts = _geo_blob_field(ore_specs, lat_n, lat_s, lon_w, lon_e, work)
    ridge_fac = np.clip((el_w - 64.0) / 62.0, 0.0, 1.0) * np.maximum(np.clip(slope / 0.09, 0.45, 1.0), np.clip((el_w - 115.0) / 35.0, 0.0, 1.0))
    ore = ore_field * ridge_fac * (0.58 + 0.60 * n_r)
    ore = np.where(dry, np.clip((ore - 0.09) / 0.62, 0.0, 1.0), 0.0)

    # Keep extraction belts and agricultural plains distinct, with soft edges.
    oil *= np.clip(1.0 - ore * 2.0, 0.0, 1.0)
    extraction = np.maximum(oil, ore)
    fertile *= np.clip(1.0 - extraction * 2.0, 0.0, 1.0)

    # 4. Groundwater aquifers along Geumgang, Gapcheon, Gwanpyeong, Jeonmin/Munji & Seokbong
    gw_specs = [
        ("지하수: 금강 드론공원·불무 연안", 36.4545, 127.3995, 880.0, 540.0, 0.96),
        ("지하수: 석봉·금강로하스 대수층", 36.4535, 127.4235, 920.0, 520.0, 0.96),
        ("지하수: 목상·관평 갑천 대수층", 36.4270, 127.3965, 780.0, 1020.0, 0.92),
        ("지하수: 탑립·회덕 수변 대수층", 36.4095, 127.4110, 720.0, 820.0, 0.94),
        ("지하수: 전민·원촌 갑천 대수층", 36.3890, 127.4065, 680.0, 860.0, 0.96),
    ]
    gw_field, g_pts = _geo_blob_field(gw_specs, lat_n, lat_s, lon_w, lon_e, work)
    gw = (gw_field * 0.80 + river_near * 0.34) * (0.68 + 0.44 * n_g)
    gw *= np.clip((0.09 - slope) / 0.06, 0.0, 1.0) * np.clip((64.0 - el_w) / 20.0, 0.0, 1.0)
    gw = np.where(dry, np.clip((gw - 0.16) / 0.64, 0.0, 1.0), 0.0)
    start_gw, start_pts = _geo_blob_field([START_AQUIFER], lat_n, lat_s, lon_w, lon_e, work)
    # A usable starting reserve must survive the slope/elevation heuristics.
    start_ok = dry & (hwy < 0.25) & (slope < 0.12) & (el_w < 85.0)
    gw = np.maximum(gw, np.where(start_ok, start_gw * 0.95, 0.0))
    gw *= np.clip(1.0 - extraction * 2.0, 0.0, 1.0)

    # 5. Forest / wood: hillsides > 50m & mapped woods, strictly excluding urban pads, highways & farmland
    elev_wood = np.clip((el_w - 50.0) / 38.0, 0.0, 1.0)
    forest_raw = np.maximum(for_mask * 0.9, elev_wood) * (0.48 + 0.72 * n_w)
    forest = forest_raw * (1.0 - 0.92 * urb) * (1.0 - 0.90 * hwy) * np.clip(1.0 - fertile * 1.4, 0.0, 1.0)
    forest = np.where(dry, np.clip((forest - 0.22) / 0.62, 0.0, 1.0), 0.0)
    forest *= np.clip(1.0 - extraction * 2.0, 0.0, 1.0)

    res_work = {
        "resource_fertile": fertile,
        "resource_forest": forest,
        "resource_ore": ore,
        "resource_oil": oil,
        "resource_underground_water": gw,
    }
    for base, arr in res_work.items():
        u8_w = np.clip(np.round(arr * 255.0), 0, 255).astype(np.uint8)
        im_w = Image.fromarray(u8_w, mode="L")
        im_w.resize((4096, 4096), Image.BICUBIC).save(os.path.join(out_dir, f"{base}_4096.png"))
        im_w.resize((256, 256), Image.BILINEAR).save(os.path.join(out_dir, f"{base}_256.png"))
        pct = float((u8_w > 20).mean() * 100.0)
        print(f"  {base:26s}: max={int(u8_w.max()):3d}, cover(>20)={pct:5.1f}%")

    labels = (
        [(lbl, (235, 210, 45), lat, lon) for lbl, lat, lon in f_pts]
        + [(lbl, (235, 70, 95), lat, lon) for lbl, lat, lon in o_pts]
        + [(lbl, (245, 130, 45), lat, lon) for lbl, lat, lon in r_pts]
        + [(lbl, (55, 165, 255), lat, lon) for lbl, lat, lon in g_pts]
        + [(lbl, (55, 165, 255), lat, lon) for lbl, lat, lon in start_pts]
    )

    # Export CS2-ready 256x256x5 uint16 resource binary (row-flipped South->North for CellMapSystem)
    def _to_cs2_grid(arr: np.ndarray, max_val: int = 10000) -> np.ndarray:
        g = np.array(Image.fromarray(np.clip(arr, 0.0, 1.0), mode="F").resize((256, 256), Image.BILINEAR), dtype=np.float32)
        return np.clip(np.round(g[::-1, :] * max_val), 0, max_val).astype(np.uint16)

    wat_256 = np.array(Image.fromarray(wat_w.astype(np.uint8) * 255).resize((256, 256), Image.BILINEAR), dtype=np.float32) / 255.0
    fish_grid = np.clip(np.round(wat_256[::-1, :] * 7200.0), 0, 10000).astype(np.uint16)
    bin_arr = np.stack([
        _to_cs2_grid(fertile, 10000),
        _to_cs2_grid(ore, 10000),
        _to_cs2_grid(oil, 10000),
        fish_grid,
        _to_cs2_grid(gw, 10000),
    ], axis=-1)
    bin_arr.astype("<u2").tofile(os.path.join(out_dir, "sintanjin_resources_256.bin"))
    return res_work, labels


def generate_realistic_trees(
    elev: np.ndarray, water_mask: np.ndarray, masks: dict,
    sat_img: Image.Image, res_work: dict[str, np.ndarray], out_dir: str
) -> dict[str, int]:
    """Sample realistic Korean mixed forest & riparian/park trees from Esri canopy + OSM + DEM."""
    grid = 1024  # 1 cell = 14.0 m x 14.0 m in CS2 (14,336 m / 1024)
    cell_m = CS2_SIDE_M / grid

    el_g = np.array(Image.fromarray(elev, mode="F").resize((grid, grid), Image.BILINEAR), dtype=np.float32)
    gy, gx = np.gradient(el_g, REAL_SIDE_M / grid)
    slope = np.hypot(gx, gy)
    north_aspect = np.clip(0.5 - gy / (np.maximum(slope, 0.05) * 2.0), 0.0, 1.0)  # gy<0 means slope faces North

    wat_g = np.array(
        Image.fromarray(water_mask.astype(np.uint8) * 255).resize((grid, grid), Image.NEAREST).filter(ImageFilter.MaxFilter(5))
    ) > 80
    hwy_g = np.array(
        masks["highways"].resize((grid, grid), Image.BILINEAR).filter(ImageFilter.MaxFilter(5))
    ) > 65
    rail_g = np.array(
        masks["rail"].resize((grid, grid), Image.BILINEAR).filter(ImageFilter.MaxFilter(5))
    ) > 65
    urb_g = np.array(masks["urban"].resize((grid, grid), Image.BILINEAR), dtype=np.float32) / 255.0
    for_g = np.array(masks["forest"].resize((grid, grid), Image.BILINEAR), dtype=np.float32) / 255.0
    fert_g = np.array(
        Image.fromarray(res_work["resource_fertile"], mode="F").resize((grid, grid), Image.BILINEAR),
        dtype=np.float32,
    )

    # Real satellite canopy detection (Esri World Imagery resampled to 14m cells)
    sat_g = np.array(sat_img.resize((grid, grid), Image.Resampling.BILINEAR), dtype=np.float32)
    r_ch, g_ch, b_ch = sat_g[:, :, 0], sat_g[:, :, 1], sat_g[:, :, 2]
    luma = 0.299 * r_ch + 0.587 * g_ch + 0.114 * b_ch
    exg = g_ch - 0.55 * r_ch - 0.45 * b_ch
    gratio = (g_ch - r_ch) / (g_ch + r_ch + 8.0)

    # Dense natural trees in Daejeon satellite are rich mid/dark greens (luma ~28..122) with clear green excess
    canopy_green = np.clip((exg - 3.5) / 14.0, 0.0, 1.0) * np.clip((gratio - 0.015) / 0.075, 0.0, 1.0)
    canopy_shade = np.clip((luma - 18.0) / 16.0, 0.0, 1.0) * np.clip((132.0 - luma) / 42.0, 0.0, 1.0)
    sat_canopy = canopy_green * canopy_shade

    # Multi-scale organic variation so clearings, rocky outcrops & groves look natural
    n_macro = _fbm_2d(grid, seed=707)
    n_micro = _fbm_2d(grid, seed=808)
    n_species = _fbm_2d(grid, seed=909)

    # Mountain woods (elevation + slope + satellite canopy + OSM wood)
    elev_woods = np.clip((el_g - 52.0) / 36.0, 0.0, 1.0) * (0.45 + 0.55 * sat_canopy)
    osm_woods = for_g * np.clip((exg + 1.0) / 12.0, 0.15, 1.0)
    hill_density = np.maximum(np.maximum(elev_woods, osm_woods * 0.92), sat_canopy * 0.85)

    # Urban parks / campus / riparian belts (only where satellite clearly shows real green canopy!)
    park_canopy = np.clip((sat_canopy - 0.30) / 0.45, 0.0, 1.0) * np.clip(1.15 - urb_g * 0.72, 0.15, 1.0)
    raw_density = np.where(el_g < 50.0, np.maximum(osm_woods * 0.85, park_canopy * 0.58), hill_density)

    # Dampen bare rocky cliffs, agricultural fields, and noisy outliers; zero out rivers/highways/rail/below sea level
    cliff_ok = np.clip((0.72 - slope) / 0.28, 0.15, 1.0)
    farm_damp = np.clip(1.0 - fert_g * 1.15, 0.08, 1.0)
    urb_damp = np.where(el_g > 72.0, 1.0 - 0.85 * urb_g, np.where(sat_canopy > 0.38, 1.0 - 0.48 * urb_g, 1.0 - 0.92 * urb_g))
    density = raw_density * cliff_ok * farm_damp * urb_damp * (0.55 + 0.65 * n_macro)
    extraction = np.maximum(res_work["resource_oil"], res_work["resource_ore"])
    extraction_g = np.array(Image.fromarray(extraction).resize((grid, grid), Image.BILINEAR))
    density *= np.clip(1.0 - extraction_g * 2.0, 0.0, 1.0)

    blocked = wat_g | hwy_g | rail_g | (el_g < WATER_SEA_LEVEL_M + 0.6)
    density = np.where(blocked, 0.0, np.clip(density, 0.0, 1.0))

    # Calibrate probability so total tree count stays within realistic CS2 sweet spot (~82,000 trees)
    prob = np.clip((density - 0.16) / 0.68, 0.0, 1.0) ** 1.15
    target_trees = 84000.0
    cur_sum = float(prob.sum())
    if cur_sum > 1e-3:
        scale = target_trees / cur_sum
        prob = np.clip(prob * min(scale, 0.92), 0.0, 0.92)

    rng = np.random.default_rng(20261115)
    roll = rng.random((grid, grid), dtype=np.float32)
    rows, cols = np.nonzero(roll < prob)

    n_trees = len(rows)
    jitter_x = rng.uniform(-0.44 * cell_m, 0.44 * cell_m, size=n_trees).astype(np.float32)
    jitter_z = rng.uniform(-0.44 * cell_m, 0.44 * cell_m, size=n_trees).astype(np.float32)

    # CS2 coordinates: X West(-7168)->East(+7168), Z South(-7168)->North(+7168); image row 0 is North (+7168)
    wx = (-0.5 * CS2_SIDE_M + (cols.astype(np.float32) + 0.5) * cell_m + jitter_x).astype(np.float32)
    wz = (+0.5 * CS2_SIDE_M - (rows.astype(np.float32) + 0.5) * cell_m + jitter_z).astype(np.float32)

    # Filter edge safety
    valid = (wx > -7145.0) & (wx < 7145.0) & (wz > -7145.0) & (wz < 7145.0)
    rows, cols, wx, wz = rows[valid], cols[valid], wx[valid], wz[valid]
    n_trees = len(rows)

    el_t = el_g[rows, cols]
    sl_t = slope[rows, cols]
    na_t = north_aspect[rows, cols]
    urb_t = urb_g[rows, cols]
    prob_t = prob[rows, cols]
    sp_n = n_species[rows, cols]
    mi_n = n_micro[rows, cols]

    # Biome classification: 0=ConiferRidge(Pine/Spruce), 1=MixedMountain(Oak/Birch/Pine), 2=RiparianPark(Birch/Alder/Oak), 3=EdgeShrub
    biome = np.ones(n_trees, dtype=np.uint8)
    is_park_riparian = (el_t < 46.0) | ((urb_t > 0.25) & (el_t < 75.0))
    is_conifer = ((el_t > 88.0) & (sp_n > 0.36 + 0.22 * na_t)) | ((sl_t > 0.24) & (na_t < 0.45) & (sp_n > 0.30))
    is_shrub = ((prob_t < 0.14) & (rng.random(n_trees) < 0.52)) | ((sl_t > 0.42) & (rng.random(n_trees) < 0.45))

    biome[is_conifer] = 0
    biome[is_park_riparian] = 2
    biome[is_shrub] = 3

    # Realistic age (0.12..0.90 -> 31..230 uint8; Teen/Adult/Elderly mix, avoiding dead stumps)
    age_f = np.clip(0.32 + 0.36 * density[rows, cols] + rng.normal(0.0, 0.14, size=n_trees), 0.12, 0.90)
    age_f[biome == 3] = rng.uniform(0.10, 0.38, size=int((biome == 3).sum()))
    age_u8 = np.clip(np.round(age_f * 255.0), 15, 232).astype(np.uint8)
    rot_u8 = rng.integers(0, 256, size=n_trees, dtype=np.uint8)
    var_u8 = np.clip(np.round(mi_n * 255.0), 0, 255).astype(np.uint8)

    # Save binary pack for CS2 C# mod: header "SJT1" + uint32 count + N*(float32 wx, float32 wz, 4x uint8)
    rec_dtype = np.dtype([("wx", "<f4"), ("wz", "<f4"), ("biome", "u1"), ("age", "u1"), ("rot", "u1"), ("var", "u1")])
    recs = np.empty(n_trees, dtype=rec_dtype)
    recs["wx"] = wx
    recs["wz"] = wz
    recs["biome"] = biome
    recs["age"] = age_u8
    recs["rot"] = rot_u8
    recs["var"] = var_u8
    bin_path = os.path.join(out_dir, "sintanjin_trees.bin")
    with open(bin_path, "wb") as f:
        f.write(b"SJT1")
        f.write(struct.pack("<I", n_trees))
        f.write(recs.tobytes())

    counts = {
        "total": int(n_trees),
        "conifer": int((biome == 0).sum()),
        "mixed": int((biome == 1).sum()),
        "riparian_park": int((biome == 2).sum()),
        "edge_shrub": int((biome == 3).sum()),
    }
    print(
        f"  trees                     : total={counts['total']:,} "
        f"(Pine/Conifer={counts['conifer']:,}, Mixed={counts['mixed']:,}, "
        f"Park/Riparian={counts['riparian_park']:,}, EdgeShrub={counts['edge_shrub']:,})"
    )

    # Visual verification preview_forest_trees.png (1536x1536)
    sz_v = 1536
    sat_v = np.array(sat_img.resize((sz_v, sz_v), Image.Resampling.BILINEAR), dtype=np.float32) * 0.62
    wat_v = np.array(Image.fromarray(water_mask.astype(np.uint8) * 255).resize((sz_v, sz_v), Image.NEAREST)) > 127
    hwy_v = np.array(masks["highways"].resize((sz_v, sz_v), Image.BILINEAR)) > 90
    sat_v[wat_v] = np.array([26, 102, 175], dtype=np.float32)
    sat_v[hwy_v] = np.array([240, 185, 35], dtype=np.float32)

    px_x = np.clip(np.round((wx / CS2_SIDE_M + 0.5) * (sz_v - 1)).astype(np.int32), 0, sz_v - 1)
    px_y = np.clip(np.round((0.5 - wz / CS2_SIDE_M) * (sz_v - 1)).astype(np.int32), 0, sz_v - 1)
    palette = np.array([
        [34, 152, 68],   # 0: Conifer Ridge
        [82, 204, 88],   # 1: Mixed Mountain
        [48, 224, 165],  # 2: Riparian / Park
        [188, 228, 86],  # 3: Edge Shrub
    ], dtype=np.float32)
    sat_v[px_y, px_x] = palette[biome]
    im_v = Image.fromarray(np.clip(sat_v, 0, 255).astype(np.uint8), mode="RGB")

    draw = ImageDraw.Draw(im_v)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 18)
        font_sm = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 15)
    except Exception:
        font = font_sm = ImageFont.load_default()
    draw.rectangle([20, 20, 560, 175], fill=(18, 24, 34), outline=(140, 160, 185), width=2)
    draw.text((34, 30), f"실측 위성+DEM 산림/수변 식생 배치 ({counts['total']:,}그루)", fill=(255, 255, 255), font=font)
    legend_rows = [
        ((34, 152, 68), f"침엽수 능선 (소나무·가문비) : {counts['conifer']:,}그루"),
        ((82, 204, 88), f"산악 혼효림 (참나무·자작·소나무) : {counts['mixed']:,}그루"),
        ((48, 224, 165), f"수변·공원 녹지 (버들·오리·활엽수) : {counts['riparian_park']:,}그루"),
        ((188, 228, 86), f"임연부·경사 관목/유목 : {counts['edge_shrub']:,}그루"),
    ]
    yc = 64
    for col, txt in legend_rows:
        draw.rectangle([34, yc, 50, yc + 16], fill=col, outline=(255, 255, 255))
        draw.text((58, yc - 2), txt, fill=(235, 242, 248), font=font_sm)
        yc += 25
    im_v.save(os.path.join(out_dir, "preview_forest_trees.png"))
    return counts


def _sample_elev_bilinear(elev: np.ndarray, wx: np.ndarray | float, wz: np.ndarray | float) -> np.ndarray | float:
    """Sample 4096x4096 terrain height (m) at CS2 world XZ coordinates."""
    size = elev.shape[0]
    fx = np.clip((np.asarray(wx, dtype=np.float32) / CS2_SIDE_M + 0.5) * (size - 1), 0.0, size - 1.001)
    fy = np.clip((0.5 - np.asarray(wz, dtype=np.float32) / CS2_SIDE_M) * (size - 1), 0.0, size - 1.001)
    x0 = np.floor(fx).astype(np.int32)
    y0 = np.floor(fy).astype(np.int32)
    dx = fx - x0
    dy = fy - y0
    val = (
        elev[y0, x0] * (1.0 - dx) * (1.0 - dy)
        + elev[y0, x0 + 1] * dx * (1.0 - dy)
        + elev[y0 + 1, x0] * (1.0 - dx) * dy
        + elev[y0 + 1, x0 + 1] * dx * dy
    )
    return float(val) if np.ndim(wx) == 0 else val


def _clip_polyline_box(pts: list[tuple[float, float, int]], limit: float) -> list[list[tuple[float, float, int]]]:
    """Liang-Barsky clip a sequence of (x, z, nid) points against [-limit, +limit]^2."""
    pieces: list[list[tuple[float, float, int]]] = []
    cur: list[tuple[float, float, int]] = []

    def clip_seg(p0, p1):
        x0, z0, id0 = p0
        x1, z1, id1 = p1
        dx, dz = x1 - x0, z1 - z0
        t0, t1 = 0.0, 1.0
        for p, q in ((-dx, x0 + limit), (dx, limit - x0), (-dz, z0 + limit), (dz, limit - z0)):
            if abs(p) < 1e-9:
                if q < 0.0:
                    return None
            else:
                r = q / p
                if p < 0.0:
                    if r > t1:
                        return None
                    if r > t0:
                        t0 = r
                else:
                    if r < t0:
                        return None
                    if r < t1:
                        t1 = r
        nx0 = x0 + t0 * dx
        nz0 = z0 + t0 * dz
        nx1 = x0 + t1 * dx
        nz1 = z0 + t1 * dz
        ni0 = id0 if t0 < 1e-6 else -1
        ni1 = id1 if t1 > 1.0 - 1e-6 else -1
        return (nx0, nz0, ni0), (nx1, nz1, ni1), t0 > 1e-6, t1 < 1.0 - 1e-6

    for i in range(len(pts) - 1):
        res = clip_seg(pts[i], pts[i + 1])
        if res is None:
            if len(cur) >= 2:
                pieces.append(cur)
            cur = []
            continue
        q0, q1, clipped_start, clipped_end = res
        if not cur:
            cur = [q0, q1]
        else:
            if clipped_start or math.hypot(cur[-1][0] - q0[0], cur[-1][1] - q0[1]) > 0.5:
                if len(cur) >= 2:
                    pieces.append(cur)
                cur = [q0, q1]
            else:
                cur.append(q1)
        if clipped_end and len(cur) >= 2:
            pieces.append(cur)
            cur = []
    if len(cur) >= 2:
        pieces.append(cur)
    return pieces


def generate_backbone_roads(
    osm: dict, elev: np.ndarray, water_mask: np.ndarray, sat_img: Image.Image,
    lat_n: float, lat_s: float, lon_w: float, lon_e: float, out_dir: str,
) -> dict[str, int]:
    """
    Export clean 1:1 backbone highways, major arterials & main railways (sintanjin_roads.bin 'SJR1')
    and preview_roads_backbone.png, omitting IC/JC link ramps and industrial rail yards.
    """
    nodes = {e["id"]: (e["lat"], e["lon"]) for e in osm["elements"] if e["type"] == "node"}
    clip_lim = CS2_SIDE_M * 0.5 - 18.0  # ±7150m safely inside ±7168m border

    def to_cs2(lat: float, lon: float) -> tuple[float, float]:
        u = (lon - lon_w) / (lon_e - lon_w)
        v = (lat_n - lat) / (lat_n - lat_s)
        return ((u - 0.5) * CS2_SIDE_M, (0.5 - v) * CS2_SIDE_M)

    # Road kinds written into SJR1 binary:
    # 0=3L_OW_Hwy, 1=2L_OW_Hwy, 2=4L_Divided, 3=2L_Twoway, 4=2L_OW_Street, 5=Double_Rail
    raw_ways: list[dict] = []
    for e in osm["elements"]:
        if e["type"] != "way":
            continue
        t = e.get("tags", {})
        hw = t.get("highway", "")
        rw = t.get("railway", "")

        is_rail = (rw == "rail") and (not t.get("service"))
        is_hwy = hw in ("motorway", "trunk", "primary")
        if not (is_hwy or is_rail):
            continue

        nids = [n for n in e.get("nodes", []) if n in nodes]
        if len(nids) < 2:
            continue

        layer = 0
        try:
            layer = int(t.get("layer", "0"))
        except ValueError:
            layer = 0
        is_bridge = t.get("bridge", "") not in ("", "no") or layer >= 1
        is_tunnel = t.get("tunnel", "") not in ("", "no") or layer <= -1
        if is_bridge and layer < 1:
            layer = 1
        if is_tunnel and layer > -1:
            layer = -1

        lanes = 0
        try:
            lanes = int(str(t.get("lanes", "0")).split(";")[0])
        except ValueError:
            lanes = 0

        oneway = t.get("oneway") == "yes" or hw == "motorway"
        name = t.get("name", "")
        cat = "rail" if is_rail else hw

        if is_rail:
            kind = 5
        elif hw == "motorway":
            kind = 0 if lanes >= 3 else 1
        elif hw == "trunk":
            kind = 1 if oneway else 2
        else:  # primary
            if oneway:
                kind = 4
            else:
                kind = 2 if (lanes == 0 or lanes >= 4) else 3

        pts = [(*to_cs2(*nodes[nid]), nid) for nid in nids]
        for piece in _clip_polyline_box(pts, clip_lim):
            raw_ways.append({
                "id": e["id"],
                "cat": cat,
                "name": name,
                "kind": kind,
                "oneway": oneway,
                "lanes": lanes,
                "layer": layer,
                "bridge": is_bridge,
                "tunnel": is_tunnel,
                "pts": piece,  # [(x, z, osm_nid)]
            })

    # Helper to query closest opposite/parallel point separation on raw/polylines
    def _min_perp_dist_segs(
        p: tuple[float, float], tx: float, tz: float, cands_pts: list[list[tuple[float, float]]], req_opp: bool
    ) -> tuple[float, tuple[float, float] | None]:
        px, pz = p
        best_d = 1e9
        best_q = None
        for cpts in cands_pts:
            for i in range(len(cpts) - 1):
                ax, az = cpts[i][0], cpts[i][1]
                bx, bz = cpts[i + 1][0], cpts[i + 1][1]
                dx, dz = bx - ax, bz - az
                L2 = dx * dx + dz * dz
                if L2 < 1e-4:
                    continue
                L = math.sqrt(L2)
                dot = (dx * tx + dz * tz) / L
                if req_opp and dot > -0.60:
                    continue
                if (not req_opp) and abs(dot) < 0.65:
                    continue
                u = max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / L2))
                qx, qz = ax + u * dx, az + u * dz
                d = math.hypot(px - qx, pz - qz)
                if 0.25 < d < best_d:
                    best_d = d
                    best_q = (qx, qz)
        return best_d, best_q

    def _pt_to_poly_list(
        px: float, pz: float, polys: list[list[tuple[float, float]]], max_d: float
    ) -> tuple[float, tuple[float, float] | None, int, int, float]:
        best_d = max_d
        best_q = None
        best_pi = -1
        best_si = -1
        best_u = 0.0
        for pi, poly in enumerate(polys):
            for si in range(len(poly) - 1):
                ax, az = poly[si][0], poly[si][1]
                bx, bz = poly[si + 1][0], poly[si + 1][1]
                dx, dz = bx - ax, bz - az
                L2 = dx * dx + dz * dz
                if L2 < 1e-4:
                    continue
                u = max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / L2))
                qx, qz = ax + u * dx, az + u * dz
                d = math.hypot(px - qx, pz - qz)
                if d < best_d:
                    best_d = d
                    best_q = (qx, qz)
                    best_pi = pi
                    best_si = si
                    best_u = u
        return best_d, best_q, best_pi, best_si, best_u

    # Split raw ways into topological edges preserving attributes, and stitch into continuous corridors FIRST!
    def _stitch_ways(ways: list[dict], allow_reverse: bool, match_kind: bool = False) -> list[dict]:
        """Stitch raw ways sharing exact or <=1.5m endpoints into continuous corridors keeping per-span metadata."""
        used = [False] * len(ways)
        stitched: list[dict] = []
        # Represent each corridor as spans list: each span = dict(pts=[(x,z,nid)], kind, bridge, tunnel, layer, name, oneway, lanes)
        for i, w in enumerate(ways):
            if used[i]:
                continue
            used[i] = True
            # Start chain of directed sub-ways [(pts, span_meta)]
            chain_parts = [{
                "pts": list(w["pts"]),
                "kind": w["kind"],
                "bridge": w["bridge"],
                "tunnel": w["tunnel"],
                "layer": w["layer"],
                "name": w["name"],
                "oneway": w["oneway"],
                "lanes": w["lanes"],
            }]
            changed = True
            while changed:
                changed = False
                h_pts = chain_parts[0]["pts"]
                t_pts = chain_parts[-1]["pts"]
                head = h_pts[0]
                tail = t_pts[-1]
                hx, hz = h_pts[1][0] - head[0], h_pts[1][1] - head[1]
                hl = math.hypot(hx, hz) or 1.0
                hx /= hl; hz /= hl
                tx, tz = tail[0] - t_pts[-2][0], tail[1] - t_pts[-2][1]
                tl = math.hypot(tx, tz) or 1.0
                tx /= tl; tz /= tl

                best_fwd = (1.5, -1, False)
                best_bwd = (1.5, -1, False)
                for j, w2 in enumerate(ways):
                    if used[j] or w2["oneway"] != w["oneway"]:
                        continue
                    if match_kind and w2["kind"] != w["kind"]:
                        continue
                    pts2 = w2["pts"]
                    p0, p1 = pts2[0], pts2[-1]
                    s0x, s0z = pts2[1][0] - p0[0], pts2[1][1] - p0[1]
                    s0l = math.hypot(s0x, s0z) or 1.0
                    s0x /= s0l; s0z /= s0l
                    e1x, e1z = p1[0] - pts2[-2][0], p1[1] - pts2[-2][1]
                    e1l = math.hypot(e1x, e1z) or 1.0
                    e1x /= e1l; e1z /= e1l

                    df0 = math.hypot(tail[0] - p0[0], tail[1] - p0[1])
                    if df0 < best_fwd[0] and (tx * s0x + tz * s0z) > 0.0:
                        best_fwd = (df0, j, False)
                    if allow_reverse:
                        df1 = math.hypot(tail[0] - p1[0], tail[1] - p1[1])
                        if df1 < best_fwd[0] and (tx * (-e1x) + tz * (-e1z)) > 0.0:
                            best_fwd = (df1, j, True)
                    db1 = math.hypot(head[0] - p1[0], head[1] - p1[1])
                    if db1 < best_bwd[0] and (e1x * hx + e1z * hz) > 0.0:
                        best_bwd = (db1, j, False)
                    if allow_reverse:
                        db0 = math.hypot(head[0] - p0[0], head[1] - p0[1])
                        if db0 < best_bwd[0] and ((-s0x) * hx + (-s0z) * hz) > 0.0:
                            best_bwd = (db0, j, True)
                if best_fwd[1] >= 0:
                    _, j, rev = best_fwd
                    used[j] = True
                    w2 = ways[j]
                    pts2 = list(reversed(w2["pts"])) if rev else list(w2["pts"])
                    chain_parts.append({
                        "pts": pts2,
                        "kind": w2["kind"],
                        "bridge": w2["bridge"],
                        "tunnel": w2["tunnel"],
                        "layer": w2["layer"],
                        "name": w2["name"],
                        "oneway": w2["oneway"],
                        "lanes": w2["lanes"],
                    })
                    changed = True
                elif best_bwd[1] >= 0:
                    _, j, rev = best_bwd
                    used[j] = True
                    w2 = ways[j]
                    pts2 = list(reversed(w2["pts"])) if rev else list(w2["pts"])
                    chain_parts.insert(0, {
                        "pts": pts2,
                        "kind": w2["kind"],
                        "bridge": w2["bridge"],
                        "tunnel": w2["tunnel"],
                        "layer": w2["layer"],
                        "name": w2["name"],
                        "oneway": w2["oneway"],
                        "lanes": w2["lanes"],
                    })
                    changed = True
            stitched.append({"parts": chain_parts, "oneway": w["oneway"], "cat": w["cat"]})
        return stitched

    # Separate raw ways by category
    hw_ways = [w for w in raw_ways if w["cat"] in ("motorway", "trunk")]
    pri_ways = [w for w in raw_ways if w["cat"] == "primary"]
    rail_ways = [w for w in raw_ways if w["cat"] == "rail"]

    # Unified graph structures:
    # edges: list of dict(pts=[(x,z)...], kind, cat, oneway, bridge, tunnel, layer)
    graph_segments: list[dict] = []

    # 1) Motorway & Trunk: lock shift per OSM node id so dual oneway lanes never split at joints
    for cat_name in ("motorway", "trunk"):
        grp = [w for w in hw_ways if w["cat"] == cat_name]
        min_sep = 16.5 if cat_name == "motorway" else 15.0
        nid_shifts: dict[int, list[tuple[float, float]]] = {}
        way_shifts: list[list[tuple[float, float]]] = []
        for w in grp:
            wpts = w["pts"]
            opp_cands = [o["pts"] for o in grp if o is not w and o["oneway"] and abs(o["layer"] - w["layer"]) <= 0]
            sh_list: list[tuple[float, float]] = []
            for idx, (px, pz, nid) in enumerate(wpts):
                p_prev = wpts[max(0, idx - 1)]
                p_next = wpts[min(len(wpts) - 1, idx + 1)]
                vx, vz = p_next[0] - p_prev[0], p_next[1] - p_prev[1]
                vn = math.hypot(vx, vz) or 1.0
                d, q = _min_perp_dist_segs((px, pz), vx / vn, vz / vn, opp_cands, req_opp=True)
                if q is not None and d < min_sep and d > 0.5:
                    push = min(3.5, (min_sep - d) * 0.52)
                    sh = ((px - q[0]) / d * push, (pz - q[1]) / d * push)
                else:
                    sh = (0.0, 0.0)
                sh_list.append(sh)
                if nid > 0:
                    nid_shifts.setdefault(nid, []).append(sh)
            way_shifts.append(sh_list)
        nid_avg = {
            nid: (sum(s[0] for s in lst) / len(lst), sum(s[1] for s in lst) / len(lst))
            for nid, lst in nid_shifts.items()
        }
        for w, sh_list in zip(grp, way_shifts):
            wpts = w["pts"]
            npts = []
            for idx, (px, pz, nid) in enumerate(wpts):
                i0, i1 = max(0, idx - 1), min(len(wpts) - 1, idx + 1)
                sx = (sh_list[i0][0] + sh_list[idx][0] * 2.0 + sh_list[i1][0]) / 4.0
                sz = (sh_list[i0][1] + sh_list[idx][1] * 2.0 + sh_list[i1][1]) / 4.0
                if nid > 0 and nid in nid_avg:
                    ax, az = nid_avg[nid]
                    # Blend toward shared nid shift (at ends exact nid_avg so joints meet bit-identically!)
                    if idx == 0 or idx == len(wpts) - 1:
                        sx, sz = ax, az
                    else:
                        sx, sz = 0.5 * (sx + ax), 0.5 * (sz + az)
                npts.append((px + sx, pz + sz))
            graph_segments.append({
                "pts": npts, "kind": w["kind"], "cat": cat_name, "oneway": w["oneway"],
                "bridge": w["bridge"], "tunnel": w["tunnel"], "layer": w["layer"],
            })

    # 2) Primary arterials: keep twoway as-is; stitch oneway corridors across name changes (현도교/신탄진로 etc.)
    pri_twoways = [w for w in pri_ways if not w["oneway"]]
    for w in pri_twoways:
        graph_segments.append({
            "pts": [(p[0], p[1]) for p in w["pts"]],
            "kind": w["kind"], "cat": "primary", "oneway": False,
            "bridge": w["bridge"], "tunnel": w["tunnel"], "layer": w["layer"],
        })

    def _cor_len(cor: dict) -> float:
        s = 0.0
        for sp in cor["parts"]:
            pts = sp["pts"]
            for k in range(len(pts) - 1):
                s += math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1])
        return s

    def _collapse_parallel_corridors(
        ways_in: list[dict],
        allow_reverse: bool,
        req_opp: bool,
        mid_enter_thr: float,
        mid_stay_thr: float,
        cov_same_thr: float,
        cov_any_thr: float,
        is_primary: bool,
    ) -> list[dict]:
        """Stitch ways into continuous corridors, sort longest-first, collapse parallel twins via greedy acceptance (zero holes!)."""
        stitched = _stitch_ways(ways_in, allow_reverse=allow_reverse, match_kind=False)
        stitched.sort(key=_cor_len, reverse=True)
        all_raw_pts = [w["pts"] for w in ways_in]
        accepted_segs: list[dict] = []

        for cor in stitched:
            flat_v: list[tuple[float, float]] = []
            span_metas: list[dict] = []
            for sp_idx, sp in enumerate(cor["parts"]):
                spts = sp["pts"]
                if sp_idx == 0:
                    flat_v.append((spts[0][0], spts[0][1]))
                for k in range(len(spts) - 1):
                    flat_v.append((spts[k + 1][0], spts[k + 1][1]))
                    span_metas.append(sp)
            if len(flat_v) < 2:
                continue

            shifted_v: list[tuple[float, float]] = []
            paired_v: list[bool] = []
            in_pair = False
            min_d = 0.5 if req_opp else 2.5
            for vi, (px, pz) in enumerate(flat_v):
                p0 = flat_v[max(0, vi - 1)]
                p1 = flat_v[min(len(flat_v) - 1, vi + 1)]
                vx, vz = p1[0] - p0[0], p1[1] - p0[1]
                vn = math.hypot(vx, vz) or 1.0
                d, q = _min_perp_dist_segs((px, pz), vx / vn, vz / vn, all_raw_pts, req_opp=req_opp)
                thr = mid_stay_thr if in_pair else mid_enter_thr
                if q is not None and min_d < d < thr:
                    in_pair = True
                    shifted_v.append(((px + q[0]) * 0.5, (pz + q[1]) * 0.5))
                    paired_v.append(True)
                else:
                    in_pair = False
                    shifted_v.append((px, pz))
                    paired_v.append(False)

            acc_polys = [[s["p0"], s["p1"]] for s in accepted_segs]
            covered_flags: list[bool] = []
            for si in range(len(flat_v) - 1):
                sp = span_metas[si]
                ax, az = shifted_v[si]
                bx, bz = shifted_v[si + 1]
                mx, mz = 0.5 * (ax + bx), 0.5 * (az + bz)
                dx, dz = bx - ax, bz - az
                slen = math.hypot(dx, dz) or 1.0
                tx, tz = dx / slen, dz / slen

                def _is_covered(px: float, pz: float) -> bool:
                    best_same = 1e9
                    best_any = 1e9
                    for s_acc in accepted_segs:
                        if abs(s_acc["layer"] - sp["layer"]) > 1:
                            continue
                        sx0, sz0 = s_acc["p0"]
                        sx1, sz1 = s_acc["p1"]
                        sdx, sdz = sx1 - sx0, sz1 - sz0
                        sL2 = sdx * sdx + sdz * sdz
                        if sL2 < 1e-4:
                            continue
                        dot = abs((sdx * tx + sdz * tz) / math.sqrt(sL2))
                        if dot < 0.65:
                            continue
                        u = max(0.0, min(1.0, ((px - sx0) * sdx + (pz - sz0) * sdz) / sL2))
                        d = math.hypot(px - (sx0 + u * sdx), pz - (sz0 + u * sdz))
                        if d < best_any:
                            best_any = d
                        if (not sp["name"] or not s_acc["name"] or sp["name"] == s_acc["name"]) and d < best_same:
                            best_same = d
                    return (best_any < cov_any_thr) or (best_same < cov_same_thr)

                covered_flags.append(_is_covered(ax, az) and _is_covered(bx, bz) and _is_covered(mx, mz))

            for si in range(1, len(covered_flags) - 1):
                if covered_flags[si] and (not covered_flags[si - 1]) and (not covered_flags[si + 1]):
                    covered_flags[si] = False

            for si, cov in enumerate(covered_flags):
                if cov:
                    continue
                sp = span_metas[si]
                p0 = shifted_v[si]
                p1 = shifted_v[si + 1]
                if si > 0 and covered_flags[si - 1] and acc_polys:
                    d_snap, q_snap, _, _, _ = _pt_to_poly_list(p0[0], p0[1], acc_polys, 34.0)
                    if q_snap is not None and d_snap > 0.5:
                        p0 = q_snap
                if si + 1 < len(covered_flags) and covered_flags[si + 1] and acc_polys:
                    d_snap, q_snap, _, _, _ = _pt_to_poly_list(p1[0], p1[1], acc_polys, 34.0)
                    if q_snap is not None and d_snap > 0.5:
                        p1 = q_snap
                if math.hypot(p1[0] - p0[0], p1[1] - p0[1]) < 2.0:
                    continue
                collapsed_span = is_primary and paired_v[si] and paired_v[si + 1]
                seg_kind = 5 if (not is_primary) else (2 if (collapsed_span or sp["lanes"] >= 3) else sp["kind"])
                seg_ow = False if (not is_primary or collapsed_span) else sp["oneway"]
                accepted_segs.append({
                    "p0": p0, "p1": p1, "name": sp["name"], "layer": sp["layer"],
                    "bridge": sp["bridge"], "tunnel": sp["tunnel"],
                    "kind": seg_kind, "oneway": seg_ow,
                })
        return accepted_segs

    # 2) Primary oneways (신탄진로, 대덕대로, 신문로, 대전로, 가정로, 현도교): hole-proof longest-first twin collapse!
    pri_oneways = [w for w in pri_ways if w["oneway"]]
    for s_acc in _collapse_parallel_corridors(
        pri_oneways, allow_reverse=False, req_opp=True,
        mid_enter_thr=25.5, mid_stay_thr=32.5, cov_same_thr=24.5, cov_any_thr=21.0, is_primary=True,
    ):
        graph_segments.append({
            "pts": [s_acc["p0"], s_acc["p1"]],
            "kind": s_acc["kind"], "cat": "primary", "oneway": s_acc["oneway"],
            "bridge": s_acc["bridge"], "tunnel": s_acc["tunnel"], "layer": s_acc["layer"],
        })

    # 3) Railways (경부선, 경부고속선): hole-proof longest-first twin collapse!
    for s_acc in _collapse_parallel_corridors(
        rail_ways, allow_reverse=True, req_opp=False,
        mid_enter_thr=23.0, mid_stay_thr=23.0, cov_same_thr=22.5, cov_any_thr=17.5, is_primary=False,
    ):
        graph_segments.append({
            "pts": [s_acc["p0"], s_acc["p1"]],
            "kind": 5, "cat": "rail", "oneway": False,
            "bridge": s_acc["bridge"], "tunnel": s_acc["tunnel"], "layer": s_acc["layer"],
        })

    # === 4) Build Unified Segment Graph (nodes + atomic edges), snap T-junctions & split intersecting edges! ===
    g_nodes: list[list] = []  # [x, z, layer_hint]
    g_edges: list[dict] = []  # {u, v, kind, cat, oneway, br, tn, layer}

    # Quantized grid index for node lookup within eps
    def _find_or_add_node(x: float, z: float, layer: int, snap_r: float = 2.0) -> int:
        best_i = -1
        best_d = snap_r
        for ni, nd in enumerate(g_nodes):
            # Merge nodes sharing exact/near XZ if same vertical layer (or adjacent ground/bridge boundary when snapped later)
            if abs(nd[2] - layer) > 0:
                continue
            d = math.hypot(nd[0] - x, nd[1] - z)
            if d < best_d:
                best_d = d
                best_i = ni
        if best_i >= 0:
            return best_i
        g_nodes.append([float(x), float(z), int(layer)])
        return len(g_nodes) - 1

    for seg in graph_segments:
        pts = seg["pts"]
        # Use same layer at vertices, EXCEPT merge layer-transition endpoints across same corridor below
        # Tag vertices by layer so grade-separated crossings (bridge over road!) NEVER falsely merge!
        vert_nodes = [_find_or_add_node(px, pz, seg["layer"], snap_r=1.5) for px, pz in pts]
        for k in range(len(vert_nodes) - 1):
            u, v = vert_nodes[k], vert_nodes[k + 1]
            if u == v:
                continue
            g_edges.append({
                "u": u, "v": v, "kind": seg["kind"], "cat": seg["cat"],
                "oneway": seg["oneway"], "br": seg["bridge"], "tn": seg["tunnel"], "layer": seg["layer"],
            })

    # Merge coincident cross-layer nodes ONLY when two DIFFERENT-layer edges meet cleanly at a bridge/tunnel portal
    # (i.e. endpoint of bridge layer=1 at the exact portal XZ of ground layer=0 within < 2.2m, on same cat/kind)!
    def _rebuild_adj():
        adj: dict[int, list[int]] = {i: [] for i in range(len(g_nodes))}
        for ei, ed in enumerate(g_edges):
            if ed["u"] == ed["v"]:
                continue
            adj[ed["u"]].append(ei)
            adj[ed["v"]].append(ei)
        return adj

    adj = _rebuild_adj()
    node_remap = list(range(len(g_nodes)))
    def _root(ni: int) -> int:
        while node_remap[ni] != ni:
            node_remap[ni] = node_remap[node_remap[ni]]
            ni = node_remap[ni]
        return ni

    # Merge coincident cross-layer portal nodes (ground <-> bridge/tunnel transitions) WITHOUT merging crossing overpasses
    def _out_dir(ni: int, ei: int) -> tuple[float, float]:
        ed = g_edges[ei]
        oth = ed["v"] if ed["u"] == ni else ed["u"]
        dx, dz = g_nodes[oth][0] - g_nodes[ni][0], g_nodes[oth][1] - g_nodes[ni][1]
        l = math.hypot(dx, dz) or 1.0
        return dx / l, dz / l

    active_nodes = [ni for ni, eis in adj.items() if eis]
    for ni in active_nodes:
        ri = _root(ni)
        eis_i = adj.get(ri, [])
        if not eis_i:
            continue
        cats_i = {g_edges[ei]["cat"] for ei in eis_i}
        xi, zi, li = g_nodes[ri]
        is_deg1_i = len(eis_i) == 1
        max_r = (6.0 if ("primary" in cats_i or "rail" in cats_i) else 3.5) if is_deg1_i else 1.5
        best_j = -1
        best_d = max_r
        for nj in active_nodes:
            rj = _root(nj)
            if rj == ri:
                continue
            eis_j = adj.get(rj, [])
            if not eis_j:
                continue
            cats_j = {g_edges[ej]["cat"] for ej in eis_j}
            shared_cats = cats_i & cats_j
            if not shared_cats:
                continue
            d = math.hypot(g_nodes[rj][0] - xi, g_nodes[rj][1] - zi)
            if d >= best_d:
                continue
            max_ldiff = 2 if ("rail" in shared_cats and d < 1.5) else 1
            if abs(g_nodes[rj][2] - li) > max_ldiff:
                continue
            is_deg1_j = len(eis_j) == 1
            # Require at least one portal deg1 end OR a collinear continuation (opposite outward directions along same corridor!)
            if is_deg1_i and is_deg1_j:
                ok = True
            elif is_deg1_i or is_deg1_j:
                # Merge deg1 end into multi-way node at portal ONLY if d < 2.5m (exact portal or tiny split)
                ok = (d < 2.5)
            else:
                # Both multi-way at exact point (<1.5m): only merge if an edge from i and j continue smoothly (dot < -0.45)
                ok = any(
                    (_out_dir(ri, ei)[0] * _out_dir(rj, ej)[0] + _out_dir(ri, ei)[1] * _out_dir(rj, ej)[1]) < -0.45
                    for ei in eis_i for ej in eis_j
                )
            if ok:
                best_d = d
                best_j = rj
        if best_j >= 0:
            keep, drop = (ri, best_j) if abs(g_nodes[ri][2]) <= abs(g_nodes[best_j][2]) else (best_j, ri)
            node_remap[drop] = keep

    for ed in g_edges:
        ed["u"] = _root(ed["u"])
        ed["v"] = _root(ed["v"])
    g_edges = [ed for ed in g_edges if ed["u"] != ed["v"]]

    # Bridge collinear internal rail/primary gaps (< 75m rail / < 36m primary) & T-junction edge splits!
    for pass_snap in range(2):
        adj = _rebuild_adj()
        deg1_list = [ni for ni, eis in adj.items() if len(eis) == 1]

        # 4a) First bridge aligned open rail endpoints (< 75m facing each other!)
        if pass_snap == 0:
            bridged_nodes = set()
            for ni in deg1_list:
                if ni in bridged_nodes or not adj[ni]:
                    continue
                nx, nz, _ = g_nodes[ni]
                if max(abs(nx), abs(nz)) > clip_lim - 45.0:
                    continue
                ei = adj[ni][0]
                if g_edges[ei]["cat"] != "rail":
                    continue
                ou = g_edges[ei]["v"] if g_edges[ei]["u"] == ni else g_edges[ei]["u"]
                ox, oz, _ = g_nodes[ou]
                out_dx, out_dz = nx - ox, nz - oz
                ol = math.hypot(out_dx, out_dz) or 1.0
                out_dx /= ol; out_dz /= ol
                best_nj = -1
                best_d = 78.0
                for nj in deg1_list:
                    if nj == ni or nj in bridged_nodes or not adj[nj]:
                        continue
                    ej = adj[nj][0]
                    if g_edges[ej]["cat"] != "rail":
                        continue
                    mx, mz, _ = g_nodes[nj]
                    d = math.hypot(mx - nx, mz - nz)
                    if 1.0 < d < best_d:
                        vx, vz = (mx - nx) / d, (mz - nz) / d
                        if vx * out_dx + vz * out_dz > 0.55:
                            best_d = d
                            best_nj = nj
                if best_nj >= 0:
                    ej = adj[best_nj][0]
                    br_flag = g_edges[ei]["br"] or g_edges[ej]["br"]
                    tn_flag = g_edges[ei]["tn"] and g_edges[ej]["tn"]
                    lyr_flag = min(g_edges[ei]["layer"], g_edges[ej]["layer"]) if tn_flag else (1 if br_flag else 0)
                    g_edges.append({
                        "u": ni, "v": best_nj, "kind": 5, "cat": "rail",
                        "oneway": False, "br": br_flag, "tn": tn_flag, "layer": lyr_flag,
                    })
                    bridged_nodes.add(ni)
                    bridged_nodes.add(best_nj)
            continue

        # 4b) Snap remaining internal degree-1 endpoints onto nearest compatible node OR split nearest compatible edge!
        for ni in deg1_list:
            if len(adj.get(ni, [])) != 1:
                continue
            ei = adj[ni][0]
            ed = g_edges[ei]
            nx, nz, nlyr = g_nodes[ni]
            if max(abs(nx), abs(nz)) > clip_lim - 45.0:
                continue
            max_snap = 36.0 if ed["cat"] in ("primary", "rail") else 14.0
            best_d = max_snap
            best_target_node = -1
            best_split_edge = -1
            best_split_q = None

            # Check other nodes first (snap if < min(max_snap, 18m))
            for nj in range(len(g_nodes)):
                if nj == ni or not adj.get(nj):
                    continue
                # Must share compatible category & within 1 elevation layer
                cats_j = {g_edges[ej]["cat"] for ej in adj[nj]}
                if ed["cat"] not in cats_j:
                    continue
                # Avoid snapping directly onto adjacent neighbor along tiny edge
                if any((g_edges[ej]["u"] == ni or g_edges[ej]["v"] == ni) for ej in adj[nj]):
                    continue
                if abs(g_nodes[nj][2] - nlyr) > 1:
                    continue
                d = math.hypot(g_nodes[nj][0] - nx, g_nodes[nj][1] - nz)
                if d < min(best_d, 20.0):
                    best_d = d
                    best_target_node = nj
                    best_split_edge = -1

            # Check edge interiors for T-junction splits (primary & rail)
            if ed["cat"] in ("primary", "rail"):
                for ej, e2 in enumerate(g_edges):
                    if ej == ei or e2["cat"] != ed["cat"]:
                        continue
                    if e2["u"] == ni or e2["v"] == ni:
                        continue
                    if abs(e2["layer"] - ed["layer"]) > 1:
                        continue
                    ax, az, _ = g_nodes[e2["u"]]
                    bx, bz, _ = g_nodes[e2["v"]]
                    dx, dz = bx - ax, bz - az
                    L2 = dx * dx + dz * dz
                    if L2 < 1e-4:
                        continue
                    u = max(0.0, min(1.0, ((nx - ax) * dx + (nz - az) * dz) / L2))
                    qx, qz = ax + u * dx, az + u * dz
                    d = math.hypot(nx - qx, nz - qz)
                    if d < best_d:
                        best_d = d
                        best_target_node = -1
                        best_split_edge = ej
                        best_split_q = (qx, qz, u, e2["u"], e2["v"])

            if best_target_node >= 0:
                if best_d < 12.0:
                    # Merge deg-1 node ni directly onto existing node best_target_node (if incident edge >= 10m)
                    ux, uz, _ = g_nodes[ed["u"]]
                    vx, vz, _ = g_nodes[ed["v"]]
                    if math.hypot(vx - ux, vz - uz) > 8.0:
                        if ed["u"] == ni:
                            ed["u"] = best_target_node
                        else:
                            ed["v"] = best_target_node
                        adj = _rebuild_adj()
                else:
                    g_edges.append({
                        "u": ni, "v": best_target_node, "kind": ed["kind"], "cat": ed["cat"],
                        "oneway": ed["oneway"], "br": ed["br"], "tn": ed["tn"], "layer": ed["layer"],
                    })
                    adj = _rebuild_adj()
            elif best_split_edge >= 0 and best_split_q is not None:
                qx, qz, u_t, eu, ev = best_split_q
                if u_t < 0.08:
                    g_edges.append({
                        "u": ni, "v": eu, "kind": ed["kind"], "cat": ed["cat"],
                        "oneway": ed["oneway"], "br": ed["br"], "tn": ed["tn"], "layer": ed["layer"],
                    })
                elif u_t > 0.92:
                    g_edges.append({
                        "u": ni, "v": ev, "kind": ed["kind"], "cat": ed["cat"],
                        "oneway": ed["oneway"], "br": ed["br"], "tn": ed["tn"], "layer": ed["layer"],
                    })
                else:
                    # True T-junction split of edge best_split_edge cleanly at new node q!
                    e2 = g_edges[best_split_edge]
                    q_nid = len(g_nodes)
                    g_nodes.append([float(qx), float(qz), e2["layer"]])
                    e2_tail = dict(e2)
                    e2["v"] = q_nid
                    e2_tail["u"] = q_nid
                    g_edges.append(e2_tail)
                    g_edges.append({
                        "u": ni, "v": q_nid, "kind": ed["kind"], "cat": ed["cat"],
                        "oneway": ed["oneway"], "br": ed["br"], "tn": ed["tn"], "layer": ed["layer"],
                    })
                adj = _rebuild_adj()

    # Contract tiny micro-edges (< 6.0m) cleanly into shared junction nodes, preserving distinct layers
    adj = _rebuild_adj()
    keep_e = [True] * len(g_edges)
    for ei, ed in enumerate(g_edges):
        u, v = ed["u"], ed["v"]
        if u == v:
            keep_e[ei] = False
            continue
        ux, uz, _ = g_nodes[u]
        vx, vz, _ = g_nodes[v]
        d = math.hypot(vx - ux, vz - uz)
        if d < 6.0:
            du, dv = len(adj.get(u, [])), len(adj.get(v, []))
            drop, stay = (u, v) if du <= dv else (v, u)
            keep_e[ei] = False
            for ej in adj.get(drop, []):
                if ej != ei and keep_e[ej]:
                    if g_edges[ej]["u"] == drop:
                        g_edges[ej]["u"] = stay
                    if g_edges[ej]["v"] == drop:
                        g_edges[ej]["v"] = stay
            adj[stay].extend(x for x in adj.get(drop, []) if x != ei)
            adj[drop] = []
    g_edges = [ed for idx, ed in enumerate(g_edges) if keep_e[idx] and ed["u"] != ed["v"]]

    # Deduplicate unordered node pairs cleanly
    seen_pairs: set[tuple[int, int, int]] = set()
    dedup_edges: list[dict] = []
    for ed in g_edges:
        a, b = min(ed["u"], ed["v"]), max(ed["u"], ed["v"])
        pk = (a, b, ed["layer"])
        if pk in seen_pairs:
            continue
        seen_pairs.add(pk)
        dedup_edges.append(ed)
    g_edges = dedup_edges

    # Prune ONLY genuine short (< 45m) dead-end cross-street whiskers branching off >=3-way intersections (looping cleanly)
    changed_whisker = True
    while changed_whisker:
        changed_whisker = False
        adj = _rebuild_adj()
        keep_whisker = [True] * len(g_edges)
        for ni, eis in adj.items():
            if len(eis) != 1:
                continue
            ei = eis[0]
            ed = g_edges[ei]
            if ed["cat"] != "primary":
                continue
            nx, nz, _ = g_nodes[ni]
            if max(abs(nx), abs(nz)) > clip_lim - 60.0:
                continue
            ou, ov = ed["u"], ed["v"]
            other = ov if ou == ni else ou
            if len(adj.get(other, [])) >= 3:
                ux, uz, _ = g_nodes[ou]
                vx, vz, _ = g_nodes[ov]
                if math.hypot(vx - ux, vz - uz) < 45.0:
                    keep_whisker[ei] = False
                    changed_whisker = True
        if changed_whisker:
            g_edges = [ed for idx, ed in enumerate(g_edges) if keep_whisker[idx]]

    # Subdivide edges longer than 85m so curves & DEM terrain hug smoothly
    sub_edges: list[dict] = []
    for ed in g_edges:
        ux, uz, ul = g_nodes[ed["u"]]
        vx, vz, vl = g_nodes[ed["v"]]
        d = math.hypot(vx - ux, vz - uz)
        if d > 85.0:
            n_sub = int(math.ceil(d / 75.0))
            prev_n = ed["u"]
            for s in range(1, n_sub):
                t = s / float(n_sub)
                nx = ux + (vx - ux) * t
                nz = uz + (vz - uz) * t
                mid_n = len(g_nodes)
                g_nodes.append([float(nx), float(nz), ed["layer"]])
                ne = dict(ed)
                ne["u"] = prev_n
                ne["v"] = mid_n
                sub_edges.append(ne)
                prev_n = mid_n
            ne_last = dict(ed)
            ne_last["u"] = prev_n
            sub_edges.append(ne_last)
        else:
            sub_edges.append(ed)
    g_edges = sub_edges

    # === 5) Unified Node-Level Elevation Solver (zero vertical disjunction across junctions & portals!) ===
    n_nodes = len(g_nodes)
    nxs = np.array([nd[0] for nd in g_nodes], dtype=np.float32)
    nzs = np.array([nd[1] for nd in g_nodes], dtype=np.float32)
    ter_y = _sample_elev_bilinear(elev, nxs, nzs)
    wy = ter_y.copy()

    adj = _rebuild_adj()
    node_has_br = [False] * n_nodes
    node_only_tn = [False] * n_nodes
    node_has_tn = [False] * n_nodes
    node_max_layer = [0] * n_nodes

    for ni in range(n_nodes):
        eis = adj.get(ni, [])
        if not eis:
            continue
        all_tn = True
        any_br = False
        any_tn = False
        mlyr = 0
        for ei in eis:
            ed = g_edges[ei]
            if ed["br"] or ed["layer"] >= 1:
                any_br = True
            if ed["tn"] or ed["layer"] <= -1:
                any_tn = True
            else:
                all_tn = False
            if ed["layer"] > mlyr:
                mlyr = ed["layer"]
        node_has_br[ni] = any_br
        node_only_tn[ni] = all_tn and any_tn
        node_has_tn[ni] = any_tn
        node_max_layer[ni] = mlyr

    # Solve bridge floor heights along connected bridge nodes (abutment linear + clearance above river floor 26.5m)
    vis_br = [False] * n_nodes
    for start_n in range(n_nodes):
        if not node_has_br[start_n] or vis_br[start_n]:
            continue
        comp = []
        stk = [start_n]
        vis_br[start_n] = True
        while stk:
            cur = stk.pop()
            comp.append(cur)
            for ei in adj[cur]:
                ed = g_edges[ei]
                if not (ed["br"] or ed["layer"] >= 1):
                    continue
                oth = ed["v"] if ed["u"] == cur else ed["u"]
                if node_has_br[oth] and not vis_br[oth]:
                    vis_br[oth] = True
                    stk.append(oth)
        for ni in comp:
            clr = 19.0 if node_max_layer[ni] >= 2 else 10.5
            wy[ni] = max(float(ter_y[ni]), 26.5) + clr

    # Smooth bridge heights along bridge edges (20 passes of averaging/grade smoothing so decks don't wave over minor peaks)
    for _pass in range(16):
        for ei, ed in enumerate(g_edges):
            if not (ed["br"] or ed["layer"] >= 1):
                continue
            u, v = ed["u"], ed["v"]
            ds = math.hypot(float(nxs[v] - nxs[u]), float(nzs[v] - nzs[u]))
            clr_u = 19.0 if node_max_layer[u] >= 2 else 10.5
            clr_v = 19.0 if node_max_layer[v] >= 2 else 10.5
            floor_u = max(float(ter_y[u]), 26.5) + clr_u
            floor_v = max(float(ter_y[v]), 26.5) + clr_v
            if wy[u] - wy[v] > 0.045 * ds:
                wy[v] = max(floor_v, wy[u] - 0.045 * ds)
            elif wy[v] - wy[u] > 0.045 * ds:
                wy[u] = max(floor_u, wy[v] - 0.045 * ds)

    # Solve tunnel interiors (strictly underground nodes): smoothly linearly interpolate between ground portals <= ter_y - 11.5m!
    # Notice: portal nodes (where ground meets tunnel edge) stay at ter_y (or bridge approach ramp), while interior tunnel nodes stay <= ter_y - 11.5m!
    vis_tn = [False] * n_nodes
    for start_n in range(n_nodes):
        if not node_only_tn[start_n] or vis_tn[start_n]:
            continue
        comp = []
        stk = [start_n]
        vis_tn[start_n] = True
        portals = []
        while stk:
            cur = stk.pop()
            comp.append(cur)
            for ei in adj[cur]:
                ed = g_edges[ei]
                oth = ed["v"] if ed["u"] == cur else ed["u"]
                if node_only_tn[oth]:
                    if not vis_tn[oth]:
                        vis_tn[oth] = True
                        stk.append(oth)
                else:
                    portals.append(oth)
        if portals:
            # Interpolate between portal heights via distance weights, clamped <= ter_y - 11.5m
            py_vals = [min(float(wy[p]), float(ter_y[p])) - 8.0 for p in portals]
            for ni in comp:
                weights = [1.0 / max(1.0, math.hypot(float(nxs[ni] - nxs[p]), float(nzs[ni] - nzs[p]))) for p in portals]
                wsum = sum(weights) or 1.0
                est_y = sum(wv * pv for wv, pv in zip(weights, py_vals)) / wsum
                wy[ni] = min(est_y, float(ter_y[ni]) - 11.5)
        else:
            for ni in comp:
                wy[ni] = float(ter_y[ni]) - 13.0

    # Smooth grade propagation along ground/approach edges (max_grade = 0.055 up from bridges & down toward portals)
    max_grade = 0.055
    for _pass in range(18):
        for ed in g_edges:
            u, v = ed["u"], ed["v"]
            if ed["tn"]:
                continue
            ds = math.hypot(float(nxs[v] - nxs[u]), float(nzs[v] - nzs[u]))
            if wy[u] > wy[v] + max_grade * ds and not node_only_tn[v]:
                wy[v] = max(wy[v], wy[u] - max_grade * ds)
            elif wy[v] > wy[u] + max_grade * ds and not node_only_tn[u]:
                wy[u] = max(wy[u], wy[v] - max_grade * ds)

    # Also smooth interior tunnel grades if needed (<= 0.055), keeping <= ter_y - 11.5m
    for _pass in range(12):
        for ed in g_edges:
            if not ed["tn"]:
                continue
            u, v = ed["u"], ed["v"]
            ds = math.hypot(float(nxs[v] - nxs[u]), float(nzs[v] - nzs[u]))
            if node_only_tn[u] and wy[u] > wy[v] + max_grade * ds:
                wy[u] = min(float(ter_y[u]) - 11.5, wy[v] + max_grade * ds)
            if node_only_tn[v] and wy[v] > wy[u] + max_grade * ds:
                wy[v] = min(float(ter_y[v]) - 11.5, wy[u] + max_grade * ds)

    # Snap tiny terrain residuals on ground nodes strictly to 0.0m
    rel_elev = wy - ter_y
    for ni in range(n_nodes):
        if (not node_has_br[ni]) and (not node_only_tn[ni]) and abs(float(rel_elev[ni])) < 0.45:
            rel_elev[ni] = 0.0
            wy[ni] = ter_y[ni]

    # === 6) Compute node-level G1 tangents (for deg==2 corridors) and export edges in BFS connected order! ===
    def _node_tangent_for_edge(ni: int, ei: int, is_out: bool) -> tuple[float, float]:
        eis = adj.get(ni, [])
        ed = g_edges[ei]
        oth = ed["v"] if ed["u"] == ni else ed["u"]
        dx = float(nxs[oth] - nxs[ni]) * (1.0 if is_out else -1.0)
        dz = float(nzs[oth] - nzs[ni]) * (1.0 if is_out else -1.0)
        l_self = math.hypot(dx, dz) or 1.0
        tx, tz = dx / l_self, dz / l_self
        if len(eis) == 2:
            oei = eis[1] if eis[0] == ei else eis[0]
            oed = g_edges[oei]
            oo = oed["v"] if oed["u"] == ni else oed["u"]
            odx = float(nxs[ni] - nxs[oo]) * (1.0 if is_out else -1.0)
            odz = float(nzs[ni] - nzs[oo]) * (1.0 if is_out else -1.0)
            ol = math.hypot(odx, odz) or 1.0
            if (odx * dx + odz * dz) / (ol * l_self) > 0.50:
                sx, sz = tx + odx / ol, tz + odz / ol
                sn = math.hypot(sx, sz) or 1.0
                return sx / sn, sz / sn
        return tx, tz

    # Traverse connected components in BFS order so contiguous corridors export sequentially!
    adj = _rebuild_adj()
    vis_edge = [False] * len(g_edges)
    ordered_edges: list[int] = []
    for ei in range(len(g_edges)):
        if vis_edge[ei]:
            continue
        q_edges = [ei]
        vis_edge[ei] = True
        head = 0
        while head < len(q_edges):
            cur_ei = q_edges[head]
            head += 1
            ordered_edges.append(cur_ei)
            ced = g_edges[cur_ei]
            for ni in (ced["u"], ced["v"]):
                for nei in adj.get(ni, []):
                    if not vis_edge[nei]:
                        vis_edge[nei] = True
                        q_edges.append(nei)

    export_edges: list[tuple] = []  # (kind, flags, p0, p1, p2, p3, elev0, elev1)
    for ei in ordered_edges:
        ed = g_edges[ei]
        u, v = ed["u"], ed["v"]
        p0 = (float(nxs[u]), float(wy[u]), float(nzs[u]))
        p3 = (float(nxs[v]), float(wy[v]), float(nzs[v]))
        seg_xz = math.hypot(p3[0] - p0[0], p3[2] - p0[2])
        if seg_xz < 1.5:
            continue
        tx0, tz0 = _node_tangent_for_edge(u, ei, is_out=True)
        tx1, tz1 = _node_tangent_for_edge(v, ei, is_out=False)
        cx, cz = (p3[0] - p0[0]) / seg_xz, (p3[2] - p0[2]) / seg_xz
        if tx0 * cx + tz0 * cz < 0.5:
            tx0, tz0 = cx, cz
        if tx1 * cx + tz1 * cz < 0.5:
            tx1, tz1 = cx, cz
        hl = seg_xz / 3.0
        p1 = (p0[0] + tx0 * hl, p0[1] + (p3[1] - p0[1]) / 3.0, p0[2] + tz0 * hl)
        p2 = (p3[0] - tx1 * hl, p3[1] - (p3[1] - p0[1]) / 3.0, p3[2] - tz1 * hl)

        e0 = float(rel_elev[u])
        e1 = float(rel_elev[v])
        flags = 0
        if ed["br"] or max(e0, e1) >= 6.5:
            flags |= 1
        if ed["tn"] or min(e0, e1) <= -6.5:
            flags |= 2
        if e0 >= 6.5:
            flags |= 4
        if e1 >= 6.5:
            flags |= 8
        export_edges.append((ed["kind"], flags, p0, p1, p2, p3, e0, e1))

    # Write SJR1 binary
    bin_path = os.path.join(out_dir, "sintanjin_roads.bin")
    with open(bin_path, "wb") as f:
        f.write(b"SJR1")
        f.write(struct.pack("<I", len(export_edges)))
        for kind, flags, p0, p1, p2, p3, e0, e1 in export_edges:
            f.write(struct.pack(
                "<BBH14f",
                kind, flags, 0,
                p0[0], p0[1], p0[2],
                p1[0], p1[1], p1[2],
                p2[0], p2[1], p2[2],
                p3[0], p3[1], p3[2],
                e0, e1,
            ))

    # Visual verification preview_roads_backbone.png
    sz_v = 1536
    bg = np.array(sat_img.resize((sz_v, sz_v), Image.Resampling.BILINEAR), dtype=np.float32) * 0.48
    wat_v = np.array(Image.fromarray(water_mask.astype(np.uint8) * 255).resize((sz_v, sz_v), Image.NEAREST)) > 127
    bg[wat_v] = np.array([22, 85, 145], dtype=np.float32)
    im_r = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8), mode="RGB")
    dr = ImageDraw.Draw(im_r)

    def _to_v(x: float, z: float) -> tuple[float, float]:
        return ((x / CS2_SIDE_M + 0.5) * (sz_v - 1), (0.5 - z / CS2_SIDE_M) * (sz_v - 1))

    counts_by_kind = [0] * 6
    bridge_cnt = 0
    tunnel_cnt = 0
    col_map = {
        0: (255, 130, 30),   # 3L Highway
        1: (250, 195, 45),   # 2L Highway / Trunk
        2: (70, 215, 245),   # 4L Divided Arterial
        3: (125, 225, 180),  # 2L Arterial
        4: (100, 195, 255),  # 2L Oneway Street
        5: (240, 240, 245),  # Double Train Track
    }
    for kind, flags, p0, p1, p2, p3, e0, e1 in export_edges:
        counts_by_kind[kind] += 1
        if flags & 1:
            bridge_cnt += 1
        if flags & 2:
            tunnel_cnt += 1
        pts_b = []
        for s in range(9):
            t = s / 8.0
            mt = 1.0 - t
            bx = (mt**3) * p0[0] + 3 * (mt**2) * t * p1[0] + 3 * mt * (t**2) * p2[0] + (t**3) * p3[0]
            bz = (mt**3) * p0[2] + 3 * (mt**2) * t * p1[2] + 3 * mt * (t**2) * p2[2] + (t**3) * p3[2]
            pts_b.append(_to_v(bx, bz))
        col = col_map.get(kind, (220, 220, 220))
        w_px = 4 if kind in (0, 1) else 3
        if flags & 1:
            dr.line(pts_b, fill=(255, 255, 120), width=w_px + 2)
        elif flags & 2:
            dr.line(pts_b, fill=(90, 130, 255), width=w_px + 2)
        dr.line(pts_b, fill=col, width=w_px)

    try:
        font = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 18)
        font_sm = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 14)
    except Exception:
        font = font_sm = ImageFont.load_default()
    dr.rectangle([20, 20, 620, 195], fill=(18, 22, 30), outline=(140, 165, 190), width=2)
    dr.text((34, 28), f"Method A: 간선 도로/고속도로/철도 백본 ({len(export_edges):,} 세그먼트, IC램프 제외)", fill=(255, 255, 255), font=font)
    rows = [
        ((255, 130, 30), f"고속도로 (경부·호남지선 2~3L) : {counts_by_kind[0] + counts_by_kind[1]:,} 세그먼트"),
        ((70, 215, 245), f"주요 간선도로 (신탄진로·대덕대로·신문로 등) : {counts_by_kind[2] + counts_by_kind[3] + counts_by_kind[4]:,} 세그먼트"),
        ((240, 240, 245), f"본선 철도 (경부선·경부고속선 복선, 조차장 제외) : {counts_by_kind[5]:,} 세그먼트"),
        ((255, 255, 120), f"교량·고가 구간 (+10~19m) : {bridge_cnt:,}개  |  터널 구간 (-14m) : {tunnel_cnt:,}개"),
        ((185, 200, 215), "※ 회덕JC·신탄진IC·북대전IC 램프는 수동 커브/Move It 연결용으로 제외됨"),
    ]
    yc = 60
    for col, txt in rows:
        dr.rectangle([34, yc + 2, 48, yc + 15], fill=col, outline=(255, 255, 255))
        dr.text((56, yc), txt, fill=(235, 242, 248), font=font_sm)
        yc += 25
    im_r.save(os.path.join(out_dir, "preview_roads_backbone.png"))
    print(f"  Exported {len(export_edges)} backbone road/rail spans -> sintanjin_roads.bin (bridges={bridge_cnt}, tunnels={tunnel_cnt})")
    return {"total": len(export_edges), "bridges": bridge_cnt, "tunnels": tunnel_cnt}


def build_resource_visuals(
    elev: np.ndarray, water_mask: np.ndarray, sat_img: Image.Image,
    res_work: dict[str, np.ndarray], res_labels: list[tuple[str, tuple[int, int, int], float, float]],
    lat_n: float, lat_s: float, lon_w: float, lon_e: float, out_dir: str
):
    """Render combined hillshade resource map preview (1536) & satellite Resource Overlay (4096)."""
    def _paint_layers(base_arr: np.ndarray, out_sz: int, wat_sz: np.ndarray) -> np.ndarray:
        canvas = base_arr.astype(np.float32, copy=True)
        layers = [
            ("resource_forest", np.array([46, 158, 72], dtype=np.float32), 0.42),
            ("resource_fertile", np.array([235, 212, 48], dtype=np.float32), 0.58),
            ("resource_underground_water", np.array([45, 145, 245], dtype=np.float32), 0.52),
            ("resource_ore", np.array([240, 115, 38], dtype=np.float32), 0.62),
            ("resource_oil", np.array([225, 52, 90], dtype=np.float32), 0.68),
        ]
        for key, col, alpha in layers:
            m = np.array(
                Image.fromarray(res_work[key], mode="F").resize((out_sz, out_sz), Image.BILINEAR),
                dtype=np.float32,
            )
            a = np.clip(m * alpha, 0.0, alpha)[:, :, None]
            canvas = canvas * (1.0 - a) + col[None, None, :] * a
        canvas[wat_sz] = np.array([28, 108, 178], dtype=np.float32)
        return np.clip(canvas, 0, 255).astype(np.uint8)

    def _draw_legend_and_labels(im: Image.Image, font_sz: int, legend_w: int, draw_zones: bool):
        draw = ImageDraw.Draw(im)
        sz = im.size[0]
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", font_sz)
            font_sm = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", max(12, int(font_sz * 0.85)))
        except Exception:
            font = font_sm = ImageFont.load_default()

        if draw_zones:
            for lbl, col, lat, lon in res_labels:
                if not (lat_s <= lat <= lat_n and lon_w <= lon <= lon_e):
                    continue
                x = (lon - lon_w) / (lon_e - lon_w) * (sz - 1)
                y = (lat_n - lat) / (lat_n - lat_s) * (sz - 1)
                r = max(5, int(sz * 0.004))
                draw.ellipse([x - r, y - r, x + r, y + r], fill=col, outline=(255, 255, 255), width=2)
                bb = draw.textbbox((0, 0), lbl, font=font_sm)
                tw = bb[2] - bb[0]
                th = bb[3] - bb[1]
                tx = x + r + 8 if (x + r + 8 + tw <= sz - 24) else max(24.0, x - r - 8 - tw)
                ty = min(max(24.0, y - th / 2.0), sz - th - 24.0)
                draw.text((tx, ty), lbl, fill=(255, 255, 255), font=font_sm, stroke_width=3, stroke_fill=(15, 20, 30))

        # Legend box top-left
        pad = int(sz * 0.015)
        box_h = int(font_sz * 9.5)
        draw.rectangle([pad, pad, pad + legend_w, pad + box_h], fill=(20, 26, 36), outline=(140, 160, 185), width=2)
        draw.text((pad + 14, pad + 10), "시티즈 2 자원 배치 가이드 (1.45× 확대)", fill=(255, 255, 255), font=font)
        items = [
            ((235, 212, 48), "비옥한 토지 (Fertile) : 미호·금강북안·구즉·전민 충적평야"),
            ((225, 52, 90), "석유 공업 (Oil) : 대덕3·4산단·평촌·탑립·벤처협동화단지"),
            ((240, 115, 38), "광물 자원 (Ore) : 불무산·계족산 서사면·자운 능선"),
            ((45, 145, 245), "지하수 (Groundwater) : 금강·갑천 연안 충적 대수층"),
            ((46, 158, 72), "산림 자원 (Forest) : 산지·구릉 임야 (시가지·농지 제외)"),
        ]
        y_cur = pad + int(font_sz * 2.1)
        sw = max(14, int(font_sz * 1.1))
        for col, text in items:
            draw.rectangle([pad + 14, y_cur, pad + 14 + sw, y_cur + sw], fill=col, outline=(255, 255, 255))
            draw.text((pad + 22 + sw, y_cur - 2), text, fill=(235, 242, 248), font=font_sm)
            y_cur += int(font_sz * 1.42)

    # 1) preview_resources_combined.png (1536x1536 hillshade backdrop)
    sz_p = 1536
    el_p = np.array(Image.fromarray(elev, mode="F").resize((sz_p, sz_p), Image.BILINEAR))
    wat_p = np.array(Image.fromarray((water_mask.astype(np.uint8) * 255)).resize((sz_p, sz_p), Image.NEAREST)) > 127
    gy, gx = np.gradient(el_p, REAL_SIDE_M / sz_p)
    hs = np.clip(
        math.sin(math.radians(42.0)) * np.cos(np.arctan(np.hypot(gx, gy)))
        + math.cos(math.radians(42.0)) * np.sin(np.arctan(np.hypot(gx, gy))) * np.cos(math.radians(315.0) - np.arctan2(-gx, gy)),
        0.0, 1.0,
    )
    base_hs = np.stack([115 * (0.45 + 0.65 * hs)] * 3, axis=-1)
    comb = Image.fromarray(_paint_layers(base_hs, sz_p, wat_p), mode="RGB")
    _draw_legend_and_labels(comb, font_sz=18, legend_w=540, draw_zones=False)
    comb.save(os.path.join(out_dir, "preview_resources_combined.png"))

    # 2) resources_overlay_4096.png (4096x4096 satellite overlay for CS2 Image Overlay mod)
    sz_o = 4096
    wat_o = water_mask
    sat_arr = np.array(sat_img, dtype=np.float32) * 0.88
    ov_im = Image.fromarray(_paint_layers(sat_arr, sz_o, wat_o), mode="RGB")
    _draw_legend_and_labels(ov_im, font_sz=36, legend_w=1180, draw_zones=True)
    ov_im.save(os.path.join(out_dir, "resources_overlay_4096.png"))


def build_previews(
    elev: np.ndarray, water_mask: np.ndarray, masks: dict, sat_img: Image.Image,
    lat_n: float, lat_s: float, lon_w: float, lon_e: float, out_dir: str
):
    """Save hillshade, satellite+road alignment, and landmark-annotated inspection previews."""
    size = 1536
    el_s = np.array(Image.fromarray(elev, mode="F").resize((size, size), Image.BILINEAR))
    wat_s = np.array(Image.fromarray((water_mask.astype(np.uint8) * 255), mode="L").resize((size, size), Image.NEAREST)) > 127

    gy, gx = np.gradient(el_s, REAL_SIDE_M / size)
    az = math.radians(315.0)
    alt = math.radians(42.0)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    hs = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
    hs = np.clip(hs, 0.0, 1.0)

    # Hypsometric tint
    rgb = np.zeros((size, size, 3), dtype=np.float32)
    t = np.clip((el_s - 24.0) / 180.0, 0.0, 1.0)
    rgb[:, :, 0] = 65 + 150 * t
    rgb[:, :, 1] = 135 + 45 * t - 40 * (t ** 2)
    rgb[:, :, 2] = 75 + 40 * (1.0 - t)
    shaded = np.clip(rgb * (0.45 + 0.70 * hs[:, :, None]), 0, 255)
    shaded[wat_s] = np.array([34, 118, 178], dtype=np.float32)
    hs_im = Image.fromarray(shaded.astype(np.uint8), mode="RGB")
    hs_im.save(os.path.join(out_dir, "preview_topography_hillshade.png"))

    # Satellite + alignment overlay
    sat_s = sat_img.resize((size, size), Image.BILINEAR)
    hwy_s = np.array(masks["highways"].resize((size, size), Image.BILINEAR)) > 90
    rail_s = np.array(masks["rail"].resize((size, size), Image.BILINEAR)) > 90
    sat_arr = np.array(sat_s, dtype=np.uint8)
    sat_arr[wat_s] = (sat_arr[wat_s] * 0.6 + np.array([0, 140, 230]) * 0.4).astype(np.uint8)
    sat_arr[hwy_s] = np.array([255, 195, 0], dtype=np.uint8)
    sat_arr[rail_s] = np.array([235, 235, 235], dtype=np.uint8)
    align_im = Image.fromarray(sat_arr, mode="RGB")
    align_im.save(os.path.join(out_dir, "preview_satellite_alignment.png"))

    # Annotated landmarks preview
    ann = align_im.copy()
    draw = ImageDraw.Draw(ann)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 18)
    except Exception:
        font = ImageFont.load_default()

    landmarks = [
        ("불무산 (160.8m)", 36.45485, 127.39064),
        ("금강변 드론공원", 36.45620, 127.40250),
        ("금강로하스 / 석봉동", 36.45380, 127.42080),
        ("신탄진역", 36.44963, 127.42817),
        ("신탄진고등학교", 36.44883, 127.43642),
        ("대덕산업단지 3·4 (목상동)", 36.44000, 127.40300),
        ("신탄진 IC", 36.44000, 127.41900),
        ("송강동", 36.43086, 127.38076),
        ("관평동 (테크노밸리)", 36.42270, 127.39837),
        ("탑립동 (벤처타운)", 36.41500, 127.41300),
        ("대전철도차량정비단", 36.42611, 127.43069),
        ("북대전 IC", 36.41235, 127.38482),
        ("화암네거리", 36.40709, 127.37356),
        ("회덕 JC", 36.40446, 127.41645),
        ("회덕역", 36.40225, 127.42128),
        ("전민동 (엑스포APT)", 36.39773, 127.40579),
        ("문지동", 36.39156, 127.39773),
        ("대전 벤처 협동화 단지 (엑스포로339)", 36.38600, 127.39950),
        ("원촌교 (갑천 남단)", 36.37851, 127.40980),
    ]
    for label, lat, lon in landmarks:
        if not (lat_s <= lat <= lat_n and lon_w <= lon <= lon_e):
            continue
        x = (lon - lon_w) / (lon_e - lon_w) * (size - 1)
        y = (lat_n - lat) / (lat_n - lat_s) * (size - 1)
        draw.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(255, 60, 40), outline=(255, 255, 255), width=2)
        draw.text((x + 10, y - 10), label, fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    ann.save(os.path.join(out_dir, "preview_map_regions_annotated.png"))


def write_docs_and_meta(out_dir: str, lat_n: float, lat_s: float, lon_w: float, lon_e: float, elev: np.ndarray, world_max_m: float):
    """Write machine-readable metadata and user guide with exact CS2 import numbers."""
    meta = {
        "map_name": "Sintanjin - Daedeok Ind - Gwanpyeong - Jeonmin & Daejeon Venture Coop (1.45x Zoomed)",
        "bounds": {
            "lat_north": round(lat_n, 6),
            "lat_south": round(lat_s, 6),
            "lon_west": round(lon_w, 6),
            "lon_east": round(lon_e, 6),
            "center_lat": CENTER_LAT,
            "center_lon": CENTER_LON,
        },
        "scale": {
            "real_width_m": round(REAL_SIDE_M, 2),
            "real_height_m": round(REAL_SIDE_M, 2),
            "cs2_playable_m": CS2_SIDE_M,
            "cs2_worldmap_m": CS2_SIDE_M * WORLD_MULTIPLIER,
            "zoom_multiplier": SCALE_FACTOR,
        },
        "elevation": {
            "min_m": round(float(elev.min()), 2),
            "p50_m": round(float(np.median(elev)), 2),
            "max_m": round(float(elev.max()), 2),
            "worldmap_max_m": round(world_max_m, 2),
            "recommended_sea_level_m": WATER_SEA_LEVEL_M,
        },
        "files": {
            "recommended_1024m_playable": "heightmap_cs2_4096_1024m.png",
            "recommended_1024m_worldmap": "heightmap_cs2_worldmap_1024m.png",
            "default_4096m_playable": "heightmap_cs2_4096_std4096m.png",
            "default_4096m_worldmap": "heightmap_cs2_worldmap_4096m.png",
            "ultra_fine_500m_playable": "heightmap_cs2_4096_500m.png",
            "image_overlay_4096": "satellite_overlay_4096.png",
            "resources_overlay_4096": "resources_overlay_4096.png",
            "resources_combined_preview": "preview_resources_combined.png",
            "cs2_resources_bin": "sintanjin_resources_256.bin",
            "cs2_trees_bin": "sintanjin_trees.bin",
            "forest_trees_preview": "preview_forest_trees.png",
            "cs2_roads_bin": "sintanjin_roads.bin",
            "roads_backbone_preview": "preview_roads_backbone.png",
        },
    }
    with open(os.path.join(out_dir, "map_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    guide = f"""# 신탄진·대덕산단·관평·전민동·대전 벤처 협동화 단지 CS2 하이트맵 가이드

## 1. 포함 범위 및 축척 (1.45× 확대 매핑)
요청하신 범위(**불무산·금강 북안 ~ 전민동·문지동·대전 벤처 협동화 단지·원촌교**, **송강·화암·관평·탑립 ~ 석봉동·신탄진역·신탄진고·평촌산단·대전철도차량정비단·회덕JC·회덕역**)만 **약 9.89 km × 9.89 km** 정사각 영역으로 잘라내어 시티즈: 스카이라인 2 기본 맵 크기(**14.336 km × 14.336 km**)에 **1.45배**로 꽉 차게 확대했습니다.
- 둔산동/정부청사 남쪽 및 대청호/계족산 동쪽 외곽은 제외했습니다.
- 실제 지형·능선(불무산 160.8m, 동측 산지)은 Copernicus GLO-30 C2 연속 DEM 기반으로 매끄럽게 유지하고, 금강·갑천 하상/제방과 공단·주거지 평지(목상·대덕산단, 석봉동, 신탄진·철도정비단, 관평·탑립, 전민·벤처단지)를 단차·웅덩이 없이 연속 평탄화했습니다.

| 항목 | 값 |
| --- | --- |
| 위도 범위 | {lat_s:.5f}°N ~ {lat_n:.5f}°N |
| 경도 범위 | {lon_w:.5f}°E ~ {lon_e:.5f}°E |
| 실측 / CS2 축척 | {REAL_SIDE_M:.1f} m → {CS2_SIDE_M:.1f} m (1.45×) |
| 플레이 맵 최저 / 최고 고도 | {elev.min():.1f} m / {elev.max():.1f} m |
| 권장 해수면 (Sea Level) | **{WATER_SEA_LEVEL_M:.1f} m** (금강·갑천 수로 안정 수위) |

## 2. 파일별 용도 및 CS2 에디터 Import 설정

| 파일명 | 권장 Height Scale | 설명 |
| --- | --- | --- |
| **`heightmap_cs2_4096_1024m.png`** | **`1024 m`** | **[추천] 고정밀 하이트맵** (1.56cm 단위 정밀도, 월드맵과 클리핑 없이 호환) |
| **`heightmap_cs2_worldmap_1024m.png`** | **`1024 m`** | **[추천] 4× 외곽 월드맵** (계룡산·식장산·대청호 원경 포함, 플레이 경계 심리스 블렌딩) |
| `heightmap_cs2_4096_std4096m.png` | `4096 m` (기본값) | 에디터 Height Scale 변경 없이 기본 `4096 m` 그대로 Import용 |
| `heightmap_cs2_worldmap_4096m.png` | `4096 m` (기본값) | 기본 `4096 m` 설정과 짝을 이루는 외곽 월드맵 |
| `heightmap_cs2_4096_500m.png` | `500 m` | 플레이 영역 전용 초정밀 하이트맵 (0.76cm 단위, 월드맵 불필요 시) |
| `satellite_overlay_4096.png` | - | **Image Overlay 모드용 4096×4096 위성 오버레이** (하이트맵과 1:1 좌표 일치) |
| `resources_overlay_4096.png` | - | **Image Overlay 모드용 4096×4096 천연자원 배치 가이드** (비옥·석유·광물·지하수·산림) |
| `sintanjin_resources_256.bin` | - | `SintanjinMapBuilder` 모드용 `256×256` 천연자원 바이너리 (비옥·광물·석유·어업·지하수) |
| `sintanjin_trees.bin` | - | `SintanjinMapBuilder` 모드용 실측 위성·DEM 기반 산림/수변 식생 바이너리 (~8.4만 그루) |
| `sintanjin_roads.bin` | - | `SintanjinMapBuilder` 모드용 Method A 간선도로·고속도로·철도 백본 바이너리 (IC 램프 제외) |

## 3. 적용 방법
1. `%UserProfile%\\AppData\\LocalLow\\Colossal Order\\Cities Skylines II\\Heightmaps\\` 폴더에 원하는 하이트맵 복사
2. (선택) `...\\Overlays\\` 폴더에 `satellite_overlay_4096.png` 복사
3. CS2 **Map Editor → Terrain → Import Heightmap**에서 하이트맵 선택 후 **Height Scale**을 표에 맞게 설정 (`1024 m` 권장, 월드맵 쓰면 **Import Worldmap**도 동일 스케일로 선택)
4. **Water → Sea Level**을 **`{WATER_SEA_LEVEL_M:.1f} m`** 로 맞추면 금강·갑천 수로가 즉시 채워집니다.
5. `SintanjinMapBuilder` 모드가 설치되어 있으므로 에디터 또는 게임에서 **`F6`** (전체: 천연자원+실측 숲+백본 도로/철도 자동 구축), **`Ctrl+Shift+R`** (천연자원만), **`Ctrl+Shift+T`** (숲/나무만), **`Ctrl+Shift+H`** (간선 도로/고속도로/철도 백본만), **`Ctrl+Shift+X`** (심은 나무 초기화) 단축키로 즉시 자동 반영됩니다.
6. 백본 도로 깔기 후 회덕JC·신탄진IC·북대전IC 연결 램프만 바닐라 도로 커브 + `Move It`으로 매끄럽게 이어 주면 1:1 대전 북부 도로망이 완성됩니다.
"""
    with open(os.path.join(out_dir, "MAP_GUIDE.md"), "w", encoding="utf-8") as f:
        f.write(guide)


def main():
    parser = argparse.ArgumentParser()
    default_out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sintanjin_jeonmin")
    parser.add_argument("--out-dir", default=default_out)
    parser.add_argument("--cache-dir", default=os.path.join(default_out, "_cache"))
    parser.add_argument("--resources-only", action="store_true",
                        help="Reuse saved 1024m heightmap and satellite; rebuild resources, trees and resource previews only")
    args = parser.parse_args()

    out_dir = args.out_dir
    cache_dir = args.cache_dir
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)

    lat_n, lat_s, lon_w, lon_e = compute_bounds(CENTER_LAT, CENTER_LON, REAL_SIDE_M)
    if args.resources_only:
        # Read both inputs before generating anything; never re-engineer the saved terrain.
        elev = np.array(Image.open(os.path.join(out_dir, "heightmap_cs2_4096_1024m.png")), dtype=np.float32) * (1024.0 / 65535.0)
        sat_img = Image.open(os.path.join(out_dir, "satellite_overlay_4096.png")).convert("RGB")
        if elev.shape != (4096, 4096) or sat_img.size != (4096, 4096):
            raise ValueError("Resources require matching 4096x4096 heightmap and satellite inputs")
        osm = fetch_osm_features(lat_n, lat_s, lon_w, lon_e, os.path.join(cache_dir, "osm_area.json"))
        masks = rasterize_osm_masks(osm, lat_n, lat_s, lon_w, lon_e, size=elev.shape[0])
        water_mask = elev < WATER_SEA_LEVEL_M
        res_work, labels = generate_resources(elev, water_mask, masks, lat_n, lat_s, lon_w, lon_e, out_dir)
        generate_realistic_trees(elev, water_mask, masks, sat_img, res_work, out_dir)
        build_resource_visuals(elev, water_mask, sat_img, res_work, labels, lat_n, lat_s, lon_w, lon_e, out_dir)
        return
    print(f"Playable bounds ({REAL_SIDE_M:.1f}m -> {CS2_SIDE_M:.0f}m @ {SCALE_FACTOR}x):")
    print(f"  N={lat_n:.5f}, S={lat_s:.5f}, W={lon_w:.5f}, E={lon_e:.5f}")

    # 1. Playable DEM: primary Copernicus GLO-30 C2 B-spline (void-free), fallback z14 Terrarium
    print("[1/6] Fetching playable Copernicus GLO-30 C2 DEM...")
    try:
        elev = fetch_copernicus_glo30_window(lat_n, lat_s, lon_w, lon_e, cache_dir, out_size=4096)
        print(f"  Copernicus GLO-30 C2 clean DEM loaded (min={elev.min():.2f}m, max={elev.max():.2f}m)")
    except Exception as exc:
        print(f"  Copernicus fallback to z14 Terrarium: {exc}")
        x0f, y0f = deg2num_f(lat_n, lon_w, 14)
        dem_raw, px_box = fetch_terrarium_grid(lat_n, lat_s, lon_w, lon_e, 14, cache_dir)
        dem_clean, n_bad = repair_dem_voids(dem_raw, min_valid_m=16.0)
        print(f"  Repaired {n_bad} DEM nodata/negative glitches (clean min={dem_clean.min():.2f}m)")
        elev = resample_mercator_window(
            dem_clean, px_box, lat_n, lat_s, lon_w, lon_e,
            int(math.floor(x0f)), int(math.floor(y0f)), 14, out_size=4096
        )

    # 2. OSM geometry masks
    print("[2/6] Loading OSM waterways, landuse & corridors...")
    osm_path = os.path.join(cache_dir, "osm_area.json")
    osm = fetch_osm_features(lat_n, lat_s, lon_w, lon_e, osm_path)
    masks = rasterize_osm_masks(osm, lat_n, lat_s, lon_w, lon_e, size=4096)

    # 3. Waterbed grading & urban/industrial flatland micro-terracing
    print("[3/6] Grading Geumgang/Gapcheon & micro-terracing buildable plains...")
    elev_final, water_mask = apply_river_and_terrace_engineering(elev, masks)
    elev_final = polish_mountain_terrain(elev_final, masks, lat_n, lat_s, lon_w, lon_e, cache_dir)
    print(f"  Playable elev: min={elev_final.min():.2f}m, p50={np.median(elev_final):.2f}m, max={elev_final.max():.2f}m")

    # 4. WorldMap 4x DEM (Copernicus GLO-30 B-spline, fallback z11 Terrarium) + seamless feather blending
    print("[4/6] Fetching 4x WorldMap DEM & blending core...")
    w_lat_n, w_lat_s, w_lon_w, w_lon_e = compute_bounds(CENTER_LAT, CENTER_LON, REAL_SIDE_M * WORLD_MULTIPLIER)
    w_bad = 0
    try:
        world_elev = fetch_copernicus_glo30_window(w_lat_n, w_lat_s, w_lon_w, w_lon_e, cache_dir, out_size=4096)
        world_elev = exact_gaussian_f32(world_elev, 1.6)
        print("  WorldMap source: Copernicus GLO-30 C2 B-spline")
    except Exception as exc:
        print(f"  WorldMap Copernicus fallback to z11 Terrarium: {exc}")
        wx0f, wy0f = deg2num_f(w_lat_n, w_lon_w, 11)
        w_dem_raw, w_px_box = fetch_terrarium_grid(w_lat_n, w_lat_s, w_lon_w, w_lon_e, 11, cache_dir)
        w_dem_clean, w_bad = repair_dem_voids(w_dem_raw, min_valid_m=12.0, spike_thresh_m=80.0, dilate_px=0)
        world_elev = resample_mercator_window(
            w_dem_clean, w_px_box, w_lat_n, w_lat_s, w_lon_w, w_lon_e,
            int(math.floor(wx0f)), int(math.floor(wy0f)), 11, out_size=4096
        )
        world_elev = gaussian_blur_f32(world_elev, sigma=2.5)
    core_1024 = np.array(Image.fromarray(elev_final, mode="F").resize((1024, 1024), Image.BICUBIC), dtype=np.float32)
    feather = Image.new("L", (1024, 1024), 0)
    ImageDraw.Draw(feather).rectangle([40, 40, 983, 983], fill=255)
    fw = np.array(feather.filter(ImageFilter.GaussianBlur(radius=18.0)), dtype=np.float32) / 255.0
    world_elev[1536:2560, 1536:2560] = core_1024 * fw + world_elev[1536:2560, 1536:2560] * (1.0 - fw)
    world_max_m = float(world_elev.max())
    print(f"  WorldMap elev: min={world_elev.min():.2f}m, max={world_max_m:.2f}m (repaired {w_bad})")

    # 5. Export 16-bit PNGs + Resource Maps + Satellite Overlay
    print("[5/6] Exporting 16-bit heightmaps, resources & satellite overlay...")
    save_uint16_png(elev_final, 1024.0, os.path.join(out_dir, "heightmap_cs2_4096_1024m.png"))
    save_uint16_png(world_elev, 1024.0, os.path.join(out_dir, "heightmap_cs2_worldmap_1024m.png"))
    save_uint16_png(elev_final, 4096.0, os.path.join(out_dir, "heightmap_cs2_4096_std4096m.png"))
    save_uint16_png(world_elev, 4096.0, os.path.join(out_dir, "heightmap_cs2_worldmap_4096m.png"))
    save_uint16_png(elev_final, 500.0, os.path.join(out_dir, "heightmap_cs2_4096_500m.png"))

    Image.fromarray(
        np.clip((elev_final - elev_final.min()) / max(1.0, elev_final.max() - elev_final.min()) * 255.0, 0, 255).astype(np.uint8),
        mode="L",
    ).resize((1024, 1024), Image.BILINEAR).save(os.path.join(out_dir, "heightmap_preview_8bit.png"))

    res_work, res_labels = generate_resources(elev_final, water_mask, masks, lat_n, lat_s, lon_w, lon_e, out_dir)
    sat_img = fetch_satellite_overlay(lat_n, lat_s, lon_w, lon_e, cache_dir, out_size=4096)
    sat_img.save(os.path.join(out_dir, "satellite_overlay_4096.png"))

    # 6. Build trees + backbone roads + visual verification previews & docs
    print("[6/6] Sampling realistic forest, backbone roads/rails, previews & MAP_GUIDE.md...")
    generate_realistic_trees(elev_final, water_mask, masks, sat_img, res_work, out_dir)
    generate_backbone_roads(osm, elev_final, water_mask, sat_img, lat_n, lat_s, lon_w, lon_e, out_dir)
    build_previews(elev_final, water_mask, masks, sat_img, lat_n, lat_s, lon_w, lon_e, out_dir)
    build_resource_visuals(elev_final, water_mask, sat_img, res_work, res_labels, lat_n, lat_s, lon_w, lon_e, out_dir)
    write_docs_and_meta(out_dir, lat_n, lat_s, lon_w, lon_e, elev_final, world_max_m)
    print(f"Done! Output directory: {out_dir}")


if __name__ == "__main__":
    main()
