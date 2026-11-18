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

SPAN = 22.0             # 기둥 중심 간격: 4 x 3.6 m 차로 + 3.0 m 갓길 + 1.0 m 측대 + 여유 # estimated
COL = 0.50              # 각형 강관 기둥 # estimated
Z_COL_TOP = 8.60
TRUSS_Z = (6.30, 7.90)  # 하현·상현재 높이
TRUSS_Y = (-0.45, 0.45)
CH = 0.14               # 현재 단면
SIGN_Z = (5.50, 8.50)   # 판 하단 5.5 m (문형식 하단 높이 5.0 m 이상 확보) # estimated
SIGN_Y = (-0.66, -0.58)
SIGN_L = (-7.40, -0.90)     # 6.5 m
SIGN_R = (0.50, 6.00)       # 5.5 m


def _paint_straight(ctx):
    w, h = SIGN_L[1] - SIGN_L[0], SIGN_Z[1] - SIGN_Z[0]

    def fn(drw, cw, ch):
        sign_border(drw, cw, ch)
        draw_route_shield(drw, cw * 0.11, ch * 0.42, ch * 0.42, "1")
        x = cw * 0.22
        draw_place(drw, x, ch * 0.08, "청주", "Cheongju", ch * 0.22, int(cw * 0.50))
        draw_place(drw, x, ch * 0.52, "서울", "Seoul", ch * 0.22, int(cw * 0.50))
        draw_arrow(drw, cw * 0.86, ch * 0.50, ch * 0.62, "down")
    draw_canvas(ctx, "gantry_straight", w, h, fn)


def _paint_exit(ctx):
    w, h = SIGN_R[1] - SIGN_R[0], SIGN_Z[1] - SIGN_Z[0]

    def fn(drw, cw, ch):
        sign_border(drw, cw, ch)
        x = cw * 0.07
        draw_place(drw, x, ch * 0.08, "신탄진", "Sintanjin", ch * 0.22, int(cw * 0.58))
        draw_place(drw, x, ch * 0.52, "대전", "Daejeon", ch * 0.22, int(cw * 0.58))
        draw_arrow(drw, cw * 0.83, ch * 0.36, ch * 0.46, "upright")
        # 출구 표시: 백색 바탕 녹색 글자 박스
        bx0, bx1, by0, by1 = cw * 0.69, cw * 0.96, ch * 0.66, ch * 0.92
        drw.rounded_rectangle([bx0, by0, bx1, by1], radius=int(ch * 0.03), fill=SIGN_WHITE)
        fk = _fit_font(drw, FONT_KR, "출구", int((bx1 - bx0) * 0.80), int((by1 - by0) * 0.62))
        fe = _fit_font(drw, FONT_EN, "EXIT", int((bx1 - bx0) * 0.80), int((by1 - by0) * 0.34))
        _text_at(drw, (bx0 + bx1) / 2, by0 + (by1 - by0) * 0.36, "출구", fk, SIGN_GREEN, "c")
        _text_at(drw, (bx0 + bx1) / 2, by0 + (by1 - by0) * 0.80, "EXIT", fe, SIGN_GREEN, "c")
    draw_canvas(ctx, "gantry_exit", w, h, fn)


A = make_atlas(["concrete", "gantry_steel", "sign_back",
                ("sign_straight", dict(color=SIGN_GREEN, gloss=0.35, px=1008, painter=_paint_straight)),
                ("sign_exit", dict(color=SIGN_GREEN, gloss=0.35, px=1008, painter=_paint_exit))], size=2048)


