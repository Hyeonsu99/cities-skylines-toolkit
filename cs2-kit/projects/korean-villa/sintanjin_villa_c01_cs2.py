# -*- coding: utf-8 -*-
"""신탄진형 다세대 빌라 C01 대표형: 흰 미장 + 정면 수직 돌출창 2열 + 1층 필로티, 5층(필로티+주거 4개 층).

STYLE_BRIEF 5.3 프리셋 C (v02 돌출 창대, v08 5층, v20/v23 돌출 발코니창, user_ref 우측 흰 미장).
A(적갈 벽돌·흰 띠)·B(차콜 벽돌·평면) 와 다른 점: 흰 미장 매스, 정면 0.6 m 수직 돌출창 매스 2열과 층별 화강석 창대 띠,
다크 알루미늄 창틀 + 스텐 난간, 계단형(중앙 상승) 파라펫, 우측면 후면 계단실 수직 유리, 3면 주차 + 보행 통로.
공동현관은 B01 11/24 피드백 기준대로 주차 후면 벽(y=rear) 라인에 두고 정면으로 돌출시키지 않는다.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import villa_core as V

K, DC, KX = V.K, V.DC, V.KX
SPEC = V.VillaSpec(name="SintanjinVillaC01", lot=(2, 3), width=12.4, depth=12.4,
                   z_pil=2.45, n_upper=4, road_no="45", seed=23)

X0, X1, D, REAR = -6.2, 6.2, 12.4, 8.0
ZP, ZU = 2.45, 3.10
NF = 4
ZROOF = 3.0 + NF * 2.8                      # 14.20 옥상 슬래브선
ZPAR = ZROOF + 0.90
BAYS = ((-5.0, -2.0), (2.0, 5.0))           # 정면 수직 돌출창 매스 # estimated (v20/v23 돌출창 폭 비례)
P = 0.60                                    # 돌출 깊이 (브리프 0.60~0.90)
COL_X = (-5.95, -2.95, 0.05, 3.05, 5.95)
COL_Y = (0.25, 5.70)
ENT = (3.90, 5.10, 0.02, 2.24)              # 공동현관: 우측 보행 통로 끝 후면 벽
SVC = (9.60, 10.50, 0.02, 2.10)             # 보조문: 후면실 좌측 벽
STAIR = (9.05, 10.45)                       # 우측면 계단실 수직 유리 띠 (y)

FRONT_C = [(-0.60, 0.60, 1.20, 2.28, 2)]
BAY_W = [(0.35, 2.30)]                      # 돌출창 앞면: 낮은 창대 확장형 창 (브리프 0.45~0.60)
LEFT = [(1.20, 3.40, .90, 2.28, 3), (4.80, 5.90, 1.20, 2.28, 2), (7.40, 9.60, .90, 2.28, 3),
        (10.40, 11.50, 1.20, 2.28, 2)]
RIGHT = [(1.20, 3.40, .90, 2.28, 3), (4.80, 5.90, 1.20, 2.28, 2), (6.90, 8.00, 1.20, 2.28, 2),
         (11.00, 11.90, 1.20, 2.28, 2)]
BACK = [(-4.90, -2.70, .90, 2.28, 3), (-1.00, .20, 1.20, 2.28, 2), (2.30, 4.50, .90, 2.28, 3)]


def zf(f):
    return 3.0 + 2.8 * f


def holes_for(hs, f):
    return [(a, b, zf(f) + s, zf(f) + h, "window", f + 1, p) for a, b, s, h, p in hs]


def bay_holes(b0, b1, f):
    return [(b0 + .35, b1 - .35, zf(f) + .55, zf(f) + 2.30, "window", f + 1, 3)]


def build_stage(spec, atlas, stage):
    mb, wins = K.MeshBuilder(atlas, split_tiles=stage == 0), K.WindowSet()
    rh = DC.add_recessed_wall
    lit = []
    cols = [(x, y) for x in COL_X for y in COL_Y]

    # ================= LOD2 =================
    if stage == 2:
        for x, y in ((COL_X[0], COL_Y[0]), (COL_X[-1], COL_Y[0])):
            mb.box(x - .25, x + .25, y - .25, y + .25, 0, ZP, "granite_light", skip=("bottom",))
        mb.box(X0, X1, REAR, D, 0, ZP, "wall_main", skip=("bottom",))
        mb.box(X0 - .08, X1 + .08, -.08, D + .08, ZP, ZU, "granite_light")
        mb.box(X0, X1, 0, D, ZU, ZPAR, "wall_main", skip=("bottom",))
        for b0, b1 in BAYS:
            mb.box(b0, b1, -P, 0, ZU, ZPAR, "wall_main", skip=("back",))
        mb.box(3.30, 5.75, 8.40, 11.40, ZPAR, ZROOF + 2.55, "wall_main", skip=("bottom",))
        mb.box(-2.0, 2.0, 0, .22, ZPAR, ZPAR + .65, "wall_main", skip=("bottom",))
        K.paint(mb, "y", REAR, -1, ENT[0], ENT[1], ENT[2], ENT[3], "window_backing")
        K.paint(mb, "x", X1, 1, STAIR[0] + .1, STAIR[1] - .1, ZU + .2, ZROOF - .2, "window_backing")
        for f in range(NF):
            for axis, c, s, hs in (("y", 0, -1, FRONT_C), ("x", X0, -1, LEFT), ("x", X1, 1, RIGHT),
                                   ("y", D, 1, BACK)):
                for a, b, sl, hd, _ in hs:
                    K.paint(mb, axis, c, s, a, b, zf(f) + sl, zf(f) + hd, "window_backing")
            for b0, b1 in BAYS:
                K.paint(mb, "y", -P, -1, b0 + .35, b1 - .35, zf(f) + .55, zf(f) + 2.30, "window_backing")
        return mb, wins

    # ================= 1층 필로티 =================
    for x, y in cols:
        if stage == 0:
            KX.bevel_box(mb, x - .25, x + .25, y - .25, y + .25, 0, ZP, "granite_light", bevel=.018)
        else:
            mb.box(x - .25, x + .25, y - .25, y + .25, 0, ZP, "granite_light", skip=("bottom",))
    # 후면실(주차 뒤 벽): 공동현관 + 창, 좌측 보조문, 우측·후면 창
    V.wall_with_doors(mb, wins, "y", REAR, -1, X0, X1, 0, ZP, "wall_main",
                      [(-4.60, -3.60, 1.20, 2.05, "window", 0, 2), (-0.90, 0.10, 1.20, 2.05, "window", 0, 2)],
                      stage, 41, [ENT])
    V.add_glass_entry_door(mb, wins, "y", REAR, -1, *ENT, stage, unit=113, lit=lit)
    V.wall_with_doors(mb, wins, "x", X0, -1, REAR + .22, D - .22, 0, ZP, "wall_main", [], stage, 43, [SVC])
    V.add_steel_door(mb, "x", X0, -1, *SVC, stage)
    rh(mb, wins, "x", X1, 1, REAR + .22, D - .22, 0, ZP, "wall_main",
       [(9.40, 10.40, 1.25, 2.05, "window", 0, 2)], stage, 45)
    rh(mb, wins, "y", D, 1, X0, X1, 0, ZP, "wall_main",
       [(-4.2, -3.1, 1.25, 2.05, "window", 0, 2), (2.6, 3.7, 1.25, 2.05, "window", 0, 2)], stage, 47)
    mb.box(X0 + .24, X1 - .24, REAR + .24, D - .24, 0, ZP - .01, "concrete_light", skip=("bottom",))

    # 필로티 슬래브 띠 (모서리 감싸는 한 덩어리) + 돌출창 아래 슬래브 연장 (밑면 닫힘)
    mb.box(X0 - .08, X1 + .08, -.08, D + .08, ZP, ZU, "granite_light")
    for b0, b1 in BAYS:
        mb.box(b0 - .08, b1 + .08, -P - .08, -.08, ZP, ZU, "granite_light")

    # ================= 2~5층 =================
    # 정면 본체: 돌출창 사이 3구간 (돌출창 구간은 돌출 매스가 대신 막음)
    segs = [(X0, BAYS[0][0]), (BAYS[0][1], BAYS[1][0]), (BAYS[1][1], X1)]
    for k, (a, b) in enumerate(segs):
        hs = [h for f in range(NF) for h in holes_for(FRONT_C, f)] if k == 1 else []
        rh(mb, wins, "y", 0, -1, a, b, ZU, ZPAR, "wall_main", hs, stage, 50 + k, sash_reg="sash_dark")
    for j, (b0, b1) in enumerate(BAYS):
        rh(mb, wins, "y", -P, -1, b0, b1, ZU, ZROOF, "wall_main",
           [h for f in range(NF) for h in bay_holes(b0, b1, f)], stage, 60 + j, sash_reg="sash_dark")
        rh(mb, wins, "x", b0, -1, -P + .22, 0, ZU, ZROOF, "wall_main", [], stage, 62 + j)
        rh(mb, wins, "x", b1, 1, -P + .22, 0, ZU, ZROOF, "wall_main", [], stage, 64 + j)
        # 돌출창 상부 파라펫 (속이 찬 미장 블록) + 내부 막음
        DC._world_tiled_box(mb, b0, b1, -P, .219, ZROOF, ZPAR, "wall_main", skip=("top",))
        mb.box(b0 + .24, b1 - .24, -P + .24, .24, ZU + .01, ZROOF, "wall_main", skip=("top",))
        # 층별 화강석 창대 띠 (돌출 매스 3면 감쌈, 본체 벽에 맞대기)
        for f in range(1, NF):
            mb.box(b0 - .05, b1 + .05, -P - .05, 0, zf(f) - .08, zf(f) + .10, "granite_light", skip=("back",))
    # 좌·우·후면
    rh(mb, wins, "x", X0, -1, .22, D - .22, ZU, ZPAR, "wall_main",
       [h for f in range(NF) for h in holes_for(LEFT, f)], stage, 70, sash_reg="sash_dark")
    w_pre = len(wins.items)
    rh(mb, wins, "x", X1, 1, .22, D - .22, ZU, ZPAR, "wall_main",
       [h for f in range(NF) for h in holes_for(RIGHT, f)] +
       [(STAIR[0], STAIR[1], ZU + .12, ZROOF - .10, "window", 1, 1)], stage, 71, sash_reg="sash_dark")
    if stage == 0:
        # 우측 계단실 수직 유리: 단일 유리 → 층별 4장 발광 패널 (반층 계단참 멀리언 앞)
        idx = [i for i in range(w_pre, len(wins.items)) if wins.items[i]["hh"] > 5.0]
        for i in sorted(idx, reverse=True):
            wins.items.pop(i)
        g0, g1 = STAIR[0] + .076, STAIR[1] - .076
        bounds = [ZU + .20] + [zf(f) - .03 for f in range(1, NF)] + [ZROOF - .18]
        for sf in range(NF):
            gz0 = bounds[sf] + (.03 if sf else 0)
            gz1 = bounds[sf + 1] - (.03 if sf < NF - 1 else 0)
            wins.add_face("x", X1 - .145, 1, g0, g1, gz0, gz1, sf + 1, 120 + sf)
            wins.items[-1]["pts2"] = K.face_pts("x", X1 + .025, 1, STAIR[0] + .05, STAIR[1] - .05, gz0, gz1)
            lit.append(len(wins.items) - 1)
        for z in [zf(f) + .95 for f in range(NF)] + [zf(f) for f in range(1, NF)]:
            K.axbox(mb, "x", X1, 1, STAIR[0] + .10, STAIR[1] - .10, -.115, -.02, z - .03, z + .025, "sash_dark")
    rh(mb, wins, "y", D, 1, X0, X1, ZU, ZPAR, "wall_main",
       [h for f in range(NF) for h in holes_for(BACK, f)], stage, 72, sash_reg="sash_dark")
    mb.box(X0 + .24, X1 - .24, .24, D - .24, ZU + .01, ZROOF, "wall_main", skip=("top",))

    # ================= 옥상 =================
    zdeck = ZROOF + .14
    mb.box(X0 + .219, X1 - .219, .219, D - .219, ZROOF, zdeck, "roof_deck")
    cz0, cz1 = ZPAR, ZPAR + .10
    mb.box(X0 - .05, X1 + .05, -.05, .23, cz0, cz1, "granite_light")
    mb.box(X0 - .05, X1 + .05, D - .23, D + .05, cz0, cz1, "granite_light")
    mb.box(X0 - .05, X0 + .23, .23, D - .23, cz0, cz1, "granite_light")
    mb.box(X1 - .23, X1 + .05, .23, D - .23, cz0, cz1, "granite_light")
    for b0, b1 in BAYS:
        mb.box(b0 - .05, b1 + .05, -P - .05, -.05, cz0, cz1, "granite_light")
    # 계단형 파라펫: 정면 중앙 상승부 (규칙 8: 갓돌이 모서리를 감쌈)
    DC._world_tiled_box(mb, -2.0, 2.0, 0.0, .22, cz1, cz1 + .55, "wall_main", skip=("bottom",))
    mb.box(-2.05, 2.05, -.05, .27, cz1 + .55, cz1 + .65, "granite_light")
    # 옥탑 계단실 (우측 후면 계단 위) # estimated
    px0, px1, py0, py1, ph = 3.30, 5.75, 8.40, 11.40, 2.40
    zt = zdeck + ph - .20
    DC._world_tiled_box(mb, px0, px1, py0, py1, zdeck, zt, "wall_main", skip=("bottom",))
    mb.box(px0 - .05, px1 + .05, py0 - .05, py1 + .05, zt, zdeck + ph, "granite_light")
    V.add_rooftop_door(mb, "x", px0, -1, 9.40, 10.30, zdeck, zdeck + 2.02, stage)
    # 물탱크 (스텐 원통 + 패드) # estimated
    tx, ty = -3.6, 9.4
    mb.box(tx - .72, tx + .72, ty - .72, ty + .72, zdeck, zdeck + .14, "concrete_light", skip=("bottom",))
    DC.add_oct_tube(mb, (tx, ty, zdeck + .14), (tx, ty, zdeck + 1.50), .56, "stainless", n=12 if stage == 0 else 8)
    V.add_frustum(mb, tx, ty, zdeck + 1.50, zdeck + 1.66, .56, .20, "stainless", n=12 if stage == 0 else 8)

    if stage == 0:
        # 돌출창 스텐 파이프 난간 (창대 0.55 → 높이 0.75, 유리 앞 0.16)
        for b0, b1 in BAYS:
            for f in range(NF):
                z = zf(f) + .55
                o = -P - .16
                DC.add_railing_run(mb, (b0 + .31, o), (b1 - .31, o), z, .75, stage, reg="stainless",
                                   post_step=1.15, picket_step=.12)
        # 큰 창 다크 철제 낮은 방범 난간 (좌측·후면)
        for axis, c, s, hs in (("x", X0, -1, LEFT), ("y", D, 1, BACK)):
            for f in range(NF):
                for a, b, sl, hd, p in hs:
                    if p != 3:
                        continue
                    o = c + s * .16
                    p0, p1 = ((a, o), (b, o)) if axis == "y" else ((o, a), (o, b))
                    DC.add_railing_run(mb, p0, p1, zf(f) + sl, .62, stage, reg="iron_dark",
                                       post_step=1.15, picket_step=.14)
        # 실외기: 좌측면 작은 창 아래 + 후면 + 1층 후면실 옆
        for f in range(NF):
            DC.add_ac_unit(mb, "x", X0, -1, 6.60, zf(f) + .30, stage)
            DC.add_ac_unit(mb, "y", D, 1, 1.30, zf(f) + .32, stage)
        DC.add_ac_unit(mb, "y", REAR, -1, -2.20, .10, stage)
        # 우수관: 후면 양 모서리
        for x in (X0 + .33, X1 - .33):
            DC.add_downspout(mb, "y", D, 1, x, .15, ZPAR - .10)
        # 기둥 충돌방지 띠 · 번호판 · 카스토퍼 · 천장등
        for x, y in cols:
            V.decal_plate(mb, "y", y - .25, -1, x - .21, x + .21, .35, 1.15, .005, "bumper")
        V.decal_plate(mb, "y", 0, -1, COL_X[3] - .135, COL_X[3] + .135, 1.80, 2.02, .014, "address")
        for x in (-4.45, -1.45, 1.55):
            mb.box(x - .60, x + .60, 6.90, 7.08, 0, .12, "stopper", skip=("bottom",))
            V.add_ceiling_lamp(mb, x - .32, x + .32, 1.15, 1.55, ZP)
            V.add_ceiling_lamp(mb, x - .32, x + .32, 4.25, 4.60, ZP)
        for ly in (1.30, 4.30, REAR - .70):
            V.add_ceiling_lamp(mb, 4.20, 4.80, ly, ly + .40, ZP)
        # 공동현관: 문턱·논슬립, 인터폰(문 오른쪽), 우편함(문 왼쪽 벽)
        mb.box(ENT[0], ENT[1], REAR - .30, REAR - .002, 0, .036, "concrete_light", skip=("bottom",))
        mb.box(ENT[0] + .02, ENT[1] - .02, REAR - .30, REAR - .265, .036, .044, "stainless", skip=("bottom",))
        V.add_intercom(mb, "y", REAR, -1, ENT[1] + .16, ENT[1] + .40, 1.28, 1.58)
        K.axbox(mb, "y", REAR, -1, ENT[0] - .80, ENT[0] - .20, 0, .15, 1.0, 1.75, "stainless")
        K.axbox(mb, "y", REAR, -1, ENT[0] - .82, ENT[0] - .18, 0, .18, 1.75, 1.775, "stainless")
        for z in (1.12, 1.34, 1.56):
            K.axbox(mb, "y", REAR - .15, -1, ENT[0] - .75, ENT[0] - .25, .002, .008, z, z + .025, "iron_dark")
        V.ensure_lit_windows(wins, lit, spec.seed + 53)
    return mb, wins


def build_and_export():
    a = V.build_atlas(SPEC, wall="stucco_white")
    main, wins = build_stage(SPEC, a, 0)
    lod1, _ = build_stage(SPEC, a, 1)
    lod2, _ = build_stage(SPEC, a, 2)
    print(f"[C01] main={main.tri_count} lod1={lod1.tri_count} lod2={lod2.tri_count} windows={len(wins.items)}")
    assert lod1.tri_count < main.tri_count * .5
    assert lod2.tri_count + len(wins.items) * 2 <= 500
    return K.export_asset(SPEC.name, 1, dict(main=main, lod1=lod1, lod2=lod2, windows=wins), a,
                          K.out_dir_from_argv("output"), lod2_tex=512, lot=SPEC.lot, front_yard=SPEC.front_yard,
                          notes=dict(archetype="villa_C_white_stucco_bay_piloti", seed=SPEC.seed))


if __name__ == "__main__":
    build_and_export()
