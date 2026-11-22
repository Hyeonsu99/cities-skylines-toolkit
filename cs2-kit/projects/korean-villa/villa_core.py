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


def build_atlas(spec: VillaSpec, *, charcoal=False) -> K.Atlas:
    s = spec.seed
    a = K.Atlas(size=2048, pad=12)
    # 벽돌: 사진 a01 그늘 벽돌 면 (132,104,99) ~ 브리프 진적갈 (128,92,86). 줄눈 밝은 회색 시멘트 (규칙 18)
    a.add("wall_main", color=(96, 98, 100) if charcoal else (128, 92, 86), ctrl=(0, 255, 0), px=512, tile=(2.3, 2.4),
          gloss=0.24, painter=_brick_painter(s, (188, 186, 185)))
    a.add("plaster_white", color=(212, 211, 208), ctrl=(0, 255, 0), px=384, tile=(2.4, 2.4),
          gloss=0.24, painter=DC._make_plaster_painter(s + 11))
    a.add("concrete_light", color=(178, 180, 183), px=256, tile=(2.4, 2.4),
          gloss=0.24, painter=DC._make_concrete_plinth_painter(s + 23))
    # 갈색 경사 처마 (a01·a02 상단 갈색 기와형 금속 처마) # estimated 재질
    a.add("roof_shingle", color=(104, 76, 64), ctrl=(255, 0, 0), px=384, tile=(1.76, 1.68),
          gloss=0.36, painter=DC._make_clay_tile_painter(s + 31))
    a.add("roof_trim", color=(104, 76, 64), ctrl=(255, 0, 0), px=128, gloss=0.38,
          painter=DC._solid(3.0, 0.30, 0.44, s + 33))
    a.add("roof_deck", color=(124, 140, 128), px=256, tile=(2.4, 2.4), gloss=0.30,
          painter=DC._make_terrace_floor_painter(s + 47))   # 옥상 우레탄 방수 녹회 # estimated
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
    a.add("lamp", color=(244, 224, 182), emissive=(255, 218, 156), px=32, gloss=0.62,
          painter=DC._solid(1.0, 0.56, 0.66, s + 107))
    a.add("address", px=256, gloss=0.48,
          painter=_plate_painter(f"addr_{spec.road_name}_{spec.road_no}", _draw_address(spec.road_name, spec.road_no)))
    a.add("bumper", px=128, gloss=0.46, painter=_plate_painter("bumper", _draw_bumper))
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
    """얇은 3D 판 + 앞면 칸 전체 UV (번호판·충돌방지 띠, 규칙 12)."""
    K.axbox(mb, axis, c, side, a0, a1, o0, o0 + t, z0, z1, edge_reg, skip=(_skip_face(axis, side),))
    mb.quad(K.face_pts(axis, c + side * (o0 + t), side, a0, a1, z0, z1), mb.atlas.uv_full(full_reg), full_reg)


def _floor_base(spec, f):
    return spec.z_f2 + f * spec.floor_h


# 창 정의: (a0, a1, sill_off, head_off, panes) — 층 바닥 기준 높이
BIG = (0.90, 2.30)      # 거실·안방 2~3짝 미닫이 1.40 m (브리프 1.25~1.45)
SMALL = (1.20, 2.25)    # 방·화장실 1.05 m
STAIR = (1.55, 2.62)    # 계단참 높이 창 (반층 위)


