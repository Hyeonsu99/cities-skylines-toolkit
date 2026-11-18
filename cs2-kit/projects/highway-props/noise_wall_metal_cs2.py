"""금속 흡음형 방음벽 1모듈 (지주 간격 2.0 m). x 방향으로 2 m 마다 이어 붙인다.

단면(아래→위): 콘크리트 기초벽 0.60 m / 흡음판 7단 × 0.50 m (전면 슬릿 타공) / 상부 캡.
지주는 모듈 왼쪽 끝(x=-1.0) 에 H-150x150 1본. 치수 근거는 shape_notes.md.
"""
import os, sys  # noqa: E401
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # Blender --python 은 스크립트 폴더를 path 에 넣지 않는다
from hwprops_common import K, make_atlas, h_beam, export

L = 2.0
Z_BASE = 0.60           # # estimated
PANEL_H = 0.50          # 흡음판 1단 높이 (폭 0.5 m × 길이 2 m 판 수평 적층)
N_PANEL = 7             # # estimated (총고 4.1 m)
Z_TOP = Z_BASE + PANEL_H * N_PANEL
HB, HH, TW, TF = 0.150, 0.150, 0.007, 0.010
PANEL_T = 0.095         # # estimated

A = make_atlas(["concrete", "steel_post", "absorb_panel"])
x0, x1 = -L / 2, L / 2
xi0, xi1 = x0 + 0.004, x1 - 0.004


def build(stage):
    mb = K.MeshBuilder(A)
    mb.box(x0, x1, -0.15, 0.15, 0.0, Z_BASE, "concrete", skip=("bottom",))
    if stage == 0:
        mb.box(x0 - 0.14, x0 + 0.14, -0.14, 0.14, Z_BASE, Z_BASE + 0.022, "steel_post", skip=("bottom",))
    h_beam(mb, x0, 0.0, Z_BASE, Z_TOP + 0.05, HB, HH, TW, TF, "steel_post", simple=stage >= 1)
    if stage == 0:
        # 판마다 따로: 이음 그림자가 기하로도 드러나도록 단마다 앞면을 4 mm 씩 엇갈리게 (판 겹침 시공 모양)
        for i in range(N_PANEL):
            za = Z_BASE + i * PANEL_H
            off = 0.004 if i % 2 else 0.0
            # 좁은 단(짝수)은 위·아래를 넓은 단이 덮으므로 생략 → 같은 평면 겹침 없음
            sk = () if i % 2 else (("bottom",) if i == N_PANEL - 1 else ("bottom", "top"))
            mb.box(xi0, xi1, -PANEL_T / 2 - off, PANEL_T / 2 + off, za, za + PANEL_H, "absorb_panel", skip=sk)
        mb.box(x0 - 0.09, x0 + 0.09, -0.09, 0.09, Z_TOP + 0.05, Z_TOP + 0.07, "steel_post")
        mb.box(xi0, xi1, -0.06, 0.06, Z_TOP, Z_TOP + 0.03, "steel_post")            # 상부 캡 채널
    else:
        mb.box(xi0, xi1, -PANEL_T / 2, PANEL_T / 2, Z_BASE, Z_TOP, "absorb_panel", skip=("bottom",))
    return mb


export("NoiseWallMetal", dict(main=build(0), lod1=build(1), lod2=build(2)), A, size_hint=(1, 1),
       notes=dict(module_m=L, height_m=Z_TOP, tiling="x 방향 2.0 m 간격", post="H-150x150x7x10"))
