"""한국식 W빔 가드레일(노측용 방호울타리) 1모듈 4.0 m. x 방향으로 4 m 마다 이어 붙인다.

바닐라 CS2 가드레일과 다른 점: 원형 강관 지주(φ139.8) + 간격재 + 2 m 지주 간격 + 지주마다 시선유도표지.
도로(차량) 쪽 = -Y. 지주는 x=-2.0, 0.0 (다음 모듈이 x=+2.0 을 채운다). 치수 근거는 shape_notes.md.
"""
import os, sys  # noqa: E401
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # Blender --python 은 스크립트 폴더를 path 에 넣지 않는다
from hwprops_common import K, make_atlas, prism, extrude, export

L = 4.0                 # 레일 1장 유효 길이 # estimated
POST_XS = (-2.0, 0.0)   # 지주 간격 2.0 m # estimated (등급에 따라 2 m / 4 m)
HC = 0.60               # 레일 중심 높이 # estimated
POST_R = 0.0699         # φ139.8 강관
POST_TOP = 0.80         # # estimated
T = 0.004               # 레일 두께 4 mm
SPACER = 0.10           # 간격재 깊이 # estimated
POST_Y = T + SPACER + POST_R
# W 단면 (앞=-y). 아래→위: 아래 날개, 아래 산, 가운데 골(지주 쪽), 위 산, 위 날개. 폭 310 mm, 깊이 83 mm
W_FRONT = [(-0.020, -0.155), (-0.083, -0.105), (-0.083, -0.060), (0.000, -0.012),
           (0.000, 0.012), (-0.083, 0.060), (-0.083, 0.105), (-0.020, 0.155)]

A = make_atlas(["galv", "reflector_w"])


def wbeam_poly(front, hc):
    f = [(y, z + hc) for y, z in front]
    b = [(y + T, z) for y, z in f][::-1]
    return f + b


def build(stage):
    mb = K.MeshBuilder(A)
    x0, x1 = -L / 2, L / 2
    if stage == 0:
        extrude(mb, A, wbeam_poly(W_FRONT, HC), x0, x1, "galv", cap="strip")
    else:   # 산 두 개만 남긴 단순 단면
        simple = [(-0.020, -0.155), (-0.083, -0.083), (-0.083, 0.083), (-0.020, 0.155)]
        extrude(mb, A, wbeam_poly(simple, HC), x0, x1, "galv", cap="strip")
    for i, px in enumerate(POST_XS):
        prism(mb, A, (px, POST_Y, 0.0), (px, POST_Y, POST_TOP), POST_R, "galv",
              sides=8 if stage == 0 else 4, caps=(False, True))
        if stage < 2:   # 간격재 (레일 뒤 → 지주 앞)
            mb.box(px - 0.06, px + 0.06, T * 0.5, POST_Y - POST_R * 0.5, HC - 0.09, HC + 0.09, "galv")
        if stage == 0:
            prism(mb, A, (px, POST_Y, POST_TOP), (px, POST_Y, POST_TOP + 0.02), POST_R * 1.08, "galv", sides=8)  # 지주 캡
    if stage == 0:      # 시선유도표지 (반사체) — 레일 위 브래킷
        mb.box(-0.004, 0.004, -0.010, 0.0, HC + 0.155, HC + 0.215, "galv")
        mb.box(-0.05, 0.05, -0.020, -0.010, HC + 0.17, HC + 0.27, "reflector_w")
    return mb


export("GuardrailWBeam", dict(main=build(0), lod1=build(1), lod2=build(2)), A, size_hint=(1, 1),
       notes=dict(module_m=L, post_spacing_m=2.0, rail_center_m=HC, post="φ139.8 강관"))
