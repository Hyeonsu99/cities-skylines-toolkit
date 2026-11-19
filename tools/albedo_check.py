# -*- coding: utf-8 -*-
"""알베도 상한 검사 (cs2-kit 원본 check.py 무수정 — 로컬 확장).

각 output/<에셋>/ 의 BaseColor·MaskMap·Emissive 와 manifest.json 아틀라스 칸 위치로
비금속·비발광 칸의 평균 sRGB 를 재서, 게임 조명에서 날리거나 형광처럼 보일 칸을 경고한다.
경고만 하고 실패시키지 않는다. 기준값은 인게임 확인 뒤 조정하는 노브.

사용: python tools/albedo_check.py            (전체)
      python tools/albedo_check.py Korean     (이름 필터)
"""
import colorsys
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "cs2-kit" / "projects"

MAX_VALUE = 225        # sRGB 최대 채널 평균 상한 (순백 패널 날림)
MAX_SAT = 0.55         # HSV 채도 상한 (원색 도장·형광 녹색)
MIN_SAT_VALUE = 60     # 너무 어두운 칸은 채도 계산 제외
METAL_SKIP = 0.30      # MaskMap R 평균이 이보다 크면 금속 칸 -> 제외
EMIS_SKIP = 12         # Emissive 평균이 이보다 크면 발광 칸(창·간판·조명) -> 제외
IGNORE = ("window", "sign", "glass", "lamp", "led", "kx_grime", "drip", "rust", "weather")


def check_asset(out):
    man = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    name = man["asset"]
    cells = man.get("atlas", {}).get("cells", {})
    try:
        base = np.asarray(Image.open(out / f"{name}_BaseColor.png").convert("RGBA"), np.float32)
        mask = np.asarray(Image.open(out / f"{name}_MaskMap.png").convert("RGBA"), np.float32)
        emis = np.asarray(Image.open(out / f"{name}_Emissive.png").convert("RGB"), np.float32)
    except FileNotFoundError:
        return name, []
    warns = []
    for cname, c in cells.items():
        if any(k in cname.lower() for k in IGNORE) or "rect" not in c:
            continue
        x, y, w, h = c["rect"]
        sl = (slice(y, y + h), slice(x, x + w))
        a = base[sl][..., 3] > 128
        if a.sum() < 16:
            continue
        if mask[sl][..., 0][a].mean() / 255 > METAL_SKIP or emis[sl][a].mean() > EMIS_SKIP:
            continue
        rgb = base[sl][..., :3][a].mean(0)
        hh, ss, vv = colorsys.rgb_to_hsv(*(rgb / 255))
        if rgb.max() > MAX_VALUE:
            warns.append(f"{cname}: 밝기 {rgb.max():.0f} > {MAX_VALUE} (평균 sRGB {np.round(rgb).astype(int).tolist()})")
        if vv * 255 > MIN_SAT_VALUE and ss > MAX_SAT:
            warns.append(f"{cname}: 채도 {ss:.2f} > {MAX_SAT} (평균 sRGB {np.round(rgb).astype(int).tolist()})")
    return name, warns


def run(name_filter=""):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    total = 0
    for out in sorted(SRC.glob("*/output/*/")):
        if not (out / "manifest.json").exists() or name_filter not in out.name:
            continue
        name, warns = check_asset(out)
        total += len(warns)
        for w in warns:
            print(f"  ! ALBEDO {name}  {w}")
    print(f"[albedo] 경고 {total}건 (기준: 밝기 {MAX_VALUE}, 채도 {MAX_SAT}; 금속·발광 칸 제외)")
    return total


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "")
