"""한국 고속도로 소품 세트 공용 모듈 (재질·간판 텍스처·기하 헬퍼).

간판 텍스처 방식은 projects/sintanjin-tollgate/sintanjin_tollgate_cs2.py 의
_load_font / _fit_font / _text_center / .npz 캐시 방식을 복사해 소품용으로 줄인 것이다.
(원본 폴더는 수정하지 않는다.)
"""
import math
import os
import sys

import numpy as np


def find_kit():
    path = os.path.dirname(os.path.abspath(__file__))
    for _ in range(4):
        if os.path.exists(os.path.join(path, "cs2kit.py")):
            return path
        path = os.path.dirname(path)
    raise RuntimeError("cs2kit.py not found")


sys.path.insert(0, find_kit())
import cs2kit as K  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
_SIGN_CACHE_DIR = os.path.join(HERE, "work", "_sign_cache")

FONT_KR = [r"C:\Windows\Fonts\malgunbd.ttf", r"C:\Windows\Fonts\malgun.ttf", r"C:\Windows\Fonts\gulim.ttc"]
FONT_EN = [r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\malgunbd.ttf", r"C:\Windows\Fonts\arial.ttf"]

# 도로표지규칙 색: 안내표지 녹색 바탕 + 백색 글자 (색값은 사진 기준 # estimated)
SIGN_GREEN = (0, 112, 74)
SIGN_WHITE = (250, 252, 250)


# ---------------------------------------------------------------------------
# 폰트·캔버스 (sintanjin-tollgate 에서 복사)
# ---------------------------------------------------------------------------

def _load_font(candidates, size):
    from PIL import ImageFont
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                pass
    return ImageFont.load_default()


def _fit_font(drw, candidates, text, max_w, init_px):
    sz = init_px
    while sz > 16:
        fnt = _load_font(candidates, sz)
        bbox = drw.textbbox((0, 0), text, font=fnt)
        if (bbox[2] - bbox[0]) <= max_w:
            return fnt
        sz = max(16, int(sz * 0.90))
    return _load_font(candidates, 16)


def _text_at(drw, x, y_center, text, font, fill, anchor_x="l"):
    bbox = drw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    if anchor_x == "c":
        x = x - tw * 0.5
    elif anchor_x == "r":
        x = x - tw
    drw.text((x - bbox[0], y_center - th * 0.5 - bbox[1]), text, font=font, fill=fill)
    return tw


def draw_canvas(ctx, cache_tag, world_w, world_h, draw_fn, bg=SIGN_GREEN):
    """실제 종횡비 캔버스에 PIL 로 그린 뒤 칸 크기로 줄여 넣는다. PIL 없는 Blender 실행은 .npz 캐시 사용."""
    cache_path = os.path.join(_SIGN_CACHE_DIR, f"{cache_tag}_{ctx.w}x{ctx.h}.npz")
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        if not os.path.exists(cache_path):
            raise RuntimeError(f"PIL unavailable and sign cache missing: {cache_path}")
        with np.load(cache_path) as d:
            ctx.rgb[...] = d["rgb"].astype(np.float32)
        return
    ch = 1024
    cw = int(round(ch * world_w / world_h))
    img = Image.new("RGB", (cw, ch), bg)
    draw_fn(ImageDraw.Draw(img), cw, ch)
    img = img.resize((ctx.w, ctx.h), Image.Resampling.LANCZOS)
    arr = np.asarray(img, dtype=np.uint8)
    ctx.rgb[...] = arr.astype(np.float32)
    os.makedirs(_SIGN_CACHE_DIR, exist_ok=True)
    np.savez(cache_path, rgb=arr)


# ---------------------------------------------------------------------------
# 도로표지 그림 요소
# ---------------------------------------------------------------------------

def draw_route_shield(drw, cx, cy, h, number):
    """고속국도 노선번호 표지: 청색 방패 + 상단 적색 띠 + 백색 번호 (도로표지규칙 고속국도 노선표지 형태)."""
    w = h * 0.86
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    shield = [(x0, y0 + h * 0.10), (cx, y0), (x1, y0 + h * 0.10), (x1, y0 + h * 0.62),
              (cx, y1), (x0, y0 + h * 0.62)]
    drw.polygon(shield, fill=SIGN_WHITE)
    inset = h * 0.05
    inner = [(x0 + inset, y0 + h * 0.13), (cx, y0 + inset), (x1 - inset, y0 + h * 0.13),
             (x1 - inset, y0 + h * 0.60), (cx, y1 - inset * 1.4), (x0 + inset, y0 + h * 0.60)]
    drw.polygon(inner, fill=(0, 74, 152))
    band = [(x0 + inset, y0 + h * 0.13), (cx, y0 + inset), (x1 - inset, y0 + h * 0.13),
            (x1 - inset, y0 + h * 0.27), (x0 + inset, y0 + h * 0.27)]
    drw.polygon(band, fill=(208, 32, 40))
    f = _fit_font(drw, FONT_EN, number, int(w * 0.6), int(h * 0.50))
    _text_at(drw, cx, cy + h * 0.10, number, f, SIGN_WHITE, "c")


def draw_arrow(drw, cx, cy, size, direction, fill=SIGN_WHITE):
    """도로표지 화살표. direction: 'up' 직진, 'down' 차로지정, 'upright' 우측 진출."""
    s = size
    shaft_w, head_w, head_h = s * 0.16, s * 0.52, s * 0.38
    pts = [(-shaft_w / 2, s / 2), (-shaft_w / 2, -s / 2 + head_h), (-head_w / 2, -s / 2 + head_h),
           (0, -s / 2), (head_w / 2, -s / 2 + head_h), (shaft_w / 2, -s / 2 + head_h), (shaft_w / 2, s / 2)]
    ang = {"up": 0.0, "down": math.pi, "upright": math.radians(40)}[direction]
    ca, sa = math.cos(ang), math.sin(ang)
    drw.polygon([(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts], fill=fill)


def draw_place(drw, x, y_top, kr, en, kr_h, cw_avail, anchor="l"):
    """지명: 국문 위, 영문 아래 (영문 글자 높이 = 국문의 1/2, 도로표지규칙 영문 병기 비율 # estimated)."""
    fk = _fit_font(drw, FONT_KR, kr, cw_avail, int(kr_h * 1.25))
    fe = _fit_font(drw, FONT_EN, en, cw_avail, int(kr_h * 0.62))
    _text_at(drw, x, y_top + kr_h * 0.5, kr, fk, SIGN_WHITE, anchor)
    _text_at(drw, x, y_top + kr_h * 1.42, en, fe, SIGN_WHITE, anchor)


def sign_border(drw, cw, ch):
    """백색 테두리 (안쪽 여백 포함)."""
    m = int(ch * 0.025)
    t = max(4, int(ch * 0.018))
    drw.rounded_rectangle([m, m, cw - m, ch - m], radius=int(ch * 0.05), outline=SIGN_WHITE, width=t)


# ---------------------------------------------------------------------------
# 재질 painter
# ---------------------------------------------------------------------------

def _paint_concrete(ctx):
    n = ctx.noise(scale_px=24, amp=1.0, seed=3)
    ctx.rgb *= (1.0 + 0.025 * n)[..., None]
    ctx.height += 0.3 * n
    x, y = ctx.meters()
    joint = np.abs(((x + 1.0) % 4.0) - 2.0) > 1.985        # 4 m 신축이음 홈 (# estimated)
    ctx.rgb[joint] *= 0.72
    ctx.height[joint] -= 1.0


def _paint_galv(ctx):
    n = ctx.noise(scale_px=10, amp=1.0, seed=5)
    ctx.rgb *= (1.0 + 0.05 * n)[..., None]
    ctx.gloss += 0.05 * n


def _paint_absorb_panel(ctx):
    """금속 흡음판 전면: 0.5 m 단 이음 + 슬릿 타공 줄 (흡음형 방음판 전면 슬릿형)."""
    x, y = ctx.meters()
    yy = y % 0.5
    joint = (yy < 0.012) | (yy > 0.488)
    rib = (np.abs(yy - 0.25) < 0.012)
    slit_row = ((yy > 0.05) & (yy < 0.22)) | ((yy > 0.28) & (yy < 0.45))
    slit = slit_row & (((y * 40.0) % 1.0) < 0.35) & (((x * 8.0) % 1.0) < 0.82)
    ctx.rgb[slit] *= 0.55
    ctx.height[slit] -= 0.8
    ctx.rgb[rib] *= 1.08
    ctx.height[rib] += 0.6
    ctx.rgb[joint] *= 0.60
    ctx.height[joint] -= 1.2


def _paint_reflector(ctx):
    ctx.gloss[...] = 0.9


def make_atlas(tags, size=1024):
    """필요한 재질만 담은 작은 아틀라스 (소품은 반복 배치되므로 1024 기본)."""
    defs = {
        "concrete": dict(color=(176, 174, 166), gloss=0.18, px=256, tile=(4.0, 1.0), painter=_paint_concrete),
        "steel_post": dict(color=(118, 124, 122), metal=0.55, gloss=0.42, px=64, painter=_paint_galv),
        "absorb_panel": dict(color=(122, 150, 146), metal=0.35, gloss=0.40, px=256, tile=(2.0, 1.0),
                             painter=_paint_absorb_panel, normal_strength=2.6),
        "panel_frame": dict(color=(178, 184, 186), metal=0.6, gloss=0.50, px=64),
        "glass": dict(color=(168, 204, 210), gloss=0.92, px=32),
        "acrylic_lod": dict(color=(140, 176, 182), gloss=0.80, px=32),
        "galv": dict(color=(182, 186, 186), metal=0.70, gloss=0.55, px=64, painter=_paint_galv),
        "reflector_y": dict(color=(246, 196, 20), gloss=0.9, px=32, painter=_paint_reflector),
        "reflector_w": dict(color=(240, 242, 240), gloss=0.9, px=32, painter=_paint_reflector),
        "sign_back": dict(color=(150, 156, 158), metal=0.55, gloss=0.40, px=64),
        "gantry_steel": dict(color=(164, 170, 172), metal=0.60, gloss=0.45, px=64, painter=_paint_galv),
    }
    A = K.Atlas(size=size, pad=8)
    for t in tags:
        if isinstance(t, tuple):            # (name, kwargs) 간판 등 프롭 전용 칸
            A.add(t[0], **t[1])
        else:
            A.add(t, **defs[t])
    return A


# ---------------------------------------------------------------------------
# 기하 헬퍼
# ---------------------------------------------------------------------------

def prism(mb, A, p0, p1, r, tag, sides=4, caps=(False, True)):
    """p0→p1 축의 n각 기둥 (원형 강관 근사). caps=(아래, 위)."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = p1 - p0
    d /= np.linalg.norm(d)
    ref = np.array([0, 0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0, 0])
    e1 = np.cross(d, ref); e1 /= np.linalg.norm(e1)
    e2 = np.cross(d, e1)
    off = math.pi / sides
    ring = [r * (math.cos(off + 2 * math.pi * i / sides) * e1 + math.sin(off + 2 * math.pi * i / sides) * e2)
            for i in range(sides)]
    uv = A.uv(tag)
    for i in range(sides):
        a, b = ring[i], ring[(i + 1) % sides]
        mb.quad([tuple(p0 + a), tuple(p0 + b), tuple(p1 + b), tuple(p1 + a)], uv, tag)   # 바깥 법선
    if caps[1]:
        for i in range(1, sides - 1):
            mb.tri([tuple(p1 + ring[0]), tuple(p1 + ring[i]), tuple(p1 + ring[i + 1])], uv[:3], tag)
    if caps[0]:
        for i in range(1, sides - 1):
            mb.tri([tuple(p0 + ring[0]), tuple(p0 + ring[i + 1]), tuple(p0 + ring[i])], uv[:3], tag)


def extrude(mb, A, poly, x0, x1, tag, cap="fan"):
    """(y, z) 단면을 x0→x1 로 압출. poly 는 y 오른쪽·z 위 기준 시계방향(왼쪽 아래에서 위로 시작).
    cap: 'fan' = 무게중심 부채꼴(별 모양 단면), 'strip' = 앞 절반·뒤 절반 짝 사각형(얇은 판 단면), None = 끝면 없음."""
    uv = A.uv(tag)
    n = len(poly)
    for k in range(n):
        (ya, za), (yb, zb) = poly[k], poly[(k + 1) % n]
        if za == 0.0 and zb == 0.0:     # 땅에 닿는 밑면은 만들지 않는다
            continue
        mb.quad([(x0, ya, za), (x1, ya, za), (x1, yb, zb), (x0, yb, zb)], uv, tag)
    if cap == "fan":
        cy = sum(p[0] for p in poly) / n
        cz = sum(p[1] for p in poly) / n
        for k in range(n):
            (ya, za), (yb, zb) = poly[k], poly[(k + 1) % n]
            mb.tri([(x0, cy, cz), (x0, ya, za), (x0, yb, zb)], uv[:3], tag)
            mb.tri([(x1, cy, cz), (x1, yb, zb), (x1, ya, za)], uv[:3], tag)
    elif cap == "strip":
        h = n // 2
        P, Q = poly[:h], poly[h:][::-1]
        for k in range(h - 1):
            (pa, pb, qa, qb) = (P[k], P[k + 1], Q[k], Q[k + 1])
            mb.quad([(x0, *pa), (x0, *pb), (x0, *qb), (x0, *qa)], uv, tag)
            mb.quad([(x1, *qa), (x1, *qb), (x1, *pb), (x1, *pa)], uv, tag)


def h_beam(mb, x, y, z0, z1, b, h, tw, tf, tag, simple=False):
    """H형강 지주. 플랜지는 벽면과 평행(±y), 웨브는 벽 길이(x) 수직 → 양쪽 홈에 패널이 끼워진다."""
    if simple:
        mb.box(x - b / 2, x + b / 2, y - h / 2, y + h / 2, z0, z1, tag, skip=("bottom",))
        return
    mb.box(x - b / 2, x + b / 2, y - h / 2, y - h / 2 + tf, z0, z1, tag, skip=("bottom",))
    mb.box(x - b / 2, x + b / 2, y + h / 2 - tf, y + h / 2, z0, z1, tag, skip=("bottom",))
    mb.box(x - tw / 2, x + tw / 2, y - h / 2 + tf, y + h / 2 - tf, z0, z1, tag, skip=("bottom", "front", "back"))


def sign_face(mb, A, x0, x1, y, z0, z1, tag):
    """-Y(도로 쪽) 를 보는 간판 면 1장, 전체 그림 UV."""
    mb.quad(K.face_pts("y", y, -1, x0, x1, z0, z1), A.uv_full(tag), tag)


def sign_panel(mb, A, x0, x1, y0, y1, z0, z1, face_tag, back_tag="sign_back"):
    """앞면 그림 + 나머지 5면 알루미늄 판."""
    sign_face(mb, A, x0, x1, y0, z0, z1, face_tag)
    mb.box(x0, x1, y0, y1, z0, z1, back_tag, skip=("front",))


def export(name, meshes, A, size_hint=None, notes=None):
    res = K.export_asset(name, 1, meshes, A, K.out_dir_from_argv("output"), lod2_tex=256,
                         lot=size_hint, front_yard=0.0, notes=notes)
    print(f"Exported {name} -> {res}")
    return res
