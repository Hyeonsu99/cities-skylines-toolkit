"""고속도로 측주식(路側) 녹색 이정표 — 2주식 강관 지주.

경부고속도로 상행 신탄진IC 앞 예시 (거리값은 예시 문안 # estimated):
  신탄진 Sintanjin 2 km / 청주 Cheongju 23 km / 서울 Seoul 128 km
도로(-Y) 쪽에서 읽는다. 치수 근거는 shape_notes.md.
"""
import os, sys  # noqa: E401
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # Blender --python 은 스크립트 폴더를 path 에 넣지 않는다
from hwprops_common import (K, make_atlas, prism, sign_panel, export, draw_canvas, draw_place, sign_border,
                            _fit_font, _text_at, FONT_EN, SIGN_WHITE)

W, H = 3.60, 2.40               # 판 크기 # estimated
Z0 = 2.00                       # 판 하단 높이 (측주식 하단 1.0 m 이상, 고속도로 갓길 시인성 고려) # estimated
POST_X = (-1.10, 1.10)
POST_R = 0.108                  # φ216.3 강관 # estimated
POST_Y = 0.12
PANEL_Y = (-0.06, 0.0)
ROWS = [("신탄진", "Sintanjin", "2"), ("청주", "Cheongju", "23"), ("서울", "Seoul", "128")]


def _paint_distance(ctx):
    def fn(drw, cw, ch):
        sign_border(drw, cw, ch)
        row_h = ch * 0.30
        for i, (kr, en, km) in enumerate(ROWS):
            y0 = ch * 0.05 + i * row_h
            draw_place(drw, cw * 0.07, y0 + row_h * 0.07, kr, en, row_h * 0.46, int(cw * 0.55))
            f = _fit_font(drw, FONT_EN, km, int(cw * 0.22), int(row_h * 0.62))
            fu = _fit_font(drw, FONT_EN, "km", int(cw * 0.10), int(row_h * 0.36))
            tw = _text_at(drw, cw * 0.80, y0 + row_h * 0.42, km, f, SIGN_WHITE, "r")
            _text_at(drw, cw * 0.82, y0 + row_h * 0.50, "km", fu, SIGN_WHITE, "l")
            if i < len(ROWS) - 1:
                yl = y0 + row_h * 0.98
                drw.line([(cw * 0.05, yl), (cw * 0.95, yl)], fill=SIGN_WHITE, width=max(3, int(ch * 0.008)))
    draw_canvas(ctx, "side_distance", W, H, fn)


A = make_atlas(["concrete", "galv", "sign_back",
                ("sign_distance", dict(color=(0, 112, 74), gloss=0.35, px=1024, painter=_paint_distance))], size=2048)


def build(stage):
    mb = K.MeshBuilder(A)
    sides = (8, 4, 4)[stage]
    z_top = Z0 + H + 0.05
    for px in POST_X:
        mb.box(px - 0.35, px + 0.35, POST_Y - 0.35, POST_Y + 0.35, 0.0, 0.25, "concrete", skip=("bottom",))
        prism(mb, A, (px, POST_Y, 0.25), (px, POST_Y, z_top), POST_R, "galv", sides=sides)
        if stage == 0:
            prism(mb, A, (px, POST_Y, 0.25), (px, POST_Y, 0.31), POST_R * 1.6, "galv", sides=8)   # 베이스 플랜지
    sign_panel(mb, A, -W / 2, W / 2, PANEL_Y[0], PANEL_Y[1], Z0, Z0 + H, "sign_distance")
    if stage == 0:
        for zc in (Z0 + 0.40, Z0 + H - 0.40):   # 판 뒤 수평 형강 → 지주 결속
            mb.box(-W / 2 + 0.15, W / 2 - 0.15, PANEL_Y[1] - 0.005, POST_Y, zc - 0.04, zc + 0.04, "sign_back")
    return mb


export("SignSideDistance", dict(main=build(0), lod1=build(1), lod2=build(2)), A, size_hint=(1, 1),
       notes=dict(panel_m=[W, H], bottom_m=Z0, text=" / ".join(f"{k} {e} {d} km" for k, e, d in ROWS)))
