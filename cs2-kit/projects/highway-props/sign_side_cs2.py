"""고속도로 측주식(路側) 녹색 이정표 — 2주식 강관 지주.

경부고속도로 상행 신탄진IC 앞 예시 (거리값은 예시 문안 # estimated):
  신탄진 Sintanjin 2 km / 청주 Cheongju 23 km / 서울 Seoul 128 km
도로(-Y) 쪽에서 읽는다. 치수 근거는 shape_notes.md.
"""
import os, sys  # noqa: E401
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # Blender --python 은 스크립트 폴더를 path 에 넣지 않는다
from hwprops_common import (K, make_atlas, prism, sign_panel, export, draw_canvas, draw_place, sign_border,
                            _fit_font, _text_at, FONT_EN, SIGN_GREEN, SIGN_WHITE)

W, H = 3.60, 2.40               # 판 크기
Z0 = 2.00                       # 판 하단 높이
POST_X = (-1.10, 1.10)
POST_R = 0.108                  # φ216.3 원형 강관
POST_Y = 0.14
PANEL_Y = (-0.06, 0.0)
ROWS = [("신탄진", "Sintanjin", "2"), ("청주", "Cheongju", "23"), ("서울", "Seoul", "128")]
BACK_RAILS_Z = (Z0 + 0.28, Z0 + 0.90, Z0 + 1.50, Z0 + 2.12)


def _paint_distance(ctx):
    def fn(drw, cw, ch):
        sign_border(drw, cw, ch)
        row_h = ch * 0.295
        widest = max((r[2] for r in ROWS), key=len)          # 숫자 크기는 가장 긴 값 기준으로 세 행 공통
        f = _fit_font(drw, FONT_EN, widest, int(cw * 0.22), int(row_h * 0.64))
        fu = _fit_font(drw, FONT_EN, "km", int(cw * 0.10), int(row_h * 0.36))
        for i, (kr, en, km) in enumerate(ROWS):
            y0 = ch * 0.055 + i * row_h
            draw_place(drw, cw * 0.065, y0 + row_h * 0.06, kr, en, row_h * 0.45, int(cw * 0.56))
            base = y0 + row_h * 0.68                         # 숫자·km 공통 기준선
            drw.text((cw * 0.80, base), km, font=f, fill=SIGN_WHITE, anchor="rs")
            drw.text((cw * 0.82, base), "km", font=fu, fill=SIGN_WHITE, anchor="ls")
            if i < len(ROWS) - 1:
                yl = y0 + row_h * 0.96
                drw.line([(cw * 0.055, yl), (cw * 0.945, yl)], fill=SIGN_WHITE, width=max(4, int(ch * 0.010)))
    draw_canvas(ctx, "side_distance", W, H, fn)


A = make_atlas(["concrete", "galv", "sign_back",
                ("sign_distance", dict(color=SIGN_GREEN, gloss=0.40, px=1024, painter=_paint_distance,
                                       normal_strength=1.2))], size=2048)


def build(stage):
    mb = K.MeshBuilder(A)
    if stage == 2:
        mb.split_tiles = False
    sides = (8, 4, 4)[stage]
    z_top = Z0 + H + 0.08
    for px in POST_X:
        mb.box(px - 0.36, px + 0.36, POST_Y - 0.36, POST_Y + 0.36, 0.0, 0.25, "concrete", skip=("bottom",))
        prism(mb, A, (px, POST_Y, 0.25), (px, POST_Y, z_top), POST_R, "galv", sides=sides, tiled=stage == 0)
        if stage == 0:
            # 원형 베이스 플랜지 + 앵커 너트 쌍 + 지주 상단 빗물 캡 (caps=(True, True))
            prism(mb, A, (px, POST_Y, 0.25), (px, POST_Y, 0.295), POST_R * 1.65, "galv", sides=8, caps=(True, True), tiled=False)
            for dx in (-0.13, 0.13):
                mb.box(px + dx - 0.018, px + dx + 0.018, POST_Y - 0.020, POST_Y + 0.020,
                       0.295, 0.325, "galv", skip=("bottom",))
            prism(mb, A, (px, POST_Y, z_top), (px, POST_Y, z_top + 0.035), POST_R * 1.15, "galv", sides=8, caps=(True, True), tiled=False)
    sign_panel(mb, A, -W / 2, W / 2, PANEL_Y[0], PANEL_Y[1], Z0, Z0 + H, "sign_distance")
    if stage == 0:
        # 뒷면 수평 알루미늄 C채널 4단 + 상/하 주가로보U볼트 클램프 칼라 (4곳)
        for idx, zc in enumerate(BACK_RAILS_Z):
            mb.box(-W / 2 + 0.12, W / 2 - 0.12, PANEL_Y[1] - 0.004, POST_Y - POST_R * 0.72,
                   zc - 0.038, zc + 0.038, "sign_back")
            if idx in (0, len(BACK_RAILS_Z) - 1):
                for px in POST_X:
                    mb.box(px - POST_R * 1.18, px + POST_R * 1.18, POST_Y - POST_R * 1.05, POST_Y + POST_R * 1.05,
                           zc - 0.048, zc + 0.048, "galv")
    elif stage == 1:
        for zc in (Z0 + 0.45, Z0 + H - 0.45):
            mb.box(-W / 2 + 0.15, W / 2 - 0.15, PANEL_Y[1] - 0.005, POST_Y, zc - 0.04, zc + 0.04, "sign_back")
    return mb


export("SignSideDistance", dict(main=build(0), lod1=build(1), lod2=build(2)), A, size_hint=(1, 1),
       notes=dict(panel_m=[W, H], bottom_m=Z0, text=" / ".join(f"{k} {e} {d} km" for k, e, d in ROWS)))
