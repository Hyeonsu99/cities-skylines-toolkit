# -*- coding: utf-8 -*-
"""신탄진형 다세대 빌라 D01 대표형: 1층 근린상가 2칸 + 2~4층 고동 벽돌 주거, 4층.

STYLE_BRIEF 5.3 프리셋 D (v04·v07·v10·v22 1층 근린상가형, 브리프 4장 간판 규칙).
A~C 와 다른 점: 필로티 대신 1층 상가(층고 3.5 m, 화강석 기단·처마 띠, 알루미늄 커튼 쇼윈도·유리문),
가상 상호 가로 간판 2개 + 세로 돌출 간판, 중앙 매립형 주거 현관(정면 돌출 0, 쇼윈도 라인보다 1.4 m 안쪽),
정면 중앙 수직 계단실 유리, 연베이지 미장 모서리 기둥·파라펫과 중앙 박공 장식, 1층 측면 실외기.
상호·전화번호는 모두 가상(브리프 4장 예시 이름, 국번 000). 간판 발광은 근린상가 01 피드백대로 약하게 둔다.
"""
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import villa_core as V

K, DC, KX = V.K, V.DC, V.KX
HERE = Path(__file__).resolve().parent
SPEC = V.VillaSpec(name="SintanjinVillaD01", lot=(3, 3), width=14.0, depth=12.5,
                   n_upper=3, road_no="52", seed=31)

X0, X1, D = -7.0, 7.0, 12.5
ZS, ZB = 3.50, 3.75                     # 1층 상가 층고 3.5 (브리프 3.30~3.70) + 처마 띠
NF = 3
ZROOF = 3.65 + NF * 2.8                 # 12.05
ZPAR = ZROOF + .90
ZG = 2.70                               # 쇼윈도 상단 (위로 간판 띠)
ZT = 2.10                               # 쇼윈도·문 트랜섬
SA_W, SA_D = (-6.70, -2.30, .35, ZG), (-2.30, -1.10, .02, ZG)
SB_D, SB_W = (1.10, 2.30, .02, ZG), (2.30, 6.70, .35, ZG)
ALC = (-.90, .90, 0.0, ZG)              # 매립 현관 입구
ALC_Y = 1.40                            # 현관 매립 깊이
ENT = (-.60, .60, .02, 2.40)
SVC = (-3.30, -2.40, .02, 2.10)         # 후면 보조문 (상가 반출)
STAIR = (-.70, .70)                     # 정면 중앙 계단실 수직 유리

FRONT = [(-5.90, -3.50, .90, 2.30, 2), (-2.50, -1.50, 1.20, 2.25, 2),
         (1.50, 2.50, 1.20, 2.25, 2), (3.50, 5.90, .90, 2.30, 2)]
SIDE = [(1.60, 3.80, .90, 2.30, 2), (5.40, 6.40, 1.20, 2.25, 2), (8.60, 10.80, .90, 2.30, 2)]
BACK = [(-5.40, -3.20, .90, 2.30, 2), (-.50, .50, 1.20, 2.25, 2), (3.20, 5.40, .90, 2.30, 2)]
SHOPS = (("신탄칼국수", "손칼국수 · 수제비 · 보쌈", "042-000-5821", (142, 70, 62)),
         ("덕암컴퓨터", "수리 · 조립 · 프린터", "042-000-3307", (46, 78, 112)))


def zf(f):
    return 3.65 + 2.8 * f


def holes_for(hs, f):
    return [(a, b, zf(f) + s, zf(f) + h, "window", f + 1, p) for a, b, s, h, p in hs]


# ---------------------------------------------------------------------------
# 간판 시트 (1024 칸: 가로 간판 2장 + 세로 돌출 간판)
# ---------------------------------------------------------------------------
SIGN_A = (0, 0, 1024, 112)              # 픽셀 사각형 (x0, y0, x1, y1) — 판 비율 5.4 x 0.56 m ≈ 9.6:1
SIGN_B = (0, 128, 1024, 240)
SIGN_V = (0, 256, 232, 1024)            # 0.60 x 2.0 m ≈ 0.30


