# -*- coding: utf-8 -*-
"""한국형 근린상가 01 (2x2, 모퉁이 3층 석재 + 박공 파라펫 + 옥탑, 1층 노란 간판·파란 차양, 2층 유리 글자)."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shop_core import PRESETS, build_and_export

if __name__ == "__main__":
    build_and_export(PRESETS["01"])
