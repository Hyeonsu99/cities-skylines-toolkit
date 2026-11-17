"""Regenerate only satellite imagery; preserve terrain, resources and game settings."""
import argparse
import json
from pathlib import Path

from generate_sintanjin_jeonmin_heightmap import fetch_satellite_overlay


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map-dir", type=Path, default=Path(__file__).resolve().parents[1] / "sintanjin_jeonmin")
    parser.add_argument("--size", type=int, choices=(4096, 8192, 16384), default=8192)
    args = parser.parse_args()
    bounds = json.loads((args.map_dir / "map_metadata.json").read_text(encoding="utf-8"))["bounds"]
    output = args.map_dir / f"satellite_overlay_{args.size}.png"
    print(f"Fetching native-resolution imagery for {output}", flush=True)
    image = fetch_satellite_overlay(
        bounds["lat_north"], bounds["lat_south"], bounds["lon_west"], bounds["lon_east"],
        str(args.map_dir / "_imagery_cache"), out_size=args.size,
    )
    temporary = output.with_suffix(".tmp.png")
    image.save(temporary)
    temporary.replace(output)
    print(f"Saved {image.size}: {output}", flush=True)


if __name__ == "__main__":
    main()
