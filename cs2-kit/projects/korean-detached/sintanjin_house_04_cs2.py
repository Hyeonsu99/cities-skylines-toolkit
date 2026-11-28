# -*- coding: utf-8 -*-
"""신탄진 단독주택 04 (2x2, T4: 1층 근린상가 2곳 + 2층 적갈 벽돌 주거 + 평지붕 파라펫·옥상 물탱크)."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detached_core import PRESETS, build_and_export

if __name__ == "__main__":
    build_and_export(PRESETS["04"])