def _draw_signs(W, H):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (W, H), (96, 100, 104))
    d = ImageDraw.Draw(im)
    S = W / 1024.0
    cream, gold = (216, 212, 200), (212, 188, 120)
    F = lambda f, sz: ImageFont.truetype("C:/Windows/Fonts/" + f, int(sz * S))
    for (x0, y0, x1, y1), (name, sub, tel, bg) in zip((SIGN_A, SIGN_B), SHOPS):
        box = [int(x0 * S), int(y0 * S), int(x1 * S) - 1, int(y1 * S) - 1]
        d.rectangle(box, fill=bg)
        d.rectangle([box[0] + int(6 * S), box[1] + int(6 * S), box[2] - int(6 * S), box[3] - int(6 * S)],
                    outline=cream, width=max(2, int(4 * S)))
        cy = (y0 + y1) / 2 * S
        d.text((34 * S, cy), name, font=F("HMKMRHD.TTF", 84), fill=cream, anchor="lm")
        d.text((990 * S, cy - 20 * S), sub, font=F("H2GTRE.TTF", 30), fill=gold, anchor="rm")
        d.text((990 * S, cy + 22 * S), tel, font=F("H2HDRM.TTF", 34), fill=cream, anchor="rm")
    x0, y0, x1, y1 = SIGN_V
    name, _, _, bg = SHOPS[0]
    d.rectangle([int(x0 * S), int(y0 * S), int(x1 * S) - 1, int(y1 * S) - 1], fill=bg)
    d.rectangle([int((x0 + 8) * S), int((y0 + 8) * S), int((x1 - 8) * S), int((y1 - 8) * S)],
                outline=cream, width=max(2, int(4 * S)))
    chars = "칼국수"
    step = (y1 - y0 - 120) / len(chars)
    for k, ch in enumerate(chars):
        d.text(((x0 + x1) / 2 * S, (y0 + 50 + (k + .5) * step) * S), ch, font=F("HMKMRHD.TTF", 150),
               fill=gold if k == 0 else cream, anchor="mm")
    return im


def _signs_painter(ctx):
    cache = HERE / "work" / "_sign_cache" / f"d01_signs_{ctx.w}x{ctx.h}.npz"
    try:
        from PIL import Image
        rgb = np.asarray(_draw_signs(ctx.w * 2, ctx.h * 2).resize((ctx.w, ctx.h), Image.LANCZOS))
        cache.parent.mkdir(parents=True, exist_ok=True)
        np.savez(cache, rgb=rgb)
    except (ImportError, OSError):
        rgb = np.load(cache)["rgb"]
    ctx.rgb[...] = rgb
    lum = rgb.mean(axis=-1) / 255.0
    # 근린상가 01 "발광 너무 강함" 피드백: 글자만 은은하게 (최대 0.22)
    ctx.emis[...] = np.clip(0.05 + 0.20 * np.clip((lum - 0.55) * 3.0, 0, 1), 0.05, 0.22)
    ctx.grain(amp=1.0, scale_px=2, height=0.01, seed=331)
    ctx.gloss = np.clip(0.52 + 0.03 * DC._var(ctx, 8, 337), 0.45, 0.60)


def build_atlas(spec):
    a = V.build_atlas(spec, wall="brick_brown")
    a.add("shop_signs", color=(96, 100, 104), px=512, gloss=0.54, emissive=(255, 236, 200), painter=_signs_painter)
    return a


def sign_uv(atlas, rect):
    x0, y0, x1, y1 = rect
    return KX.uv_cell(atlas, "shop_signs", x0 / 1024, 1 - y1 / 1024, x1 / 1024, 1 - y0 / 1024)


