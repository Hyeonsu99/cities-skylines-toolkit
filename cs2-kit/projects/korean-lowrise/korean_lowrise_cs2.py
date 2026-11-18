# -*- coding: utf-8 -*-
"""A형 2층 벽돌 양옥 시제품, 2x2 lot."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from house_core import PRESETS, build_and_export

if __name__ == "__main__":
    build_and_export(PRESETS["a01"])
