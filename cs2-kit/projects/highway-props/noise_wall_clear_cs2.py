"""투명 방음벽 1모듈 (지주 간격 2.0 m). x 방향으로 2 m 마다 이어 붙인다.

단면(아래→위): 콘크리트 기초벽 0.60 m / 금속 흡음판 1단 0.50 m / 투명 PC 패널 3단 × 1.00 m / 상부 캡.
지주는 모듈 왼쪽 끝(x=-1.0) 에 H-150x150 1본 — 다음 모듈의 지주가 오른쪽 끝을 닫는다.
치수 근거는 shape_notes.md.
"""
import math
import os, sys  # noqa: E401
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # Blender --python 은 스크립트 폴더를 path 에 넣지 않는다
from hwprops_common import K, make_atlas, h_beam, export, _SIGN_CACHE_DIR

L = 2.0                 # 지주 간격
Z_BASE = 0.55           # 주름 콘크리트 기초벽 노출 높이
Z_METAL = 1.80          # 하단 스톤베이지 금속 흡음판 (1.25 m)
CLEAR = [1.80, 2.375, 2.95, 3.525, 4.10]   # 투명판 4단 (칸 높이 0.575 m × 폭 1.0 m = 실사진 약 2:1 격자)
Z_TOP = 4.10
HB, HH, TW, TF = 0.150, 0.150, 0.007, 0.010   # H-150x150x7x10
PANEL_T = 0.095         # 흡음판 두께
FRAME_T = 0.064         # 가로프레임 두께(y)
FRAME_H = 0.044         # 프레임 높이/폭
MULLION_W = 0.044       # 중앙 세로 분할 프레임 폭(1.0 m 간격 격자)
MULLION_T = 0.050       # 가로프레임보다 7 mm 얇게 하여 z-fighting 방지


def _paint_neutral_glass(ctx):
    """약한 회색 반사 투명 방음판 재질 (BaseColor + Alpha)."""
    n = ctx.noise(scale_px=16, amp=1.0, seed=9)
    ctx.rgb[..., 0] = np.clip(188.0 + 12.0 * ctx.v + 4.0 * n, 0, 255)
    ctx.rgb[..., 1] = np.clip(194.0 + 12.0 * ctx.v + 4.0 * n, 0, 255)
    ctx.rgb[..., 2] = np.clip(198.0 + 12.0 * ctx.v + 4.0 * n, 0, 255)
    ctx.alpha[...] = 76.0   # 투명도 약 30% 불투명 (뒤 배경 비침)
    ctx.gloss[...] = 0.92


def _paint_bird_sticker(ctx):
    """실사진과 같은 날개 편 맹금류(매) 검은 실루엣 알파 텍스처 (배경 alpha=0)."""
    import numpy as _np
    cache_path = os.path.join(_SIGN_CACHE_DIR, f"bird_hawk_alpha_{ctx.w}x{ctx.h}.npz")
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        if not os.path.exists(cache_path):
            raise RuntimeError(f"PIL unavailable and bird sticker cache missing: {cache_path}")
        with _np.load(cache_path) as d:
            ctx.rgb[...] = d["rgb"].astype(_np.float32)
            ctx.alpha[...] = d["alpha"].astype(_np.float32)
        return
    S = 512
    im = Image.new("RGBA", (S, S), (22, 24, 28, 0))
    drw = ImageDraw.Draw(im)
    # 왼쪽 반쪽 맹금류 외곽선 (머리·부리 + 펼친 날개·갈라진 칼깃 + 부채꼴 꼬리)
    half_left = [
        (0.500, 0.145), (0.476, 0.155), (0.466, 0.195), (0.455, 0.245),  # 머리·목
        (0.395, 0.235), (0.295, 0.190), (0.175, 0.145), (0.040, 0.105),  # 날개 앞전
        (0.082, 0.165), (0.035, 0.190), (0.095, 0.235), (0.048, 0.265),  # 바깥 칼깃(Primary) 1~2
        (0.115, 0.305), (0.075, 0.338), (0.148, 0.370),                  # 칼깃 3~4
        (0.128, 0.415), (0.230, 0.455), (0.345, 0.480), (0.425, 0.495),  # 둘째날개깃 뒷전
        (0.458, 0.560), (0.440, 0.650), (0.378, 0.805), (0.418, 0.825),  # 부채꼴 꼬리 외측
        (0.462, 0.835), (0.500, 0.825),                                   # 꼬리 중앙
    ]
    right_mirror = [(1.0 - x, y) for x, y in reversed(half_left[:-1])]
    poly_norm = half_left + right_mirror
    pts = [(x * S, y * S) for x, y in poly_norm]
    drw.polygon(pts, fill=(22, 24, 28, 255))
    im_rot = im.rotate(-14, resample=Image.Resampling.BICUBIC)
    im_res = im_rot.resize((ctx.w, ctx.h), Image.Resampling.LANCZOS)
    arr = _np.asarray(im_res, dtype=_np.uint8)
    os.makedirs(_SIGN_CACHE_DIR, exist_ok=True)
    _np.savez(cache_path, rgb=arr[..., :3], alpha=arr[..., 3])
    ctx.rgb[...] = arr[..., :3].astype(_np.float32)
    ctx.alpha[...] = arr[..., 3].astype(_np.float32)
    ctx.gloss[...] = 0.28


