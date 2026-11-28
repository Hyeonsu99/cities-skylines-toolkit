# -*- coding: utf-8 -*-
"""신탄진형 다세대 빌라 A형(적갈 벽돌 + 흰 띠·모서리 + 1층 필로티, 4층) 생성기 코어.

근거:
- STYLE_BRIEF.md 5.3 프리셋 A, 2장 치수, 3장 색, 4장 디테일
- work/roadview_extra/a01~a06 (덕암동 빌라 골목 네이버 거리뷰 2026-10-07, SOURCES.md)
- reports/korean_housing_lessons.md 25항

재사용: korean-detached/detached_core.py 의 칠 함수·창호 벽(add_recessed_wall)·우수관·실외기·난간 헬퍼.
원본 키트(cs2kit.py, tools/)와 detached_core.py 는 수정하지 않는다.
"""
from dataclasses import dataclass
import math
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / "korean-detached"))
import cs2kit as K
import detached_core as DC
from local import kitext as KX


@dataclass(frozen=True)
class VillaSpec:
    name: str = "SintanjinVillaA01"
    lot: tuple = (2, 3)            # 16 x 24 m (STYLE_BRIEF 5.1 핵심 lot)
    front_yard: float = 2.0
    width: float = 10.6            # 정면 폭 # estimated (a01: 정면 3칸, 브리프 소형 9.5~중형 12.5)
    depth: float = 12.4            # 깊이 # estimated (a02 측면 4칸, 브리프 11~14)
    z_pil: float = 2.45            # 필로티 유효 높이 (브리프 2.40, a01 흰 기둥)
    z_f2: float = 3.00             # 2층 바닥 (필로티 층고 3.0)
    floor_h: float = 2.80          # 2~4층 층고 (브리프 2.80, a02 벽돌 줄 수)
    n_upper: int = 3               # 2~4층
    road_name: str = "신탄골목길"   # 가상 도로명 (규칙 20)
    road_no: str = "27"
    seed: int = 3


PRESETS = {"A01": VillaSpec()}

WALL_T = 0.22
BAND_O = 0.06                       # 흰 슬래브 띠 돌출 (a02)
CORNER_O, CORNER_W = 0.03, 0.30     # 흰 모서리 띠 (브리프 프리셋 A) # estimated
EAVE_O, EAVE_IN, EAVE_RISE = 0.45, 0.15, 0.70  # 갈색 경사 처마 (a01·a02) # estimated


# ---------------------------------------------------------------------------
# 아틀라스
# ---------------------------------------------------------------------------
def _brick_painter(seed, mortar_rgb, course_h=0.075, brick_w=0.23):
    """적갈·암자색 혼합 점토벽돌 (a01/a02: 줄마다 진한 벽돌이 섞인 다색 벽돌) + 밝은 회색 줄눈."""
    def painter(ctx):
        x, z = ctx.meters()
        row = np.floor(z / course_h)
        shift = (row % 2) * (brick_w * 0.5)
        col = np.floor((x + shift) / brick_w)
        joint = ((z % course_h) < 0.011) | (((x + shift) % brick_w) < 0.010)
        h1 = np.sin(row * 12.9898 + col * 78.233 + seed * 37.0) * 43758.5453
        r = h1 - np.floor(h1)
        h2 = np.sin(row * 39.346 + col * 11.135 + seed * 19.0) * 24634.6345
        r2 = (h2 - np.floor(h2)) - 0.5
        base = ctx.rgb.copy()
        tone = np.where(r < 0.28, 0.70, np.where(r > 0.86, 1.14, 1.0 + (r - 0.57) * 0.16))
        dark = r < 0.28
        base[..., 0] *= tone + r2 * 0.05
        base[..., 1] *= tone
        base[..., 2] *= tone * np.where(dark, 1.10, 1.0)
        ctx.rgb[...] = np.clip(base, 26, 210)
        ctx.rgb[joint] = mortar_rgb
        ctx.height[joint] -= 0.36
        ctx.grain(amp=3.6, scale_px=2, height=0.10, seed=101 + seed * 5)
        v = DC._var(ctx, scale_px=8, seed=107 + seed * 3)
        ctx.gloss = np.clip(np.where(joint, 0.14 + 0.02 * v, 0.24 + 0.04 * v), 0.10, 0.34)
    return painter


def _plate_painter(name, draw):
    """PIL 로 그린 판(번호판·충돌방지 띠)을 칸 전체에 채운다. 캐시는 이 프로젝트 work/_sign_cache."""
    def painter(ctx):
        cache = HERE / "work" / "_sign_cache" / f"{name}_{ctx.w}x{ctx.h}.npz"
        try:
            from PIL import Image
            rgb = np.asarray(draw(ctx.w * 4, ctx.h * 4).resize((ctx.w, ctx.h), Image.LANCZOS))
            cache.parent.mkdir(parents=True, exist_ok=True)
            np.savez(cache, rgb=rgb)
        except (ImportError, OSError):
            rgb = np.load(cache)["rgb"]
        ctx.rgb[...] = rgb
        ctx.grain(amp=1.2, scale_px=2, height=0.02, seed=251)
        ctx.gloss = np.clip(0.46 + 0.03 * DC._var(ctx, 8, 257), 0.38, 0.54)
    return painter


def _draw_address(road_name, road_no):
    def draw(W, H):
        from PIL import Image, ImageDraw, ImageFont
        navy, white = (42, 66, 108), (214, 216, 220)
        im = Image.new("RGB", (W, H), navy)
        d = ImageDraw.Draw(im)
        m = max(4, int(min(W, H) * 0.07))
        d.rectangle([m, m, W - 1 - m, H - 1 - m], outline=white, width=max(3, int(H * 0.038)))
        d.text((W * 0.5, H * 0.30), road_name, font=ImageFont.truetype("C:/Windows/Fonts/H2GTRE.TTF", int(H * 0.22)),
               fill=white, anchor="mm")
        d.text((W * 0.5, H * 0.67), road_no, font=ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(H * 0.44)),
               fill=white, anchor="mm")
        return im
    return draw


