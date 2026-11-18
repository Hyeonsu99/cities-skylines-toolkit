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

# 도로표지규칙 색: 실사진 보정 안내표지 녹색 바탕 + 백색 반사지
SIGN_GREEN = (0, 108, 74)
SIGN_WHITE = (246, 248, 245)


# ---------------------------------------------------------------------------
# 폰트·캔버스 (sintanjin-tollgate 에서 복사 + 반사지 질감·노멀·광택 보강)
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


def _apply_retroreflective_finish(ctx):
    """고휘도 반사지(Type-III/IV) 미세 프리즘 셀·테두리 리벳·은은한 풍화 및 반사광."""
    rgb = ctx.rgb
    bright = (rgb[..., 0] + rgb[..., 1] + rgb[..., 2]) / 3.0
    is_white = np.clip((bright - 140.0) / 80.0, 0.0, 1.0)
    # 미세 프리즘 셀 패턴 (대각 벌집 주기)
    yy, xx = np.mgrid[0:ctx.h, 0:ctx.w]
    cell = (np.sin((xx + yy) * 0.85) * np.sin((xx - yy) * 0.85)).astype(np.float32)
    micro = ctx.noise(scale_px=14, amp=1.0, octaves=2, seed=11)
    grad_v = (0.94 + 0.08 * ctx.v - 0.05 * np.exp(-ctx.v * 7.0)).astype(np.float32)
    rgb *= (grad_v * (1.0 + 0.018 * cell + 0.022 * micro))[..., None]
    # 외곽 프레임 음영 + 약한 먼지
    edge = np.minimum(np.minimum(ctx.u, 1.0 - ctx.u), np.minimum(ctx.v, 1.0 - ctx.v))
    rim_shadow = np.clip(edge / 0.016, 0.72, 1.0).astype(np.float32)
    rgb *= rim_shadow[..., None]
    # 노멀: 테두리 알루미늄 절곡 + 프리즘 요철
    ctx.height += 0.25 * cell + 0.35 * is_white
    ctx.height[edge < 0.012] -= 0.7
    # 광택: 백색 반사글씨/테두리가 녹색 바탕보다 약간 더 높은 반사도
    ctx.gloss[...] = 0.40 + 0.16 * is_white + 0.05 * cell


def draw_canvas(ctx, cache_tag, world_w, world_h, draw_fn, bg=SIGN_GREEN):
    """실제 종횡비 캔버스에 PIL 로 그린 뒤 칸 크기로 줄여 넣고 반사지 질감을 입힌다."""
    cache_path = os.path.join(_SIGN_CACHE_DIR, f"{cache_tag}_v2_{ctx.w}x{ctx.h}.npz")
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        if not os.path.exists(cache_path):
            raise RuntimeError(f"PIL unavailable and sign cache missing: {cache_path}")
        with np.load(cache_path) as d:
            ctx.rgb[...] = d["rgb"].astype(np.float32)
            _apply_retroreflective_finish(ctx)
        return
    ch = 1024
    cw = max(128, int(round(ch * world_w / world_h)))
    img = Image.new("RGB", (cw, ch), bg)
    draw_fn(ImageDraw.Draw(img), cw, ch)
    img = img.resize((ctx.w, ctx.h), Image.Resampling.LANCZOS)
    arr = np.asarray(img, dtype=np.uint8)
    os.makedirs(_SIGN_CACHE_DIR, exist_ok=True)
    np.savez(cache_path, rgb=arr)
    ctx.rgb[...] = arr.astype(np.float32)
    _apply_retroreflective_finish(ctx)


# ---------------------------------------------------------------------------
# 도로표지 그림 요소
# ---------------------------------------------------------------------------

