# -*- coding: utf-8 -*-
"""신탄진 단독주택 02 (2x2, T1: 2층 암적갈 벽돌 모임지붕 마당형 + 좁은 전면 발코니 + 현관 차양 + 벽돌 담장·대문)."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detached_core import PRESETS, build_and_export

if __name__ == "__main__":
    build_and_export(PRESETS["02"])
