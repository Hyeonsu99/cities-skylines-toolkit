"""금속 흡음형 방음벽 1모듈 (지주 간격 2.0 m). x 방향으로 2 m 마다 이어 붙인다.

단면(아래→위): 콘크리트 기초벽 0.60 m / 흡음판 7단 × 0.50 m (전면 슬릿 타공) / 상부 캡.
지주는 모듈 왼쪽 끝(x=-1.0) 에 H-150x150 1본. 치수 근거는 shape_notes.md.
"""
import os, sys  # noqa: E401
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # Blender --python 은 스크립트 폴더를 path 에 넣지 않는다
from hwprops_common import K, make_atlas, h_beam, export

L = 2.0
Z_BASE = 0.55           # 세로 주름 콘크리트 기초벽 (실사진 비례)
PANEL_H = 0.50          # 흡음판 1단 높이 (폭 0.5 m × 길이 2 m 판 수평 적층)
N_PANEL = 7             # 총고 4.05 m
Z_TOP = Z_BASE + PANEL_H * N_PANEL
HB, HH, TW, TF = 0.150, 0.150, 0.007, 0.010
PANEL_T = 0.095

A = make_atlas(["concrete_fluted", "steel_post", "absorb_panel"])
x0, x1 = -L / 2, L / 2
xi0, xi1 = x0 + 0.004, x1 - 0.004


def _panel_tier(mb, za, zb, ya, yb, i):
    """i번째 단 흡음판: 앞·뒷면은 전체 7단 UV 중 i/7~(i+1)/7 구간에 정확히 맞춰 하단 스톤그레이/상단 챠콜을 구분."""
    fv0, fv1 = i / N_PANEL, (i + 1) / N_PANEL
    uv_f = A.uv_sub("absorb_panel", 0.0, fv0, 1.0, fv1)
    uv_s = A.uv_sub("absorb_panel", 0.0, fv0, 0.08, fv1)
    uv_t = A.uv_sub("absorb_panel", 0.0, max(0.0, fv1 - 0.04), 1.0, fv1)
    # 앞(-y), 뒤(+y), 좌(-x), 우(+x)
    mb.quad([(xi0, ya, za), (xi1, ya, za), (xi1, ya, zb), (xi0, ya, zb)], uv_f, "absorb_panel")
    mb.quad([(xi1, yb, za), (xi0, yb, za), (xi0, yb, zb), (xi1, yb, zb)], uv_f, "absorb_panel")
    mb.quad([(xi0, yb, za), (xi0, ya, za), (xi0, ya, zb), (xi0, yb, zb)], uv_s, "absorb_panel")
    mb.quad([(xi1, ya, za), (xi1, yb, za), (xi1, yb, zb), (xi1, ya, zb)], uv_s, "absorb_panel")
    if i % 2:
        mb.quad([(xi0, ya, zb), (xi1, ya, zb), (xi1, yb, zb), (xi0, yb, zb)], uv_t, "absorb_panel")
        mb.quad([(xi0, yb, za), (xi1, yb, za), (xi1, ya, za), (xi0, ya, za)], uv_t, "absorb_panel")


def build(stage):
    mb = K.MeshBuilder(A)
    mb.box(x0, x1, -0.15, 0.15, 0.0, Z_BASE, "concrete_fluted", skip=("bottom",))
    if stage == 0:
        mb.box(x0 - 0.14, x0 + 0.14, -0.145, 0.145, Z_BASE, Z_BASE + 0.024, "steel_post", skip=("bottom",))
        for s in (-1, 1):
            y_in, y_out = s * (HH / 2), s * 0.13
            for dx in (-0.042, 0.042):
                mb.box(x0 + dx - 0.007, x0 + dx + 0.007, min(y_in, y_out), max(y_in, y_out),
                       Z_BASE + 0.024, Z_BASE + 0.12, "steel_post", skip=("bottom",))
    h_beam(mb, x0, 0.0, Z_BASE, Z_TOP + 0.05, HB, HH, TW, TF, "steel_post", simple=stage >= 1)
    if stage == 0:
        for i in range(N_PANEL):
            za = Z_BASE + i * PANEL_H
            off = 0.004 if i % 2 else 0.0
            _panel_tier(mb, za, za + PANEL_H, -PANEL_T / 2 - off, PANEL_T / 2 + off, i)
        mb.box(x0 - 0.095, x0 + 0.095, -0.095, 0.095, Z_TOP + 0.05, Z_TOP + 0.075, "steel_post")
        mb.box(xi0, xi1, -0.062, 0.062, Z_TOP, Z_TOP + 0.032, "steel_post")
    else:
        mb.box(xi0, xi1, -PANEL_T / 2, PANEL_T / 2, Z_BASE, Z_TOP, "absorb_panel", skip=("bottom",))
    return mb


export("NoiseWallMetal", dict(main=build(0), lod1=build(1), lod2=build(2)), A, size_hint=(1, 1),
       notes=dict(module_m=L, height_m=Z_TOP, tiling="x 방향 2.0 m 간격", post="H-150x150x7x10"))