# ---------------------------------------------------------------------------
# 상가 쇼윈도 (알루미늄 커튼월형: 외곽틀 + 세로 멀리언 + 트랜섬, 유리는 상·하 2장만)
# ---------------------------------------------------------------------------
def add_storefront(mb, wins, axis, c, side, a0, a1, z0, z1, stage, unit, n=3, lit=None):
    if stage == 2:
        mb.rect(K.face_pts(axis, c + side * .002, side, a0, a1, z0, z1), "window_backing")
        return
    fw, F0, F1 = .065, -.185, -.055
    K.axbox(mb, axis, c, side, a0, a1, F0, F1, z0, z0 + fw, "alu_dark")
    K.axbox(mb, axis, c, side, a0, a1, F0, F1, z1 - fw, z1, "alu_dark")
    K.axbox(mb, axis, c, side, a0, a0 + fw, F0, F1, z0 + fw, z1 - fw, "alu_dark")
    K.axbox(mb, axis, c, side, a1 - fw, a1, F0, F1, z0 + fw, z1 - fw, "alu_dark")
    K.axbox(mb, axis, c, side, a0 + fw, a1 - fw, F0, F1, ZT, ZT + .07, "alu_dark")
    for k in range(1, n):
        m = a0 + (a1 - a0) * k / n
        K.axbox(mb, axis, c, side, m - .03, m + .03, F0 + .01, F1 + .01, z0 + fw, ZT, "alu_dark")
        K.axbox(mb, axis, c, side, m - .03, m + .03, F0 + .01, F1 + .01, ZT + .07, z1 - fw, "alu_dark")
    if stage == 0:
        for gz0, gz1, u in ((z0 + fw, ZT, 0), (ZT + .07, z1 - fw, 1)):
            wins.add_face(axis, c - side * .125, side, a0 + fw, a1 - fw, gz0, gz1, 0, unit + u)
            wins.items[-1]["pts2"] = K.face_pts(axis, c + side * .025, side, a0 + fw, a1 - fw, gz0, gz1)
            if lit is not None:
                lit.append(len(wins.items) - 1)
        KX.paint_reveal(mb, axis, c, side, a0, a1, z0, z1, .055, "granite_light", inset=.002, sill=True, head=True)


def add_gable(mb, x0, x1, y0, y1, zb, rise, region):
    """정면 박공 장식 (삼각 프리즘, 밑면 생략)."""
    xm, zt = (x0 + x1) / 2, zb + rise
    uv = mb.atlas.uv(region)[:3]
    mb.tri([(x0, y0, zb), (x1, y0, zb), (xm, y0, zt)], uv, region)
    mb.tri([(x1, y1, zb), (x0, y1, zb), (xm, y1, zt)], uv, region)
    mb.rect([(x1, y0, zb), (x1, y1, zb), (xm, y1, zt), (xm, y0, zt)], region)
    mb.rect([(x0, y1, zb), (x0, y0, zb), (xm, y0, zt), (xm, y1, zt)], region)


