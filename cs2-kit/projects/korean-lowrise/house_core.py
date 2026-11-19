"""한국 저층 주택: 시대별 규칙과 재현 가능한 시드 조합."""
from dataclasses import dataclass
import json
from pathlib import Path
import sys
import random

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import cs2kit as K
from local import kitext as KX  # 로컬 확장 (원본 키트 무수정)


@dataclass(frozen=True)
class HouseSpec:
    name: str = "KoreanHouseA01"
    lot: tuple = (2, 2)
    width: float = 9.6
    depth: float = 9.2
    floors: int = 2
    floor_h: float = 3.05
    wall_color: tuple = (151, 79, 57)
    roof_color: tuple = (80, 102, 87)
    stairs: bool = True
    tank: bool = True
    fence: bool = True
    era: str = "80s"
    seed: int = 0
    finish: str = "brick"
    balcony: str = "none"
    notch: bool = False
    shop: bool = False
    eaves: bool = False
    addon: str = "blue"
    fence_finish: str = "fence_white"
    roof_prop: str = "rack"
    grille_up: bool = False

    def __post_init__(self):
        if not (1 <= self.floors <= 2 and self.width >= 7 and self.depth >= 8):
            raise ValueError("M1 A형 범위: 1~2층, 폭 7m 이상, 깊이 8m 이상")
        if self.width + 4.4 > self.lot[0] * K.CELL_M or self.depth + 6 > self.lot[1] * K.CELL_M:
            raise ValueError("담장·외부계단 포함 형상이 lot를 넘음")


