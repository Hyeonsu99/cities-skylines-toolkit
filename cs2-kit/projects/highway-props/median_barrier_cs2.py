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


A = make_atlas(["concrete", "reflector_y"])


def build(stage):
    mb = K.MeshBuilder(A)
    x0, x1 = -L / 2, L / 2
    poly = profile(stage == 0)
    if stage >= 1:          # 하단 수직부 생략
        poly = [p for p in poly if abs(p[1] - Z_LIP) > 1e-6]
    if stage == 2:          # 사다리꼴 (먼 거리)
        poly = [(-B, 0.0), (-B_TOP, H), (B_TOP, H), (B, 0.0)]
    extrude(mb, A, poly, x0, x1, "concrete", cap="fan" if stage == 0 else "strip")
    if stage == 0:          # 양면 반사체 (모듈당 1개, 꺾임점 위 상부 경사면) # estimated
        for s in (-1, 1):
            z0, z1 = 0.95, 1.05
            def yat(z): return s * (B_BRK + (B_TOP - B_BRK) * (z - Z_BRK) / (H - CH - Z_BRK))
            ya, yb = yat(z0), yat(z1)
            d = s * 0.012
            if s < 0:
                pts = [(-0.08, ya + d, z0), (0.08, ya + d, z0), (0.08, yb + d, z1), (-0.08, yb + d, z1)]
            else:
                pts = [(0.08, ya + d, z0), (-0.08, ya + d, z0), (-0.08, yb + d, z1), (0.08, yb + d, z1)]
            mb.quad(pts, A.uv("reflector_y"), "reflector_y")
    return mb


export("MedianBarrierConcrete", dict(main=build(0), lod1=build(1), lod2=build(2)), A, size_hint=(1, 1),
       notes=dict(module_m=L, height_m=H, base_width_m=2 * B, top_width_m=2 * B_TOP, joint="4 m 신축이음 홈(텍스처)"))
