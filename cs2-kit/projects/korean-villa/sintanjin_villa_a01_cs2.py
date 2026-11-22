# -*- coding: utf-8 -*-
"""신탄진형 다세대 빌라 A01 (2x3, 적갈 벽돌 + 흰 띠·모서리 + 1층 필로티 3대 주차, 4층)."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from villa_core import PRESETS, build_and_export

if __name__ == "__main__":
    build_and_export(PRESETS["A01"])
