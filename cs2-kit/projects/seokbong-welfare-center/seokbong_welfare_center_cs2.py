# -*- coding: utf-8 -*-
"""석봉동 행정복지센터 (석봉복합문화센터) 정밀 CS2 에셋 생성기.

실측 근거 (대전광역시 대덕구 대덕대로 1579 / 석봉동 774):
- VWorld & Google z19 정사 위성영상 (0.24017 m/px, 건물 축 -11.2도 회전 정합)
- 2026-10-07 ~ 10-14 네이버 거리뷰 4방위·모서리 12개 시점 큐브맵 실측
- 공개 건축개요: 대지 5,400 m2, 건축면적 3,239.29 m2, 연면적 12,639.36 m2, 지하2~지상3층, 최고높이 ~21 m

좌표 규약:
- 1 unit = 1 m, 지면 z = 0, 정면(대덕대로, 남측) = -Y, 후면(북측 주차장) = +Y, 좌(-X)=서측 풋살장, 우(+X)=동측 골목
- 주 본체 폭 51.0 m (X in [-25.5, +25.5]), 깊이 70.2 m (Y in [0.0, 70.2]), 최고높이 20.8 m
"""

import math
import os
import sys

import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def find_kit():
    path = os.path.dirname(os.path.abspath(__file__))
    for _ in range(4):
        if os.path.exists(os.path.join(path, "cs2kit.py")):
            return path
        path = os.path.dirname(path)
    raise RuntimeError("cs2kit.py not found")


sys.path.insert(0, find_kit())
import cs2kit as K  # noqa: E402


# ---------------------------------------------------------------------------
# 폰트 및 사인 캔버스 캐시 유틸리티
# ---------------------------------------------------------------------------

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

# 표지석(2.4 x 1.4 m = 1.714:1)은 576x288 칸 왼쪽 494x288 활성 영역만 사용해 비율 정확도 0.6% 이내 유지
_SIGN_ACTIVE_W = {
    "sign_monolith": 494,
}


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
    while sz > 14:
        fnt = _load_font(candidates, sz)
        bb = drw.textbbox((0, 0), text, font=fnt)
        if (bb[2] - bb[0]) <= max_w:
            return fnt
        sz = max(14, int(sz * 0.90))
    return _load_font(candidates, 14)


def _text_metrics(drw, text, font):
    bb = drw.textbbox((0, 0), text, font=font)
    return bb[0], bb[1], bb[2] - bb[0], bb[3] - bb[1]


def _draw_3d_text(rgb_im, mask_im, emis_im, x, y, text, font, fill_rgb,
                  shadow_rgb=(168, 174, 180), emis_val=0, shadow_off=(5, 5), shadow_blur=1.6):
    """글자 본체 + 우하단 약한 그림자 + 양각 높이 마스크 + 야간 글자 전용 발광을 2x 캔버스에 그린다."""
    from PIL import Image, ImageDraw, ImageFilter

    dx, dy = shadow_off
    if shadow_rgb is not None:
        sh_alpha = Image.new("L", rgb_im.size, 0)
        ImageDraw.Draw(sh_alpha).text((x + dx, y + dy), text, font=font, fill=195)
        if shadow_blur > 0:
            sh_alpha = sh_alpha.filter(ImageFilter.GaussianBlur(shadow_blur))
        sh_layer = Image.new("RGB", rgb_im.size, shadow_rgb)
        rgb_im.paste(sh_layer, (0, 0), sh_alpha)

    ImageDraw.Draw(rgb_im).text((x, y), text, font=font, fill=fill_rgb)
    ImageDraw.Draw(mask_im).text((x, y), text, font=font, fill=255)
    if emis_val > 0:
        ImageDraw.Draw(emis_im).text((x, y), text, font=font, fill=int(emis_val))


def _render_sign_cell(ctx, cache_tag, bg_rgb, draw_2x_fn, active_w=None, relief=0.82, edge_blur=1.6):
    """개별 사인 칸(2x 슈퍼샘플링 + LANCZOS 축소 + 높이 베벨 + 글자 전용 발광 + 크기별 캐시)."""
    cw = active_w if active_w is not None else ctx.w
    ch = ctx.h
    ctx.rgb[...] = np.array(bg_rgb, np.float32)
    ctx.emis[...] = 0.0
    cache_path = os.path.join(_SIGN_CACHE_DIR, f"{cache_tag}_{ctx.w}x{ctx.h}.npz")

    try:
        from PIL import Image, ImageFilter
    except ImportError:
        if not os.path.exists(cache_path):
            raise RuntimeError(f"PIL unavailable and sign cache missing: {cache_path}")
        with np.load(cache_path) as d:
            ctx.rgb[...] = d["rgb"].astype(np.float32)
            ctx.emis[...] = d["emis"].astype(np.float32)
            if "height" in d:
                ctx.height[...] = d["height"].astype(np.float32)
        return

    w2, h2 = cw * 2, ch * 2
    rgb2 = Image.new("RGB", (w2, h2), bg_rgb)
    mask2 = Image.new("L", (w2, h2), 0)
    emis2 = Image.new("L", (w2, h2), 0)

    draw_2x_fn(rgb2, mask2, emis2, w2, h2)

    if edge_blur > 0:
        mask2 = mask2.filter(ImageFilter.GaussianBlur(edge_blur))

    rgb_im = rgb2.resize((cw, ch), Image.Resampling.LANCZOS)
    mask_im = mask2.resize((cw, ch), Image.Resampling.LANCZOS)
    emis_im = emis2.resize((cw, ch), Image.Resampling.LANCZOS)

    ctx.rgb[:, :cw, :] = np.asarray(rgb_im, dtype=np.float32)
    ctx.height[:, :cw] += relief * (np.asarray(mask_im, dtype=np.float32) / 255.0)
    ctx.emis[:, :cw] = np.asarray(emis_im, dtype=np.float32) / 255.0

    if cw < ctx.w:
        ctx.rgb[:, cw:, :] = ctx.rgb[:, cw - 1:cw, :]
        ctx.height[:, cw:] = 0.0
        ctx.emis[:, cw:] = 0.0

    os.makedirs(_SIGN_CACHE_DIR, exist_ok=True)
    np.savez(
        cache_path,
        rgb=np.clip(ctx.rgb, 0, 255).astype(np.uint8),
        emis=ctx.emis.astype(np.float16),
        height=ctx.height.astype(np.float16),
    )


def _draw_daedeok_badge(rgb_im, mask_im, cx, cy, r, shadow_rgb=(162, 168, 174)):
    """대덕구 심볼 배지 (백색 중앙 여백 + 녹색/청록/청색 호 심볼 + 약한 그림자 + 양각)."""
    from PIL import Image, ImageDraw, ImageFilter

    x0, y0, x1, y1 = int(cx - r), int(cy - r), int(cx + r), int(cy + r)
    if shadow_rgb is not None:
        sh = Image.new("L", rgb_im.size, 0)
        ImageDraw.Draw(sh).ellipse([x0 + 4, y0 + 4, x1 + 4, y1 + 4], fill=175)
        sh = sh.filter(ImageFilter.GaussianBlur(1.5))
        rgb_im.paste(Image.new("RGB", rgb_im.size, shadow_rgb), (0, 0), sh)

    drw = ImageDraw.Draw(rgb_im)
    drw.pieslice([x0, y0, x1, y1], 195, 345, fill=(76, 164, 74))
    drw.pieslice([x0, y0, x1, y1], 345, 95, fill=(32, 146, 172))
    drw.pieslice([x0, y0, x1, y1], 95, 195, fill=(28, 96, 152))
    ir = max(4, int(r * 0.42))
    drw.ellipse([int(cx - ir), int(cy - ir), int(cx + ir), int(cy + ir)], fill=(232, 234, 232))
    ImageDraw.Draw(mask_im).ellipse([x0, y0, x1, y1], fill=255)


def _draw_sign_panel_seams(rgb2, w2, h2, n_panels, seam_rgb=(210, 212, 210)):
    """간판 배경이 외벽 white_panel 줄눈과 자연스럽게 이어지도록 수직 패널 이음선 추가."""
    from PIL import ImageDraw
    drw = ImageDraw.Draw(rgb2)
    for i in range(1, n_panels):
        sx = int(round(w2 * i / float(n_panels)))
        drw.line([(sx, 0), (sx, h2)], fill=seam_rgb, width=2)


def _paint_sign_center_roof(ctx):
    """남측·서측 지붕 파시아 간판 (15.4x1.34 m, white_panel 정합 바탕 + 대덕 심볼 + 짙은 차콜 입체 글자)."""
    def paint_2x(rgb2, mask2, emis2, w2, h2):
        from PIL import ImageDraw
        _draw_sign_panel_seams(rgb2, w2, h2, n_panels=15, seam_rgb=(208, 211, 209))
        drw = ImageDraw.Draw(rgb2)
        text = "석봉복합문화센터"
        fnt = _fit_font(drw, FONT_KR, text, int(w2 * 0.72), int(h2 * 0.66))
        bx, by, tw, th = _text_metrics(drw, text, fnt)
        badge_r = int(th * 0.44)
        gap = int(badge_r * 0.75)
        total_w = badge_r * 2 + gap + tw
        start_x = (w2 - total_w) * 0.5
        _draw_daedeok_badge(rgb2, mask2, start_x + badge_r, h2 * 0.5, badge_r, shadow_rgb=(160, 165, 172))
        tx = start_x + badge_r * 2 + gap - bx
        ty = (h2 - th) * 0.5 - by
        _draw_3d_text(rgb2, mask2, emis2, tx, ty, text, fnt,
                      fill_rgb=(40, 46, 54), shadow_rgb=(156, 162, 168),
                      emis_val=165, shadow_off=(5, 5), shadow_blur=1.8)

    _render_sign_cell(ctx, "sign_center_roof", (232, 234, 232), paint_2x, relief=0.92)
    ctx.grain(amp=1.2, scale_px=2, height=0.05, seed=81)
    ctx.gloss[...] = 0.42


def _paint_sign_welfare_led(ctx):
    """1층 주출입구 LED 간판 (8.8x0.82 m, 흑색 프레임 + 청록-하늘 LED 글자)."""
    def paint_2x(rgb2, mask2, emis2, w2, h2):
        from PIL import ImageDraw
        drw = ImageDraw.Draw(rgb2)
        mdrw = ImageDraw.Draw(mask2)
        bw = max(6, int(h2 * 0.035))
        drw.rectangle([bw, bw, w2 - bw - 1, h2 - bw - 1], outline=(48, 54, 62), width=bw)
        mdrw.rectangle([bw, bw, w2 - bw - 1, h2 - bw - 1], outline=120, width=bw)
        text = "석봉동 행정복지센터"
        fnt = _fit_font(drw, FONT_KR, text, int(w2 * 0.86), int(h2 * 0.62))
        bx, by, tw, th = _text_metrics(drw, text, fnt)
        tx = (w2 - tw) * 0.5 - bx
        ty = (h2 - th) * 0.5 - by
        _draw_3d_text(rgb2, mask2, emis2, tx, ty, text, fnt,
                      fill_rgb=(124, 228, 250), shadow_rgb=(6, 8, 12),
                      emis_val=244, shadow_off=(4, 4), shadow_blur=1.2)

    _render_sign_cell(ctx, "sign_welfare_led", (18, 22, 28), paint_2x, relief=0.58)
    ctx.gloss[...] = 0.48


def _paint_sign_localfood(ctx):
    """사선 램프 우측 파시아 간판 (8.67x0.70 m, white_panel 바탕 + '대덕' 짙은 청남 + '로컬푸드직매장' 주황)."""
    def paint_2x(rgb2, mask2, emis2, w2, h2):
        from PIL import ImageDraw
        _draw_sign_panel_seams(rgb2, w2, h2, n_panels=9, seam_rgb=(208, 211, 209))
        drw = ImageDraw.Draw(rgb2)
        t_left = "대덕"
        t_right = "로컬푸드직매장"
        full = t_left + t_right
        fnt = _fit_font(drw, FONT_KR, full, int(w2 * 0.78), int(h2 * 0.64))
        bx, by, tw, th = _text_metrics(drw, full, fnt)
        _, _, tw_l, _ = _text_metrics(drw, t_left, fnt)
        badge_r = int(th * 0.42)
        gap = int(badge_r * 0.70)
        total_w = badge_r * 2 + gap + tw
        start_x = (w2 - total_w) * 0.5
        _draw_daedeok_badge(rgb2, mask2, start_x + badge_r, h2 * 0.5, badge_r, shadow_rgb=(162, 168, 172))
        tx = start_x + badge_r * 2 + gap - bx
        ty = (h2 - th) * 0.5 - by
        _draw_3d_text(rgb2, mask2, emis2, tx, ty, t_left, fnt,
                      fill_rgb=(24, 54, 72), shadow_rgb=(160, 166, 170),
                      emis_val=155, shadow_off=(4, 4), shadow_blur=1.5)
        _draw_3d_text(rgb2, mask2, emis2, tx + tw_l + int(w2 * 0.004), ty, t_right, fnt,
                      fill_rgb=(198, 102, 34), shadow_rgb=(160, 166, 170),
                      emis_val=175, shadow_off=(4, 4), shadow_blur=1.5)

    _render_sign_cell(ctx, "sign_localfood", (232, 234, 232), paint_2x, relief=0.82)
    ctx.grain(amp=1.2, scale_px=2, height=0.05, seed=82)
    ctx.gloss[...] = 0.42


def _paint_sign_monolith(ctx):
    """남동 광장 전면 표지석 동판 (2.4x1.4 m, 다크 브론즈 바탕 + 석봉 / 석봉복합문화센터 입체 글자)."""
    active_w = _SIGN_ACTIVE_W["sign_monolith"]

    def paint_2x(rgb2, mask2, emis2, w2, h2):
        from PIL import ImageDraw
        drw = ImageDraw.Draw(rgb2)
        mdrw = ImageDraw.Draw(mask2)
        pad = 14
        drw.rectangle([pad, pad, w2 - pad - 1, h2 - pad - 1], outline=(194, 176, 156), width=6)
        mdrw.rectangle([pad, pad, w2 - pad - 1, h2 - pad - 1], outline=140, width=6)

        # 중앙 상단 육각 문양 + '석 봉'
        cx, cy_top = w2 * 0.5, h2 * 0.36
        hr = h2 * 0.25
        hex_pts = [(cx + hr * math.cos(math.radians(60 * k + 30)),
                    cy_top + hr * math.sin(math.radians(60 * k + 30))) for k in range(6)]
        drw.polygon(hex_pts, outline=(228, 220, 208), width=4)
        mdrw.polygon(hex_pts, outline=130, width=4)

        t1 = "석 봉"
        f1 = _fit_font(drw, FONT_KR, t1, int(w2 * 0.56), int(h2 * 0.28))
        bx1, by1, tw1, th1 = _text_metrics(drw, t1, f1)
        _draw_3d_text(rgb2, mask2, emis2, (w2 - tw1) * 0.5 - bx1, cy_top - th1 * 0.5 - by1,
                      t1, f1, fill_rgb=(246, 244, 240), shadow_rgb=(36, 20, 16),
                      emis_val=155, shadow_off=(4, 4), shadow_blur=1.3)

        # 구분선 + 하단 '석봉복합문화센터'
        div_y = int(h2 * 0.65)
        drw.line([(int(w2 * 0.16), div_y), (int(w2 * 0.84), div_y)], fill=(202, 188, 170), width=3)
        mdrw.line([(int(w2 * 0.16), div_y), (int(w2 * 0.84), div_y)], fill=110, width=3)

        t2 = "석봉복합문화센터"
        f2 = _fit_font(drw, FONT_KR, t2, int(w2 * 0.80), int(h2 * 0.17))
        bx2, by2, tw2, th2 = _text_metrics(drw, t2, f2)
        _draw_3d_text(rgb2, mask2, emis2, (w2 - tw2) * 0.5 - bx2, h2 * 0.78 - th2 * 0.5 - by2,
                      t2, f2, fill_rgb=(242, 236, 228), shadow_rgb=(36, 20, 16),
                      emis_val=170, shadow_off=(3, 3), shadow_blur=1.1)

    _render_sign_cell(ctx, "sign_monolith", (84, 54, 42), paint_2x, active_w=active_w, relief=0.78)
    ctx.grain(amp=1.8, scale_px=2, height=0.06, seed=83)
    ctx.gloss[...] = 0.40