import numpy as np  # noqa: E402
A = make_atlas([
    "concrete_fluted",
    "steel_post",
    "absorb_warm",
    "panel_frame",
    ("glass", dict(color=(194, 198, 202), gloss=0.92, px=128, painter=_paint_neutral_glass)),
    "acrylic_lod",
    ("bird_sticker", dict(color=(22, 24, 28), gloss=0.28, px=192, painter=_paint_bird_sticker)),
])
x0, x1 = -L / 2, L / 2
xp = x0                 # 지주 중심
xi0, xi1 = x0 + 0.004, x1 - 0.004   # 패널은 웨브 앞까지 홈에 들어간다 (모듈 사이 4+4 mm 여유)


def _add_gusset_fins(mb):
    """H형강 지주 하단 삼각 보강 리브(전후 각 2개, 실사진 noisewall_clear_04 재현)."""
    z_a = Z_BASE + 0.024
    for s in (-1, 1):
        y_in, y_out = s * (HH / 2), s * 0.132
        for dx in (-0.042, 0.042):
            xa, xb = xp + dx - 0.007, xp + dx + 0.007
            mb.box(xa, xb, min(y_in, y_out), max(y_in, y_out), z_a, z_a + 0.09, "steel_post", skip=("bottom",))
    for dx in (-0.10, 0.10):
        for dy in (-0.10, 0.10):
            mb.box(xp + dx - 0.015, xp + dx + 0.015, dy - 0.015, dy + 0.015,
                   Z_BASE + 0.024, Z_BASE + 0.046, "steel_post", skip=("bottom",))


