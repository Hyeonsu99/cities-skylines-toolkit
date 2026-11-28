# -*- coding: utf-8 -*-
"""신탄진 단독주택 03 (2x2, T3: 흑회색 벽돌 2층 + 전면 흰 미장 외부계단 매스·막힌 난간벽 + 암회 기와 모임지붕)."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detached_core import PRESETS, build_and_export

if __name__ == "__main__":
    build_and_export(PRESETS["03"])
