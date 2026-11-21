"""Offline regression: python maps/tools/test_resources.py"""
from pathlib import Path
import struct
import tempfile

import numpy as np
from PIL import Image

import generate_sintanjin_jeonmin_heightmap as g


def read_pack(path):
    assert path.stat().st_size == 256 * 256 * 5 * 2
    data = np.fromfile(path, dtype="<u2").reshape(256, 256, 5)
    assert data.max() <= 10000
    return data[::-1]  # Geographic image order: north first.


def check():
    bounds = g.compute_bounds(g.CENTER_LAT, g.CENTER_LON, g.REAL_SIDE_M)
    n, s, w, e = bounds
    size = 512
    elev = np.full((size, size), 35, dtype=np.float32)
    elev[:, -80:] = 150  # Eastern mineral/forestry ridge.
    water = np.zeros((size, size), dtype=bool)
    water[180:200] = True
    masks = {name: Image.new("L", (size, size)) for name in ("urban", "highways", "forest")}
    with tempfile.TemporaryDirectory() as tmp:
        fields, _ = g.generate_resources(elev, water, masks, *bounds, tmp)
        data = read_pack(Path(tmp) / "sintanjin_resources_256.bin")
        for key, name in g.RESOURCE_HEIGHTMAPS.items():
            path = Path(tmp) / f"Sintanjin_Jeonmin_145x_{name}_16bit.png"
            assert path.read_bytes()[24:26] == bytes((16, 0)), "PNG depth/color"
            with Image.open(path) as im:
                assert im.size == (size, size)
                pixels = np.array(im, dtype=np.float32) / 65535
            assert np.abs(pixels - fields[key]).max() < 1 / 65535, "PNG orientation/precision"

        for channel, key in ((0, "fertile"), (1, "ore"), (2, "oil"), (4, "underground_water")):
            field = fields["resource_" + key]
            assert np.isfinite(field).all() and field.min() >= 0 and field.max() <= 1
            assert not field[water].any(), key + " underwater"
            # Compare north/south landmarks to catch a reversed binary or channel swap.
            for row, col in ((18, 172), (60, 120), (200, 150)):
                expected = field[row * 2:row * 2 + 2, col * 2:col * 2 + 2].mean() * 10000
                assert abs(float(data[row, col, channel]) - expected) < 450, key
        assert data[94, 20, 3] == 7200 and data[20, 20, 3] == 0
        lat, lon = g.START_AQUIFER[1:3]
        tile_col = int(((lon - g.CENTER_LON) * g.M_PER_DEG_LON * g.SCALE_FACTOR
                        + g.CS2_SIDE_M / 2) / (g.CS2_SIDE_M / 23))
        tile_row = int(((lat - g.CENTER_LAT) * g.M_PER_DEG_LAT * g.SCALE_FACTOR
                        + g.CS2_SIDE_M / 2) / (g.CS2_SIDE_M / 23))
        assert g.START_TILE_COLS[0] <= tile_col <= g.START_TILE_COLS[1]
        assert g.START_TILE_ROWS[0] <= tile_row <= g.START_TILE_ROWS[1]
        assert lat < 36.445 and lon > 127.425, "Reserve returned to Seokbong"
        row, col = round((n - lat) / (n - s) * 255), round((lon - w) / (e - w) * 255)
        assert data[row, col, 4] > 8500, "Starting aquifer lost to heuristics"
        for i, j in ((0, 1), (0, 2), (1, 2)):
            assert not ((data[:, :, i] > 3000) & (data[:, :, j] > 3000)).any()
        extraction = np.maximum(fields["resource_ore"], fields["resource_oil"])
        assert not fields["resource_forest"][extraction >= 0.5].any()

    pack = Path(__file__).resolve().parents[1] / "sintanjin_jeonmin"
    data = read_pack(pack / "sintanjin_resources_256.bin")
    assert data[row, col, 4] > 7000, "Shipped pack lacks starting groundwater"
    assert data[row, col, 1:3].max() == 0, "Extraction overlaps starting water"
    for i in range(5):
        assert (data[:, :, i] > 2000).sum() > 100, "Missing resource channel"
    for i, j in ((0, 1), (0, 2), (1, 2), (1, 4), (2, 4)):
        assert not ((data[:, :, i] > 3000) & (data[:, :, j] > 3000)).any()
    ntiles = 23
    ys, xs = np.indices((256, 256))
    tile_cols = (xs + 0.5) / 256 * ntiles
    tile_rows = (255.5 - ys) / 256 * ntiles
    inside = ((tile_cols >= g.START_TILE_COLS[0]) & (tile_cols < g.START_TILE_COLS[1] + 1)
              & (tile_rows >= g.START_TILE_ROWS[0]) & (tile_rows < g.START_TILE_ROWS[1] + 1))
    assert (data[:, :, 4][inside] > 7000).sum() >= 4, "No usable groundwater in start area"
    ref = pack / "heightmap_cs2_4096_1024m.png"
    with Image.open(ref) as im:
        ref_size = im.size
    for key, name in g.RESOURCE_HEIGHTMAPS.items():
        path = pack / f"Sintanjin_Jeonmin_145x_{name}_16bit.png"
        assert path.read_bytes()[24:26] == bytes((16, 0))
        with Image.open(path) as im:
            assert im.size == ref_size
            pix = np.array(im)
        assert pix.max() > 0
        if key == "resource_underground_water":
            pr = round((n - lat) / (n - s) * (ref_size[1] - 1))
            pc = round((lon - w) / (e - w) * (ref_size[0] - 1))
            assert pix[pr, pc] > 0.7 * 65535, "Heightmap groundwater missing/reversed"
    raw = (pack / "sintanjin_trees.bin").read_bytes()
    assert raw[:4] == b"SJT1"
    count, = struct.unpack_from("<I", raw, 4)
    assert len(raw) == 8 + count * 12 and 1000 < count < 100000
    trees = np.frombuffer(raw, offset=8, dtype=[("x", "<f4"), ("z", "<f4"), ("flags", "u1", (4,))])
    assert np.isfinite(trees["x"]).all() and np.isfinite(trees["z"]).all()
    assert np.abs(trees["x"]).max() < g.CS2_SIDE_M / 2
    assert np.abs(trees["z"]).max() < g.CS2_SIDE_M / 2
    rows = np.clip(((0.5 - trees["z"] / g.CS2_SIDE_M) * 256).astype(int), 0, 255)
    cols = np.clip(((0.5 + trees["x"] / g.CS2_SIDE_M) * 256).astype(int), 0, 255)
    assert data[rows, cols, 1:3].max() < 6000, "Trees inside extraction cores"
    print("Resource layout, starting groundwater, binary channels/orientation: PASS")


if __name__ == "__main__":
    check()