def build(stage):
    mb = K.MeshBuilder(A)
    xl, xr = -SPAN / 2, SPAN / 2
    # 기초 페데스탈 + 기둥 + 베이스플레이트
    for xc in (xl, xr):
        mb.box(xc - 0.55, xc + 0.55, -0.55, 0.55, 0.0, 0.60, "concrete", skip=("bottom",))
        if stage == 0:
            mb.box(xc - 0.40, xc + 0.40, -0.40, 0.40, 0.60, 0.63, "gantry_steel", skip=("bottom",))
        mb.box(xc - COL / 2, xc + COL / 2, -COL / 2, COL / 2, 0.60, Z_COL_TOP, "gantry_steel", skip=("bottom", "top"))
    # 트러스 보 (기둥 사이)
    bx0, bx1 = xl + COL / 2, xr - COL / 2
    cx0, cx1 = bx0 - 0.10, bx1 + 0.10       # 현재는 기둥 속까지 넣어 같은 평면 겹침을 피한다
    if stage == 2:
        mb.box(cx0, cx1, TRUSS_Y[0] - CH / 2, TRUSS_Y[1] + CH / 2, TRUSS_Z[0] - CH / 2, TRUSS_Z[1] + CH / 2, "gantry_steel")
    else:
        for yc in TRUSS_Y:
            for zc in TRUSS_Z:
                mb.box(cx0, cx1, yc - CH / 2, yc + CH / 2, zc - CH / 2, zc + CH / 2, "gantry_steel")
        n = 10
        step = (bx1 - bx0) / n
        r = 0.045
        for i in range(n + 1):
            x = bx0 + i * step
            if 0 < i < n:
                for yc in TRUSS_Y:      # 수직재
                    prism(mb, A, (x, yc, TRUSS_Z[0] + CH / 2), (x, yc, TRUSS_Z[1] - CH / 2), r, "gantry_steel", caps=(False, False))
                if stage == 0:          # 상·하 수평 연결재
                    for zc in TRUSS_Z:
                        prism(mb, A, (x, TRUSS_Y[0] + CH / 2, zc), (x, TRUSS_Y[1] - CH / 2, zc), r * 0.8, "gantry_steel", caps=(False, False))
            if stage == 0 and i < n:    # 앞·뒤 사재 (와렌 트러스)
                xa, xb = (x, x + step) if i % 2 == 0 else (x + step, x)
                for yc in TRUSS_Y:
                    prism(mb, A, (xa, yc, TRUSS_Z[0] + CH / 2), (xb, yc, TRUSS_Z[1] - CH / 2), r * 0.9, "gantry_steel", caps=(False, False))
    # 기둥 머리 캡
    for xc in (xl, xr):
        mb.box(xc - 0.32, xc + 0.32, -0.62, 0.62, Z_COL_TOP, Z_COL_TOP + 0.04, "gantry_steel")
        mb.box(xc - COL / 2 - 0.03, xc + COL / 2 + 0.03, -0.55, 0.55, TRUSS_Z[0] - 0.12, TRUSS_Z[1] + 0.12, "gantry_steel")
    # 표지판 + 뒤쪽 가로 보강재(판 → 트러스 앞 현재)
    for (sx0, sx1), tag in ((SIGN_L, "sign_straight"), (SIGN_R, "sign_exit")):
        sign_panel(mb, A, sx0, sx1, SIGN_Y[0], SIGN_Y[1], SIGN_Z[0], SIGN_Z[1], tag)
        if stage < 2:
            for zc in TRUSS_Z:
                mb.box(sx0 + 0.15, sx1 - 0.15, SIGN_Y[1] - 0.005, TRUSS_Y[0], zc - 0.05, zc + 0.05, "gantry_steel")
            if stage == 0:
                for zc in (SIGN_Z[0] + 0.35, SIGN_Z[1] - 0.35):     # 판 뒤 수평 형강 2줄
                    mb.box(sx0 + 0.10, sx1 - 0.10, SIGN_Y[1] - 0.005, SIGN_Y[1] + 0.06, zc - 0.04, zc + 0.04, "sign_back")
    return mb


export("SignGantry", dict(main=build(0), lod1=build(1), lod2=build(2)), A, size_hint=(3, 1),
       notes=dict(span_m=SPAN, sign_bottom_m=SIGN_Z[0], text="청주 Cheongju / 서울 Seoul | 신탄진 Sintanjin / 대전 Daejeon 출구"))