# ---------------------------------------------------------------------------
# 아틀라스 재질 페인터 (4096x4096)
# ---------------------------------------------------------------------------

def _variant_weather(ctx, amount=0.025, cu=3, cv=3, seed=7):
    """변형(vi)마다 서로 다른 시드로 주기적 미세 웨더링을 적용해 넓은 벽의 반복감을 줄인다."""
    vw = ctx.w // max(1, ctx.variants)
    for v in range(ctx.variants):
        rng = np.random.default_rng(seed + v * 37)
        pu = rng.uniform(0, 2 * math.pi, 2)
        pv = rng.uniform(0, 2 * math.pi, 2)
        sl = slice(v * vw, (v + 1) * vw if v < ctx.variants - 1 else ctx.w)
        vu = ctx.vu[:, sl]
        vv = ctx.v[:, sl]
        w = 0.5 * np.sin(2 * math.pi * cu * vu + pu[0]) + 0.5 * np.cos(2 * math.pi * cv * vv + pv[0])
        k = 1.0 - amount * (0.5 + 0.5 * w)
        ctx.rgb[:, sl] *= k[..., None]
        ctx.gloss[:, sl] *= (1.0 - 0.12 * amount * (0.5 + 0.5 * w))


def _paint_white_panel(ctx):
    # 백색 대형 알루미늄 복합판넬 (north_ne_oblique.png · dnbarch_3.jpg 기준: 과노출 클리핑 방지 + 1x1m 패널 줄눈/변주)
    base_mean = ctx.rgb.mean(axis=(0, 1)).copy()
    d = ctx.joints(cols=4, rows=4, width_m=0.012, depth=0.72, stagger=0.0, darken=0.14, tone=2.4, seed=11)
    ctx.grain(amp=1.4, scale_px=2, height=0.07, seed=12)
    ctx.rgb += ctx.noise(scale_px=48, amp=1.4, octaves=3, seed=13)[..., None]
    ctx.stains(amount=0.040, scale_px=64, streaks=0.45, seed=14)
    _variant_weather(ctx, amount=0.018, cu=2, cv=2, seed=15)
    face = d < 0.15
    if np.any(face):
        cur_mean = ctx.rgb[face].mean(axis=0)
        ctx.rgb[face] += (base_mean - cur_mean)
    ctx.rgb[...] = np.clip(ctx.rgb, 180.0, 244.0)


def _paint_white_grooved(ctx):
    # 북측 체육관 상단 4단 수평 그루브 백색 메탈 파시아 (north_front_mid.png 기준)
    base_mean = ctx.rgb.mean(axis=(0, 1)).copy()
    _, my = ctx.meters()
    d = ctx.joints(cols=2, rows=5, width_m=0.014, depth=0.68, stagger=0.0, darken=0.14, tone=2.2, seed=16)
    groove = np.abs((my % 0.80) - 0.40) > 0.378
    ctx.rgb[groove] *= 0.64
    ctx.height[groove] -= 0.85
    ctx.grain(amp=1.4, scale_px=2, height=0.07, seed=17)
    ctx.rgb += ctx.noise(scale_px=48, amp=1.4, octaves=3, seed=18)[..., None]
    ctx.stains(amount=0.040, scale_px=56, streaks=0.45, seed=19)
    _variant_weather(ctx, amount=0.016, cu=2, cv=1, seed=20)
    face = (d < 0.15) & ~groove
    if np.any(face):
        cur_mean = ctx.rgb[face].mean(axis=0)
        ctx.rgb[face] += (base_mean - cur_mean)
    ctx.rgb[...] = np.clip(ctx.rgb, 138.0, 242.0)


def _paint_beige_stone(ctx):
    # 1~2층 웜베이지 화강석 석재 패널 (north_front_mid.png · dnbarch_3.jpg 기준: 밝고 따뜻한 아이보리/크림 화강석)
    base_mean = ctx.rgb.mean(axis=(0, 1)).copy()
    d = ctx.joints(cols=2, rows=5, width_m=0.012, depth=0.72, stagger=0.5, darken=0.19, tone=3.0, seed=21)
    ctx.grain(amp=3.2, scale_px=2, height=0.20, seed=22)
    fleck = ctx.noise(scale_px=3, amp=1.0, octaves=1, seed=26) < -1.20
    ctx.rgb[fleck] *= 0.93
    ctx.rgb += ctx.noise(scale_px=32, amp=1.8, octaves=3, seed=23)[..., None]
    ctx.stains(amount=0.045, scale_px=56, streaks=0.40, seed=24)
    _variant_weather(ctx, amount=0.018, cu=2, cv=2, seed=25)
    face = d < 0.15
    if np.any(face):
        cur_mean = ctx.rgb[face].mean(axis=0)
        ctx.rgb[face] += (base_mean - cur_mean)
    ctx.rgb[...] = np.clip(ctx.rgb, 148.0, 236.0)


def _paint_brown_panel(ctx):
    # 북측 3층·중정 상부 다크 브론즈-에스프레소 수평 메탈 패널 (north_front_mid.png · dnbarch_4.jpg 기준)
    base_mean = ctx.rgb.mean(axis=(0, 1)).copy()
    d = ctx.joints(cols=2, rows=5, width_m=0.012, depth=0.70, stagger=0.0, darken=0.24, tone=3.2, seed=31)
    ctx.grain(amp=1.8, scale_px=2, height=0.08, seed=32)
    ctx.rgb += ctx.noise(scale_px=40, amp=1.8, octaves=3, seed=33)[..., None]
    ctx.stains(amount=0.055, scale_px=48, streaks=0.40, seed=34)
    _variant_weather(ctx, amount=0.022, cu=2, cv=2, seed=35)
    face = d < 0.15
    if np.any(face):
        cur_mean = ctx.rgb[face].mean(axis=0)
        ctx.rgb[face] += (base_mean - cur_mean)
    ctx.rgb[...] = np.clip(ctx.rgb, 48.0, 128.0)


def _paint_roof_membrane(ctx):
    # 남서·남동 주지붕 밝은 쿨화이트 방수 시트 (sat_vworld_z19.png · dnbarch_3.jpg 기준)
    base_mean = ctx.rgb.mean(axis=(0, 1)).copy()
    d = ctx.joints(cols=4, rows=2, width_m=0.015, depth=0.28, darken=0.08, tone=1.8, seed=41)
    ctx.grain(amp=2.6, scale_px=2, height=0.12, seed=42)
    ctx.rgb += ctx.noise(scale_px=44, amp=2.2, octaves=3, seed=43)[..., None]
    ctx.stains(amount=0.038, scale_px=64, streaks=0.10, seed=44)
    _variant_weather(ctx, amount=0.018, cu=2, cv=2, seed=45)
    face = d < 0.15
    if np.any(face):
        cur_mean = ctx.rgb[face].mean(axis=0)
        ctx.rgb[face] += (base_mean - cur_mean)
    ctx.rgb[...] = np.clip(ctx.rgb, 185.0, 238.0)


def _paint_roof_concrete(ctx):
    # 동측 연결동 옥상 웜 스톤-콘크리트 지붕 바닥 (sat_vworld_z19.png 기준)
    base_mean = ctx.rgb.mean(axis=(0, 1)).copy()
    d = ctx.joints(cols=3, rows=3, width_m=0.014, depth=0.35, darken=0.10, tone=2.2, seed=46)
    ctx.grain(amp=3.4, scale_px=2, height=0.15, seed=47)
    ctx.rgb += ctx.noise(scale_px=38, amp=2.4, octaves=3, seed=48)[..., None]
    ctx.stains(amount=0.048, scale_px=56, streaks=0.10, seed=49)
    face = d < 0.15
    if np.any(face):
        cur_mean = ctx.rgb[face].mean(axis=0)
        ctx.rgb[face] += (base_mean - cur_mean)
    ctx.rgb[...] = np.clip(ctx.rgb, 165.0, 228.0)


def _paint_roof_soffit(ctx):
    # 지붕 캔틸레버 하부 soffit 백색-라이트그레이 패널 (north_ne_oblique.png 기준: 그림자는 조명/AO가 처리)
    base_mean = ctx.rgb.mean(axis=(0, 1)).copy()
    d = ctx.joints(cols=4, rows=4, width_m=0.014, depth=0.62, stagger=0.0, darken=0.15, tone=1.8, seed=19)
    ctx.grain(amp=1.4, scale_px=2, height=0.07, seed=20)
    ctx.rgb += ctx.noise(scale_px=48, amp=1.6, octaves=2, seed=28)[..., None]
    ctx.stains(amount=0.035, scale_px=64, streaks=0.10, seed=29)
    _variant_weather(ctx, amount=0.015, cu=2, cv=2, seed=30)
    face = d < 0.15
    if np.any(face):
        cur_mean = ctx.rgb[face].mean(axis=0)
        ctx.rgb[face] += (base_mean - cur_mean)
    ctx.rgb[...] = np.clip(ctx.rgb, 150.0, 222.0)


def _paint_terrace_deck(ctx):
    # 그린테라스 및 중정 합성목재 데크 (dnbarch_4.jpg · dnbarch_3.jpg · 위성 기준: 짙은 스모크드 월넛 판재 + 나뭇결)
    base_mean = ctx.rgb.mean(axis=(0, 1)).copy()
    mx, my = ctx.meters()
    pw = 0.16
    pid = np.floor(mx / pw).astype(np.int64)
    plank_seam = np.abs((mx % pw) - pw * 0.5) > (pw * 0.5 - 0.008)
    end_seam = np.abs(((my + (pid % 2) * 1.0) % 2.0) - 1.0) > 0.992
    tone = (((pid * 37 + 11) % 13) - 6) * 1.2
    ctx.rgb += tone[..., None]
    # 목재 길이(Y) 방향 미세 결
    ctx.rgb += (ctx.noise(scale_px=4, amp=1.6, octaves=2, seed=52) * 0.7)[..., None]
    ctx.rgb += ctx.noise(scale_px=36, amp=2.0, octaves=3, seed=53)[..., None]
    seam = plank_seam | end_seam
    ctx.rgb[seam] *= 0.68
    ctx.height[seam] -= 0.35
    ctx.stains(amount=0.050, scale_px=56, streaks=0.15, seed=54)
    _variant_weather(ctx, amount=0.022, cu=2, cv=2, seed=55)
    face = ~seam
    if np.any(face):
        cur_mean = ctx.rgb[face].mean(axis=0)
        ctx.rgb[face] += (base_mean - cur_mean) * 0.85
    ctx.rgb[...] = np.clip(ctx.rgb, 36.0, 120.0)


def _paint_stair_stone(ctx):
    # 동측 외부 계단 · 데크 화강석 디딤판 (north_ne_oblique.png 기준: 웜 다크그레이 화강석 판석)
    base_mean = ctx.rgb.mean(axis=(0, 1)).copy()
    d = ctx.joints(cols=4, rows=8, width_m=0.012, depth=0.58, stagger=0.5, darken=0.20, tone=3.0, seed=57)
    ctx.grain(amp=4.4, scale_px=2, height=0.20, seed=58)
    ctx.rgb += ctx.noise(scale_px=32, amp=2.2, octaves=3, seed=59)[..., None]
    ctx.stains(amount=0.055, scale_px=52, streaks=0.20, seed=60)
    face = d < 0.15
    if np.any(face):
        cur_mean = ctx.rgb[face].mean(axis=0)
        ctx.rgb[face] += (base_mean - cur_mean)
    ctx.rgb[...] = np.clip(ctx.rgb, 78.0, 158.0)


def _paint_plaza_paving(ctx):
    # 지상 및 북동 광장 줄무늬 보도블록 (north_ne_oblique.png 기준: 밝은 은회색 화강석 + 연한 샌드크림 띠)
    _, my = ctx.meters()
    band = ((my % 2.0) < 0.55)
    ctx.rgb[band] = np.array([206.0, 192.0, 172.0], np.float32)
    ctx.joints(cols=8, rows=12, width_m=0.009, depth=0.45, stagger=0.5, darken=0.14, tone=2.8, seed=61)
    ctx.grain(amp=3.8, scale_px=2, height=0.16, seed=62)
    ctx.rgb += ctx.noise(scale_px=36, amp=2.0, octaves=3, seed=63)[..., None]
    ctx.stains(amount=0.032, scale_px=64, streaks=0.0, seed=64)
    ctx.rgb[...] = np.clip(ctx.rgb, 148.0, 234.0)


def _paint_monolith_stone(ctx):
    # 표지석 하부 및 배면 밝은 소금후추 거친 화강석 블록 (dnbarch_2.jpg · south_se_close.png 기준)
    base_mean = ctx.rgb.mean(axis=(0, 1)).copy()
    d = ctx.joints(cols=3, rows=4, width_m=0.012, depth=0.85, stagger=0.5, darken=0.26, tone=6.5, seed=74)
    ctx.grain(amp=14.0, scale_px=2, height=0.45, seed=75)
    speck = ctx.noise(scale_px=2, amp=1.0, octaves=1, seed=78)
    ctx.rgb[speck < -1.0] *= 0.68
    ctx.rgb[speck > 1.1] = np.minimum(210.0, ctx.rgb[speck > 1.1] * 1.24)
    ctx.rgb += ctx.noise(scale_px=14, amp=5.5, octaves=3, seed=76)[..., None]
    ctx.stains(amount=0.055, scale_px=40, streaks=0.35, seed=77)
    face = d < 0.15
    if np.any(face):
        cur_mean = ctx.rgb[face].mean(axis=0)
        ctx.rgb[face] += (base_mean - cur_mean)
    ctx.rgb[...] = np.clip(ctx.rgb, 48.0, 205.0)


def _paint_green_planter(ctx):
    # 조경 화단 식재 (dnbarch_3/4 기준: 짙은 부엽토 + 올리브/세이지 관목 군락 변주)
    clump = ctx.noise(scale_px=12, amp=1.0, octaves=3, seed=67)
    leaf = ctx.noise(scale_px=3, amp=1.0, octaves=2, seed=65)
    ctx.rgb[...] += clump[..., None] * np.array([10.0, 13.0, 7.0], np.float32)
    ctx.rgb[...] += leaf[..., None] * np.array([8.0, 11.0, 6.0], np.float32)
    soil = clump < -1.25
    ctx.rgb[soil] = np.array([50.0, 56.0, 42.0], np.float32)
    ctx.height[...] += 0.45 * leaf + 0.30 * clump
    ctx.stains(amount=0.060, scale_px=32, streaks=0.0, seed=68)
    _variant_weather(ctx, amount=0.05, cu=4, cv=4, seed=66)
    ctx.rgb[...] = np.clip(ctx.rgb, 30.0, 142.0)


def _paint_solar_pv(ctx):
    mx, my = ctx.meters()
    fu = mx % 1.0
    fv = (my % 2.0) / 2.0
    frame = (fu < 0.032) | (fu > 0.968) | (fv < 0.022) | (fv > 0.978)
    cu = ((fu - 0.032) / 0.936 * 6.0) % 1.0
    cv = ((fv - 0.022) / 0.956 * 10.0) % 1.0
    grid_line = (cu < 0.032) | (cu > 0.968) | (cv < 0.028) | (cv > 0.972)
    # 위성(sat_vworld_z19) 타일 평균 #384f56 유지 + 셀 미세 반사 변주
    ctx.rgb[...] = np.array([44, 64, 74], np.float32)
    ctx.rgb += (2.5 * np.sin(2.0 * math.pi * (fu + fv)))[..., None]
    ctx.rgb[grid_line & ~frame] = np.array([72, 94, 104], np.float32)
    ctx.rgb[frame] = np.array([186, 192, 200], np.float32)
    ctx.height[frame] += 0.25
    ctx.height[grid_line & ~frame] -= 0.06
    ctx.gloss[...] = np.where(frame, 0.58, 0.86)
    ctx.emis[...] = 0.0


