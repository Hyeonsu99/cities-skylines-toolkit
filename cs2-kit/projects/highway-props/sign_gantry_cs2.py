"""고속도로 문형식(갠트리) 녹색 안내표지 — 편도 4차로 + 갓길 횡단.

경부고속도로 상행(서울 방향) 신탄진IC 진출부 예시:
  왼쪽 판(직진): 노선표지 1 + 청주 Cheongju / 서울 Seoul + 차로지정 ↓
  오른쪽 판(진출): 신탄진 Sintanjin / 대전 Daejeon + ↗ + 출구 EXIT
도로(-Y) 쪽에서 읽는다. 치수 근거는 shape_notes.md.
"""
import os, sys  # noqa: E401
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # Blender --python 은 스크립트 폴더를 path 에 넣지 않는다
from hwprops_common import (K, make_atlas, prism, sign_panel, export, draw_canvas, draw_route_shield,
                            draw_arrow, draw_place, sign_border, _fit_font, _text_at, FONT_KR, FONT_EN,
                            SIGN_GREEN, SIGN_WHITE)

SPAN = 22.0             # 기둥 중심 간격: 4 x 3.6 m 차로 + 3.0 m 갓길 + 1.0 m 측대 + 여유
COL_R = 0.165           # 복열 원형 강관 지주 반지름 (φ330 급)
COL_YS = (-0.30, 0.30)  # 전/후 복열 지주 중심선
Z_COL_TOP = 8.65
TRUSS_Z = (6.30, 7.90)  # 하현·상현재 높이
TRUSS_Y = (-0.42, 0.42)
CH_R = 0.098            # 원형 현재 파이프 반지름
SIGN_Z = (5.50, 8.50)   # 판 하단 5.5 m
SIGN_Y = (-0.64, -0.56)
SIGN_L = (-7.40, -0.90)     # 6.5 m
SIGN_R = (0.50, 6.00)       # 5.5 m


def _paint_straight(ctx):
    w, h = SIGN_L[1] - SIGN_L[0], SIGN_Z[1] - SIGN_Z[0]

    def fn(drw, cw, ch):
        sign_border(drw, cw, ch)
        draw_route_shield(drw, cw * 0.11, ch * 0.42, ch * 0.42, "1")
        x = cw * 0.22
        draw_place(drw, x, ch * 0.10, "청주", "Cheongju", ch * 0.22, int(cw * 0.50))
        draw_place(drw, x, ch * 0.54, "서울", "Seoul", ch * 0.22, int(cw * 0.50))
        draw_arrow(drw, cw * 0.86, ch * 0.50, ch * 0.62, "down")
    draw_canvas(ctx, "gantry_straight", w, h, fn)


def _paint_exit(ctx):
    w, h = SIGN_R[1] - SIGN_R[0], SIGN_Z[1] - SIGN_Z[0]

    def fn(drw, cw, ch):
        sign_border(drw, cw, ch)
        x = cw * 0.07
        draw_place(drw, x, ch * 0.10, "신탄진", "Sintanjin", ch * 0.22, int(cw * 0.58))
        draw_place(drw, x, ch * 0.54, "대전", "Daejeon", ch * 0.22, int(cw * 0.58))
        draw_arrow(drw, cw * 0.83, ch * 0.36, ch * 0.46, "upright")
        bx0, bx1, by0, by1 = cw * 0.68, cw * 0.955, ch * 0.65, ch * 0.915
        drw.rounded_rectangle([bx0, by0, bx1, by1], radius=int(ch * 0.032), fill=SIGN_WHITE)
        fk = _fit_font(drw, FONT_KR, "출구", int((bx1 - bx0) * 0.80), int((by1 - by0) * 0.62))
        fe = _fit_font(drw, FONT_EN, "EXIT", int((bx1 - bx0) * 0.80), int((by1 - by0) * 0.34))
        _text_at(drw, (bx0 + bx1) / 2, by0 + (by1 - by0) * 0.36, "출구", fk, SIGN_GREEN, "c")
        _text_at(drw, (bx0 + bx1) / 2, by0 + (by1 - by0) * 0.80, "EXIT", fe, SIGN_GREEN, "c")
    draw_canvas(ctx, "gantry_exit", w, h, fn)


