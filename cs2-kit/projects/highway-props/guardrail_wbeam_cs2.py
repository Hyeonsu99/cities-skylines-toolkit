"""한국식 W빔 가드레일(노측용 방호울타리) 1모듈 4.0 m. x 방향으로 4 m 마다 이어 붙인다.

바닐라 CS2 가드레일과 다른 점: 원형 강관 지주(φ139.8) + 간격재 + 2 m 지주 간격 + 지주마다 시선유도표지.
도로(차량) 쪽 = -Y. 지주는 x=-2.0, 0.0 (다음 모듈이 x=+2.0 을 채운다). 치수 근거는 shape_notes.md.
"""
import os, sys  # noqa: E401
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # Blender --python 은 스크립트 폴더를 path 에 넣지 않는다
from hwprops_common import K, make_atlas, prism, extrude, export

L = 4.0                 # 레일 1장 유효 길이
POST_XS = (-2.0, 0.0)   # 지주 간격 2.0 m
HC = 0.60               # 레일 중심 높이
POST_R = 0.0699         # φ139.8 원형 강관
POST_TOP = 0.80         # 지주 상단 높이
T = 0.004               # 레일 두께 4 mm
SPACER = 0.115          # 간격재(U형 블록아웃) 깊이
POST_Y = T + SPACER + POST_R
# W 단면 (앞=-y). 아래→위: 아래 날개, 아래 산, 가운데 골(지주 쪽), 위 산, 위 날개. 폭 310 mm, 깊이 83 mm
W_FRONT = [(-0.020, -0.155), (-0.083, -0.105), (-0.083, -0.060), (0.000, -0.012),
           (0.000, 0.012), (-0.083, 0.060), (-0.083, 0.105), (-0.020, 0.155)]

A = make_atlas(["galv_wbeam", "galv", "reflector_w", "reflector_y"])


def wbeam_poly(front, hc):
    f = [(y, z + hc) for y, z in front]
    b = [(y + T, z) for y, z in f][::-1]
    return f + b


def _u_blockout(mb, px, simple=False):
    """실물 C/U형 블록아웃 간격재 (레일 뒤→지주 앞 결합 브래킷)."""
    ya, yb = T * 0.6, POST_Y - POST_R * 0.55
    if simple:
        mb.box(px - 0.06, px + 0.06, ya, yb, HC - 0.095, HC + 0.095, "galv")
        return
    # 뒷판(지주 측 접합면) + 상·하 날개 플랜지
    mb.box(px - 0.065, px + 0.065, yb - 0.018, yb, HC - 0.105, HC + 0.105, "galv")
    mb.box(px - 0.058, px + 0.058, ya, yb - 0.018, HC + 0.075, HC + 0.105, "galv")
    mb.box(px - 0.058, px + 0.058, ya, yb - 0.018, HC - 0.105, HC - 0.075, "galv")


def build(stage):
    mb = K.MeshBuilder(A)
    x0, x1 = -L / 2, L / 2
    if stage == 0:
        extrude(mb, A, wbeam_poly(W_FRONT, HC), x0, x1, "galv_wbeam", cap="strip", map_mode="rail_z")
    else:
        simple = [(-0.020, -0.155), (-0.083, -0.083), (-0.083, 0.083), (-0.020, 0.155)]
        extrude(mb, A, wbeam_poly(simple, HC), x0, x1, "galv_wbeam", cap="strip", map_mode="rail_z")
    for px in POST_XS:
        prism(mb, A, (px, POST_Y, 0.0), (px, POST_Y, POST_TOP), POST_R, "galv",
              sides=10 if stage == 0 else 4, caps=(False, True), tiled=stage == 0)
        if stage < 2:
            _u_blockout(mb, px, simple=stage == 1)
        if stage == 0:
            # 원형 파이프 상단 둥근 빗물 캡 (guardrail_01_rear_blockout 실물 재현)
            prism(mb, A, (px, POST_Y, POST_TOP), (px, POST_Y, POST_TOP + 0.024),
                  POST_R * 1.12, "galv", sides=10, tiled=False)
            # 중앙 골 체결 볼트 머리(전면 -Y 노출)
            mb.box(px - 0.014, px + 0.014, -0.014, 0.002, HC - 0.014, HC + 0.014, "galv")
    # 시선유도표지 (반사체) — 닫힌 금속 하우징 + 전후면 반사지 (구멍/이면 노출 없음)
    if stage == 0:
        mb.box(-0.008, 0.008, -0.016, 0.008, HC + 0.145, HC + 0.215, "galv")
        mb.box(-0.056, 0.056, -0.018, 0.002, HC + 0.205, HC + 0.305, "galv")
        mb.quad([(-0.050, -0.021, HC + 0.212), (0.050, -0.021, HC + 0.212),
                 (0.050, -0.021, HC + 0.298), (-0.050, -0.021, HC + 0.298)], A.uv("reflector_w"), "reflector_w")
        mb.quad([(0.050, 0.005, HC + 0.212), (-0.050, 0.005, HC + 0.212),
                 (-0.050, 0.005, HC + 0.298), (0.050, 0.005, HC + 0.298)], A.uv("reflector_y"), "reflector_y")
    elif stage == 1:
        mb.box(-0.05, 0.05, -0.020, -0.005, HC + 0.19, HC + 0.28, "reflector_w")
    return mb


export("GuardrailWBeam", dict(main=build(0), lod1=build(1), lod2=build(2)), A, size_hint=(1, 1),
       notes=dict(module_m=L, post_spacing_m=2.0, rail_center_m=HC, post="φ139.8 강관 + U블록아웃"))
