"""Render a georeferenced road/lanes map from cached OSM vectors.

Run after fetching _imagery_cache/roads_osm.json. Lane positions are schematic;
unknown lane counts are never inferred from road classification.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from PIL import Image
import numpy as np


def lane_count(tags):
    value = tags.get("lanes", "")
    return int(value) if value.isascii() and value.isdigit() and 1 <= int(value) <= 16 else None


def offset_line(points, distance):
    """Offset a polyline in pixel space, with bounded joins at sharp corners."""
    points = np.asarray(points, dtype=float)
    delta = np.diff(points, axis=0)
    length = np.linalg.norm(delta, axis=1)
    if len(length) == 0 or np.any(length == 0):
        raise ValueError("Polyline must contain distinct consecutive points")
    normals = np.column_stack((-delta[:, 1], delta[:, 0])) / length[:, None]
    joins = np.vstack((normals[0], (normals[:-1] + normals[1:]) / 2, normals[-1]))
    denom = np.sum(joins * joins, axis=1)
    return points + joins * (distance / np.maximum(denom, .5))[:, None]


def main():
    root = Path(__file__).resolve().parents[1] / "sintanjin_jeonmin"
    meta = json.loads((root / "map_metadata.json").read_text(encoding="utf-8"))
    bounds = meta["bounds"]
    roads = json.loads((root / "_imagery_cache/roads_osm.json").read_text(encoding="utf-8"))["elements"]
    size = 8192
    scale = (size - 1) / meta["scale"]["real_width_m"]
    edges, dividers, unknown, tunnels, labels = [], [], [], [], []
    used_cells = set()
    counts = {"roads": 0, "tagged_lanes": 0, "unknown_lanes": 0}
    for road in sorted(roads, key=lambda r: int(r.get("tags", {}).get("layer", "0")) if r.get("tags", {}).get("layer", "0").lstrip("-").isdigit() else 0):
        tags = road.get("tags", {})
        if tags.get("area") == "yes":
            continue
        points = np.array([
            ((p["lon"] - bounds["lon_west"]) / (bounds["lon_east"] - bounds["lon_west"]) * (size - 1),
             (bounds["lat_north"] - p["lat"]) / (bounds["lat_north"] - bounds["lat_south"]) * (size - 1))
            for p in road.get("geometry", [])
        ])
        if len(points) < 2:
            continue
        points = points[np.r_[True, np.any(np.diff(points, axis=0) != 0, axis=1)]]
        if len(points) < 2 or (points[:, 0].max() < 0 or points[:, 1].max() < 0 or points[:, 0].min() >= size or points[:, 1].min() >= size):
            continue
        if tags.get("tunnel") in ("yes", "building_passage"):
            tunnels.append(points)
            continue
        counts["roads"] += 1
        lanes = lane_count(tags)
        if lanes is None:
            unknown.append(points)
            counts["unknown_lanes"] += 1
            continue
        counts["tagged_lanes"] += 1
        # ponytail: equal 3.25m lanes are schematic; use surveyed lane geometry for exact markings.
        width = lanes * 3.25 * scale
        edges.extend((offset_line(points, -width / 2), offset_line(points, width / 2)))
        dividers.extend(offset_line(points, -width / 2 + i * width / lanes) for i in range(1, lanes))
        lengths = np.linalg.norm(np.diff(points, axis=0), axis=1)
        if lengths.sum() < 65 * scale:
            continue
        cumulative = np.r_[0, np.cumsum(lengths)]
        midpoint = lengths.sum() / 2
        i = min(np.searchsorted(cumulative, midpoint, side="right") - 1, len(lengths) - 1)
        point = points[i] + (points[i + 1] - points[i]) * (midpoint - cumulative[i]) / lengths[i]
        if not (15 < point[0] < size - 15 and 15 < point[1] < size - 15):
            continue
        cell = tuple((point / 90).astype(int))
        if cell not in used_cells:
            used_cells.add(cell)
            suffix = " L ->" if tags.get("oneway") in ("yes", "1", "true") else " L total"
            if tags.get("oneway") == "-1":
                suffix = " L <-"
            # Arrow follows way order; lane total remains explicit on two-way roads.
            labels.append((point, f"{lanes}{suffix}"))

    fig = plt.figure(figsize=(size / 100, size / 100), dpi=100)
    ax = fig.add_axes((0, 0, 1, 1))
    with Image.open(root / "satellite_overlay_8192.png") as base:
        ax.imshow(np.asarray(base), extent=(0, size - 1, size - 1, 0), interpolation="nearest", alpha=.70)
    ax.set_facecolor("#101820")
    for lines, color, linewidth, style in (
        (unknown, "#141820", 2.3, "solid"),
        (unknown, "#ff9eeb", .85, "solid"),
        (edges, "#101820", 2.6, "solid"),
        (edges, "#38efff", 1.05, "solid"),
        (dividers, "#ffffff", .8, (0, (3, 3))),
        (tunnels, "#ffb84d", 1.2, (0, (4, 4))),
    ):
        ax.add_collection(LineCollection(lines, colors=color, linewidths=linewidth, linestyles=style))
    for point, text in labels:
        ax.text(*point, text.replace(" ->", " one-way").replace(" <-", " one-way"), color="white", fontsize=5.4,
                ha="center", va="center", bbox=dict(boxstyle="round,pad=.18", fc="#102331", ec="none", alpha=.9))
    ax.text(45, 60, "ROAD / LANE GUIDE | cyan: schematic road edges | white dashes: lane guides\n"
            "pink: lane count unknown | orange dashes: tunnel | L total: both directions combined\n"
            "3.25m assumed lane width. Junction markings / shoulders / turning pockets not surveyed.\n"
            "Roads: (c) OpenStreetMap contributors (ODbL) | Imagery: Esri / Vantor / Earthstar Geographics / GIS User Community",
            color="white", fontsize=8, va="top", bbox=dict(fc="#102331", ec="none", alpha=.9))
    ax.set_xlim(0, size - 1)
    ax.set_ylim(size - 1, 0)
    ax.set_axis_off()
    output = root / "road_lane_guide_8192.png"
    fig.savefig(output, dpi=100, facecolor="#101820")
    plt.close(fig)
    (root / "road_lane_guide_stats.json").write_text(json.dumps(counts, indent=2), encoding="utf-8")
    print(output, counts)


if __name__ == "__main__":
    main()
