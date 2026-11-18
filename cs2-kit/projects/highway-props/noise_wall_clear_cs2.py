"""투명 방음벽 1모듈 (지주 간격 2.0 m). x 방향으로 2 m 마다 이어 붙인다.

단면(아래→위): 콘크리트 기초벽 0.60 m / 금속 흡음판 1단 0.50 m / 투명 PC 패널 3단 × 1.00 m / 상부 캡.
지주는 모듈 왼쪽 끝(x=-1.0) 에 H-150x150 1본 — 다음 모듈의 지주가 오른쪽 끝을 닫는다.
치수 근거는 shape_notes.md.
"""
import math
import os, sys  # noqa: E401
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # Blender --python 은 스크립트 폴더를 path 에 넣지 않는다
from hwprops_common import K, make_atlas, h_beam, prism, export

L = 2.0                 # 지주 간격
Z_BASE = 0.55           # 주름 콘크리트 기초벽 노출 높이 (실사진 비례)
Z_METAL = 1.80          # 하단 스톤베이지 금속 흡음판 (1.25 m)
CLEAR = [1.80, 2.57, 3.34, 4.10]   # 투명판 3단 경계 (판 높이 0.77 m)
Z_TOP = 4.10
HB, HH, TW, TF = 0.150, 0.150, 0.007, 0.010   # H-150x150x7x10
PANEL_T = 0.095         # 흡음판 두께
GLASS_T = 0.012         # PC 판 두께
FRAME_T = 0.062         # 알루미늄 프레임 두께(y)
FRAME_H = 0.048         # 프레임 높이(z)

A = make_atlas(["concrete_fluted", "steel_post", "absorb_warm", "panel_frame", "glass", "acrylic_lod", "bird_sticker"])
x0, x1 = -L / 2, L / 2
xp = x0                 # 지주 중심
xi0, xi1 = x0 + 0.004, x1 - 0.004   # 패널은 웨브 앞까지 홈에 들어간다 (모듈 사이 4+4 mm 여유)


def _bird_sticker(mb, cx, cz, sc=0.22, tilt_deg=-15.0):
    """투명 방음판 위 맹금류 조류충돌방지 실루엣(유리 양면으로 8 mm 돌출된 닫힌 형상)."""
    ca, sa = math.cos(math.radians(tilt_deg)), math.sin(math.radians(tilt_deg))
    def pt(dx, dz):
        return (cx + dx * ca - dz * sa, 0.0, cz + dx * sa + dz * ca)
    # 몸통(머리~꼬리) + 좌/우 펼친 날개
    prism(mb, A, pt(0.0, -sc * 0.55), pt(0.0, sc * 0.45), 0.017, "bird_sticker", sides=4, caps=(True, True), tiled=False)
    prism(mb, A, pt(-0.02, sc * 0.12), pt(-sc * 1.10, sc * 0.36), 0.015, "bird_sticker", sides=4, caps=(True, True), tiled=False)
    prism(mb, A, pt(0.02, sc * 0.12), pt(sc * 1.10, sc * 0.36), 0.015, "bird_sticker", sides=4, caps=(True, True), tiled=False)


def _add_gusset_fins(mb):
    """H형강 지주 하단 삼각 보강 리브(전후 각 2개, 실사진 noisewall_clear_04 재현)."""
    z_a, z_b = Z_BASE + 0.024, Z_BASE + 0.165
    for s in (-1, 1):
        y_in, y_out = s * (HH / 2), s * 0.132
        for dx in (-0.042, 0.042):
            xa, xb = xp + dx - 0.007, xp + dx + 0.007
            mb.box(xa, xb, min(y_in, y_out), max(y_in, y_out), z_a, z_a + 0.09, "steel_post", skip=("bottom",))
    # 앵커 볼트 너트 캡 (4개)
    for dx in (-0.10, 0.10):
        for dy in (-0.10, 0.10):
            mb.box(xp + dx - 0.015, xp + dx + 0.015, dy - 0.015, dy + 0.015, Z_BASE + 0.024, Z_BASE + 0.046, "steel_post", skip=("bottom",))


