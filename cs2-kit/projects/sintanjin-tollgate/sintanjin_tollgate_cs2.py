"""경부고속도로 신탄진IC 영업소 (Sintanjin Tollgate) 정밀 CS2 에셋 생성기.

실측 근거 (대전광역시 대덕구 덕암로 207 / 36.43942°N, 127.42217°E):
- 7차선 + 6아일랜드 + 2외곽연석 (전폭 40.60 m, X ∈ [-20.30, +20.30])
- 중앙 스카이블루 경사 파시아 캐노피 (31.6 m × 11.4 m) + 옥상 양면 간판(신탄진 | Sintanjin)
- 비대칭 청록색 폴리카보네이트 아치 (서측 4.18 m 균일 돌출 / 동측 E1 단축 2.48 m + E2·E3 장대 8.08 m)
- 북측 1차선 반아치(Wing 0), 오렌지-실버 톨부스 4동 + 지하통로 초록 돔 3동
- 전후 3개 포털 갠트리 (서측 라임그린 2차선, 동측 실버 1차선, 동측 오렌지 화물 1차선)
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
from local import kitext as KX


# ---------------------------------------------------------------------------
# 폰트 및 PIL 텍스처 유틸리티
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


FONT_KR = [
    r"C:\Windows\Fonts\malgunbd.ttf",
    r"C:\Windows\Fonts\malgun.ttf",
    r"C:\Windows\Fonts\gulim.ttc",
]
FONT_EN = [
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\malgunbd.ttf",
    r"C:\Windows\Fonts\arial.ttf",
]


_SIGN_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "work", "_sign_cache")

# 고해상도 다중 배너 팩킹 테이블 (cell_name, u0, v0, u1, v1)
SIGN_SUB = {
    "sign_sjt_kr": ("signs_sjt", 0.005, 0.506, 0.995, 0.994),
    "sign_sjt_en": ("signs_sjt", 0.005, 0.006, 0.995, 0.494),
    "led_hipass":  ("led_banners", 0.005, 0.6797, 0.995, 0.9922),
    "led_warn":    ("led_banners", 0.005, 0.3457, 0.995, 0.6582),
    "led_freight": ("led_banners", 0.005, 0.0117, 0.995, 0.3242),
}


def _draw_canvas_to_ctx(ctx, cache_tag, world_w, world_h, draw_fn, emis_fn=None, bg=(16, 36, 60)):
    """실세계 종횡비(world_w : world_h) 캔버스에서 PIL로 그린 뒤 .npz 캐시와 ctx에 반영 (Blender NumPy 전용 호환)."""
    cache_path = os.path.join(_SIGN_CACHE_DIR, f"{cache_tag}_{ctx.w}x{ctx.h}.npz")
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        if not os.path.exists(cache_path):
            raise RuntimeError(f"PIL unavailable and sign cache missing: {cache_path}")
        with np.load(cache_path) as d:
            ctx.rgb[...] = d["rgb"].astype(np.float32)
            ctx.emis[...] = d["emis"].astype(np.float32)
        return

    if abs(world_w - world_h) < 1e-4:
        cw, ch = ctx.w, ctx.h
    else:
        scale = max(64, int(1536 / max(world_w, world_h)))
        cw = max(256, min(2048, int(round(world_w * scale))))
        ch = max(128, min(1024, int(round(world_h * scale))))
    img = Image.new("RGB", (cw, ch), bg)
    drw = ImageDraw.Draw(img)
    draw_fn(drw, cw, ch)
    if (cw, ch) != (ctx.w, ctx.h):
        img = img.resize((ctx.w, ctx.h), Image.Resampling.LANCZOS)
    rgb_arr = np.asarray(img, dtype=np.uint8)
    ctx.rgb[...] = rgb_arr.astype(np.float32)

    if emis_fn is not None:
        eimg = Image.new("L", (cw, ch), 0)
        edrw = ImageDraw.Draw(eimg)
        emis_fn(edrw, cw, ch)
        if (cw, ch) != (ctx.w, ctx.h):
            eimg = eimg.resize((ctx.w, ctx.h), Image.Resampling.LANCZOS)
        emis_arr = np.asarray(eimg, dtype=np.float32) / 255.0
        ctx.emis[...] = emis_arr
    else:
        emis_arr = ctx.emis.copy()

    os.makedirs(_SIGN_CACHE_DIR, exist_ok=True)
    np.savez(cache_path, rgb=rgb_arr, emis=emis_arr.astype(np.float16))


def _text_center(drw, cw, ch, text, font, fill, x_offset=0, y_offset=0):
    bbox = drw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (cw - tw) * 0.5 - bbox[0] + x_offset
    y = (ch - th) * 0.5 - bbox[1] + y_offset
    drw.text((x, y), text, font=font, fill=fill)


def _apply_led_dot_matrix(ctx, pitch_px=4):
    """LED 전광판 픽셀 도트 피치 및 미세 발광 질감 부여."""
    h, w = ctx.h, ctx.w
    yy = np.arange(h)[:, None] % pitch_px
    xx = np.arange(w)[None, :] % pitch_px
    dot = np.where((yy == 0) | (xx == 0), 0.78, 1.0).astype(np.float32)
    ctx.rgb *= dot[..., None]
    ctx.emis *= np.where((yy == 0) | (xx == 0), 0.70, 1.0).astype(np.float32)


# ---------------------------------------------------------------------------
# 아틀라스 재질 정의 (4096x4096 풀 패킹 고해상도 텍스처)
# ---------------------------------------------------------------------------

def _paint_blue_fascia(ctx):
    # 스카이블루 법랑/도장 강판 카세트 패널 (실측 세루리안 스카이블루 + 은은한 세로 줄눈·풍화)
    ctx.joints(cols=5, rows=1, width_m=0.012, depth=1.05, darken=0.11, tone=3.5, seed=11)
    # 상하 절곡 에지 베벨 음영
    edge_bot = np.clip((0.055 - ctx.v) / 0.055, 0.0, 1.0)
    edge_top = np.clip((ctx.v - 0.945) / 0.055, 0.0, 1.0)
    ctx.rgb *= (1.0 - 0.14 * edge_bot + 0.06 * edge_top)[..., None]
    ctx.height += 0.30 * edge_top - 0.45 * edge_bot
    ctx.grain(amp=2.4, scale_px=2, height=0.10, seed=12)
    ctx.stains(amount=0.06, scale_px=64, streaks=0.40, seed=13)


def _paint_teal_roof(ctx):
    mx, my = ctx.meters()
    seam = np.exp(-((np.mod(mx, 0.50) - 0.25) ** 2) / (0.022 ** 2)).astype(np.float32)
    rib_fine = np.exp(-((np.mod(mx, 0.125) - 0.0625) ** 2) / (0.012 ** 2)).astype(np.float32)
    ctx.rgb += (20.0 * seam + 5.0 * rib_fine)[..., None]
    ctx.height += 0.90 * seam + 0.20 * rib_fine
    ctx.grain(amp=3.0, scale_px=3, height=0.12, seed=22)
    ctx.stains(amount=0.12, scale_px=56, streaks=0.30, seed=21)


def _paint_soffit(ctx):
    # 처마 하부 웜메탈릭 브론즈-토프 E-W 리브 스팬드럴 루버 천장 (실측 under_look_n/s 기준)
    mx, _my = ctx.meters()
    # mx 방향 변화 -> 차량 진행(Y)과 나란한 종방향 리브 루버 형성, 0.15m 피치로 선명한 명암 대비
    slat = 0.5 + 0.5 * np.cos(mx * (2.0 * math.pi / 0.15))
    ctx.rgb *= (0.72 + 0.44 * slat)[..., None]
    ctx.height += 0.92 * slat
    ctx.gloss = np.clip(ctx.gloss + 0.18 * slat, 0.22, 0.68)
    ctx.joints(cols=2, rows=3, width_m=0.024, depth=1.05, darken=0.28, tone=5.0, seed=31)
    ctx.grain(amp=3.8, scale_px=2, height=0.16, seed=32)
    ctx.stains(amount=0.08, scale_px=48, streaks=0.25, seed=33)


def _paint_polycarb(ctx):
    # 맑은 반투명 아쿠아-아이스블루 복층 폴리카보네이트 + 깔끔한 백색/알루미늄 멀리온 격자
    ctx.joints(cols=4, rows=3, width_m=0.036, depth=0.80, darken=0.14, tone=2.5, seed=41)
    ctx.rgb += ctx.noise(scale_px=32, amp=2.0, octaves=2, seed=42)[..., None]
    mx, my = ctx.meters()
    # 복층 골판 미세 리브 (0.125m 피치)
    rib = 0.5 + 0.5 * np.sin(mx * (2.0 * math.pi / 0.125))
    ctx.rgb += (6.5 * rib)[..., None]
    ctx.height += 0.22 * rib
    # 밝은 백색/알루미늄 펄린·서까래 격자 + 얇은 흑색 가스켓 테두리
    dx_p = np.abs((mx % 1.0) - 0.5)
    dy_p = np.abs((my % 0.8333) - 0.4167)
    gasket = ((dx_p > 0.460) & (dx_p <= 0.473)) | ((dy_p > 0.382) & (dy_p <= 0.394))
    mullion = (dx_p > 0.473) | (dy_p > 0.394)
    ctx.rgb[gasket] = ctx.rgb[gasket] * 0.35 + np.array((42, 48, 52), dtype=np.float32) * 0.65
    ctx.rgb[mullion] = ctx.rgb[mullion] * 0.15 + np.array((236, 242, 244), dtype=np.float32) * 0.85
    ctx.height[mullion] += 0.55
    ctx.gloss = np.clip(ctx.gloss + 0.10 * rib, 0.35, 0.96)
    ctx.gloss[mullion] = 0.45
    ctx.gloss[gasket] = 0.22
    ctx.stains(amount=0.02, scale_px=64, streaks=0.15, seed=43)


def _paint_concrete(ctx):
    # 현장타설 방호벽 콘크리트 + 거푸집 이음·폼타이 및 하단 노면 물튀김 얼룩
    ctx.joints(cols=2, rows=2, width_m=0.014, depth=0.65, darken=0.22, tone=5.5, seed=51)
    mx, my = ctx.meters()
    tie_u = ((mx % 1.5) - 0.75) ** 2
    tie_v = ((my % 1.5) - 0.75) ** 2
    tie = np.exp(-(tie_u + tie_v) / (0.04 ** 2)).astype(np.float32)
    ctx.rgb *= (1.0 - 0.22 * tie)[..., None]
    ctx.height -= 0.45 * tie
    ctx.grain(amp=8.5, scale_px=2, height=0.40, seed=52)
    ctx.stains(amount=0.14, scale_px=42, streaks=0.65, seed=53)


def _paint_blue_curb(ctx):
    ctx.grain(amp=6.0, scale_px=2, height=0.28, seed=61)
    ctx.stains(amount=0.10, scale_px=36, streaks=0.50, seed=62)
    dirt = np.clip(1.0 - ctx.v * 2.2, 0.0, 1.0)
    ctx.rgb *= (1.0 - 0.34 * dirt)[..., None]
    ctx.gloss *= (1.0 - 0.40 * dirt)


def _paint_booth_metal(ctx):
    ctx.joints(cols=3, rows=2, width_m=0.010, depth=0.80, darken=0.24, tone=4.0, seed=71)
    ctx.grain(amp=2.6, scale_px=2, height=0.10, seed=72)
    ctx.stains(amount=0.04, scale_px=48, streaks=0.25, seed=73)


def _paint_trim_white(ctx):
    """백색 아연/알루미늄 트림·거터·코핑 패널 (6m×6m 타일로 분할 절감 + 1.0m×1.5m 줄눈 질감 유지)."""
    ctx.joints(cols=6, rows=4, width_m=0.010, depth=0.75, darken=0.20, tone=3.2, seed=74)
    ctx.grain(amp=2.4, scale_px=2, height=0.10, seed=75)
    ctx.stains(amount=0.04, scale_px=48, streaks=0.25, seed=76)
    n = ctx.noise(scale_px=20, amp=1.0, octaves=2, seed=79)
    ctx.gloss[...] = np.clip(ctx.gloss + 0.07 * n, 0.34, 0.62)


def _paint_painted_steel(ctx):
    ctx.grain(amp=2.4, scale_px=3, height=0.10, seed=77)
    ctx.stains(amount=0.05, scale_px=40, streaks=0.30, seed=78)


def _paint_green_dome(ctx):
    ctx.joints(cols=1, rows=10, width_m=0.022, depth=1.1, darken=0.28, tone=3.5, seed=81)
    ctx.grain(amp=2.2, scale_px=2, height=0.10, seed=83)
    ctx.stains(amount=0.07, scale_px=36, streaks=0.35, seed=82)


def _paint_lamp_strip(ctx):
    # 프리즘 아크릴 등기구 루버 셀 + 중앙 고휘도 발광
    lx = (np.sin(ctx.u * 24.0 * math.pi) > 0.85) | (np.sin(ctx.v * 6.0 * math.pi) > 0.85)
    center = np.exp(-((ctx.u - 0.5) ** 2) / 0.14).astype(np.float32)
    ctx.rgb = np.where(lx[..., None], np.array((210, 214, 218), dtype=np.float32),
                       np.array((248, 250, 240), dtype=np.float32))
    ctx.height += np.where(lx, -0.35, 0.10).astype(np.float32)
    ctx.emis[...] = np.where(lx, 0.35, 0.82 + 0.18 * center)


def _paint_window(ctx):
    # 네 부스 모두 켜진 상태에서 실내 밝기와 반사광 높이만 다르게 표현한다.
    subtle = ctx.noise(scale_px=24, amp=3.5, octaves=2, seed=85)
    u, v = ctx.u * K.REF_GRID, ctx.v * K.REF_GRID
    col = u.astype(int)
    glow = np.array([0.80, 0.62, 0.74, 0.55, 0.0])[col]
    height = v % 1.0
    ctx.rgb[...] = np.array((52, 88, 106), dtype=np.float32)
    ctx.rgb += (subtle + 14 * height)[..., None]
    ctx.gloss[...] = 0.90
    ctx.emis[...] = np.clip(glow * (0.70 + 0.30 * height) + 0.004 * subtle, 0.0, 1.0)


def _fit_font(drw, candidates, text, max_w, init_px):
    """텍스트가 지정된 폭(max_w)을 넘지 않도록 폰트 크기를 자동 조절."""
    sz = init_px
    while sz > 16:
        fnt = _load_font(candidates, sz)
        bbox = drw.textbbox((0, 0), text, font=fnt)
        if (bbox[2] - bbox[0]) <= max_w:
            return fnt
        sz = max(16, int(sz * 0.90))
    return _load_font(candidates, 16)


def _render_packed_bands(ctx, cache_tag, band_specs, bg=(12, 26, 44)):
    """각 배너를 실세계 종횡비(world_w : world_h) 캔버스로 그린 뒤 1024x1024 아틀라스 밴드에 무왜곡 LANCZOS 배치."""
    cache_path = os.path.join(_SIGN_CACHE_DIR, f"{cache_tag}_{ctx.w}x{ctx.h}.npz")
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        if not os.path.exists(cache_path):
            raise RuntimeError(f"PIL unavailable and sign cache missing: {cache_path}")
        with np.load(cache_path) as d:
            ctx.rgb[...] = d["rgb"].astype(np.float32)
            ctx.emis[...] = d["emis"].astype(np.float32)
        return

    sheet = Image.new("RGB", (ctx.w, ctx.h), bg)
    esheet = Image.new("L", (ctx.w, ctx.h), 0)
    sy = ctx.h / 1024.0
    for py0, py1, world_w, world_h, band_bg, draw_fn, emis_fn in band_specs:
        ry0, ry1 = int(round(py0 * sy)), int(round(py1 * sy))
        bh = max(32, ry1 - ry0)
        aspect = world_w / max(world_h, 1e-4)
        ch = 512
        cw = max(256, min(2560, int(round(ch * aspect))))
        im = Image.new("RGB", (cw, ch), band_bg)
        drw = ImageDraw.Draw(im)
        draw_fn(drw, cw, ch)
        im = im.resize((ctx.w, bh), Image.Resampling.LANCZOS)
        sheet.paste(im, (0, ry0))

        eim = Image.new("L", (cw, ch), 0)
        edrw = ImageDraw.Draw(eim)
        emis_fn(edrw, cw, ch)
        eim = eim.resize((ctx.w, bh), Image.Resampling.LANCZOS)
        esheet.paste(eim, (0, ry0))

    rgb_arr = np.asarray(sheet, dtype=np.uint8)
    emis_arr = np.asarray(esheet, dtype=np.float32) / 255.0
    ctx.rgb[...] = rgb_arr.astype(np.float32)
    ctx.emis[...] = emis_arr

    os.makedirs(_SIGN_CACHE_DIR, exist_ok=True)
    np.savez(cache_path, rgb=rgb_arr, emis=emis_arr.astype(np.float16))


def _paint_signs_sjt(ctx):
    # 상단 절반: 신탄진, 하단 절반: Sintanjin (실측 west_close_look_se 기준 2.95:1 딥네이비 캐비닛 + 꽉 찬 백색 채널문자)
    navy_bg = (22, 52, 92)

    def draw_sjt(text, candidates, size_ratio):
        def _fn(drw, cw, ch):
            drw.rectangle([0, 0, cw, ch], fill=navy_bg)
            for sx in (cw // 3, (2 * cw) // 3):
                drw.line([(sx, 0), (sx, ch)], fill=(16, 38, 68), width=3)
            drw.line([(0, ch // 2), (cw, ch // 2)], fill=(18, 42, 74), width=2)
            drw.rectangle([0, 0, cw - 1, ch - 1], outline=(168, 184, 202), width=4)
            pad = max(10, int(ch * 0.05))
            fnt = _fit_font(drw, candidates, text, int((cw - 2 * pad) * 0.94), int(ch * size_ratio))
            _text_center(drw, cw, ch, text, fnt, (248, 250, 255), y_offset=-int(ch * 0.01))
        return _fn

    def emis_sjt(text, candidates, size_ratio):
        def _fn(edrw, cw, ch):
            pad = max(10, int(ch * 0.05))
            fnt = _fit_font(edrw, candidates, text, int((cw - 2 * pad) * 0.94), int(ch * size_ratio))
            _text_center(edrw, cw, ch, text, fnt, 250, y_offset=-int(ch * 0.01))
        return _fn

    bands = [
        (4, 506, 5.25, 1.78, navy_bg, draw_sjt("신탄진", FONT_KR, 0.80), emis_sjt("신탄진", FONT_KR, 0.80)),
        (518, 1020, 5.25, 1.78, navy_bg, draw_sjt("Sintanjin", FONT_EN, 0.72), emis_sjt("Sintanjin", FONT_EN, 0.72)),
    ]
    _render_packed_bands(ctx, "signs_sjt", bands, bg=navy_bg)
    ctx.gloss[...] = 0.44


def _paint_led_banners(ctx):
    # 3단 실세계 종횡비(4.10:0.92, 4.10:0.92, 4.80:0.86) 무왜곡 흑색 LED 배너 팩킹 (west_far_look_e/east_near_look_w 기준)
    def draw_hp(drw, cw, ch):
        drw.rectangle([0, 0, cw, ch], fill=(14, 18, 22))
        drw.rectangle([6, 6, cw - 7, ch - 7], outline=(52, 60, 70), width=6)
        f_main = _fit_font(drw, FONT_KR, "하이패스 전용", int(cw * 0.88), int(ch * 0.62))
        _text_center(drw, cw, ch, "하이패스 전용", f_main, (168, 252, 86), y_offset=-int(ch * 0.02))

    def emis_hp(edrw, cw, ch):
        f_main = _fit_font(edrw, FONT_KR, "하이패스 전용", int(cw * 0.88), int(ch * 0.62))
        _text_center(edrw, cw, ch, "하이패스 전용", f_main, 248, y_offset=-int(ch * 0.02))

    def draw_warn(drw, cw, ch):
        drw.rectangle([0, 0, cw, ch], fill=(14, 18, 22))
        drw.rectangle([6, 6, cw - 7, ch - 7], outline=(52, 60, 70), width=6)
        split_x = int(cw * 0.58)
        f1 = _fit_font(drw, FONT_KR, "상습미납차량", int((split_x - 24) * 0.92), int(ch * 0.46))
        f2 = _fit_font(drw, FONT_KR, "형사고발", int((cw - split_x - 24) * 0.92), int(ch * 0.46))
        _text_center(drw, split_x - 10, ch, "상습미납차량", f1, (166, 250, 86), x_offset=10, y_offset=-int(ch * 0.02))
        _text_center(drw, cw - split_x - 10, ch, "형사고발", f2, (255, 138, 42), x_offset=split_x, y_offset=-int(ch * 0.02))

    def emis_warn(edrw, cw, ch):
        split_x = int(cw * 0.58)
        f1 = _fit_font(edrw, FONT_KR, "상습미납차량", int((split_x - 24) * 0.92), int(ch * 0.46))
        f2 = _fit_font(edrw, FONT_KR, "형사고발", int((cw - split_x - 24) * 0.92), int(ch * 0.46))
        _text_center(edrw, split_x - 10, ch, "상습미납차량", f1, 244, x_offset=10, y_offset=-int(ch * 0.02))
        _text_center(edrw, cw - split_x - 10, ch, "형사고발", f2, 246, x_offset=split_x, y_offset=-int(ch * 0.02))

    def draw_fr(drw, cw, ch):
        # 실측 east_near_look_w 기준: [화물] (오렌지) | [하이패스] (초록) | [통행권] (오렌지) 3분할 흑색 LED
        drw.rectangle([0, 0, cw, ch], fill=(16, 18, 22))
        x1 = int(cw * 0.23)
        x2 = int(cw * 0.69)
        m = 8
        drw.rectangle([m, m, x1 - 4, ch - m], fill=(22, 18, 14), outline=(228, 108, 36), width=5)
        drw.rectangle([x1 + 4, m, x2 - 4, ch - m], fill=(14, 22, 18), outline=(92, 110, 98), width=4)
        drw.rectangle([x2 + 4, m, cw - m, ch - m], fill=(22, 18, 14), outline=(228, 108, 36), width=5)
        f1 = _fit_font(drw, FONT_KR, "화물", int((x1 - 18) * 0.92), int(ch * 0.72))
        f2 = _fit_font(drw, FONT_KR, "하이패스", int((x2 - x1 - 18) * 0.92), int(ch * 0.72))
        f3 = _fit_font(drw, FONT_KR, "통행권", int((cw - x2 - 18) * 0.92), int(ch * 0.72))
        _text_center(drw, x1 - 12, ch, "화물", f1, (255, 178, 56), x_offset=6)
        _text_center(drw, x2 - x1 - 8, ch, "하이패스", f2, (88, 244, 120), x_offset=x1 + 4)
        _text_center(drw, cw - x2 - 12, ch, "통행권", f3, (255, 178, 56), x_offset=x2 + 4)

    def emis_fr(edrw, cw, ch):
        x1 = int(cw * 0.23)
        x2 = int(cw * 0.69)
        f1 = _fit_font(edrw, FONT_KR, "화물", int((x1 - 18) * 0.92), int(ch * 0.72))
        f2 = _fit_font(edrw, FONT_KR, "하이패스", int((x2 - x1 - 18) * 0.92), int(ch * 0.72))
        f3 = _fit_font(edrw, FONT_KR, "통행권", int((cw - x2 - 18) * 0.92), int(ch * 0.72))
        _text_center(edrw, x1 - 12, ch, "화물", f1, 240, x_offset=6)
        _text_center(edrw, x2 - x1 - 8, ch, "하이패스", f2, 248, x_offset=x1 + 4)
        _text_center(edrw, cw - x2 - 12, ch, "통행권", f3, 240, x_offset=x2 + 4)

    bands = [
        (8, 328, 4.10, 0.92, (14, 18, 22), draw_hp, emis_hp),
        (350, 670, 4.10, 0.92, (14, 18, 22), draw_warn, emis_warn),
        (692, 1012, 4.80, 0.86, (16, 18, 22), draw_fr, emis_fr),
    ]
    _render_packed_bands(ctx, "led_banners", bands, bg=(14, 18, 24))
    _apply_led_dot_matrix(ctx, pitch_px=4)
    ctx.gloss[...] = 0.48


def _paint_sig_green_down(ctx):
    def draw(drw, cw, ch):
        drw.rectangle([0, 0, cw, ch], fill=(16, 20, 22))
        drw.rectangle([10, 10, cw - 11, ch - 11], outline=(52, 58, 66), width=max(8, cw // 56))
        drw.ellipse([int(cw * 0.10), int(ch * 0.10), int(cw * 0.90), int(ch * 0.90)],
                    fill=(14, 24, 18), outline=(36, 46, 40), width=4)
        cx, cy = cw * 0.5, ch * 0.5
        s = min(cw, ch)
        drw.rectangle([cx - s * 0.095, cy - s * 0.29, cx + s * 0.095, cy + s * 0.04], fill=(46, 248, 114))
        poly = [(cx - s * 0.28, cy + s * 0.02), (cx + s * 0.28, cy + s * 0.02), (cx, cy + s * 0.32)]
        drw.polygon(poly, fill=(46, 248, 114))

    def emis(edrw, cw, ch):
        cx, cy = cw * 0.5, ch * 0.5
        s = min(cw, ch)
        edrw.rectangle([cx - s * 0.095, cy - s * 0.29, cx + s * 0.095, cy + s * 0.04], fill=255)
        poly = [(cx - s * 0.28, cy + s * 0.02), (cx + s * 0.28, cy + s * 0.02), (cx, cy + s * 0.32)]
        edrw.polygon(poly, fill=255)

    _draw_canvas_to_ctx(ctx, "sig_green_down", 1.0, 1.0, draw, emis)
    _apply_led_dot_matrix(ctx, pitch_px=4)
    ctx.gloss[...] = 0.58


def _paint_sig_red_x(ctx):
    def draw(drw, cw, ch):
        drw.rectangle([0, 0, cw, ch], fill=(16, 20, 22))
        drw.rectangle([10, 10, cw - 11, ch - 11], outline=(52, 58, 66), width=max(8, cw // 56))
        drw.ellipse([int(cw * 0.10), int(ch * 0.10), int(cw * 0.90), int(ch * 0.90)],
                    fill=(26, 14, 14), outline=(48, 34, 34), width=4)
        m = int(cw * 0.25)
        w = max(14, int(cw * 0.14))
        drw.line([(m, m), (cw - m, ch - m)], fill=(252, 56, 44), width=w)
        drw.line([(cw - m, m), (m, ch - m)], fill=(252, 56, 44), width=w)

    def emis(edrw, cw, ch):
        m = int(cw * 0.25)
        w = max(14, int(cw * 0.14))
        edrw.line([(m, m), (cw - m, ch - m)], fill=255, width=w)
        edrw.line([(cw - m, m), (m, ch - m)], fill=255, width=w)

    _draw_canvas_to_ctx(ctx, "sig_red_x", 1.0, 1.0, draw, emis)
    _apply_led_dot_matrix(ctx, pitch_px=4)
    ctx.gloss[...] = 0.58


def _paint_sign_30(ctx):
    def draw(drw, cw, ch):
        drw.rectangle([0, 0, cw, ch], fill=(224, 228, 232))
        m = int(cw * 0.06)
        drw.ellipse([m, m, cw - m, ch - m], fill=(248, 248, 250), outline=(212, 32, 34), width=max(24, cw // 9))
        fnt = _load_font(FONT_EN, int(ch * 0.46))
        _text_center(drw, cw, ch, "30", fnt, (24, 26, 30))

    _draw_canvas_to_ctx(ctx, "sign_30", 1.0, 1.0, draw, None, bg=(224, 228, 232))
    ctx.gloss[...] = 0.48


def _paint_sign_notruck(ctx):
    def draw(drw, cw, ch):
        drw.rectangle([0, 0, cw, ch], fill=(224, 228, 232))
        m = int(cw * 0.06)
        drw.ellipse([m, m, cw - m, ch - m], fill=(248, 248, 250), outline=(212, 32, 34), width=max(24, cw // 9))
        cx, cy = cw * 0.5, ch * 0.52
        drw.rectangle([cx - cw * 0.22, cy - ch * 0.12, cx + cw * 0.06, cy + ch * 0.08], fill=(32, 36, 42))
        drw.rectangle([cx + cw * 0.07, cy - ch * 0.06, cx + cw * 0.20, cy + ch * 0.08], fill=(32, 36, 42))
        drw.ellipse([cx - cw * 0.17, cy + ch * 0.06, cx - cw * 0.09, cy + ch * 0.14], fill=(32, 36, 42))
        drw.ellipse([cx + cw * 0.09, cy + ch * 0.06, cx + cw * 0.17, cy + ch * 0.14], fill=(32, 36, 42))
        d0, d1 = int(cw * 0.22), int(cw * 0.78)
        drw.line([(d0, d0), (d1, d1)], fill=(212, 32, 34), width=max(16, cw // 14))

    _draw_canvas_to_ctx(ctx, "sign_notruck", 1.0, 1.0, draw, None, bg=(224, 228, 232))
    ctx.gloss[...] = 0.48


def _paint_sign_30_panel(ctx):
    # 서측 라임그린 갠트리 하부 현수형 청색 상단바 + 백색 사각 제한속도 30 표지판 (west_far_look_e 기준)
    def draw(drw, cw, ch):
        drw.rectangle([0, 0, cw, ch], fill=(242, 244, 246))
        hdr_h = int(ch * 0.24)
        drw.rectangle([6, 6, cw - 7, hdr_h], fill=(24, 86, 174))
        drw.rectangle([6, 6, cw - 7, ch - 7], outline=(56, 64, 74), width=5)
        f_top = _fit_font(drw, FONT_KR, "하이패스 전용", int(cw * 0.82), int(hdr_h * 0.56))
        _text_center(drw, cw, hdr_h, "하이패스 전용", f_top, (248, 250, 255), y_offset=2)
        f_sub = _fit_font(drw, FONT_KR, "무단통과 시 과태료 부과", int(cw * 0.82), int(ch * 0.085))
        _text_center(drw, cw, int(ch * 0.14), "무단통과 시 과태료 부과", f_sub, (32, 38, 46), y_offset=int(ch * 0.26))
        r = int(min(cw * 0.33, ch * 0.24))
        cx, cy = int(cw * 0.50), int(ch * 0.69)
        drw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(250, 250, 252), outline=(214, 34, 36), width=max(16, r // 4))
        f_num = _load_font(FONT_EN, int(r * 1.10))
        _text_center(drw, cw, int(r * 2.0), "30", f_num, (24, 26, 30), y_offset=cy - r)

    _draw_canvas_to_ctx(ctx, "sign_30_panel", 0.84, 1.04, draw, None, bg=(242, 244, 246))
    ctx.gloss[...] = 0.46


def _paint_barrier_arm(ctx):
    band = ((ctx.u * 6.0) % 1.0) < 0.5
    red = np.array((214, 38, 36), dtype=np.float32)
    white = np.array((244, 246, 248), dtype=np.float32)
    ctx.rgb = np.where(band[..., None], red, white)
    ctx.grain(amp=1.8, scale_px=2, height=0.06, seed=91)
    ctx.gloss[...] = 0.56


def _paint_bollard_stripe(ctx):
    u, v = ctx.u, ctx.v
    band = ((u * 2.0 + v * 2.0) % 1.0) < 0.5
    yellow = np.array((244, 186, 22), dtype=np.float32)
    black = np.array((26, 28, 32), dtype=np.float32)
    ctx.rgb = np.where(band[..., None], yellow, black)
    ctx.grain(amp=2.0, scale_px=2, height=0.10, seed=92)
    ctx.gloss[...] = 0.45


def make_atlas(size=4096):
    A = K.Atlas(size=size, pad=16)
    # 1024x1024 히어로 타일 및 다중 배너 팩킹 (4K 아틀라스 공간 효율 극대화)
    A.add("polycarb", color=(156, 214, 218), metal=0.05, gloss=0.88, px=1024, tile=(4.0, 2.5), painter=_paint_polycarb, normal_strength=1.4)
    A.add("blue_fascia", color=(46, 140, 202), metal=0.22, gloss=0.54, px=1024, tile=(6.0, 1.50), painter=_paint_blue_fascia, normal_strength=2.2)
    A.add("signs_sjt", color=(22, 52, 92), gloss=0.44, emissive=(225, 240, 255), px=1024, painter=_paint_signs_sjt)
    A.add("led_banners", color=(14, 46, 86), gloss=0.48, emissive=(255, 226, 130), px=1024, painter=_paint_led_banners)
    A.add("concrete", color=(206, 208, 202), metal=0.0, gloss=0.20, px=1024, tile=(3.0, 3.0), painter=_paint_concrete, normal_strength=2.6)
    A.add("soffit", color=(114, 96, 78), metal=0.30, gloss=0.42, px=1024, tile=(3.0, 3.0), painter=_paint_soffit, normal_strength=3.2)
    A.add("teal_roof", color=(48, 116, 144), metal=0.34, gloss=0.44, px=768, tile=(3.0, 3.0), painter=_paint_teal_roof, normal_strength=2.6)

    # 512x512 주요 구조재 및 신호/원형·현수 표지
    A.add("window", color=(58, 96, 112), ctrl=(0, 0, 0), metal=0.0, gloss=0.90, emissive=(255, 232, 190), px=512, tile=(1.5, 1.5), painter=_paint_window)
    A.add("blue_curb", color=(28, 86, 168), metal=0.0, gloss=0.35, px=512, tile=(2.0, 0.5), painter=_paint_blue_curb, normal_strength=2.2)
    A.add("booth_orange", color=(230, 108, 30), metal=0.18, gloss=0.52, px=512, tile=(2.0, 1.5), painter=_paint_booth_metal, normal_strength=2.4)
    A.add("booth_silver", color=(204, 210, 216), metal=0.42, gloss=0.56, px=512, tile=(2.0, 1.5), painter=_paint_booth_metal, normal_strength=2.2)
    A.add("trim_white", color=(236, 240, 244), metal=0.18, gloss=0.48, px=512, tile=(6.0, 6.0), painter=_paint_trim_white, normal_strength=1.8)
    A.add("green_dome", color=(34, 126, 78), metal=0.14, gloss=0.48, px=512, tile=(2.0, 2.0), painter=_paint_green_dome, normal_strength=2.4)
    A.add("sig_green_down", color=(16, 20, 22), gloss=0.58, emissive=(50, 255, 114), px=512, painter=_paint_sig_green_down)
    A.add("sig_red_x", color=(16, 20, 22), gloss=0.58, emissive=(255, 56, 44), px=512, painter=_paint_sig_red_x)
    A.add("sign_30", color=(244, 246, 248), gloss=0.48, px=512, painter=_paint_sign_30)
    A.add("sign_notruck", color=(244, 246, 248), gloss=0.48, px=512, painter=_paint_sign_notruck)
    A.add("sign_30_panel", color=(242, 244, 246), gloss=0.46, px=512, painter=_paint_sign_30_panel)

    # 256x256 소형 디테일·프레임
    A.add("bollard_stripe", color=(244, 186, 22), gloss=0.45, px=256, tile=(0.3, 0.9), painter=_paint_bollard_stripe)
    A.add("barrier_arm", color=(214, 38, 36), gloss=0.56, px=256, painter=_paint_barrier_arm)
    A.add("dark_steel", color=(44, 50, 56), metal=0.48, gloss=0.44, px=256, painter=_paint_painted_steel)
    A.add("gantry_lime", color=(190, 218, 38), metal=0.22, gloss=0.50, px=256, painter=_paint_painted_steel)
    A.add("gantry_orange", color=(230, 102, 28), metal=0.22, gloss=0.50, px=256, painter=_paint_painted_steel)
    A.add("gantry_grey", color=(190, 194, 198), metal=0.40, gloss=0.50, px=256, painter=_paint_painted_steel)
    A.add("rail_blue", color=(28, 102, 184), metal=0.28, gloss=0.52, px=256, painter=_paint_painted_steel)
    A.add("terminal_blue", color=(26, 84, 162), metal=0.24, gloss=0.48, px=256, painter=_paint_painted_steel)
    A.add("safety_yellow", color=(240, 192, 28), metal=0.16, gloss=0.48, px=256, painter=_paint_painted_steel)
    A.add("lamp_strip", color=(248, 250, 240), metal=0.0, gloss=0.82, emissive=(255, 242, 215), px=256, painter=_paint_lamp_strip)
    return A


# ---------------------------------------------------------------------------
# 기하 조립 헬퍼 (폐합 솔리드, CCW 외향 법선, 동일 평면 겹침 방지)
# ---------------------------------------------------------------------------

def _uv_seg(A, tag, u_len, v_len):
    """아틀라스 타일 셀 내부 UV [0..fu, 0..fv] 생성."""
    if A is not None and A.is_tiled(tag):
        return A.uv_tile(tag, u_len, v_len)
    return A.uv(tag) if A is not None else [(0, 0), (1, 0), (1, 1), (0, 1)]


def _emit_graphic_quad(mb, A, pts, tag, fallback_tag):
    """단일 그래픽 태그(또는 SIGN_SUB 다중 배너)를 정확한 UV로 사각면에 매핑."""
    if not tag:
        mb.quad(pts, A.uv(fallback_tag), fallback_tag)
        return
    if tag in SIGN_SUB:
        cell, u0, v0, u1, v1 = SIGN_SUB[tag]
        mb.quad(pts, A.uv_sub(cell, u0, v0, u1, v1), cell)
    else:
        mb.quad(pts, A.uv_full(tag), tag)


def build_graphic_box(mb, A, x0, x1, y0, y1, z0, z1, frame_tag, front_tag=None, back_tag=None, skip=()):
    """동일 평면 중복 없이 앞/뒤 full-art UV를 갖는 6면 폐합 박스 생성."""
    sk = set(skip)
    if "front" not in sk:
        pts = K.face_pts("y", y0, -1, x0, x1, z0, z1)
        _emit_graphic_quad(mb, A, pts, front_tag, frame_tag)
    if "back" not in sk:
        pts = K.face_pts("y", y1, +1, x0, x1, z0, z1)
        _emit_graphic_quad(mb, A, pts, back_tag, frame_tag)
    if "left" not in sk:
        mb.rect(K.face_pts("x", x0, -1, y0, y1, z0, z1), frame_tag)
    if "right" not in sk:
        mb.rect(K.face_pts("x", x1, +1, y0, y1, z0, z1), frame_tag)
    if "top" not in sk:
        mb.rect([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], frame_tag)
    if "bottom" not in sk:
        mb.rect([(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)], frame_tag)


def build_sloped_signal(mb, A, xc, half_w, z0, z1, y_wall0, y_wall1, side, tag, frame_tag="dark_steel", proud=0.04):
    """경사 전면 그래픽과 수직 후면을 가진 신호함."""
    x0, x1 = xc - half_w, xc + half_w
    yf0 = y_wall0 + side * proud
    yf1 = y_wall1 + side * proud
    yb = side * (abs(y_wall0) - 0.16)
    uv_f = A.uv(frame_tag)
    if side < 0:
        pts_out = [(x0, yf0, z0), (x1, yf0, z0), (x1, yf1, z1), (x0, yf1, z1)]
        pts_in = [(x1, yb, z0), (x0, yb, z0), (x0, yb, z1), (x1, yb, z1)]
        pts_l = [(x0, yb, z0), (x0, yf0, z0), (x0, yf1, z1), (x0, yb, z1)]
        pts_r = [(x1, yf0, z0), (x1, yb, z0), (x1, yb, z1), (x1, yf1, z1)]
        pts_t = [(x0, yf1, z1), (x1, yf1, z1), (x1, yb, z1), (x0, yb, z1)]
        pts_b = [(x1, yf0, z0), (x0, yf0, z0), (x0, yb, z0), (x1, yb, z0)]
    else:
        pts_out = [(x1, yf0, z0), (x0, yf0, z0), (x0, yf1, z1), (x1, yf1, z1)]
        pts_in = [(x0, yb, z0), (x1, yb, z0), (x1, yb, z1), (x0, yb, z1)]
        pts_l = [(x0, yf0, z0), (x0, yb, z0), (x0, yb, z1), (x0, yf1, z1)]
        pts_r = [(x1, yb, z0), (x1, yf0, z0), (x1, yf1, z1), (x1, yb, z1)]
        pts_t = [(x0, yb, z1), (x1, yb, z1), (x1, yf1, z1), (x0, yf1, z1)]
        pts_b = [(x1, yb, z0), (x0, yb, z0), (x0, yf0, z0), (x1, yf0, z0)]
    _emit_graphic_quad(mb, A, pts_out, tag, frame_tag)
    for pts in (pts_in, pts_l, pts_r, pts_t, pts_b):
        mb.quad(pts, uv_f, frame_tag)


def build_trapezoid_frustum(mb, A, bx0, bx1, by0, by1, z0, tx0, tx1, ty0, ty1, z1,
                            wall_tag, top_tag, bot_tag, segs_x=8, segs_y=3, skip=()):
    """하단 (bx0..bx1, by0..by1, z0)에서 상단 (tx0..tx1, ty0..ty1, z1)로 선형 외향 경사진 사다리꼴 6면 솔리드."""
    sk = set(skip)
    dz = z1 - z0
    dy_f = abs(ty0 - by0)
    slant_y = math.hypot(dz, dy_f)

    if "bottom" not in sk:
        mb.rect([(bx1, by0, z0), (bx0, by0, z0), (bx0, by1, z0), (bx1, by1, z0)], bot_tag)
    if "top" not in sk:
        mb.rect([(tx0, ty0, z1), (tx1, ty0, z1), (tx1, ty1, z1), (tx0, ty1, z1)], top_tag)

    # Front (-Y) & Back (+Y) 사다리꼴 분할 (세그먼트당 <= 4m로 타일 왜곡 방지)
    for i in range(segs_x):
        f0, f1 = i / segs_x, (i + 1) / segs_x
        xb0 = bx0 + (bx1 - bx0) * f0
        xb1 = bx0 + (bx1 - bx0) * f1
        xt0 = tx0 + (tx1 - tx0) * f0
        xt1 = tx0 + (tx1 - tx0) * f1
        pw = max(abs(xb1 - xb0), abs(xt1 - xt0))
        uv = _uv_seg(A, wall_tag, pw, slant_y)
        if "front" not in sk:
            mb.quad([(xb0, by0, z0), (xb1, by0, z0), (xt1, ty0, z1), (xt0, ty0, z1)], uv, wall_tag)
        if "back" not in sk:
            mb.quad([(xb1, by1, z0), (xb0, by1, z0), (xt0, ty1, z1), (xt1, ty1, z1)], uv, wall_tag)

    # Left (-X) & Right (+X)
    slant_x = math.hypot(dz, abs(tx0 - bx0))
    for j in range(segs_y):
        g0, g1 = j / segs_y, (j + 1) / segs_y
        yb0 = by0 + (by1 - by0) * g0
        yb1 = by0 + (by1 - by0) * g1
        yt0 = ty0 + (ty1 - ty0) * g0
        yt1 = ty0 + (ty1 - ty0) * g1
        pw = max(abs(yb1 - yb0), abs(yt1 - yt0))
        uv = _uv_seg(A, wall_tag, pw, slant_x)
        if "left" not in sk:
            mb.quad([(bx0, yb1, z0), (bx0, yb0, z0), (tx0, yt0, z1), (tx0, yt1, z1)], uv, wall_tag)
        if "right" not in sk:
            mb.quad([(bx1, yb0, z0), (bx1, yb1, z0), (tx1, yt1, z1), (tx1, yt0, z1)], uv, wall_tag)


def arch_profile_circular(x0, x1, z_edge, z_crown, n_seg, half_mode=None):
    """원호 단면 곡선 [(x_i, z_i), ...] 반환. half_mode='north'|'south'면 외곽 반아치."""
    pts = []
    if half_mode in ("north", "south"):
        w = x1 - x0
        h = z_crown - z_edge
        for i in range(n_seg + 1):
            t = i / n_seg
            x = x0 + w * t
            angle = t * math.pi * 0.5
            z = z_edge + h * (math.sin(angle) if half_mode == "north" else math.cos(angle))
            pts.append((x, z))
        return pts

    w = x1 - x0
    h = z_crown - z_edge
    xm = 0.5 * (x0 + x1)
    r = (w * w / 8.0 + h * h / 2.0) / max(h, 1e-4)
    zc = z_edge + h - r
    for i in range(n_seg + 1):
        t = i / n_seg
        x = x0 + w * t
        dx = x - xm
        z = zc + math.sqrt(max(0.0, r * r - dx * dx))
        pts.append((x, z))
    return pts


def build_closed_arch_vault(mb, A, x0, x1, y0, y1, z_edge, z_crown, thick, n_seg,
                            tag, edge_tag=None, half_mode=None, skip_bottom=False):
    """완전 폐합 이중외피(thick) 아치 지붕 쉘 + CCW 외향 법선 + 평면 사각형."""
    edge_tag = edge_tag or tag
    prof = arch_profile_circular(x0, x1, z_edge, z_crown, n_seg, half_mode=half_mode)
    bot = [(x, z - 0.5 * thick) for (x, z) in prof]
    top = [(x, z + 0.5 * thick) for (x, z) in prof]

    # Y방향 타일 쪼개기 (스테이지 0/1에서만 적절히 분할, LOD2는 1단)
    tw_m, th_m = A.tile_size(tag) if (A is not None and A.is_tiled(tag)) else (y1 - y0, 4.0)
    y_len = y1 - y0
    ny = max(1, math.ceil(y_len / tw_m - 1e-6)) if mb.split_tiles else 1

    for j in range(ny):
        ya = y0 + (y_len * j) / ny
        yb = y0 + (y_len * (j + 1)) / ny
        for i in range(n_seg):
            xa0, zt0 = top[i]
            xa1, zt1 = top[i + 1]
            _, zb0 = bot[i]
            _, zb1 = bot[i + 1]
            seg_len = math.hypot(xa1 - xa0, zt1 - zt0)
            uv_top = _uv_seg(A, tag, yb - ya, seg_len)
            # Top (+Z)
            mb.quad([(xa0, ya, zt0), (xa1, ya, zt1), (xa1, yb, zt1), (xa0, yb, zt0)], uv_top, tag)
            # Bottom (-Z)
            if not skip_bottom:
                mb.quad([(xa1, ya, zb1), (xa0, ya, zb0), (xa0, yb, zb0), (xa1, yb, zb1)], uv_top, tag)

    # Front (-Y at y0) & Back (+Y at y1) 마구리 면
    for i in range(n_seg):
        xa0, zt0 = top[i]
        xa1, zt1 = top[i + 1]
        _, zb0 = bot[i]
        _, zb1 = bot[i + 1]
        uv_end = _uv_seg(A, edge_tag, math.hypot(xa1 - xa0, zt1 - zt0), thick)
        mb.quad([(xa0, y0, zb0), (xa1, y0, zb1), (xa1, y0, zt1), (xa0, y0, zt0)], uv_end, edge_tag)
        mb.quad([(xa1, y1, zb1), (xa0, y1, zb0), (xa0, y1, zt0), (xa1, y1, zt1)], uv_end, edge_tag)

    # Left (-X) & Right (+X) 측면 마구리
    uv_side = _uv_seg(A, edge_tag, y_len, thick)
    mb.quad([(bot[0][0], y1, bot[0][1]), (bot[0][0], y0, bot[0][1]),
             (top[0][0], y0, top[0][1]), (top[0][0], y1, top[0][1])], uv_side, edge_tag)
    mb.quad([(bot[-1][0], y0, bot[-1][1]), (bot[-1][0], y1, bot[-1][1]),
             (top[-1][0], y1, top[-1][1]), (top[-1][0], y0, top[-1][1])], uv_side, edge_tag)


def build_arch_rib(mb, A, x0, x1, yc, y_width, z_edge, z_crown, drop_top, depth_h, n_seg, tag, half_mode=None):
    """아치 하부 백색 곡선 강관 트러스 리브 (폐합 사각 단면 밴드)."""
    prof = arch_profile_circular(x0, x1, z_edge, z_crown, n_seg, half_mode=half_mode)
    top = [(x, z - drop_top) for (x, z) in prof]
    bot = [(x, z - drop_top - depth_h) for (x, z) in prof]
    y0, y1 = yc - 0.5 * y_width, yc + 0.5 * y_width
    uv_s = A.uv(tag)
    for i in range(n_seg):
        xa0, zt0 = top[i]
        xa1, zt1 = top[i + 1]
        _, zb0 = bot[i]
        _, zb1 = bot[i + 1]
        mb.quad([(xa0, y0, zt0), (xa1, y0, zt1), (xa1, y1, zt1), (xa0, y1, zt0)], uv_s, tag)
        mb.quad([(xa1, y0, zb1), (xa0, y0, zb0), (xa0, y1, zb0), (xa1, y1, zb1)], uv_s, tag)
        mb.quad([(xa0, y0, zb0), (xa1, y0, zb1), (xa1, y0, zt1), (xa0, y0, zt0)], uv_s, tag)
        mb.quad([(xa1, y1, zb1), (xa0, y1, zb0), (xa0, y1, zt0), (xa1, y1, zt1)], uv_s, tag)
    mb.quad([(bot[0][0], y1, bot[0][1]), (bot[0][0], y0, bot[0][1]),
             (top[0][0], y0, top[0][1]), (top[0][0], y1, top[0][1])], uv_s, tag)
    mb.quad([(bot[-1][0], y0, bot[-1][1]), (bot[-1][0], y1, bot[-1][1]),
             (top[-1][0], y1, top[-1][1]), (top[-1][0], y0, top[-1][1])], uv_s, tag)


def build_diagonal_strut(mb, A, x0, y0, z0, x1, y1, z1, r, tag):
    """두 3D 점을 잇는 백색/철재 사각 단면 브레이싱 스트럿 (닫힌 육면체 프리즘)."""
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    L = math.sqrt(dx * dx + dy * dy + dz * dz)
    if L < 1e-4:
        return
    tx, ty, tz = dx / L, dy / L, dz / L
    # 직교 기저 2축 생성
    ref = (0.0, 0.0, 1.0) if abs(tz) < 0.9 else (1.0, 0.0, 0.0)
    ux = ty * ref[2] - tz * ref[1]
    uy = tz * ref[0] - tx * ref[2]
    uz = tx * ref[1] - ty * ref[0]
    ul = math.sqrt(ux * ux + uy * uy + uz * uz)
    ux, uy, uz = ux / ul * r, uy / ul * r, uz / ul * r
    vx = (ty * uz - tz * uy) / 1.0
    vy = (tz * ux - tx * uz) / 1.0
    vz = (tx * uy - ty * ux) / 1.0

    def pt(base, sx, sy):
        return (base[0] + sx * ux + sy * vx,
                base[1] + sx * uy + sy * vy,
                base[2] + sx * uz + sy * vz)

    c0 = [pt((x0, y0, z0), sx, sy) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    c1 = [pt((x1, y1, z1), sx, sy) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    uv = A.uv(tag)
    for k in range(4):
        nk = (k + 1) % 4
        # c0[k] -> c0[nk] -> c1[nk] -> c1[k] 방향이 외향인지 법선 검증
        e1 = (c0[nk][0] - c0[k][0], c0[nk][1] - c0[k][1], c0[nk][2] - c0[k][2])
        e2 = (c1[k][0] - c0[k][0], c1[k][1] - c0[k][1], c1[k][2] - c0[k][2])
        cx = e1[1] * e2[2] - e1[2] * e2[1]
        cy = e1[2] * e2[0] - e1[0] * e2[2]
        cz = e1[0] * e2[1] - e1[1] * e2[0]
        mid_out = (0.5 * (c0[k][0] + c0[nk][0]) - x0,
                   0.5 * (c0[k][1] + c0[nk][1]) - y0,
                   0.5 * (c0[k][2] + c0[nk][2]) - z0)
        if cx * mid_out[0] + cy * mid_out[1] + cz * mid_out[2] >= 0:
            mb.quad([c0[k], c0[nk], c1[nk], c1[k]], uv, tag)
        else:
            mb.quad([c0[nk], c0[k], c1[k], c1[nk]], uv, tag)
    # 양 끝단 마구리
    mb.quad([c0[3], c0[2], c0[1], c0[0]], uv, tag)
    mb.quad([c1[0], c1[1], c1[2], c1[3]], uv, tag)


def build_portal_arch(mb, A, pts_xz, y_c, half_y, half_r, tag, skip_bottom=False):
    """모따기/곡선 갠트리 포털 프레임을 정확한 마이터 단면과 외향 법선으로 폐합 생성."""
    n_pts = len(pts_xz)
    if n_pts < 2:
        return
    segs = []
    for i in range(n_pts - 1):
        dx = pts_xz[i + 1][0] - pts_xz[i][0]
        dz = pts_xz[i + 1][1] - pts_xz[i][1]
        L = math.hypot(dx, dz)
        tx, tz = dx / max(L, 1e-6), dz / max(L, 1e-6)
        segs.append((tz, -tx))  # 시계방향 경로 기준 내향 법선

    p_in, p_out = [], []
    for i, (px, pz) in enumerate(pts_xz):
        if i == 0:
            nx, nz = segs[0]
            mx, mz = nx * half_r, nz * half_r
        elif i == n_pts - 1:
            nx, nz = segs[-1]
            mx, mz = nx * half_r, nz * half_r
        else:
            n0, n1 = segs[i - 1], segs[i]
            sx, sz = n0[0] + n1[0], n0[1] + n1[1]
            denom = max(0.25, 1.0 + n0[0] * n1[0] + n0[1] * n1[1])
            scale = half_r / denom
            mx, mz = sx * scale, sz * scale
        p_in.append((px + mx, pz + mz))
        p_out.append((px - mx, pz - mz))

    y0, y1 = y_c - half_y, y_c + half_y
    uv = A.uv(tag)
    for i in range(n_pts - 1):
        ix0, iz0 = p_in[i]
        ix1, iz1 = p_in[i + 1]
        ox0, oz0 = p_out[i]
        ox1, oz1 = p_out[i + 1]
        mb.quad([(ix0, y0, iz0), (ix1, y0, iz1), (ox1, y0, oz1), (ox0, y0, oz0)], uv, tag)  # Front (-Y)
        mb.quad([(ix1, y1, iz1), (ix0, y1, iz0), (ox0, y1, oz0), (ox1, y1, oz1)], uv, tag)  # Back (+Y)
        mb.quad([(ox0, y0, oz0), (ox1, y0, oz1), (ox1, y1, oz1), (ox0, y1, oz0)], uv, tag)  # Outer
        mb.quad([(ix1, y0, iz1), (ix0, y0, iz0), (ix0, y1, iz0), (ix1, y1, iz1)], uv, tag)  # Inner
    if not skip_bottom:
        ix0, iz0 = p_in[0]
        ox0, oz0 = p_out[0]
        mb.quad([(ix0, y0, iz0), (ox0, y0, oz0), (ox0, y1, oz0), (ix0, y1, iz0)], uv, tag)
        ixe, ize = p_in[-1]
        oxe, oze = p_out[-1]
        mb.quad([(oxe, y0, oze), (ixe, y0, ize), (ixe, y1, ize), (oxe, y1, oze)], uv, tag)


def build_octagonal_prism(mb, A, cx, cy, z0, z1, r, tag, cap_tag=None, skip_bottom=True):
    """폐합 팔각 기둥 솔리드 (원형 강관·충격흡수 드럼 근사용, CCW 외향 법선)."""
    cap_tag = cap_tag or tag
    pts0, pts1 = [], []
    for k in range(8):
        ang = 2.0 * math.pi * (k + 0.5) / 8.0
        px = cx + r * math.cos(ang)
        py = cy + r * math.sin(ang)
        pts0.append((px, py, z0))
        pts1.append((px, py, z1))
    seg_w = 2.0 * r * math.sin(math.pi / 8.0)
    uv_side = _uv_seg(A, tag, seg_w, z1 - z0)
    for k in range(8):
        nk = (k + 1) % 8
        mb.quad([pts0[k], pts0[nk], pts1[nk], pts1[k]], uv_side, tag)
    uv_cap = A.uv(cap_tag)
    # 상단/하단 팔각 캡을 3개의 비퇴화 사각형으로 분할
    mb.quad([pts1[0], pts1[1], pts1[2], pts1[3]], uv_cap, cap_tag)
    mb.quad([pts1[4], pts1[5], pts1[6], pts1[7]], uv_cap, cap_tag)
    mb.quad([pts1[7], pts1[0], pts1[3], pts1[4]], uv_cap, cap_tag)
    if not skip_bottom:
        mb.quad([pts0[3], pts0[2], pts0[1], pts0[0]], uv_cap, cap_tag)
        mb.quad([pts0[7], pts0[6], pts0[5], pts0[4]], uv_cap, cap_tag)
        mb.quad([pts0[4], pts0[3], pts0[0], pts0[7]], uv_cap, cap_tag)


def build_octagonal_prism_y(mb, A, cx, y0, y1, cz, r, tag, cap_front=True, cap_back=True):
    """Y축 방향 폐합 팔각 기둥 솔리드 (소형 실외기 팬 슈라우드 등)."""
    pts0, pts1 = [], []
    for k in range(8):
        ang = 2.0 * math.pi * (k + 0.5) / 8.0
        pts0.append((cx + r * math.cos(ang), y0, cz + r * math.sin(ang)))
        pts1.append((cx + r * math.cos(ang), y1, cz + r * math.sin(ang)))
    uv_s = A.uv(tag)
    for k in range(8):
        nk = (k + 1) % 8
        mb.quad([pts0[nk], pts0[k], pts1[k], pts1[nk]], uv_s, tag)
    if cap_front:
        mb.quad([pts0[0], pts0[1], pts0[2], pts0[3]], uv_s, tag)
        mb.quad([pts0[4], pts0[5], pts0[6], pts0[7]], uv_s, tag)
        mb.quad([pts0[7], pts0[0], pts0[3], pts0[4]], uv_s, tag)
    if cap_back:
        mb.quad([pts1[3], pts1[2], pts1[1], pts1[0]], uv_s, tag)
        mb.quad([pts1[7], pts1[6], pts1[5], pts1[4]], uv_s, tag)
        mb.quad([pts1[4], pts1[3], pts1[0], pts1[7]], uv_s, tag)


def build_island(mb, A, x0, x1, y0, y1, nose_len, stage):
    """하단 로얄블루 연석(0..0.16) + 상단 콘크리트 방호벽(0.16..0.56) + 테이퍼 불노즈."""
    w = x1 - x0
    xm = 0.5 * (x0 + x1)
    z_top = 0.56
    if stage == 2:
        mb.box(x0, x1, y0, y1, 0.0, z_top,
               dict(default="concrete", front="blue_curb", back="blue_curb", left="blue_curb", right="blue_curb"),
               skip=("bottom",))
        return

    body_y0 = y0 + nose_len
    body_y1 = y1 - nose_len
    # 중앙 본체: 하단 블루(0.0..0.16), 상단 콘크리트(0.16..0.56)
    mb.box(x0, x1, body_y0, body_y1, 0.0, 0.16, "blue_curb", skip=("bottom", "top"))
    mb.box(x0, x1, body_y0, body_y1, 0.16, z_top, "concrete", skip=("bottom",))

    # 양단 테이퍼 불노즈 사다리꼴 (front/back 접촉면 생략으로 동일평면 중복 제거)
    nw_half = max(0.28, w * 0.28)
    for end_y0, end_y1, w_y0_half, w_y1_half, skip_inner in (
        (y0, body_y0, nw_half, 0.5 * w, "back"),
        (body_y1, y1, 0.5 * w, nw_half, "front"),
    ):
        ax0, ax1 = xm - w_y0_half, xm + w_y0_half
        bx0, bx1 = xm - w_y1_half, xm + w_y1_half
        nose_len_local = end_y1 - end_y0
        for z_a, z_b, reg, sk_tb in (
            (0.0, 0.16, "blue_curb", ("bottom", "top", skip_inner)),
            (0.16, z_top, "concrete", ("bottom", skip_inner)),
        ):
            sk = set(sk_tb)
            if "front" not in sk:
                mb.rect(K.face_pts("y", end_y0, -1, ax0, ax1, z_a, z_b), reg)
            if "back" not in sk:
                mb.rect(K.face_pts("y", end_y1, +1, bx0, bx1, z_a, z_b), reg)
            dx_s = bx0 - ax0
            uv_s = _uv_seg(A, reg, math.hypot(nose_len_local, dx_s), z_b - z_a)
            mb.quad([(bx0, end_y1, z_a), (ax0, end_y0, z_a), (ax0, end_y0, z_b), (bx0, end_y1, z_b)], uv_s, reg)
            mb.quad([(ax1, end_y0, z_a), (bx1, end_y1, z_a), (bx1, end_y1, z_b), (ax1, end_y0, z_b)], uv_s, reg)
            if "top" not in sk:
                uv_t = _uv_seg(A, reg, max(w_y0_half, w_y1_half) * 2.0, nose_len_local)
                mb.quad([(ax0, end_y0, z_b), (ax1, end_y0, z_b), (bx1, end_y1, z_b), (bx0, end_y1, z_b)], uv_t, reg)


# ---------------------------------------------------------------------------
# 통합 다단계 에셋 생성기 (stage 0=Main, 1=LOD1, 2=LOD2)
# ---------------------------------------------------------------------------

def build_stage(A, stage):
    mb = K.MeshBuilder(A, split_tiles=(stage < 2))
    wins = K.WindowSet() if stage == 0 else None
    z_isl = 0.56

    # 1. 아일랜드 1~6 + 북/남 연석 0,7 (X ∈ [-20.30, +20.30], Y ∈ [-14.20, +14.20])
    islands = [
        # (name, x0, x1, y0, y1, nose_len)
        ("curb_n", -20.30, -19.30, -11.40, 14.00, 0.55),
        ("isl_1", -15.50, -13.50, -11.00, 13.80, 0.60),
        ("isl_2", -10.00, -7.20, -10.80, 13.00, 0.60),
        ("isl_3", -3.80, -1.60, -10.80, 13.80, 0.60),
        ("isl_4", 1.80, 4.00, -10.20, 9.20, 0.65),
        ("isl_5", 7.70, 9.90, -14.20, 14.20, 0.50),
        ("isl_6", 13.40, 15.40, -14.20, 14.20, 0.50),
        ("curb_s", 18.90, 20.30, -14.20, 14.20, 0.50),
    ]
    for _name, x0, x1, y0, y1, nl in islands:
        build_island(mb, A, x0, x1, y0, y1, nl, stage)

    # 2. 중앙 스카이블루 본체 캐노피 데크 (x ∈ [-15.30, +15.80], y ∈ [-5.70, +5.70], z = 5.18..6.62)
    bx0, bx1, by0, by1 = -15.30, 15.80, -5.70, 5.70
    tx0, tx1, ty0, ty1 = -15.58, 16.08, -6.08, 6.08
    z_dec_bot, z_dec_top = 5.18, 6.62

    if stage == 2:
        build_trapezoid_frustum(
            mb, A, bx0, bx1, by0, by1, z_dec_bot, tx0, tx1, ty0, ty1, z_dec_top,
            wall_tag="blue_fascia", top_tag="teal_roof", bot_tag="soffit", segs_x=1, segs_y=1,
        )
    else:
        # 슬림 백색 코핑(0.18 m 폭 × 0.10 m 높이)과 동일평면 방지를 위해 상면은 코핑 안쪽만 생성
        build_trapezoid_frustum(
            mb, A, bx0, bx1, by0, by1, z_dec_bot, tx0, tx1, ty0, ty1, z_dec_top,
            wall_tag="blue_fascia", top_tag="teal_roof", bot_tag="soffit",
            segs_x=(6 if stage == 0 else 4), segs_y=(4 if stage == 0 else 2),
            skip=("top",),
        )
        cx0, cx1, cy0, cy1 = tx0 + 0.18, tx1 - 0.18, ty0 + 0.18, ty1 - 0.18
        mb.rect([(cx0, cy0, z_dec_top), (cx1, cy0, z_dec_top), (cx1, cy1, z_dec_top), (cx0, cy1, z_dec_top)], "teal_roof")
        z_cop = 6.72
        mb.box(tx0, tx1, ty0, cy0, z_dec_top, z_cop, "trim_white")
        mb.box(tx0, tx1, cy1, ty1, z_dec_top, z_cop, "trim_white")
        mb.box(tx0, cx0, cy0, cy1, z_dec_top, z_cop, "trim_white", skip=("front", "back"))
        mb.box(cx1, tx1, cy0, cy1, z_dec_top, z_cop, "trim_white", skip=("front", "back"))

    # 3. 옥상 양면 대형 간판 (실측 비율 5.25x1.78m = 2.95:1, 다리 0.74m 가시 높이, 좌: 신탄진 / 우: Sintanjin) + 풍향 마스트 3본
    if stage == 2:
        build_graphic_box(mb, A, -5.30, -0.05, -0.26, 0.26, z_dec_top, 9.14, "dark_steel",
                          front_tag="sign_sjt_kr", back_tag="sign_sjt_en", skip=("bottom",))
        build_graphic_box(mb, A, 0.55, 5.80, -0.26, 0.26, z_dec_top, 9.14, "dark_steel",
                          front_tag="sign_sjt_en", back_tag="sign_sjt_kr", skip=("bottom",))
    else:
        for px in (-4.55, -0.80, 1.30, 5.05):
            mb.box(px - 0.14, px + 0.14, -0.17, 0.17, z_dec_top, 7.36, "trim_white", skip=("bottom", "top"))
        build_graphic_box(mb, A, -5.30, -0.05, -0.26, 0.26, 7.36, 9.14, "dark_steel",
                          front_tag="sign_sjt_kr", back_tag="sign_sjt_en")
        build_graphic_box(mb, A, 0.55, 5.80, -0.26, 0.26, 7.36, 9.14, "dark_steel",
                          front_tag="sign_sjt_en", back_tag="sign_sjt_kr")
        if stage == 0:
            # 3본 상부 안테나/피뢰 마스트 + 3색 풍향계 프로펠러 (좌: 파랑, 중: 노랑, 우측 지붕: 다크)
            mast_specs = [
                (-5.22, "terminal_blue", 9.14, 10.10),
                (0.25,  "safety_yellow", z_dec_top, 10.02),
                (8.20,  "dark_steel",    z_dec_top, 9.85),
            ]
            mb.box(-4.22, -4.18, -0.02, 0.02, 9.14, 10.38, "trim_white", skip=("bottom",))
            for mx, vane_tag, z_base_m, z_top_m in mast_specs:
                mb.box(mx - 0.035, mx + 0.035, -0.035, 0.035, z_base_m, z_top_m, "trim_white", skip=("bottom",))
                zv = z_top_m - 0.36
                mb.box(mx - 0.24, mx + 0.24, -0.025, 0.025, zv - 0.025, zv + 0.025, "dark_steel")
                mb.box(mx - 0.025, mx + 0.025, -0.24, 0.24, zv + 0.03, zv + 0.08, "dark_steel")
                for vx0, vx1 in ((mx - 0.30, mx - 0.20), (mx + 0.20, mx + 0.30)):
                    mb.box(vx0, vx1, -0.05, 0.05, zv - 0.06, zv + 0.06, vane_tag)
                for vy0, vy1 in ((-0.30, -0.20), (0.20, 0.30)):
                    mb.box(mx - 0.05, mx + 0.05, vy0, vy1, zv, zv + 0.11, vane_tag)

    # 4. 비대칭 폴리카보네이트 아치 지붕 (실측: Wing 0 서측 상향 갈매기 날개 + 1/7차선 하부 원통 볼트 + 남측 6차선 W3/E3 상향 캔틸레버)
    n_arch = 16 if stage == 0 else (5 if stage == 1 else 2)
    arch_thick = 0.06
    w1 = (-14.32, -2.88, -10.30, -5.72, 4.94, 5.56, None)  # 서측 2+3차선
    w2 = (-2.52, 8.62, -10.30, -5.72, 4.94, 5.56, None)    # 서측 4+5차선
    if stage == 2:
        arch_specs = [
            (-19.80, -15.48, -10.30, 8.58, 4.36, 4.86, None),        # Wing 0 통합 간소화
            (15.40, 19.70, -10.20, 5.70, 4.34, 4.78, None),          # Wing S (7차선 하부)
            w1,
            w2,
            (8.98, 15.80, -10.30, -5.72, 4.94, 5.44, "north"),       # W3 (6차선 상향 캔틸레버)
            (-8.44, -2.88, 5.72, 8.60, 4.94, 5.40, None),            # E1 (3차선 단독)
            (-2.52, 8.62, 5.72, 14.20, 4.94, 5.56, None),            # E2 (4+5차선)
            (8.98, 15.80, 5.72, 14.20, 4.94, 5.44, "north"),         # E3 (6차선 상향 캔틸레버, 7차선 개방)
        ]
    else:
        arch_specs = [
            (-19.80, -14.64, -10.30, -5.72, 4.94, 5.46, "south"),    # Wing 0 West: 1차선 서측 외향 상향 날개
            (-19.80, -15.48, -6.50, 8.58, 4.28, 4.68, None),         # Wing 0 Main/East: 1차선 하부 원통 캐노피
            (15.40, 19.70, -10.20, 5.70, 4.34, 4.78, None),          # Wing S: 남측 7차선 하부 원통 캐노피 (동측 개방)
            w1,
            w2,
            (8.98, 15.80, -10.30, -5.72, 4.94, 5.44, "north"),       # W3: 서측 6차선 상향 캔틸레버 날개
            (-8.44, -2.88, 5.72, 8.60, 4.94, 5.40, None),            # E1: 동측 3차선 단독 단축 (2차선 개방)
            (-2.52, 8.62, 5.72, 14.20, 4.94, 5.56, None),            # E2: 동측 4+5차선 장대
            (8.98, 15.80, 5.72, 14.20, 4.94, 5.44, "north"),         # E3: 동측 6차선 상향 캔틸레버 날개
        ]
    for ax0, ax1, ay0, ay1, ze, zc, hm in arch_specs:
        build_closed_arch_vault(
            mb, A, ax0, ax1, ay0, ay1, ze, zc, arch_thick, n_arch,
            tag="polycarb", edge_tag="trim_white", half_mode=hm,
        )

    # 5. 아치 골짜기 백색 배수거터 빔 + 곡선 강관 트러스 리브
    if stage < 2:
        gutters = [
            (-19.96, -19.82, -10.28, -5.74, 5.38, 5.54),  # Wing 0 West 상향 끝단 빔
            (-19.96, -19.82, -6.48, 8.56, 4.20, 4.38),    # Wing 0 Main 북측 연석 거터
            (-15.46, -15.32, -6.48, 8.56, 4.20, 4.38),    # Wing 0 Main 내측 거터
            (-14.62, -14.34, -10.28, -5.74, 4.86, 5.06),  # Island 1 W1 서측 거터
            (-8.74, -8.46, 5.74, 8.58, 4.86, 5.06),       # Island 2 E1 동측 거터
            (-2.86, -2.54, -10.28, -5.74, 4.86, 5.06),    # Island 3 W1/W2 거터
            (-2.86, -2.54, 5.74, 14.18, 4.86, 5.06),      # Island 3 E1/E2 거터
            (8.64, 8.96, -10.28, -5.74, 4.86, 5.06),      # Island 5 W2/W3 거터
            (8.64, 8.96, 5.74, 14.18, 4.86, 5.06),        # Island 5 E2/E3 거터
            (15.82, 15.98, -10.28, -5.74, 5.36, 5.52),    # W3 남측 상향 끝단 빔
            (15.82, 15.98, 5.74, 14.18, 5.36, 5.52),      # E3 남측 상향 끝단 빔
            (15.24, 15.38, -10.18, 5.68, 4.26, 4.44),     # Wing S 내측 거터
            (19.72, 19.88, -10.18, 5.68, 4.26, 4.44),     # Wing S 남측 외곽 거터
        ]
        for gx0, gx1, gy0, gy1, gz0, gz1 in gutters:
            mb.box(gx0, gx1, gy0, gy1, gz0, gz1, "trim_white")

    if stage == 0:
        rib_sets = [
            (-19.80, -14.64, (-10.18, -8.10, -5.86), 4.94, 5.46, "south"),
            (-19.80, -15.48, (-6.38, -3.60, -0.80, 2.00, 4.90, 8.46), 4.28, 4.68, None),
            (15.40, 19.70, (-10.08, -7.20, -4.20, -1.20, 1.80, 5.58), 4.34, 4.78, None),
            (-14.32, -2.88, (-10.18, -8.10, -5.95), 4.94, 5.56, None),
            (-2.52, 8.62, (-10.18, -8.10, -5.95), 4.94, 5.56, None),
            (8.98, 15.80, (-10.18, -8.10, -5.86), 4.94, 5.44, "north"),
            (-8.44, -2.88, (5.95, 8.48), 4.94, 5.40, None),
            (-2.52, 8.62, (5.95, 8.70, 11.45, 14.08), 4.94, 5.56, None),
            (8.98, 15.80, (5.95, 8.70, 11.45, 14.08), 4.94, 5.44, "north"),
        ]
        for ax0, ax1, ys, ze, zc, hm in rib_sets:
            for yc in ys:
                build_arch_rib(mb, A, ax0, ax1, yc, 0.13, ze, zc, 0.04, 0.16, 12, "trim_white", half_mode=hm)

    # 6. 중앙 콘크리트 사각 교각 + 서측 캔틸레버 기둥(y=-5.70) & 동측 아치 기둥·V-브레이싱
    pier_coords = [
        (-14.50, -3.75), (-14.50, 3.75),
        (-2.70, -3.75), (-2.70, 3.75),
        (8.80, -3.75), (8.80, 3.75),
    ]
    if stage < 2:
        pier_coords.extend([(14.40, -3.75), (14.40, 3.75)])
    for px, py in pier_coords:
        mb.box(px - 0.28, px + 0.28, py - 0.36, py + 0.36, z_isl, z_dec_bot, "concrete", skip=("bottom", "top"))
        if stage == 0:
            # 상부 콘크리트 주두(코벨) & 투광등/스피커 하우징 (under_look_s 실물)
            mb.box(px - 0.36, px + 0.36, py - 0.44, py + 0.44, 4.66, z_dec_bot, "concrete", skip=("top",))
            for fx0, fx1 in ((px - 0.44, px - 0.28), (px + 0.28, px + 0.44)):
                mb.box(fx0, fx1, py - 0.14, py + 0.14, 4.46, 4.60, "dark_steel")

    # 서측(y=-5.70) 캔틸레버 지주 + 동측(y=+5.70, +8.20, +13.50) 아치 지주 + 북측 1차선/남측 7차선 하부 기둥
    steel_cols = [
        (-19.88, -5.80, 4.20), (-19.88, 1.20, 4.20), (-19.88, 8.10, 4.20),  # 북측 1차선 하부 볼트 외곽 기둥
        (-14.48, -5.70, 4.86), (-14.48, 5.70, 4.90),                        # Island 1
        (-8.60, 8.20, 4.86),                                                # Island 2 (E1 동측 지주)
        (-2.70, -5.70, 4.86), (-2.70, 5.70, 4.86), (-2.70, 13.50, 4.86),    # Island 3
        (8.80, -5.70, 4.86), (8.80, 5.70, 4.86), (8.80, 13.50, 4.86),       # Island 5
        (19.80, -5.70, 4.26), (19.80, 0.00, 4.26), (19.80, 5.45, 4.26),     # Island 7 (Wing S 하부만 지지, 동측 개방)
    ]
    if stage < 2:
        for cx, cy, zt in steel_cols:
            if stage == 0:
                # 기둥 받침과 머리의 노출된 모서리를 다듬는다.
                KX.bevel_box(mb, cx - 0.24, cx + 0.24, cy - 0.24, cy + 0.24, z_isl, z_isl + 0.14, "concrete", bevel=0.018)
                # 강재 베이스플레이트 + 4개 앵커볼트 + 팔각 기둥 + 상단 거셋 새들 + 중단 브레이싱 접합 칼라
                mb.box(cx - 0.19, cx + 0.19, cy - 0.19, cy + 0.19, z_isl + 0.14, z_isl + 0.175, "dark_steel", skip=("bottom",))
                for adx in (-0.14, 0.14):
                    for ady in (-0.14, 0.14):
                        mb.box(cx + adx - 0.018, cx + adx + 0.018, cy + ady - 0.018, cy + ady + 0.018,
                               z_isl + 0.175, z_isl + 0.21, "dark_steel", skip=("bottom",))
                build_octagonal_prism(mb, A, cx, cy, z_isl + 0.175, zt - 0.08, 0.14, "trim_white", skip_bottom=True)
                KX.bevel_box(mb, cx - 0.17, cx + 0.17, cy - 0.17, cy + 0.17, zt - 0.08, zt - 0.005, "dark_steel", bevel=0.009, bottom=True)
                build_octagonal_prism(mb, A, cx, cy, 3.00, 3.36, 0.172, "dark_steel", skip_bottom=False)
            else:
                mb.box(cx - 0.13, cx + 0.13, cy - 0.13, cy + 0.13, z_isl, zt - 0.005, "trim_white", skip=("bottom",))
        if stage == 0:
            # 서측 y=-5.70 기둥 -> 전방 캔틸레버 아치(-Y) & 본체(+Y) 사재 브레이싱 (west_close_look_ne/se 실물)
            for vx in (-14.48, -2.70, 8.80):
                build_diagonal_strut(mb, A, vx, -5.78, 3.20, vx, -8.85, 4.88, 0.070, "trim_white")
                build_diagonal_strut(mb, A, vx, -5.62, 3.20, vx, -4.15, 5.18, 0.065, "trim_white")
            # Island 1 서측 외향 북측 날개(Wing 0 West) 상향 캔틸레버 스트럿 (west_close_look_ne 실물)
            build_diagonal_strut(mb, A, -14.56, -5.78, 3.25, -18.20, -8.40, 5.30, 0.068, "trim_white")
            # Island 5 남측 외향 6차선 날개(W3, E3) 상향 캔틸레버 스트럿 (east_far_look_sw/west_close_look_se 실물)
            build_diagonal_strut(mb, A, 8.88, -5.78, 3.25, 13.20, -8.30, 5.30, 0.068, "trim_white")
            build_diagonal_strut(mb, A, 8.88, 5.78, 3.25, 13.20, 8.20, 5.30, 0.068, "trim_white")
            build_diagonal_strut(mb, A, 8.88, 13.42, 3.25, 13.60, 13.42, 5.32, 0.068, "trim_white")
            # 동측 y=+5.70 기둥 V-브레이싱 (본체 -Y & 동측 장대 아치 +Y, mid_south_look_nw 실물)
            for vx in (-2.70, 8.80):
                build_diagonal_strut(mb, A, vx, 5.62, 3.20, vx, 4.15, 5.18, 0.065, "trim_white")
                build_diagonal_strut(mb, A, vx, 5.78, 3.20, vx, 8.20, 4.88, 0.070, "trim_white")
                # 동측 끝단 y=+13.50 내측 경사 스트럿
                build_diagonal_strut(mb, A, vx, 13.42, 3.25, vx, 11.40, 4.88, 0.065, "trim_white")
            # E1 단축 아치(y=+8.20) 경사 스트럿
            build_diagonal_strut(mb, A, -8.60, 8.12, 3.30, -8.60, 6.20, 4.88, 0.065, "trim_white")
            # 북측 1차선 & 남측 7차선 하부 볼트 외곽 기둥 내측 경사 스트럿
            for cy in (-5.80, 1.20):
                build_diagonal_strut(mb, A, -19.82, cy, 3.05, -17.75, cy, 4.62, 0.060, "trim_white")
            for cy in (-5.70, 0.00, 5.45):
                build_diagonal_strut(mb, A, 19.72, cy, 3.05, 17.65, cy, 4.72, 0.062, "trim_white")
            build_diagonal_strut(mb, A, 19.72, -5.78, 3.05, 19.72, -8.50, 4.30, 0.060, "trim_white")

            # 교각·외곽 지주 팔각 드레인 파이프 (상부 집수 호퍼 + 고정 밴드 3단 + 하부 배수 슈)
            pier_drains = [(-14.50, -3.75), (-14.50, 3.75), (-2.70, -3.75), (-2.70, 3.75), (8.80, -3.75), (8.80, 3.75)]
            for dx, dy in pier_drains:
                px_d = dx + 0.36
                mb.box(px_d - 0.09, px_d + 0.09, dy - 0.09, dy + 0.09, z_isl, z_isl + 0.09, "dark_steel", skip=("bottom",))
                build_octagonal_prism(mb, A, px_d, dy, z_isl + 0.09, 4.88, 0.052, "booth_silver", skip_bottom=True)
                mb.box(px_d - 0.10, px_d + 0.10, dy - 0.10, dy + 0.10, 4.88, 5.17, "dark_steel", skip=("top",))  # 보 플랜지(±0.11)와 면 공유 방지
                for bz in (1.50, 2.75, 4.00):
                    build_octagonal_prism(mb, A, px_d, dy, bz - 0.035, bz + 0.035, 0.066, "dark_steel", skip_bottom=False)
            for dx_w, dy_w, zt_w in ((-19.88, 1.55, 4.20), (19.80, 0.35, 4.26)):
                mb.box(dx_w - 0.08, dx_w + 0.08, dy_w - 0.08, dy_w + 0.08, z_isl, z_isl + 0.08, "dark_steel", skip=("bottom",))
                build_octagonal_prism(mb, A, dx_w, dy_w, z_isl + 0.08, zt_w - 0.08, 0.048, "booth_silver", skip_bottom=True)
                mb.box(dx_w - 0.09, dx_w + 0.09, dy_w - 0.22, dy_w + 0.08, zt_w - 0.12, zt_w - 0.02, "dark_steel")  # 기둥 새들 상면과 같은 높이 방지
                for bz in (1.40, 2.75):
                    build_octagonal_prism(mb, A, dx_w, dy_w, bz - 0.03, bz + 0.03, 0.060, "dark_steel", skip_bottom=False)

    # 7. 차선별 슬림 선형 천장 LED 등기구 & 소핏 하부 종/횡 강재 보 & 1차선 1신호 원칙 매립/아치 신호박스
    lane_centers = [-17.40, -11.75, -5.50, 0.10, 5.85, 11.65, 17.15]
    if stage == 0:
        # 본체 천장 전폭 연속 이열 LED 등기구, 모듈 분할 보·테두리 트림 (under_look_n/s 실물 비례)
        for lx in lane_centers[1:-1]:
            for sx_off in (-0.48, 0.48):
                mb.box(lx + sx_off - 0.08, lx + sx_off + 0.08, -5.15, 5.15, 5.135, z_dec_bot, "lamp_strip", skip=("top",))
            for my_p in (-2.80, 0.0, 2.80):
                mb.box(lx - 0.62, lx + 0.62, my_p - 0.14, my_p + 0.14, 5.122, z_dec_bot, "dark_steel", skip=("top",))
        for rx_b in (-14.50, -8.60, -2.70, 2.90, 8.80, 14.40):
            mb.box(rx_b - 0.06, rx_b + 0.06, -5.54, 5.54, 5.125, z_dec_bot, "booth_silver", skip=("top",))
        for ry_b in (-1.90, 1.90):
            mb.box(bx0 + 0.16, bx1 - 0.16, ry_b - 0.04, ry_b + 0.04, 5.145, z_dec_bot, "dark_steel", skip=("top",))
        for sy_trim0, sy_trim1 in ((-5.68, -5.56), (5.56, 5.68)):
            mb.box(bx0 + 0.02, bx1 - 0.02, sy_trim0, sy_trim1, 5.110, z_dec_bot, "booth_silver", skip=("top",))
        for sx_trim0, sx_trim1 in ((bx0 + 0.02, bx0 + 0.14), (bx1 - 0.14, bx1 - 0.02)):
            mb.box(sx_trim0, sx_trim1, -5.56, 5.56, 5.115, z_dec_bot, "booth_silver", skip=("top",))

        # 소핏 하부 종/횡 강재 보 구조 (교각 코벨·등기구·트림과 겹치지 않는 z=4.94..5.108 층 분리)
        for gx_b in (-14.50, -2.70, 8.80, 14.40):
            for gy0_s, gy1_s in ((-5.54, -4.22), (-3.28, 3.28), (4.22, 5.54)):
                mb.box(gx_b - 0.08, gx_b + 0.08, gy0_s, gy1_s, 4.98, 5.108, "dark_steel")
                mb.box(gx_b - 0.14, gx_b + 0.14, gy0_s, gy1_s, 4.94, 4.98, "booth_silver")
        for gx_b in (-8.60, 2.90):
            mb.box(gx_b - 0.07, gx_b + 0.07, -5.54, 5.54, 4.99, 5.108, "dark_steel")
            mb.box(gx_b - 0.12, gx_b + 0.12, -5.54, 5.54, 4.95, 4.99, "booth_silver")
        # 종방향(X) I형 강재 보 (y = ±3.75 코벨 사이 경간 + 중앙 y = 0.0)
        for ly_b in (-3.75, 3.75):
            for lx0_s, lx1_s in ((-14.12, -3.08), (-2.32, 8.42), (9.18, 14.02)):
                mb.box(lx0_s, lx1_s, ly_b - 0.06, ly_b + 0.06, 5.01, 5.105, "dark_steel")
                mb.box(lx0_s, lx1_s, ly_b - 0.11, ly_b + 0.11, 4.97, 5.01, "booth_silver")
        for lx0_s, lx1_s in ((-15.10, -14.60), (-14.40, -8.70), (-8.50, -2.80), (-2.60, 2.80), (3.00, 8.70), (8.90, 14.30), (14.50, 15.62)):
            mb.box(lx0_s, lx1_s, -0.05, 0.05, 5.02, 5.105, "dark_steel")
        # 아치 하부 종방향 선형 등기구 바
        arch_lamp_specs = [
            (-17.64, (-4.8, -1.5, 2.0, 5.5), 4.63),
            (lane_centers[1], (-8.0,), 5.20),
            (lane_centers[2], (-8.0, 7.1), 5.20),
            (lane_centers[3], (-8.0, 7.6, 12.1), 5.22),
            (lane_centers[4], (-8.0, 7.6, 12.1), 5.22),
            (lane_centers[5], (-8.0, 7.6, 12.1), 5.16),
            (17.55, (-8.0, -2.5, 2.5), 4.72),
        ]
        for lx, lys, lz in arch_lamp_specs:
            for ly in lys:
                mb.box(lx - 0.09, lx + 0.09, ly - 1.15, ly + 1.15, lz - 0.04, lz, "lamp_strip")

    if stage < 2:
        # 서측 사진의 전면 테두리 이음부 기준 X 추정값 (3차선 / 4차선).
        for cx, arch, tag in ((-5.20, w1, "sig_red_x"), (0.50, w2, "sig_green_down")):
            ax0, ax1, front_y, _, ze, zc, _ = arch
            xs, zs = zip(*arch_profile_circular(ax0, ax1, ze, zc, n_arch))
            x0, x1 = cx - 0.27, cx + 0.27
            # 양쪽 모서리가 닿도록 실제 분할된 쉘의 낮은 상면에서 5 mm 내린다.
            base = min(np.interp((x0, x1), xs, zs)) + arch_thick / 2 - 0.005
            build_graphic_box(mb, A, x0, x1, front_y - 0.01, front_y + 0.23,
                              base, base + 0.52, "dark_steel", front_tag=tag)

        # 동측(+Y): E1 3차선 단축아치 전면 Red X (east_near_look_w 실측) + Lane 2/4/5 파시아 소형 CCTV/센서 하우징
        build_graphic_box(mb, A, lane_centers[2] - 0.28, lane_centers[2] + 0.28, 8.46, 8.68, 5.20, 5.76, "dark_steel",
                          back_tag="sig_red_x")
        if stage == 0:
            y_slope0 = 5.70 + 0.38 * (5.44 - z_dec_bot) / (z_dec_top - z_dec_bot)
            y_slope1 = 5.70 + 0.38 * (5.96 - z_dec_bot) / (z_dec_top - z_dec_bot)
            for cx in (-12.50, -11.00, lane_centers[3], lane_centers[4]):
                build_sloped_signal(mb, A, cx, 0.18, 5.76, 6.10, y_slope0, y_slope1, +1, None)

    # 8. 오렌지-실버 요금소 부스 4동 (Islands 1..4) + 슬림 백색 지붕 캡 + WindowSet 유리
    booth_xs = [-14.50, -8.60, -2.70, 2.90]
    for b_idx, bx in enumerate(booth_xs):
        w2 = 0.72
        by0_b, by1_b = -1.70, 1.70
        if stage == 2:
            mb.box(bx - w2, bx + w2, by0_b, by1_b, z_isl, 3.08,
                   dict(default="booth_silver", bottom="booth_orange", top="trim_white"), skip=("bottom",))
        else:
            mb.box(bx - w2, bx + w2, by0_b, by1_b, z_isl, 1.28, "booth_orange", skip=("bottom", "top"))
            mb.box(bx - w2, bx + w2, by0_b, by1_b, 1.28, 2.58, "booth_silver", skip=("bottom", "top"))
            mb.box(bx - w2 - 0.05, bx + w2 + 0.05, by0_b - 0.05, by1_b + 0.05, 2.58, 3.00, "booth_orange", skip=("top",))
            mb.box(bx - w2 - 0.06, bx + w2 + 0.06, by0_b - 0.06, by1_b + 0.06, 3.00, 3.10, "trim_white", skip=("bottom",))
            if stage == 0:
                # 4모서리 다크 알루미늄 코너 프레임, 하단 고무 킥플레이트/벨트라인 & 창호 3D 프레임
                mb.box(bx - w2 - 0.018, bx + w2 + 0.018, by0_b - 0.018, by1_b + 0.018, z_isl, z_isl + 0.10, "dark_steel", skip=("bottom",))
                mb.box(bx - w2 - 0.016, bx + w2 + 0.016, by0_b - 0.016, by1_b + 0.016, 1.24, 1.28, "dark_steel")
                for cx_s in (bx - w2 - 0.01, bx + w2 - 0.03):
                    for cy_s in (by0_b - 0.01, by1_b - 0.03):
                        mb.box(cx_s, cx_s + 0.04, cy_s, cy_s + 0.04, 1.28, 2.58, "dark_steel", skip=("bottom", "top"))
                for sx_off in (-(w2 + 0.05), w2 + 0.01):
                    mb.box(bx + sx_off, bx + sx_off + 0.04, -1.10, 1.10, 2.54, 2.58, "lamp_strip", skip=("top",))

                # 창호 하부 스테인리스 거래 선반/카운터 + 요금 수납 인터컴 박스 (창틀 z=1.445 하부)
                for side_s, sx_wall in ((-1, bx - w2), (1, bx + w2)):
                    K.axbox(mb, "x", sx_wall, side_s, -1.18, 1.18, 0.0, 0.20, 1.37, 1.43, "booth_silver")
                    for bky in (-0.95, 0.0, 0.95):
                        K.axbox(mb, "x", sx_wall, side_s, bky - 0.03, bky + 0.03, 0.0, 0.16, 1.29, 1.37, "dark_steel")
                    K.axbox(mb, "x", sx_wall, side_s, 0.18, 0.56, 0.0, 0.06, 0.94, 1.22, "dark_steel")
                    K.axbox(mb, "x", sx_wall, side_s, 0.23, 0.51, 0.06, 0.08, 0.99, 1.17, "booth_silver")

                # 부스 전면(-Y) 하단 외벽 소형 실외기 + L브라켓 + 팬 슈라우드 + 냉매 배관 덕트
                ac_x0, ac_x1 = bx - 0.42, bx + 0.22
                for ac_bx in (ac_x0 + 0.08, ac_x1 - 0.08):
                    mb.box(ac_bx - 0.025, ac_bx + 0.025, by0_b - 0.22, by0_b, 0.72, 0.77, "dark_steel", skip=("back",))
                mb.box(ac_x0, ac_x1, by0_b - 0.24, by0_b, 0.77, 1.24,
                       dict(default="booth_silver", top="trim_white"), skip=("back",))
                build_octagonal_prism_y(mb, A, bx - 0.18, by0_b - 0.27, by0_b - 0.24, 1.01, 0.17, "dark_steel",
                                        cap_front=True, cap_back=False)
                build_octagonal_prism_y(mb, A, bx - 0.18, by0_b - 0.285, by0_b - 0.27, 1.01, 0.05, "trim_white",
                                        cap_front=True, cap_back=False)
                mb.box(ac_x1 + 0.04, ac_x1 + 0.10, by0_b - 0.06, by0_b, 0.92, 2.56, "dark_steel", skip=("back",))

                # 부스 지붕 상부 환기팬 유닛 + 통신 정션박스 + 지붕 파라펫 트림 림
                mb.box(bx - 0.30, bx + 0.30, -0.88, -0.28, 3.10, 3.20, "dark_steel", skip=("bottom",))
                mb.box(bx - 0.24, bx + 0.24, -0.82, -0.34, 3.20, 3.34, "booth_silver", skip=("bottom",))
                KX.bevel_box(mb, bx - 0.34, bx + 0.34, -0.92, -0.24, 3.34, 3.41, "trim_white", bevel=0.012, bottom=True)
                mb.box(bx - 0.22, bx + 0.22, 0.42, 0.88, 3.10, 3.26, "dark_steel", skip=("bottom",))
                mb.box(bx - 0.24, bx + 0.24, 0.40, 0.90, 3.26, 3.30, "booth_silver")
                for py_lip in (by0_b - 0.06, by1_b + 0.02):
                    mb.box(bx - w2 - 0.06, bx + w2 + 0.06, py_lip, py_lip + 0.04, 3.10, 3.14, "dark_steel")

        if wins is not None:
            unit = (b_idx * 18) % 25  # WindowSet의 7배 stride를 역변환해 부스별 셀 0..3 사용.
            booth_faces = (
                ("x", bx - w2, -1, -1.42, 1.42, 1.50, ((-1.42, -0.04), (0.04, 1.42))),
                ("x", bx + w2, +1, -1.42, 1.42, 1.50, ((-1.42, -0.04), (0.04, 1.42))),
                ("y", by0_b, -1, bx - 0.50, bx + 0.50, 1.62, ((bx - 0.50, bx + 0.50),)),
                ("y", by1_b, +1, bx - 0.50, bx + 0.50, 1.50, ((bx - 0.50, bx + 0.50),)),
            )
            for axis, wall, side, a0, a1, z0, panes in booth_faces:
                z1 = 2.48
                # 창대를 벽 안으로 4 mm 물려 뒤쪽 모따기에 틈이 생기지 않게 한다.
                KX.ax_bevel(mb, axis, wall, side, a0 - 0.08, a1 + 0.08, -0.004, 0.145, z0 - 0.055, z0, "booth_silver", bevel=0.004)
                K.axbox(mb, axis, wall, side, a0 - 0.07, a1 + 0.07, 0, 0.105, z1, z1 + 0.055, "booth_silver")
                for lo, hi in ((a0 - 0.05, a0), (a1, a1 + 0.05)):
                    K.axbox(mb, axis, wall, side, lo, hi, 0, 0.085, z0, z1, "booth_silver")
                if len(panes) == 2:
                    K.axbox(mb, axis, wall, side, -0.04, 0.04, 0, 0.075, z0, z1, "booth_silver")
                for lo, hi in panes:
                    wins.add_face(axis, wall, side, lo, hi, z0, z1, floor=0, unit=unit)

    if stage == 0:
        # 무인정산기·단말기 기둥 및 적백 차단기 바 + 북측 화물차선 노란색 U자 안전가드 & W-빔 가드레일
        terminal_coords = [
            (-14.50, 2.25), (-8.60, 2.25), (-2.70, 2.25), (2.90, 2.25),
            (-14.50, -2.25), (8.80, 2.25), (14.40, 2.25),
        ]
        for tx, ty in terminal_coords:
            mb.box(tx - 0.22, tx + 0.22, ty - 0.28, ty + 0.28, z_isl, 1.68, "terminal_blue", skip=("bottom",))
            mb.box(tx - 0.16, tx + 0.16, ty - 0.20, ty + 0.20, 1.68, 1.78, "dark_steel", skip=("bottom",))
            mb.box(tx - 0.07, tx + 0.07, ty - 0.07, ty + 0.07, 1.78, 1.88, "gantry_orange", skip=("bottom",))

        barrier_specs = [
            (-15.05, -18.75, -15.48, 2.30),  # Lane 1 (화물)
            (-7.65, -7.22, -4.25, 2.30),     # Lane 3 (TCS)
            (-2.05, -1.62, 1.35, 2.30),      # Lane 4 (TCS)
            (3.55, 3.98, 7.15, 2.30),        # Lane 5 (TCS)
        ]
        for cx, ax0, ax1, by in barrier_specs:
            mb.box(cx - 0.20, cx + 0.20, by - 0.20, by + 0.20, z_isl, 1.44, "booth_orange", skip=("bottom",))
            mb.box(cx - 0.22, cx + 0.22, by - 0.22, by + 0.22, 1.44, 1.52, "dark_steel", skip=("bottom",))
            mb.box(ax0, ax1, by - 0.04, by + 0.04, 1.20, 1.30, "barrier_arm")

        # 북측 1차선(west_close_look_ne/under_look_n 실물): 개방형 노란색 U자 파이프 보호가드 2기 + 외곽 백색 W-빔 가드레일
        for uy in (-4.40, -1.80):
            build_portal_arch(
                mb, A,
                [(-19.52, z_isl), (-19.52, 1.45), (-19.44, 1.62), (-19.04, 1.62), (-18.96, 1.45), (-18.96, z_isl)],
                uy, 0.055, 0.055, "safety_yellow", skip_bottom=True,
            )
            mb.box(-19.36, -19.12, uy + 0.18, uy + 0.44, z_isl, 1.32, "terminal_blue", skip=("bottom",))
        # 북측 외곽 연석 W-빔 가드레일
        mb.box(-20.02, -19.90, -10.50, 12.80, 0.94, 1.18, "booth_silver")
        for ry in (-10.0, -6.0, -2.0, 2.0, 6.0, 10.0, 12.4):
            mb.box(-19.90, -19.80, ry - 0.05, ry + 0.05, z_isl, 1.16, "dark_steel", skip=("bottom",))

    # 9. 지하통로 계단 초록 아치형 돔 3동 (Islands 2, 3, 4 서측 y ∈ [-5.10, -2.50])
    for dx in (-8.60, -2.70, 2.90):
        if stage == 2:
            mb.box(dx - 0.68, dx + 0.68, -5.10, -2.50, z_isl, 1.48, "green_dome", skip=("bottom",))
        else:
            mb.box(dx - 0.68, dx + 0.68, -5.10, -2.50, z_isl, 1.08, "concrete", skip=("bottom",))
            build_closed_arch_vault(
                mb, A, dx - 0.72, dx + 0.72, -5.10, -2.50, 1.12, 1.50, 0.08,
                6 if stage == 0 else 4, tag="green_dome", edge_tag="dark_steel",
            )
            if stage == 0:
                build_arch_rib(mb, A, dx - 0.72, dx + 0.72, -5.15, 0.08, 1.12, 1.50, 0.01, 0.08, 6, "dark_steel")
                build_arch_rib(mb, A, dx - 0.72, dx + 0.72, -2.45, 0.08, 1.12, 1.50, 0.01, 0.08, 6, "dark_steel")

    # 10. 아일랜드 파란색 강관 난간 & 충돌방지 충격흡수 블록/볼라드 (`stage == 0`)
    if stage == 0:
        dome_xs = {-8.60, -2.70, 2.90}
        for _name, x0, x1, y0, y1, _nl in islands[1:7]:
            xm = 0.5 * (x0 + x1)
            # 서/동 진입단 충격흡수 드럼/블록
            build_octagonal_prism(mb, A, xm, y0 + 0.58, z_isl, 1.28, 0.34, "bollard_stripe", cap_tag="dark_steel", skip_bottom=True)
            if abs(xm - (-8.60)) < 0.8:
                # 동측 Island 2 대형 황흑 사선 충격흡수 쿠션 (east_far_look_w 실물)
                mb.box(xm - 0.56, xm + 0.56, y1 - 1.15, y1 - 0.25, z_isl, 1.38, "bollard_stripe", skip=("bottom",))
            else:
                build_octagonal_prism(mb, A, xm, y1 - 0.58, z_isl, 1.32, 0.38, "bollard_stripe", cap_tag="dark_steel", skip_bottom=True)
            has_dome = any(abs(xm - dx) < 0.6 for dx in dome_xs)
            wy0 = max(y0 + 1.50, -9.60)
            wy1 = -5.45 if has_dome else -2.50
            ey0 = 3.00
            ey1 = min(y1 - 1.50, 8.60)
            for rx in (x0 + 0.14, x1 - 0.14):
                mb.box(rx - 0.03, rx + 0.03, ey0, ey1, 0.86, 0.93, "rail_blue")
                for ry in (ey0 + 0.10, 0.5 * (ey0 + ey1), ey1 - 0.10):
                    mb.box(rx - 0.035, rx + 0.035, ry - 0.035, ry + 0.035, z_isl, 0.86, "rail_blue", skip=("bottom", "top"))
                if wy1 - wy0 > 1.2:
                    mb.box(rx - 0.03, rx + 0.03, wy0, wy1, 0.86, 0.93, "rail_blue")
                    for ry in (wy0 + 0.10, 0.5 * (wy0 + wy1), wy1 - 0.10):
                        mb.box(rx - 0.035, rx + 0.035, ry - 0.035, ry + 0.035, z_isl, 0.86, "rail_blue", skip=("bottom", "top"))

    # 11. 전후방 3대 포털 갠트리 (모따기 아치 프레임 + 진행방향 단일면 발광/표지)
    # 11-A. 서측 출구 라임그린 2차선 하이패스 갠트리 (y = -13.60, Lanes 6+7, -Y 전면)
    gy_w = -13.60
    if stage == 2:
        for gx in (8.80, 14.40, 19.60):
            mb.box(gx - 0.16, gx + 0.16, gy_w - 0.18, gy_w + 0.18, z_isl, 5.95, "gantry_lime", skip=("bottom", "top"))
        mb.box(8.55, 19.85, gy_w - 0.22, gy_w + 0.22, 5.95, 6.32, "gantry_lime")
    else:
        build_portal_arch(
            mb, A,
            [(8.80, z_isl), (8.80, 5.65), (9.35, 6.20), (19.05, 6.20), (19.60, 5.65), (19.60, z_isl)],
            gy_w, 0.18, 0.16, "gantry_lime", skip_bottom=True,
        )
        mb.box(14.24, 14.56, gy_w - 0.17, gy_w + 0.17, z_isl, 6.04, "gantry_lime", skip=("bottom", "top"))
        # west_far_look_e: 두 전광판은 모따기 안쪽에 현수, 화살표는 상부 보 위에 장착.
        mb.box(8.95, 19.45, gy_w - 0.14, gy_w + 0.14, 4.98, 5.08, "gantry_lime")
        for sx, x0_s, x1_s, tag in ((11.65, 9.70, 13.85, "led_hipass"), (17.15, 14.95, 18.90, "led_warn")):
            build_graphic_box(mb, A, x0_s, x1_s, gy_w - 0.22, gy_w + 0.10, 5.17, 5.96,
                              "dark_steel", front_tag=tag)
            for mount in (sx - 0.85, sx + 0.85):
                mb.box(mount - 0.045, mount + 0.045, gy_w - 0.075, gy_w + 0.075, 5.95, 6.05, "dark_steel")
            build_graphic_box(mb, A, sx - 0.33, sx + 0.33, gy_w - 0.15, gy_w + 0.15, 6.36, 6.99,
                              "dark_steel", front_tag="sig_green_down", skip=("bottom",))
        if stage == 0:
            # 각 차로 중앙에 현수된 백색 사각 제한속도 30 표지판 + 기둥 하단 황흑 보호패드
            for gx in (8.80, 14.40, 19.60):
                mb.box(gx - 0.21, gx + 0.21, gy_w - 0.23, gy_w + 0.23, z_isl, 1.50, "bollard_stripe", skip=("bottom",))
            for sx in (11.65, 17.15):
                for hx in (sx - 0.28, sx + 0.28):
                    mb.box(hx - 0.025, hx + 0.025, gy_w - 0.04, gy_w + 0.04, 4.90, 5.12, "dark_steel", skip=("bottom", "top"))
                build_graphic_box(mb, A, sx - 0.42, sx + 0.42, gy_w - 0.08, gy_w + 0.02, 3.86, 4.90, "trim_white",
                                  front_tag="sign_30_panel", back_tag=None)

    # 11-B. 동측 진입 실버 1차선 하이패스 갠트리 (y = +12.00, Lane 2, +Y 전면)
    gy_e2 = 12.00
    if stage == 2:
        for gx in (-14.50, -8.60):
            mb.box(gx - 0.16, gx + 0.16, gy_e2 - 0.16, gy_e2 + 0.16, z_isl, 5.85, "gantry_grey", skip=("bottom", "top"))
        mb.box(-14.70, -8.40, gy_e2 - 0.20, gy_e2 + 0.20, 5.85, 6.20, "gantry_grey")
    else:
        build_portal_arch(
            mb, A,
            [(-14.50, z_isl), (-14.50, 5.55), (-14.00, 6.06), (-9.10, 6.06), (-8.60, 5.55), (-8.60, z_isl)],
            gy_e2, 0.16, 0.15, "gantry_grey", skip_bottom=True,
        )
        # east_near_look_w: 전광판 상단은 포털 보 하단과 분리하고 트러스에 지지.
        mb.box(-14.36, -8.74, gy_e2 - 0.10, gy_e2 + 0.10, 4.66, 4.74, "gantry_grey")
        build_graphic_box(mb, A, -13.63, -9.47, gy_e2 - 0.08, gy_e2 + 0.19, 5.04, 5.86, "dark_steel",
                          front_tag=None, back_tag="led_hipass")
        for mount in (-13.20, -9.90):
            mb.box(mount - 0.045, mount + 0.045, gy_e2 - 0.06, gy_e2 + 0.06, 5.85, 5.92, "gantry_grey")
        build_graphic_box(mb, A, -12.11, -11.39, gy_e2 - 0.15, gy_e2 + 0.15, 6.21, 6.86, "dark_steel",
                          back_tag="sig_green_down", skip=("bottom",))
    if stage == 0:
        for px_g in (-14.50, -8.60):
            mb.box(px_g - 0.24, px_g + 0.24, gy_e2 - 0.24, gy_e2 + 0.24, z_isl, z_isl + 0.04, "dark_steel", skip=("bottom",))
        for lx_s in (-14.15, -8.95):
            mb.box(lx_s - 0.025, lx_s + 0.025, gy_e2 - 0.05, gy_e2 + 0.05, 4.74, 5.92, "gantry_grey", skip=("bottom", "top"))
        for lx_s in (-13.10, -12.00, -11.00, -9.95):
            mb.box(lx_s - 0.022, lx_s + 0.022, gy_e2 - 0.04, gy_e2 + 0.04, 4.74, 5.05, "gantry_grey", skip=("bottom", "top"))
        # 하부 카메라 센서 포드
        mb.box(-11.88, -11.62, gy_e2 - 0.08, gy_e2 + 0.14, 4.42, 4.66, "trim_white")
        # Island 1 & Island 2 독립 원형 표지판 지주 (트럭진입금지 + 보조명판 + 제한속도 30, east_far_look_w 실물)
        for px, py_p in ((-8.15, 12.65), (-13.95, 13.15)):
            mb.box(px - 0.05, px + 0.05, py_p - 0.05, py_p + 0.05, z_isl, 5.05, "gantry_grey", skip=("bottom",))
            build_graphic_box(mb, A, px - 0.35, px + 0.35, py_p + 0.05, py_p + 0.11, 4.38, 5.08, "trim_white",
                              front_tag=None, back_tag="sign_notruck")
            mb.box(px - 0.34, px + 0.34, py_p + 0.05, py_p + 0.10, 4.08, 4.32, "trim_white")
            build_graphic_box(mb, A, px - 0.35, px + 0.35, py_p + 0.05, py_p + 0.11, 3.32, 4.02, "trim_white",
                              front_tag=None, back_tag="sign_30")
        # 내측 모따기 감지 센서 아치 (y = +9.20)
        build_portal_arch(
            mb, A,
            [(-14.30, z_isl), (-14.30, 4.82), (-13.92, 5.20), (-9.18, 5.20), (-8.80, 4.82), (-8.80, z_isl)],
            9.20, 0.11, 0.10, "gantry_grey", skip_bottom=True,
        )

    # 11-C. 동측 진입 오렌지 화물 하이패스·통행권 갠트리 (y = +12.80, Lane 1, +Y 전면)
    gy_e1 = 12.80
    if stage == 2:
        for gx in (-19.80, -14.50):
            mb.box(gx - 0.16, gx + 0.16, gy_e1 - 0.16, gy_e1 + 0.16, z_isl, 5.55, "gantry_orange", skip=("bottom", "top"))
        mb.box(-20.00, -14.30, gy_e1 - 0.20, gy_e1 + 0.20, 5.55, 5.92, "gantry_orange")
    else:
        # east_near_look_w 기준: 오렌지 모따기 아치 상부 위에 3분할 LED 박스 탑재
        build_portal_arch(
            mb, A,
            [(-19.80, z_isl), (-19.80, 4.82), (-19.28, 5.34), (-15.02, 5.34), (-14.50, 4.82), (-14.50, z_isl)],
            gy_e1, 0.17, 0.15, "gantry_orange", skip_bottom=True,
        )
        for mount in (-18.80, -15.50):
            mb.box(mount - 0.10, mount + 0.10, gy_e1 - 0.09, gy_e1 + 0.09, 5.48, 5.54, "dark_steel")
        build_graphic_box(mb, A, -19.45, -14.85, gy_e1 - 0.14, gy_e1 + 0.22, 5.53, 6.26, "dark_steel",
                          front_tag=None, back_tag="led_freight")
        build_graphic_box(mb, A, -17.76, -17.04, gy_e1 - 0.13, gy_e1 + 0.17, 6.26, 6.92, "dark_steel",
                          back_tag="sig_green_down", skip=("bottom",))
    if stage == 0:
        for px_g in (-19.80, -14.50):
            mb.box(px_g - 0.24, px_g + 0.24, gy_e1 - 0.24, gy_e1 + 0.24, z_isl, z_isl + 0.04, "dark_steel", skip=("bottom",))
        # 하부 슬림 실버 트러스 & 우측 차로 카메라 하우징 (east_near_look_w 실물)
        mb.box(-19.58, -14.72, gy_e1 - 0.10, gy_e1 + 0.10, 4.92, 4.98, "gantry_grey")
        for lx_f in (-18.80, -17.70, -16.60, -15.50):
            mb.box(lx_f - 0.025, lx_f + 0.025, gy_e1 - 0.04, gy_e1 + 0.04, 4.98, 5.19, "gantry_grey", skip=("bottom", "top"))
        mb.box(-16.15, -15.85, gy_e1 - 0.10, gy_e1 + 0.26, 4.68, 4.92, "trim_white")

    return dict(mb=mb, wins=wins)


def main():
    A = make_atlas(size=4096)
    s0 = build_stage(A, 0)
    s1 = build_stage(A, 1)
    s2 = build_stage(A, 2)

    out_dir = K.out_dir_from_argv("output")
    notes = {
        "building_name": "SintanjinTollgate (경부고속도로 신탄진IC 영업소)",
        "real_location": "36.43942N, 127.42217E / 대전 대덕구 덕암로 207",
        "azimuth_deg": -6.6,
        "lanes": 7,
        "islands": "6 central + 2 outer curbs",
        "photo_mode": "NOT_APPLICABLE",
    }
    res = K.export_asset(
        "SintanjinTollgate",
        level=1,
        meshes=dict(main=s0["mb"], lod1=s1["mb"], lod2=s2["mb"], windows=s0["wins"]),
        atlas=A,
        out_root=out_dir,
        lod2_tex=1024,
        lot=(6, 4),
        front_yard=1.5,
        notes=notes,
    )
    print(f"Exported SintanjinTollgate -> {res}")


if __name__ == "__main__":
    main()
