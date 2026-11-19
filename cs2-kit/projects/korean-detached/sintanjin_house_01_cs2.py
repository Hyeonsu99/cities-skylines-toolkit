# -*- coding: utf-8 -*-
"""신탄진 단독주택 01 (2x3, T2: 고동 벽돌 1층 앞 볼륨 + 옥상 테라스 + 폴리카보네이트 차양 + 적갈 기와 모임지붕)."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detached_core import PRESETS, build_and_export

if __name__ == "__main__":
    build_and_export(PRESETS["01"])