def draw_route_shield(drw, cx, cy, h, number):
    """고속국도 노선번호 표지: 청색 방패 + 상단 적색 띠 + 백색 번호 (도로표지규칙)."""
    w = h * 0.88
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    shield = [(x0, y0 + h * 0.10), (cx, y0), (x1, y0 + h * 0.10), (x1, y0 + h * 0.62),
              (cx, y1), (x0, y0 + h * 0.62)]
    drw.polygon(shield, fill=SIGN_WHITE)
    inset = h * 0.055
    inner = [(x0 + inset, y0 + h * 0.13), (cx, y0 + inset), (x1 - inset, y0 + h * 0.13),
             (x1 - inset, y0 + h * 0.60), (cx, y1 - inset * 1.4), (x0 + inset, y0 + h * 0.60)]
    drw.polygon(inner, fill=(0, 70, 146))
    band = [(x0 + inset, y0 + h * 0.13), (cx, y0 + inset), (x1 - inset, y0 + h * 0.13),
            (x1 - inset, y0 + h * 0.27), (x0 + inset, y0 + h * 0.27)]
    drw.polygon(band, fill=(204, 30, 38))
    f = _fit_font(drw, FONT_EN, number, int(w * 0.58), int(h * 0.50))
    _text_at(drw, cx, cy + h * 0.11, number, f, SIGN_WHITE, "c")