def _paint_louver_grille(ctx):
    # 북측 1층·나루마당 알루미늄 환기 루버 (north_front_mid.png 기준: 밝은 사틴 은백 알루미늄 슬랫)
    u, v = ctx.u, ctx.v
    border = (u < 0.045) | (u > 0.955) | (v < 0.055) | (v > 0.945)
    ph = (v * 12.0) % 1.0
    shadow = ph < 0.28
    face = (ph >= 0.28) & ~border
    ctx.rgb[border] = np.array([166, 172, 178], np.float32)
    ctx.rgb[shadow & ~border] = np.array([82, 88, 96], np.float32)
    ctx.rgb[face] = np.array([194, 199, 205], np.float32)
    ctx.height[shadow & ~border] -= 0.50
    ctx.height[face] += 0.15


def _paint_spandrel(ctx):
    # 커튼월 층간 슬래브 스팬드럴 (dnbarch_2.jpg · east_front_mid.png 기준: 짙은 슬레이트-틸 후면 배면유리)
    u, v = ctx.u, ctx.v
    sky_grad = (v - 0.5) * 14.0
    refl = 3.0 * np.sin(2.0 * math.pi * (u * 1.5 + v * 0.5))
    ctx.rgb[...] = np.clip(np.array([36.0, 56.0, 72.0], np.float32) + (sky_grad + refl)[..., None], 22.0, 92.0)
    ctx.joints(cols=2, rows=2, width_m=0.014, depth=0.25, darken=0.10, tone=1.4, seed=71)
    ctx.gloss[...] = 0.88
    ctx.emis[...] = 0.0


def _paint_teal_glass(ctx):
    """남측 램프 하부 1층 다크 에메랄드-틸 Low-E 커튼월 유리 (south_se_close.png 기준: 짙은 청록 반사 + 야간 부분 점등)."""
    u, v = ctx.u, ctx.v
    cols, rows = 6, 2
    cx = np.floor(u * cols).astype(np.int64)
    cy = np.floor(v * rows).astype(np.int64)
    fv = (v * rows) % 1.0
    h = ((cx * 37 + cy * 53) % 100) / 100.0

    # 상부(fv~1) 하늘 반사 + 하부(fv~0) 짙은 청록 실내 깊이감, 주간/야간 BaseColor 일관 유지
    sky_grad = (fv - 0.40) * 18.0 + 4.0 * np.sin(2.0 * math.pi * (u * 1.5 + v * 0.5))
    tint = (h - 0.5) * 6.0
    base_rgb = np.array([46.0, 94.0, 98.0], np.float32) + (tint + sky_grad)[..., None]

    # 야간 일부 베이(~33%) 은은한 실내 점등 + 외곽 밉맵 번짐 방지 가드
    cid = cy * cols + cx
    lit = np.isin(cid, (0, 3, 7, 10))
    r = max(2, round(ctx.w * 0.016))
    m = np.pad(lit, r, constant_values=False)
    for ax in (0, 1):
        m = np.logical_and.reduce([np.roll(m, k, ax) for k in range(-r, r + 1)])
    lit = m[r:-r, r:-r]
    glow = 0.26 + 0.10 * (1.0 - fv)
    ctx.rgb[...] = np.clip(base_rgb, 30.0, 134.0)
    ctx.emis[...] = np.where(lit, glow, 0.0)
    ctx.gloss[...] = 0.92


def _paint_window_atlas(ctx):
    """5x5 REF_GRID 창문 아틀라스 (깊은 로이(Low-E) 청록-슬레이트 반사유리 + 약 32% 야간 점등, 1px 슬롯 비침범 가드)."""
    g = K.REF_GRID
    u, v = ctx.u, ctx.v
    fu = (u * g) % 1.0
    fv = (v * g) % 1.0
    cx = np.floor(u * g).astype(np.int64)
    cy = np.floor(v * g).astype(np.int64)
    cid = cy * g + cx
    h = ((cx * 37 + cy * 71) % 100) / 100.0

    # 상부(fv~1) 은은한 하늘 반사 광택 -> 하부(fv~0) 깊은 슬레이트-청록 로이유리 깊이감 + 미세 창틀 음영
    sky_grad = (fv - 0.35) * 24.0 + 4.0 * np.sin(2.0 * math.pi * (u * 1.5 + v * 1.0))
    tint = (h - 0.5) * 5.0
    base_rgb = (
        np.array([74.0, 118.0, 150.0], np.float32)
        + (tint + sky_grad)[..., None] * np.array([0.85, 0.95, 1.0], np.float32)
    )
    edge = (np.minimum(fu, 1.0 - fu) < 0.03) | (np.minimum(fv, 1.0 - fv) < 0.03)
    base_rgb[edge] *= 0.90
    ctx.rgb[...] = np.clip(base_rgb, 44.0, 182.0)

    # 연속 점등 블록 (cells 0..7 ~32% 점등), r=1px로 22px 창 슬롯 절반 절단 방지 + 패딩 내 밉맵 가드
    lit = cid < 8
    r = 1
    m = np.pad(lit, r, constant_values=False)
    for ax in (0, 1):
        m = np.logical_and.reduce([np.roll(m, k, ax) for k in range(-r, r + 1)])
    lit = m[r:-r, r:-r]

    glow = (0.28 + 0.12 * ((h * 17.0) % 1.0)) * (0.86 + 0.14 * (1.0 - fv * 0.4))
    ctx.emis[...] = np.where(lit, glow, 0.0)
    ctx.gloss[...] = 0.93


def _paint_entrance_door(ctx):
    u, v = ctx.u, ctx.v
    frame = (u < 0.05) | (u > 0.95) | (v > 0.95) | (np.abs(u - 0.50) < 0.025) | (np.abs(v - 0.78) < 0.022)
    glass = ~frame & (v > 0.06)
    ctx.rgb[frame] = np.array([36, 40, 46], np.float32)
    ctx.rgb[glass] = np.array([42, 62, 74], np.float32) + (v[glass] * 16.0)[..., None]
    ctx.gloss[...] = np.where(glass, 0.90, 0.52)
    ctx.emis[...] = np.where(glass, 0.24, 0.0)


def _paint_equipment(ctx):
    border = (ctx.u < 0.04) | (ctx.u > 0.96) | (ctx.v < 0.04) | (ctx.v > 0.96) | (np.abs(ctx.u - 0.50) < 0.015)
    ctx.rgb[border] *= 0.76
    ctx.height[border] -= 0.35
    louv = (ctx.u > 0.14) & (ctx.u < 0.86) & (ctx.v > 0.22) & (ctx.v < 0.78) & (((ctx.v * 24.0) % 1.0) < 0.36)
    ctx.rgb[louv] *= 0.52
    ctx.height[louv] -= 0.45
    ctx.grain(amp=1.6, scale_px=2, height=0.07, seed=72)
    ctx.stains(amount=0.032, scale_px=36, streaks=0.25, seed=73)


def _paint_louver_white(ctx):
    # 백색 도장 알루미늄 루버 핀 · #퍼골라 (미세 표면 결 부여해 플라스틱 평탄함 완화)
    ctx.grain(amp=1.2, scale_px=2, height=0.04, seed=91)
    ctx.rgb += ctx.noise(scale_px=24, amp=1.0, octaves=2, seed=92)[..., None]
    ctx.rgb[...] = np.clip(ctx.rgb, 214.0, 242.0)


def _paint_anodized_metal(ctx):
    # 아노다이징 금속 프레임 · 멀리언 · 스테인리스 난간 미세 브러시드 질감
    ctx.grain(amp=1.5, scale_px=2, height=0.04, seed=94)
    ctx.rgb += ctx.noise(scale_px=18, amp=1.2, octaves=2, seed=95)[..., None]


def _paint_lamp_strip(ctx):
    ctx.rgb[...] = np.array([252, 248, 232], np.float32)
    ctx.emis[...] = 0.88


def make_atlas(size=4096):
    A = K.Atlas(size=size, pad=16)
    A.add("white_panel",   color=(232, 234, 232), ctrl=(0, 0, 0), metal=0.14, gloss=0.42,
          px=1024, tile=(4.0, 4.0), variants=3, painter=_paint_white_panel, normal_strength=2.2)
    A.add("white_grooved", color=(229, 231, 229), ctrl=(0, 0, 0), metal=0.15, gloss=0.42,
          px=768, tile=(4.0, 4.0), variants=2, painter=_paint_white_grooved, normal_strength=2.6)
    A.add("beige_stone",   color=(218, 204, 188), ctrl=(0, 0, 0), metal=0.0, gloss=0.26,
          px=768, tile=(3.0, 3.0), variants=2, painter=_paint_beige_stone, normal_strength=2.4)
    A.add("brown_panel",   color=(94, 78, 72), ctrl=(0, 0, 0), metal=0.28, gloss=0.44,
          px=768, tile=(4.0, 4.0), variants=2, painter=_paint_brown_panel, normal_strength=2.4)
    A.add("roof_membrane", color=(220, 224, 224), ctrl=(0, 0, 0), metal=0.0, gloss=0.20,
          px=512, tile=(3.2, 3.2), painter=_paint_roof_membrane, normal_strength=1.5)
    A.add("roof_concrete", color=(206, 202, 188), ctrl=(0, 0, 0), metal=0.0, gloss=0.18,
          px=512, tile=(3.2, 3.2), painter=_paint_roof_concrete, normal_strength=1.5)
    A.add("roof_soffit",   color=(198, 202, 206), ctrl=(0, 0, 0), metal=0.12, gloss=0.26,
          px=512, tile=(4.0, 4.0), painter=_paint_roof_soffit, normal_strength=1.6)
    A.add("terrace_deck",  color=(84, 68, 60), ctrl=(0, 0, 0), metal=0.0, gloss=0.24,
          px=512, tile=(4.0, 4.0), painter=_paint_terrace_deck, normal_strength=2.2)
    A.add("stair_stone",   color=(124, 118, 112), ctrl=(0, 0, 0), metal=0.0, gloss=0.24,
          px=512, tile=(4.0, 4.0), painter=_paint_stair_stone, normal_strength=2.2)
    A.add("plaza_paving",  color=(216, 216, 214), ctrl=(0, 0, 0), metal=0.0, gloss=0.20,
          px=512, tile=(4.0, 4.0), painter=_paint_plaza_paving, normal_strength=1.9)
    A.add("green_planter", color=(66, 98, 56), ctrl=(0, 0, 0), metal=0.0, gloss=0.12,
          px=256, tile=(3.0, 3.0), painter=_paint_green_planter, normal_strength=2.0)
    A.add("solar_pv",      color=(46, 66, 76), ctrl=(0, 0, 0), metal=0.38, gloss=0.86,
          px=512, tile=(2.0, 2.0), painter=_paint_solar_pv, normal_strength=2.0)
    A.add("louver_grille", color=(190, 196, 202), ctrl=(0, 0, 0), metal=0.52, gloss=0.48,
          px=256, tile=(2.0, 1.5), painter=_paint_louver_grille, normal_strength=2.4)
    A.add("spandrel_dark", color=(36, 56, 72), ctrl=(0, 0, 0), metal=0.12, gloss=0.88,
          px=256, tile=(2.0, 2.0), painter=_paint_spandrel, normal_strength=1.2)
    A.add("teal_glass",    color=(46, 94, 98), ctrl=(0, 0, 0), metal=0.14, gloss=0.92,
          emissive=(255, 228, 184), px=512, tile=(22.6 / 38.0 * 6.0, 4.0),
          painter=_paint_teal_glass, normal_strength=1.2)
    A.add("frame_metal",   color=(40, 44, 50), ctrl=(0, 0, 0), metal=0.55, gloss=0.52,
          px=128, painter=_paint_anodized_metal, normal_strength=1.0)
    A.add("curtain_frame", color=(48, 54, 62), ctrl=(0, 0, 0), metal=0.58, gloss=0.55,
          px=128, painter=_paint_anodized_metal, normal_strength=1.0)
    A.add("louver_white",  color=(234, 235, 233), ctrl=(0, 0, 0), metal=0.18, gloss=0.46,
          px=128, painter=_paint_louver_white, normal_strength=1.2)
    A.add("railing_steel", color=(192, 198, 204), ctrl=(0, 0, 0), metal=0.85, gloss=0.72,
          px=128, painter=_paint_anodized_metal, normal_strength=1.0)
    A.add("glass_rail",    color=(154, 182, 196), ctrl=(0, 0, 0), metal=0.0, gloss=0.92, px=128)
    A.add("door_entrance", color=(42, 62, 74), ctrl=(0, 0, 0), metal=0.20, gloss=0.84,
          emissive=(235, 224, 198), px=256, painter=_paint_entrance_door, normal_strength=1.8)
    A.add("equipment",     color=(194, 200, 206), ctrl=(0, 0, 0), metal=0.35, gloss=0.40,
          px=256, painter=_paint_equipment, normal_strength=1.8)
    A.add("monolith_stone", color=(118, 120, 122), ctrl=(0, 0, 0), metal=0.0, gloss=0.20,
          px=256, tile=(2.0, 2.0), painter=_paint_monolith_stone, normal_strength=2.8)
    A.add("lamp_strip",    color=(252, 248, 232), ctrl=(0, 0, 0), metal=0.10, gloss=0.65,
          emissive=(255, 244, 212), px=128, painter=_paint_lamp_strip)
    A.add("window",        color=(74, 118, 150), ctrl=(0, 0, 0), metal=0.14, gloss=0.93,
          emissive=(255, 224, 166), px=768, painter=_paint_window_atlas)
    # 간판 4종 개별 고해상도 칸 (실사 가로세로 비율 정렬)
    A.add("sign_center_roof", color=(232, 234, 232), ctrl=(0, 0, 0), metal=0.14, gloss=0.42,
          emissive=(118, 126, 136), px=256, variants=11, painter=_paint_sign_center_roof, normal_strength=2.6)
    A.add("sign_welfare_led", color=(18, 22, 28), ctrl=(0, 0, 0), metal=0.18, gloss=0.48,
          emissive=(135, 235, 255), px=160, variants=11, painter=_paint_sign_welfare_led, normal_strength=2.4)
    A.add("sign_localfood",   color=(232, 234, 232), ctrl=(0, 0, 0), metal=0.14, gloss=0.42,
          emissive=(215, 165, 110), px=144, variants=12, painter=_paint_sign_localfood, normal_strength=2.5)
    A.add("sign_monolith",    color=(84, 54, 42), ctrl=(0, 0, 0), metal=0.34, gloss=0.40,
          emissive=(255, 242, 216), px=288, variants=2, painter=_paint_sign_monolith, normal_strength=2.4)
    return A


# ---------------------------------------------------------------------------
# 기하 헬퍼
# ---------------------------------------------------------------------------

def _sign_uv(A, sign_key, margin_px=1.5):
    A.layout()
    x, y, w, h = A.cells[sign_key]["rect"]
    aw = _SIGN_ACTIVE_W.get(sign_key, w)
    S = float(A.size)
    u0 = (x + margin_px) / S
    u1 = (x + aw - margin_px) / S
    v0 = 1.0 - (y + h - margin_px) / S
    v1 = 1.0 - (y + margin_px) / S
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def _sign_quad(mb, A, pts, sign_key):
    mb.quad(pts, _sign_uv(A, sign_key), sign_key)