def build_stage(spec, atlas, stage):
    mb, wins = K.MeshBuilder(atlas, split_tiles=stage == 0), K.WindowSet()
    rh = DC.add_recessed_wall
    tb = DC._world_tiled_box
    lit = []

    # ================= LOD2 =================
    if stage == 2:
        mb.box(X0, X1, 0, D, 0, ZS, "granite_light", skip=("bottom",))
        mb.box(X0 - .08, X1 + .08, -.08, D + .08, ZS, ZB, "granite_light")
        mb.box(X0, X1, 0, D, ZB, ZPAR, "wall_main", skip=("bottom",))
        add_gable(mb, -2.2, 2.2, 0.0, .22, ZPAR, 1.20, "plaster_beige")
        mb.box(-1.5, 1.5, .9, 3.9, ZPAR, ZROOF + 2.55, "wall_main", skip=("bottom",))
        for r in (SA_W, SA_D, SB_D, SB_W, ALC):
            K.paint(mb, "y", 0, -1, r[0], r[1], r[2], r[3], "window_backing")
        for r, (a, b) in ((SIGN_A, (-6.6, -1.2)), (SIGN_B, (1.2, 6.6))):
            mb.quad(K.face_pts("y", -.01, -1, a, b, 2.84, 3.40), sign_uv(atlas, r), "shop_signs")
        K.paint(mb, "y", 0, -1, STAIR[0] + .1, STAIR[1] - .1, ZB + .2, ZROOF - .2, "window_backing")
        for f in range(NF):
            for axis, c, s, hs in (("y", 0, -1, FRONT), ("x", X0, -1, SIDE), ("x", X1, 1, SIDE), ("y", D, 1, BACK)):
                for a, b, sl, hd, _ in hs:
                    K.paint(mb, axis, c, s, a, b, zf(f) + sl, zf(f) + hd, "window_backing")
        return mb, wins

    # ================= 1층 근린상가 =================
    V.wall_with_doors(mb, wins, "y", 0, -1, X0, X1, 0, ZS, "granite_light", [], stage, 11,
                      [SA_W, SA_D, ALC, SB_D, SB_W])
    add_storefront(mb, wins, "y", 0, -1, *SA_W, stage, 201, lit=lit)
    add_storefront(mb, wins, "y", 0, -1, *SB_W, stage, 211, lit=lit)
    V.add_glass_entry_door(mb, wins, "y", 0, -1, *SA_D, stage, unit=205, lit=lit, casing=False)
    V.add_glass_entry_door(mb, wins, "y", 0, -1, *SB_D, stage, unit=215, lit=lit, casing=False)
    # 매립 주거 현관: 양옆 화강석 벽 + 미장 안벽 + 천장(속 찬 블록)
    tb(mb, -1.10, -.90, .22, ALC_Y, 0, ZS, "granite_light", skip=("bottom",))
    tb(mb, .90, 1.10, .22, ALC_Y, 0, ZS, "granite_light", skip=("bottom",))
    tb(mb, -.90, .90, .22, ALC_Y, ZG, ZS, "granite_light", skip=("top",))
    V.wall_with_doors(mb, wins, "y", ALC_Y, -1, -.90, .90, 0, ZG, "plaster_beige", [], stage, 13, [ENT])
    w_pre = len(wins.items)
    V.add_glass_entry_door(mb, wins, "y", ALC_Y, -1, *ENT, stage, unit=221, lit=lit)
    for w in wins.items[w_pre:]:            # LOD2 는 현관 매립부가 없는 단순 매스 → 창 면을 정면으로 당김
        w["pts2"] = [(x, -.025, z) for x, _, z in w["pts2"]]
    # 측·후면 (고동 벽돌), 후면 보조문
    rh(mb, wins, "x", X0, -1, .22, D - .22, 0, ZS, "wall_main", [(8.4, 9.6, 1.30, 2.30, "window", 0, 2)], stage, 15)
    rh(mb, wins, "x", X1, 1, .22, D - .22, 0, ZS, "wall_main", [(8.4, 9.6, 1.30, 2.30, "window", 0, 2)], stage, 16)
    V.wall_with_doors(mb, wins, "y", D, 1, X0, X1, 0, ZS, "wall_main",
                      [(2.6, 3.8, 1.30, 2.30, "window", 0, 2)], stage, 17, [SVC])
    V.add_steel_door(mb, "y", D, 1, *SVC, stage)
    # 상가 내부 막음 (현관 구간 비움)
    mb.box(X0 + .24, -1.10, .24, D - .24, 0, ZS - .01, "concrete_light", skip=("bottom",))
    mb.box(1.10, X1 - .24, .24, D - .24, 0, ZS - .01, "concrete_light", skip=("bottom",))
    mb.box(-1.10, 1.10, ALC_Y + .24, D - .24, 0, ZS - .01, "concrete_light", skip=("bottom",))
    # 처마 띠 (모서리 감쌈)
    mb.box(X0 - .08, X1 + .08, -.08, D + .08, ZS, ZB, "granite_light")

    # ================= 2~4층 =================
    w_pre = len(wins.items)
    rh(mb, wins, "y", 0, -1, X0, X1, ZB, ZROOF, "wall_main",
       [h for f in range(NF) for h in holes_for(FRONT, f)] +
       [(STAIR[0], STAIR[1], ZB + .12, ZROOF - .10, "window", 1, 1)], stage, 20)
    if stage == 0:
        idx = [i for i in range(w_pre, len(wins.items)) if wins.items[i]["hh"] > 5.0]
        for i in sorted(idx, reverse=True):
            wins.items.pop(i)
        g0, g1 = STAIR[0] + .076, STAIR[1] - .076
        bounds = [ZB + .20] + [zf(f) - .03 for f in range(1, NF)] + [ZROOF - .18]
        for sf in range(NF):
            gz0 = bounds[sf] + (.03 if sf else 0)
            gz1 = bounds[sf + 1] - (.03 if sf < NF - 1 else 0)
            wins.add_face("y", .145, -1, g0, g1, gz0, gz1, sf + 1, 130 + sf)
            wins.items[-1]["pts2"] = K.face_pts("y", -.025, -1, STAIR[0] + .05, STAIR[1] - .05, gz0, gz1)
            lit.append(len(wins.items) - 1)
        for z in [zf(f) + .95 for f in range(NF)] + [zf(f) for f in range(1, NF)]:
            K.axbox(mb, "y", 0, -1, STAIR[0] + .10, STAIR[1] - .10, -.115, -.02, z - .03, z + .025, "sash_dark")
    rh(mb, wins, "x", X0, -1, .22, D - .22, ZB, ZROOF, "wall_main",
       [h for f in range(NF) for h in holes_for(SIDE, f)], stage, 21)
    rh(mb, wins, "x", X1, 1, .22, D - .22, ZB, ZROOF, "wall_main",
       [h for f in range(NF) for h in holes_for(SIDE, f)], stage, 22)
    rh(mb, wins, "y", D, 1, X0, X1, ZB, ZROOF, "wall_main",
       [h for f in range(NF) for h in holes_for(BACK, f)], stage, 23)
    mb.box(X0 + .24, X1 - .24, .24, D - .24, ZB + .01, ZROOF, "wall_main", skip=("top",))
    # 연베이지 미장 파라펫 (4면) + 정면 모서리 기둥형 미장 (L자, 0.04 돌출)
    rh(mb, wins, "y", 0, -1, X0, X1, ZROOF, ZPAR, "plaster_beige", [], stage, 24)
    rh(mb, wins, "y", D, 1, X0, X1, ZROOF, ZPAR, "plaster_beige", [], stage, 25)
    rh(mb, wins, "x", X0, -1, .22, D - .22, ZROOF, ZPAR, "plaster_beige", [], stage, 26)
    rh(mb, wins, "x", X1, 1, .22, D - .22, ZROOF, ZPAR, "plaster_beige", [], stage, 27)
    for xs in (-1, 1):
        cx = X0 if xs < 0 else X1
        fx0, fx1 = sorted((cx + xs * .04, cx - xs * .50))
        tb(mb, fx0, fx1, -.04, 0, ZB, ZPAR, "plaster_beige", skip=("back",))
        sx0, sx1 = sorted((cx, cx + xs * .04))
        tb(mb, sx0, sx1, 0, .50, ZB, ZPAR, "plaster_beige", skip=("left",) if xs > 0 else ("right",))

    # ================= 옥상 =================
    zdeck = ZROOF + .14
    mb.box(X0 + .22, X1 - .22, .22, D - .22, ZROOF, zdeck, "roof_deck")
    cz0, cz1 = ZPAR, ZPAR + .10
    mb.box(X0 - .08, X1 + .08, -.08, .23, cz0, cz1, "granite_light")
    mb.box(X0 - .08, X1 + .08, D - .23, D + .05, cz0, cz1, "granite_light")
    mb.box(X0 - .08, X0 + .23, .23, D - .23, cz0, cz1, "granite_light")
    mb.box(X1 - .23, X1 + .08, .23, D - .23, cz0, cz1, "granite_light")
    # 중앙 박공 장식 + 경사 갓돌
    add_gable(mb, -2.2, 2.2, -.04, .22, cz1, 1.10, "plaster_beige")
    for xa, hw in ((-2.32, .19), (2.32, .185)):      # 폭 5 mm 차이: 꼭짓점에서 두 갓돌 옆면이 같은 평면에 겹치지 않게
        DC.add_beam(mb, (xa, .09, cz1 - .02), (0.0, .09, cz1 + 1.16), hw, .05, "granite_light")
    # 옥탑 계단실 (정면 계단 위, 박공 뒤) # estimated
    px0, px1, py0, py1, ph = -1.50, 1.50, .90, 3.90, 2.40
    zt = zdeck + ph - .20
    tb(mb, px0, px1, py0, py1, zdeck, zt, "wall_main", skip=("bottom",))
    mb.box(px0 - .05, px1 + .05, py0 - .05, py1 + .05, zt, zdeck + ph, "granite_light")
    V.add_rooftop_door(mb, "x", px1, 1, 2.00, 2.90, zdeck, zdeck + 2.02, stage)
    # 물탱크 # estimated
    tx, ty = 4.4, 9.4
    mb.box(tx - .72, tx + .72, ty - .72, ty + .72, zdeck, zdeck + .14, "concrete_light", skip=("bottom",))
    DC.add_oct_tube(mb, (tx, ty, zdeck + .14), (tx, ty, zdeck + 1.50), .56, "stainless", n=12 if stage == 0 else 8)
    V.add_frustum(mb, tx, ty, zdeck + 1.50, zdeck + 1.66, .56, .20, "stainless", n=12 if stage == 0 else 8)

    # 가로 간판 (얇은 3D 판, 앞면 칸 전체 UV)
    for r, (a, b) in ((SIGN_A, (-6.6, -1.2)), (SIGN_B, (1.2, 6.6))):
        K.axbox(mb, "y", 0, -1, a, b, 0, .12, 2.84, 3.40, "iron_dark", skip=("front",))
        mb.quad(K.face_pts("y", -.12, -1, a, b, 2.84, 3.40), sign_uv(atlas, r), "shop_signs")

    if stage == 0:
        # 세로 돌출 간판 (좌측 모서리 미장 기둥, 2~3층 높이, 양면) + 브래킷
        sx0, sx1, sy0, sy1, sz0, sz1 = -6.80, -6.70, -.80, -.14, 4.05, 6.05
        mb.box(sx0, sx1, sy0, sy1, sz0, sz1, "iron_dark", skip=("left", "right"))
        uv = sign_uv(atlas, SIGN_V)
        mb.quad(K.face_pts("x", sx0, -1, sy0, sy1, sz0, sz1), uv, "shop_signs")
        mb.quad(K.face_pts("x", sx1, 1, sy0, sy1, sz0, sz1), uv, "shop_signs")
        for bz in (sz0 + .25, sz1 - .25):
            mb.box(-6.77, -6.73, -.14, -.04, bz - .03, bz + .03, "iron_dark")
        # 창 방범 난간 (정면 큰 창)
        for f in range(NF):
            for a, b, sl, hd, p in FRONT:
                if b - a < 2.0:
                    continue
                DC.add_railing_run(mb, (a - .04, -.12), (b + .04, -.12), zf(f) + sl, .62, stage, reg="iron_dark",
                                   post_step=1.20, picket_step=.145)
        # 실외기: 1층 상가용 측면 바닥 + 후면 층별
        for c, s in ((X0, -1), (X1, 1)):
            DC.add_ac_unit(mb, "x", c, s, 2.20, .10, stage)
            DC.add_ac_unit(mb, "x", c, s, 3.30, .10, stage)
        for f in range(NF):
            DC.add_ac_unit(mb, "y", D, 1, -1.60, zf(f) + .32, stage)
            DC.add_ac_unit(mb, "y", D, 1, 1.60, zf(f) + .32, stage)
        for x in (X0 + .33, X1 - .33):
            DC.add_downspout(mb, "y", D, 1, x, .15, ZPAR - .10)
        # 현관: 문턱·논슬립, 우편함(왼벽), 인터폰(오른벽), 천장등, 번호판(우측 기둥 정면)
        mb.box(ENT[0], ENT[1], ALC_Y - .30, ALC_Y - .002, 0, .036, "concrete_light", skip=("bottom",))
        mb.box(ENT[0] + .02, ENT[1] - .02, ALC_Y - .30, ALC_Y - .265, .036, .044, "stainless", skip=("bottom",))
        K.axbox(mb, "x", -.90, 1, .42, 1.02, 0, .15, 1.0, 1.75, "stainless")
        K.axbox(mb, "x", -.90, 1, .40, 1.04, 0, .18, 1.75, 1.775, "stainless")
        for z in (1.12, 1.34, 1.56):
            K.axbox(mb, "x", -.75, 1, .47, .97, .002, .008, z, z + .025, "iron_dark")
        V.add_intercom(mb, "x", .90, -1, 1.00, 1.24, 1.28, 1.58)
        V.add_ceiling_lamp(mb, -.30, .30, .55, .95, ZG)
        V.decal_plate(mb, "y", 0, -1, 6.715, 6.985, 1.80, 2.02, .014, "address")
        V.ensure_lit_windows(wins, lit, spec.seed + 53)
    return mb, wins


def build_and_export():
    a = build_atlas(SPEC)
    main, wins = build_stage(SPEC, a, 0)
    lod1, _ = build_stage(SPEC, a, 1)
    lod2, _ = build_stage(SPEC, a, 2)
    print(f"[D01] main={main.tri_count} lod1={lod1.tri_count} lod2={lod2.tri_count} windows={len(wins.items)}")
    assert lod1.tri_count < main.tri_count * .5
    assert lod2.tri_count + len(wins.items) * 2 <= 500
    return K.export_asset(SPEC.name, 1, dict(main=main, lod1=lod1, lod2=lod2, windows=wins), a,
                          K.out_dir_from_argv("output"), lod2_tex=512, lot=SPEC.lot, front_yard=SPEC.front_yard,
                          notes=dict(archetype="villa_D_ground_shop", seed=SPEC.seed))


if __name__ == "__main__":
    build_and_export()