A = make_atlas(["concrete", "gantry_steel", "sign_back",
                ("sign_straight", dict(color=SIGN_GREEN, gloss=0.40, px=960, painter=_paint_straight,
                                       normal_strength=1.2)),
                ("sign_exit", dict(color=SIGN_GREEN, gloss=0.40, px=960, painter=_paint_exit,
                                   normal_strength=1.2))], size=2048)


def build(stage):
    mb = K.MeshBuilder(A)
    if stage == 2:
        mb.split_tiles = False
    xl, xr = -SPAN / 2, SPAN / 2
    # 기초 페데스탈 + 베이스플레이트 + 앵커볼트 + 복열 원형 강관 지주 (실사진 sign_gantry_03 재현)
    for xc in (xl, xr):
        mb.box(xc - 0.52, xc + 0.52, -0.60, 0.60, 0.0, 0.60, "concrete", skip=("bottom",))
        if stage == 2:
            mb.box(xc - 0.25, xc + 0.25, -0.42, 0.42, 0.60, Z_COL_TOP, "gantry_steel", skip=("bottom",))
            continue
        if stage == 0:
            mb.box(xc - 0.32, xc + 0.32, -0.52, 0.52, 0.60, 0.635, "gantry_steel", skip=("bottom",))
            for dx in (-0.24, 0.24):
                for dy in (-0.45, 0.45):
                    mb.box(xc + dx - 0.022, xc + dx + 0.022, dy - 0.022, dy + 0.022, 0.635, 0.67, "gantry_steel", skip=("bottom",))
            for zt in (1.5, 2.8, 4.1, 5.4):  # 전후 지주 연결 타이 리브 (5단)
                mb.box(xc - 0.05, xc + 0.05, COL_YS[0], COL_YS[1], zt - 0.018, zt + 0.018, "gantry_steel")
        for yc in COL_YS:
            prism(mb, A, (xc, yc, 0.60), (xc, yc, Z_COL_TOP), COL_R, "gantry_steel",
                  sides=8 if stage == 0 else 4, caps=(False, False), tiled=stage == 0, max_stacks=2)
        mb.box(xc - 0.28, xc + 0.28, -0.52, 0.52, Z_COL_TOP, Z_COL_TOP + 0.05, "gantry_steel")
        # 트러스 접합부 볼트 거셋 새들
        mb.box(xc - 0.26, xc + 0.26, -0.50, 0.50, TRUSS_Z[0] - 0.14, TRUSS_Z[1] + 0.14, "gantry_steel")

    bx0, bx1 = xl + 0.26, xr - 0.26
    cx0, cx1 = bx0 - 0.08, bx1 + 0.08
    if stage == 2:
        mb.box(cx0, cx1, TRUSS_Y[0] - CH_R, TRUSS_Y[1] + CH_R, TRUSS_Z[0] - CH_R, TRUSS_Z[1] + CH_R, "gantry_steel")
    else:
        # 상·하현재 원형/육각 강관 + 중앙 스플라이스 볼트 플랜지 칼라
        for yc in TRUSS_Y:
            for zc in TRUSS_Z:
                prism(mb, A, (cx0, yc, zc), (cx1, yc, zc), CH_R, "gantry_steel",
                      sides=6 if stage == 0 else 4, caps=(False, False), tiled=stage == 0, max_stacks=2)
                if stage == 0:
                    prism(mb, A, (-0.08, yc, zc), (0.08, yc, zc), CH_R * 1.45, "gantry_steel",
                          sides=6, caps=(True, True), tiled=False)
        # 와렌(Warren) 트러스 사재 (\ / \ /) — 실제 용접 거셋처럼 절점 0.07 m 이격해 겹침(coplanar) 제거
        n = 14 if stage == 0 else 6
        step = (bx1 - bx0) / n
        r_brace = 0.048
        gap = 0.075
        za_brace, zb_brace = TRUSS_Z[0] + CH_R * 0.55, TRUSS_Z[1] - CH_R * 0.55
        for i in range(n):
            x = bx0 + i * step
            xa, xb = (x + gap, x + step - gap) if i % 2 == 0 else (x + step - gap, x + gap)
            for yc in TRUSS_Y:
                prism(mb, A, (xa, yc, za_brace), (xb, yc, zb_brace), r_brace,
                      "gantry_steel", sides=4, caps=(False, False), tiled=False)
            if stage == 0 and i % 2 == 0 and i > 0:     # 2경간마다 상·하 수평 브레이스 (평면 비틀림 방지)
                for zc in TRUSS_Z:
                    prism(mb, A, (x, TRUSS_Y[0], zc), (x, TRUSS_Y[1], zc), r_brace * 0.75,
                          "gantry_steel", sides=4, caps=(False, False), tiled=False)
        if stage == 0:
            # 상단 보수점검 난간 (전후 레일 + 기둥 9쌍) + 우측 지주 사다리 (하단 닫힘 caps=(True, True))
            rx0, rx1 = xl + 0.35, xr - 0.35
            for yc in TRUSS_Y:
                for zr in (TRUSS_Z[1] + 0.50, TRUSS_Z[1] + 0.92):
                    prism(mb, A, (rx0, yc, zr), (rx1, yc, zr), 0.020, "gantry_steel", sides=4, caps=(True, True), tiled=False)
                for k in range(9):
                    xp = rx0 + (rx1 - rx0) * (k / 8.0)
                    prism(mb, A, (xp, yc, TRUSS_Z[1]), (xp, yc, TRUSS_Z[1] + 0.92), 0.020,
                          "gantry_steel", sides=4, caps=(False, True), tiled=False)
            lx = xr + 0.32
            for ly in (-0.18, 0.18):
                prism(mb, A, (lx, ly, 2.3), (lx, ly, Z_COL_TOP + 0.25), 0.018, "gantry_steel", sides=4, caps=(True, True), tiled=False)
            for zr in range(3, 9):
                prism(mb, A, (lx, -0.18, zr - 0.3), (lx, 0.18, zr - 0.3), 0.014, "gantry_steel", sides=4, caps=(False, False), tiled=False)

    # 표지판 + 뒤쪽 수평 C채널 3줄 + 수직 행거 브래킷 (실사진 sign_gantry_04·sign_side_04 재현)
    for (sx0, sx1), tag in ((SIGN_L, "sign_straight"), (SIGN_R, "sign_exit")):
        sign_panel(mb, A, sx0, sx1, SIGN_Y[0], SIGN_Y[1], SIGN_Z[0], SIGN_Z[1], tag)
        if stage < 2:
            for zc in TRUSS_Z:
                mb.box(sx0 + 0.20, sx1 - 0.20, SIGN_Y[1] - 0.004, TRUSS_Y[0], zc - 0.045, zc + 0.045, "gantry_steel")
            if stage == 0:
                for zc in (SIGN_Z[0] + 0.30, 7.00, SIGN_Z[1] - 0.30):
                    mb.box(sx0 + 0.12, sx1 - 0.12, SIGN_Y[1] - 0.004, SIGN_Y[1] + 0.055, zc - 0.038, zc + 0.038, "sign_back")
                for hx in (sx0 + 0.85, (sx0 + sx1) * 0.5, sx1 - 0.85):
                    mb.box(hx - 0.04, hx + 0.04, SIGN_Y[1] + 0.01, SIGN_Y[1] + 0.075, SIGN_Z[0] + 0.20, SIGN_Z[1] - 0.20, "gantry_steel")
    return mb


export("SignGantry", dict(main=build(0), lod1=build(1), lod2=build(2)), A, size_hint=(3, 1),
       notes=dict(span_m=SPAN, sign_bottom_m=SIGN_Z[0], text="청주 Cheongju / 서울 Seoul | 신탄진 Sintanjin / 대전 Daejeon 출구"))