def _closed_quad_prism(mb, p0, p1, p2, p3, dz, region, skip_bottom=False, tiled=True):
    """수평/경사 사각형(p0..p3, 바닥 CCW)에서 위(+Z)로 dz만큼 돌출한 닫힌 6면체."""
    b0, b1, b2, b3 = p0, p1, p2, p3
    t0 = (p0[0], p0[1], p0[2] + dz)
    t1 = (p1[0], p1[1], p1[2] + dz)
    t2 = (p2[0], p2[1], p2[2] + dz)
    t3 = (p3[0], p3[1], p3[2] + dz)
    emit = (lambda pts: mb.rect(pts, region)) if tiled else (lambda pts: mb.quad(pts, mb.atlas.uv(region), region))
    emit([t0, t1, t2, t3])                # top (+Z)
    if not skip_bottom:
        emit([b3, b2, b1, b0])            # bottom (-Z)
    emit([b0, b1, t1, t0])                # edge 0-1
    emit([b1, b2, t2, t1])                # edge 1-2
    emit([b2, b3, t3, t2])                # edge 2-3
    emit([b3, b0, t0, t3])                # edge 3-0


def _glass_railing_run(mb, gls, axis, c, s, a0, a1, z_base, h=1.08, stage=0):
    """유리 난간 + 상단 스테인리스 손스침 + 기둥 포스트 (지주 간격 ~1.8m)."""
    if stage >= 2:
        return
    # 상단 핸드레일 (닫힌 바)
    K.axbox(mb, axis, c, s, a0, a1, 0.01, 0.08, z_base + h - 0.06, z_base + h, "railing_steel")
    # 유리 패널 (Gls 메시, 양면이 아니므로 바깥/안쪽 약 1cm 분리된 한 면 또는 gls)
    if gls is not None and stage == 0:
        gls.rect(K.face_pts(axis, c + s * 0.045, s, a0, a1, z_base + 0.06, z_base + h - 0.06), "glass_rail")
        # 안쪽에서도 보이게 1cm 뒤로 반대면 추가 (두께 확보)
        gls.rect(K.face_pts(axis, c + s * 0.030, -s, a0, a1, z_base + 0.06, z_base + h - 0.06), "glass_rail")
    if stage == 0:
        span = a1 - a0
        n_posts = max(2, int(round(span / 1.80)) + 1)
        for i in range(n_posts):
            ap = a0 + span * i / max(1, n_posts - 1)
            K.axbox(mb, axis, c, s, max(a0, ap - 0.025), min(a1, ap + 0.025),
                    0.01, 0.075, z_base, z_base + h - 0.06, "railing_steel")


def _pipe_railing_run(mb, axis, c, s, a0, a1, z_base, h=1.08, stage=0):
    """개방형 3단 파이프 금속 난간 (나루마당 및 외부 계단/램프용)."""
    if stage >= 2:
        return
    top_z0, top_z1 = z_base + h - 0.08, z_base + h - 0.03
    for rz0, rz1 in ((top_z0, top_z1), (z_base + h * 0.60, z_base + h * 0.65), (z_base + h * 0.30, z_base + h * 0.35)):
        if stage == 1 and rz0 < top_z0 - 0.05:
            continue
        K.axbox(mb, axis, c, s, a0, a1, 0.01, 0.07, rz0, rz1, "railing_steel")
    span = a1 - a0
    n_posts = max(2, int(round(span / 1.80)) + 1)
    for i in range(n_posts):
        ap = a0 + 0.08 + max(0.0, span - 0.16) * i / max(1, n_posts - 1)
        K.axbox(mb, axis, c, s, ap - 0.025, ap + 0.025, 0.015, 0.065, z_base, top_z0, "railing_steel")


def _add_window_bay(mb, wins, axis, c, s, a0, a1, z0, z1, floor, unit, stage=0, frame_t=0.055):
    """프레임이 창을 가리지 않도록 창 영역을 프레임 안쪽으로 정확히 맞추어 WindowSet 등록."""
    fa0, fa1 = a0 + frame_t, a1 - frame_t
    fz0, fz1 = z0 + frame_t, z1 - frame_t
    if fa1 <= fa0 + 0.08 or fz1 <= fz0 + 0.08:
        return
    wins.add_face(axis, c, s, fa0, fa1, fz0, fz1, floor=floor, unit=unit)
    if stage == 0:
        K.axbox(mb, axis, c, s, a0, a1, 0.0, 0.06, z0, fz0, "frame_metal")
        K.axbox(mb, axis, c, s, a0, a1, 0.0, 0.06, fz1, z1, "frame_metal")
        K.axbox(mb, axis, c, s, a0, fa0, 0.0, 0.06, fz0, fz1, "frame_metal")
        K.axbox(mb, axis, c, s, fa1, a1, 0.0, 0.06, fz0, fz1, "frame_metal")


RAMP_X0, RAMP_X1 = -18.8, 24.8
RAMP_XK = 14.4                  # 경사 끝 → 로컬푸드직매장 위 수평 띠 (south_se_entrance: 행정복지 LED 우측 기둥에서 수평 전환)
RAMP_DZ = 0.85


def _ramp_yf(x):
    t = (x - RAMP_X0) / (RAMP_X1 - RAMP_X0)
    return 10.05 - 3.35 * t


def _ramp_zb(x):
    t = min(1.0, (x - RAMP_X0) / (RAMP_XK - RAMP_X0))
    return 8.30 - 4.30 * t


def _ramp_zt(x):
    return _ramp_zb(x) + RAMP_DZ


def _ramp_x_at_zt(z):
    return RAMP_X0 + (RAMP_XK - RAMP_X0) * (8.30 + RAMP_DZ - z) / 4.30


def _sloped_y_bar(mb, x0, x1, y0, y1, zb0, zb1, zt0, zt1, region):
    """X축을 따라 양 끝 Z가 경사진 닫힌 프레임 바 (사선 램프 상단 커튼월 실용)."""
    if x1 - x0 < 1e-5 or y1 - y0 < 1e-5:
        return
    b00, b10 = (x0, y0, zb0), (x1, y0, zb1)
    b01, b11 = (x0, y1, zb0), (x1, y1, zb1)
    t00, t10 = (x0, y0, zt0), (x1, y0, zt1)
    t01, t11 = (x0, y1, zt0), (x1, y1, zt1)
    mb.rect([b00, b10, t10, t00], region)  # front (-Y)
    mb.rect([b11, b01, t01, t11], region)  # back (+Y)
    mb.rect([t00, t10, t11, t01], region)  # top (+Z)
    mb.rect([b01, b11, b10, b00], region)  # bottom (-Z)
    mb.rect([b01, b00, t00, t01], region)  # left (-X)
    mb.rect([b10, b11, t11, t10], region)  # right (+X)


def _spandrel_tile_uv(A, w_m, h_lo_m, h_hi_m, h_top_m):
    """spandrel_dark 타일 셀 안 비례 UV (사선 하단 클립 사다리꼴/삼각형용)."""
    tw, th = A.tile_size("spandrel_dark")
    u0, v0, u1, v1 = A._uvrect("spandrel_dark")
    e = 0.5 / A.size
    du, dv = (u1 - u0 - 2 * e), (v1 - v0 - 2 * e)
    fu = min(1.0, max(0.01, w_m / tw))
    fv_lo = max(0.0, min(1.0, h_lo_m / th))
    fv_hi = max(0.0, min(1.0, h_hi_m / th))
    fv_top = max(0.0, min(1.0, h_top_m / th))
    U = lambda f: u0 + e + du * f
    V = lambda f: v0 + e + dv * f
    return U, V, fu, fv_lo, fv_hi, fv_top


def _curtain_wall_grid(mb, wins, axis, c, s, a0, a1, z0, z1, nx, nz, floor0, unit0,
                       stage=0, louver_step=1, louver_depth=0.28, spandrel_rows=(),
                       mullion=(0.065, 0.11), transom=(0.06, 0.08),
                       frame_region="frame_metal", ends=(True, True), z_bot_fn=None):
    """모듈 격자형 커튼월 + 수평 차양 루버 핀 (멀리언/트랜섬 비겹침·사선 램프 하단 클리핑 지원)."""
    w = (a1 - a0) / nx
    h = (z1 - z0) / nz
    mw, md = mullion
    th, td = transom

    mulls = []
    for ix in range(nx + 1):
        ax = a0 + ix * w
        if ix == 0:
            mulls.append((a0, a0 + mw) if ends[0] else None)
        elif ix == nx:
            mulls.append((a1 - mw, a1) if ends[1] else None)
        else:
            mulls.append((ax - mw * 0.5, ax + mw * 0.5))

    inners = [
        (mulls[ix][1] if mulls[ix] else a0, mulls[ix + 1][0] if mulls[ix + 1] else a1)
        for ix in range(nx)
    ]

    if stage == 0:
        for m in mulls:
            if m:
                mz0 = z0
                if z_bot_fn is not None:
                    mz0 = max(z0, min(z_bot_fn(m[0]), z_bot_fn(m[1])) - 0.04)
                if z1 > mz0 + 0.02:
                    K.axbox(mb, axis, c, s, m[0], m[1], 0.0, md, mz0, z1, frame_region)
        if z_bot_fn is not None and axis == "y":
            for lo, hi in inners:
                r_lo, r_hi = z_bot_fn(lo), z_bot_fn(hi)
                if r_lo > z0 + 0.005:
                    y_f = c + s * (td - 0.002)
                    y_b = c + s * 0.004
                    _sloped_y_bar(mb, lo - 0.004, hi + 0.004, min(y_f, y_b), max(y_f, y_b),
                                  r_lo - 0.02, r_hi - 0.02, r_lo + th, r_hi + th, frame_region)

    for iz in range(nz):
        zb, zt = z0 + iz * h, z0 + (iz + 1) * h
        if stage == 0:
            # 가로 트랜섬은 반드시 멀리언 사이(lo..hi)에만 배치 -> 멀리언과 겹침 0!
            for lo, hi in inners:
                if z_bot_fn is None:
                    K.axbox(mb, axis, c, s, lo, hi, 0.0, td, zb, zb + th, frame_region)
                else:
                    r_lo, r_hi = z_bot_fn(lo), z_bot_fn(hi)
                    if zb >= r_lo - 0.01:
                        K.axbox(mb, axis, c, s, lo, hi, 0.0, td, zb, zb + th, frame_region)
                    elif zb + th > r_hi + 0.01:
                        t_hit = (r_lo - zb) / max(1e-6, r_lo - r_hi)
                        x_hit = lo + (hi - lo) * max(0.0, min(1.0, t_hit))
                        if hi - x_hit > 0.03:
                            K.axbox(mb, axis, c, s, x_hit, hi, 0.0, td, zb, zb + th, frame_region)
                if iz == nz - 1:
                    K.axbox(mb, axis, c, s, lo, hi, 0.0, td, zt - th, zt, frame_region)
            # 수평 돌출 차양 루버 핀은 멀리언 앞(md+0.005)에서 시작해 바깥으로 돌출 -> 겹침 0!
            if louver_step > 0 and (iz % louver_step == 0) and iz > 0:
                K.axbox(mb, axis, c, s, a0, a1, md + 0.005, max(md + 0.08, louver_depth),
                        zb - 0.048, zb + 0.048, "louver_white")

        gz0 = zb + th + 0.015
        gz1 = zt - (th + 0.015 if iz == nz - 1 else 0.015)
        if gz1 <= gz0 + 0.12:
            continue
        is_spandrel = (iz in spandrel_rows)
        for ix, (lo, hi) in enumerate(inners):
            ga0, ga1 = lo + 0.012, hi - 0.012
            if ga1 <= ga0 + 0.12:
                continue
            if z_bot_fn is not None and axis == "y" and s < 0:
                rga, rgb = z_bot_fn(ga0), z_bot_fn(ga1)
                sa = (rga + th - 0.005) if rga > z0 + 0.005 else gz0
                sb = (rgb + th - 0.005) if rgb > z0 + 0.005 else gz0
                if gz1 <= sb + 0.01:
                    continue
                if gz0 < sa - 0.005:
                    y_sp = c + s * K.PAINT_OFF
                    xa = ga0 if sa <= gz1 else ga0 + (ga1 - ga0) * ((sa - gz1) / max(1e-6, sa - sb))
                    za_lo = min(gz1, max(gz0, sa))
                    if ga1 - xa < 0.02:
                        continue
                    A = mb.atlas
                    if sb >= gz0 - 0.005:
                        zb_lo = max(gz0, sb)
                        U, V, fu, fv_a, fv_b, fv_t = _spandrel_tile_uv(A, ga1 - xa, za_lo - zb, zb_lo - zb, gz1 - zb)
                        if za_lo >= gz1 - 0.002:
                            mb.tri([(ga1, y_sp, zb_lo), (ga1, y_sp, gz1), (xa, y_sp, gz1)],
                                   [(U(fu), V(fv_b)), (U(fu), V(fv_t)), (U(0.0), V(fv_t))], "spandrel_dark")
                        else:
                            mb.quad([(xa, y_sp, za_lo), (ga1, y_sp, zb_lo), (ga1, y_sp, gz1), (xa, y_sp, gz1)],
                                    [(U(0.0), V(fv_a)), (U(fu), V(fv_b)), (U(fu), V(fv_t)), (U(0.0), V(fv_t))], "spandrel_dark")
                    else:
                        xm = ga0 + (ga1 - ga0) * ((sa - gz0) / max(1e-6, sa - sb))
                        if xm - xa >= 0.02:
                            U, V, fu, fv_a, fv_b, fv_t = _spandrel_tile_uv(A, xm - xa, za_lo - zb, gz0 - zb, gz1 - zb)
                            if za_lo >= gz1 - 0.002:
                                mb.tri([(xm, y_sp, gz0), (xm, y_sp, gz1), (xa, y_sp, gz1)],
                                       [(U(fu), V(fv_b)), (U(fu), V(fv_t)), (U(0.0), V(fv_t))], "spandrel_dark")
                            else:
                                mb.quad([(xa, y_sp, za_lo), (xm, y_sp, gz0), (xm, y_sp, gz1), (xa, y_sp, gz1)],
                                        [(U(0.0), V(fv_a)), (U(fu), V(fv_b)), (U(fu), V(fv_t)), (U(0.0), V(fv_t))], "spandrel_dark")
                        if ga1 - xm >= 0.12:
                            K.paint(mb, axis, c, s, xm, ga1, gz0, gz1, "spandrel_dark", layer=1)
                    continue
            if is_spandrel:
                K.paint(mb, axis, c, s, ga0, ga1, gz0, gz1, "spandrel_dark", layer=1)
            else:
                fl = floor0 + (iz * 3) // max(1, nz)
                wins.add_face(axis, c, s, ga0, ga1, gz0, gz1, floor=fl, unit=unit0 + ix)


def _rect_var(mb, pts, region, variant=0):
    """MeshBuilder.rect 와 동일한 타일 분할을 수행하되 변형 번호(variant)를 가로·세로(X/Z)로 교차 배정."""
    A = mb.atlas
    if A is not None and A.is_tiled(region) and mb.split_tiles:
        (p0x, p0y, p0z), (p1x, p1y, p1z), _p2, (p3x, p3y, p3z) = pts
        dx, dy, dz = p1x - p0x, p1y - p0y, p1z - p0z
        W = (dx * dx + dy * dy + dz * dz) ** 0.5
        gx, gy, gz = p3x - p0x, p3y - p0y, p3z - p0z
        H = (gx * gx + gy * gy + gz * gz) ** 0.5
        if W < 1e-6 or H < 1e-6:
            return
        tw, th = A.tile_size(region)
        ex, ey, ez = dx / W, dy / W, dz / W
        fx, fy, fz = gx / H, gy / H, gz / H
        nx, ny = max(1, math.ceil(W / tw - 1e-6)), max(1, math.ceil(H / th - 1e-6))
        for j in range(ny):
            b0 = j * th
            b1 = H if j == ny - 1 else (j + 1) * th
            bx0, by0, bz0 = fx * b0, fy * b0, fz * b0
            bx1, by1, bz1 = fx * b1, fy * b1, fz * b1
            for i in range(nx):
                a0 = i * tw
                a1 = W if i == nx - 1 else (i + 1) * tw
                ax0, ay0, az0 = ex * a0, ey * a0, ez * a0
                ax1, ay1, az1 = ex * a1, ey * a1, ez * a1
                q = [(p0x + ax0 + bx0, p0y + ay0 + by0, p0z + az0 + bz0),
                     (p0x + ax1 + bx0, p0y + ay1 + by0, p0z + az1 + bz0),
                     (p0x + ax1 + bx1, p0y + ay1 + by1, p0z + az1 + bz1),
                     (p0x + ax0 + bx1, p0y + ay0 + by1, p0z + az0 + bz1)]
                mb.quad(q, A.uv_tile(region, a1 - a0, b1 - b0, variant=(variant + i * 7 + j * 5)), region)
    else:
        mb.rect(pts, region)