def draw_arrow(drw, cx, cy, size, direction, fill=SIGN_WHITE):
    """한국 도로표지 굵은 화살표 (넓은 삼각 화살촉 + 두꺼운 목). direction: 'up', 'down', 'upright'."""
    s = size
    shaft_w, head_w, head_h = s * 0.24, s * 0.64, s * 0.42
    pts = [(-shaft_w / 2, s * 0.46), (-shaft_w / 2, -s * 0.46 + head_h),
           (-head_w / 2, -s * 0.46 + head_h), (0, -s * 0.46),
           (head_w / 2, -s * 0.46 + head_h), (shaft_w / 2, -s * 0.46 + head_h),
           (shaft_w / 2, s * 0.46)]
    ang = {"up": 0.0, "down": math.pi, "upright": math.radians(42)}[direction]
    ca, sa = math.cos(ang), math.sin(ang)
    drw.polygon([(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts], fill=fill)


def draw_place(drw, x, y_top, kr, en, kr_h, cw_avail, anchor="l"):
    """지명: 국문 위, 영문 아래 (영문 글자 높이 = 국문의 1/2, 실사진 비례 정렬)."""
    fk = _fit_font(drw, FONT_KR, kr, cw_avail, int(kr_h * 1.24))
    fe = _fit_font(drw, FONT_EN, en, cw_avail, int(kr_h * 0.58))
    # 기준선 정렬: bbox 중심 정렬은 g·j 하강부가 있는 영문(Cheongju)을 위로 띄워 행마다 간격이 달라진다
    for text, fnt, base in ((kr, fk, y_top + kr_h * 0.98), (en, fe, y_top + kr_h * 1.59)):
        l, _, r, _ = drw.textbbox((0, 0), text, font=fnt, anchor="ls")
        x0 = x - l if anchor == "l" else x - r if anchor == "r" else x - (l + r) / 2
        drw.text((x0, base), text, font=fnt, fill=SIGN_WHITE, anchor="ls")


def sign_border(drw, cw, ch):
    """실사진과 동일한 바깥 여백 및 두꺼운 백색 라운드 테두리 + 코너 리벳."""
    m = int(ch * 0.026)
    t = max(5, int(ch * 0.022))
    r = int(ch * 0.048)
    drw.rounded_rectangle([m, m, cw - m, ch - m], radius=r, outline=SIGN_WHITE, width=t)
    # 코너 리벳 암시 점
    rv = max(2, int(ch * 0.005))
    for rx in (m * 1.8, cw - m * 1.8):
        for ry in (m * 1.8, ch - m * 1.8):
            drw.ellipse([rx - rv, ry - rv, rx + rv, ry + rv], fill=(215, 224, 218))


# ---------------------------------------------------------------------------
# 재질 painter
# ---------------------------------------------------------------------------

def _paint_concrete(ctx):
    """고속도로 방호벽/기초 콘크리트: 거푸집 결 + 골재 노이즈 + 타이홀 + 하단 노면 오염 + 4 m 신축이음 홈."""
    x, y = ctx.meters()
    tw, th = ctx.tile
    n_coarse = ctx.noise(scale_px=38, amp=1.0, octaves=3, seed=3)
    n_fine = ctx.noise(scale_px=6, amp=1.0, octaves=2, seed=17)
    n_streak = ctx.noise(scale_px=12, amp=1.0, octaves=2, seed=29)
    # 거푸집 판자 미세 수직 이음 (약 1.0 m 간격)
    form_seam = (np.abs(((x + 0.0) % 1.0) - 0.5) > 0.492)
    # 폼타이(볼트 구멍) 1.33 m 간격 × 중단 높이
    tie_u = ((x + 0.66) % 1.333) - 0.666
    tie_v = y - 0.62
    tie_r = np.hypot(tie_u, tie_v)
    tie_hole = tie_r < 0.022
    # 하단 노면 비산 오염 (0 ~ 0.28 m)
    splash_env = np.exp(-np.maximum(0.0, y) / 0.20) * (0.70 + 0.30 * np.clip(n_coarse, -1, 1))
    # 상단부터 내려오는 빗물 얼룩
    rain = np.maximum(0.0, n_streak) * np.clip((y / max(th, 0.1)) ** 0.7, 0.2, 1.0)
    tone = 1.0 + 0.045 * n_coarse + 0.028 * n_fine - 0.14 * splash_env - 0.04 * rain
    ctx.rgb *= tone[..., None]
    # 하단 오염은 약간 흙·타이어 빛
    ctx.rgb[..., 0] *= (1.0 - 0.03 * splash_env)
    ctx.rgb[..., 2] *= (1.0 - 0.08 * splash_env)
    ctx.rgb[form_seam] *= 0.91
    ctx.rgb[tie_hole] *= 0.65
    # 실물 슬립폼 콘크리트는 거푸집 이음·타이홀·신축이음은 뚜렷하되 표면은 잔잔함
    ctx.height += 0.09 * n_fine + 0.05 * n_coarse - 0.14 * splash_env
    ctx.height[form_seam] -= 0.45
    ctx.height[tie_hole] -= 1.35
    # 4 m 양 끝 V자 신축이음 홈 (x=0 / x=tw 근처)
    edge_x = np.minimum(x, tw - x)
    joint = edge_x < 0.026
    ctx.rgb[joint] *= 0.58
    ctx.height[joint] -= 1.6
    ctx.gloss[...] = np.clip(0.16 + 0.03 * n_coarse - 0.04 * splash_env, 0.08, 0.24)


def _paint_concrete_fluted(ctx):
    """방음벽 하단 세로 주름(fluted) 콘크리트 기초벽 (실사진 기반)."""
    x, y = ctx.meters()
    tw, th = ctx.tile
    n_c = ctx.noise(scale_px=26, amp=1.0, octaves=3, seed=7)
    n_f = ctx.noise(scale_px=5, amp=1.0, octaves=2, seed=19)
    rib_phase = (x % 0.055) / 0.055
    flute = np.sin(rib_phase * 2.0 * math.pi)
    cap_band = (y > th - 0.055)
    flute_mask = (~cap_band).astype(np.float32)
    base_moss = np.exp(-np.maximum(0.0, y) / 0.11) * (0.65 + 0.35 * n_c)
    drip = np.maximum(0.0, ctx.noise(scale_px=14, amp=1.0, seed=41)) * (1.0 - 0.5 * ctx.v)
    tone = 1.0 + 0.045 * n_c + 0.02 * n_f + 0.065 * flute * flute_mask - 0.18 * base_moss - 0.09 * drip
    ctx.rgb *= tone[..., None]
    ctx.rgb[..., 1] *= (1.0 + 0.04 * base_moss)
    ctx.rgb[cap_band] *= 1.04
    edge_x = np.minimum(x, tw - x)
    seam = edge_x < 0.018
    ctx.rgb[seam] *= 0.65
    ctx.height += 0.68 * flute * flute_mask + 0.08 * n_f
    ctx.height[cap_band] += 0.28
    ctx.height[seam] -= 1.1
    ctx.gloss[...] = np.clip(0.14 + 0.03 * n_f, 0.08, 0.22)


def _paint_galv(ctx):
    """용융아연도금 스팽글(결정무늬) 및 매끄러운 은회색 금속 질감."""
    n_sp1 = ctx.noise(scale_px=8, amp=1.0, octaves=2, seed=5)
    n_sp2 = ctx.noise(scale_px=22, amp=1.0, octaves=2, seed=23)
    spangle = 0.50 * n_sp1 + 0.50 * n_sp2
    ctx.rgb *= (1.0 + 0.038 * spangle)[..., None]
    ctx.height += 0.14 * spangle
    ctx.gloss[...] = np.clip(ctx.gloss + 0.065 * spangle, 0.42, 0.72)


def _paint_galv_wbeam(ctx):
    """W빔 가드레일 전용 아연도금 판: 스팽글 + 양 끝 8볼트 겹침 이음 + 중앙 지주 볼트."""
    _paint_galv(ctx)
    x, y = ctx.meters()
    tw, th = ctx.tile
    # 4 m 양 끝 겹침 이음부 (모듈 경계에서 정확히 겹침)
    for sx in (0.0, tw):
        lap = np.abs(x - sx) < 0.12
        lap_edge = np.abs(np.abs(x - sx) - 0.12) < 0.008
        ctx.rgb[lap] *= 0.96
        ctx.rgb[lap_edge] *= 0.62
        ctx.height[lap] += 0.30
        ctx.height[lap_edge] -= 0.70
    # 양 끝 8볼트 패턴
    for bx in (0.045, 0.100, tw - 0.100, tw - 0.045):
        for by in (th * 0.24, th * 0.76):
            r = np.hypot(x - bx, y - by)
            bolt = r < 0.015
            ring = (r >= 0.015) & (r < 0.022)
            ctx.rgb[bolt] *= 1.15
            ctx.rgb[ring] *= 0.66
            ctx.height[bolt] += 0.9
            ctx.height[ring] -= 0.35
    # 중앙 x=tw/2 지주 체결 볼트 2개
    for by in (th * 0.32, th * 0.68):
        r = np.hypot(x - tw * 0.5, y - by)
        bolt = r < 0.016
        ctx.rgb[bolt] *= 1.15
        ctx.height[bolt] += 0.9
    dust = np.exp(-np.maximum(0.0, y) / (th * 0.28)) * 0.06
    ctx.rgb *= (1.0 - dust)[..., None]


def _paint_cassette_wall(ctx, cols, rows, warm=False):
    """실사진(경부고속도로) 사각 카세트 금속 흡음판 격자 + 내부 루버 타공 + 빗물·노면 풍화."""
    x, y = ctx.meters()
    tw, th = ctx.tile
    cw = tw / cols
    rh = th / rows
    cx = (x % cw) / cw          # 0..1 카세트 내 가로
    cy = (y % rh) / rh          # 0..1 카세트 내 세로
    row_i = np.minimum((y / rh).astype(int), rows - 1)

    n_weath = ctx.noise(scale_px=26, amp=1.0, octaves=3, seed=13)
    n_streak = ctx.noise(scale_px=10, amp=1.0, octaves=2, seed=31)
    # 각 카세트 외곽 프레임(밝은 테두리) vs 내부 타공 리세스
    frame = (cx < 0.11) | (cx > 0.89) | (cy < 0.13) | (cy > 0.87)
    bevel = (cx < 0.145) | (cx > 0.855) | (cy < 0.165) | (cy > 0.835)
    inner = ~bevel
    # 내부 미세 루버 / 다중 슬릿 타공 격자
    slit_y = ((cy - 0.165) / 0.67) * 7.0
    slit_x = ((cx - 0.145) / 0.71) * 3.0
    slit_hole = inner & ((slit_y % 1.0) < 0.46) & ((slit_x % 1.0) < 0.84)

    if warm:
        # NoiseWallClear 하단: 상단 1~2단 따뜻한 베이지스톤 -> 하단 노면 비산 어두운 갈회색
        base_grad = np.clip(0.82 + 0.22 * (row_i / max(1, rows - 1)), 0.80, 1.04)
        ctx.rgb *= (base_grad + 0.04 * n_weath)[..., None]
        # 가끔 얇은 녹슨 빗물 자국 (사진 noisewall_clear_04 재현)
        rust = np.exp(-((x - tw * 0.62) / 0.08) ** 2) * np.exp(-((y - th * 0.72) / 0.10) ** 2)
        ctx.rgb[..., 0] = np.clip(ctx.rgb[..., 0] + 24.0 * rust, 0, 255)
        ctx.rgb[..., 2] = np.clip(ctx.rgb[..., 2] - 18.0 * rust, 0, 255)
    else:
        # NoiseWallMetal: 실물 엑슬루 옆 진한 챠콜브라운 상부 + 하단 2단 밝은 스톤그레이 이형/풍화 띠
        low_band = (row_i <= 1).astype(np.float32)
        c_dark = np.array([78.0, 72.0, 70.0], np.float32)
        c_low = np.array([126.0, 117.0, 108.0], np.float32)
        mix = low_band[..., None]
        ctx.rgb[...] = c_dark * (1.0 - mix) + c_low * mix
        ctx.rgb *= (1.0 + 0.06 * n_weath - 0.05 * np.maximum(0.0, n_streak) * (1.0 - ctx.v * 0.4))[..., None]

    # 카세트 격자 음영/노멀
    ctx.rgb[frame] *= 1.18
    ctx.rgb[bevel & ~frame] *= 0.78
    ctx.rgb[slit_hole] *= 0.62
    # 가로·세로 판 이음 실선
    seam = (cx < 0.03) | (cx > 0.97) | (cy < 0.04) | (cy > 0.96)
    ctx.rgb[seam] *= 0.68

    ctx.height[frame] += 0.75
    ctx.height[bevel & ~frame] -= 0.45
    ctx.height[slit_hole] -= 0.95
    ctx.height[seam] -= 1.20
    ctx.height += 0.18 * n_weath
    ctx.gloss[...] = np.where(frame, 0.44, 0.30) + 0.04 * n_weath


def _paint_absorb_panel(ctx):
    """기본 흡음판: 실사진 기준 챠콜·스톤그레이 4열×7단 카세트 금속 흡음판 (NoiseWallMetal)."""
    _paint_cassette_wall(ctx, cols=4, rows=7, warm=False)


def _paint_absorb_warm(ctx):
    """투명방음벽 하단 흡음판: 실사진 기준 따뜻한 스톤베이지 6열×3단 카세트 (NoiseWallClear)."""
    _paint_cassette_wall(ctx, cols=6, rows=3, warm=True)


def _paint_clear_glass(ctx):
    """투명 방음판 전면: 고무 가스켓 테두리 + 2마리 맹금류 조류충돌방지 스티커 + 미세 먼지."""
    u, v = ctx.u, ctx.v
    # 창 유리 바탕 (약한 상하 스카이 반사 그라데이션)
    n = ctx.noise(scale_px=18, amp=1.0, seed=9)
    ctx.rgb[..., 0] = 172.0 + 14.0 * v + 4.0 * n
    ctx.rgb[..., 1] = 200.0 + 12.0 * v + 4.0 * n
    ctx.rgb[..., 2] = 208.0 + 10.0 * v + 4.0 * n
    # 수직 고무 패킹 (H지주 양쪽 클램프) & 수평 가로살 가스켓 힌트
    v_seal = (u < 0.025) | (u > 0.975)
    h_seal = (v < 0.025) | (v > 0.975)
    ctx.rgb[v_seal] = (58.0, 62.0, 66.0)
    ctx.rgb[h_seal] = (128.0, 124.0, 108.0)
    ctx.gloss[v_seal | h_seal] = 0.25

    # 순수 numpy 맹금류(매) 비행 실루엣 2개 (상단 좌측 + 중단 우측 대각 배치)
    aspect = ctx.w / max(1, ctx.h)
    for cx, cy, sc, ang_deg in ((0.30, 0.72, 0.13, -18.0), (0.72, 0.38, 0.125, 16.0)):
        ang = math.radians(ang_deg)
        dx = (u - cx) * aspect
        dy = v - cy
        rx = dx * math.cos(ang) + dy * math.sin(ang)
        ry = -dx * math.sin(ang) + dy * math.cos(ang)
        ax = np.abs(rx)
        wing_y = 0.28 * sc * np.sin(np.minimum(1.0, ax / sc) * math.pi * 0.85) - 0.10 * sc * (ax / sc) ** 1.5
        chord = 0.21 * sc * np.clip(1.0 - 0.62 * (ax / sc) ** 1.4, 0.12, 1.0)
        in_wing = (ax <= sc) & (np.abs(ry - wing_y) <= chord)
        in_body = (ax <= sc * 0.11) & (ry >= -0.46 * sc) & (ry <= 0.34 * sc)
        in_tail = (ry >= -0.52 * sc) & (ry <= -0.18 * sc) & (ax <= sc * (0.09 + 0.14 * (-ry / sc - 0.18)))
        bird = in_wing | in_body | in_tail
        ctx.rgb[bird] = (28.0, 30.0, 34.0)
        ctx.gloss[bird] = 0.35


def _paint_sign_back(ctx):
    """표지판 뒷면 알루미늄 판: 브러시드 메탈 결 + 1.0 m 수직 판 이음선."""
    x, _y = ctx.meters()
    n_grain = ctx.noise(scale_px=5, amp=1.0, seed=14)
    n_broad = ctx.noise(scale_px=24, amp=1.0, seed=21)
    ctx.rgb *= (1.0 + 0.035 * n_grain + 0.03 * n_broad)[..., None]
    seam = np.abs((x % 1.0) - 0.5) > 0.493
    ctx.rgb[seam] *= 0.82
    ctx.height += 0.22 * n_grain
    ctx.height[seam] -= 0.5
    ctx.gloss[...] = 0.42 + 0.05 * n_grain


def _paint_hazard_yb(ctx):
    """가드레일 단부/지주용 황·흑 45도 반사 사선 경고무늬."""
    s = (ctx.u + ctx.v) * 4.5
    is_y = (s % 1.0) < 0.5
    ctx.rgb[is_y] = (242.0, 192.0, 22.0)
    ctx.rgb[~is_y] = (28.0, 30.0, 32.0)
    n = ctx.noise(scale_px=4, amp=1.0, seed=8)
    ctx.rgb *= (1.0 + 0.025 * n)[..., None]
    ctx.gloss[...] = np.where(is_y, 0.82, 0.35)


def _paint_reflector(ctx):
    yy, xx = np.mgrid[0:ctx.h, 0:ctx.w]
    prism_cell = np.sin(xx * 0.9) * np.sin(yy * 0.9)
    ctx.rgb *= (0.96 + 0.05 * prism_cell)[..., None]
    ctx.height += 0.5 * prism_cell
    ctx.gloss[...] = 0.92


def make_atlas(tags, size=1024):
    """필요한 재질만 담은 아틀라스 (소품 반복 배치 경량화 유지 + 실물 질감 상향)."""
    defs = {
        "concrete": dict(color=(168, 162, 152), gloss=0.16, px=448, tile=(4.0, 1.30),
                         painter=_paint_concrete, normal_strength=1.4),
        "concrete_fluted": dict(color=(162, 154, 140), gloss=0.14, px=384, tile=(2.0, 0.65),
                                painter=_paint_concrete_fluted, normal_strength=2.3),
        "steel_post": dict(color=(132, 134, 132), metal=0.62, gloss=0.48, px=192, tile=(1.0, 2.5),
                           painter=_paint_galv, normal_strength=1.5),
        "absorb_panel": dict(color=(80, 74, 72), metal=0.38, gloss=0.34, px=512, tile=(2.0, 3.5),
                             painter=_paint_absorb_panel, normal_strength=3.2),
        "absorb_warm": dict(color=(178, 166, 156), metal=0.28, gloss=0.32, px=384, tile=(2.0, 1.25),
                            painter=_paint_absorb_warm, normal_strength=3.0),
        "panel_frame": dict(color=(164, 162, 156), metal=0.65, gloss=0.52, px=128, tile=(2.0, 0.5),
                            painter=_paint_galv, normal_strength=1.4),
        "glass": dict(color=(174, 204, 212), gloss=0.92, px=320, painter=_paint_clear_glass),
        "acrylic_lod": dict(color=(152, 184, 192), gloss=0.80, px=64),
        "bird_sticker": dict(color=(26, 28, 32), gloss=0.22, px=32),
        "galv": dict(color=(186, 190, 190), metal=0.72, gloss=0.58, px=256, tile=(1.5, 2.5),
                     painter=_paint_galv, normal_strength=1.6),
        "galv_wbeam": dict(color=(188, 192, 192), metal=0.74, gloss=0.58, px=512, tile=(4.0, 0.45),
                           painter=_paint_galv_wbeam, normal_strength=2.6),
        "reflector_y": dict(color=(244, 194, 20), gloss=0.92, px=64, painter=_paint_reflector, normal_strength=2.0),
        "reflector_w": dict(color=(242, 244, 242), gloss=0.92, px=64, painter=_paint_reflector, normal_strength=2.0),
        "hazard_yb": dict(color=(242, 192, 22), gloss=0.78, px=128, painter=_paint_hazard_yb),
        "sign_back": dict(color=(158, 164, 166), metal=0.60, gloss=0.45, px=256, tile=(2.0, 1.5),
                          painter=_paint_sign_back, normal_strength=1.5),
        "gantry_steel": dict(color=(176, 182, 184), metal=0.68, gloss=0.54, px=256, tile=(1.5, 3.0),
                             painter=_paint_galv, normal_strength=1.6),
    }
    A = K.Atlas(size=size, pad=8)
    for t in tags:
        if isinstance(t, tuple):            # (name, kwargs) 간판 등 프롭 전용 칸
            A.add(t[0], **t[1])
        else:
            A.add(t, **defs[t])
    return A


# ---------------------------------------------------------------------------
# 기하 헬퍼 (실세계 미터 UV 매핑 지원)
# ---------------------------------------------------------------------------

def _cell_uv_box(A, tag, fu0, fv0, fu1, fv1):
    u0, v0, u1, v1 = A._uvrect(tag)
    e = 0.5 / A.size
    du = u1 - u0 - 2.0 * e
    dv = v1 - v0 - 2.0 * e
    U0 = u0 + e + du * max(0.0, min(1.0, fu0))
    U1 = u0 + e + du * max(0.0, min(1.0, fu1))
    V0 = v0 + e + dv * max(0.0, min(1.0, fv0))
    V1 = v0 + e + dv * max(0.0, min(1.0, fv1))
    return U0, V0, U1, V1


def prism(mb, A, p0, p1, r, tag, sides=4, caps=(False, True), tiled=True, max_stacks=2):
    """p0→p1 축의 n각 기둥 (원형 강관 근사). tiled=True 이면 둘레·길이 방향 미터 UV 적용."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = p1 - p0
    length = float(np.linalg.norm(d))
    if length < 1e-6:
        return
    d /= length
    ref = np.array([0, 0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0, 0])
    e1 = np.cross(d, ref); e1 /= np.linalg.norm(e1)
    e2 = np.cross(d, e1)
    off = math.pi / sides
    ring = [r * (math.cos(off + 2 * math.pi * i / sides) * e1 + math.sin(off + 2 * math.pi * i / sides) * e2)
            for i in range(sides)]

    use_tile = tiled and A.is_tiled(tag)
    if use_tile:
        tw, th = A.tile_size(tag)
        circ = 2.0 * math.pi * r
        n_stacks = min(max_stacks, max(1, math.ceil(length / th - 1e-6))) if sides >= 6 else 1
        du_total = min(1.0, circ / tw)
    else:
        n_stacks = 1
        uv_flat = A.uv(tag)

    for s in range(n_stacks):
        t0, t1 = s / n_stacks, (s + 1) / n_stacks
        pa = p0 + d * (t0 * length)
        pb = p0 + d * (t1 * length)
        seg_len = (t1 - t0) * length
        for i in range(sides):
            a, b = ring[i], ring[(i + 1) % sides]
            if use_tile:
                fu0, fu1 = du_total * (i / sides), du_total * ((i + 1) / sides)
                fv1 = min(1.0, seg_len / th)
                U0, V0, U1, V1 = _cell_uv_box(A, tag, fu0, 0.0, fu1, fv1)
                q_uv = [(U0, V0), (U1, V0), (U1, V1), (U0, V1)]
            else:
                q_uv = uv_flat
            mb.quad([tuple(pa + a), tuple(pa + b), tuple(pb + b), tuple(pb + a)], q_uv, tag)

    uv_cap = A.uv(tag)
    if caps[1]:
        for i in range(1, sides - 1):
            mb.tri([tuple(p1 + ring[0]), tuple(p1 + ring[i]), tuple(p1 + ring[i + 1])], uv_cap[:3], tag)
    if caps[0]:
        for i in range(1, sides - 1):
            mb.tri([tuple(p0 + ring[0]), tuple(p0 + ring[i + 1]), tuple(p0 + ring[i])], uv_cap[:3], tag)


def extrude(mb, A, poly, x0, x1, tag, cap="fan", map_mode="perim", z_max=None):
    """(y, z) 단면을 x0→x1 로 압출. map_mode='world_z' 면 높이(z)와 길이(x)를 아틀라스 타일에 직접 매핑."""
    n = len(poly)
    w_m = abs(x1 - x0)
    is_tiled = A.is_tiled(tag)
    if is_tiled:
        tw, th = A.tile_size(tag)
        fu_span = min(1.0, w_m / tw)
    else:
        tw, th, fu_span = 1.0, 1.0, 1.0
    uv_flat = A.uv(tag)

    # 둘레 누적 길이 계산 (map_mode='perim' 용)
    seg_s = [0.0]
    for k in range(n):
        (ya, za), (yb, zb) = poly[k], poly[(k + 1) % n]
        seg_s.append(seg_s[-1] + math.hypot(yb - ya, zb - za))
    perim = max(1e-6, seg_s[-1])
    z_min = min(p[1] for p in poly)
    z_top = z_max if z_max is not None else max(p[1] for p in poly)
    z_span = max(1e-6, z_top - z_min)

    for k in range(n):
        (ya, za), (yb, zb) = poly[k], poly[(k + 1) % n]
        if za == 0.0 and zb == 0.0:     # 땅에 닿는 밑면은 만들지 않는다
            continue
        if is_tiled:
            if map_mode == "world_z":
                # th 기준 실제 미터 높이로 매핑 (상단·하단 방향 무관하게 지상 0 m 기준 정렬)
                fva = max(0.0, min(1.0, (za - z_min) / th))
                fvb = max(0.0, min(1.0, (zb - z_min) / th))
            elif map_mode == "rail_z":
                fva = max(0.0, min(1.0, (za - z_min) / z_span))
                fvb = max(0.0, min(1.0, (zb - z_min) / z_span))
            else:
                fva = (seg_s[k] % th) / th
                fvb = fva + math.hypot(yb - ya, zb - za) / th
                if fvb > 1.0:
                    fva, fvb = 0.0, min(1.0, math.hypot(yb - ya, zb - za) / th)
            U0, _, U1, _ = _cell_uv_box(A, tag, 0.0, 0.0, fu_span, 1.0)
            _, Va, _, Vb = _cell_uv_box(A, tag, 0.0, min(fva, fvb), 1.0, max(fva, fvb))
            va_uv, vb_uv = (Va, Vb) if fva <= fvb else (Vb, Va)
            q_uv = [(U0, va_uv), (U1, va_uv), (U1, vb_uv), (U0, vb_uv)]
        else:
            q_uv = uv_flat
        mb.quad([(x0, ya, za), (x1, ya, za), (x1, yb, zb), (x0, yb, zb)], q_uv, tag)

    if cap == "fan":
        cy = sum(p[0] for p in poly) / n
        cz = sum(p[1] for p in poly) / n
        for k in range(n):
            (ya, za), (yb, zb) = poly[k], poly[(k + 1) % n]
            mb.tri([(x0, cy, cz), (x0, ya, za), (x0, yb, zb)], uv_flat[:3], tag)
            mb.tri([(x1, cy, cz), (x1, yb, zb), (x1, ya, za)], uv_flat[:3], tag)
    elif cap == "strip":
        h = n // 2
        P, Q = poly[:h], poly[h:][::-1]
        for k in range(h - 1):
            (pa, pb, qa, qb) = (P[k], P[k + 1], Q[k], Q[k + 1])
            mb.quad([(x0, *pa), (x0, *pb), (x0, *qb), (x0, *qa)], uv_flat, tag)
            mb.quad([(x1, *qa), (x1, *qb), (x1, *pb), (x1, *pa)], uv_flat, tag)


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
