"""Run: python maps/tools/test_road_lane_guide.py"""
import numpy as np
from render_road_lane_guide import lane_count, offset_line

assert lane_count({"lanes": "4"}) == 4
for value in ("", "0", "3;4", "2.5", "-1", "99", "４"):
    assert lane_count({"lanes": value}) is None
np.testing.assert_allclose(offset_line([(0, 0), (10, 0)], 2), [(0, 2), (10, 2)])
np.testing.assert_allclose(offset_line([(0, 0), (10, 0), (10, 10)], 2), [(0, 2), (8, 2), (8, 10)])
try:
    offset_line([(0, 0), (0, 0)], 1)
except ValueError:
    pass
else:
    raise AssertionError("Duplicate points must fail")
print("Lane parsing and road offsets: PASS")