def _box_var(mb, x0, x1, y0, y1, z0, z1, region, variant=0, skip=()):
    """MeshBuilder.box 와 동일한 기하를 유지하면서 조각별 변형(variant) 오프셋을 적용."""
    if x1 - x0 < 1e-5 or y1 - y0 < 1e-5 or z1 - z0 < 1e-5:
        return
    F = {
        "front": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
        "back": [(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)],
        "left": [(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)],
        "right": [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
        "top": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        "bottom": [(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)],
    }
    for f_idx, (face, pts) in enumerate(F.items()):
        if face in skip:
            continue
        reg = region if isinstance(region, str) else region.get(face, region.get("default"))
        if reg:
            _rect_var(mb, pts, reg, variant=variant + f_idx)


def _segmented_ramp_slab(mb, x0, x1, yf0, yf1, y_back, zb0, zb1, dz, region, n_seg=11):
    """사선 램프 프리즘을 n_seg개 직교 근사/평면 분할로 생성해 _tiled 오버슈트 없이 256 px/m 텍셀·변형 교차 확보."""
    # 경사 구간(x0..RAMP_XK)과 수평 구간(RAMP_XK..x1)을 꺾임점에서 나눠 분할 (zb는 _ramp_zb 를 따름)
    n_flat = 3 if n_seg > 3 else 1
    n_slope = max(1, n_seg - n_flat)
    xs = [x0 + (RAMP_XK - x0) * k / n_slope for k in range(n_slope)] + \
         [RAMP_XK + (x1 - RAMP_XK) * k / n_flat for k in range(n_flat + 1)]
    n_seg = len(xs) - 1
    for i in range(n_seg):
        xa, xb = xs[i], xs[i + 1]
        t0, t1 = (xa - x0) / (x1 - x0), (xb - x0) / (x1 - x0)
        yfa, yfb = yf0 + (yf1 - yf0) * t0, yf0 + (yf1 - yf0) * t1
        zba, zbb = _ramp_zb(xa), _ramp_zb(xb)
        p0, p1 = (xa, yfa, zba), (xb, yfb, zbb)
        p2, p3 = (xb, y_back, zbb), (xa, y_back, zba)
        b0, b1, b2, b3 = p0, p1, p2, p3
        t_0 = (p0[0], p0[1], p0[2] + dz)
        t_1 = (p1[0], p1[1], p1[2] + dz)
        t_2 = (p2[0], p2[1], p2[2] + dz)
        t_3 = (p3[0], p3[1], p3[2] + dz)
        uv_f = mb.atlas.uv_tile(region, min(4.0, math.hypot(xb - xa, yfb - yfa)), dz, variant=i) if mb.split_tiles else mb.atlas.uv(region)
        uv_top = mb.atlas.uv_tile(region, min(4.0, xb - xa), min(4.0, y_back - min(yfa, yfb)), variant=i + 1) if mb.split_tiles else mb.atlas.uv(region)
        mb.quad([t_0, t_1, t_2, t_3], uv_top, region)
        mb.quad([b3, b2, b1, b0], uv_top, region)
        mb.quad([b0, b1, t_1, t_0], uv_f, region)
        mb.quad([b2, b3, t_3, t_2], uv_f, region)
        if i == 0:
            mb.quad([b3, b0, t_0, t_3], uv_f, region)
        if i == n_seg - 1:
            mb.quad([b1, b2, t_2, t_1], uv_f, region)


def _cheek_wall_segment(mb, x0, x1, y0, y1, zb0, zb1, zt0, zt1, region, skip_bottom=False, variant_base=0):
    """Y축을 따라 수직 단면이 사다리꼴인 닫힌 프리즘 (동측 계단 솔리드 측벽·경사 밑면 단차용)."""
    if x1 - x0 < 1e-5 or y1 - y0 < 1e-5:
        return
    reg_fn = (lambda face: region if isinstance(region, str) else region.get(face, region.get("default")))
    n_sub = max(1, math.ceil((y1 - y0) / 2.5)) if mb.split_tiles else 1
    for k in range(n_sub):
        t0, t1 = k / n_sub, (k + 1) / n_sub
        ya = y0 + (y1 - y0) * t0
        yb = y0 + (y1 - y0) * t1
        zba = zb0 + (zb1 - zb0) * t0
        zbb = zb0 + (zb1 - zb0) * t1
        zta = zt0 + (zt1 - zt0) * t0
        ztb = zt0 + (zt1 - zt0) * t1
        b00, b10 = (x0, ya, zba), (x1, ya, zba)
        b01, b11 = (x0, yb, zbb), (x1, yb, zbb)
        t00, t10 = (x0, ya, zta), (x1, ya, zta)
        t01, t11 = (x0, yb, ztb), (x1, yb, ztb)

        dy = yb - ya
        z_ref = min(zba, zbb)
        h_span = max(0.05, max(zta, ztb) - z_ref)
        v_idx = variant_base + k

        def _emit_side(pts, r, y_start, v_off=0):
            A = mb.atlas
            if mb.split_tiles and A is not None and A.is_tiled(r):
                tw, th = A.cells[r]["tile"]
                if h_span <= th + 1e-4 and dy <= tw + 1e-4:
                    e = 0.5 / A.size
                    u0, v0, u1, v1 = A._uvrect(r, variant=v_idx + v_off)
                    du, dv = (u1 - u0 - 2 * e), (v1 - v0 - 2 * e)
                    uvs = [
                        (u0 + e + du * min(1.0, abs(p[1] - y_start) / tw),
                         v0 + e + dv * min(1.0, max(0.0, (p[2] - z_ref) / th)))
                        for p in pts
                    ]
                    mb.quad(pts, uvs, r)
                    return
                mb.quad(pts, A.uv_tile(r, min(4.0, dy), min(4.0, h_span), variant=v_idx + v_off), r)
            else:
                mb.quad(pts, A.uv(r) if A is not None else [(0, 0), (1, 0), (1, 1), (0, 1)], r)

        if reg_fn("right"):
            _emit_side([b10, b11, t11, t10], reg_fn("right"), ya, 0)
        if reg_fn("left"):
            _emit_side([b01, b00, t00, t01], reg_fn("left"), yb, 1)
        if reg_fn("top"):
            _rect_var(mb, [t00, t10, t11, t01], reg_fn("top"), variant=v_idx)
        if not skip_bottom and reg_fn("bottom"):
            _rect_var(mb, [b01, b11, b10, b00], reg_fn("bottom"), variant=v_idx)
        if k == 0 and reg_fn("front"):
            _rect_var(mb, [b00, b10, t10, t00], reg_fn("front"), variant=v_idx)
        if k == n_sub - 1 and reg_fn("back"):
            _rect_var(mb, [b11, b01, t01, t11], reg_fn("back"), variant=v_idx)


def _sloped_pipe_railing(mb, x_c, pts_yz, h=0.92, stage=0):
    """수평·경사 구간이 이어진 3단 스테인리스 파이프 난간 (LOD1에서는 최상단 바만 유지)."""
    if stage >= 2 or len(pts_yz) < 2:
        return
    bar_offsets = (h - 0.05,) if stage == 1 else (h - 0.05, h * 0.60, h * 0.28)
    for idx in range(len(pts_yz) - 1):
        y0, z0 = pts_yz[idx]
        y1, z1 = pts_yz[idx + 1]
        if y1 <= y0 + 1e-4:
            continue
        for off in bar_offsets:
            _cheek_wall_segment(mb, x_c - 0.030, x_c + 0.030, y0, y1,
                                z0 + off, z1 + off, z0 + off + 0.045, z1 + off + 0.045,
                                "railing_steel")
        if stage == 0:
            seg_len = math.hypot(y1 - y0, z1 - z0)
            n_posts = max(2, int(round(seg_len / 1.15)) + 1)
            for p in range(n_posts):
                if idx > 0 and p == 0:
                    continue
                t = p / max(1, n_posts - 1)
                yp = y0 + (y1 - y0) * t
                zp = z0 + (z1 - z0) * t
                mb.box(x_c - 0.022, x_c + 0.022, yp - 0.022, yp + 0.022,
                       zp, zp + h - 0.05, "railing_steel")


def build_east_stair_and_terrace(mb, stage):
    """동측 2층 데크 · 솔리드 측벽 외부 계단(1층 필로티 통과) · 북동 하부 8단 조경 계단."""
    if stage >= 2:
        return

    step_mat = {"top": "stair_stone", "back": "stair_stone", "default": "white_panel"}
    deck_mat = {"top": "stair_stone", "default": "white_panel"}

    # 1. 동측 2층 데크 (Y=35.2..51.8, X=24.80..26.68, Z=4.05..4.75) + 외측 두꺼운 백색 측벽/파시아 (X=26.68..27.00)
    _box_var(mb, 24.80, 26.68, 35.20, 51.80, 4.05, 4.75, deck_mat, variant=0)
    _box_var(mb, 26.68, 27.00, 35.20, 51.80, 4.05, 4.85, "white_panel", variant=1)
    # 1b. 남측 날개 동면(X=24.4)을 따라 남동 모서리(Y=10.2)까지 연속 (sat_vworld_z19 동측 띠 · east_front_mid 2층 흰 띠)
    _box_var(mb, 24.40, 26.68, 10.20, 35.20, 4.05, 4.75, deck_mat, variant=1)
    _box_var(mb, 26.68, 27.00, 6.70, 35.20, 4.05, 4.85, "white_panel", variant=2)
    # 1c. 남동 모서리: 남측 경사로 수평 구간 끝(X=24.8, 로컬푸드직매장 상부 띠)과 동측 데크를 이음
    _box_var(mb, 24.80, 26.68, 7.02, 10.20, 4.05, 4.75, deck_mat, variant=2, skip=("left",))
    _box_var(mb, 24.80, 26.68, 6.70, 7.02, 4.05, 4.85, "white_panel", variant=0, skip=("left",))

    # 2. 계단 동선 본체 (Y=51.8..66.1, 3개 경사 구간 + 2개 중간 참; Y<=58.6 구간은 하부 1층 필로티 개방)
    flights = (
        (51.80, 54.40, 4.75, 3.85, 4.05, 3.15, 6),   # 1구간 (6단, 하부 오픈 필로티)
        (56.40, 60.80, 3.85, 2.35, 3.15, 1.65, 10),  # 2구간 (10단, Y=58.6부터 하부 솔리드)
        (63.00, 66.10, 2.35, 1.34, 0.14, 0.14, 7),   # 3구간 (7단, 하부 솔리드)
    )
    if stage == 0:
        # 1참 (Y=54.4..56.4, 필로티 상부 슬래브) & 2참 (Y=60.8..63.0, 하부 솔리드)
        _box_var(mb, 24.80, 26.68, 54.40, 56.40, 3.15, 3.85, deck_mat, variant=0)
        _box_var(mb, 24.80, 26.68, 60.80, 63.00, 0.14, 2.35, deck_mat, variant=2, skip=("bottom",))
        for y0, y1, zt0, zt1, zb0, zb1, n_st in flights:
            for i in range(n_st):
                t0, t1 = i / n_st, (i + 1) / n_st
                sy0 = y0 + (y1 - y0) * t0
                sy1 = y0 + (y1 - y0) * t1
                sz_top = zt0 + (zt1 - zt0) * t1
                y_mid = 0.5 * (sy0 + sy1)
                if y_mid <= 58.60:
                    s_b0 = zb0 + (zb1 - zb0) * t0
                    s_b1 = zb0 + (zb1 - zb0) * t1
                    _cheek_wall_segment(mb, 24.80, 26.68, sy0, sy1, s_b0, s_b1, sz_top, sz_top, step_mat, variant_base=i)
                else:
                    _box_var(mb, 24.80, 26.68, sy0, sy1, 0.14, sz_top, step_mat, variant=i, skip=("bottom",))
    else:
        # LOD1 간략 계단 매스
        _cheek_wall_segment(mb, 24.80, 26.68, 51.80, 58.60, 4.05, 2.40, 4.75, 3.10, deck_mat, variant_base=0)
        _cheek_wall_segment(mb, 24.80, 26.68, 58.60, 66.10, 0.14, 0.14, 3.10, 1.34, deck_mat, skip_bottom=True, variant_base=1)

    # 3. 하부 넓은 테라스 (Z=1.34) 및 북동 모서리 8단 넓은 조경 계단 (X=20.55..26.68, Y=69.72..71.40)
    _box_var(mb, 24.80, 26.68, 66.10, 69.20, 0.14, 1.34, deck_mat, variant=1, skip=("bottom",))
    _box_var(mb, 20.55, 26.68, 69.20, 69.72, 0.14, 1.34, deck_mat, variant=2, skip=("bottom",))
    if stage == 0:
        for k in range(7):
            sy0 = 69.72 + k * 0.24
            sy1 = 69.72 + (k + 1) * 0.24
            sz_top = 1.34 - (k + 1) * 0.15
            _box_var(mb, 20.55, 26.68, sy0, sy1, 0.14, sz_top, step_mat, variant=k, skip=("bottom",))
    else:
        _cheek_wall_segment(mb, 20.55, 26.68, 69.72, 71.40, 0.14, 0.14, 1.34, 0.29, deck_mat, skip_bottom=True, variant_base=2)

    # 조경 계단 서측 단부 옹벽 측벽 (X=20.25..20.55, north_front_mid.png 좌측 정합)
    _box_var(mb, 20.25, 20.55, 69.20, 69.72, 0.14, 1.34, "white_panel", variant=1, skip=("bottom",))
    _cheek_wall_segment(mb, 20.25, 20.55, 69.72, 71.40, 0.14, 0.14, 1.34, 0.35, "white_panel", skip_bottom=True, variant_base=2)

    # 4. 동측 외곽 솔리드 백색 측벽 (X=26.68..27.00, Y=51.8..71.40; Y<=58.6 필로티 상부, Y>=58.6 바닥 접지)
    cheek_segs = (
        (51.80, 54.40, 4.05, 3.15, 4.85, 4.15, False),
        (54.40, 56.40, 3.15, 3.15, 4.15, 4.15, False),
        (56.40, 58.60, 3.15, 2.38, 4.15, 3.40, False),
        (58.60, 60.80, 0.14, 0.14, 3.40, 2.65, True),
        (60.80, 63.00, 0.14, 0.14, 2.65, 2.65, True),
        (63.00, 66.10, 0.14, 0.14, 2.65, 1.64, True),
        (66.10, 69.72, 0.14, 0.14, 1.64, 1.64, True),
        (69.72, 71.40, 0.14, 0.14, 1.64, 0.48, True),
    )
    for idx, (y0, y1, zb0, zb1, zt0, zt1, on_ground) in enumerate(cheek_segs):
        _cheek_wall_segment(mb, 26.68, 27.00, y0, y1, zb0, zb1, zt0, zt1, "white_panel", skip_bottom=on_ground, variant_base=idx)

    # 5. 외측·내측 금속 난간 및 북동 테라스 U형 가드레일·필로티 하부 안전펜스
    outer_rail_pts = (
        (6.80, 4.85), (51.80, 4.85), (54.40, 4.15), (56.40, 4.15),
        (60.80, 2.65), (63.00, 2.65), (66.10, 1.64), (69.72, 1.64), (71.36, 0.48),
    )
    _pipe_railing_run(mb, "y", 6.80, 1, 24.80, 26.80, 4.85, h=1.02, stage=stage)
    _sloped_pipe_railing(mb, 26.84, outer_rail_pts, h=0.92, stage=stage)
    if stage == 0:
        inner_rail_pts = (
            (51.80, 4.75), (54.40, 3.85), (56.40, 3.85),
            (60.80, 2.35), (63.00, 2.35), (66.10, 1.34),
        )
        _sloped_pipe_railing(mb, 24.90, inner_rail_pts, h=0.88, stage=0)
        # 북면 1층 테라스 위 U형 스테인리스 루프 레일 2개소 (슬릿창 X=21.0..21.95 비차단)
        for ux0, ux1 in ((22.30, 23.20), (23.50, 24.40)):
            mb.box(ux0, ux0 + 0.05, 69.46, 69.51, 1.34, 1.88, "railing_steel", skip=("bottom",))
            mb.box(ux1 - 0.05, ux1, 69.46, 69.51, 1.34, 1.88, "railing_steel", skip=("bottom",))
            mb.box(ux0, ux1, 69.46, 69.51, 1.88, 1.93, "railing_steel")
        # 계단 경사 하부 저높이 필로티 출입방지 펜스 (Y=55.4..58.5)
        _pipe_railing_run(mb, "x", 26.55, 1, 55.40, 58.50, 0.14, h=0.88, stage=0)


# ---------------------------------------------------------------------------
# 건물 구역별 빌더
# ---------------------------------------------------------------------------

def build_plaza_and_site(mb, A, wins, stage):
    """1. 대지 바닥 보도 광장 · 남서 외부 계단/접근로 · 전면 석봉복합문화센터 표지석."""
    # 직교 주 광장 포장 (Y in [6.2, 70.2], Z = 0.00..0.14)
    mb.box(-25.5, 25.5, 6.2, 70.2, 0.0, 0.14, "plaza_paving", skip=("bottom",))
    if stage < 2:
        # 동측 외부 계단 및 북동 조경 계단 하부 보도 포장 (Z=0.00..0.14)
        mb.box(25.5, 27.0, 10.2, 70.2, 0.0, 0.14, "plaza_paving", skip=("bottom",))
        mb.box(20.0, 27.0, 70.2, 71.4, 0.0, 0.14, "plaza_paving", skip=("bottom",))
    # 전면 남측 대덕대로변 사선 쐐기 보행광장 (Y: 서 0.0 -> 동 6.2, 직교 계단식 스트립 분할로 타일 오버슈트 방지)
    n_plaza = 20 if stage < 2 else 4
    for i in range(n_plaza):
        t0, t1 = i / n_plaza, (i + 1) / n_plaza
        px0, px1 = -25.5 + 51.0 * t0, -25.5 + 51.0 * t1
        py0 = 6.2 * (t0 + t1) * 0.5
        if py0 < 6.18:
            mb.box(px0, px1, py0, 6.2, 0.0, 0.14, "plaza_paving", skip=("bottom", "back"))

    if stage >= 2:
        return

    # 남서측 개방형 계단 및 접근 테라스 (하부 오픈형 경사 계단 + 측벽 스트링거, south_front_mid.png 좌측)
    if stage == 0:
        steps = 14
        y_start, y_end = 2.0, 10.2
        z_start, z_end = 0.14, 4.45
        for i in range(steps):
            t0, t1 = i / steps, (i + 1) / steps
            sy0 = y_start + (y_end - y_start) * t0
            sy1 = y_start + (y_end - y_start) * t1
            sz0 = max(0.14, z_start + (z_end - z_start) * t0 - 0.35)
            sz1 = z_start + (z_end - z_start) * t1
            _box_var(mb, -24.4, -21.0, sy0, sy1, sz0, sz1, "white_panel", variant=i, skip=(("bottom",) if sz0 <= 0.15 else ()))
        # 계단 경사 측벽 스트링거 + 2층 연결 랜딩 기둥
        _closed_quad_prism(mb, (-24.65, y_start, 0.14), (-24.40, y_start, 0.14), (-24.40, y_end, 4.10), (-24.65, y_end, 4.10), 1.05, "white_panel", tiled=False)
        _closed_quad_prism(mb, (-21.00, y_start, 0.14), (-20.75, y_start, 0.14), (-20.75, y_end, 4.10), (-21.00, y_end, 4.10), 1.05, "white_panel", tiled=False)
        _box_var(mb, -24.6, -24.1, 9.5, 10.1, 0.14, 4.10, "white_panel", variant=0, skip=("bottom",))
        _box_var(mb, -21.2, -20.7, 9.5, 10.1, 0.14, 4.10, "white_panel", variant=1, skip=("bottom",))
    else:
        for i in range(4):
            t0, t1 = i / 4.0, (i + 1) / 4.0
            sy0 = 2.0 + 8.2 * t0
            sy1 = 2.0 + 8.2 * t1
            sz0 = max(0.14, 0.14 + 4.31 * t0 - 0.50)
            sz1 = 0.14 + 4.31 * t1
            _box_var(mb, -24.6, -20.8, sy0, sy1, sz0, sz1, "white_panel", variant=i, skip=(("bottom",) if sz0 <= 0.15 else ()))

    # 전면 남동 광장 표지석 ('석봉복합문화센터', south_se_entrance.png 기준 X=+17.5, Y=5.0)
    mb.box(15.6, 19.8, 4.8, 5.4, 0.14, 0.44, "monolith_stone", skip=("bottom",))
    mb.box(16.2, 19.2, 4.92, 5.32, 0.44, 2.25, "monolith_stone", skip=("bottom",))
    if stage == 0:
        _sign_quad(mb, A, [(16.5, 4.90, 0.65), (18.9, 4.90, 0.65), (18.9, 4.90, 2.05), (16.5, 4.90, 2.05)], "sign_monolith")


def build_north_wing(mb, A, wins, gls, stage):
    """2. 북측 체육관 · 평생학습관 · 옥상 나루마당 · 경사 태양광 지붕 (Y=49.6..71.4, Z up to 21.15 m)."""
    # 북측동 수평 캔틸레버 지붕 외곽 (벽 밖 서 2.5m · 동 2.2m · 북 체육관벽 3.0m / 타워 2.2m 돌출)
    rx0, rx1 = -27.0, 27.0
    ry0, ry1 = 49.6, 71.4
    roof_mat = {"bottom": "roof_soffit", "default": "white_panel"}

    if stage == 2:
        # LOD2: 북측 후퇴면(Y=68.4, 65.4)·동북 타워(Y=69.2)·평탄 캔틸레버 지붕(X=-27..27, Y=49.6..71.4, Z=18.55..20.15) 유지 + 폐합 입체
        mb.box(-24.5, 13.5, 50.4, 68.4, 0.14, 9.10, "beige_stone", skip=("bottom",))
        mb.box(13.5, 20.5, 50.4, 65.4, 0.14, 14.80, "white_panel", skip=("bottom",))
        mb.box(20.5, 24.8, 50.4, 64.0, 0.14, 14.80, "white_panel", skip=("bottom",))
        mb.box(20.5, 24.8, 64.0, 69.2, 0.14, 18.55, "white_panel", skip=("bottom",))
        mb.box(-24.5, 13.5, 50.4, 68.4, 9.10, 14.80, "brown_panel")
        mb.box(-24.5, 13.5, 50.4, 68.4, 14.80, 18.55, "white_grooved")
        mb.box(rx0, rx1, ry0, ry1, 18.55, 20.15, roof_mat)
        return

    # 1~2층 본체 (X in [-24.5, +13.5], Y in [50.4, 68.4])
    _box_var(mb, -24.5, 13.5, 50.4, 68.4, 0.14, 9.10, "beige_stone", variant=0, skip=("bottom",))
    # 동북 커튼월 로비 후퇴부 (X in [13.5, 20.5], Y in [50.4, 65.4], 1~3층 Z in [0.14, 14.80])
    _box_var(mb, 13.5, 20.5, 50.4, 65.4, 0.14, 14.80, "white_panel", variant=0, skip=("bottom",))
    # 동북 코너 솔리드 계단/엘리베이터 타워 (X in [20.5, 24.8], Y in [64.0, 69.2], Z in [0.14, 18.55])
    _box_var(mb, 20.5, 24.8, 64.0, 69.2, 0.14, 18.55, "white_panel", variant=1, skip=("bottom",))
    # 동북 타워 남측 연속 백색 벽 (1층 Y=50.4..58.6 구간 X=22.0 회랑 필로티 후퇴 + 기둥, 2~3층 Z=4.45..14.80)
    _box_var(mb, 20.5, 22.0, 50.4, 58.6, 0.14, 4.45, "white_panel", variant=2, skip=("bottom",))
    _box_var(mb, 20.5, 24.8, 58.6, 64.0, 0.14, 4.45, "white_panel", variant=0, skip=("bottom",))
    _box_var(mb, 20.5, 24.8, 50.4, 64.0, 4.45, 14.80, "white_panel", variant=2)
    _box_var(mb, 23.9, 24.6, 51.0, 51.7, 0.14, 4.45, "white_panel", variant=1, skip=("bottom",))

    # 1~2층 북면 입면 디테일 (Y = 68.4, s = +1)
    # 1층 NW 부설입구 유리문 (X in [-24.2, -19.2], Z in [0.14, 4.10])
    _add_window_bay(mb, wins, "y", 68.4, 1, -24.0, -21.8, 0.30, 3.60, 0, 10, stage)
    _add_window_bay(mb, wins, "y", 68.4, 1, -21.6, -19.4, 0.30, 3.60, 0, 11, stage)
    # 1층 하부 알루미늄 환기 루버 4개소 (north_front_mid.png 기준)
    for lx0, lx1 in ((-18.6, -15.2), (-10.0, -5.8), (-4.0, 0.5), (5.5, 9.8)):
        K.paint(mb, "y", 68.4, 1, lx0, lx1, 0.35, 1.70, "louver_grille", layer=1)
    # 1층 세로형 창열 (north_front_mid.png 기준 12베이)
    north_1f_xs = [-17.4, -15.6, -13.8, -11.4, -9.4, -7.4, -4.6, -2.6, 0.2, 2.2, 5.4, 7.6, 10.6, 12.2]
    for idx, x0 in enumerate(north_1f_xs):
        _add_window_bay(mb, wins, "y", 68.4, 1, x0, x0 + 1.05, 2.05, 3.95, 0, 20 + idx, stage)

    # 북측 2층 & 3층 캔틸레버 발코니 슬래브 (Y in [68.4, 70.2], 깊이 1.8m -> WIN_BLOCKED 1.5m 회피!)
    mb.box(-24.5, 20.5, 68.4, 70.2, 4.35, 4.78, "white_panel")
    mb.box(-19.5, 20.5, 68.4, 70.2, 8.85, 9.28, "white_panel")
    _glass_railing_run(mb, gls, "y", 70.2, 1, -24.4, 20.4, 4.78, h=1.08, stage=stage)
    _glass_railing_run(mb, gls, "y", 70.2, 1, -19.4, 20.4, 9.28, h=1.08, stage=stage)

    # 북측 2층 세로형 창열 (Y = 68.4, Z in [5.25, 8.20]) — NW 코너까지 연속 배치 (north_nw_oblique.png 정합)
    north_2f_xs = [-23.2, -21.2, -19.2, -17.2, -15.2, -13.2, -11.0, -8.8, -6.6, -4.2, -1.8, 0.6, 3.0, 5.6, 8.0, 10.8]
    for idx, x0 in enumerate(north_2f_xs):
        _add_window_bay(mb, wins, "y", 68.4, 1, x0, x0 + 1.05, 5.35, 8.20, 1, 40 + idx, stage)

    # 북동측 후퇴 커튼월 로비 (X in [13.5, 20.5], Y = 65.4, Z in [0.20, 14.40])
    _curtain_wall_grid(mb, wins, "y", 65.4, 1, 13.6, 20.4, 0.25, 4.35, nx=4, nz=2,
                       floor0=0, unit0=70, stage=stage, louver_step=0)
    _curtain_wall_grid(mb, wins, "y", 65.4, 1, 13.6, 20.4, 4.78, 14.20, nx=4, nz=6,
                       floor0=1, unit0=75, stage=stage, louver_step=0)

    # 동북 타워 전층 연속 세로 슬릿 창 2열 (북면 Y=69.2 1x11단, 동면 X=24.8 2x9단, north_ne_oblique.png 기준)
    _curtain_wall_grid(mb, wins, "y", 69.2, 1, 21.0, 21.95, 1.55, 16.95, nx=1, nz=11,
                       floor0=0, unit0=82, stage=stage, louver_step=0,
                       mullion=(0.055, 0.085), transom=(0.055, 0.085), frame_region="curtain_frame")
    _curtain_wall_grid(mb, wins, "x", 24.8, 1, 66.1, 67.4, 3.80, 17.65, nx=2, nz=9,
                       floor0=0, unit0=83, stage=stage, louver_step=0,
                       mullion=(0.055, 0.085), transom=(0.055, 0.085), frame_region="curtain_frame")

    # 3층 다목적 체육관 복층 볼륨 (X in [-24.5, +13.5], Y in [51.0, 68.4], Z in [9.10, 18.55])
    _box_var(mb, -24.5, 13.5, 51.0, 68.4, 9.10, 14.80, "brown_panel", variant=0)
    _box_var(mb, -24.5, 13.5, 51.0, 68.4, 14.80, 18.55, "white_grooved", variant=0)
    # 3층 짙은 브라운 구간 수평 띠창 3개소 (north_front_mid.png 기준)
    for idx, (wx0, wx1) in enumerate(((-15.5, -10.5), (-6.8, -0.8), (2.5, 8.8))):
        _add_window_bay(mb, wins, "y", 68.4, 1, wx0, wx1, 10.35, 11.75, 2, 85 + idx, stage)

    # 동북 3층 옥상 나루마당 (X in [13.5, 24.8], Y in [50.4, 65.4], 바닥 Z=14.80, 두꺼운 백색 캔틸레버 지붕 Z=18.55..20.00)
    _box_var(mb, 23.85, 24.8, 50.4, 64.0, 14.80, 15.10, "white_panel", variant=0, skip=("bottom",))
    _box_var(mb, 13.5, 23.85, 50.4, 51.0, 14.80, 15.10, "white_panel", variant=1, skip=("bottom",))
    _pipe_railing_run(mb, "y", 65.4, 1, 13.6, 20.4, 14.80, h=1.08, stage=stage)
    _pipe_railing_run(mb, "x", 24.8, 1, 51.45, 57.15, 15.10, h=0.95, stage=stage)
    _pipe_railing_run(mb, "x", 24.8, 1, 58.05, 63.95, 15.10, h=0.95, stage=stage)
    # 굵은 백색 필로티 사각 기둥 2개소 + 북서 모서리 기둥 (east_front_mid.png · east_ne_oblique.png 실측)
    for idx, cy in enumerate((51.0, 57.6)):
        _box_var(mb, 23.85, 24.75, cy - 0.42, cy + 0.42, 15.10, 18.55, "white_panel", variant=idx, skip=("bottom",))
    _box_var(mb, 13.5, 14.35, 64.15, 65.0, 14.80, 18.55, "white_panel", variant=2, skip=("bottom",))
    if stage == 0:
        # 나루마당 북측 낮은 루버 스크린(Z=14.8..16.3, 상부 완전 개방) + 설비 박스
        mb.box(14.35, 20.5, 65.10, 65.30, 14.80, 16.30, "louver_grille")
        for hx in (15.5, 17.5, 19.5):
            mb.box(hx, hx + 1.2, 53.0, 54.0, 14.80, 16.05, "equipment", skip=("bottom",))

    # 북측 체육관·나루마당 통합 수평 캔틸레버 백색 지붕 슬래브 (Z=18.55..20.00, 서 2.5m·동 2.2m·북 3.0m/타워 2.2m 돌출 + 하부 soffit)
    _box_var(mb, rx0, rx1, ry0, ry1, 18.55, 20.00, roof_mat, variant=1)
    # 상부 외곽 백색 파라펫 테두리 (Z=20.00..20.32 — 측면에서 태양광 박스가 돌출되지 않게 차폐)
    parapet_t = 0.8
    _box_var(mb, rx1 - parapet_t, rx1, ry0, ry1, 20.00, 20.32, "white_panel", variant=0)
    _box_var(mb, rx0, rx1 - parapet_t, ry1 - parapet_t, ry1, 20.00, 20.32, "white_panel", variant=1)
    _box_var(mb, rx0, rx1 - parapet_t, ry0, ry0 + 0.7, 20.00, 20.32, "white_panel", variant=2)
    _box_var(mb, rx0, rx0 + parapet_t, ry0 + 0.7, ry1 - parapet_t, 20.00, 20.32, "white_panel", variant=0)
    # 중앙 옥탑 계단실 박스 + 저프로파일 태양광 어레이 (sat_vworld_z19.png 위성 배치 유지, 동측 X_max=23.6 내측 정렬)
    _box_var(mb, 7.5, 13.5, 50.6, 56.0, 20.00, 21.15, "white_panel", variant=1)
    for sx0, sx1, sy0, sy1 in ((-21.0, 7.0, 51.6, 68.8), (7.2, 23.6, 56.6, 68.8), (14.0, 23.6, 51.6, 56.4)):
        mb.box(sx0, sx1, sy0, sy1, 20.00, 20.16, "solar_pv")


def build_middle_courtyard_and_east(mb, wins, gls, stage):
    """3. 중정(아트리움) · 서측 2~3층 그린테라스(#퍼골라) · 동측 본체 및 외부 대계단 (Y=35.2..50.4)."""
    if stage == 2:
        # LOD2: 서측 테라스 기단 (X=-24.6..-6.0, Z=9.2) + 동측 연결동 (1F 회랑 포함 Z=15.5), 중앙 중정은 개방 유지!
        mb.box(-24.6, -6.0, 35.2, 50.4, 0.14, 9.20, {"top": "terrace_deck", "default": "beige_stone"}, skip=("bottom",))
        mb.box(8.2, 22.0, 35.2, 50.4, 0.14, 4.45, "white_panel", skip=("bottom",))
        mb.box(8.2, 24.8, 35.2, 50.4, 4.45, 15.50, "white_panel")
        return

    # A. 서측 1~2층 그린테라스 하부 매스 (X in [-24.6, -6.0], Y in [35.2, 50.4], Z in [0.14, 9.10])
    _box_var(mb, -24.6, -6.0, 35.2, 50.4, 0.14, 9.10, "beige_stone", variant=1, skip=("bottom",))
    # 2층 서측 테라스 옥외 데크 바닥 (Z=9.10..9.24) + 조경 화단 + 유리 난간
    _box_var(mb, -25.0, -6.0, 35.2, 50.4, 9.10, 9.26, "terrace_deck", variant=0)
    if stage == 0:
        # 서측 1~2층 연속 세로형 창 (west_nw_corner.png & north_nw_oblique.png 기준)
        for i in range(6):
            wy0 = 36.2 + i * 2.35
            _add_window_bay(mb, wins, "x", -24.6, -1, wy0, wy0 + 1.05, 1.40, 3.85, 0, 100 + i, stage)
            _add_window_bay(mb, wins, "x", -24.6, -1, wy0, wy0 + 1.05, 5.45, 8.15, 1, 110 + i, stage)
        # 2층 돌출 발코니 슬래브 & 유리 난간 (X=-25.8..-24.6 깊이 1.2m -> Z=4.4..4.8)
        # 참고: 위 1층 창(1.4..3.85)과 2층 창(5.45..8.15)은 Z구간이 달라 1.2m 난간에 가리지 않음!
        _box_var(mb, -26.2, -24.6, 35.2, 50.4, 4.40, 4.82, "white_panel", variant=2)
        _glass_railing_run(mb, gls, "x", -26.2, -1, 35.3, 50.3, 4.82, h=1.06, stage=stage)
    # 3층 레벨 서측 그린테라스 외곽 유리 난간 (Z=9.26)
    _glass_railing_run(mb, gls, "x", -25.0, -1, 35.3, 50.3, 9.26, h=1.08, stage=stage)

    # 서측 그린테라스 특징: #자형 백색 대형 퍼골라 캐노피 (sat_vworld_z19.png 실측 X in [-20.0, -9.4], Y in [37.4, 47.8])
    px0, px1 = -20.0, -9.4
    py0, py1 = 37.4, 47.8
    # 4개 교차 지점 기둥 + #자형 4본 격자 보 (Z=9.26 .. 12.10, 보 Z=12.10 .. 12.70)
    xbars = (-17.2, -12.2)
    ybars = (40.2, 45.0)
    for xb in xbars:
        for yb in ybars:
            mb.box(xb - 0.22, xb + 0.22, yb - 0.22, yb + 0.22, 9.26, 12.10, "louver_white")
    for yb in ybars:
        mb.box(px0, px1, yb - 0.45, yb + 0.45, 12.10, 12.75, "louver_white")
    for xb in xbars:
        # X방향 보와 Y방향 보가 교차점에서 COPLANAR 되지 않게 Z를 12.20..12.82로 미세 분리
        mb.box(xb - 0.45, xb + 0.45, py0, py1, 12.18, 12.82, "louver_white")
    if stage == 0:
        # 그린테라스 녹지 화단
        mb.box(-24.2, -21.0, 36.2, 49.4, 9.26, 9.65, "green_planter")
        mb.box(-9.0, -6.5, 36.2, 44.0, 9.26, 9.65, "green_planter")

    # B. 중앙 중정 (X in [-6.0, +8.2], Y in [35.2, 50.4]): 바닥 Z=0.14..0.50 + 북서 1층 연결 브리지 + 사방 유리 아트리움
    mb.box(-6.0, 8.2, 35.2, 50.4, 0.14, 0.50, "terrace_deck", skip=("bottom",))
    mb.box(-6.0, -0.5, 44.6, 50.4, 0.50, 4.70, "white_panel", skip=("bottom",))
    mb.box(-5.5, -1.0, 45.2, 49.8, 4.70, 5.05, "green_planter")
    if stage == 0:
        # 중정을 둘러싼 내부 커튼월 창 (북/남/동/서 4면 아트리움 개방감)
        _curtain_wall_grid(mb, wins, "y", 50.4, -1, -0.2, 8.0, 0.60, 14.0, nx=5, nz=6, floor0=0, unit0=130, stage=stage, louver_step=0)
        _curtain_wall_grid(mb, wins, "y", 35.2,  1, -5.5, 8.0, 0.60, 14.0, nx=8, nz=6, floor0=0, unit0=140, stage=stage, louver_step=0)
        _curtain_wall_grid(mb, wins, "x",  8.2, -1, 35.5, 50.0, 0.60, 14.0, nx=8, nz=6, floor0=0, unit0=150, stage=stage, louver_step=0)
        _curtain_wall_grid(mb, wins, "x", -6.0,  1, 35.5, 44.2, 0.60, 8.80, nx=5, nz=4, floor0=0, unit0=160, stage=stage, louver_step=0)

    # C. 동측 연결동 (X in [+8.2, +24.8], Y in [35.2, 50.4], 1층 회랑 후퇴 X=22.0 + 2~3층 백색 벽 Z=4.45..14.80)
    _box_var(mb, 8.2, 22.0, 35.2, 50.4, 0.14, 4.45, "white_panel", variant=0, skip=("bottom",))
    _box_var(mb, 8.2, 24.8, 35.2, 50.4, 4.45, 14.80, "white_panel", variant=1)
    mb.box(8.2, 24.8, 35.2, 50.4, 14.80, 14.95, "roof_concrete")
    # 동측 1층 회랑 백색 기둥 + 후퇴 창 (east_front_mid.png · east_ne_oblique.png 기준)
    for idx, cy in enumerate((40.2, 45.6)):
        _box_var(mb, 23.9, 24.6, cy - 0.32, cy + 0.32, 0.14, 4.45, "white_panel", variant=idx, skip=("bottom",))
    if stage == 0:
        for idx, (ya, yb) in enumerate(((35.8, 39.4), (41.0, 44.8), (46.2, 49.8))):
            _curtain_wall_grid(mb, wins, "x", 22.0, 1, ya, yb, 0.30, 4.20, nx=2, nz=2, floor0=0, unit0=166 + idx * 2, stage=stage, louver_step=0)
    # 동측 옥상 파라펫 테두리 (north_ne_oblique.png & sat_vworld_z19.png)
    _box_var(mb, 24.3, 24.8, 35.2, 50.4, 14.95, 15.65, "white_panel", variant=2)
    _box_var(mb, 8.2, 8.7, 35.2, 50.4, 14.95, 15.65, "white_panel", variant=0)
    build_east_stair_and_terrace(mb, stage)
    if stage == 0:
        # 동측 외벽 창호 (east_ne_far.png & north_ne_oblique.png 기준: 2층 계단실 대형창 + 3층 세로창 열)
        _curtain_wall_grid(mb, wins, "x", 24.8, 1, 45.2, 49.6, 5.10, 13.90, nx=3, nz=5, floor0=1, unit0=170, stage=stage, louver_step=0)
        for idx, y0 in enumerate((36.4, 38.6, 41.2, 43.2)):
            _add_window_bay(mb, wins, "x", 24.8, 1, y0, y0 + 1.0, 5.35, 8.15, 1, 175 + idx, stage)
            _add_window_bay(mb, wins, "x", 24.8, 1, y0, y0 + 1.0, 9.85, 13.05, 2, 180 + idx, stage)
        # 옥상 공조 설비 (X in [11..20], Y in [38..48])
        mb.box(12.0, 17.0, 38.0, 42.5, 14.95, 16.35, "equipment", skip=("bottom",))
        mb.box(18.5, 22.0, 43.0, 47.5, 14.95, 16.25, "equipment", skip=("bottom",))


def build_south_wings(mb, A, wins, gls, stage):
    """4. 남측 2~3층 연속 전면 커튼월 · 통합 두꺼운 백색 지붕 파시아 · 서측 갤러리 · 남동 태양광 (Y=10.2..35.2)."""
    if stage == 2:
        mb.box(-18.8, 3.0, 10.2, 35.2, 0.14, 14.80, "white_panel", skip=("bottom",))
        mb.box(3.0, 22.0, 10.2, 35.2, 0.14, 4.45, "white_panel", skip=("bottom",))
        mb.box(3.0, 24.4, 10.2, 35.2, 4.45, 14.80, "spandrel_dark")
        mb.box(-19.3, 25.2, 9.65, 10.75, 14.80, 16.45, "white_panel")
        mb.box(-19.3, 3.0, 10.75, 35.2, 14.80, 16.45, "white_panel")
        mb.box(3.0, 24.2, 10.75, 35.2, 14.80, 15.20, "roof_membrane")
        mb.box(24.2, 25.2, 10.75, 35.2, 14.80, 16.45, "white_panel")
        mb.box(-24.6, -18.8, 10.2, 35.2, 0.14, 9.20, {"top": "terrace_deck", "default": "beige_stone"}, skip=("bottom",))
        return

    # A. 남서 3층 백색 상자 매스 (X in [-18.8, +3.0], Y in [10.2, 35.2], Z in [0.14, 14.80]) + 상부 통합 지붕
    _box_var(mb, -18.8, 3.0, 10.2, 35.2, 0.14, 14.80, "white_panel", variant=0, skip=("bottom",))
    # 서측 처마 보 격자 (10개 천창 개구부: X in [-18.8, -16.2], Y in [10.75, 34.7])
    mb.box(-16.2, 2.5, 10.75, 34.7, 14.80, 16.05, "roof_membrane")
    mb.box(-18.2, -16.2, 10.75, 34.7, 14.80, 15.20, "roof_membrane")
    _box_var(mb, 2.5, 3.0, 10.75, 34.7, 14.80, 16.45, "white_panel", variant=1)
    _box_var(mb, -19.3, -18.2, 10.75, 35.2, 14.80, 16.45, "white_panel", variant=2)
    if stage == 0:
        for k in range(10):
            ry = 11.2 + k * 2.45
            _box_var(mb, -18.2, -16.2, ry, ry + 0.55, 15.20, 16.30, "white_panel", variant=k)

    # 서측 1~2층 연결 갤러리 (X in [-24.6, -18.8], Y in [10.2, 35.2], Z in [0.14, 9.10])
    _box_var(mb, -24.6, -18.8, 10.2, 35.2, 0.14, 9.10, "beige_stone", variant=0, skip=("bottom", "right"))
    _box_var(mb, -25.6, -24.6, 10.2, 35.2, 4.40, 4.82, "white_panel", variant=1, skip=("right",))
    mb.box(-25.0, -18.8, 10.2, 35.2, 9.10, 9.26, "terrace_deck", skip=("right",))
    _glass_railing_run(mb, gls, "x", -25.6, -1, 10.3, 35.1, 4.82, h=1.06, stage=stage)
    _glass_railing_run(mb, gls, "x", -25.0, -1, 10.3, 35.1, 9.26, h=1.08, stage=stage)
    if stage == 0:
        for i in range(9):
            wy0 = 11.5 + i * 2.50
            _add_window_bay(mb, wins, "x", -24.6, -1, wy0, wy0 + 1.05, 1.40, 3.85, 0, 200 + i, stage)
            _add_window_bay(mb, wins, "x", -24.6, -1, wy0, wy0 + 1.05, 5.45, 8.15, 1, 210 + i, stage)
        # 남서 매스 3층 수평 창 열 (south_sw_ramp.png 기준)
        _curtain_wall_grid(mb, wins, "x", -18.8, -1, 11.2, 22.8, 10.10, 14.60, nx=7, nz=3, floor0=2, unit0=225, stage=stage, louver_step=0)
        # 남서 모서리 상부 사인 (두꺼운 백색 파시아 서측면 -19.32, 외향 -X CCW 정방향)
        _sign_quad(mb, A, [(-19.32, 23.2, 15.05), (-19.32, 11.8, 15.05), (-19.32, 11.8, 16.25), (-19.32, 23.2, 16.25)], "sign_center_roof")

    # B. 남동 2~3층 커튼월 동 (X in [+3.0, +24.4], Y in [10.2, 35.2])
    # 1층부(Z=0.14..4.45): 동측 회랑 기둥 앞(X=24.0)으로부터 2.0m 후퇴(X_east=22.0) + 남면(Y=10.2) 정렬
    _box_var(mb, 3.0, 22.0, 10.2, 35.2, 0.14, 4.45, "white_panel", variant=1, skip=("bottom", "left"))
    # 2~3층 본체 (Z=4.45..14.80) + 통합 남측/동측 두꺼운 백색 오버행 지붕 파시아 (Z=14.80..16.45, height 1.65 m)
    _box_var(mb, 3.0, 24.4, 10.2, 35.2, 4.45, 14.80, "white_panel", variant=2, skip=("left",))
    _box_var(mb, -19.3, 25.2, 9.65, 10.75, 14.80, 16.45, "white_panel", variant=0)
    _box_var(mb, 24.2, 25.2, 10.75, 35.2, 14.80, 16.45, "white_panel", variant=1)
    _box_var(mb, -18.2, 24.2, 34.7, 35.2, 14.80, 16.45, "white_panel", variant=2)
    mb.box(3.0, 24.2, 10.75, 34.7, 14.80, 15.10, "roof_membrane")

    # 남동 1층 동측 회랑 기둥 (X = 23.7..24.3, 창면 X=22.0에서 1.7m>1.5m 이격 + 기둥 사이 창 배치)
    col_ys = (12.6, 18.1, 23.8, 29.4, 34.8)
    for idx, cy in enumerate(col_ys):
        _box_var(mb, 23.7, 24.3, cy - 0.30, cy + 0.30, 0.14, 4.45, "white_panel", variant=idx, skip=("bottom",))
    # 1층 동측 회랑 안쪽 창호 (X = 22.0, s = +1) — 기둥 사이 4스팬 배치
    for idx, (ya, yb) in enumerate(((13.2, 17.5), (18.7, 23.2), (24.4, 28.8), (30.0, 34.2))):
        _curtain_wall_grid(mb, wins, "x", 22.0, 1, ya, yb, 0.30, 4.20, nx=2, nz=2, floor0=0, unit0=240 + idx * 2, stage=stage, louver_step=0)

    # 남면 2~3층 연속 전면 커튼월 (X in [-18.4, +24.4], Y = 10.2, s = -1, Z_top=14.72 통합 정렬)
    # 사선 경사로 윗면(_ramp_zt)과 빈틈없이 맞물리도록 전 구간 z0=5.05, nz=9 동일 격자에서 경사로 하단 클리핑 적용
    ramp_clip_z = lambda x: max(5.05, _ramp_zt(x))
    cw_kw = dict(mullion=(0.048, 0.092), transom=(0.048, 0.072),
                 frame_region="curtain_frame", louver_step=0)
    _curtain_wall_grid(mb, wins, "y", 10.2, -1, 4.0, 14.0, 5.05, 14.72, nx=7, nz=9,
                       floor0=1, unit0=260, stage=stage, spandrel_rows=(0, 1), ends=(True, False),
                       z_bot_fn=ramp_clip_z, **cw_kw)
    _curtain_wall_grid(mb, wins, "y", 10.2, -1, 14.0, 19.7, 5.05, 14.72, nx=4, nz=9,
                       floor0=1, unit0=268, stage=stage, spandrel_rows=(0,), ends=(True, False),
                       z_bot_fn=ramp_clip_z, **cw_kw)
    _curtain_wall_grid(mb, wins, "y", 10.2, -1, 19.7, 21.15, 5.05, 14.72, nx=1, nz=9,
                       floor0=1, unit0=274, stage=stage, spandrel_rows=(0,), ends=(True, False),
                       z_bot_fn=ramp_clip_z, **cw_kw)
    _curtain_wall_grid(mb, wins, "y", 10.2, -1, 21.15, 24.4, 5.05, 14.72, nx=2, nz=9,
                       floor0=1, unit0=276, stage=stage, ends=(True, False),
                       z_bot_fn=ramp_clip_z, **cw_kw)
    _curtain_wall_grid(mb, wins, "y", 10.2, -1, -18.4, -7.2, 5.05, 14.72, nx=8, nz=9,
                       floor0=2, unit0=280, stage=stage, spandrel_rows=(3, 4), ends=(True, False),
                       z_bot_fn=ramp_clip_z, **cw_kw)
    _curtain_wall_grid(mb, wins, "y", 10.2, -1, -7.2, 4.0, 5.05, 14.72, nx=8, nz=9,
                       floor0=2, unit0=289, stage=stage, spandrel_rows=(2, 3), ends=(True, False),
                       z_bot_fn=ramp_clip_z, **cw_kw)
    _curtain_wall_grid(mb, wins, "x", 24.4, 1, 10.2, 35.2, 5.05, 14.72, nx=14, nz=9,
                       floor0=1, unit0=300, stage=stage, ends=(False, True), **cw_kw)
    if stage == 0:
        mb.box(24.4, 24.492, 10.108, 10.2, 5.05, 14.72, "curtain_frame")

    # 남측·동측 2~3층 연속 흰색 수평 차양 루버 핀 (1.0744m 피치, 경사로 윗면 교차점까지 연장 · 동측 Y=35.2 연결동 접합)
    if stage <= 1:
        pitch = (14.72 - 5.05) / 9.0
        md_clr = 0.097
        for k in range(1, 9):
            zb = 5.05 + k * pitch
            major = (k % 2 == 1)  # k=1(6.12), 3(8.27), 5(10.42), 7(12.57)
            depth = 0.50 if major else 0.40
            half_t = 0.075 if major else 0.054
            x0_s = max(-18.4, _ramp_x_at_zt(zb + half_t))
            mb.box(x0_s, 24.4 + depth, 10.2 - depth, 10.2 - md_clr, zb - half_t, zb + half_t, "louver_white")
            mb.box(24.4 + md_clr, 24.4 + depth, 10.2 - md_clr, 35.20, zb - half_t, zb + half_t, "louver_white")

    if stage == 0:
        _sign_quad(mb, A, [(6.8, 9.63, 14.98), (22.2, 9.63, 14.98), (22.2, 9.63, 16.32), (6.8, 9.63, 16.32)], "sign_center_roof")

    # 남동 평지붕 태양광 어레이 2개소 (sat_vworld_z19.png 실측)
    mb.box(3.8, 20.4, 14.0, 27.6, 15.10, 15.32, "solar_pv")
    mb.box(3.8, 13.5, 29.0, 34.0, 15.10, 15.32, "solar_pv")


def build_south_ramp_and_entrance(mb, A, wins, stage):
    """5. 남측 사선 문화산책로 경사로 · 하부 수직 핀 유리 아트리움 · 1층 행정복지센터/로컬푸드 주출입구."""
    x_l, x_r = RAMP_X0, RAMP_X1
    ramp_yf, ramp_zb, dz_ramp = _ramp_yf, _ramp_zb, RAMP_DZ

    # 1) 사선 램프 백색 대들보/캐노피 슬래브 (y_back=10.16으로 Y=10.2 본체와 4cm 분리해 COPLANAR 방지)
    _segmented_ramp_slab(
        mb, x_l, x_r, ramp_yf(x_l), ramp_yf(x_r), 10.16,
        ramp_zb(x_l), ramp_zb(x_r), dz_ramp, "white_panel",
        n_seg=(11 if stage < 2 else 1),
    )

    if stage == 2:
        # LOD2: 사선 경사로 하부 1층 청록 유리 쐐기 유지 (2 tris)
        mb.quad(
            [(-18.4, 10.19, 0.20), (4.2, 10.19, 0.20),
             (4.2, 10.19, ramp_zb(4.2)), (-18.4, 10.19, ramp_zb(-18.4))],
            A.uv("teal_glass"), "teal_glass",
        )
        return

    # 2) 사선 램프 상단 경사 3단 스테인리스 난간 (south_se_close.png 기준)
    if stage == 0:
        for rh in (0.36, 0.68, 1.02):
            for ra, rb in ((x_l, RAMP_XK), (RAMP_XK, x_r)):
                _closed_quad_prism(
                    mb,
                    (ra, ramp_yf(ra) + 0.05, ramp_zb(ra) + dz_ramp + rh),
                    (rb, ramp_yf(rb) + 0.05, ramp_zb(rb) + dz_ramp + rh),
                    (rb, ramp_yf(rb) + 0.12, ramp_zb(rb) + dz_ramp + rh),
                    (ra, ramp_yf(ra) + 0.12, ramp_zb(ra) + dz_ramp + rh),
                    0.045, "railing_steel",
                )
        n_posts = 22
        for i in range(n_posts):
            xp = x_l + (x_r - x_l) * i / (n_posts - 1)
            yp = ramp_yf(xp) + 0.06
            zp = ramp_zb(xp) + dz_ramp
            mb.box(xp - 0.025, xp + 0.025, yp, yp + 0.06, zp, zp + 1.04, "railing_steel")

    # 3) 1층 우측 주출입구 ('석봉동 행정복지센터' X in [+4.2, +14.2] + '대덕로컬푸드직매장' X in [+14.5, +22.0])
    _box_var(mb, 3.55, 4.25, 7.80, 8.50, 0.14, ramp_zb(3.90), "white_panel", variant=0, skip=("bottom",))
    for idx, cx in enumerate((14.4, 19.2, 23.9)):
        _box_var(mb, cx - 0.24, cx + 0.24, 7.05, 7.55, 0.14, ramp_zb(cx), "white_panel", variant=idx + 1, skip=("bottom",))

    # 1층 행정복지센터 주출입구 문 프레임/자동문 (Y=10.2 벽 앞 정렬, 벽 두께 Y=10.20..10.28)
    K.paint(mb, "y", 10.20, -1, 4.4, 14.2, 0.14, 4.30, "frame_metal", layer=1)
    K.paint(mb, "y", 10.20, -1, 7.8, 10.8, 0.14, 3.05, "door_entrance", layer=2)
    _add_window_bay(mb, wins, "y", 10.16, -1, 4.7, 7.5, 0.35, 3.05, 0, 320, stage)
    _add_window_bay(mb, wins, "y", 10.16, -1, 11.1, 13.9, 0.35, 3.05, 0, 321, stage)
    # 대덕로컬푸드직매장 전면 통창 (X in [+14.5, +21.9], Y=10.2)
    _curtain_wall_grid(mb, wins, "y", 10.2, -1, 14.5, 21.9, 0.30, 3.80, nx=5, nz=2, floor0=0, unit0=330, stage=stage, louver_step=0)

    if stage == 0:
        _sign_quad(mb, A, [(5.0, 10.10, 3.14), (13.8, 10.10, 3.14), (13.8, 10.10, 3.96), (5.0, 10.10, 3.96)], "sign_welfare_led")
        _sign_quad(
            mb, A,
            [(14.9, ramp_yf(14.9) - 0.03, ramp_zb(14.9) + 0.08),
             (23.5, ramp_yf(23.5) - 0.03, ramp_zb(23.5) + 0.08),
             (23.5, ramp_yf(23.5) - 0.03, ramp_zb(23.5) + 0.78),
             (14.9, ramp_yf(14.9) - 0.03, ramp_zb(14.9) + 0.78)],
            "sign_localfood",
        )
        # 1층 캐노피·주출입구 전실 하부 매입 조명등 4개소 (경사로 저면 아래 비간섭 밀착)
        for lx in (5.6, 7.8, 10.0, 12.2):
            zl = ramp_zb(lx + 0.28) - 0.01
            yl = ramp_yf(lx) + 0.85
            mb.box(lx - 0.28, lx + 0.28, yl, yl + 0.24, zl - 0.04, zl, "lamp_strip")

    # 4) 사선 경사로 하부(X in [-18.4, +4.2]) 약 0.6 m 간격 수직 백색 핀(폭 0.15 m, 깊이 0.38 m) + 1층 밝은 청록 유리 커튼월
    x_fin0, x_fin1 = -18.4, 4.2
    n_bays = 38
    bw = (x_fin1 - x_fin0) / n_bays  # 0.5947 m (~0.6 m)
    fin_hw = 0.075  # 핀 폭 0.15 m

    # 하부 베이스 실 · 1/2층 슬래브 트랜섬 · 우측 출입구 연결 잼 (유리 앞 10.125..10.183, 서로 비겹침)
    K.axbox(mb, "y", 10.183, -1, x_fin0, 4.200, 0.0, 0.058, 0.14, 0.28, "frame_metal", skip=("bottom",))
    K.axbox(mb, "y", 10.183, -1, x_fin0, 4.200, 0.0, 0.058, 3.98, 4.24, "frame_metal")
    K.axbox(mb, "y", 10.183, -1, 4.278, 4.40, 0.0, 0.058, 0.14, ramp_zb(4.40) - 0.09, "frame_metal", skip=("bottom",))
    if stage == 0:
        K.axbox(mb, "y", 10.183, -1, x_fin0, 4.200, 0.0, 0.048, 2.10, 2.17, "frame_metal")
        K.axbox(mb, "y", 10.183, -1, x_fin0, 1.20, 0.0, 0.048, 6.18, 6.25, "frame_metal")
        _closed_quad_prism(
            mb,
            (x_fin0, 10.125, ramp_zb(x_fin0) - 0.09),
            (4.40, 10.125, ramp_zb(4.40) - 0.09),
            (4.40, 10.183, ramp_zb(4.40) - 0.09),
            (x_fin0, 10.183, ramp_zb(x_fin0) - 0.09),
            0.09, "frame_metal", tiled=False,
        )

    # 청록 유리 커튼월 배경 (Y = 10.187, 1층 직사각 타일링 + 상부 쐐기 연속 UV 정합)
    K.paint(mb, "y", 10.197, -1, x_fin0, x_fin1, 0.28, 3.98, "teal_glass", layer=1)
    tu0, tv0, tu1, tv1 = A._uvrect("teal_glass")
    m_e = 0.5 / A.size
    tu0 += m_e
    tu1 -= m_e
    tv0 += m_e
    tv1 -= m_e
    for k in range(n_bays // 2):
        xa = x_fin0 + 2 * k * bw
        xb = min(x_fin1, xa + 2 * bw)
        za = min(8.24, ramp_zb(xa))
        zb = min(8.24, ramp_zb(xb))
        col_mod = k % 3
        fu0, fu1 = col_mod / 3.0, (col_mod + 1.0) / 3.0
        if xb - xa < 1.9 * bw:
            fu1 = fu0 + ((xb - xa) / (6.0 * bw))
        fva = min(1.0, max(0.02, (za - 4.24) / 4.0))
        fvb = min(1.0, max(0.02, (zb - 4.24) / 4.0))
        u_a = tu0 + (tu1 - tu0) * fu0
        u_b = tu0 + (tu1 - tu0) * fu1
        v_0 = tv0
        v_a = tv0 + (tv1 - tv0) * fva
        v_b = tv0 + (tv1 - tv0) * fvb
        mb.quad(
            [(xa, 10.187, 4.24), (xb, 10.187, 4.24), (xb, 10.187, zb), (xa, 10.187, za)],
            [(u_a, v_0), (u_b, v_0), (u_b, v_b), (u_a, v_a)],
            "teal_glass",
        )

    # 경사선 따라 높이가 달라지는 수직 백색 핀 열 (간격 ~0.595 m, 폭 0.15 m, 깊이 최대 0.38 m, LOD1 포함)
    if stage <= 1:
        for i in range(n_bays + 1):
            xf = x_fin0 + i * bw
            z_top_fin = min(8.26, ramp_zb(xf - fin_hw))
            y_fin_front = max(9.82, ramp_yf(xf - fin_hw) + 0.02)
            mb.box(xf - fin_hw, xf + fin_hw, y_fin_front, 10.20, 0.14, z_top_fin, "louver_white", skip=("bottom",))


def build_stage(A, stage):
    mb = K.MeshBuilder(A, split_tiles=(stage < 2))
    wins = K.WindowSet()
    gls = K.MeshBuilder(A)

    build_plaza_and_site(mb, A, wins, stage)
    build_north_wing(mb, A, wins, gls, stage)
    build_middle_courtyard_and_east(mb, wins, gls, stage)
    build_south_wings(mb, A, wins, gls, stage)
    build_south_ramp_and_entrance(mb, A, wins, stage)

    return dict(mb=mb, gls=gls, wins=wins)


def main():
    A = make_atlas(size=4096)
    s0 = build_stage(A, 0)
    s1 = build_stage(A, 1)
    s2 = build_stage(A, 2)

    out_dir = K.out_dir_from_argv("output")
    notes = {
        "building_name": "SeokbongWelfareCenter (석봉동 행정복지센터 / 석봉복합문화센터)",
        "real_location": "36.45068N, 127.42325E / 대전광역시 대덕구 대덕대로 1579 (석봉동 774)",
        "azimuth_deg": -11.2,
        "built_year": 2024,
        "floors": "B2~3F (최고높이 20.7 m)",
        "photo_mode": "NOT_APPLICABLE",
    }
    res = K.export_asset(
        "SeokbongWelfareCenter",
        level=1,
        meshes=dict(
            main=s0["mb"], lod1=s1["mb"], lod2=s2["mb"],
            gls=s0["gls"], lod1_gls=None, windows=s0["wins"],
        ),
        atlas=A,
        out_root=out_dir,
        lod2_tex=1024,
        lot=(7, 9),
        front_yard=1.0,
        notes=notes,
    )
    print(f"Exported SeokbongWelfareCenter -> {res}")


if __name__ == "__main__":
    main()