def upper_holes(spec):
    W2, D = spec.width / 2.0, spec.depth
    return {
        ("y", 0.0, -1): [(-4.20, -2.40, *BIG, 3), (-1.20, 0.00, *SMALL, 2), (3.20, 4.40, *STAIR, 2)],
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
    holes = upper_holes(spec)

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
        # 필로티 천장 LED 평판등
        for lx in (-3.8, -1.3, 1.2):
            mb.box(lx - 0.30, lx + 0.30, 3.6, 3.9, zp - 0.03, zp, "lamp")

    # 1층 외벽: 우측 코어(정면·좌·우) + 후면 실(정면·좌·후)
    rh = DC.add_recessed_wall
    # 코어 정면 (도로, -Y): 작은 창
    rh(mb, wins, "y", 0.0, -1, x_core, x1, 0.0, zp, "wall_main",
       [(3.40, 4.40, 1.20, 2.05, "window", 0, 2)], stage, spec.seed, wall_t=WALL_T)
    # 코어 좌측면 (-X, 필로티 쪽): 공동현관 유리문 (알루미늄 다크 프레임)
    rh(mb, wins, "x", x_core, -1, WALL_T, y_rear + WALL_T, 0.0, zp, "wall_main",
       [(1.00, 2.40, 0.03, 2.15, "door_glass", 0, 2), (5.20, 6.20, 1.25, 2.05, "window", 0, 2)],
       stage, spec.seed + 1, wall_t=WALL_T, sash_reg="sash_dark")
    # 우측면 (+X) 전체 깊이
    rh(mb, wins, "x", x1, 1, WALL_T, D - WALL_T, 0.0, zp, "wall_main",
       [(4.00, 5.00, 1.25, 2.05, "window", 0, 2), (9.80, 11.00, 1.25, 2.05, "window", 0, 2)],
       stage, spec.seed + 2, wall_t=WALL_T)
    # 후면 실 정면 (주차장 쪽, -Y at y_rear): 철제문 + 창
    rh(mb, wins, "y", y_rear, -1, x0, x_core, 0.0, zp, "wall_main",
       [(-4.00, -2.80, 1.20, 2.05, "window", 0, 2), (-1.10, -0.15, 0.03, 2.10, "door_solid", 0, 1)],
       stage, spec.seed + 3, wall_t=WALL_T)
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
        # 공동현관 옆 우편함·인터폰, 도로 쪽 번호판 (브리프 4장, 규칙 20)
        K.axbox(mb, "x", x_core, -1, 2.60, 3.20, 0.0, 0.15, 1.00, 1.80, "stainless")
        K.paint(mb, "x", x_core - 0.15, -1, 2.64, 3.16, 1.04, 1.76, "louver")
        K.axbox(mb, "x", x_core, -1, 0.70, 0.84, 0.0, 0.04, 1.35, 1.55, "equip_gray")
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
            lo, hi = _face_span(spec, axis, c)
            hh = [(h0, h1, zb + so, zb + ho, "window", f + 1, p) for (h0, h1, so, ho, p) in hs]
            rh(mb, wins, axis, c, side, lo, hi, zb0, zb1, "wall_main", hh, stage,
               spec.seed + 10 + f * 4 + k, wall_t=WALL_T)
    mb.box(x0 + ci, x1 - ci, ci, D - ci, z_slab1 + 0.01, top_band[0] - 0.01, "wall_main")
    for b0, b1 in bands + [top_band]:
        mb.box(x0 - BAND_O, x1 + BAND_O, -BAND_O, D + BAND_O, b0, b1, "plaster_white")

    # 흰 모서리 띠 (4 모서리 L자, 띠 돌출 0.06 안쪽 0.03 → 겹침 0)
    for xs, ys in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        cx = x0 if xs < 0 else x1
        cy = 0.0 if ys < 0 else D
        fx0, fx1 = sorted((cx + xs * CORNER_O, cx - xs * CORNER_W))
        fy0, fy1 = sorted((cy, cy + ys * CORNER_O))
        mb.box(fx0, fx1, fy0, fy1, z_slab1, top_band[0], "plaster_white")
        sx0, sx1 = sorted((cx, cx + xs * CORNER_O))
        sy0, sy1 = sorted((cy, cy - ys * CORNER_W))
        mb.box(sx0, sx1, sy0, sy1, z_slab1, top_band[0], "plaster_white")

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
    # 옥탑 계단실 (코어 위) # estimated (브리프 4장 2.6x3.2x2.4)
    px0, px1, py0, py1, ph = 2.55, 4.95, 0.60, 3.80, 2.40
    if stage == 2:
        mb.box(px0, px1, py0, py1, z_roof, z_roof + ph, "wall_main", skip=("bottom",))
        return
    zt = z_roof + ph - 0.22
    mb.box(px0, px1, py0, py1, z_roof, zt, "wall_main", skip=("bottom",))
    mb.box(px0 - 0.06, px1 + 0.06, py0 - 0.06, py1 + 0.06, zt, z_roof + ph,
           {"default": "plaster_white", "top": "concrete_light"})
    K.axbox(mb, "x", px0, -1, 1.80, 2.70, 0.0, 0.03, z_roof, z_roof + 2.0, "door_wood")
    # 물탱크 (스텐 원통 1.2 m x 1.5 m, 콘크리트 받침) # estimated
    tx, ty = -3.2, D - 2.4
    mb.box(tx - 0.75, tx + 0.75, ty - 0.75, ty + 0.75, z_roof, z_roof + 0.15, "concrete_light", skip=("bottom",))
    DC.add_oct_tube(mb, (tx, ty, z_roof + 0.15), (tx, ty, z_roof + 1.65), 0.60, "stainless", n=12 if stage == 0 else 8)


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