def _glass_pane(gls, ya, yb, za, zb, fv0, fv1):
    """투명 방음판 1장: 앞/뒤 면은 조류스티커·가스켓 전체 UV(uv_sub), 4 테두리는 유리 단색 UV."""
    uv_front = A.uv_sub("glass", 0.0, fv0, 1.0, fv1)
    uv_back = A.uv_sub("glass", 0.0, fv0, 1.0, fv1)
    uv_edge = A.uv("glass")
    gls.quad([(xi0, ya, za), (xi1, ya, za), (xi1, ya, zb), (xi0, ya, zb)], uv_front, "glass")
    gls.quad([(xi1, yb, za), (xi0, yb, za), (xi0, yb, zb), (xi1, yb, zb)], uv_back, "glass")
    gls.quad([(xi0, yb, za), (xi0, ya, za), (xi0, ya, zb), (xi0, yb, zb)], uv_edge, "glass")
    gls.quad([(xi1, ya, za), (xi1, yb, za), (xi1, yb, zb), (xi1, ya, zb)], uv_edge, "glass")
    gls.quad([(xi0, ya, zb), (xi1, ya, zb), (xi1, yb, zb), (xi0, yb, zb)], uv_edge, "glass")
    gls.quad([(xi0, yb, za), (xi1, yb, za), (xi1, ya, za), (xi0, ya, za)], uv_edge, "glass")


def build(stage):
    mb, gls = K.MeshBuilder(A), K.MeshBuilder(A)
    if stage == 2:
        mb.split_tiles = False
    # 세로 주름 콘크리트 기초벽 (0.30 m 두께) + 베이스플레이트
    mb.box(x0, x1, -0.15, 0.15, 0.0, Z_BASE, "concrete_fluted", skip=("bottom",))
    if stage == 0:
        mb.box(xp - 0.14, xp + 0.14, -0.145, 0.145, Z_BASE, Z_BASE + 0.024, "steel_post", skip=("bottom",))
        _add_gusset_fins(mb)
    # H형강 지주
    h_beam(mb, xp, 0.0, Z_BASE, Z_TOP + 0.05, HB, HH, TW, TF, "steel_post", simple=stage >= 1)
    if stage == 2:
        mb.box(xi0, xi1, -PANEL_T / 2, PANEL_T / 2, Z_BASE, Z_METAL, "absorb_warm", skip=("bottom",))
        mb.box(xi0, xi1, -0.006, 0.006, Z_METAL, Z_TOP, "acrylic_lod", skip=("bottom",))
        return mb, gls
    # 하단 스톤베이지 카세트 흡음판
    mb.box(xi0, xi1, -PANEL_T / 2, PANEL_T / 2, Z_BASE, Z_METAL, "absorb_warm", skip=("bottom",))
    # 투명판 가로살 프레임 + 조류스티커 포함 유리판
    for i, z in enumerate(CLEAR):
        za = z if i == 0 else (z - FRAME_H if i == len(CLEAR) - 1 else z - FRAME_H / 2)
        zb = z + FRAME_H if i == 0 else (z if i == len(CLEAR) - 1 else z + FRAME_H / 2)
        if stage == 1 and 0 < i < len(CLEAR) - 1:
            continue
        mb.box(xi0, xi1, -FRAME_T / 2, FRAME_T / 2, za, zb, "panel_frame", skip=())
    n_panes = len(CLEAR) - 1
    for i, (za, zb) in enumerate(zip(CLEAR[:-1], CLEAR[1:])):
        za2 = za + (FRAME_H if za == CLEAR[0] else FRAME_H / 2)
        zb2 = zb - (FRAME_H if zb == CLEAR[-1] else FRAME_H / 2)
        if stage == 1:
            za2, zb2 = CLEAR[0] + FRAME_H, CLEAR[-1] - FRAME_H
            _glass_pane(gls, -GLASS_T / 2, GLASS_T / 2, za2, zb2, 0.0, 1.0)
            break
        _glass_pane(gls, -GLASS_T / 2, GLASS_T / 2, za2, zb2, i / n_panes, (i + 1) / n_panes)
    # 상부 지주 덮개 캡 + 조류충돌방지 실루엣 2개(실사진 noisewall_clear_01/04 위치)
    if stage == 0:
        mb.box(xp - 0.095, xp + 0.095, -0.095, 0.095, Z_TOP + 0.05, Z_TOP + 0.075, "steel_post")
        _bird_sticker(mb, -0.32, 3.68, sc=0.22, tilt_deg=-16.0)
        _bird_sticker(mb, 0.40, 2.95, sc=0.20, tilt_deg=14.0)
    return mb, gls


m0, g0 = build(0)
m1, g1 = build(1)
m2, _ = build(2)
export("NoiseWallClear", dict(main=m0, lod1=m1, lod2=m2, gls=g0, lod1_gls=g1), A, size_hint=(1, 1),
       notes=dict(module_m=L, height_m=Z_TOP, tiling="x 방향 2.0 m 간격", post="H-150x150x7x10"))
