"""투명 방음벽 1모듈 (지주 간격 2.0 m). x 방향으로 2 m 마다 이어 붙인다.

단면(아래→위): 콘크리트 기초벽 0.60 m / 금속 흡음판 1단 0.50 m / 투명 PC 패널 3단 × 1.00 m / 상부 캡.
지주는 모듈 왼쪽 끝(x=-1.0) 에 H-150x150 1본 — 다음 모듈의 지주가 오른쪽 끝을 닫는다.
치수 근거는 shape_notes.md.
"""
import os, sys  # noqa: E401
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # Blender --python 은 스크립트 폴더를 path 에 넣지 않는다
from hwprops_common import K, make_atlas, h_beam, export

L = 2.0                 # 지주 간격
Z_BASE = 0.60           # 콘크리트 기초벽 노출 높이 # estimated
Z_METAL = 1.10          # 하단 금속 흡음판 1단 (0.5 m)
CLEAR = [1.10, 2.10, 3.10, 4.10]   # 투명판 3단 경계 # estimated (판 높이 1.0 m)
Z_TOP = 4.10
HB, HH, TW, TF = 0.150, 0.150, 0.007, 0.010   # H-150x150x7x10
PANEL_T = 0.095         # 흡음판 두께 # estimated (100 mm 급)
GLASS_T = 0.012         # PC 판 두께 # estimated
FRAME_T = 0.060         # 알루미늄 프레임 두께(y)
FRAME_H = 0.050         # 프레임 높이(z)

A = make_atlas(["concrete", "steel_post", "absorb_panel", "panel_frame", "glass", "acrylic_lod"])
x0, x1 = -L / 2, L / 2
xp = x0                 # 지주 중심
xi0, xi1 = x0 + 0.004, x1 - 0.004   # 패널은 웨브 앞까지 홈에 들어간다 (모듈 사이 4+4 mm 여유)


def build(stage):
    mb, gls = K.MeshBuilder(A), K.MeshBuilder(A)
    # 기초벽 (0.30 m 두께) + 지주 베이스플레이트
    mb.box(x0, x1, -0.15, 0.15, 0.0, Z_BASE, "concrete", skip=("bottom",))
    if stage == 0:
        mb.box(xp - 0.14, xp + 0.14, -0.14, 0.14, Z_BASE, Z_BASE + 0.022, "steel_post", skip=("bottom",))
    # 지주
    h_beam(mb, xp, 0.0, Z_BASE, Z_TOP + 0.05, HB, HH, TW, TF, "steel_post", simple=stage >= 1)
    if stage == 2:
        mb.box(xi0, xi1, -PANEL_T / 2, PANEL_T / 2, Z_BASE, Z_METAL, "absorb_panel", skip=("bottom",))
        mb.box(xi0, xi1, -0.006, 0.006, Z_METAL, Z_TOP, "acrylic_lod", skip=("bottom",))
        return mb, gls
    # 하단 흡음판 1단
    mb.box(xi0, xi1, -PANEL_T / 2, PANEL_T / 2, Z_BASE, Z_METAL, "absorb_panel", skip=("bottom",))
    # 투명판 프레임(가로살) + 판
    for i, z in enumerate(CLEAR):
        za, zb = (z, z + FRAME_H) if i == 0 else ((z - FRAME_H, z) if i == len(CLEAR) - 1 else (z - FRAME_H / 2, z + FRAME_H / 2))
        if stage == 1 and 0 < i < len(CLEAR) - 1:
            continue
        mb.box(xi0, xi1, -FRAME_T / 2, FRAME_T / 2, za, zb, "panel_frame", skip=())
    for za, zb in zip(CLEAR[:-1], CLEAR[1:]):
        za2 = za + (FRAME_H if za == CLEAR[0] else FRAME_H / 2)
        zb2 = zb - (FRAME_H if zb == CLEAR[-1] else FRAME_H / 2)
        if stage == 1:
            za2, zb2 = CLEAR[0] + FRAME_H, CLEAR[-1] - FRAME_H
        gls.box(xi0, xi1, -GLASS_T / 2, GLASS_T / 2, za2, zb2, "glass")
        if stage == 1:
            break
    # 상부 캡 (지주 위 덮개)
    if stage == 0:
        mb.box(xp - 0.09, xp + 0.09, -0.09, 0.09, Z_TOP + 0.05, Z_TOP + 0.07, "steel_post")
    return mb, gls


m0, g0 = build(0)
m1, g1 = build(1)
m2, _ = build(2)
export("NoiseWallClear", dict(main=m0, lod1=m1, lod2=m2, gls=g0, lod1_gls=g1), A, size_hint=(1, 1),
       notes=dict(module_m=L, height_m=Z_TOP, tiling="x 방향 2.0 m 간격", post="H-150x150x7x10"))
