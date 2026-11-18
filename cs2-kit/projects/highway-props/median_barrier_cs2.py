"""콘크리트 중앙분리대(강성 방호벽) 1모듈 4.0 m, 높이 1.27 m (SB5급 고규격형). x 방향으로 이어 붙인다.

바닐라 CS2 고속도로 중앙분리대(낮은 저지형)와 다른 점: 1.27 m 고규격 + F형 2단 경사 단면 + 양면 황색 반사체.
치수 근거는 shape_notes.md.
"""
import os, sys  # noqa: E401
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # Blender --python 은 스크립트 폴더를 path 에 넣지 않는다
from hwprops_common import K, make_atlas, extrude, export

L = 4.0
H = 1.27                # 1270 mm 고규격 중앙분리대
B = 0.405               # 하단 반폭 (폭 0.81 m) # estimated
Z_LIP = 0.075           # 하단 수직부 # estimated (F형)
Z_BRK = 0.33            # 경사 꺾임점 높이 # estimated
B_BRK = 0.226           # 꺾임점 반폭 (하단 55° 경사) # estimated
B_TOP = 0.125           # 상단 반폭 (폭 0.25 m, 상부 84° 경사) # estimated
CH = 0.02               # 상단 모따기


def half(full):
    if full:
        return [(B, 0.0), (B, Z_LIP), (B_BRK, Z_BRK), (B_TOP, H - CH), (B_TOP - CH, H)]
    return [(B, 0.0), (B, Z_LIP), (B_BRK, Z_BRK), (B_TOP, H)]


def profile(full):
    """시계방향(왼쪽 아래 → 위 → 오른쪽 → 아래)."""
    right = half(full)
    left = [(-y, z) for y, z in right]
    return left + right[::-1]


import numpy as np  # noqa: E402


def _paint_barrier_concrete(ctx):
    """슬립폼 연속 타설 콘크리트: 밝은 회색 + 4 m 모듈 끝 신축이음 위주 + 하단 약한 노면 먼지."""
    x, y = ctx.meters()
    tw, _th = ctx.tile
    n_broad = ctx.noise(scale_px=48, amp=1.0, octaves=2, seed=3)
    n_fine = ctx.noise(scale_px=6, amp=1.0, octaves=2, seed=17)
    # 오염은 노면 접지부 최하단(0 ~ 0.16 m)에만 약하게 제한
    curb_dust = np.exp(-np.maximum(0.0, y) / 0.075) * 0.095 * (0.78 + 0.22 * np.clip(n_broad, -1, 1))
    tone = 1.0 + 0.016 * n_broad + 0.020 * n_fine - curb_dust
    ctx.rgb *= tone[..., None]
    ctx.rgb[..., 2] *= (1.0 - 0.03 * curb_dust)
    ctx.height += 0.08 * n_fine + 0.03 * n_broad - 0.10 * curb_dust
    # 4 m 모듈 경계(x=0 / x=tw)에만 신축이음 홈 (중간 촘촘한 줄눈·타이홀 제거)
    edge_x = np.minimum(x, tw - x)
    joint = edge_x < 0.022
    ctx.rgb[joint] *= 0.72
    ctx.height[joint] -= 1.25
    ctx.gloss[...] = np.clip(0.16 + 0.025 * n_fine - 0.03 * curb_dust, 0.10, 0.22)


A = make_atlas([
    ("concrete_barrier", dict(color=(202, 198, 191), gloss=0.16, px=448, tile=(4.0, 1.30),
                              painter=_paint_barrier_concrete, normal_strength=0.85)),
    "galv",
    "reflector_y",
])


def _side_delineator(mb, xc, s):
    """경사 상부 양면 시선유도 반사체: 경사면 바깥에 돌출 부착된 아연도금 베젤 + 황색 반사지."""
    z0, z1 = 0.94, 1.05
    def yat(z): return s * (B_BRK + (B_TOP - B_BRK) * (z - Z_BRK) / (H - CH - Z_BRK))
    ya0, ya1 = yat(z0), yat(z1)
    yo = ya0 + s * 0.022
    yi = ya1 - s * 0.004
    mb.box(xc - 0.09, xc + 0.09, min(yo, yi), max(yo, yi), z0, z1, "galv")
    yf = yo + s * 0.003
    if s < 0:
        pts = [(xc - 0.074, yf, z0 + 0.012), (xc + 0.074, yf, z0 + 0.012),
               (xc + 0.074, yf, z1 - 0.012), (xc - 0.074, yf, z1 - 0.012)]
    else:
        pts = [(xc + 0.074, yf, z0 + 0.012), (xc - 0.074, yf, z0 + 0.012),
               (xc - 0.074, yf, z1 - 0.012), (xc + 0.074, yf, z1 - 0.012)]
    mb.quad(pts, A.uv_full("reflector_y"), "reflector_y")


def build(stage):
    mb = K.MeshBuilder(A)
    x0, x1 = -L / 2, L / 2
    poly = profile(stage == 0)
    if stage >= 1:          # 하단 수직부 생략
        poly = [p for p in poly if abs(p[1] - Z_LIP) > 1e-6]
    if stage == 2:          # 사다리꼴 (먼 거리)
        poly = [(-B, 0.0), (-B_TOP, H), (B_TOP, H), (B, 0.0)]
    extrude(mb, A, poly, x0, x1, "concrete_barrier", cap="fan" if stage == 0 else "strip",
            map_mode="world_z" if stage < 2 else "perim", z_max=H)
    if stage == 0:
        for xc in (-1.0, 1.0):
            for s in (-1, 1):
                _side_delineator(mb, xc, s)
        # 상단 중앙 시선유도 표지병 (작은 델리네이터 캡)
        mb.box(-0.06, 0.06, -0.045, 0.045, H, H + 0.025, "galv", skip=("bottom",))
        mb.box(-0.045, 0.045, -0.052, 0.052, H + 0.025, H + 0.055, "reflector_y", skip=("bottom",))
    elif stage == 1:
        for s in (-1, 1):
            z0, z1 = 0.95, 1.05
            def yat(z): return s * (B_BRK + (B_TOP - B_BRK) * (z - Z_BRK) / (H - CH - Z_BRK))
            ya, yb = yat(z0), yat(z1)
            d = s * 0.012
            pts = [(-0.08, ya + d, z0), (0.08, ya + d, z0), (0.08, yb + d, z1), (-0.08, yb + d, z1)]
            if s > 0:
                pts = [pts[1], pts[0], pts[3], pts[2]]
            mb.quad(pts, A.uv("reflector_y"), "reflector_y")
    return mb


export("MedianBarrierConcrete", dict(main=build(0), lod1=build(1), lod2=build(2)), A, size_hint=(1, 1),
       notes=dict(module_m=L, height_m=H, base_width_m=2 * B, top_width_m=2 * B_TOP, joint="4 m 신축이음 홈 + 폼타이 + 오염"))
