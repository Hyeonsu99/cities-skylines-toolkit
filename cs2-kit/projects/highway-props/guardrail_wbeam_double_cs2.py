"""한국식 2단 W빔 가드레일(강성 구조물·문형표지 지주 방호용 SB5~SB6급) 1모듈 4.0 m.

경부고속도로 신탄진IC 문형표지 지주 보호구간(guardrail_03_run_sunlit.png·sign_gantry_02_truss_side.png) 실사진 근거.
연속 노측·램프는 기본 1단형(GuardrailWBeam), 교각·지주 앞 방호 구간에는 본 2단형(GuardrailWBeamDouble)을 배치한다.
"""
import os, sys  # noqa: E401
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hwprops_common import K, make_atlas, prism, extrude, export

L = 4.0                 # 레일 1장 유효 길이 (GuardrailWBeam 과 동일하게 x 방향 4 m 타일링)
POST_XS = (-2.0, 0.0)   # 지주 간격 2.0 m
RAILS_HC = (0.43, 0.83) # 하단(0.43 m)·상단(0.83 m) W빔 중심 높이 (실사진 2단 간격 ~9 cm)
POST_R = 0.0699         # φ139.8 원형 강관
POST_TOP = 1.06         # 2단 레일용 지주 상단 높이
T = 0.004
SPACER = 0.115
POST_Y = T + SPACER + POST_R
W_FRONT = [(-0.020, -0.155), (-0.083, -0.105), (-0.083, -0.060), (0.000, -0.012),
           (0.000, 0.012), (-0.083, 0.060), (-0.083, 0.105), (-0.020, 0.155)]

A = make_atlas(["galv_wbeam", "galv", "reflector_w", "reflector_y"])


def wbeam_poly(front, hc):
    f = [(y, z + hc) for y, z in front]
    b = [(y + T, z) for y, z in f][::-1]
    return f + b


def _u_blockout(mb, px, hc, simple=False):
    ya, yb = T * 0.6, POST_Y - POST_R * 0.55
    if simple:
        mb.box(px - 0.06, px + 0.06, ya, yb, hc - 0.095, hc + 0.095, "galv")
        return
    mb.box(px - 0.065, px + 0.065, yb - 0.018, yb, hc - 0.105, hc + 0.105, "galv")
    mb.box(px - 0.058, px + 0.058, ya, yb - 0.018, hc + 0.075, hc + 0.105, "galv")
    mb.box(px - 0.058, px + 0.058, ya, yb - 0.018, hc - 0.105, hc - 0.075, "galv")


def build(stage):
    mb = K.MeshBuilder(A)
    if stage == 2:
        mb.split_tiles = False
    x0, x1 = -L / 2, L / 2
    if stage == 0:
        for hc in RAILS_HC:
            extrude(mb, A, wbeam_poly(W_FRONT, hc), x0, x1, "galv_wbeam", cap="strip", map_mode="rail_z")
    elif stage == 1:
        simple = [(-0.020, -0.155), (-0.083, -0.083), (-0.083, 0.083), (-0.020, 0.155)]
        for hc in RAILS_HC:
            extrude(mb, A, wbeam_poly(simple, hc), x0, x1, "galv_wbeam", cap="strip", map_mode="rail_z")
    else:
        # LOD2(<=48 tris 유지): 상하 2단 얇은 판 + 4각 지주 2본
        for hc in RAILS_HC:
            mb.box(x0, x1, -0.083, 0.004, hc - 0.155, hc + 0.155, "galv")

    for px in POST_XS:
        prism(mb, A, (px, POST_Y, 0.0), (px, POST_Y, POST_TOP), POST_R, "galv",
              sides=8 if stage == 0 else 4, caps=(False, True), tiled=stage == 0)
        if stage < 2:
            for hc in RAILS_HC:
                _u_blockout(mb, px, hc, simple=stage == 1)
        if stage == 0:
            prism(mb, A, (px, POST_Y, POST_TOP), (px, POST_Y, POST_TOP + 0.026),
                  POST_R * 1.12, "galv", sides=8, caps=(True, True), tiled=False)
            for hc in RAILS_HC:
                mb.box(px - 0.014, px + 0.014, -0.014, 0.002, hc - 0.014, hc + 0.014, "galv")

    # 시선유도표지 (상단 레일 위 장착)
    top_hc = RAILS_HC[-1]
    if stage == 0:
        mb.box(-0.008, 0.008, -0.016, 0.008, top_hc + 0.145, top_hc + 0.210, "galv")
        mb.box(-0.056, 0.056, -0.018, 0.002, top_hc + 0.205, top_hc + 0.305, "galv")
        mb.quad([(-0.050, -0.021, top_hc + 0.212), (0.050, -0.021, top_hc + 0.212),
                 (0.050, -0.021, top_hc + 0.298), (-0.050, -0.021, top_hc + 0.298)], A.uv("reflector_w"), "reflector_w")
        mb.quad([(0.050, 0.005, top_hc + 0.212), (-0.050, 0.005, top_hc + 0.212),
                 (-0.050, 0.005, top_hc + 0.298), (0.050, 0.005, top_hc + 0.298)], A.uv("reflector_y"), "reflector_y")
    elif stage == 1:
        mb.box(-0.05, 0.05, -0.020, -0.005, top_hc + 0.19, top_hc + 0.28, "reflector_w")
    return mb


export("GuardrailWBeamDouble", dict(main=build(0), lod1=build(1), lod2=build(2)), A, size_hint=(1, 1),
       notes=dict(module_m=L, post_spacing_m=2.0, rails_m=list(RAILS_HC), post="φ139.8 강관 2단 W빔"))
