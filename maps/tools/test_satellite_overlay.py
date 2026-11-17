"""Offline check: python maps/tools/test_satellite_overlay.py"""
import io
import tempfile
from unittest.mock import patch

import numpy as np
from PIL import Image

from generate_sintanjin_jeonmin_heightmap import deg2num_f, fetch_satellite_overlay


def check():
    # A continuous coordinate gradient across tile seams catches flips and bad crops.
    def tile(url, *_args, **_kwargs):
        zoom, y, x = map(int, url.split("/")[-3:])
        yy, xx = np.mgrid[:256, :256]
        rgb = np.zeros((256, 256, 3), dtype=np.uint8)
        rgb[:, :, 0] = (x * 256 + xx) % 256
        rgb[:, :, 1] = (y * 256 + yy) % 256
        buffer = io.BytesIO()
        Image.fromarray(rgb).save(buffer, format="PNG")
        return buffer.getvalue()

    bounds = (36.421, 36.420, 127.404, 127.405)
    with tempfile.TemporaryDirectory() as cache, patch(
        "generate_sintanjin_jeonmin_heightmap.fetch_url_cached", side_effect=tile
    ) as fetch:
        image = fetch_satellite_overlay(*bounds, cache, out_size=32)
        zoom = int(fetch.call_args.args[0].split("/")[-3])
        assert zoom > 15, "Small areas need higher source zoom, too"
        assert image.size == (32, 32)
        pixels = np.asarray(image)
        for row, col in ((0, 0), (16, 16), (31, 31)):
            lat = bounds[0] + (bounds[1] - bounds[0]) * row / 31
            lon = bounds[2] + (bounds[3] - bounds[2]) * col / 31
            x, y = deg2num_f(lat, lon, zoom)
            expected = np.round([x * 256 % 256, y * 256 % 256])
            assert np.max(np.abs(pixels[row, col, :2].astype(float) - expected)) <= 1
        for size in (0, 16385):
            try:
                fetch_satellite_overlay(*bounds, cache, out_size=size)
            except ValueError:
                pass
            else:
                raise AssertionError("Invalid sizes must fail before downloading")
    print("Satellite sampling, orientation, native zoom and validation: PASS")


if __name__ == "__main__":
    check()