def seeded(era, seed, name=None):
    if era not in ("70s", "80s", "90s") or not isinstance(seed, int) or seed < 0:
        raise ValueError("시대는 70s/80s/90s, 시드는 0 이상의 정수")
    rng = random.Random(f"{era}:{seed}")
    finishes = {"70s": ("plaster", "mosaic", "plaster", "brick"),
                "80s": ("brick", "brick", "plaster", "porcelain"),
                "90s": ("mosaic", "porcelain", "mosaic", "plaster")}
    finish = finishes[era][seed % 4]
    if finish == "plaster" and (seed // 4) % 2:
        finish = "plaster_gray"
    return HouseSpec(name=name or f"KoreanHouseA{era}{seed+1:02}", era=era, seed=seed,
                     width=rng.choice((8.4, 9.0, 9.6)), depth=rng.choice((8.4, 9.0, 9.6)),
                     floor_h={"70s": 2.8, "80s": 2.95, "90s": 3.05}[era],
                     finish=finish, balcony=("rail", "enclosed", "none")[seed % 3],
                     notch=seed % 3 == 1, shop=era != "70s" and seed % 3 == 2,
                     eaves=era == "70s", addon=("blue", "orange")[seed % 2],
                     fence_finish="brick" if seed % 5 == 4 else "fence_white",
                     roof_prop=("rack", "platform", "jars", "dish", "solar")[seed % 5],
                     tank=seed % 4 != 3, stairs=seed % 4 != 2, grille_up=era == "70s" and seed % 2 == 1)


PRESETS = {"a01": HouseSpec(), "70s": seeded("70s", 0, "KoreanHouseA70s01"),
           "80s": seeded("80s", 1, "KoreanHouseA80s01"),
           "90s": seeded("90s", 2, "KoreanHouseA90s01")}


def _var(ctx, scale_px=6, seed=1):
    return np.tanh(ctx.noise(scale_px=scale_px, amp=1.0, octaves=2, seed=seed) * 0.65)


def _make_weather_painter(seed, stain_amt, tone_mul):
    def _painter(ctx):
        ctx.rgb[...] *= tone_mul
        ctx.grain(amp=3.5, scale_px=3, height=0.08, seed=71 + seed * 3)
        k = ctx.stains(amount=stain_amt, scale_px=38, streaks=0.20, seed=73 + seed * 11)
        v = _var(ctx, scale_px=10, seed=79 + seed * 5)
        ctx.gloss = np.clip(ctx.gloss + 0.035 * v - 0.055 * k, 0.12, 0.90)
    return _painter


def weather(ctx):
    ctx.grain(amp=3.5, scale_px=3, height=0.08, seed=71)
    k = ctx.stains(amount=0.085, scale_px=38, streaks=0.20, seed=73)
    v = _var(ctx, scale_px=10, seed=79)
    ctx.gloss = np.clip(ctx.gloss + 0.035 * v - 0.055 * k, 0.12, 0.90)


def _make_mosaic_painter(seed, stain_amt, tone_mul):
    def _painter(ctx):
        ctx.rgb[...] *= tone_mul
        d = ctx.joints(cols=20, rows=20, width_m=0.006, depth=0.35, darken=0.24, tone=6, seed=3 + seed * 7)
        ctx.grain(amp=3.2, scale_px=3, height=0.08, seed=71 + seed * 3)
        k = ctx.stains(amount=stain_amt, scale_px=38, streaks=0.20, seed=73 + seed * 11)
        v = _var(ctx, scale_px=10, seed=79 + seed * 5)
        ctx.gloss = np.clip(ctx.gloss + 0.035 * v - 0.055 * k, 0.12, 0.90)
        jv = _var(ctx, scale_px=4, seed=5 + seed)
        ctx.gloss = np.clip(ctx.gloss * (1.0 - d) + (0.17 + 0.02 * jv) * d, 0.14, 0.56)
    return _painter


def mosaic(ctx):
    d = ctx.joints(cols=20, rows=20, width_m=0.006, depth=0.35, darken=0.24, tone=6, seed=3)
    weather(ctx)
    jv = _var(ctx, scale_px=4, seed=5)
    ctx.gloss = np.clip(ctx.gloss * (1.0 - d) + (0.17 + 0.02 * jv) * d, 0.14, 0.56)


def _make_porcelain_painter(seed, stain_amt, tone_mul):
    def _painter(ctx):
        ctx.rgb[...] *= tone_mul
        d = ctx.joints(cols=4, rows=3, width_m=0.008, depth=0.38, darken=0.24, tone=5, seed=7 + seed * 7)
        ctx.grain(amp=3.2, scale_px=3, height=0.08, seed=71 + seed * 3)
        k = ctx.stains(amount=stain_amt, scale_px=38, streaks=0.20, seed=73 + seed * 11)
        v = _var(ctx, scale_px=10, seed=79 + seed * 5)
        ctx.gloss = np.clip(ctx.gloss + 0.035 * v - 0.055 * k, 0.12, 0.90)
        jv = _var(ctx, scale_px=4, seed=8 + seed)
        ctx.gloss = np.clip(ctx.gloss * (1.0 - d) + (0.16 + 0.02 * jv) * d, 0.13, 0.44)
    return _painter


def porcelain(ctx):
    d = ctx.joints(cols=4, rows=3, width_m=0.008, depth=0.38, darken=0.24, tone=5, seed=7)
    weather(ctx)
    jv = _var(ctx, scale_px=4, seed=8)
    ctx.gloss = np.clip(ctx.gloss * (1.0 - d) + (0.16 + 0.02 * jv) * d, 0.13, 0.44)


def stone(ctx):
    d = ctx.joints(cols=2, rows=3, width_m=0.012, depth=0.6, darken=0.28, tone=12, stagger=0.5, seed=9)
    ctx.grain(amp=10, scale_px=2, height=0.35, seed=17)
    v = _var(ctx, scale_px=6, seed=18)
    ctx.gloss = np.clip((0.28 + 0.05 * v) * (1.0 - d) + (0.16 + 0.02 * v) * d, 0.13, 0.35)


def plinth(ctx):
    d = ctx.joints(cols=4, rows=1, width_m=0.012, depth=0.4, darken=0.25, tone=5, seed=11)
    ctx.grain(amp=8, scale_px=2, height=0.3, seed=13)
    splash = np.clip(1-ctx.v/0.65, 0, 1) * (0.5+0.5*ctx.noise(scale_px=12, seed=15))
    ctx.rgb *= (1-0.24*splash)[..., None]
    v = _var(ctx, scale_px=6, seed=16)
    face_g = 0.29 + 0.045 * v - 0.06 * np.clip(splash, 0, 1)
    ctx.gloss = np.clip(face_g * (1.0 - d) + (0.15 + 0.015 * v) * d, 0.13, 0.35)


def pattern(ctx):
    x, z = ctx.meters()
    diamond = np.abs(x % 0.3 - 0.15) + np.abs(z-0.15) < 0.11
    ctx.rgb[diamond] = (78, 99, 111)
    d = ctx.joints(cols=8, rows=2, width_m=0.005, depth=0.2, tone=1, seed=21)
    ctx.grain(amp=2.5, scale_px=2, height=0.05, seed=23)
    v = _var(ctx, scale_px=5, seed=24)
    tile_g = np.where(diamond, 0.50, 0.44) + 0.035 * v
    ctx.gloss = np.clip(tile_g * (1.0 - d) + 0.17 * d, 0.15, 0.55)


def corrugated(ctx):
    x, _ = ctx.meters()
    rib = np.cos(x * np.pi * 2 / 0.12)
    ctx.rgb += rib[..., None]*9
    ctx.height += rib*0.35
    weather(ctx)
    ctx.gloss = np.clip(ctx.gloss + 0.03 * rib, 0.34, 0.54)


def clay(ctx):
    x, z = ctx.meters()
    rib = np.cos(x*np.pi*2/0.18)
    ctx.height += 0.5*rib
    ctx.rgb *= (0.82+0.18*rib)[..., None]
    d = ctx.joints(cols=12, rows=4, width_m=0.015, depth=0.4, tone=7, seed=22)
    ctx.grain(amp=3.0, scale_px=3, height=0.06, seed=25)
    v = _var(ctx, scale_px=8, seed=26)
    ctx.gloss = np.clip((0.34 + 0.04 * rib + 0.035 * v) * (1.0 - d) + 0.17 * d, 0.15, 0.44)


def louver(ctx):
    rib = np.cos(ctx.v*42*np.pi) > 0.25
    ctx.rgb[rib] *= 0.43
    ctx.height[rib] -= 0.35
    ctx.grain(amp=2, scale_px=2, height=0.03, seed=24)
    v = _var(ctx, scale_px=6, seed=27)
    ctx.gloss = np.clip(np.where(rib, 0.16 + 0.02 * v, 0.43 + 0.04 * v), 0.12, 0.50)


def streak(ctx):
    # 투명 컷아웃 얼룩. 창 아래·실외기 아래에만 작은 면으로 배치한다.
    n = ctx.noise(scale_px=7, amp=1, octaves=2, seed=35)
    stripes = (np.sin(ctx.u*73)+np.sin(ctx.u*117+2))*0.25+0.5
    mask = stripes * (0.25+0.75*ctx.v) + n*0.15 > 0.58
    ctx.alpha[...] = np.where(mask, 255, 0)
    ctx.grain(amp=4.0, scale_px=3, height=0.06, seed=36)
    v = _var(ctx, scale_px=6, seed=37)
    ctx.gloss = np.clip(0.17 + 0.035 * v, 0.12, 0.22)


def _make_weather_band_painter(mode, seed):
    """벽 전체 폭 기준 위치 기반 오염/음영 밴드(투명 컷아웃) — 2.4m 타일 반복감 완화."""
    def _painter(ctx):
        base_col = ctx.rgb[0, 0].copy()
        n1 = ctx.noise(scale_px=12, amp=1.0, octaves=3, seed=301 + seed * 7)
        n2 = ctx.noise(scale_px=4, amp=1.0, octaves=2, seed=307 + seed * 11)
        if mode == "bot":
            density = np.clip(1.0 - ctx.v * 1.15, 0.0, 1.0)
            stripes = 0.5 + 0.5 * np.sin(ctx.u * 41.0 + seed)
            mask = (density * 0.72 + 0.14 * stripes + 0.22 * n1 + 0.16 * n2) > 0.62
        else:
            col_n = ctx.noise(scale_px=5, amp=1.0, octaves=2, seed=401 + seed * 5).mean(axis=0, keepdims=True)
            density = np.clip((ctx.v - 0.10) / 0.90, 0.0, 1.0)
            mask = (density * 0.70 + 0.24 * col_n + 0.20 * n1 + 0.15 * n2) > 0.62
        ctx.alpha[...] = np.where(mask, 255, 0)
        ctx.rgb[...] = base_col * (0.88 + 0.14 * n1[..., None] + 0.08 * n2[..., None])
        ctx.height[...] = 0.06 * n2
        v = _var(ctx, scale_px=8, seed=313 + seed)
        ctx.gloss = np.clip(0.15 + 0.03 * v, 0.11, 0.21)
    return _painter


def text_label(ctx, text, key):
    cache = HERE / "work" / "_sign_cache" / f"{key}_{ctx.w}x{ctx.h}.npz"
    try:
        from PIL import Image, ImageDraw, ImageFont
        im = Image.new("RGB", (ctx.w, ctx.h), (33, 64, 98))
        draw = ImageDraw.Draw(im)
        size = int(min(ctx.h*0.65, ctx.w*1.3/len(text)))
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", max(12, size))
        bb = draw.textbbox((0, 0), text, font=font)
        draw.text(((ctx.w-bb[2])/2, (ctx.h-bb[3])/2), text, font=font, fill=(246, 244, 227))
        rgb = np.asarray(im)
        cache.parent.mkdir(parents=True, exist_ok=True)
        np.savez(cache, rgb=rgb)
    except ImportError:
        rgb = np.load(cache)["rgb"]
    ctx.rgb[...] = rgb
    ctx.grain(amp=1.5, scale_px=2, height=0.03, seed=39)
    ctx.gloss = np.clip(0.42 + 0.04 * _var(ctx, scale_px=8, seed=40), 0.36, 0.48)


def address(ctx):
    """도로명 건물번호판(남색 바탕·흰 테두리·흰 글씨, 도로명 + 번호 두 줄). 칸 가운데 2:1 띠(v 0.25~0.75)에 그리고
    판 앞면은 uv_sub 로 그 띠만 쓴다. 도로명은 가상 이름."""
    cache = HERE / "work" / "_sign_cache" / f"address2_{ctx.w}x{ctx.h}.npz"
    navy = (30, 58, 112)
    try:
        from PIL import Image, ImageDraw, ImageFont
        S = 4
        W, H = ctx.w * S, ctx.h * S
        im = Image.new("RGB", (W, H), navy)
        d = ImageDraw.Draw(im)
        top, bot = int(H * 0.25), int(H * 0.75)
        ph = bot - top
        m = int(ph * 0.08)
        d.rectangle([m, top + m, W - 1 - m, bot - 1 - m], outline=(238, 240, 244), width=max(2, int(ph * 0.035)))
        lines = (("다온길", "C:/Windows/Fonts/malgunbd.ttf", 0.24, 0.33), ("17-8", "C:/Windows/Fonts/arialbd.ttf", 0.42, 0.66))
        for text, font_path, size, cy in lines:
            font = ImageFont.truetype(font_path, int(ph * size))
            bb = d.textbbox((0, 0), text, font=font)
            d.text(((W - (bb[2] - bb[0])) / 2 - bb[0], top + ph * cy - (bb[3] - bb[1]) / 2 - bb[1]), text,
                   font=font, fill=(244, 245, 247))
        rgb = np.asarray(im.resize((ctx.w, ctx.h), Image.LANCZOS))
        cache.parent.mkdir(parents=True, exist_ok=True)
        np.savez(cache, rgb=rgb)
    except (ImportError, OSError):
        rgb = np.load(cache)["rgb"]
    ctx.rgb[...] = rgb
    ctx.grain(amp=1.2, scale_px=2, height=0.02, seed=39)
    ctx.gloss = np.clip(0.46 + 0.03 * _var(ctx, scale_px=8, seed=40), 0.40, 0.52)


def sign(ctx):
    text_label(ctx, "DAON SHOP", "sign")


def _make_brick_painter(seed, mortar_rgb, stain_amt, tone_mul):
    def _painter(ctx):
        x, z = ctx.meters()
        row = np.floor(z / 0.075)
        col_i = np.floor((x + (row % 2) * 0.12) / 0.24)
        joint = ((z % 0.075) < 0.009) | (((x + (row % 2) * 0.12) % 0.24) < 0.009)
        brick_var = (((row * 31 + col_i * 17 + seed * 13) % 11) - 5) * 2.2
        ctx.rgb[...] = np.clip(ctx.rgb * tone_mul + brick_var[..., None], 40, 224)
        ctx.rgb[joint] = mortar_rgb
        ctx.height[joint] -= 0.3
        ctx.grain(amp=4, scale_px=2, height=0.1, seed=71 + seed * 3)
        k = ctx.stains(amount=stain_amt, scale_px=36, streaks=0.16, seed=75 + seed * 13)
        v = _var(ctx, scale_px=6, seed=77 + seed * 5)
        ctx.gloss = np.clip(np.where(joint, 0.16 + 0.02 * v, 0.26 + 0.035 * v - 0.05 * k), 0.13, 0.32)
    return _painter


def brick(ctx):
    x, z = ctx.meters()
    row = np.floor(z / 0.075)
    joint = ((z % 0.075) < 0.009) | (((x + (row % 2) * 0.12) % 0.24) < 0.009)
    ctx.rgb[joint] = (176, 158, 137)
    ctx.height[joint] -= 0.3
    ctx.grain(amp=4, scale_px=2, height=0.1, seed=71)
    k = ctx.stains(amount=0.08, scale_px=36, streaks=0.16, seed=75)
    v = _var(ctx, scale_px=6, seed=77)
    ctx.gloss = np.clip(np.where(joint, 0.16 + 0.02 * v, 0.26 + 0.035 * v - 0.05 * k), 0.13, 0.32)


def waterproof(ctx):
    ctx.grain(amp=3, scale_px=8, height=0.06, seed=17)
    k = ctx.stains(amount=0.07, scale_px=40, streaks=0, seed=19)
    v = _var(ctx, scale_px=12, seed=20)
    ctx.gloss = np.clip(0.37 + 0.045 * v - 0.07 * k, 0.24, 0.45)


def windows(ctx):
    u, v = ctx.u * K.REF_GRID, ctx.v * K.REF_GRID
    cell = v.astype(int) * K.REF_GRID + u.astype(int)
    curtain = 0.5 + 0.5 * np.cos(u * (2 * np.pi * 15))
    edge = np.minimum(u % 1, 1 - u % 1) < 0.015
    edge |= np.minimum(v % 1, 1 - v % 1) < 0.015
    lit = np.isin(cell, (0, 3, 7, 11, 14, 18, 21)) & ~edge
    ctx.rgb[...] *= (0.86 + 0.10 * curtain + 0.10 * (v % 1))[..., None]
    ctx.emis[...] = np.where(lit, (0.28 + 0.06 * (cell % 4)) * (0.72 + 0.28 * curtain), 0)
    nv = _var(ctx, scale_px=10, seed=81)
    glass_g = 0.79 + 0.04 * nv
    curtain_g = 0.72 + 0.03 * nv
    ctx.gloss = np.where(edge, 0.62, glass_g * (1.0 - curtain) + curtain_g * curtain)


def _solid_grain(ctx, amp, scale_px, height, g_lo, g_hi, seed, stain=0.0):
    ctx.grain(amp=amp, scale_px=scale_px, height=height, seed=seed)
    k = ctx.stains(amount=stain, scale_px=max(12, ctx.w // 4), streaks=0.12, seed=seed + 1) if stain > 0 else 0.0
    v = _var(ctx, scale_px=max(4, ctx.w // 10), seed=seed + 2)
    mid = 0.5 * (g_lo + g_hi)
    half = 0.5 * (g_hi - g_lo)
    g = mid + half * v - (0.03 * (k - 0.5) if stain > 0 else 0.0)
    ctx.gloss = np.clip(g, g_lo, g_hi)


def paint_cement(ctx):
    _solid_grain(ctx, amp=4.5, scale_px=3, height=0.14, g_lo=0.18, g_hi=0.26, seed=41, stain=0.06)


def paint_frame(ctx):
    _solid_grain(ctx, amp=2.5, scale_px=3, height=0.06, g_lo=0.40, g_hi=0.54, seed=44)


def paint_steel(ctx):
    _solid_grain(ctx, amp=3.0, scale_px=3, height=0.08, g_lo=0.36, g_hi=0.48, seed=47)


def paint_door(ctx):
    _solid_grain(ctx, amp=3.5, scale_px=3, height=0.10, g_lo=0.30, g_hi=0.40, seed=50)


def paint_roof_equipment(ctx):
    _solid_grain(ctx, amp=3.0, scale_px=3, height=0.07, g_lo=0.38, g_hi=0.48, seed=53, stain=0.05)


def paint_tank(ctx):
    _solid_grain(ctx, amp=3.5, scale_px=3, height=0.08, g_lo=0.40, g_hi=0.54, seed=56, stain=0.05)


def paint_gas(ctx):
    _solid_grain(ctx, amp=2.5, scale_px=2, height=0.06, g_lo=0.34, g_hi=0.44, seed=59)


def paint_wood(ctx):
    plank = np.sin(ctx.v * 24 * np.pi)
    ctx.rgb += plank[..., None] * 2.5
    ctx.height += plank * 0.04
    _solid_grain(ctx, amp=4.0, scale_px=2, height=0.10, g_lo=0.22, g_hi=0.30, seed=62, stain=0.04)


def paint_jar(ctx):
    _solid_grain(ctx, amp=3.5, scale_px=2, height=0.08, g_lo=0.48, g_hi=0.62, seed=65)


def paint_solar(ctx):
    grid = (np.minimum((ctx.u * 8) % 1, 1 - (ctx.u * 8) % 1) < 0.04) | (
        np.minimum((ctx.v * 12) % 1, 1 - (ctx.v * 12) % 1) < 0.04)
    ctx.rgb[grid] *= 1.18
    ctx.height[grid] += 0.06
    _solid_grain(ctx, amp=1.5, scale_px=2, height=0.03, g_lo=0.80, g_hi=0.88, seed=68)


def paint_awning(ctx):
    _solid_grain(ctx, amp=2.5, scale_px=3, height=0.06, g_lo=0.36, g_hi=0.48, seed=83)


def paint_lamp(ctx):
    _solid_grain(ctx, amp=1.0, scale_px=3, height=0.02, g_lo=0.55, g_hi=0.65, seed=86)


SOLID_PAINTERS = {
    "cement": paint_cement,
    "frame": paint_frame,
    "steel": paint_steel,
    "door": paint_door,
    "roof_equipment": paint_roof_equipment,
    "tank": paint_tank,
    "gas": paint_gas,
    "wood": paint_wood,
    "jar": paint_jar,
    "solar": paint_solar,
}


def atlas(spec):
    s = spec.seed
    era_off = {"70s": 1, "80s": 2, "90s": 3}[spec.era]
    sv = s * 3 + era_off
    stain_amt = 0.065 + (sv % 4) * 0.015
    tone_mul = 0.96 + (sv % 5) * 0.018
    m_shift = ((sv % 5) - 2) * 5.0
    m_warm = ((sv % 3) - 1) * 4.0
    mortar_rgb = (int(np.clip(176 + m_shift + m_warm, 145, 200)),
                  int(np.clip(158 + m_shift, 130, 185)),
                  int(np.clip(137 + m_shift - m_warm, 110, 165)))

    a = K.Atlas(size=2048, pad=12)
    a.add("brick", color=spec.wall_color, ctrl=(0, 255, 0), px=512,
          tile=(2.4, 2.4), gloss=0.26, painter=_make_brick_painter(sv, mortar_rgb, stain_amt, tone_mul))
    a.add("mosaic", color=(210, 210, 197), ctrl=(0, 255, 0), px=512, tile=(1.6, 1.6), gloss=0.50,
          painter=_make_mosaic_painter(sv, stain_amt, tone_mul))
    a.add("plaster", color=(214, 209, 192), ctrl=(0, 255, 0), px=384, tile=(2.4, 2.4), gloss=0.25,
          painter=_make_weather_painter(sv, stain_amt, tone_mul))
    a.add("plaster_gray", color=(191, 195, 192), ctrl=(0, 255, 0), px=256, tile=(2.4, 2.4), gloss=0.25,
          painter=_make_weather_painter(sv + 7, stain_amt, tone_mul))
    a.add("fence_white", color=(206, 206, 198), ctrl=(0, 255, 0), px=256, tile=(2.4, 2.4), gloss=0.25,
          painter=_make_weather_painter(sv + 13, stain_amt, tone_mul))
    a.add("porcelain", color=(164, 158, 146), ctrl=(0, 255, 0), px=512, tile=(2.4, 2.4), gloss=0.38,
          painter=_make_porcelain_painter(sv, stain_amt, tone_mul))
    a.add("pattern", color=(212, 209, 190), ctrl=(0, 255, 0), px=256, tile=(1.2, 0.3), gloss=0.44, painter=pattern)
    a.add("plinth", color=(77, 79, 74), px=256, tile=(2.4, 0.6), gloss=0.29, painter=plinth)
    a.add("roof", color=spec.roof_color, ctrl=(255, 0, 0), px=256,
          tile=(3.2, 3.2), gloss=0.37, painter=waterproof)
    window_color = {"70s": (85, 107, 110), "80s": (91, 120, 130), "90s": (123, 146, 150)}[spec.era]
    a.add("window", color=window_color, px=384, gloss=0.79,
          emissive=(255, 219, 171), painter=windows)
    a.add("window_backing", color=window_color, px=32, gloss=0.76)
    a.add("stone", color=(164, 161, 147), px=256, tile=(1.0, 1.2), gloss=0.28, painter=stone)
    a.add("clay", color=(163, 73, 48), px=256, tile=(2.16, 0.8), gloss=0.34, painter=clay)
    a.add("blue", color=(74, 102, 120), px=128, tile=(2, 2), gloss=0.46, painter=corrugated)
    a.add("orange", color=(154, 109, 86), px=128, tile=(2, 2), gloss=0.46, painter=corrugated)
    a.add("shutter", color=(134, 139, 132), ctrl=(0, 0, 255), px=256, gloss=0.43, painter=louver)
    a.add("equipment_face", color=(169, 177, 168), px=128, gloss=0.43, painter=louver)
    a.add("drip", color=(95, 89, 68), px=128, gloss=0.17, painter=streak)
    a.add("rust", color=(132, 74, 40), px=128, gloss=0.17, painter=streak)
    a.add("weather_bot", color=(78, 73, 62), px=128, variants=2, gloss=0.15,
          painter=_make_weather_band_painter("bot", sv))
    a.add("weather_top", color=(72, 69, 60), px=128, variants=2, gloss=0.16,
          painter=_make_weather_band_painter("top", sv))
    a.add("address", px=256, gloss=0.46, painter=address)
    a.add("sign", px=256, gloss=0.42, painter=sign)
    # 콘크리트 차양·코핑·계단 등은 1 m 넘는 면이 많아 실제 크기 타일 재질로 (단색 칸은 면 크기와 무관하게 늘어남)
    a.add("cement", color=(163, 166, 158), px=256, tile=(2.4, 2.4), gloss=0.24, painter=KX.stone_trim(sv))
    KX.add_grime_cells(a, seed=sv)
    for name, color, px in [("frame", {"70s": (157, 145, 118), "80s": (180, 184, 179), "90s": (215, 217, 207)}[spec.era], 128),
                            ("steel", (31, 39, 38), 128),
                            ("door", (89, 75, 60), 128),
                            ("roof_equipment", (175, 181, 167), 128),
                            ("tank", (182, 187, 180), 128),
                            ("gas", (184, 162, 92), 128),
                            ("wood", (133, 99, 64), 128), ("jar", (87, 56, 39), 128),
                            ("solar", (43, 71, 91), 128)]:
        a.add(name, color=color, px=px, metal=0.4 if name in ("steel", "tank") else 0,
              painter=SOLID_PAINTERS[name])
    a.add("awning", color=(97, 112, 100), ctrl=(0, 0, 255), px=128, gloss=0.42, painter=paint_awning)
    a.add("lamp", color=(255, 229, 175), emissive=(255, 214, 145), px=32, gloss=0.60, painter=paint_lamp)
    return a


def openings(spec, axis, side):
    length = spec.width if axis == "y" else spec.depth
    start = -spec.width / 2 if axis == "y" else 0
    result = []
    for f in range(spec.floors):
        for pos in (0.23, 0.77):
            if axis == "y" and side == -1 and f == 0 and spec.shop:
                continue
            if axis == "y" and side == -1 and f == 1 and spec.balcony == "enclosed":
                continue
            if axis == "x" and side == 1 and pos == (0.23 if f == 0 else 0.77):
                continue  # 외부계단 상부 출입문·계단 참 확보
            c = start + pos * length
            if axis == "x" and side == 1 and f == 0:
                c = 0.83 * length
            half = {"70s": 0.75, "80s": 0.85, "90s": 0.95}[spec.era]
            height = {"70s": 1.25, "80s": 1.35, "90s": 1.45}[spec.era]
            result.append((c-half, c+half, f*spec.floor_h+1.0,
                           f*spec.floor_h+1.0+height, "window", f))
    if axis == "y" and side == -1:
        result.append((-0.55, 0.55, 0.16, 2.35, "door", 0))
        if spec.floors == 2 and spec.balcony == "rail":
            result.append((-0.48, 0.48, spec.floor_h+0.04, spec.floor_h+2.22, "door", 1))
    if axis == "x" and side == 1 and spec.floors == 2 and spec.stairs:
        result.append((5.10, 6.05, spec.floor_h + 0.04, spec.floor_h + 2.22, "door", 1))
    return sorted(result)


def _paint_band_clipped(mb, axis, c, side, lo, hi, z0, z1, region, blocked_spans, layer=1, variant=0):
    """개구부/부착물 구간을 제외한 벽 전체 폭에 비타일 오염 밴드를 칠한다."""
    spans = [(lo, hi)]
    for b0, b1 in blocked_spans:
        nxt = []
        for s0, s1 in spans:
            if b1 <= s0 + 0.04 or b0 >= s1 - 0.04:
                nxt.append((s0, s1))
            else:
                if b0 > s0 + 0.08:
                    nxt.append((s0, b0))
                if b1 < s1 - 0.08:
                    nxt.append((b1, s1))
        spans = nxt
    uv = mb.atlas.uv_full(region, variant=variant)
    for s0, s1 in spans:
        if s1 - s0 > 0.12:
            mb.quad(K.face_pts(axis, c + side * K.PAINT_OFF * layer, side, s0, s1, z0, z1), uv, region)


def facade(mb, wins, spec, axis, c, side, stage, lo=None, hi=None):
    """외벽을 개구부 주위 조각으로 만들어 유리가 실제 0.20m 후퇴한다."""
    if lo is None:
        lo, hi = (-spec.width / 2, spec.width / 2) if axis == "y" else (0, spec.depth)
    if axis == "x" and stage < 2:
        lo, hi = lo + 0.24, hi - 0.24  # 앞·뒤 벽이 모서리 두께를 담당
    holes = [v for v in openings(spec, axis, side) if v[0] > lo+0.05 and v[1] < hi-0.05]
    if spec.shop and axis == "y" and side == -1 and c == 0:
        holes.append((-spec.width*0.40, -0.95, 0.24, 2.38, "shutter", 0))
        holes.append((0.95, spec.width*0.40, 0.24, 2.38, "shutter", 0))
    top = spec.floors * spec.floor_h - 0.1
    cuts = sorted({lo, hi, *(v for h in holes for v in h[:2])})
    for left, right in zip(cuts, cuts[1:]):
        covered = sorted((h[2], h[3]) for h in holes if h[0] <= left and h[1] >= right)
        z = 0 if stage == 2 else 0.15
        for z0, z1 in covered + [(top, top)]:
            if z0 > z:
                if stage == 2:
                    mb.rect(K.face_pts(axis, c, side, left, right, z, z0), spec.finish)
                else:
                    K.axbox(mb, axis, c, side, left, right, -0.24, 0, z, z0, spec.finish)
            z = max(z, z1)
    for i, (a0, a1, z0, z1, kind, floor) in enumerate(holes):
        if kind == "window":
            mid = (a0 + a1) / 2
            face = (2 if axis == "x" else 0) + (side > 0)
            unit = face * 11 + i + 5 * spec.seed
            for b0, b1 in ((a0+0.06, mid-0.025), (mid+0.025, a1-0.06)):
                wins.add_face(axis, c - side * 0.22, side, b0, b1, z0+0.05, z1-0.05, floor, unit)
                wins.items[-1]["pts2"] = K.face_pts(axis, c+side*0.02, side, b0, b1, z0+0.05, z1-0.05)
            if stage == 2:
                mb.rect(K.face_pts(axis, c+side*0.001, side, a0, a1, z0, z1), "window_backing")
        else:
            reg = "shutter" if kind == "shutter" else "door"
            if stage == 2:
                mb.rect(K.face_pts(axis, c+side*0.001, side, a0, a1, z0, z1), reg)
            else:
                K.axbox(mb, axis, c, side, a0+0.065, a1-0.065, -0.219, -0.20,
                        z0+0.05, z1-0.05, reg)
        if stage == 0:
            for b0, b1 in ((a0, a0 + 0.06), (a1 - 0.06, a1)):
                K.axbox(mb, axis, c, side, b0, b1, -0.22, -0.12, z0+0.05, z1-0.05, "frame")
            if kind == "window":
                for bz0, bz1 in ((z0 + 0.04, z0 + 0.05), (z1 - 0.05, z1 - 0.04)):
                    K.axbox(mb, axis, c, side, a0, a1, -0.22, -0.10, bz0, bz1, "frame")
                K.axbox(mb, axis, c, side, mid - 0.025, mid + 0.025, -0.22, -0.12, z0+0.05, z1-0.05, "frame")
                if floor == 0 or spec.grille_up:
                    # 방범창 막대를 수직 3개 + 수평 2개로 절감(기존 8개 -> 5개)
                    for u in (0.18, 0.50, 0.82):
                        x = a0+(a1-a0)*u
                        K.axbox(mb, axis, c, side, x-0.014, x+0.014, 0.10, 0.13, z0+0.08, z1-0.08, "steel")
                    for z in (z0+(z1-z0)*0.28, z0+(z1-z0)*0.72):
                        K.axbox(mb, axis, c, side, a0+0.05, a1-0.05, 0.13, 0.15, z-0.014, z+0.014, "steel")
                K.paint(mb, axis, c, side, a0+0.08, a1-0.08, max(0.65, z0-0.50), z0-0.08, "drip")
        if stage < 2:
            for b0, b1, lip in ((z0 - 0.07, z0 + 0.03, 0.12), (z1 - 0.03, z1 + 0.09, 0.05)):
                if stage == 0:
                    KX.ax_bevel(mb, axis, c, side, a0 - 0.08, a1 + 0.08, -0.23, lip, b0, b1, "stone", bevel=0.015)
                else:
                    K.axbox(mb, axis, c, side, a0 - 0.08, a1 + 0.08, -0.23, lip, b0, b1, "stone")
        if stage == 0:
            # 개구부 옆면(창틀 앞 0.12 m)을 콘크리트로 — 벽 타일이 옆면에 늘어져 보이던 것 정리
            KX.paint_reveal(mb, axis, c, side, a0, a1, z0 + 0.03, z1 - 0.03, 0.12, "cement", sill=False, head=False)
        if stage == 0 and kind == "window":
            for bx in (a0 + 0.12, a1 - 0.12):
                K.axbox(mb, axis, c, side, bx - 0.04, bx + 0.04, 0.0, 0.09, z0 - 0.15, z0 - 0.07, "stone", skip=("top",))
        if stage < 2 and kind == "window":
            # 창 위 콘크리트 차양 (0.30 m 내밀기) + 하부 물끊기 + 까치발 2개
            if stage == 0:
                KX.ax_bevel(mb, axis, c, side, a0 - 0.14, a1 + 0.14, 0.0, 0.30, z1 + 0.13, z1 + 0.21, "cement", bevel=0.02)
            else:
                K.axbox(mb, axis, c, side, a0 - 0.14, a1 + 0.14, 0.0, 0.30, z1 + 0.13, z1 + 0.21, "cement")
            if stage == 0:
                K.axbox(mb, axis, c, side, a0 - 0.14, a1 + 0.14, 0.25, 0.30, z1 + 0.10, z1 + 0.13, "cement", skip=("top",))
                for bx in (a0 - 0.06, a1 + 0.06):
                    K.axbox(mb, axis, c, side, bx - 0.03, bx + 0.03, 0.0, 0.18, z1 + 0.04, z1 + 0.13, "cement", skip=("top",))
    plo, phi = lo + 0.02, hi - 0.02  # 칠 띠가 모서리 끝에서 비쳐 보이지 않도록
    K.paint(mb, axis, c, side, plo, phi, 0.16, 0.62, "plinth")
    if spec.finish == "mosaic":
        K.paint(mb, axis, c, side, plo, phi, spec.floor_h-0.42, spec.floor_h-0.12, "pattern")
    if stage < 2:
        face_v = (1 if side > 0 else 0)
        bot_blocked = [(h[0] - 0.10, h[1] + 0.10) for h in holes if h[2] < 0.78]
        if axis == "y" and side == -1 and spec.stairs:
            pass
        _paint_band_clipped(mb, axis, c, side, plo, phi, 0.16, 0.75, "weather_bot",
                            bot_blocked, layer=2, variant=face_v)
        top_blocked = []
        if axis == "y" and side == -1 and spec.balcony == "enclosed":
            bw = spec.width * 0.34 + 0.05
            top_blocked.append((-bw, bw))
        _paint_band_clipped(mb, axis, c, side, plo, phi, top - 0.35, top, "weather_top",
                            top_blocked, layer=1, variant=face_v ^ 1)


def slope_box(mb, bounds, region, axis, rise):
    part = K.MeshBuilder(mb.atlas, split_tiles=mb.split_tiles)
    part.box(*bounds, region)
    origin = bounds[axis*2]
    span = bounds[axis*2+1]-origin
    part.verts = [(x, y, z+((x, y)[axis]-origin)*rise/span) for x, y, z in part.verts]
    mb.merge(part)


def _oct_prism_pts(cx, cy, r, z0, z1, n=8):
    ring = [(cx + r * np.cos(t * 2 * np.pi / n), cy + r * np.sin(t * 2 * np.pi / n)) for t in range(n)]
    return ring, z0, z1


def _add_oct_tube(mb, p0, p1, r, region, n=8):
    """두 점 p0->p1을 잇는 8각 관형 세그먼트(닫힌 입체, 수직/경사 모두 지원)."""
    dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    L = float(np.sqrt(dx * dx + dy * dy + dz * dz))
    if L < 1e-5:
        return
    ux, uy, uz = dx / L, dy / L, dz / L
    if abs(uz) < 0.9:
        rx, ry, rz = -uy, ux, 0.0
    else:
        rx, ry, rz = 1.0, 0.0, 0.0
    rl = float(np.sqrt(rx * rx + ry * ry + rz * rz))
    rx, ry, rz = rx / rl, ry / rl, rz / rl
    bx, by, bz = uy * rz - uz * ry, uz * rx - ux * rz, ux * ry - uy * rx
    ring0, ring1 = [], []
    for k in range(n):
        ang = k * 2 * np.pi / n
        ca, sa = np.cos(ang) * r, np.sin(ang) * r
        ox, oy, oz = rx * ca + bx * sa, ry * ca + by * sa, rz * ca + bz * sa
        ring0.append((p0[0] + ox, p0[1] + oy, p0[2] + oz))
        ring1.append((p1[0] + ox, p1[1] + oy, p1[2] + oz))
    uv = mb.atlas.uv(region)
    for k in range(n):
        kn = (k + 1) % n
        mb.quad([ring0[k], ring0[kn], ring1[kn], ring1[k]], uv, region)
    for k in range(1, n - 1):
        mb.tri([ring0[0], ring0[k + 1], ring0[k]], uv[:3], region)
        mb.tri([ring1[0], ring1[k], ring1[k + 1]], uv[:3], region)


def _add_downspout(mb, axis, c, side, a_pos, z_bot, z_top, eave_out=0.0):
    """8각 수직 선홈통 + 처마 물받이 박스 + 클램프 밴드 + 지면 엘보."""
    def pt(o, a, z):
        return (a, c + side * o, z) if axis == "y" else (c + side * o, a, z)

    # 1) 지붕 처마 물받이 박스 (Hopper box) + 상부 테두리
    ho0, ho1 = 0.03 + eave_out, 0.23 + eave_out
    K.axbox(mb, axis, c, side, a_pos - 0.11, a_pos + 0.11, ho0, ho1, z_top - 0.02, z_top + 0.14, "steel")
    K.axbox(mb, axis, c, side, a_pos - 0.13, a_pos + 0.13, ho0 - 0.01, ho1 + 0.01, z_top + 0.14, z_top + 0.17, "steel")

    # 2) 상부 백조목 연결 엘보 -> 벽면 수직관(offset 0.07m) + 상단 칼라 링
    o_hop = 0.5 * (ho0 + ho1)
    p_top = pt(o_hop, a_pos, z_top - 0.02)
    p_mid = pt(0.5 * (o_hop + 0.075), a_pos, z_top - 0.14)
    p_shaft_top = pt(0.075, a_pos, z_top - 0.28)
    _add_oct_tube(mb, p_top, p_mid, 0.052, "steel", n=8)
    _add_oct_tube(mb, p_mid, p_shaft_top, 0.052, "steel", n=8)
    _add_oct_tube(mb, pt(0.075, a_pos, z_top - 0.31), pt(0.075, a_pos, z_top - 0.25), 0.068, "steel", n=8)

    # 3) 8각 수직 선홈통 본체 (층 분할로 깔끔한 관절)
    z_elbow_top = z_bot + 0.24
    z_mid_joint = 0.5 * (z_elbow_top + z_top - 0.28)
    _add_oct_tube(mb, pt(0.075, a_pos, z_elbow_top), pt(0.075, a_pos, z_mid_joint), 0.052, "steel", n=8)
    _add_oct_tube(mb, pt(0.075, a_pos, z_mid_joint), p_shaft_top, 0.052, "steel", n=8)

    # 4) 클램프 밴드 + 벽면 고정 브래킷 (층당 2개소, 약 1.3m 간격)
    n_clamps = 4 if (z_top - z_bot) > 4.5 else 2
    for idx in range(n_clamps):
        zc = z_elbow_top + 0.45 + idx * (z_top - 0.45 - (z_elbow_top + 0.45)) / max(1, n_clamps - 1)
        _add_oct_tube(mb, pt(0.075, a_pos, zc - 0.025), pt(0.075, a_pos, zc + 0.025), 0.068, "steel", n=8)
        K.axbox(mb, axis, c, side, a_pos - 0.022, a_pos + 0.022, 0.0, 0.045, zc - 0.02, zc + 0.02, "steel")

    # 5) 지면 토출 엘보 (벽에서 바깥쪽으로 꺾여 배수) + 콘크리트 물받이 패드
    p_el1 = pt(0.125, a_pos, z_bot + 0.11)
    p_el2 = pt(0.24, a_pos, z_bot + 0.04)
    _add_oct_tube(mb, pt(0.075, a_pos, z_elbow_top), p_el1, 0.054, "steel", n=8)
    _add_oct_tube(mb, p_el1, p_el2, 0.056, "steel", n=8)
    _add_oct_tube(mb, p_el2, pt(0.27, a_pos, z_bot + 0.025), 0.064, "steel", n=8)
    K.axbox(mb, axis, c, side, a_pos - 0.14, a_pos + 0.14, 0.06, 0.42, 0.0, 0.045, "cement", skip=("bottom",))


def _draw_single_roof_prop(mb, kind, x, y, z, stage, scale=1.0):
    sc = scale
    if kind == "rack":
        for xx in (x - 0.7 * sc, x + 0.7 * sc):
            mb.box(xx - 0.04, xx + 0.04, y - 0.42 * sc, y + 0.42 * sc, z, z + 0.05, "cement", skip=("bottom",))
            mb.box(xx - 0.028, xx + 0.028, y - 0.40 * sc, y + 0.40 * sc, z + 0.05, z + 0.09, "steel")
            mb.box(xx - 0.022, xx + 0.022, y - 0.022, y + 0.022, z + 0.09, z + 1.05 * sc, "steel")
        for yy in (y - 0.35 * sc, y, y + 0.35 * sc):
            mb.box(x - 0.76 * sc, x + 0.76 * sc, yy - 0.016, yy + 0.016, z + 1.05 * sc, z + 1.08 * sc, "steel")
        if stage == 0:
            mb.box(x - 0.70 * sc, x + 0.70 * sc, y - 0.015, y + 0.015, z + 0.52 * sc, z + 0.55 * sc, "steel")
            for yy in (y - 0.35 * sc, y + 0.35 * sc):
                mb.box(x - 0.72 * sc, x - 0.68 * sc, min(y, yy), max(y, yy), z + 1.00 * sc, z + 1.05 * sc, "steel")
                mb.box(x + 0.68 * sc, x + 0.72 * sc, min(y, yy), max(y, yy), z + 1.00 * sc, z + 1.05 * sc, "steel")
    elif kind == "platform":
        for xx in (x - 0.62 * sc, x + 0.62 * sc):
            for yy in (y - 0.52 * sc, y + 0.52 * sc):
                mb.box(xx - 0.045, xx + 0.045, yy - 0.045, yy + 0.045, z, z + 0.25 * sc, "wood", skip=("bottom",))
        mb.box(x - 0.72 * sc, x + 0.72 * sc, y - 0.60 * sc, y + 0.60 * sc, z + 0.25 * sc, z + 0.30 * sc, "wood")
        for i in range(6):
            px0 = x - 0.75 * sc + i * 0.255 * sc
            mb.box(px0, px0 + 0.22 * sc, y - 0.65 * sc, y + 0.65 * sc, z + 0.30 * sc, z + 0.38 * sc, "wood")
        if stage == 0:
            mb.box(x - 0.50 * sc, x + 0.50 * sc, y - 0.90 * sc, y - 0.66 * sc, z, z + 0.16 * sc, "wood", skip=("bottom",))
    elif kind == "jars":
        if stage == 0:
            mb.box(x - 0.95 * sc, x + 0.95 * sc, y - 0.44 * sc, y + 0.44 * sc, z, z + 0.08, "cement", skip=("bottom",))
        z_base = z + (0.08 if stage == 0 else 0.0)
        radii = (0.24 * sc, 0.18 * sc, 0.28 * sc, 0.20 * sc) if stage == 0 else (0.25 * sc, 0.19 * sc, 0.29 * sc)
        for i, radius in enumerate(radii):
            cx = x + (i - (len(radii) - 1) * 0.5) * 0.52 * sc
            cy = y + (0.12 * sc if i % 2 else -0.10 * sc)
            n = 10 if stage == 0 else 6
            ring = [(cx + radius * np.cos(t * 2 * np.pi / n), cy + radius * np.sin(t * 2 * np.pi / n)) for t in range(n)]
            K.volume_prism(mb.atlas, ring, radius * 1.85, z0=z_base, wall="jar", roof="jar", mb=mb)
            if stage == 0:
                lid_r = radius * 0.88
                lring = [(cx + lid_r * np.cos(t * 2 * np.pi / 8), cy + lid_r * np.sin(t * 2 * np.pi / 8)) for t in range(8)]
                K.volume_prism(mb.atlas, lring, 0.045, z0=z_base + radius * 1.85, wall="jar", roof="jar", mb=mb)
                mb.box(cx - 0.03, cx + 0.03, cy - 0.03, cy + 0.03, z_base + radius * 1.895, z_base + radius * 1.94, "jar")
    elif kind == "dish":
        mb.box(x - 0.45 * sc, x + 0.45 * sc, y - 0.35 * sc, y + 0.35 * sc, z, z + 0.09, "cement", skip=("bottom",))
        mb.box(x - 0.04, x + 0.04, y - 0.04, y + 0.04, z + 0.09, z + 0.92 * sc, "steel")
        if stage == 0:
            mb.box(x - 0.22 * sc, x + 0.22 * sc, y - 0.22 * sc, y + 0.22 * sc, z + 0.09, z + 0.14, "steel")
        ring = [(x + 0.52 * sc * np.cos(t * np.pi / 6), y + 0.52 * sc * np.sin(t * np.pi / 6)) for t in range(12)]
        part = K.MeshBuilder(mb.atlas)
        K.volume_prism(mb.atlas, ring, 0.055, wall="tank", roof="tank", mb=part)
        if stage == 0:
            # LNB 암 + 리시버 헤드
            part.box(-0.02, 0.02, -0.35 * sc, 0.02, -0.45 * sc, 0.0, "steel")
            part.box(-0.045, 0.045, -0.40 * sc, -0.30 * sc, -0.48 * sc, -0.38 * sc, "roof_equipment")
        part.verts = [(vx, y + (vy - y) * 0.5 - vz * 0.866, z + 0.95 * sc + (vy - y) * 0.866 + vz * 0.5)
                      for vx, vy, vz in part.verts]
        mb.merge(part)
    else:
        for xx in (x - 0.70 * sc, x + 0.70 * sc):
            mb.box(xx - 0.04, xx + 0.04, y - 0.60 * sc, y + 0.60 * sc, z, z + 0.14, "steel", skip=("bottom",))
            if stage == 0:
                mb.box(xx - 0.025, xx + 0.025, y + 0.48 * sc, y + 0.58 * sc, z + 0.14, z + 0.85 * sc, "steel")
        slope_box(mb, (x - 0.80 * sc, x + 0.80 * sc, y - 0.65 * sc, y + 0.65 * sc, z + 0.16, z + 0.23),
                  "solar", 1, 0.65 * sc)
        # 온수기 저장 탱크 + 지지 새들 + 배관
        part = K.MeshBuilder(mb.atlas)
        ring = [(0.22 * sc * np.cos(t * np.pi / 5), 0.22 * sc * np.sin(t * np.pi / 5)) for t in range(10)]
        K.volume_prism(mb.atlas, ring, 1.7 * sc, wall="tank", roof="tank", mb=part)
        part.verts = [(x - 0.85 * sc + vz, y + 0.65 * sc + vy, z + 1.0 * sc - vx) for vx, vy, vz in part.verts]  # 회전(행렬식 +1)이라 면 방향 유지
        mb.merge(part)
        if stage == 0:
            for px in (x - 0.86 * sc, x + 0.86 * sc):
                mb.box(px - 0.025, px + 0.025, y + 0.55 * sc, y + 0.65 * sc, z, z + 1.0 * sc, "steel", skip=("bottom",))


def roof_objects(mb, spec, h, stage):
    if stage == 2:
        return
    x, y = 1.2 + (spec.seed % 3) * 0.45, 2.0 + (spec.seed % 2) * 0.8
    z = h + 0.12
    _draw_single_roof_prop(mb, spec.roof_prop, x, y, z, stage, scale=1.0)

    # 옥상 소품 밀도 2배 보강: 시드별 보조 소품 + 옥상 환기팬/배기덕트 + 배관·발판
    if stage == 0:
        props_all = ("rack", "platform", "jars", "dish", "solar")
        sec_idx = (props_all.index(spec.roof_prop) + 2 + (spec.seed % 2)) % len(props_all)
        sec_kind = props_all[sec_idx]
        sx = -spec.width / 2 + 1.45 + (spec.seed % 2) * 0.35
        sy = 1.75 + ((spec.seed + 1) % 2) * 0.85
        _draw_single_roof_prop(mb, sec_kind, sx, sy, z, stage, scale=0.82)

        # 옥상 버섯형 환기팬(8각 후드) + 배기 덕트 박스
        vx = -spec.width / 2 + 1.15
        vy = (spec.depth - 3.6) if not spec.notch else (spec.depth - 3.5)
        mb.box(vx - 0.28, vx + 0.28, vy - 0.28, vy + 0.28, z, z + 0.18, "cement", skip=("bottom",))
        mb.box(vx - 0.18, vx + 0.18, vy - 0.18, vy + 0.18, z + 0.18, z + 0.42, "roof_equipment")
        hood = [(vx + 0.32 * np.cos(t * np.pi / 4), vy + 0.32 * np.sin(t * np.pi / 4)) for t in range(8)]
        K.volume_prism(mb.atlas, hood, 0.12, z0=z + 0.42, wall="steel", roof="tank", mb=mb)

        # 옥상 보조 화분통(테라코타/목재 틀, plant/soil 태그 미사용)
        px0 = -0.35 if spec.notch else 0.15
        mb.box(px0, px0 + 0.90, 0.55, 1.05, z, z + 0.34, "wood", skip=("bottom",))
        mb.box(px0 + 0.06, px0 + 0.84, 0.61, 0.99, z + 0.34, z + 0.38, "cement")
        for jx in (px0 - 0.45, px0 + 1.25):
            jring = [(jx + 0.16 * np.cos(t * np.pi / 4), 0.80 + 0.16 * np.sin(t * np.pi / 4)) for t in range(8)]
            K.volume_prism(mb.atlas, jring, 0.32, z0=z, wall="jar", roof="jar", mb=mb)

        # 옥상 보일러/설비 함 + 배관 + 디딤석 + 옥탑 TV 안테나 마스트
        ux = -0.55 if spec.notch else -0.05
        uy = spec.depth - 1.35
        mb.box(ux - 0.36, ux + 0.36, uy - 0.24, uy + 0.24, z, z + 0.92, "roof_equipment", skip=("bottom",))
        mb.box(ux - 0.38, ux + 0.38, uy - 0.26, uy + 0.26, z + 0.92, z + 0.97, "tank")
        mb.box(ux - 0.30, ux + 0.30, uy - 0.26, uy - 0.24, z + 0.08, z + 0.84, "frame")
        # 옥상 디딤석 패드 (계단실 문 -> 중앙)
        hx = 0.3 if spec.notch else -2.7
        for si in range(4):
            py = spec.depth - 2.95 - si * 0.65
            mb.box(hx + 0.72, hx + 1.38, py - 0.22, py + 0.22, h + 0.08, h + 0.13, "cement", skip=("bottom",))
        # 옥탑 안테나 마스트
        ax_m, ay_m = hx + 2.05, spec.depth - 0.85
        mb.box(ax_m - 0.025, ax_m + 0.025, ay_m - 0.025, ay_m + 0.025, h + 1.98, h + 3.45, "steel")
        for az, aw in ((h + 2.85, 0.42), (h + 3.10, 0.34), (h + 3.32, 0.24)):
            mb.box(ax_m - aw, ax_m + aw, ay_m - 0.015, ay_m + 0.015, az - 0.015, az + 0.015, "steel")
            mb.box(ax_m - 0.015, ax_m + 0.015, ay_m - aw * 0.55, ay_m + aw * 0.55, az - 0.015, az + 0.015, "steel")


def _add_ac_unit(mb, axis, c, side, pos, z0, stage, duct_to_z=None):
    """외벽 실외기 본체 + 팬 그릴/슈라우드 + L-앵글 브래킷 + 냉매 배관/덕트 커버."""
    K.axbox(mb, axis, c, side, pos - 0.46, pos + 0.46, 0.10, 0.46, z0, z0 + 0.62, "roof_equipment")
    K.paint(mb, axis, c + side * 0.46, side, pos - 0.41, pos + 0.41, z0 + 0.05, z0 + 0.57, "equipment_face")
    if stage == 0:
        # 상단 덮개 캡 + 측면 서비스 박스 + 원형(8각) 팬 슈라우드 링
        K.axbox(mb, axis, c, side, pos - 0.47, pos + 0.47, 0.09, 0.47, z0 + 0.62, z0 + 0.65, "tank")
        K.axbox(mb, axis, c, side, pos + 0.46, pos + 0.50, 0.14, 0.38, z0 + 0.08, z0 + 0.42, "frame")
        fc = (pos - 0.12, c + side * 0.46, z0 + 0.31) if axis == "y" else (c + side * 0.46, pos - 0.12, z0 + 0.31)
        _add_oct_tube(mb, fc, (fc[0] + (0 if axis == "y" else side * 0.03),
                               fc[1] + (side * 0.03 if axis == "y" else 0), fc[2]), 0.20, "steel", n=8)
        for pp in (pos - 0.34, pos + 0.34):
            K.axbox(mb, axis, c, side, pp - 0.025, pp + 0.025, 0.02, 0.48, z0 - 0.06, z0 - 0.01, "steel")
            K.axbox(mb, axis, c, side, pp - 0.025, pp + 0.025, 0.01, 0.06, z0 - 0.32, z0 - 0.06, "steel")
        K.paint(mb, axis, c, side, pos - 0.38, pos + 0.38, max(0.76, z0 - 0.72), z0 - 0.08, "rust")
        # 냉매 배관 + 외벽 덕트 커버
        dz_top = duct_to_z if duct_to_z is not None else (z0 + 0.85)
        K.axbox(mb, axis, c, side, pos + 0.46, pos + 0.56, 0.01, 0.09, min(z0 + 0.18, dz_top), max(z0 + 0.45, dz_top), "frame")
        K.axbox(mb, axis, c, side, pos + 0.47, pos + 0.56, 0.09, 0.22, z0 + 0.16, z0 + 0.24, "steel")


def living_details(mb, spec, stage):
    if stage == 2:
        return
    w, d = spec.width, spec.depth
    # 1) 뒷벽 1층 실외기
    y = d if not spec.notch else d - 2.6
    cx = 0.2 if not spec.notch else -w / 2 + 1.3
    _add_ac_unit(mb, "y", y, 1, cx, 1.85, stage, duct_to_z=2.75)

    # 2) 좌측 외벽 2층 중앙(창 사이 빈 벽) 실외기 + 냉매 덕트 커버
    _add_ac_unit(mb, "x", -w / 2, -1, 4.35, spec.floor_h + 1.55, stage, duct_to_z=spec.floor_h + 2.55)

    # 3) 시드/시대에 따른 3번째 실외기 (A01, 80s, 90s 등)
    if spec.seed % 3 != 2 or spec.era != "70s":
        if spec.notch:
            _add_ac_unit(mb, "x", -w / 2, -1, 4.35, 1.75, stage, duct_to_z=spec.floor_h + 1.55)
        else:
            _add_ac_unit(mb, "y", d, 1, 0.2, spec.floor_h + 1.80, stage, duct_to_z=spec.floor_h + 2.65)

    if stage == 0:
        # 정면 빈 벽띠의 노란 가스관·계량기·고정 클램프
        gx = -0.82
        mb.box(gx - 0.024, gx + 0.024, -0.11, -0.055, 0.18, spec.floor_h + 0.40, "gas")
        mb.box(gx - 0.09, gx + 0.09, -0.14, -0.04, 1.05, 1.38, "cement")
        mb.box(gx - 0.35, gx + 0.18, -0.145, -0.09, 0.28, 0.33, "gas")
        for cz in (0.65, 1.85, 2.88):
            mb.box(gx - 0.045, gx + 0.045, -0.12, -0.01, cz - 0.02, cz + 0.02, "steel")
        # 전기 계량기함 + 배관 (우측 대문 기둥/현관 우측 벽)
        ex = 0.92 if not spec.shop else 0.78
        mb.box(ex - 0.11, ex + 0.11, -0.11, 0.0, 1.32, 1.68, "roof_equipment")
        mb.box(ex - 0.08, ex + 0.08, -0.12, -0.105, 1.48, 1.60, "frame")
        mb.box(ex - 0.02, ex + 0.02, -0.07, -0.01, 1.68, spec.floor_h - 0.1, "steel")

    # 썬라이트 차양은 불투명 청록 면과 외곽 프레임.
    if not spec.shop:
        slope_box(mb, (-1.1, 1.1, -1.00, -0.02, 2.42, 2.48), "awning", 1, 0.22)
        if stage == 0:
            for xx in (-1.08, 0, 1.08):
                slope_box(mb, (xx - 0.022, xx + 0.022, -1.00, -0.02, 2.485, 2.52), "frame", 1, 0.22)
    else:
        slope_box(mb, (-w * 0.44, w * 0.44, -1.15, -0.02, 2.51, 2.57), "awning", 1, 0.36)
        mb.box(-w * 0.44, w * 0.44, -1.18, -1.15, 2.32, 2.57, "awning")
        mb.box(-w * 0.35, w * 0.35, -0.08, -0.015, 2.93, 3.20, {"front": "sign", "default": "steel"})


def build_stage(spec, a, stage):
    mb = K.MeshBuilder(a, split_tiles=stage == 0)
    wins = K.WindowSet()
    w, d, h = spec.width, spec.depth, spec.floors * spec.floor_h
    x0, x1 = -w / 2, w / 2
    if spec.notch:
        ring = [(x0, 0), (x1, 0), (x1, d), (x0 + 2.6, d), (x0 + 2.6, d - 2.6), (x0, d - 2.6)]
        inner = [(x0 + 0.24, 0.24), (x1 - 0.24, 0.24), (x1 - 0.24, d - 0.24),
                 (x0 + 2.84, d - 0.24), (x0 + 2.84, d - 2.84), (x0 + 0.24, d - 2.84)]
        walls = [("y", 0, -1, x0, x1), ("x", x1, 1, 0, d),
                 ("y", d, 1, x0 + 2.6, x1), ("x", x0 + 2.6, -1, d - 2.6, d),
                 ("y", d - 2.6, 1, x0, x0 + 2.6), ("x", x0, -1, 0, d - 2.6)]
    else:
        ring = [(x0, 0), (x1, 0), (x1, d), (x0, d)]
        inner = [(x0 + 0.24, 0.24), (x1 - 0.24, 0.24), (x1 - 0.24, d - 0.24), (x0 + 0.24, d - 0.24)]
        walls = [("y", 0, -1, x0, x1), ("y", d, 1, x0, x1),
                 ("x", x0, -1, 0, d), ("x", x1, 1, 0, d)]
    # 매스 코어가 창 뒤에 있고 별도 외벽 셸에 실제 개구부가 있다.
    meta = K.volume_prism(a, inner, h, volume_id="house", wall=spec.finish, roof="roof", mb=mb)
    if stage < 2:
        K.volume_prism(a, ring, 0.15, z0=0.0, wall="plinth", roof="cement", mb=mb)
    K.volume_prism(a, ring, 0.18, z0=h - 0.1, wall=spec.finish, roof="roof", mb=mb)
    coping_ov = 0.34
    for axis, c, side, lo, hi in walls:
        facade(mb, wins, spec, axis, c, side, stage, lo, hi)
        pa, pb = (lo + 0.18, hi - 0.18) if axis == "x" else (lo, hi)
        if stage == 2:
            K.axbox(mb, axis, c, side, pa, pb, -0.18, 0, h + 0.08, h + 0.62,
                    {"default": spec.finish, "top": "cement"}, skip=("bottom",))
        else:
            K.axbox(mb, axis, c, side, pa, pb, -0.18, 0, h + 0.08, h + 0.55, spec.finish)
            # 파라펫 코핑 확장 (0.34m 외벽 밖 내밀기 + 하부 물끊기 soffit/drip lip)
            is_notch_y = spec.notch and axis == "y" and abs(c - (d - 2.6)) < 1e-6
            is_notch_x = spec.notch and axis == "x" and abs(c - (x0 + 2.6)) < 1e-6
            if axis == "y":
                ca, cb = (lo - coping_ov, hi - coping_ov) if is_notch_y else (lo - coping_ov, hi + coping_ov)
            else:
                ca, cb = (lo - 0.20, hi - 0.20) if is_notch_x else (lo + 0.20, hi - 0.20)
            K.axbox(mb, axis, c, side, ca, cb, -0.20, coping_ov, h + 0.55, h + 0.63, "cement")
            # 하부 물끊기 (drip lip) + 소핏 단차
            if axis == "y":
                da, db = (lo - coping_ov, hi - (coping_ov - 0.08)) if is_notch_y else (lo - coping_ov, hi + coping_ov)
            else:
                da, db = (lo + coping_ov, hi - coping_ov) if is_notch_x else (lo + coping_ov, hi - coping_ov)
            K.axbox(mb, axis, c, side, da, db, coping_ov - 0.08, coping_ov, h + 0.50, h + 0.55, "cement", skip=("top",))
            if stage == 0:
                K.axbox(mb, axis, c, side, ca, cb - (0.02 if is_notch_y else 0), -0.20, coping_ov + 0.02, h + 0.63, h + 0.66, "cement")
                if axis == "y":
                    sa, sb = (lo - (coping_ov - 0.08), hi - coping_ov) if is_notch_y else (lo - (coping_ov - 0.08), hi + (coping_ov - 0.08))
                else:
                    sa, sb = (lo + (coping_ov - 0.08), hi - (coping_ov - 0.08)) if is_notch_x else (lo + (coping_ov - 0.08), hi - (coping_ov - 0.08))
                K.axbox(mb, axis, c, side, sa, sb, 0.01, coping_ov - 0.08, h + 0.525, h + 0.55, "cement", skip=("top",))
        if spec.eaves:
            part = K.MeshBuilder(a, split_tiles=stage == 0)
            is_notch_y = spec.notch and axis == "y" and abs(c - (d - 2.6)) < 1e-6
            if axis == "y":
                ea, eb = (lo - 0.48, hi - 0.48) if is_notch_y else (lo - 0.48, hi + 0.48)
            else:
                ea, eb = lo + 0.48, hi - 0.48
            K.axbox(part, axis, c, side, ea, eb, 0.01, 0.48, h - 0.08, h + 0.03, "clay")
            if stage < 2:
                # 기와 처마 하부 물끊기 턱 (막새 림)
                K.axbox(part, axis, c, side, ea, eb, 0.42, 0.49, h - 0.12, h - 0.08, "clay", skip=("top",))
            if stage == 0:
                # 목재 서까래 + 벽측 처마 도리
                n_raf = max(4, int(round((eb - ea) / 0.52)))
                for r_i in range(1, n_raf):
                    ra = ea + (eb - ea) * r_i / n_raf
                    K.axbox(part, axis, c, side, ra - 0.03, ra + 0.03, 0.08, 0.44, h - 0.15, h - 0.08, "wood", skip=("top",))
                K.axbox(part, axis, c, side, ea + 0.05, eb - 0.05, 0.015, 0.08, h - 0.16, h - 0.08, "wood", skip=("top",))
            part.verts = [(vx, vy, vz - side * ((vx, vy)[0 if axis == "x" else 1] - c) * 0.65)
                          for vx, vy, vz in part.verts]
            mb.merge(part)
    if stage == 0:
        # 8각 홈통·선홈통 4개소 (좌측 전/후 + 후면 우측 + 전면 좌측) 및 처마 물받이
        z_ds_top = (h - 0.44) if spec.eaves else (h + 0.34)
        eave_out = 0.34 if spec.eaves else 0.14
        _add_downspout(mb, "x", x0, -1, 0.35, 0.16, z_ds_top, eave_out=eave_out)
        _add_downspout(mb, "x", x0, -1, (d - 2.6 - 0.35) if spec.notch else (d - 0.35), 0.16, z_ds_top, eave_out=eave_out)
        _add_downspout(mb, "y", d, 1, x1 - 0.35, 0.16, z_ds_top, eave_out=eave_out)
        _add_downspout(mb, "y", 0, -1, x0 + 0.35, 0.16, z_ds_top, eave_out=eave_out)
        # 처마/파라펫 물받이 홈통 띠 + 고정 브래킷
        gutter_z = (h - 0.40) if spec.eaves else (h + 0.44)
        gutter_o = 0.51 if spec.eaves else 0.22  # 기와 처마 끝(0.49) 바깥
        gx_hi = (d - 2.90) if spec.notch else (d - 0.25)
        K.axbox(mb, "x", x0, -1, 0.25, gx_hi, gutter_o, gutter_o + 0.09, gutter_z, gutter_z + 0.08, "steel")
        for gy in np.linspace(0.55, gx_hi - 0.3, 6):
            K.axbox(mb, "x", x0, -1, gy - 0.02, gy + 0.02, 0.015, gutter_o + 0.09, gutter_z - 0.03, gutter_z, "steel")
        gy_lo = (x0 + 2.8) if spec.notch else (x0 + 0.25)
        K.axbox(mb, "y", d, 1, gy_lo, x1 - 0.25, gutter_o, gutter_o + 0.09, gutter_z, gutter_z + 0.08, "steel")
        for gx in np.linspace(gy_lo + 0.3, x1 - 0.55, 6):
            K.axbox(mb, "y", d, 1, gx - 0.02, gx + 0.02, 0.015, gutter_o + 0.09, gutter_z - 0.03, gutter_z, "steel")
        # 옥상 내측 배수 드레인 스커퍼 4개소
        for sx_c, sy_c in ((x0 + 0.32, 0.32), (x1 - 0.32, 0.32), (x1 - 0.32, d - 0.32)):
            mb.box(sx_c - 0.12, sx_c + 0.12, sy_c - 0.12, sy_c + 0.12, h + 0.08, h + 0.14, "steel", skip=("bottom",))
        # 1~2층 층간 돌출 띠(Belt course, 발코니·계단 구간 회피)
        bz0, bz1 = spec.floor_h - 0.09, spec.floor_h + 0.01
        K.axbox(mb, "x", x0, -1, 0.50, (d - 2.6 - 0.50) if spec.notch else (d - 0.50), 0.0, 0.045, bz0, bz1, "cement")
        K.axbox(mb, "y", d, 1, (x0 + 2.85) if spec.notch else (x0 + 0.50), x1 - 0.50, 0.0, 0.045, bz0, bz1, "cement")

    hx = 0.3 if spec.notch else -2.7
    if stage == 2:
        mb.box(hx, hx + 2.3, d - 2.5, d - 0.5, h + 0.08, h + 1.98, {"default": spec.addon, "top": "cement"})
    else:
        mb.box(hx, hx + 2.3, d - 2.5, d - 0.5, h + 0.08, h + 1.85, spec.addon)
        mb.box(hx - 0.12, hx + 2.42, d - 2.62, d - 0.38, h + 1.85, h + 1.98, "cement")
        if stage == 0:
            mb.box(hx - 0.14, hx + 2.44, d - 2.64, d - 0.36, h + 1.81, h + 1.85, "cement", skip=("top",))
            K.axbox(mb, "y", d - 2.5, -1, hx + 0.45, hx + 1.65, 0.0, 0.38, h + 1.76, h + 1.83, "steel")
            # 옥탑 출입구 발판 + 측면 환기 루버 + 배기 파이프
            mb.box(hx + 0.55, hx + 1.55, d - 2.92, d - 2.5, h + 0.08, h + 0.15, "cement", skip=("bottom",))  # 물탱크 기초(h+0.16)와 높이 분리
            mb.box(hx + 2.30, hx + 2.34, d - 1.75, d - 1.15, h + 1.15, h + 1.55, "equipment_face")
            mb.box(hx + 0.30, hx + 0.40, d - 1.00, d - 0.90, h + 1.98, h + 2.45, "steel")
            mb.box(hx + 0.25, hx + 0.45, d - 1.05, d - 0.85, h + 2.45, h + 2.51, "tank")
    if stage < 2:
        K.axbox(mb, "y", d - 2.5, -1, hx + 0.6, hx + 1.5, 0, 0.03, h + 0.08, h + 1.75, "door")
        K.feature_roof_equipment(meta, "house", size=(0.9, 0.65), height=0.62,
                                 center=(-0.1, d - 3.1) if spec.notch else (2.5, d - 2), quality_stage=stage)
    if spec.tank:
        n = 12 if stage == 0 else 6
        cx, cy = 1.7, d - 3.45
        z = h + (0.36 if stage == 0 else 0.22)
        if stage == 0:
            mb.box(cx - 0.78, cx + 0.78, cy - 0.78, cy + 0.78, h + 0.08, h + 0.16, "cement", skip=("bottom",))
            for lx in (cx - 0.48, cx + 0.48):
                for ly in (cy - 0.48, cy + 0.48):
                    mb.box(lx - 0.035, lx + 0.035, ly - 0.035, ly + 0.035, h + 0.16, z - 0.05, "steel", skip=("bottom",))
            mb.box(cx - 0.52, cx + 0.52, cy - 0.52, cy + 0.52, z - 0.05, z, "steel")
        ring = [(cx + 0.66 * np.cos(t * 2 * np.pi / n), cy + 0.66 * np.sin(t * 2 * np.pi / n)) for t in range(n)]
        K.volume_prism(a, ring, 1.1, z0=z, wall="tank", roof="tank", mb=mb)
        if stage == 0:
            for zz in (z + 0.12, z + 0.55, z + 0.94):
                collar = [(cx + 0.69 * np.cos(t * 2 * np.pi / n), cy + 0.69 * np.sin(t * 2 * np.pi / n)) for t in range(n)]
                K.volume_prism(a, collar, 0.04, z0=zz, wall="tank", roof="tank", mb=mb)
            hatch = [(cx + 0.24 * np.cos(t * 2 * np.pi / 8), cy + 0.24 * np.sin(t * 2 * np.pi / 8)) for t in range(8)]
            K.volume_prism(a, hatch, 0.08, z0=z + 1.1, wall="tank", roof="tank", mb=mb)
            cap = [(cx + 0.52 * np.cos(t * 2 * np.pi / n), cy + 0.52 * np.sin(t * 2 * np.pi / n)) for t in range(n)]
            K.volume_prism(a, cap, 0.05, z0=z + 1.1, wall="tank", roof="tank", mb=mb)
            # 물탱크 수직 배관 + 옥상 수평 헤더 배관 + 사다리 + 밸브 박스
            mb.box(cx + 0.54, cx + 0.62, cy - 0.04, cy + 0.04, h + 0.08, z + 1.22, "steel")
            mb.box(cx + 0.51, cx + 0.65, cy - 0.07, cy + 0.07, h + 0.45, h + 0.56, "steel")
            mb.box(cx - 0.64, cx + 0.54, cy - 0.035, cy + 0.035, h + 0.18, h + 0.24, "steel")
            mb.box(cx - 0.72, cx - 0.64, cy - 0.65, cy + 0.04, h + 0.18, h + 0.24, "steel")
            for sx in (cx - 0.16, cx + 0.16):
                mb.box(sx - 0.02, sx + 0.02, cy - 0.74, cy - 0.70, h + 0.08, z + 1.15, "steel", skip=("bottom",))
            for rz in (h + 0.40, h + 0.75, h + 1.10, z + 1.05):
                mb.box(cx - 0.16, cx + 0.16, cy - 0.735, cy - 0.705, rz - 0.015, rz + 0.015, "steel")
    if spec.stairs and spec.floors == 2:
        sx0, sx1 = w / 2 + 0.08, w / 2 + 1.25
        count = 17 if stage == 0 else (6 if stage == 1 else 1)
        if stage == 2:
            slope_box(mb, (sx0, sx1, 0.25, 5.10, 0.02, 0.10), "steel", 1, spec.floor_h - 0.10)
        else:
            for i in range(count):
                y0, y1 = 0.25 + i * 4.85 / count, 0.25 + (i + 1) * 4.85 / count
                z = (i + 1) * spec.floor_h / count
                mb.box(sx0 + 0.06, sx1 - 0.06, y0, y1, max(0, z - 0.13), z, "steel")  # 측판 사이
            # 계단 좌우 경사 측판(스트링거 빔)
            for bx0, bx1 in ((sx0, sx0 + 0.06), (sx1 - 0.06, sx1)):
                slope_box(mb, (bx0, bx1, 0.25, 5.10, 0.0, 0.16), "steel", 1, spec.floor_h - 0.10)
        mb.box(w / 2, sx1, 5.10, 6.2, spec.floor_h - 0.14, spec.floor_h, "steel")
        for xx in (sx0 + 0.04, sx1 - 0.04):
            if stage < 2:
                for dz in (0.48, 0.96):
                    beam = K.MeshBuilder(a)
                    beam.box(xx - 0.026, xx + 0.026, 0.25, 5.1, dz, dz + 0.055, "steel")
                    beam.verts = [(x, y, z + (y - 0.25) * spec.floor_h / 4.85) for x, y, z in beam.verts]
                    mb.merge(beam)
            if stage == 0:
                for i in range(9):
                    y = 0.25 + i * 4.85 / 8
                    z = i * spec.floor_h / 8
                    mb.box(xx - 0.03, xx + 0.03, y - 0.03, y + 0.03, z + 0.02, z + 0.99, "steel")
        if stage < 2:
            # 2층 계단 참 안전 난간 (외측·후면·전면) + 하부 지지 기둥/가새
            mb.box(sx1 - 0.06, sx1, 5.1, 6.2, spec.floor_h + 0.94, spec.floor_h + 1.02, "steel")
            mb.box(w / 2, sx1 - 0.06, 6.14, 6.2, spec.floor_h + 0.94, spec.floor_h + 1.02, "steel")
            if stage == 0:
                mb.box(sx1 - 0.05, sx1, 5.1, 6.2, spec.floor_h + 0.48, spec.floor_h + 0.53, "steel")
                mb.box(w / 2, sx1 - 0.05, 6.15, 6.2, spec.floor_h + 0.48, spec.floor_h + 0.53, "steel")
                for py in (5.135, 5.65, 6.17):
                    mb.box(sx1 - 0.055, sx1 - 0.005, py - 0.025, py + 0.025, spec.floor_h, spec.floor_h + 0.94, "steel")
                mb.box(w / 2 + 0.4, w / 2 + 0.46, 6.145, 6.195, spec.floor_h, spec.floor_h + 0.94, "steel")
                mb.box(sx1 - 0.16, sx1 - 0.08, 5.2, 6.1, spec.floor_h * 0.48, spec.floor_h * 0.52, "steel")
            for yy in (5.2, 6.1):
                mb.box(sx1 - 0.18, sx1 - 0.06, yy - 0.06, yy + 0.06, 0.0, spec.floor_h - 0.14, "steel", skip=("bottom",))
    # 담장·대문은 구조물. 조경·화분·화단 틀·흙면은 메시 금지.
    if spec.fence:
        half = w / 2 + 2
        for fx0, fx1, fy0, fy1 in ((-half, -half + 0.18, -2.32, d + 1.42),
                                   (half - 0.18, half, -2.32, d + 1.42),
                                   (-half, half, d + 1.42, d + 1.6),
                                   (-half, -1.15, -2.5, -2.32), (1.15, half, -2.5, -2.32)):
            mb.box(fx0, fx1, fy0, fy1, 0, 1.15, spec.fence_finish, skip=("bottom",))
            if stage == 0:
                cx0, cx1 = fx0 - 0.03, fx1 + 0.03
                if fx1 - fx0 > 0.5:  # 앞·뒤 담은 옆 담 갓돌(±0.21)에 맞대어 모서리 겹침 방지
                    cx0, cx1 = max(cx0, -half + 0.21), min(cx1, half - 0.21)
                mb.box(cx0, cx1, fy0 - 0.03, fy1 + 0.03, 1.15, 1.21, "cement")
        mb.box(-1.12, 1.12, -2.48, -2.40, 0.10, 1.45, "steel")
        if stage == 0:
            mb.box(-1.12, 1.12, -2.50, -2.38, 1.45, 1.50, "steel")
            for i in range(13):
                x = -1.05 + i * 2.1 / 12
                mb.box(x - 0.02, x + 0.02, -2.51, -2.47, 0.15, 1.45, "steel")
            for hx_g in (-0.98, 0.94):
                for hz_g in (0.35, 1.15):
                    mb.box(hx_g, hx_g + 0.05, -2.52, -2.36, hz_g, hz_g + 0.06, "steel")
            mb.box(-0.08, 0.08, -2.53, -2.35, 0.72, 0.86, "frame")
            mb.box(0.98, 1.26, -2.65, -2.60, 1.18, 1.42, "roof_equipment")
            mb.box(1.03, 1.21, -2.67, -2.65, 1.24, 1.36, "frame")
        for px in (-1.13, 1.13):
            if stage == 2:
                mb.box(px - 0.18, px + 0.18, -2.60, -2.24, 0, 1.73, {"default": "stone", "top": "cement"}, skip=("bottom",))
            else:
                mb.box(px - 0.18, px + 0.18, -2.60, -2.24, 0, 1.65, "stone", skip=("bottom",))
                mb.box(px - 0.20, px + 0.20, -2.62, -2.22, 1.65, 1.73, "cement")
            if stage < 2:
                mb.box(px - 0.09, px + 0.09, -2.50, -2.32, 1.73, 1.88, "lamp")
        if stage < 2:
            # 건물번호판: 1.2 cm 두께 판 + 앞면은 칸의 2:1 띠 전체 (K.paint 는 칸 가운데 절반만 잘라 써서 글자가 잘렸음)
            mb.box(-1.28, -0.98, -2.612, -2.60, 1.24, 1.39, "steel", skip=("front", "back"))
            mb.quad(K.face_pts("y", -2.612, -1, -1.28, -0.98, 1.24, 1.39), mb.atlas.uv_sub("address", 0.0, 0.25, 1.0, 0.75), "address")
            mb.box(1.40, 1.75, -2.65, -2.51, 0.85, 1.12, "steel")
    mb.box(-0.8, 0.8, -0.65, -0.001, 0, 0.16, "stone", skip=("bottom",))
    if stage == 0:
        for rx in (-0.76, 0.72):
            mb.box(rx, rx + 0.04, -0.62, -0.001, 0.82, 0.86, "steel")
            mb.box(rx + 0.005, rx + 0.035, -0.60, -0.56, 0.16, 0.82, "steel")
            mb.box(rx + 0.005, rx + 0.035, -0.10, -0.06, 0.16, 0.82, "steel")
    living_details(mb, spec, stage)
    roof_objects(mb, spec, h, stage)
    if spec.balcony != "none":
        bw = w * 0.34
        fh = spec.floor_h
        if spec.balcony != "enclosed" or stage < 2:
            mb.box(-bw, bw, -0.95, -0.001, fh - 0.14, fh, "cement")
            if stage == 0:
                KX.under_shadow(mb, "y", 0, -1, -bw, bw, fh - 0.19, depth=0.40, layer=3)
            if stage < 2:
                # 발코니 슬래브 하부 턱/물끊기
                mb.box(-bw, bw, -0.96, -0.87, fh - 0.19, fh - 0.14, "cement", skip=("top",))
                mb.box(-bw, -bw + 0.09, -0.87, -0.001, fh - 0.19, fh - 0.14, "cement", skip=("top",))
                mb.box(bw - 0.09, bw, -0.87, -0.001, fh - 0.19, fh - 0.14, "cement", skip=("top",))
        if spec.balcony == "rail":
            if stage < 2:
                mb.box(-bw, bw, -0.95, -0.88, fh, fh + 0.06, "cement", skip=("bottom",))
            mb.box(-bw, bw, -0.96, -0.89, fh + 0.88, fh + 0.94, "steel")
            if stage < 2:
                mb.box(-bw, -bw + 0.06, -0.89, -0.001, fh + 0.88, fh + 0.94, "steel")
                mb.box(bw - 0.06, bw, -0.89, -0.001, fh + 0.88, fh + 0.94, "steel")
                if stage == 0:
                    mb.box(-bw, bw, -0.945, -0.895, fh + 0.45, fh + 0.49, "steel")
                    mb.box(-bw + 0.01, -bw + 0.05, -0.89, -0.001, fh + 0.45, fh + 0.49, "steel")
                    mb.box(bw - 0.05, bw - 0.01, -0.89, -0.001, fh + 0.45, fh + 0.49, "steel")
                    for sy in (-0.48, -0.08):
                        mb.box(-bw + 0.015, -bw + 0.045, sy - 0.02, sy + 0.02, fh, fh + 0.88, "steel")
                        mb.box(bw - 0.045, bw - 0.015, sy - 0.02, sy + 0.02, fh, fh + 0.88, "steel")
                for bx in np.linspace(-bw + 0.04, bw - 0.04, 11 if stage == 0 else 5):
                    mb.box(bx - 0.018, bx + 0.018, -0.94, -0.90, fh + 0.06, fh + 0.88, "steel")
        else:
            if stage == 2:
                mb.box(-bw, bw, -0.95, -0.001, fh - 0.14, fh + 0.76, spec.finish)
            else:
                mb.box(-bw, bw, -0.95, -0.80, fh, fh + 0.76, spec.finish)
                # 옆 난간벽 (앞 난간벽 뒤에 맞댐) — 비어 있어 뒤 벽돌이 보이던 곳
                mb.box(-bw, -bw + 0.12, -0.80, -0.001, fh, fh + 0.76, spec.finish)
                mb.box(bw - 0.12, bw, -0.80, -0.001, fh, fh + 0.76, spec.finish)
            room = 50 if spec.seed % 5 == 1 else 55
            zl0, zl1, zu0, zu1 = fh + 0.83, fh + 1.86, fh + 1.92, fh + 2.36   # 하부 미서기 / 상부 고정창
            for sgn in (-1, 1):
                xo = sgn * bw
                fx0, fx1 = (xo, xo + 0.08) if sgn < 0 else (xo - 0.08, xo)
                if stage == 2:
                    mb.rect(K.face_pts("x", xo, sgn, -0.95, -0.001, fh + 0.76, fh + 2.42), "frame")
                    continue
                # 옆면 샷시: 모서리 기둥 2 + 상·하 레일 + 가로살, 사이에 유리
                mb.box(fx0, fx1, -0.95, -0.87, fh + 0.76, fh + 2.42, "frame")
                mb.box(fx0, fx1, -0.08, -0.001, fh + 0.76, fh + 2.42, "frame")
                for rz0, rz1 in ((fh + 0.76, zl0), (zl1, zu0), (zu1, fh + 2.42)):
                    mb.box(fx0, fx1, -0.87, -0.08, rz0, rz1, "frame")
                if stage == 0:
                    # 창 면은 한 장(가로살은 유리 2 cm 앞 창틀) — 창 칸 해상도·LOD2 창 예산 유지
                    wins.add_face("x", xo - sgn * 0.04, sgn, -0.87, -0.08, zl0, zu1, 0, room)
                    wins.items[-1]["pts2"] = K.face_pts("x", xo + sgn * 0.02, sgn, -0.87, -0.08, zl0, zu1)
            if stage < 2:
                mb.box(-bw - 0.08, bw + 0.08, -1.03, -0.001, fh + 2.42, fh + 2.51, "cement")
                mb.box(-bw - 0.08, bw + 0.08, -1.03, -0.96, fh + 2.38, fh + 2.42, "cement", skip=("top",))
            else:
                mb.box(-bw, bw, -0.95, -0.001, fh + 2.42, fh + 2.50, "cement")
            if stage == 2:
                mb.rect(K.face_pts("y", -0.951, -1, -bw, bw, fh + 0.76, fh + 2.42), "window_backing")
            else:
                mb.box(-bw + 0.01, bw - 0.01, -0.99, -0.79, fh + 0.75, fh + 0.80, "cement")
                for bz0, bz1 in ((fh + 0.80, zl0), (zu1, fh + 2.42)):   # 하·상 레일
                    mb.box(-bw + 0.08, bw - 0.08, -0.94, -0.85, bz0, bz1, "frame")
                # 상부 고정창 / 하부 미서기 가로살 (유리 앞, 세로살보다 얇게 해 면 겹침 방지)
                mb.box(-bw + 0.08, bw - 0.08, -0.93, -0.855, zl1, zu0, "frame")
            for i in range(6):
                ba = -bw + 0.08 + i * (2 * bw - 0.16) / 6
                bb = -bw + 0.08 + (i + 1) * (2 * bw - 0.16) / 6
                ga, gb = ba + (0.025 if i else 0), bb - (0.025 if i < 5 else 0)
                if stage == 0:
                    wins.add_face("y", -0.84, -1, ga, gb, zl0, zu1, 0, room)
                    wins.items[-1]["pts2"] = K.face_pts("y", -0.97, -1, ga, gb, zl0, zu1)
                if stage < 2 and i:
                    mb.box(ba - 0.025, ba + 0.025, -0.94, -0.85, zl0, zu1, "frame")
    if stage == 0:
        mb.box(0.68, 0.84, -0.12, -0.04, 2.1, 2.23, "lamp")
    return mb, wins


def build_and_export(spec, out_root=None, subobjects=True):
    a = atlas(spec)
    main, wins = build_stage(spec, a, 0)
    l1, _ = build_stage(spec, a, 1)
    l2, _ = build_stage(spec, a, 2)
    folder, result = K.export_asset(spec.name, 1, dict(main=main, lod1=l1, lod2=l2, windows=wins),
                                    a, out_root or K.out_dir_from_argv("output"), lod2_tex=512, lot=spec.lot,
                                    front_yard=2.7, notes=dict(era=spec.era, seed=spec.seed, finish=spec.finish,
                                        balcony=spec.balcony, notch=spec.notch, shop=spec.shop, roof_prop=spec.roof_prop))
    sx, sy = result["pivot_shift"]
    w, d = spec.width, spec.depth
    items = [
        dict(kind="planter", suggest="대문 좌측 사각 화분 (에디터 내장 소품)",
             x=-1.65 + sx, y=-2.05 + sy, z=0, rot_deg=0, scale=[0.55, 0.55, 0.50],
             source="A형 대문 좌측 화분 제안"),
        dict(kind="planter", suggest="대문 우측 사각 화분 (에디터 내장 소품)",
             x=1.65 + sx, y=-2.05 + sy, z=0, rot_deg=0, scale=[0.55, 0.55, 0.50],
             source="A형 대문 우측 화분 제안"),
        dict(kind="flower_bed", suggest="앞마당 좌측 화단 관목·초화 (에디터 Surface/소품)",
             x=-w / 2 - 0.75 + sx, y=-1.20 + sy, z=0, rot_deg=0, scale=[1.2, 0.9, 0.55],
             source="A형 앞마당 좌측 화단 제안"),
        dict(kind="tree", suggest="좌측 마당 정원수(감나무/소형 활엽수)",
             x=-w / 2 - 1.05 + sx, y=(1.8 if spec.notch else 2.4) + sy, z=0, rot_deg=15, scale=[0.75, 0.75, 0.75],
             source="A형 좌측 마당 수목 제안"),
        dict(kind="bicycle", suggest="마당 우측 벽변 자전거 소품 (에디터 내장 소품)",
             x=(w / 2 - 0.35 if spec.shop else 1.85) + sx, y=-1.35 + sy, z=0, rot_deg=85, scale=[1.0, 1.0, 1.0],
             source="A형 마당 자전거 제안"),
        dict(kind="shrub", suggest="뒷마당 담장변 관목",
             x=(0.0 if not spec.notch else -w / 2 + 1.3) + sx, y=d + 0.75 + sy, z=0, rot_deg=0, scale=[1.0, 1.0, 0.8],
             source="A형 뒷마당 관목 제안"),
    ]
    (HERE / "work").mkdir(exist_ok=True)
    content = json.dumps(
        dict(asset=result["asset"], coord="CS2 asset local: x right, y back, z up; metres; pivot applied",
             pivot_shift=[sx, sy], items=items), ensure_ascii=False, indent=2)
    if subobjects:
        for filename in ("subobjects.json", f"subobjects_{result['asset']}.json"):
            (HERE / "work" / filename).write_text(content, encoding="utf-8")
    return folder, result


def self_check():
    finishes, props = set(), set()
    min_m, max_m = 10**9, 0
    for era in ("70s", "80s", "90s"):
        signatures = set()
        for seed in range(12):
            s = seeded(era, seed)
            assert s == seeded(era, seed)
            a = atlas(s)
            meshes = [build_stage(s, a, i) for i in range(3)]
            main, wins = meshes[0]
            counts = [m.tri_count for m, _ in meshes]
            min_m, max_m = min(min_m, counts[0]), max(max_m, counts[0])
            assert 8500 <= counts[0] <= 13800, (era, seed, counts)  # kitext 베벨·옆면·콘크리트 타일 후 8.9~13.3k (위키 저밀도 권장 최대 15k 이내)
            assert counts[1] < counts[0]*0.5, (era, seed, counts)
            assert counts[2] + len(wins.items)*2 <= 500, (era, seed, counts, len(wins.items))
            assert not any("plant" in tag or "soil" in tag for tag in main.tags)
            for face, tag in zip(main.faces, main.tags):
                if tag == "roof":
                    pts = np.array([main.verts[i] for i in face])
                    assert np.ptp(pts[:, 2]) < 1e-6  # 녹색 방수는 수평면뿐
            signatures.add((s.width, s.depth, s.finish, s.balcony, s.notch, s.shop, s.addon, s.roof_prop))
            finishes.add(s.finish)
            props.add(s.roof_prop)
        assert len(signatures) == 12
    assert {"brick", "mosaic", "plaster", "porcelain"} <= finishes
    assert len(props) == 5
    for spec in PRESETS.values():
        a = atlas(spec)
        _, wins = build_stage(spec, a, 0)
        wins.build()
        cell = a.cells["window"]
        ctx = K._CellCtx(384, 384, cell)
        windows(ctx)
        rooms = {}
        for w in wins.items:
            u, v = np.mean(w["uv"], axis=0)
            lit = ctx.emis[int((1 - v) * ctx.h), int(u * ctx.w)] > 0
            rooms.setdefault((w["floor"], w["unit"]), set()).add(lit)
        assert any(cell["emissive"]) and all(len(states) == 1 for states in rooms.values())
        assert set.union(*rooms.values()) == {False, True}, spec.name
    print(f"3시대×12시드 재현성·예산({min_m}~{max_m} tris)·조합·조경 제외 검사 PASS")


if __name__ == "__main__":
    self_check()