def _draw_bumper(W, H):
    """필로티 기둥 황·흑 사선 충돌방지 띠 (브리프 4장). 채도 억제한 바랜 노랑."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (W, H), (44, 44, 46))
    d = ImageDraw.Draw(im)
    step = W // 3
    for k in range(-6, 12):
        x = k * step
        d.polygon([(x, H), (x + step // 2, H), (x + step // 2 + H, 0), (x + H, 0)], fill=(190, 166, 84))
    return im


def _roof_waterproof_painter(seed):
    """옥상 우레탄 방수 도막 (체크무늬 타일 이음선 없이 완만한 저주파 농담 + 미세 롤러 질감)."""
    def painter(ctx):
        v1 = DC._var(ctx, scale_px=48, seed=401 + seed)
        v2 = DC._var(ctx, scale_px=16, seed=409 + seed)
        tone = 1.0 + 0.045 * v1 + 0.025 * v2
        ctx.rgb[...] = np.clip(ctx.rgb * tone[..., None], 48, 198)
        ctx.grain(amp=2.6, scale_px=3, height=0.05, seed=419 + seed)
        ctx.gloss = np.clip(0.28 + 0.04 * v1 + 0.02 * v2, 0.20, 0.38)
    return painter


def _draw_intercom(W, H):
    """공동현관 로비폰/인터폰 전면 (카메라·화면·스피커·3x4 키패드·호출 버튼)."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (W, H), (164, 168, 172))
    d = ImageDraw.Draw(im)
    m = max(4, int(W * 0.06))
    # 내측 다크 페이스플레이트
    d.rectangle([m, m, W - 1 - m, H - 1 - m], fill=(50, 54, 58), outline=(92, 96, 102), width=max(2, W // 48))
    # 상단 화면 + 카메라 렌즈
    sx0, sx1 = int(W * 0.14), int(W * 0.68)
    sy0, sy1 = int(H * 0.12), int(H * 0.34)
    d.rectangle([sx0, sy0, sx1, sy1], fill=(42, 54, 68), outline=(120, 126, 134), width=max(2, W // 64))
    d.rectangle([sx0 + 6, sy0 + 6, int(sx0 + (sx1 - sx0) * 0.45), sy0 + int((sy1 - sy0) * 0.35)], fill=(86, 104, 122))
    cx, cy, cr = int(W * 0.80), int(H * 0.21), max(4, int(W * 0.065))
    d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(28, 30, 34), outline=(146, 150, 154), width=max(2, W // 64))
    d.ellipse([cx - cr // 2, cy - cr // 2, cx + cr // 2, cy + cr // 2], fill=(56, 72, 92))
    # 스피커 슬롯
    for k in range(4):
        yk = int(H * (0.39 + k * 0.028))
        d.line([(int(W * 0.16), yk), (int(W * 0.84), yk)], fill=(30, 32, 36), width=max(2, H // 80))
    # 3x4 숫자 키패드
    for r in range(4):
        for c in range(3):
            bx0 = int(W * (0.16 + c * 0.24))
            by0 = int(H * (0.53 + r * 0.085))
            bx1 = bx0 + int(W * 0.18)
            by1 = by0 + int(H * 0.062)
            d.rectangle([bx0, by0, bx1, by1], fill=(188, 190, 194), outline=(74, 78, 82), width=max(1, W // 96))
    # 하단 호출·경비 버튼 (채도 억제)
    d.rectangle([int(W * 0.16), int(H * 0.87), int(W * 0.48), int(H * 0.93)], fill=(76, 104, 138))
    d.rectangle([int(W * 0.52), int(H * 0.87), int(W * 0.84), int(H * 0.93)], fill=(78, 124, 96))
    return im


def build_atlas(spec: VillaSpec, *, charcoal=False, wall=None) -> K.Atlas:
    """wall: None(A 적갈 벽돌) | 'stucco_white'(C 흰 미장) | 'brick_brown'(D 고동 벽돌 + 연베이지 미장)."""
    s = spec.seed
    a = K.Atlas(size=2048, pad=12)
    if wall == "stucco_white":
        # 브리프 3.1 흰 미장 PBR 권장 (210,208,204) → V≤215 클램프 내 (206,204,200)
        a.add("wall_main", color=(206, 204, 200), ctrl=(0, 255, 0), px=512, tile=(2.4, 2.4),
              gloss=0.24, painter=DC._make_plaster_painter(s + 5))
    else:
        # 벽돌: A 진적갈 (128,92,86) / B 차콜 (96,98,100) / D 고동 (142,118,104). 줄눈 밝은 회색 시멘트 (규칙 18)
        brick = (96, 98, 100) if charcoal else (142, 118, 104) if wall == "brick_brown" else (128, 92, 86)
        a.add("wall_main", color=brick, ctrl=(0, 255, 0), px=512, tile=(2.3, 2.4),
              gloss=0.24, painter=_brick_painter(s, (188, 186, 185)))
    if wall:
        # 밝은 화강석(포천석) 기단·기둥 (브리프 3.1 (178,176,178))
        a.add("granite_light", color=(178, 176, 178), px=256, tile=(1.2, 1.2), gloss=0.40, painter=KX.stone_trim(s + 137))
    if wall == "brick_brown":
        a.add("plaster_beige", color=(196, 184, 168), ctrl=(0, 255, 0), px=384, tile=(2.4, 2.4),
              gloss=0.24, painter=DC._make_plaster_painter(s + 9))
    a.add("plaster_white", color=(212, 211, 208), ctrl=(0, 255, 0), px=384, tile=(2.4, 2.4),
          gloss=0.24, painter=DC._make_plaster_painter(s + 11))
    a.add("concrete_light", color=(178, 180, 183), px=256, tile=(2.4, 2.4),
          gloss=0.24, painter=DC._make_concrete_plinth_painter(s + 23))
    # 갈색 경사 처마 (a01·a02 상단 갈색 기와형 금속 처마) # estimated 재질
    a.add("roof_shingle", color=(104, 76, 64), ctrl=(255, 0, 0), px=384, tile=(1.76, 1.68),
          gloss=0.36, painter=DC._make_clay_tile_painter(s + 31))
    a.add("roof_trim", color=(104, 76, 64), ctrl=(255, 0, 0), px=128, gloss=0.38,
          painter=DC._solid(3.0, 0.30, 0.44, s + 33))
    a.add("roof_deck", color=(116, 132, 120), px=256, tile=(4.8, 4.8), gloss=0.28,
          painter=_roof_waterproof_painter(s + 47))          # 옥상 우레탄 방수 녹회 # estimated
    win_col = (76, 98, 110)
    a.add("window", color=win_col, px=384, gloss=0.82, emissive=(255, 220, 174),
          painter=DC._make_window_painter(s + 53))
    a.add("window_backing", color=win_col, px=32, gloss=0.78)
    a.add("sash", color=(212, 212, 214), px=128, gloss=0.52, painter=DC._solid(1.8, 0.46, 0.58, s + 59))
    a.add("sash_dark", color=(58, 62, 66), px=128, gloss=0.48, painter=DC._solid(2.0, 0.42, 0.54, s + 63))
    a.add("stainless", color=(172, 174, 178), px=128, metal=0.65, gloss=0.62,
          painter=DC._solid(2.0, 0.54, 0.68, s + 67))
    a.add("iron_dark", color=(56, 58, 62), px=128, metal=0.45, gloss=0.42,
          painter=DC._solid(2.4, 0.34, 0.48, s + 71))
    a.add("door_wood", color=(118, 122, 126), px=128, gloss=0.40,
          painter=DC._solid(2.2, 0.34, 0.46, s + 83))      # 회색 철제 방화문
    a.add("equip_gray", color=(184, 186, 184), px=128, gloss=0.36, painter=DC._solid(2.2, 0.30, 0.42, s + 89))
    a.add("louver", color=(162, 166, 164), px=128, gloss=0.38, painter=DC._make_louver_painter(s + 97))
    a.add("pipe_white", color=(196, 198, 198), px=64, gloss=0.48, painter=DC._solid(1.5, 0.42, 0.54, s + 103))
    # 도시가스 배관 (a01·a02 벽면 적색 도장 배관) — 채도 0.50 로 억제
    a.add("pipe_gas", color=(150, 88, 75), px=64, gloss=0.44, painter=DC._solid(1.5, 0.38, 0.50, s + 105))
    a.add("stopper", color=(150, 136, 92), px=64, gloss=0.30, painter=DC._solid(2.0, 0.24, 0.36, s + 109))
    a.add("lamp", color=(244, 224, 182), emissive=(255, 224, 162), px=32, gloss=0.62,
          painter=DC._solid(1.0, 0.56, 0.66, s + 107))
    a.add("address", px=256, gloss=0.48,
          painter=_plate_painter(f"addr_{spec.road_name}_{spec.road_no}", _draw_address(spec.road_name, spec.road_no)))
    a.add("bumper", px=128, gloss=0.46, painter=_plate_painter("bumper", _draw_bumper))
    a.add("intercom", px=128, gloss=0.50, painter=_plate_painter("intercom", _draw_intercom))
    # 문 품질 (2026-11-24 인게임 피드백): 아노다이징 다크 알루미늄 문틀과 헤어라인 샴페인 문선을 창틀·철물과 구분
    a.add("alu_dark", color=(64, 63, 61), px=128, metal=0.55, gloss=0.58,
          painter=DC._solid(1.6, 0.50, 0.64, s + 141))
    a.add("door_trim", color=(150, 146, 138), px=128, metal=0.60, gloss=0.56,
          painter=DC._solid(1.8, 0.48, 0.62, s + 143))
    if charcoal:
        a.add("granite", color=(54, 56, 59), px=256, tile=(1.2, 1.2),
              gloss=0.46, painter=KX.stone_trim(s + 131))
    return a


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------
def _skip_face(axis, side):
    if axis == "y":
        return "front" if side < 0 else "back"
    return "left" if side < 0 else "right"


def decal_plate(mb, axis, c, side, a0, a1, z0, z1, t, full_reg, edge_reg="iron_dark", o0=0.0):
    """얇은 3D 판 + 앞면 칸 전체 UV (번호판·충돌방지 띠·인터폰, 규칙 12)."""
    K.axbox(mb, axis, c, side, a0, a1, o0, o0 + t, z0, z1, edge_reg, skip=(_skip_face(axis, side),))
    mb.quad(K.face_pts(axis, c + side * (o0 + t), side, a0, a1, z0, z1), mb.atlas.uv_full(full_reg), full_reg)


def ensure_lit_windows(wins, indices, win_seed):
    """지정 창 인덱스들이 야간 점등 셀에 배정되도록 (floor, unit) 조정 (다른 창 셀 이동 방지)."""
    if not indices or not wins.items:
        return
    cells = K.REF_GRID * K.REF_GRID
    units = max(w["unit"] for w in wins.items) + 1
    stride = 7 if math.gcd(7, cells) == 1 else 11
    lit_cells = [(k * 3 + win_seed) % cells for k in range(14)]
    # 층별 밝기 변화가 자연스럽도록 cell % 3 이 골고루 섞인 후보 우선
    ordered = sorted(dict.fromkeys(lit_cells), key=lambda c: (c % 3, c))
    for n, idx in enumerate(indices):
        if not (0 <= idx < len(wins.items)):
            continue
        target = ordered[(n * 5) % len(ordered)]
        found = None
        for f in range(1, 26):
            for u in range(units):
                if ((f * units + u) * stride) % cells == target:
                    found = (f, u)
                    break
            if found:
                break
        if found:
            wins.items[idx]["floor"], wins.items[idx]["unit"] = found


def add_intercom(mb, axis, c, side, a0, a1, z0, z1):
    """공동현관 인터폰: 다크 하우징 + PIL 로비폰 전면판 + 상단 비막이 후드."""
    decal_plate(mb, axis, c, side, a0, a1, z0, z1, 0.042, "intercom", edge_reg="iron_dark")
    # 상단 비막이 후드
    K.axbox(mb, axis, c, side, a0 - 0.012, a1 + 0.012, 0.0, 0.072, z1, z1 + 0.014, "iron_dark")


def add_steel_door_details(mb, axis, c, side, a0, a1, z0, z1, *,
                           leaf_o=-0.10, fw=0.06, add_threshold=True, handle_right=True):
    """철제 방화문/보조문 디테일: 상·하 패널 요철, 킥플레이트, 레버 손잡이, 도어클로저, 문턱."""
    la0, la1 = a0 + fw, a1 - fw
    lz1 = z1 - fw
    w = la1 - la0
    h = lz1 - z0
    if w < 0.35 or h < 1.2:
        return
    # 1) 하부 킥플레이트
    K.axbox(mb, axis, c, side, la0 + 0.015, la1 - 0.015, leaf_o + 0.002, leaf_o + 0.010,
            z0 + 0.015, z0 + 0.14, "iron_dark")
    # 2) 상·하 패널 요철 (이중 단차 몰딩으로 근접 입체감 확보)
    pm = min(0.11, w * 0.15)
    for pz0, pz1 in ((z0 + 0.22, z0 + h * 0.45), (z0 + h * 0.53, lz1 - 0.18)):
        if pz1 - pz0 > 0.20:
            K.axbox(mb, axis, c, side, la0 + pm, la1 - pm, leaf_o + 0.002, leaf_o + 0.014,
                    pz0, pz1, "sash_dark")
            K.axbox(mb, axis, c, side, la0 + pm + 0.028, la1 - pm - 0.028, leaf_o + 0.014, leaf_o + 0.024,
                    pz0 + 0.028, pz1 - 0.028, "door_wood")
    # 3) 스테인리스 레버 손잡이 + 자물쇠 백플레이트
    hx = (la1 - 0.095) if handle_right else (la0 + 0.095)
    hz = z0 + 0.96
    K.axbox(mb, axis, c, side, hx - 0.024, hx + 0.024, leaf_o + 0.002, leaf_o + 0.014,
            hz - 0.085, hz + 0.055, "iron_dark")
    K.axbox(mb, axis, c, side, hx - 0.011, hx + 0.011, leaf_o + 0.014, leaf_o + 0.052,
            hz - 0.011, hz + 0.011, "stainless")
    lx0, lx1 = (hx - 0.115, hx + 0.012) if handle_right else (hx - 0.012, hx + 0.115)
    K.axbox(mb, axis, c, side, lx0, lx1, leaf_o + 0.044, leaf_o + 0.062,
            hz - 0.011, hz + 0.011, "stainless")
    # 4) 상부 도어클로저 몸체 + 링크 암
    cx0, cx1 = (la0 + 0.08, la0 + 0.30) if handle_right else (la1 - 0.30, la1 - 0.08)
    K.axbox(mb, axis, c, side, cx0, cx1, leaf_o + 0.002, leaf_o + 0.042,
            lz1 - 0.095, lz1 - 0.025, "iron_dark")
    ax0, ax1 = (cx1 - 0.02, cx1 + 0.12) if handle_right else (cx0 - 0.12, cx0 + 0.02)
    K.axbox(mb, axis, c, side, ax0, ax1, leaf_o + 0.028, leaf_o + 0.046,
            lz1 - 0.052, lz1 - 0.004, "iron_dark")
    # 5) 콘크리트 문턱 (벽 외면 앞쪽 2 mm 이격 -> 겹침 0)
    if add_threshold:
        K.axbox(mb, axis, c, side, a0 - 0.03, a1 + 0.03, 0.002, 0.11, 0.0, max(0.05, z0 + 0.02),
                "concrete_light", skip=("bottom",))


def wall_with_doors(mb, wins, axis, c, side, lo, hi, z_bot, z_top, reg, holes, stage, seed, doors, **kw):
    """벽에 문 개구부만 뚫는다(문 부재는 add_glass_entry_door/add_steel_door 로 따로 설치).
    doors: [(a0, a1, z0, z1)]. 창(holes)은 문 사이 벽 조각에 그대로 나눠 넣는다."""
    rh = DC.add_recessed_wall
    pos = lo
    for k, (a0, a1, dz0, dz1) in enumerate(sorted(doors)):
        if a0 - pos > 1e-4:
            rh(mb, wins, axis, c, side, pos, a0, z_bot, z_top, reg,
               [h for h in holes if h[0] >= pos and h[1] <= a0], stage, seed + k * 7, **kw)
        if dz0 > z_bot + 1e-4:
            rh(mb, wins, axis, c, side, a0, a1, z_bot, dz0, reg, [], stage, seed + k * 7 + 1, **kw)
        if dz1 < z_top - 1e-4:
            rh(mb, wins, axis, c, side, a0, a1, dz1, z_top, reg,
               [h for h in holes if h[0] >= a0 and h[1] <= a1 and h[2] >= dz1], stage, seed + k * 7 + 2, **kw)
        pos = a1
    if hi - pos > 1e-4:
        rh(mb, wins, axis, c, side, pos, hi, z_bot, z_top, reg,
           [h for h in holes if h[0] >= pos], stage, seed + 97, **kw)


def add_door_casing(mb, axis, c, side, a0, a1, z0, z1, stage, reg="door_trim", w=0.09, head_h=0.12):
    """문선(양옆 0.03 돌출) + 인방(상부 0.045 돌출, 문선을 덮음) + 개구부 옆면 리빌. 벽 바깥면에 붙인다."""
    if stage == 2:
        return
    zb = 0.0 if z0 < 0.06 else z0                  # 지면 문은 문선을 바닥까지 (밑면 생략)
    sk = ("top", "bottom") if zb <= 0.001 else ("top",)
    K.axbox(mb, axis, c, side, a0 - w, a0, 0.0, 0.030, zb, z1, reg, skip=sk)
    K.axbox(mb, axis, c, side, a1, a1 + w, 0.0, 0.030, zb, z1, reg, skip=sk)
    K.axbox(mb, axis, c, side, a0 - w - 0.02, a1 + w + 0.02, 0.0, 0.045, z1, z1 + head_h, reg)
    if stage == 0:
        KX.paint_reveal(mb, axis, c, side, a0, a1, z0, z1, 0.045, reg, inset=0.002, sill=False, head=True)


def add_glass_entry_door(mb, wins, axis, c, side, a0, a1, z0, z1, stage, unit=0, lit=None,
                         frame_reg="alu_dark", casing_reg="door_trim", casing=True):
    """공동현관 알루미늄 양개(폭 1.1 m 미만은 외짝) 유리문. 벽 개구부 a0..a1, z0..z1 안에 설치.

    외곽 문틀 65 mm(아노다이징 다크) → 문짝 울거미(선대 60, 상대 70, 하대 170 + 스텐 킥플레이트)
    → 유리 1장/짝(WindowSet, 분할 없음) → 스텐 세로 손잡이(받침 2개) · 도어체크 · 잠금장치
    → 높은 개구부는 상부 고정창(트랜섬). 외부는 문선·인방·리빌. 겹침 면 0 (맞대기·이격만).
    """
    if stage == 2:
        mb.rect(K.face_pts(axis, c + side * 0.002, side, a0, a1, z0, z1), "window_backing")
        return
    fw = 0.065
    F0, F1 = -0.175, -0.045
    h = z1 - z0
    zt = min(z0 + 2.08, z1 - 0.30) if h >= 2.35 else None
    lz1 = zt if zt else z1 - fw
    # 외곽 문틀 (상·좌·우) + 스텐 문턱
    K.axbox(mb, axis, c, side, a0, a1, F0, F1, z1 - fw, z1, frame_reg)
    K.axbox(mb, axis, c, side, a0, a0 + fw, F0, F1, z0, z1 - fw, frame_reg, skip=("bottom",))
    K.axbox(mb, axis, c, side, a1 - fw, a1, F0, F1, z0, z1 - fw, frame_reg, skip=("bottom",))
    K.axbox(mb, axis, c, side, a0 + fw, a1 - fw, -0.205, -0.015, z0, z0 + 0.016, "stainless", skip=("bottom",))
    if zt:
        K.axbox(mb, axis, c, side, a0 + fw, a1 - fw, F0 + 0.005, F1 - 0.005, zt, zt + 0.07, frame_reg)
    la0, la1, lz0 = a0 + fw + 0.004, a1 - fw - 0.004, z0 + 0.020
    n = 2 if (a1 - a0) >= 1.10 else 1
    mid = 0.5 * (la0 + la1)
    leaves = [(la0, mid - 0.003, 1), (mid + 0.003, la1, -1)] if n == 2 else [(la0, la1, -1)]
    L0, L1 = -0.150, -0.085           # 문짝 두께 (외곽 문틀보다 안쪽)
    sw, tr, br = 0.060, 0.070, 0.170
    for k, (b0, b1, hand) in enumerate(leaves):
        # 울거미: 하대·상대·선대 (맞대기)
        K.axbox(mb, axis, c, side, b0, b1, L0, L1, lz0, lz0 + br, frame_reg)
        K.axbox(mb, axis, c, side, b0, b1, L0, L1, lz1 - tr, lz1, frame_reg)
        K.axbox(mb, axis, c, side, b0, b0 + sw, L0, L1, lz0 + br, lz1 - tr, frame_reg)
        K.axbox(mb, axis, c, side, b1 - sw, b1, L0, L1, lz0 + br, lz1 - tr, frame_reg)
        if stage == 0:
            ga0, ga1, gz0, gz1 = b0 + sw, b1 - sw, lz0 + br, lz1 - tr
            wins.add_face(axis, c - side * 0.118, side, ga0, ga1, gz0, gz1, 0, unit + k)
            wins.items[-1]["pts2"] = K.face_pts(axis, c + side * 0.025, side, b0, b1, lz0, lz1)
            if lit is not None:
                lit.append(len(wins.items) - 1)
            # 유리 누름대(비드): 유리 앞 얇은 테 (선대 안쪽면과 맞대기)
            for p in ((ga0, ga1, gz0, gz0 + 0.022), (ga0, ga1, gz1 - 0.022, gz1)):
                K.axbox(mb, axis, c, side, p[0], p[1], L1, L1 + 0.012, p[2], p[3], frame_reg)
            for p in ((ga0, ga0 + 0.022), (ga1 - 0.022, ga1)):
                K.axbox(mb, axis, c, side, p[0], p[1], L1, L1 + 0.012, gz0 + 0.022, gz1 - 0.022, frame_reg)
            # 스텐 킥플레이트 (하대 앞 6 mm)
            K.axbox(mb, axis, c, side, b0 + 0.010, b1 - 0.010, L1, L1 + 0.006, lz0 + 0.020, lz0 + br - 0.025,
                    "stainless")
            # 세로 바 손잡이 (맞닿는 선대 쪽, 받침 2개 + 바)
            hx = (b1 - 0.115) if hand > 0 else (b0 + 0.115)
            hz0, hz1 = z0 + 0.72, z0 + 1.48
            for sz in (hz0 + 0.08, hz1 - 0.10):      # 받침은 유리 바로 앞(3 mm)까지 관통 고정
                K.axbox(mb, axis, c, side, hx - 0.009, hx + 0.009, -0.115, L1 + 0.052, sz, sz + 0.02, "stainless")
            K.axbox(mb, axis, c, side, hx - 0.014, hx + 0.014, L1 + 0.052, L1 + 0.078, hz0, hz1, "stainless")
            # 실린더 잠금장치 (선대 위)
            lx = (b1 - sw * 0.5) if hand > 0 else (b0 + sw * 0.5)
            K.axbox(mb, axis, c, side, lx - 0.018, lx + 0.018, L1, L1 + 0.010, z0 + 1.00, z0 + 1.16, "door_trim")
            # 도어체크 (상대 위, 경첩 쪽)
            cx0, cx1 = (b0 + 0.05, b0 + 0.33) if hand > 0 else (b1 - 0.33, b1 - 0.05)
            K.axbox(mb, axis, c, side, cx0, cx1, L1, L1 + 0.048, lz1 - tr + 0.008, lz1 - 0.008, "iron_dark")
        else:
            mb.rect(K.face_pts(axis, c - side * 0.118, side, b0 + sw, b1 - sw, lz0 + br, lz1 - tr), "window_backing")
    if zt and stage == 0:
        wins.add_face(axis, c - side * 0.118, side, a0 + fw, a1 - fw, zt + 0.07, z1 - fw, 0, unit + 5)
        wins.items[-1]["pts2"] = K.face_pts(axis, c + side * 0.025, side, a0 + fw, a1 - fw, zt + 0.07, z1 - fw)
        if lit is not None:
            lit.append(len(wins.items) - 1)
    elif zt:
        mb.rect(K.face_pts(axis, c - side * 0.118, side, a0 + fw, a1 - fw, zt + 0.07, z1 - fw), "window_backing")
    if casing:
        add_door_casing(mb, axis, c, side, a0, a1, z0, z1, stage, casing_reg)


def add_steel_door(mb, axis, c, side, a0, a1, z0, z1, stage, *, surface=False, handle_right=True,
                   casing=True, casing_reg="door_trim"):
    """철제 방화문/보조문 한 벌: 문틀(도장 다크) + 회색 철판 문짝 + 패널·킥플레이트·레버·도어클로저
    + 경첩 3개 + 문선·인방. surface=True 는 개구부 없는 벽(옥탑) 표면에 붙이는 형식."""
    if stage == 2:
        mb.rect(K.face_pts(axis, c + side * (0.002 if not surface else 0.004), side, a0, a1, z0, z1), "door_wood")
        return
    fw = 0.06
    if surface:
        F0, F1, L0, L1 = 0.0, 0.065, 0.0, 0.036
    else:
        F0, F1, L0, L1 = -0.150, -0.030, -0.160, -0.100
    sk = ("bottom",) if z0 <= 0.001 else ()
    K.axbox(mb, axis, c, side, a0, a1, F0, F1, z1 - fw, z1, "alu_dark")
    K.axbox(mb, axis, c, side, a0, a0 + fw, F0, F1, z0, z1 - fw, "alu_dark", skip=sk)
    K.axbox(mb, axis, c, side, a1 - fw, a1, F0, F1, z0, z1 - fw, "alu_dark", skip=sk)
    K.axbox(mb, axis, c, side, a0 + fw, a1 - fw, L0, L1, z0, z1 - fw, "door_wood", skip=sk)
    if stage == 0:
        add_steel_door_details(mb, axis, c, side, a0, a1, z0, z1, leaf_o=L1, fw=fw,
                               add_threshold=not surface and z0 <= 0.05, handle_right=handle_right)
        hx0, hx1 = (a0 + fw - 0.012, a0 + fw + 0.006) if handle_right else (a1 - fw - 0.006, a1 - fw + 0.012)
        for hz in (z0 + 0.25, z0 + 1.02, z1 - fw - 0.30):
            K.axbox(mb, axis, c, side, hx0, hx1, L1, L1 + 0.016, hz, hz + 0.11, "iron_dark")
    if casing:
        if surface:
            # 표면형: 외곽 문틀 바깥에 얇은 문선(문틀보다 낮게 0.02) + 인방
            K.axbox(mb, axis, c, side, a0 - 0.07, a0, 0.0, 0.020, z0, z1, casing_reg, skip=("top", "bottom"))
            K.axbox(mb, axis, c, side, a1, a1 + 0.07, 0.0, 0.020, z0, z1, casing_reg, skip=("top", "bottom"))
            K.axbox(mb, axis, c, side, a0 - 0.09, a1 + 0.09, 0.0, 0.040, z1, z1 + 0.10, casing_reg)
        else:
            add_door_casing(mb, axis, c, side, a0, a1, z0, z1, stage, casing_reg, w=0.07, head_h=0.10)


def add_rooftop_door(mb, axis, c, side, a0, a1, z0, z1, stage):
    """옥탑 철제 방화문: 콘크리트 문턱 위 표면형 문 한 벌 + 상부 빗물막이 차양."""
    if stage == 0:
        K.axbox(mb, axis, c, side, a0 - 0.12, a1 + 0.12, 0.0, 0.16, z0, z0 + 0.05, "concrete_light", skip=("bottom",))
        add_steel_door(mb, axis, c, side, a0, a1, z0 + 0.05, z1, stage, surface=True)
        K.axbox(mb, axis, c, side, a0 - 0.14, a1 + 0.14, 0.0, 0.24, z1 + 0.12, z1 + 0.16, "sash_dark")
    else:
        add_steel_door(mb, axis, c, side, a0, a1, z0, z1, stage, surface=True, casing=stage != 2)


def add_ceiling_lamp(mb, x0, x1, y0, y1, z_ceil, h=0.034):
    """필로티 천장 평판 LED등 (다크 베젤 + 발광 디퓨저)."""
    mb.box(x0, x1, y0, y1, z_ceil - h, z_ceil, "iron_dark", skip=("top", "bottom"))
    mb.box(x0 + 0.025, x1 - 0.025, y0 + 0.025, y1 - 0.025, z_ceil - h - 0.004, z_ceil - h + 0.002, "lamp")


def add_frustum(mb, cx, cy, z0, z1, r0, r1, reg, n=12, cap_top=True):
    """원뿔대(물탱크 상단 돔 등) 닫힌 솔리드."""
    uv = mb.atlas.uv(reg)
    uv3 = uv[:3]
    for k in range(n):
        t0 = 2.0 * math.pi * k / n
        t1 = 2.0 * math.pi * (k + 1) / n
        p0 = (cx + r0 * math.cos(t0), cy + r0 * math.sin(t0), z0)
        p1 = (cx + r0 * math.cos(t1), cy + r0 * math.sin(t1), z0)
        p2 = (cx + r1 * math.cos(t1), cy + r1 * math.sin(t1), z1)
        p3 = (cx + r1 * math.cos(t0), cy + r1 * math.sin(t0), z1)
        mb.rect([p0, p1, p2, p3], reg)
        if cap_top and r1 > 1e-4:
            mb.tri([p3, p2, (cx, cy, z1)], uv3, reg)


def _floor_base(spec, f):
    return spec.z_f2 + f * spec.floor_h


# 창 정의: (a0, a1, sill_off, head_off, panes) — 층 바닥 기준 높이
BIG = (0.90, 2.30)      # 거실·안방 2~3짝 미닫이 1.40 m (브리프 1.25~1.45)
SMALL = (1.20, 2.25)    # 방·화장실 1.05 m
STAIR = (1.55, 2.62)    # 계단참 높이 창 (반층 위, 참고용)


def upper_holes(spec):
    W2, D = spec.width / 2.0, spec.depth
    return {
        ("y", 0.0, -1): [(-4.20, -2.40, *BIG, 3), (-1.20, 0.00, *SMALL, 2)],
        ("x", -W2, -1): [(1.00, 3.20, *BIG, 3), (4.60, 5.80, *SMALL, 2), (7.60, 9.80, *BIG, 3),
                         (10.60, 11.60, *SMALL, 2)],
        ("x", W2, 1): [(2.00, 3.20, *SMALL, 2), (5.00, 7.20, *BIG, 3), (9.00, 10.20, *SMALL, 2)],
        ("y", D, 1): [(-4.20, -2.20, *BIG, 3), (-0.60, 0.40, *SMALL, 2), (2.00, 3.80, *BIG, 3)],
    }


def _face_span(spec, axis, c):
    W2, D = spec.width / 2.0, spec.depth
    return (-W2, W2) if axis == "y" else (WALL_T, D - WALL_T)


# ---------------------------------------------------------------------------
# 빌더
# ---------------------------------------------------------------------------
def build_stage(spec: VillaSpec, a: K.Atlas, stage: int):
    mb = K.MeshBuilder(a, split_tiles=(stage == 0))
    wins = K.WindowSet()
    W2, D = spec.width / 2.0, spec.depth
    x0, x1 = -W2, W2
    zp, zf2, fh = spec.z_pil, spec.z_f2, spec.floor_h
    z_top = zf2 + spec.n_upper * fh                        # 11.40 지붕 슬래브 선
    bands = [(zf2 + k * fh - 0.08, zf2 + k * fh + 0.14) for k in range(1, spec.n_upper)]
    top_band = (z_top - 0.10, z_top + 0.12)
    z_slab1 = zf2 + 0.10                                    # 필로티 슬래브 상단 3.10
    z_eave0 = top_band[1]
    z_eave1 = z_eave0 + 0.10
    z_roof = z_eave1 + EAVE_RISE                            # 12.32

    x_core = 2.50                                           # 우측 계단실 코어 (x 2.5..5.3, y 0..8.0)
    y_rear = 8.00                                           # 후면 1층 실(주차장 뒤)
    sx0, sx1 = 3.10, 4.50                                   # 정면 우측 수직 계단실 유리 띠 베이 (폭 1.40 m)
    holes = upper_holes(spec)
    lit_win_indices = []

    # ===================== LOD2 단순 매스 =====================
    if stage == 2:
        for cx in (x0 + 0.225, -2.55, -0.05):
            for cy in (0.225, 4.0):
                mb.box(cx - 0.225, cx + 0.225, cy - 0.225, cy + 0.225, 0.0, zp, "plaster_white", skip=("bottom",))
        mb.box(x_core, x1, 0.0, y_rear, 0.0, zp, "wall_main", skip=("bottom",))
        mb.box(x0, x1, y_rear, D, 0.0, zp, "wall_main", skip=("bottom",))
        mb.box(x0 - BAND_O, x1 + BAND_O, -BAND_O, D + BAND_O, zp, z_slab1, "plaster_white")
        mb.box(x0, x1, 0.0, D, z_slab1, z_eave0, "wall_main", skip=("bottom",))
        _roof(mb, spec, z_eave0, z_eave1, z_roof, stage)
        K.paint(mb, "y", 0.0, -1, sx0 + 0.08, sx1 - 0.08, z_slab1 + 0.14, top_band[0] - 0.14, "window_backing")
        for (axis, c, side), hs in holes.items():
            for f in range(spec.n_upper):
                zb = _floor_base(spec, f)
                for (h0, h1, so, ho, _p) in hs:
                    K.paint(mb, axis, c, side, h0, h1, zb + so, zb + ho, "window_backing")
        return mb, wins

    # ===================== 1층 필로티 =====================
    # 기둥 (흰 도장 0.45 각, 브리프 0.45~0.60) — 정면·중간 2열, 3대 주차
    cols = [(cx, cy) for cx in (x0 + 0.225, -2.55, -0.05) for cy in (0.225, 4.0)]
    for cx, cy in cols:
        if stage == 0:
            KX_bevel(mb, cx - 0.225, cx + 0.225, cy - 0.225, cy + 0.225, 0.0, zp)
        else:
            mb.box(cx - 0.225, cx + 0.225, cy - 0.225, cy + 0.225, 0.0, zp, "plaster_white", skip=("bottom",))
    if stage == 0:
        # 정면 기둥 앞면·안쪽면 충돌방지 띠 (5 mm 판, 규칙 4)
        for cx in (x0 + 0.225, -2.55, -0.05):
            decal_plate(mb, "y", 0.0, -1, cx - 0.19, cx + 0.19, 0.35, 1.15, 0.005, "bumper")
        # 카스토퍼 (z=0 바닥 메시 대신 3D 블록, 규칙 6)
        for bx in ((x0 + 0.45 + 0.4, -2.775 - 0.4), (-2.325 + 0.4, -0.275 - 0.4), (0.175 + 0.4, x_core - 0.4)):
            mb.box(bx[0], bx[1], y_rear - 0.90, y_rear - 0.75, 0.0, 0.12, "stopper", skip=("bottom",))
        # 필로티 천장 LED 평판등 (전면 열 + 후면 열 + 공동현관 앞)
        for lx in (-3.8, -1.3, 1.2):
            add_ceiling_lamp(mb, lx - 0.32, lx + 0.32, 1.45, 1.85, zp)
            add_ceiling_lamp(mb, lx - 0.32, lx + 0.32, 4.20, 4.55, zp)
        add_ceiling_lamp(mb, 1.55, 2.15, 1.45, 1.95, zp)

    # 1층 외벽: 우측 코어(정면·좌·우) + 후면 실(정면·좌·후)
    rh = DC.add_recessed_wall
    # 코어 정면 (도로, -Y): 작은 창
    rh(mb, wins, "y", 0.0, -1, x_core, x1, 0.0, zp, "wall_main",
       [(3.40, 4.40, 1.20, 2.05, "window", 0, 2)], stage, spec.seed, wall_t=WALL_T)
    # 코어 좌측면 (-X, 필로티 쪽): 공동현관 유리문 (알루미늄 다크 프레임)
    ent = (1.00, 2.40, 0.02, 2.24)
    wall_with_doors(mb, wins, "x", x_core, -1, WALL_T, y_rear + WALL_T, 0.0, zp, "wall_main",
                    [(5.20, 6.20, 1.25, 2.05, "window", 0, 2)], stage, spec.seed + 1, [ent], wall_t=WALL_T)
    # 공동현관 양개 유리문 (문틀·울거미·손잡이·도어체크·문선/인방, 야간 점등 보장)
    add_glass_entry_door(mb, wins, "x", x_core, -1, *ent, stage, unit=spec.seed * 5 + 7, lit=lit_win_indices)
    # 우측면 (+X) 전체 깊이
    rh(mb, wins, "x", x1, 1, WALL_T, D - WALL_T, 0.0, zp, "wall_main",
       [(4.00, 5.00, 1.25, 2.05, "window", 0, 2), (9.80, 11.00, 1.25, 2.05, "window", 0, 2)],
       stage, spec.seed + 2, wall_t=WALL_T)
    # 후면 실 정면 (주차장 쪽, -Y at y_rear): 철제문 + 창
    svc = (-1.10, -0.15, 0.02, 2.10)
    wall_with_doors(mb, wins, "y", y_rear, -1, x0, x_core, 0.0, zp, "wall_main",
                    [(-4.00, -2.80, 1.20, 2.05, "window", 0, 2)], stage, spec.seed + 3, [svc], wall_t=WALL_T)
    add_steel_door(mb, "y", y_rear, -1, *svc, stage)
    # 후면 실 좌측면 (-X)
    rh(mb, wins, "x", x0, -1, y_rear + WALL_T, D - WALL_T, 0.0, zp, "wall_main",
       [(9.60, 10.60, 1.25, 2.05, "window", 0, 2)], stage, spec.seed + 4, wall_t=WALL_T)
    # 후면 (+Y)
    rh(mb, wins, "y", D, 1, x0, x1, 0.0, zp, "wall_main",
       [(-3.60, -2.60, 1.25, 2.05, "window", 0, 2), (1.00, 2.20, 1.25, 2.05, "window", 0, 2)],
       stage, spec.seed + 5, wall_t=WALL_T)
    # 1층 실내 막음 (외벽 안쪽 2 cm, 겹침 0)
    ci = WALL_T + 0.02
    mb.box(x_core + ci, x1 - ci, ci, y_rear - 0.02, 0.0, zp - 0.01, "concrete_light", skip=("bottom",))
    mb.box(x0 + ci, x1 - ci, y_rear + ci, D - ci, 0.0, zp - 0.01, "concrete_light", skip=("bottom",))

    if stage == 0:
        # 공동현관 문턱 단차 + 미끄럼방지 스텐 논슬립 (양옆 문선 사이에 맞대기)
        mb.box(x_core - 0.28, x_core - 0.002, 1.00, 2.40, 0.0, 0.036, "concrete_light", skip=("bottom",))
        mb.box(x_core - 0.28, x_core - 0.245, 1.02, 2.38, 0.036, 0.044, "stainless", skip=("bottom",))
        # 공동현관 옆 우편함 (빗물 덮개 + 3D 투입구 슬롯) · 인터폰 · 도로 쪽 번호판
        K.axbox(mb, "x", x_core, -1, 2.60, 3.20, 0.0, 0.15, 1.00, 1.80, "stainless")
        K.axbox(mb, "x", x_core, -1, 2.58, 3.22, 0.0, 0.18, 1.80, 1.825, "stainless")
        for mz in (1.14, 1.36, 1.58):
            K.axbox(mb, "x", x_core, -1, 2.66, 3.14, 0.152, 0.160, mz, mz + 0.028, "iron_dark")
        add_intercom(mb, "x", x_core, -1, 0.66, 0.88, 1.32, 1.60)
        decal_plate(mb, "y", 0.0, -1, 2.80, 3.07, 1.85, 2.07, 0.014, "address")
        # 1층 실외기 2대 (필로티 후면 벽 앞)
        DC.add_ac_unit(mb, "y", y_rear, -1, -4.6, 0.0, stage)
        DC.add_ac_unit(mb, "y", y_rear, -1, 1.4, 0.0, stage)

    # ===================== 필로티 슬래브 띠 =====================
    mb.box(x0 - BAND_O, x1 + BAND_O, -BAND_O, D + BAND_O, zp, z_slab1, "plaster_white")

    # ===================== 2~4층 벽 =====================
    seg_z = [z_slab1] + [z for b in bands for z in b] + [top_band[0]]
    segs = list(zip(seg_z[0::2], seg_z[1::2]))            # 층별 벽 구간
    for f, (zb0, zb1) in enumerate(segs):
        zb = _floor_base(spec, f)
        for k, ((axis, c, side), hs) in enumerate(holes.items()):
            hh = [(h0, h1, zb + so, zb + ho, "window", f + 1, p) for (h0, h1, so, ho, p) in hs]
            if (axis, c, side) == ("y", 0.0, -1):
                # 정면은 우측 수직 계단실 베이(sx0..sx1) 좌·우로 분할해 층별 벽체 생성
                rh(mb, wins, axis, c, side, x0, sx0, zb0, zb1, "wall_main", hh, stage,
                   spec.seed + 10 + f * 4 + k, wall_t=WALL_T)
                rh(mb, wins, axis, c, side, sx1, x1, zb0, zb1, "wall_main", [], stage,
                   spec.seed + 50 + f, wall_t=WALL_T)
            else:
                lo, hi = _face_span(spec, axis, c)
                rh(mb, wins, axis, c, side, lo, hi, zb0, zb1, "wall_main", hh, stage,
                   spec.seed + 10 + f * 4 + k, wall_t=WALL_T)

    # 정면 우측 수직 계단실 유리 띠 (2~4층 연속 다크 프레임 + 층별/반층 가로 멀리언)
    st_a0, st_a1 = sx0 + 0.08, sx1 - 0.08
    st_z0, st_z1 = z_slab1 + 0.14, top_band[0] - 0.14
    w_before_stair = len(wins.items)
    rh(mb, wins, "y", 0.0, -1, sx0, sx1, z_slab1, top_band[0], "wall_main",
       [(st_a0, st_a1, st_z0, st_z1, "window", 1, 1)], stage, spec.seed + 77,
       wall_t=WALL_T, sash_reg="sash_dark")
    if stage == 0 and len(wins.items) > w_before_stair:
        # 단일 수직 유리를 3개 층별 발광 패널로 교체해 층별 자연스러운 야간 점등 보장
        wins.items.pop()
        g0, g1 = st_a0 + 0.095 * 0.80, st_a1 - 0.095 * 0.80
        for sf, (gz0, gz1) in enumerate(((st_z0 + 0.08, 5.78), (5.86, 8.58), (8.66, st_z1 - 0.08)), start=1):
            wins.add_face("y", 0.145, -1, g0, g1, gz0, gz1, sf, 90 + sf)
            wins.items[-1]["pts2"] = K.face_pts("y", -0.025, -1, st_a0 + 0.05, st_a1 - 0.05, gz0, gz1)
            lit_win_indices.append(len(wins.items) - 1)
    # 계단실 다크 알루미늄 가로 멀리언 (층 슬래브선 2줄 + 반층 계단참 3줄)
    for mz, mh in ((4.20, 0.048), (5.78, 0.080), (7.00, 0.048), (8.58, 0.080), (9.70, 0.048)):
        K.axbox(mb, "y", 0.0, -1, st_a0 + 0.095, st_a1 - 0.095, -0.115, -0.020, mz, mz + mh, "sash_dark")

    mb.box(x0 + ci, x1 - ci, ci, D - ci, z_slab1 + 0.01, top_band[0] - 0.01, "wall_main")
    # 층간 흰 슬래브 띠 (정면 계단실 수직 띠 구간은 깔끔하게 끊어 창 가림 0)
    for b0, b1 in bands:
        mb.box(x0 - BAND_O, x1 + BAND_O, WALL_T, D + BAND_O, b0, b1, "plaster_white")
        mb.box(x0 - BAND_O, sx0, -BAND_O, WALL_T, b0, b1, "plaster_white", skip=("back",))
        mb.box(sx1, x1 + BAND_O, -BAND_O, WALL_T, b0, b1, "plaster_white", skip=("back",))
    # 최상부 흰 띠는 전체 둘레 연속
    mb.box(x0 - BAND_O, x1 + BAND_O, -BAND_O, D + BAND_O, top_band[0], top_band[1], "plaster_white")

    # 흰 모서리 띠 (4 모서리 L자, 띠 돌출 0.06 안쪽 0.03 → 겹침 0)
    for xs, ys in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        cx = x0 if xs < 0 else x1
        cy = 0.0 if ys < 0 else D
        fx0, fx1 = sorted((cx + xs * CORNER_O, cx - xs * CORNER_W))
        fy0, fy1 = sorted((cy, cy + ys * CORNER_O))
        mb.box(fx0, fx1, fy0, fy1, z_slab1, top_band[0], "plaster_white")
        sx0_c, sx1_c = sorted((cx, cx + xs * CORNER_O))
        sy0_c, sy1_c = sorted((cy, cy - ys * CORNER_W))
        mb.box(sx0_c, sx1_c, sy0_c, sy1_c, z_slab1, top_band[0], "plaster_white")

    # ===================== 지붕 =====================
    _roof(mb, spec, z_eave0, z_eave1, z_roof, stage)

    # ===================== 부속 디테일 (main 전용) =====================
    if stage == 0:
        # 거실 큰 창 방범 난간 (창 밀착형 0.65 m, 다크 철제, 브리프 4장)
        for f in range(spec.n_upper):
            zb = _floor_base(spec, f)
            for (axis, c, side), hs in holes.items():
                if (axis, side) not in (("y", -1), ("x", -1)):
                    continue
                for (h0, h1, so, ho, p) in hs:
                    if p != 3:
                        continue
                    zs = zb + so
                    off = c + side * 0.12
                    p0, p1 = ((h0 - 0.04, off), (h1 + 0.04, off)) if axis == "y" else ((off, h0 - 0.04), (off, h1 + 0.04))
                    DC.add_railing_run(mb, p0, p1, zs, 0.65, stage, reg="iron_dark", post_step=1.15, picket_step=0.13)
                    for aa in (h0 - 0.04, h1 + 0.04):
                        K.axbox(mb, axis, c, side, aa - 0.015, aa + 0.015, 0.055, 0.096, zs + 0.06, zs + 0.10, "iron_dark")
        # 실외기 (후면 작은 창 아래, 앵글 거치대 포함)
        for f in range(spec.n_upper):
            DC.add_ac_unit(mb, "y", D, 1, -0.10, _floor_base(spec, f) + 0.30, stage)
        DC.add_ac_unit(mb, "x", x1, 1, 6.10, _floor_base(spec, 0) + 0.30, stage)
        # 우수관 (후면 양 모서리, 흰 모서리 띠 바깥)
        for ax in (x0 + 0.50, x1 - 0.50):
            DC.add_downspout(mb, "y", D, 1, ax, 0.0, z_eave0)
        # 도시가스 배관 (a01·a02: 좌측면 수평 주관 + 세대 인입 수직관)
        _gas_pipes(mb, spec, x0)
        # 계단실·공동현관 야간 점등 보장
        ensure_lit_windows(wins, lit_win_indices, spec.seed + 53)
    return mb, wins


def KX_bevel(mb, x0, x1, y0, y1, z0, z1):
    KX.bevel_box(mb, x0, x1, y0, y1, z0, z1, "plaster_white", bevel=0.02)


def _gas_pipes(mb, spec, x0):
    r, o = 0.022, 0.11
    D = spec.depth
    pt = lambda y, z: (x0 - o, y, z)
    z_h = _floor_base(spec, 0) + 0.42
    DC.add_oct_tube(mb, pt(0.70, z_h), pt(D - 0.70, z_h), r, "pipe_gas", n=6)
    DC.add_oct_tube(mb, pt(D - 0.70, 1.10), pt(D - 0.70, z_h + r), r, "pipe_gas", n=6)
    for y in (4.20, 6.40):
        DC.add_oct_tube(mb, pt(y, z_h + r), pt(y, _floor_base(spec, 2) + 0.42), r, "pipe_gas", n=6)
    # 계량기 함 (후면 실 좌측 벽, z 0.70..1.10)
    K.axbox(mb, "x", x0, -1, D - 1.00, D - 0.40, 0.0, 0.16, 0.70, 1.10, "equip_gray")
    K.axbox(mb, "x", x0, -1, D - 0.72, D - 0.68, 0.0, o, 1.08, 1.12, "iron_dark")


def _roof(mb, spec, z_e0, z_e1, z_roof, stage):
    W2, D = spec.width / 2.0, spec.depth
    x0, x1 = -W2, W2
    # 처마 띠 (갈색 + 흰 소핏), 경사면, 평지붕 덱
    mb.box(x0 - EAVE_O, x1 + EAVE_O, -EAVE_O, D + EAVE_O, z_e0, z_e1,
           {"default": "roof_trim", "bottom": "plaster_white"})
    o, i = EAVE_O, EAVE_IN
    q = [((x0 - o, -o), (x1 + o, -o), (x1 - i, i), (x0 + i, i)),
         ((x1 + o, -o), (x1 + o, D + o), (x1 - i, D - i), (x1 - i, i)),
         ((x1 + o, D + o), (x0 - o, D + o), (x0 + i, D - i), (x1 - i, D - i)),
         ((x0 - o, D + o), (x0 - o, -o), (x0 + i, i), (x0 + i, D - i))]
    for (p0, p1, p2, p3) in q:
        pts = [(p0[0], p0[1], z_e1), (p1[0], p1[1], z_e1), (p2[0], p2[1], z_roof), (p3[0], p3[1], z_roof)]
        if stage == 2:
            mb.rect(pts, "roof_trim")
        else:
            DC.add_tiled_slope_poly(mb, pts, "roof_shingle", stage)
    mb.box(x0 + i, x1 - i, i, D - i, z_e1, z_roof, {"default": "plaster_white", "top": "roof_deck"})
    # 옥탑 계단실 (코어 위, 파라펫 내측 이격) # estimated (브리프 4장 2.4x3.2x2.4)
    px0, px1, py0, py1, ph = 2.45, 4.85, 0.65, 3.85, 2.40
    if stage == 2:
        mb.box(px0, px1, py0, py1, z_roof, z_roof + ph, "wall_main", skip=("bottom",))
        return

    # 옥상 파라펫 턱 + 콘크리트 갓돌 (4면 맞대기 -> 모서리 끊김·겹침 0, 규칙 4·8)
    pt, ph_p, ch = 0.22, 0.48, 0.07
    zp1, zp2 = z_roof + ph_p, z_roof + ph_p + ch
    mb.box(x0 + i, x1 - i, i, i + pt, z_roof, zp1, "plaster_white", skip=("bottom", "top"))
    mb.box(x0 + i, x1 - i, D - i - pt, D - i, z_roof, zp1, "plaster_white", skip=("bottom", "top"))
    mb.box(x0 + i, x0 + i + pt, i + pt, D - i - pt, z_roof, zp1, "plaster_white", skip=("bottom", "top"))
    mb.box(x1 - i - pt, x1 - i, i + pt, D - i - pt, z_roof, zp1, "plaster_white", skip=("bottom", "top"))
    co = 0.03
    mb.box(x0 + i - co, x1 - i + co, i - co, i + pt + co, zp1, zp2, "concrete_light")
    mb.box(x0 + i - co, x1 - i + co, D - i - pt - co, D - i + co, zp1, zp2, "concrete_light")
    mb.box(x0 + i - co, x0 + i + pt + co, i + pt + co, D - i - pt - co, zp1, zp2, "concrete_light")
    mb.box(x1 - i - pt - co, x1 - i + co, i + pt + co, D - i - pt - co, zp1, zp2, "concrete_light")

    # 옥탑 본체 + 갓돌 + 출입문 디테일
    zt = z_roof + ph - 0.22
    mb.box(px0, px1, py0, py1, z_roof, zt, "wall_main", skip=("bottom",))
    mb.box(px0 - 0.06, px1 + 0.06, py0 - 0.06, py1 + 0.06, zt, z_roof + ph,
           {"default": "plaster_white", "top": "concrete_light"})
    da0, da1, dz0, dz1 = 1.80, 2.70, z_roof, z_roof + 2.02
    add_rooftop_door(mb, "x", px0, -1, da0, da1, dz0, dz1, stage)

    # 물탱크 (스텐 원통 + 고정 프레임 + 상단 돔/뚜껑 + 유입·유출 배관) # estimated
    tx, ty = -3.2, D - 2.4
    z_pad = z_roof + 0.14
    z_tk0 = z_pad + 0.26
    z_tk1 = z_tk0 + 1.42
    mb.box(tx - 0.78, tx + 0.78, ty - 0.78, ty + 0.78, z_roof, z_pad, "concrete_light", skip=("bottom",))
    if stage == 0:
        # 고정 철제 프레임 (4각 다리 + 상부 지지 링 보)
        for sx in (-0.46, 0.46):
            for sy in (-0.46, 0.46):
                mb.box(tx + sx - 0.032, tx + sx + 0.032, ty + sy - 0.032, ty + sy + 0.032,
                       z_pad, z_tk0 - 0.05, "iron_dark", skip=("bottom", "top"))
        mb.box(tx - 0.52, tx + 0.52, ty - 0.52, ty - 0.44, z_tk0 - 0.05, z_tk0, "iron_dark")
        mb.box(tx - 0.52, tx + 0.52, ty + 0.44, ty + 0.52, z_tk0 - 0.05, z_tk0, "iron_dark")
        mb.box(tx - 0.52, tx - 0.44, ty - 0.44, ty + 0.44, z_tk0 - 0.05, z_tk0, "iron_dark")
        mb.box(tx + 0.44, tx + 0.52, ty - 0.44, ty + 0.44, z_tk0 - 0.05, z_tk0, "iron_dark")
        # 원통 본체 + 보강 띠 2줄
        DC.add_oct_tube(mb, (tx, ty, z_tk0), (tx, ty, z_tk1), 0.60, "stainless", n=12)
        for rz in (z_tk0 + 0.44, z_tk0 + 0.96):
            DC.add_oct_tube(mb, (tx, ty, rz), (tx, ty, rz + 0.036), 0.618, "stainless", n=12)
        # 상단 2단 돔 + 점검 뚜껑(해치) + 손잡이
        add_frustum(mb, tx, ty, z_tk1, z_tk1 + 0.13, 0.61, 0.40, "stainless", n=12, cap_top=False)
        add_frustum(mb, tx, ty, z_tk1 + 0.13, z_tk1 + 0.21, 0.40, 0.22, "stainless", n=12, cap_top=True)
        DC.add_oct_tube(mb, (tx, ty, z_tk1 + 0.21), (tx, ty, z_tk1 + 0.29), 0.17, "iron_dark", n=8)
        mb.box(tx - 0.08, tx + 0.08, ty - 0.015, ty + 0.015, z_tk1 + 0.29, z_tk1 + 0.325, "stainless", skip=("bottom",))
        # 유입 배관 (상부 인입) + 유출 배관 (하부 인출 + 밸브 박스) + 오버플로우 벤트
        DC.add_oct_tube(mb, (tx + 0.88, ty - 0.30, z_roof), (tx + 0.88, ty - 0.30, z_tk1 - 0.14), 0.034, "pipe_white", n=6)
        DC.add_oct_tube(mb, (tx + 0.54, ty - 0.30, z_tk1 - 0.14), (tx + 0.91, ty - 0.30, z_tk1 - 0.14), 0.034, "pipe_white", n=6)
        DC.add_oct_tube(mb, (tx + 0.54, ty + 0.28, z_tk0 + 0.14), (tx + 0.94, ty + 0.28, z_tk0 + 0.14), 0.038, "stainless", n=6)
        DC.add_oct_tube(mb, (tx + 0.94, ty + 0.28, z_roof), (tx + 0.94, ty + 0.28, z_tk0 + 0.17), 0.038, "stainless", n=6)
        mb.box(tx + 0.70, tx + 0.82, ty + 0.22, ty + 0.34, z_tk0 + 0.08, z_tk0 + 0.24, "iron_dark")
        DC.add_oct_tube(mb, (tx - 0.56, ty, z_tk1 - 0.08), (tx - 0.74, ty, z_tk1 - 0.08), 0.024, "stainless", n=6)
        DC.add_oct_tube(mb, (tx - 0.74, ty, z_tk1 - 0.24), (tx - 0.74, ty, z_tk1 - 0.06), 0.024, "stainless", n=6)
    else:
        DC.add_oct_tube(mb, (tx, ty, z_pad), (tx, ty, z_tk1 + 0.18), 0.60, "stainless", n=8)


def build_and_export(spec: VillaSpec, out_root=None):
    a = build_atlas(spec)
    main, wins = build_stage(spec, a, 0)
    l1, _ = build_stage(spec, a, 1)
    l2, _ = build_stage(spec, a, 2)
    folder, result = K.export_asset(
        spec.name, 1, dict(main=main, lod1=l1, lod2=l2, windows=wins), a,
        out_root or K.out_dir_from_argv("output"), lod2_tex=512, lot=spec.lot, front_yard=spec.front_yard,
        notes=dict(archetype="villa_A_piloti_brick", seed=spec.seed))
    print(f"[villa_core] {result['asset']}: main={main.tri_count} lod1={l1.tri_count} "
          f"lod2={l2.tri_count} wins={len(wins.items)} (lod2+2w={l2.tri_count + len(wins.items) * 2})")
    return folder, result