def _bird_decal(mb, cx, cz, size=0.44, flip_x=False):
    """맹금류 알파 컷아웃 데칼(닫힌 2 mm 박스로 lod_check 구멍 0%, 테두리 면은 alpha=0 영역 매핑)."""
    hs = size * 0.5
    (u0, v0), (u1, _), (_, v1), _ = A.uv_full("bird_sticker")
    if flip_x:
        u0, u1 = u1, u0
    # 전후 면은 동일 월드 X-정렬 알파 텍스처, 4 측면은 alpha=0 코너 UV
    y0, y1 = -0.001, 0.001
    mb.quad([(cx - hs, y0, cz - hs), (cx + hs, y0, cz - hs),
             (cx + hs, y0, cz + hs), (cx - hs, y0, cz + hs)],
            [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], "bird_sticker")
    mb.quad([(cx + hs, y1, cz - hs), (cx - hs, y1, cz - hs),
             (cx - hs, y1, cz + hs), (cx + hs, y1, cz + hs)],
            [(u1, v0), (u0, v0), (u0, v1), (u1, v1)], "bird_sticker")
    uv_clear = A.uv_sub("bird_sticker", 0.002, 0.002, 0.015, 0.015)
    mb.quad([(cx - hs, y1, cz - hs), (cx - hs, y0, cz - hs),
             (cx - hs, y0, cz + hs), (cx - hs, y1, cz + hs)], uv_clear, "bird_sticker")
    mb.quad([(cx + hs, y0, cz - hs), (cx + hs, y1, cz - hs),
             (cx + hs, y1, cz + hs), (cx + hs, y0, cz + hs)], uv_clear, "bird_sticker")
    mb.quad([(cx - hs, y0, cz + hs), (cx + hs, y0, cz + hs),
             (cx + hs, y1, cz + hs), (cx - hs, y1, cz + hs)], uv_clear, "bird_sticker")
    mb.quad([(cx - hs, y1, cz - hs), (cx + hs, y1, cz - hs),
             (cx + hs, y0, cz - hs), (cx - hs, y0, cz - hs)], uv_clear, "bird_sticker")


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
    # 투명판 4단 가로 프레임 + 1.0 m 간격 세로 분할 프레임
    for i, z in enumerate(CLEAR):
        za = z if i == 0 else (z - FRAME_H if i == len(CLEAR) - 1 else z - FRAME_H / 2)
        zb = z + FRAME_H if i == 0 else (z if i == len(CLEAR) - 1 else z + FRAME_H / 2)
        if stage == 1 and 0 < i < len(CLEAR) - 1:
            continue
        mb.box(xi0, xi1, -FRAME_T / 2, FRAME_T / 2, za, zb, "panel_frame", skip=())
    if stage == 0:
        # 2.0 m 베이 중앙 세로 멀리언 (x=0.0, 1.0 m 단위 격자 분할)
        mb.box(-MULLION_W / 2, MULLION_W / 2, -MULLION_T / 2, MULLION_T / 2,
               CLEAR[0] + FRAME_H, CLEAR[-1] - FRAME_H, "panel_frame", skip=("bottom", "top"))
        # 단일 얇은 투명 유리판 (8칸 2열×4단 — 단면 1장으로 이중 블렌딩 불투명 현상 제거)
        cols_x = [(xi0, -MULLION_W / 2), (MULLION_W / 2, xi1)]
        for za, zb in zip(CLEAR[:-1], CLEAR[1:]):
            za2 = za + (FRAME_H if za == CLEAR[0] else FRAME_H / 2)
            zb2 = zb - (FRAME_H if zb == CLEAR[-1] else FRAME_H / 2)
            for cx0, cx1 in cols_x:
                uv_g = A.uv("glass")
                gls.quad([(cx0, 0.0, za2), (cx1, 0.0, za2), (cx1, 0.0, zb2), (cx0, 0.0, zb2)], uv_g, "glass")
    else:
        za2, zb2 = CLEAR[0] + FRAME_H, CLEAR[-1] - FRAME_H
        gls.quad([(xi0, 0.0, za2), (xi1, 0.0, za2), (xi1, 0.0, zb2), (xi0, 0.0, zb2)], A.uv("glass"), "glass")

    # 상부 지주 덮개 캡 + 알파 텍스처 맹금류(매) 실루엣 2개(좌상 4단 / 우중 2단 대각 배치)
    if stage == 0:
        mb.box(xp - 0.095, xp + 0.095, -0.095, 0.095, Z_TOP + 0.05, Z_TOP + 0.075, "steel_post")
        _bird_decal(mb, -0.48, 3.79, size=0.44, flip_x=False)
        _bird_decal(mb, 0.50, 2.66, size=0.40, flip_x=True)
    return mb, gls


m0, g0 = build(0)
m1, g1 = build(1)
m2, _ = build(2)
export("NoiseWallClear", dict(main=m0, lod1=m1, lod2=m2, gls=g0, lod1_gls=g1), A, size_hint=(1, 1),
       notes=dict(module_m=L, height_m=Z_TOP, tiling="x 방향 2.0 m 간격", post="H-150x150x7x10"))
