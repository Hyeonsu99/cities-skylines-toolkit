# -*- coding: utf-8 -*-
"""
Parametric Korean Blue-Roof Factory & Rail Depot Generator for Cities: Skylines II.
Targets Daejeon industrial complexes (Daedeok Industrial Complex, Pyeongchon SME Complex,
Daejeon Rail Vehicle Maintenance Depot) using cs2kit.py.
"""
from dataclasses import dataclass, field
import math
import os
import sys
import numpy as np


def _find_kit():
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(4):
        if os.path.exists(os.path.join(d, "cs2kit.py")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("cs2kit.py not found")


sys.path.insert(0, _find_kit())
import cs2kit as K  # noqa: E402


@dataclass
class OfficeSpec:
    enabled: bool = True
    width: float = 13.2
    depth: float = 4.4
    height: float = 7.0
    align: str = "left"          # "left", "right", "center", "full"
    door_side: str = "left"      # "left", "right", "center"
    sign_zone: str = "spandrel"  # "spandrel", "fascia"
    parapet_h: float = 0.38


@dataclass
class FactorySpec:
    name_base: str
    level: int = 1
    width: float = 28.0
    depth: float = 33.6
    eave_h: float = 9.3
    ridge_rise: float = 2.15
    gables: int = 1
    roof_overhang: float = 0.55
    roof_t: float = 0.26
    plinth_h: float = 0.85
    roof_color: tuple = (38, 86, 152)
    wall_color: tuple = (224, 226, 228)
    accent_color: tuple = (36, 74, 134)
    lot: tuple = None
    front_yard: float = 4.0
    office: OfficeSpec = field(default_factory=OfficeSpec)
    front_shutters: int = 2
    back_shutters: int = 1
    side_shutters: int = 1
    shutter_size: tuple = (4.3, 4.7)  # (width, height)
    through_tracks: bool = False  # True for rail vehicle maintenance shed
    track_bays: int = 2
    track_door_size: tuple = (5.2, 6.6)
    clerestory_bays: int = 5
    skylight_rows: int = 2
    skylight_pattern: str = "paired"      # "paired" | "staggered" | "twin_varied"
    skylight_u: tuple = (0.34, 0.50)      # left-slope u range (0=eave, 1=ridge)
    skylight_fill: float = 0.62
    ventilators: int = 5
    vent_radius: float = 0.30             # turbine rotor radius (0.25=Ø500, 0.30=Ø600, 0.35=Ø750)
    vent_pattern: str = "ridge_even"      # "ridge_even" | "ridge_rear_bias" | "ridge_staggered"
    roof_box_fans: int = 0
    roof_monitor: bool = False
    solar_arrays: bool = False
    gable_louvers: bool = True
    side_equipment: bool = True
    side_equipment_kind: str = "factory"  # "factory" | "depot"
    sign_key: str = "mid"


PRESETS = {
    "small": FactorySpec(
        name_base="BlueFactorySmall",
        level=1,
        width=20.0,
        depth=22.0,       # +4.0m office wing = 26.0m depth (TASK.md 20 x 26 x 10.6 m, lot 3x4)
        eave_h=7.8,
        ridge_rise=1.75,  # ~1:5.7 slope (9.9 deg), total height ~10.45m
        gables=1,
        roof_overhang=0.50,
        roof_color=(44, 96, 162),
        wall_color=(228, 229, 230),
        accent_color=(40, 82, 144),
        lot=(3, 4),
        office=OfficeSpec(enabled=True, width=9.8, depth=4.0, height=6.6,
                          align="left", door_side="left", sign_zone="spandrel", parapet_h=0.34),
        front_shutters=1,
        back_shutters=0,
        side_shutters=1,
        shutter_size=(4.0, 4.4),
        clerestory_bays=4,
        skylight_rows=2,
        skylight_pattern="paired",
        skylight_u=(0.28, 0.43),
        skylight_fill=0.58,
        ventilators=3,
        vent_radius=0.25,
        vent_pattern="ridge_even",
        roof_box_fans=0,
        side_equipment=True,
        side_equipment_kind="factory",
        sign_key="small",
    ),
    "mid": FactorySpec(
        name_base="BlueFactoryMid",
        level=1,
        width=28.0,
        depth=33.6,       # +4.4m office wing = 38.0m depth (TASK.md 28 x 38 x 12.6 m, lot 4x6)
        eave_h=9.3,
        ridge_rise=2.15,  # ~1:6.5 slope (8.7 deg), total height ~12.4m
        gables=1,
        roof_overhang=0.55,
        roof_color=(36, 84, 150),
        wall_color=(222, 225, 228),
        accent_color=(34, 72, 132),
        lot=(4, 6),
        office=OfficeSpec(enabled=True, width=13.2, depth=4.4, height=7.0,
                          align="right", door_side="right", sign_zone="spandrel", parapet_h=0.38),
        front_shutters=2,
        back_shutters=1,
        side_shutters=1,
        shutter_size=(4.3, 4.7),
        clerestory_bays=5,
        skylight_rows=4,
        skylight_pattern="staggered",
        skylight_u=(0.38, 0.54),
        skylight_fill=0.66,
        ventilators=4,
        vent_radius=0.30,
        vent_pattern="ridge_rear_bias",
        roof_box_fans=2,
        side_equipment=True,
        side_equipment_kind="factory",
        sign_key="mid",
    ),
    "large": FactorySpec(
        name_base="BlueFactoryLarge",
        level=2,
        width=42.0,
        depth=35.4,       # +4.6m office wing = 40.0m depth (TASK.md 42 x 40 x 13.6 m, lot 6x6)
        eave_h=10.3,
        ridge_rise=2.00,  # ~1:5.25 slope per 21m twin-gable span (10.8 deg), total height ~13.3m
        gables=2,         # Twin-gable blue roof (Daedeok Industrial Complex signature)
        roof_overhang=0.55,
        roof_color=(34, 78, 142),
        wall_color=(218, 222, 226),
        accent_color=(32, 68, 124),
        lot=(6, 6),
        office=OfficeSpec(enabled=True, width=18.0, depth=4.6, height=7.4,
                          align="center", door_side="center", sign_zone="fascia", parapet_h=0.46),
        front_shutters=2,
        back_shutters=2,
        side_shutters=2,
        shutter_size=(4.5, 4.9),
        clerestory_bays=6,
        skylight_rows=3,
        skylight_pattern="twin_varied",
        skylight_u=(0.30, 0.45),
        skylight_fill=0.56,
        ventilators=5,
        vent_radius=0.35,
        vent_pattern="ridge_staggered",
        roof_box_fans=2,
        side_equipment=True,
        side_equipment_kind="factory",
        sign_key="large",
    ),
    "depot": FactorySpec(
        name_base="BlueRailDepot",
        level=1,
        width=26.0,
        depth=55.0,       # TASK.md 26 x 56 x 14.5 m (lot 4x8, signature building)
        eave_h=10.2,
        ridge_rise=2.15,  # ~1:6.0 slope (9.4 deg), with monitor apex ~14.45m
        gables=1,
        roof_overhang=0.55,
        roof_color=(46, 98, 158),
        wall_color=(214, 218, 222),
        accent_color=(38, 78, 136),
        lot=(4, 8),
        office=OfficeSpec(enabled=False),
        front_shutters=0,
        back_shutters=0,
        side_shutters=1,
        shutter_size=(4.3, 4.7),
        through_tracks=True,
        track_bays=2,
        track_door_size=(5.2, 6.6),
        clerestory_bays=8,
        skylight_rows=4,
        skylight_pattern="paired",
        skylight_u=(0.48, 0.64),
        skylight_fill=0.62,
        ventilators=0,
        vent_radius=0.30,
        vent_pattern="ridge_even",
        roof_box_fans=0,
        roof_monitor=True,
        solar_arrays=True,  # Daejeon Rail Vehicle Maintenance Depot rooftop solar PV arrays
        side_equipment=True,
        side_equipment_kind="depot",
        sign_key="depot",
    ),
}


# ---------------------------------------------------------------------------
# Procedural Atlas Painters & Korean Signboard Renderer
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

# Packed signboard bands inside 1024x1024 sign_plate cell: (py0, py1, world_w, world_h, kr_name, en_sub)
SIGN_BANDS = {
    "small": (4, 250, 3.136, 0.68, "들빛산기", "DEULBIT INDUSTRIAL"),
    "mid":   (260, 506, 3.800, 0.68, "세별정밀", "SEBYEOL PRECISION"),
    "large": (516, 762, 5.400, 0.88, "맑은터테크", "MALGEUNTEO TECH"),
    "depot": (772, 1018, 5.000, 0.85, "새솔철도검수", "SAESOL RAIL DEPOT"),
}
SIGN_SUB = {
    k: ("sign_plate", 0.004, 1.0 - (py1 - 2) / 1024.0, 0.996, 1.0 - (py0 + 2) / 1024.0)
    for k, (py0, py1, _w, _h, _kr, _en) in SIGN_BANDS.items()
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


def _render_packed_bands(ctx, cache_tag, band_specs, bg=(22, 50, 94)):
    cache_path = os.path.join(_SIGN_CACHE_DIR, f"{cache_tag}_{ctx.w}x{ctx.h}.npz")
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        if not os.path.exists(cache_path):
            raise RuntimeError(f"PIL unavailable and sign cache missing: {cache_path}")
        with np.load(cache_path) as d:
            ctx.rgb[...] = d["rgb"].astype(np.float32)
            ctx.emis[...] = d["emis"].astype(np.float32)
            ctx.height[...] = d["height"].astype(np.float32)
            if "gloss" in d:
                ctx.gloss[...] = d["gloss"].astype(np.float32)
        return

    sheet = Image.new("RGB", (ctx.w, ctx.h), bg)
    esheet = Image.new("L", (ctx.w, ctx.h), 0)
    hsheet = Image.new("L", (ctx.w, ctx.h), 0)
    gsheet = Image.new("L", (ctx.w, ctx.h), 96)
    sy = ctx.h / 1024.0
    for py0, py1, world_w, world_h, band_bg, draw_fn in band_specs:
        ry0, ry1 = int(round(py0 * sy)), int(round(py1 * sy))
        bh = max(32, ry1 - ry0)
        aspect = world_w / max(world_h, 1e-4)
        ch = 256
        cw = max(256, min(2560, int(round(ch * aspect))))
        im = Image.new("RGB", (cw, ch), band_bg)
        eim = Image.new("L", (cw, ch), 0)
        him = Image.new("L", (cw, ch), 0)
        gim = Image.new("L", (cw, ch), 96)
        draw_fn(
            ImageDraw.Draw(im),
            ImageDraw.Draw(eim),
            ImageDraw.Draw(him),
            ImageDraw.Draw(gim),
            cw,
            ch,
        )
        sheet.paste(im.resize((ctx.w, bh), Image.Resampling.LANCZOS), (0, ry0))
        esheet.paste(eim.resize((ctx.w, bh), Image.Resampling.LANCZOS), (0, ry0))
        hsheet.paste(him.resize((ctx.w, bh), Image.Resampling.LANCZOS), (0, ry0))
        gsheet.paste(gim.resize((ctx.w, bh), Image.Resampling.LANCZOS), (0, ry0))

    rgb_arr = np.asarray(sheet, dtype=np.uint8)
    emis_arr = np.asarray(esheet, dtype=np.float32) / 255.0
    height_arr = (np.asarray(hsheet, dtype=np.float32) / 255.0) * 0.72
    gloss_arr = np.asarray(gsheet, dtype=np.float32) / 255.0
    ctx.rgb[...] = rgb_arr.astype(np.float32)
    ctx.emis[...] = emis_arr
    ctx.height[...] = height_arr
    ctx.gloss[...] = gloss_arr

    os.makedirs(_SIGN_CACHE_DIR, exist_ok=True)
    np.savez(
        cache_path,
        rgb=rgb_arr,
        emis=emis_arr.astype(np.float16),
        height=height_arr.astype(np.float16),
        gloss=gloss_arr.astype(np.float16),
    )


def _preserve_mean_rgb(arr, target_mean):
    """Keep clean white/blue surfaces from turning dingy gray after multiplicative weathering."""
    cur_mean = np.mean(arr, axis=(0, 1), keepdims=True)
    scale = np.where(cur_mean > 1.0, target_mean / cur_mean, 1.0)
    return arr * scale


def _periodic_weather(ctx, amount=0.018, cycles_u=4, cycles_v=4, seed=11):
    """High-frequency seamless periodic tonal modulation (uniform across LOD1/LOD2 mid-tile UVs)."""
    rng = np.random.default_rng(seed)
    phase_u = rng.uniform(0.0, 2.0 * math.pi, size=2)
    phase_v = rng.uniform(0.0, 2.0 * math.pi, size=2)
    w = (
        0.50 * np.sin(2.0 * math.pi * cycles_u * ctx.u + phase_u[0])
        + 0.50 * np.cos(2.0 * math.pi * cycles_v * ctx.v + phase_v[0])
    )
    k = 1.0 - amount * (0.5 + 0.5 * w)
    ctx.rgb *= k[..., None]
    ctx.gloss *= (1.0 - 0.12 * amount * (0.5 + 0.5 * w))


def _paint_corrugated_blue_roof(ctx):
    """Long-span trapezoidal color-steel roof sheets (1000mm effective width, 250mm ribs, slope-aligned stains)."""
    mx, my = ctx.meters()
    base_mean = ctx.rgb[:1, :1, :].copy()
    rib = np.clip(np.cos(2.0 * math.pi * my / 0.25) * 1.45, -1.0, 1.0)
    trough = np.clip(-rib, 0.0, 1.0)

    # Fine coated-steel grain + isotropic weathering blotches (wrapped smoothly at tile edges)
    ctx.grain(amp=1.8, scale_px=3, height=0.05, seed=121)
    rgb_pre_stain = ctx.rgb.copy()
    ctx.stains(amount=0.055, scale_px=80, streaks=0.0, seed=111)
    v_wrap = np.sin(math.pi * ctx.v) ** 0.30
    ctx.rgb = rgb_pre_stain + (ctx.rgb - rgb_pre_stain) * v_wrap[..., None]

    # Per-variant slope-direction (u/mx) rib streaks + 1m sheet tonal variation
    sheet_id = np.floor(my / 1.0).astype(np.int32) % 4
    rib_streak = np.zeros((ctx.h, ctx.w), np.float32)
    sheet_shift = np.zeros((ctx.h, ctx.w), np.float32)
    for vi in range(ctx.variants):
        m = ctx.vi == vi
        rng = np.random.default_rng(119 + vi * 29)
        tones = rng.normal(0.0, 1.8, size=4).astype(np.float32)
        sheet_shift[m] = tones[sheet_id[m]]
        n_slope = ctx.noise(scale_px=14, amp=1.0, octaves=2, seed=220 + vi)
        # Project along axis=1 (u/mx = eave-to-ridge rib direction), modulated softly along u
        u_env = 0.72 + 0.28 * np.sin(2.0 * math.pi * ctx.vu + vi * 1.7)
        streak_u = np.repeat(n_slope.mean(axis=1, keepdims=True), ctx.w, axis=1) * u_env
        rib_streak[m] = streak_u[m]

    streak_k = np.clip(0.5 + 0.5 * rib_streak, 0.0, 1.0)
    roof_stain = 0.065 * streak_k * (0.45 + 0.55 * trough)
    ctx.rgb *= (1.0 - roof_stain)[..., None]
    ctx.rgb += sheet_shift[..., None]
    ctx.rgb = _preserve_mean_rgb(ctx.rgb, base_mean)

    ctx.height += 0.60 * rib
    ctx.rgb += (rib * 7.5)[..., None]
    # Continuous 1.0m longitudinal sheet overlap seam along my
    seam_y = np.abs((my % 1.0) - 0.5) > 0.486
    ctx.rgb[seam_y] *= 0.84
    ctx.height[seam_y] -= 0.46
    # Hex fastener bolts along purlins at 1.0m mx intervals on rib crests
    bolt = (np.abs((mx % 1.0) - 0.5) < 0.020) & (np.abs((my % 0.25) - 0.125) > 0.106)
    ctx.rgb[bolt] *= 1.12
    ctx.height[bolt] += 0.20
    # Lower gloss in weathered rib troughs for natural semi-matte Posco color-steel look
    ctx.gloss[...] = (0.34 + 0.08 * np.clip(rib, 0.0, 1.0)) * (1.0 - 0.22 * roof_stain)
    _periodic_weather(ctx, amount=0.014, cycles_u=4, cycles_v=4, seed=11)


def _paint_sandwich_wall(ctx):
    """Korean vertical sandwich panel cladding (1000mm joints, 250mm micro-ribs, vertical rain streaks, 3 variants)."""
    mx, _ = ctx.meters()
    base_mean = ctx.rgb[:1, :1, :].copy()

    # Subtle coated-metal surface grain + gentle kit stains (edge-feathered in v to avoid 4m horizontal seam)
    ctx.grain(amp=1.4, scale_px=3, height=0.05, seed=101)
    rgb_pre_stain = ctx.rgb.copy()
    ctx.stains(amount=0.045, scale_px=72, streaks=0.22, seed=103)
    v_wrap = np.sin(math.pi * ctx.v) ** 0.35
    ctx.rgb = rgb_pre_stain + (ctx.rgb - rgb_pre_stain) * v_wrap[..., None]

    # Continuous vertical 1.0m panel joints + 0.25m bead troughs
    dist_joint = np.minimum(mx % 1.0, 1.0 - (mx % 1.0))
    joint = np.clip(1.0 - dist_joint / 0.016, 0.0, 1.0)
    bead = np.sin(2.0 * math.pi * mx / 0.25)
    trough = np.clip(-bead, 0.0, 1.0)
    panel_idx = np.floor(mx / 1.0).astype(np.int32) % 4

    # Per-variant distinct panel tones + seamless vertical rain-streak noise along rib troughs & joints
    rain_field = np.zeros((ctx.h, ctx.w), np.float32)
    panel_shift = np.zeros((ctx.h, ctx.w), np.float32)
    for vi in range(ctx.variants):
        m = ctx.vi == vi
        rng = np.random.default_rng(100 + vi * 37)
        tones = rng.normal(0.0, 1.9, size=4).astype(np.float32)
        tones -= tones.mean()
        panel_shift[m] = tones[panel_idx[m]]
        n_rain = ctx.noise(scale_px=16, amp=1.0, octaves=2, seed=200 + vi)
        col_streak = np.repeat(n_rain.mean(axis=0, keepdims=True), ctx.h, axis=0)
        # Periodic vertical envelope wraps seamlessly at v=0 and v=1 (no horizontal seam at z=4.85m)
        v_env = 0.78 + 0.22 * np.cos(2.0 * math.pi * ctx.v + vi * 2.1)
        rain_field[m] = (col_streak * v_env)[m]

    rain_k = np.clip(0.5 + 0.5 * rain_field, 0.0, 1.0)
    streak_dark = 0.048 * rain_k * (0.45 + 0.35 * trough + 0.20 * joint)
    ctx.rgb *= (1.0 - streak_dark)[..., None]
    ctx.rgb += panel_shift[..., None]
    # Restore mean brightness of clean wall panels so white walls never turn gray
    ctx.rgb = _preserve_mean_rgb(ctx.rgb, base_mean)

    # Apply crisp 1.0m panel joints & 0.25m micro-ribs after mean brightness preservation
    ctx.rgb *= (1.0 - 0.24 * joint)[..., None]
    ctx.height -= 0.85 * joint
    ctx.height += 0.14 * bead
    ctx.rgb += (bead * 2.2)[..., None]
    ctx.gloss *= (1.0 - 0.18 * streak_dark)
    _periodic_weather(ctx, amount=0.014, cycles_u=2, cycles_v=1, seed=9)


def _paint_office_panel(ctx):
    """Horizontal aluminum composite cladding (2.0m x 1.0m modular grid, under-joint rainwater runoff, 2 variants)."""
    base_mean = ctx.rgb[:1, :1, :].copy()
    ctx.joints(cols=2, rows=2, width_m=0.018, depth=0.75, stagger=0.0, darken=0.26, tone=2.2, seed=13)
    ctx.grain(amp=1.4, scale_px=2, height=0.05, seed=131)
    ctx.stains(amount=0.045, scale_px=52, streaks=0.38, seed=133)

    _, my = ctx.meters()
    # Subtle rainwater runoff right beneath horizontal 1.0m panel joints (v_panel=1 is top of each 1m panel)
    fy = (my % 1.0)
    runoff_band = np.clip((fy - 0.72) / 0.26, 0.0, 1.0) * (fy < 0.985)
    var_noise = np.zeros((ctx.h, ctx.w), np.float32)
    for vi in range(ctx.variants):
        m = ctx.vi == vi
        n_v = ctx.noise(scale_px=40, amp=1.0, octaves=2, seed=240 + vi)
        var_noise[m] = n_v[m]
    drip = 0.040 * runoff_band * np.clip(0.55 + 0.45 * var_noise, 0.0, 1.0)
    ctx.rgb *= (1.0 - drip)[..., None]
    # Keep office Alucobond bright crisp off-white (compensate only stain/drip loss, preserve joint darkening)
    ctx.rgb = _preserve_mean_rgb(ctx.rgb, base_mean * 0.985)

    fine_line = np.abs(((my * 2.0) % 1.0) - 0.5) > 0.488
    ctx.rgb[fine_line] *= 0.94
    ctx.gloss *= (1.0 - 0.20 * drip)
    _periodic_weather(ctx, amount=0.012, cycles_u=1, cycles_v=1, seed=15)


def _paint_plinth(ctx):
    """Concrete foundation plinth (2m control joints, aggregate grain, stains, lower splash grime)."""
    ctx.joints(cols=2, rows=1, width_m=0.014, depth=0.45, stagger=0.0, darken=0.22, tone=2.5, seed=141)
    ctx.grain(amp=6.0, scale_px=2, height=0.42, seed=143)
    ctx.stains(amount=0.085, scale_px=44, streaks=0.50, seed=145)
    # Plinth sits strictly at ground level (ny=1, v=0 is ground z=0), so lower splash grime stays at wall base
    splash_noise = np.zeros((ctx.h, ctx.w), np.float32)
    for vi in range(ctx.variants):
        m = ctx.vi == vi
        n_s = ctx.noise(scale_px=20, amp=1.0, octaves=3, seed=260 + vi)
        splash_noise[m] = n_s[m]
    splash_band = np.clip(1.0 - ctx.v / 0.20, 0.0, 1.0) ** 1.4
    splash = 0.12 * splash_band * np.clip(0.55 + 0.45 * splash_noise, 0.15, 1.0)
    ctx.rgb *= (1.0 - splash)[..., None]
    ctx.gloss *= (1.0 - 0.35 * splash)
    _periodic_weather(ctx, amount=0.03, cycles_u=2, cycles_v=1, seed=19)


def _paint_shutter(ctx):
    """Roll-up industrial steel shutter with horizontal slats, brushed grain, and subtle dust streaks."""
    ctx.joints(cols=1, rows=32, width_m=0.012, depth=0.78, stagger=0.0, darken=0.28, tone=1.6, seed=21)
    ctx.grain(amp=2.0, scale_px=3, height=0.08, seed=151)
    ctx.stains(amount=0.055, scale_px=64, streaks=0.45, seed=153)
    ctx.rgb += ctx.noise(scale_px=32, amp=1.8, octaves=2, seed=155)[..., None]


def _paint_skylight(ctx):
    """Translucent FRP roof skylight strip (non-emissive per LESSONS.md wide-surface rule)."""
    _, my = ctx.meters()
    frame = (ctx.u < 0.05) | (ctx.u > 0.95) | (ctx.v < 0.03) | (ctx.v > 0.97)
    ctx.rgb[frame] = np.array([168, 176, 182], np.float32)
    rib = np.clip(np.cos(2.0 * math.pi * my / 0.25) * 1.4, -1.0, 1.0)
    ctx.rgb[~frame] += (rib[~frame] * 8.0)[..., None]
    ctx.height[~frame] += 0.30 * rib[~frame]
    ctx.stains(amount=0.04, scale_px=48, streaks=0.0, seed=163)
    ctx.rgb += ctx.noise(scale_px=32, amp=2.8, octaves=2, seed=161)[..., None]
    ctx.emis[...] = 0.0
    ctx.gloss[...] = np.where(frame, 0.42, 0.74)


def _paint_louver_vent(ctx):
    """Recessed diagonal industrial ventilation louver grille inside dark perimeter frame."""
    u, v = ctx.u, ctx.v
    border = (u < 0.05) | (u > 0.95) | (v < 0.06) | (v > 0.94)
    blade_phase = (v * 14.0) % 1.0
    slat_shadow = blade_phase < 0.42
    slat_face = (blade_phase >= 0.42) & ~border
    ctx.rgb[border] = np.array([62, 68, 74], np.float32)
    ctx.rgb[slat_shadow & ~border] = np.array([34, 38, 44], np.float32)
    ctx.rgb[slat_face] = np.array([148, 154, 160], np.float32)
    ctx.grain(amp=1.5, scale_px=2, height=0.05, seed=167)
    ctx.height[border] += 0.25
    ctx.height[slat_shadow & ~border] -= 0.55
    ctx.height[slat_face] += 0.15
    ctx.gloss[...] = np.where(border, 0.45, np.where(slat_face, 0.52, 0.18))


def _paint_solar_pv(ctx):
    """Monocrystalline photovoltaic roof module array (sleek dark cells + silver module frames)."""
    mx, my = ctx.meters()
    # 1.0m x 2.0m module grid inside 2.0m x 2.0m tile
    fu = (mx % 1.0)
    fv = (my % 2.0) / 2.0
    frame = (fu < 0.032) | (fu > 0.968) | (fv < 0.022) | (fv > 0.978)
    cell_u = ((fu - 0.032) / 0.936 * 6.0) % 1.0
    cell_v = ((fv - 0.022) / 0.956 * 10.0) % 1.0
    grid_line = (cell_u < 0.032) | (cell_u > 0.968) | (cell_v < 0.028) | (cell_v > 0.972)
    ctx.rgb[...] = np.array([22, 36, 66], np.float32)
    ctx.rgb += (2.5 * np.sin(2.0 * math.pi * (fu + fv)))[..., None]
    ctx.rgb += ctx.noise(scale_px=32, amp=1.2, octaves=2, seed=165)[..., None]
    ctx.rgb[grid_line & ~frame] = np.array([56, 78, 114], np.float32)
    ctx.rgb[frame] = np.array([184, 190, 198], np.float32)
    ctx.height[frame] += 0.26
    ctx.height[grid_line & ~frame] -= 0.06
    ctx.gloss[...] = np.where(frame, 0.58, 0.86)
    ctx.emis[...] = 0.0


def _paint_equipment(ctx):
    """HVAC / dust-collector metal cabinet with inspection door seams and louvered intake grilles."""
    ctx.joints(cols=2, rows=2, width_m=0.014, depth=0.65, darken=0.25, tone=2.5, seed=31)
    ctx.grain(amp=2.2, scale_px=2, height=0.10, seed=171)
    ctx.stains(amount=0.05, scale_px=32, streaks=0.35, seed=173)
    louver = (ctx.u > 0.14) & (ctx.u < 0.86) & (ctx.v > 0.22) & (ctx.v < 0.78) & (((ctx.v * 26.0) % 1.0) < 0.44)
    ctx.rgb[louver] *= 0.48
    ctx.height[louver] -= 0.48


def _paint_window_atlas(ctx):
    """5x5 REF_GRID window atlas: cells 0..3 = factory clerestory wire/frosted glass (lit), 4..24 = office blinds (4..8 lit, 9..24 unlit)."""
    g = K.REF_GRID
    fu = (ctx.u * g) % 1.0
    fv = (ctx.v * g) % 1.0
    cx = np.floor(ctx.u * g).astype(np.int64)
    cy = np.floor(ctx.v * g).astype(np.int64)
    cell_id = cy * g + cx
    h = ((cx * 37 + cy * 71) % 100) / 100.0

    workshop = cell_id < 4
    office = ~workshop

    # Base glass color: office dark architectural teal vs factory frosted milky blue-gray glass
    office_rgb = np.array([56, 90, 106], np.float32) + ((h - 0.5) * 14.0)[..., None] + (fv * 38.0 - 5.0)[..., None]
    work_rgb = np.array([154, 182, 198], np.float32) + ((h - 0.5) * 12.0)[..., None] + (fv * 18.0 - 4.0)[..., None]
    ctx.rgb[...] = np.where(workshop[..., None], work_rgb, office_rgb)

    # Factory clerestory: vertical translucent polycarbonate ribs + subtle diamond wire-mesh (no blinds)
    rib = np.sin(2.0 * math.pi * fu * 10.0)
    ctx.rgb[workshop] += (rib[workshop] * 4.5)[..., None]
    ctx.height[workshop] += 0.08 * rib[workshop]
    d1 = np.abs(((fu + fv) * 6.0) % 1.0 - 0.5)
    d2 = np.abs(((fu - fv) * 6.0) % 1.0 - 0.5)
    wire = workshop & ((d1 < 0.042) | (d2 < 0.042))
    ctx.rgb[wire] *= 0.84
    ctx.height[wire] -= 0.06

    # Office windows only: horizontal Venetian blinds
    blind = office & (fv > 0.52) & (h > 0.36)
    slat = 0.90 + 0.10 * np.sin(fv * 48.0 * math.pi)
    shade = np.array([196, 202, 204], np.float32) * slat[..., None]
    ctx.rgb[blind] = ctx.rgb[blind] * 0.42 + shade[blind] * 0.58

    edge = np.minimum(np.minimum(fu, 1.0 - fu), np.minimum(fv, 1.0 - fv))
    ctx.rgb *= (0.72 + 0.28 * np.clip(edge / 0.04, 0.0, 1.0))[..., None]

    # Contiguous 9-cell lit block (cells 0..8); pad=False kills outer 16px border to prevent mip bleed
    lit_cells = 9
    lit = cell_id < lit_cells
    r = max(2, round(ctx.w * 0.016))
    m = np.pad(lit, r, constant_values=False)
    for ax in (0, 1):
        m = np.logical_and.reduce([np.roll(m, k, ax) for k in range(-r, r + 1)])
    lit = m[r:-r, r:-r]

    work_glow = (0.80 + 0.14 * (1.0 - np.abs(fv - 0.56))) * (0.90 + 0.10 * ((h * 13.0) % 1.0)) * np.where(wire, 0.85, 1.0)
    office_glow = (0.52 + 0.26 * ((h * 19.0) % 1.0)) * (0.76 + 0.24 * fv) * np.where(blind, 0.56, 1.0)
    ctx.emis[...] = np.where(lit, np.where(workshop, work_glow, office_glow), 0.0)
    ctx.gloss[...] = np.where(workshop, 0.56, np.where(blind, 0.35, 0.86))


def _paint_entrance_door(ctx):
    """Commercial double-leaf anodized aluminum entrance door with glazed vision panels & kickplate."""
    u, v = ctx.u, ctx.v
    border = (u < 0.06) | (u > 0.94) | (v > 0.95)
    mullion = np.abs(u - 0.50) < 0.028
    kick = v < 0.10
    mid_rail = np.abs(v - 0.44) < 0.032
    glass_l = (u > 0.11) & (u < 0.44) & (((v > 0.49) & (v < 0.90)) | ((v > 0.14) & (v < 0.39)))
    glass_r = (u > 0.56) & (u < 0.89) & (((v > 0.49) & (v < 0.90)) | ((v > 0.14) & (v < 0.39)))
    glass = glass_l | glass_r
    handle = ((u > 0.40) & (u < 0.43) | (u > 0.57) & (u < 0.60)) & (v > 0.42) & (v < 0.62)

    ctx.rgb[border | mullion | mid_rail] = np.array([44, 50, 56], np.float32)
    ctx.rgb[kick] = np.array([152, 158, 164], np.float32)
    ctx.grain(amp=1.6, scale_px=2, height=0.05, seed=181)
    ctx.stains(amount=0.035, scale_px=40, streaks=0.30, seed=183)
    ctx.rgb[glass] = np.array([80, 112, 126], np.float32) + (v[glass] * 26.0)[..., None]
    ctx.rgb[handle] = np.array([210, 214, 218], np.float32)
    ctx.height[glass] -= 0.35
    ctx.height[handle | mid_rail] += 0.25
    ctx.gloss[...] = np.where(glass, 0.88, np.where(kick | handle, 0.78, 0.52))
    ctx.emis[...] = np.where(glass, 0.26, 0.0)


def _paint_exit_door(ctx):
    """Industrial steel emergency fire-exit door (narrow safety vision slit, panic bar, non-emissive)."""
    u, v = ctx.u, ctx.v
    border = (u < 0.07) | (u > 0.93) | (v > 0.96)
    vision = (u > 0.58) & (u < 0.80) & (v > 0.56) & (v < 0.86)
    panic_bar = (u > 0.14) & (u < 0.82) & (v > 0.42) & (v < 0.46)
    louver = (u > 0.16) & (u < 0.84) & (v > 0.10) & (v < 0.28) & (((v * 38.0) % 1.0) < 0.45)
    ctx.rgb[...] = np.array([116, 122, 128], np.float32)
    ctx.grain(amp=1.8, scale_px=2, height=0.06, seed=185)
    ctx.stains(amount=0.045, scale_px=36, streaks=0.35, seed=187)
    ctx.rgb[border] = np.array([52, 56, 62], np.float32)
    ctx.rgb[vision] = np.array([58, 76, 86], np.float32)
    ctx.rgb[panic_bar] = np.array([196, 202, 208], np.float32)
    ctx.rgb[louver] *= 0.52
    ctx.height[vision] -= 0.30
    ctx.height[panic_bar] += 0.25
    ctx.height[louver] -= 0.35
    ctx.gloss[...] = np.where(vision, 0.82, np.where(panic_bar, 0.70, 0.38))
    ctx.emis[...] = 0.0


def _draw_sign_band(drw, edrw, hdrw, gdrw, cw, ch, kr_name, en_sub):
    """Render one crisp Korean/English corporate signboard band with 3D drop shadow and height relief."""
    for y in range(ch):
        t = y / max(1, ch - 1)
        r = int(20 + 6 * t)
        g = int(46 + 10 * t)
        b = int(88 + 14 * t)
        drw.line([(0, y), (cw - 1, y)], fill=(r, g, b))
    drw.rectangle([4, 4, cw - 5, ch - 5], outline=(168, 182, 198), width=3)
    hdrw.rectangle([4, 4, cw - 5, ch - 5], outline=90, width=3)

    # Geometric industrial emblem on left (square world-aspect coordinates via ch)
    e_r = int(ch * 0.28)
    ex_c = int(ch * 0.56)
    ey_c = ch // 2
    ring_w = max(4, int(ch * 0.068))
    # Drop shadow (+3, +3) on RGB only
    drw.ellipse([ex_c - e_r + 3, ey_c - e_r + 3, ex_c + e_r + 3, ey_c + e_r + 3],
                outline=(8, 18, 36), width=ring_w)
    drw.ellipse([ex_c - e_r, ey_c - e_r, ex_c + e_r, ey_c + e_r],
                outline=(138, 206, 248), width=ring_w)
    hdrw.ellipse([ex_c - e_r, ey_c - e_r, ex_c + e_r, ey_c + e_r], outline=185, width=ring_w)
    edrw.ellipse([ex_c - e_r, ey_c - e_r, ex_c + e_r, ey_c + e_r], outline=160, width=ring_w)
    gdrw.ellipse([ex_c - e_r, ey_c - e_r, ex_c + e_r, ey_c + e_r], outline=195, width=ring_w)

    ir = int(e_r * 0.44)
    poly_sh = [(ex_c - ir + 3, ey_c + 3), (ex_c + 3, ey_c - ir + 3), (ex_c + ir + 3, ey_c + 3), (ex_c + 3, ey_c + ir + 3)]
    poly = [(ex_c - ir, ey_c), (ex_c, ey_c - ir), (ex_c + ir, ey_c), (ex_c, ey_c + ir)]
    drw.polygon(poly_sh, fill=(8, 18, 36))
    drw.polygon(poly, fill=(240, 246, 255))
    hdrw.polygon(poly, fill=210)
    edrw.polygon(poly, fill=185)
    gdrw.polygon(poly, fill=200)

    # Korean company title + English subtitle in remaining right area
    tx0 = ex_c + e_r + int(ch * 0.20)
    tx1 = cw - int(ch * 0.16)
    tx_w = max(80, tx1 - tx0)
    f_kr = _fit_font(drw, FONT_KR, kr_name, int(tx_w * 0.94), int(ch * 0.56))
    f_en = _fit_font(drw, FONT_EN, en_sub, int(tx_w * 0.90), int(ch * 0.17))

    bb_kr = drw.textbbox((0, 0), kr_name, font=f_kr)
    bb_en = drw.textbbox((0, 0), en_sub, font=f_en)
    kr_w, kr_h = bb_kr[2] - bb_kr[0], bb_kr[3] - bb_kr[1]
    en_w, en_h = bb_en[2] - bb_en[0], bb_en[3] - bb_en[1]
    gap = int(ch * 0.08)
    top_y = (ch - (kr_h + gap + en_h)) * 0.5

    kr_x = tx0 + (tx_w - kr_w) * 0.5 - bb_kr[0]
    kr_y = top_y - bb_kr[1]
    en_x = tx0 + (tx_w - en_w) * 0.5 - bb_en[0]
    en_y = top_y + kr_h + gap - bb_en[1]

    # Drop shadow down & right (1-3 px), RGB only
    drw.text((kr_x + 3, kr_y + 3), kr_name, font=f_kr, fill=(8, 18, 36))
    drw.text((en_x + 2, en_y + 2), en_sub, font=f_en, fill=(8, 18, 36))
    # Main crisp text
    drw.text((kr_x, kr_y), kr_name, font=f_kr, fill=(246, 249, 255))
    drw.text((en_x, en_y), en_sub, font=f_en, fill=(198, 224, 248))
    # 3D raised channel-letter height relief
    hdrw.text((kr_x, kr_y), kr_name, font=f_kr, fill=242)
    hdrw.text((en_x, en_y), en_sub, font=f_en, fill=175)
    # Night emissive on letters only (background stays 0)
    edrw.text((kr_x, kr_y), kr_name, font=f_kr, fill=218)
    edrw.text((en_x, en_y), en_sub, font=f_en, fill=145)
    # Glossy acrylic letter faces
    gdrw.text((kr_x, kr_y), kr_name, font=f_kr, fill=204)
    gdrw.text((en_x, en_y), en_sub, font=f_en, fill=190)


def _paint_factory_sign(ctx):
    """Packed 1024x256 signboard bands with PIL Korean/English fonts, 3D relief & zero background glow."""
    bands = []
    for _key, (py0, py1, world_w, world_h, kr_name, en_sub) in SIGN_BANDS.items():
        bands.append((
            py0,
            py1,
            world_w,
            world_h,
            (22, 50, 94),
            lambda drw, edrw, hdrw, gdrw, cw, ch, k=kr_name, e=en_sub: _draw_sign_band(
                drw, edrw, hdrw, gdrw, cw, ch, k, e
            ),
        ))
    _render_packed_bands(ctx, "sign_plate", bands, bg=(22, 50, 94))


def _paint_hazard(ctx):
    """45-degree yellow/black safety clearance warning stripe."""
    mx, my = ctx.meters()
    stripe = ((mx + my) * 3.0) % 1.0 < 0.5
    ctx.rgb[stripe] = np.array([232, 180, 28], np.float32)
    ctx.rgb[~stripe] = np.array([34, 36, 40], np.float32)
    ctx.gloss[...] = 0.42


def _paint_warm_light(ctx):
    """Warm exterior flood/sconce emitter."""
    edge = (ctx.u < 0.08) | (ctx.u > 0.92) | (ctx.v < 0.08) | (ctx.v > 0.92)
    ctx.rgb[edge] = np.array([56, 60, 66], np.float32)
    ctx.emis[...] = np.where(edge, 0.0, 0.88)
    ctx.gloss[...] = np.where(edge, 0.4, 0.88)


def _paint_signal_lamp(ctx):
    """Yard entry signal / warning indicator bezel (small fixture only)."""
    u, v = ctx.u, ctx.v
    d = np.hypot(u - 0.5, v - 0.5)
    lens = d < 0.32
    ctx.rgb[...] = np.array([42, 46, 52], np.float32)
    ctx.rgb[lens] = np.array([228, 64, 48], np.float32)
    ctx.emis[...] = np.where(lens, 0.82, 0.0)
    ctx.gloss[...] = np.where(lens, 0.88, 0.40)


def make_atlas(spec: FactorySpec, size=4096):
    A = K.Atlas(size=size, pad=12)
    # ControlMask R=(roof + upper accent band), G=(factory sandwich wall cladding), B=(freight shutters)
    A.add("roof_blue", color=spec.roof_color, ctrl=(255, 0, 0), metal=0.28, gloss=0.38,
          px=1024, tile=(4.0, 4.0), variants=2, painter=_paint_corrugated_blue_roof, normal_strength=2.2)
    A.add("wall_panel", color=spec.wall_color, ctrl=(0, 255, 0), metal=0.08, gloss=0.34,
          px=1024, tile=(4.0, 4.0), variants=3, painter=_paint_sandwich_wall, normal_strength=2.0)
    A.add("office_panel", color=(232, 234, 236), ctrl=(0, 0, 0), metal=0.20, gloss=0.44,
          px=512, tile=(4.0, 2.0), variants=2, painter=_paint_office_panel, normal_strength=2.0)
    A.add("shutter", color=(158, 164, 170), ctrl=(0, 0, 255), metal=0.58, gloss=0.45,
          px=1024, tile=(4.0, 4.0), painter=_paint_shutter, normal_strength=2.2)
    A.add("window", color=(64, 102, 114), ctrl=(0, 0, 0), metal=0.0, gloss=0.88,
          emissive=(236, 244, 255), px=1024, painter=_paint_window_atlas)
    A.add("sign_plate", color=(22, 50, 94), ctrl=(0, 0, 0), metal=0.22, gloss=0.42,
          emissive=(225, 240, 255), px=1024, painter=_paint_factory_sign, normal_strength=2.5)
    A.add("plinth", color=(108, 112, 116), ctrl=(0, 0, 0), metal=0.0, gloss=0.20,
          px=512, tile=(4.0, 2.0), variants=2, painter=_paint_plinth, normal_strength=2.4)
    A.add("skylight_frp", color=(198, 224, 234), ctrl=(0, 0, 0), metal=0.0, gloss=0.74,
          px=512, tile=(2.0, 4.0), painter=_paint_skylight)
    A.add("louver_vent", color=(140, 146, 152), ctrl=(0, 0, 0), metal=0.50, gloss=0.44,
          px=512, tile=(2.0, 2.0), painter=_paint_louver_vent)
    A.add("solar_pv", color=(24, 38, 70), ctrl=(0, 0, 0), metal=0.25, gloss=0.84,
          px=512, tile=(2.0, 2.0), painter=_paint_solar_pv)
    A.add("equipment", color=(142, 148, 152), ctrl=(0, 0, 0), metal=0.48, gloss=0.42,
          px=256, tile=(2.0, 2.0), painter=_paint_equipment)
    A.add("door", color=(50, 56, 62), ctrl=(0, 0, 0), metal=0.45, gloss=0.68,
          emissive=(255, 224, 170), px=512, painter=_paint_entrance_door)
    A.add("exit_door", color=(116, 122, 128), ctrl=(0, 0, 0), metal=0.52, gloss=0.40,
          px=256, painter=_paint_exit_door)
    A.add("hazard_stripe", color=(232, 180, 28), ctrl=(0, 0, 0), metal=0.10, gloss=0.42,
          px=128, tile=(1.0, 0.5), painter=_paint_hazard)
    A.add("band_blue", color=spec.accent_color, ctrl=(255, 0, 0), metal=0.28, gloss=0.40, px=64)
    A.add("trim_silver", color=(184, 190, 196), ctrl=(0, 0, 0), metal=0.72, gloss=0.58, px=64)
    A.add("frame", color=(56, 60, 66), ctrl=(0, 0, 0), metal=0.68, gloss=0.52, px=64)
    A.add("safety_yellow", color=(224, 172, 34), ctrl=(0, 0, 0), metal=0.10, gloss=0.40, px=64)
    A.add("light_warm", color=(255, 246, 224), ctrl=(0, 0, 0), metal=0.0, gloss=0.85,
          emissive=(255, 232, 185), px=64, painter=_paint_warm_light)
    A.add("signal_red", color=(228, 64, 48), ctrl=(0, 0, 0), metal=0.20, gloss=0.78,
          emissive=(255, 76, 54), px=64, painter=_paint_signal_lamp)
    return A


# ---------------------------------------------------------------------------
# Geometry Helpers
# ---------------------------------------------------------------------------
def _win_unit_for(floor, idx, seed=13):
    """Pseudo-random cell assignment across office cells (4..8 lit, 9..24 unlit) for floor=0 WindowSet."""
    hv = (((floor * 7919 + idx * 104729 + seed * 3571) * 2654435761 & 0xFFFFFFFF) >> 16)
    if (hv % 25) < 9:
        cell = 4 + (hv % 5)   # lit office cells 4..8 (~36%)
    else:
        cell = 9 + (hv % 16)  # unlit office cells 9..24 (~64%)
    return (cell * 18) % 25


def _uv_wall_point(atlas, region, x, z, x_ref, z_ref, tile_origin_x, tw, th, variant=0, margin_px=0.5):
    u0, v0, u1, v1 = atlas._uvrect(region, variant=variant)
    e = margin_px / atlas.size
    ua, ub = u0 + e, u1 - e
    va, vb = v0 + e, v1 - e
    fu = max(0.0, min(1.0, (x - tile_origin_x) / tw))
    fv = max(0.0, min(1.0, (z - z_ref) / th))
    return ua + (ub - ua) * fu, va + (vb - va) * fv


def _add_gable_end_walls(mb, atlas, x_left, x_right, y0, y1, eave_z, ridge_rise, region, split_tiles=True):
    """Closed front (-Y) and back (+Y) gable triangles tiled seamlessly at real-world scale."""
    xm = 0.5 * (x_left + x_right)
    zp = eave_z + ridge_rise
    if not split_tiles or not atlas.is_tiled(region):
        p_front = [(x_left, y0, eave_z), (x_right, y0, eave_z), (xm, y0, zp)]
        p_back = [(x_right, y1, eave_z), (x_left, y1, eave_z), (xm, y1, zp)]
        uv_f = atlas.uv(region)[:3]
        mb.tri(p_front, uv_f, region)
        mb.tri(p_back, uv_f, region)
        return

    tw, th = atlas.tile_size(region)
    half_span = max(1e-6, xm - x_left)

    def z_at(x):
        return eave_z + ridge_rise * (1.0 - abs(x - xm) / half_span)

    cuts = [x_left]
    k = 1
    while x_left + k * tw < x_right - 1e-5:
        cuts.append(x_left + k * tw)
        k += 1
    cuts.append(xm)
    cuts.append(x_right)
    cuts = sorted(set(round(c, 6) for c in cuts))

    for xa, xb in zip(cuts[:-1], cuts[1:]):
        if xb - xa < 1e-4:
            continue
        za, zb = z_at(xa), z_at(xb)
        tile_idx = int(math.floor((0.5 * (xa + xb) - x_left) / tw))
        orig_x = x_left + tile_idx * tw

        def uvp(x, z):
            return _uv_wall_point(atlas, region, x, z, x_left, eave_z, orig_x, tw, th, variant=tile_idx * 7)

        if za <= eave_z + 1e-4 and zb > eave_z + 1e-4:
            pf = [(xa, y0, eave_z), (xb, y0, eave_z), (xb, y0, zb)]
            pb = [(xb, y1, eave_z), (xa, y1, eave_z), (xb, y1, zb)]
            mb.tri(pf, [uvp(p[0], p[2]) for p in pf], region)
            mb.tri(pb, [uvp(p[0], p[2]) for p in pb], region)
        elif zb <= eave_z + 1e-4 and za > eave_z + 1e-4:
            pf = [(xa, y0, eave_z), (xb, y0, eave_z), (xa, y0, za)]
            pb = [(xb, y1, eave_z), (xa, y1, eave_z), (xa, y1, za)]
            mb.tri(pf, [uvp(p[0], p[2]) for p in pf], region)
            mb.tri(pb, [uvp(p[0], p[2]) for p in pb], region)
        else:
            pf = [(xa, y0, eave_z), (xb, y0, eave_z), (xb, y0, zb), (xa, y0, za)]
            pb = [(xb, y1, eave_z), (xa, y1, eave_z), (xa, y1, za), (xb, y1, zb)]
            mb.quad(pf, [uvp(p[0], p[2]) for p in pf], region)
            mb.quad(pb, [uvp(p[0], p[2]) for p in pb], region)


def _add_gable_roof_span(mb, gx0, gx1, ry0, ry1, ze_l_u, ze_r_u, zr_u, roof_t,
                         emit_left_edge=True, emit_right_edge=True,
                         roof_reg="roof_blue", trim_reg="trim_silver", soffit_reg="wall_panel"):
    """Closed gable roof slab with slopes, underside soffit, and fascia edges."""
    gxm = 0.5 * (gx0 + gx1)
    ze_l_t = ze_l_u + roof_t
    ze_r_t = ze_r_u + roof_t
    zr_t = zr_u + roof_t

    mb.rect([(gx0, ry0, ze_l_t), (gxm, ry0, zr_t), (gxm, ry1, zr_t), (gx0, ry1, ze_l_t)], roof_reg)
    mb.rect([(gxm, ry0, zr_t), (gx1, ry0, ze_r_t), (gx1, ry1, ze_r_t), (gxm, ry1, zr_t)], roof_reg)

    mb.rect([(gx0, ry1, ze_l_u), (gxm, ry1, zr_u), (gxm, ry0, zr_u), (gx0, ry0, ze_l_u)], soffit_reg)
    mb.rect([(gxm, ry1, zr_u), (gx1, ry1, ze_r_u), (gx1, ry0, ze_r_u), (gxm, ry0, zr_u)], soffit_reg)

    mb.rect([(gx0, ry0, ze_l_u), (gxm, ry0, zr_u), (gxm, ry0, zr_t), (gx0, ry0, ze_l_t)], trim_reg)
    mb.rect([(gxm, ry0, zr_u), (gx1, ry0, ze_r_u), (gx1, ry0, ze_r_t), (gxm, ry0, zr_t)], trim_reg)

    mb.rect([(gxm, ry1, zr_u), (gx0, ry1, ze_l_u), (gx0, ry1, ze_l_t), (gxm, ry1, zr_t)], trim_reg)
    mb.rect([(gx1, ry1, ze_r_u), (gxm, ry1, zr_u), (gxm, ry1, zr_t), (gx1, ry1, ze_r_t)], trim_reg)

    if emit_left_edge:
        mb.rect([(gx0, ry1, ze_l_u), (gx0, ry0, ze_l_u), (gx0, ry0, ze_l_t), (gx0, ry1, ze_l_t)], trim_reg)
    if emit_right_edge:
        mb.rect([(gx1, ry0, ze_r_u), (gx1, ry1, ze_r_u), (gx1, ry1, ze_r_t), (gx1, ry0, ze_r_t)], trim_reg)


def _add_sloped_box(mb, p0x, p0z, p1x, p1z, y0, y1, nx, nz, off0, off1, region):
    """Closed 3D box aligned with a sloped roof segment from (p0x,p0z)->(p1x,p1z) extruded along normal (nx,nz)."""
    def pt(px, y, pz, o):
        return (px + nx * o, y, pz + nz * o)

    mb.rect([pt(p0x, y0, p0z, off1), pt(p1x, y0, p1z, off1), pt(p1x, y1, p1z, off1), pt(p0x, y1, p0z, off1)], region)
    mb.rect([pt(p0x, y0, p0z, off0), pt(p1x, y0, p1z, off0), pt(p1x, y0, p1z, off1), pt(p0x, y0, p0z, off1)], region)
    mb.rect([pt(p1x, y1, p1z, off0), pt(p0x, y1, p0z, off0), pt(p0x, y1, p0z, off1), pt(p1x, y1, p1z, off1)], region)
    mb.rect([pt(p0x, y1, p0z, off0), pt(p0x, y0, p0z, off0), pt(p0x, y0, p0z, off1), pt(p0x, y1, p0z, off1)], region)
    mb.rect([pt(p1x, y0, p1z, off0), pt(p1x, y1, p1z, off0), pt(p1x, y1, p1z, off1), pt(p1x, y0, p1z, off1)], region)


def _slope_geom(gx0, gx1, ze_u, zr_u, roof_t, u_frac0, u_frac1, side="left"):
    gxm = 0.5 * (gx0 + gx1)
    if side == "left":
        xa, za = gx0 + (gxm - gx0) * u_frac0, ze_u + (zr_u - ze_u) * u_frac0 + roof_t
        xb, zb = gx0 + (gxm - gx0) * u_frac1, ze_u + (zr_u - ze_u) * u_frac1 + roof_t
        dx, dz = gxm - gx0, zr_u - ze_u
    else:
        xa, za = gxm + (gx1 - gxm) * u_frac0, zr_u + (ze_u - zr_u) * u_frac0 + roof_t
        xb, zb = gxm + (gx1 - gxm) * u_frac1, zr_u + (ze_u - zr_u) * u_frac1 + roof_t
        dx, dz = gx1 - gxm, ze_u - zr_u
    L = math.hypot(dx, dz)
    ux, uz = dx / L, dz / L
    nx, nz = -uz, ux
    return xa, za, xb, zb, ux, uz, nx, nz


def _add_skylight_strip(mb, gx0, gx1, ze_u, zr_u, roof_t, y0, y1, u_frac0, u_frac1, side="left", bay_len=5.5):
    """Framed FRP skylight cassette raised cleanly above roof slope with curb border and cross-mullions."""
    xa, za, xb, zb, ux, uz, nx, nz = _slope_geom(gx0, gx1, ze_u, zr_u, roof_t, u_frac0, u_frac1, side)
    _add_sloped_box(mb, xa, za, xb, zb, y0, y1, nx, nz, 0.0, 0.035, "frame")
    fw = 0.08
    _add_sloped_box(mb, xa + ux * fw, za + uz * fw, xb - ux * fw, zb - uz * fw,
                    y0 + fw, y1 - fw, nx, nz, 0.035, 0.055, "skylight_frp")
    bars = max(0, round((y1 - y0) / max(3.5, bay_len)) - 1)
    for bi in range(bars):
        by = y0 + (y1 - y0) * ((bi + 1) / (bars + 1))
        _add_sloped_box(mb, xa + ux * fw, za + uz * fw, xb - ux * fw, zb - uz * fw,
                        by - 0.035, by + 0.035, nx, nz, 0.055, 0.082, "trim_silver")


def _add_roof_solar_bank(mb, gx0, gx1, ze_u, zr_u, roof_t, y0, y1, u_frac0, u_frac1, side="left", stage=0):
    """Sloped rooftop photovoltaic solar array mounted on roof racking rails (Daejeon Rail Depot)."""
    xa, za, xb, zb, ux, uz, nx, nz = _slope_geom(gx0, gx1, ze_u, zr_u, roof_t, u_frac0, u_frac1, side)
    if stage == 1:
        _add_sloped_box(mb, xa, za, xb, zb, y0, y1, nx, nz, 0.04, 0.14, "solar_pv")
        return
    # Longitudinal mounting rails resting directly on roof slope
    for u_rail in (0.20, 0.80):
        rx = xa + (xb - xa) * u_rail
        rz = za + (zb - za) * u_rail
        _add_sloped_box(mb, rx - ux * 0.05, rz - uz * 0.05, rx + ux * 0.05, rz + uz * 0.05,
                        y0 + 0.10, y1 - 0.10, nx, nz, 0.0, 0.11, "frame")
    # Split into 2m-wide module sub-banks along Y with narrow service walkways
    span_y = y1 - y0
    sub_banks = max(1, round(span_y / 12.0))
    gap = 0.55 if sub_banks > 1 else 0.0
    sub_len = (span_y - (sub_banks - 1) * gap) / sub_banks
    for si in range(sub_banks):
        sy0 = y0 + si * (sub_len + gap)
        sy1 = sy0 + sub_len
        _add_sloped_box(mb, xa, za, xb, zb, sy0, sy1, nx, nz, 0.11, 0.16, "trim_silver")
        _add_sloped_box(mb, xa + ux * 0.05, za + uz * 0.05, xb - ux * 0.05, zb - uz * 0.05,
                        sy0 + 0.05, sy1 - 0.05, nx, nz, 0.16, 0.19, "solar_pv")


def _add_frustum_z(mb, cx, cy, z0, z1, r0, r1, sides, region, cap_top=True, cap_bottom=False):
    """Closed N-sided cylindrical/tapered frustum aligned along Z with outward normals."""
    step = 2.0 * math.pi / sides
    pts0 = [(cx + r0 * math.cos(i * step), cy + r0 * math.sin(i * step), z0) for i in range(sides)]
    pts1 = [(cx + r1 * math.cos(i * step), cy + r1 * math.sin(i * step), z1) for i in range(sides)]
    for i in range(sides):
        j = (i + 1) % sides
        mb.rect([pts0[i], pts0[j], pts1[j], pts1[i]], region)
    uv3 = mb.atlas.uv(region)[:3]
    if cap_top and r1 > 1e-4:
        top_c = (cx, cy, z1)
        for i in range(sides):
            j = (i + 1) % sides
            mb.tri([top_c, pts1[i], pts1[j]], uv3, region)
    if cap_bottom and r0 > 1e-4:
        bot_c = (cx, cy, z0)
        for i in range(sides):
            j = (i + 1) % sides
            mb.tri([bot_c, pts0[j], pts0[i]], uv3, region)


def _add_ventilator(mb, cx, cy, zr_top, slope, radius=0.30):
    """Korean industrial rotary turbine ventilator seated flush into ridge cap & roof slopes."""
    # Curb base drops below zr_top - curb_half*slope so outer flanges never float above sloped sheets
    curb_half = radius + 0.05
    curb_z0 = zr_top - curb_half * slope - 0.03
    z_collar = zr_top + 0.22
    mb.box(cx - curb_half, cx + curb_half, cy - curb_half, cy + curb_half, curb_z0, z_collar, "trim_silver", skip=("bottom",))
    _add_frustum_z(mb, cx, cy, z_collar, z_collar + 0.09, radius * 0.78, radius * 0.74, 8, "trim_silver", cap_top=False)
    _add_frustum_z(mb, cx, cy, z_collar + 0.09, z_collar + 0.09 + radius, radius, radius, 8, "equipment", cap_top=False)
    _add_frustum_z(mb, cx, cy, z_collar + 0.09 + radius, z_collar + 0.20 + radius, radius * 1.06, radius * 0.45, 8, "trim_silver", cap_top=True)


def _add_roof_box_fan(mb, gx0, gx1, ze_u, zr_u, roof_t, cy, u_frac=0.74, side="left", half_w=0.52):
    """Low-profile galvanized powered roof exhaust box fan seated flush into upper roof slope."""
    gxm = 0.5 * (gx0 + gx1)
    if side == "left":
        cx = gx0 + (gxm - gx0) * u_frac
        slope = (zr_u - ze_u) / max(1e-6, gxm - gx0)
        z_center = ze_u + (zr_u - ze_u) * u_frac + roof_t
    else:
        cx = gxm + (gx1 - gxm) * u_frac
        slope = (zr_u - ze_u) / max(1e-6, gx1 - gxm)
        z_center = zr_u + (ze_u - zr_u) * u_frac + roof_t
    z_low = z_center - half_w * slope - 0.04
    z_curb_top = z_center + half_w * slope + 0.26
    mb.box(cx - half_w, cx + half_w, cy - half_w, cy + half_w, z_low, z_curb_top, "frame")
    mb.box(cx - half_w + 0.06, cx + half_w - 0.06, cy - half_w + 0.06, cy + half_w - 0.06,
           z_curb_top, z_curb_top + 0.28, dict(default="louver_vent", top="trim_silver"), skip=("bottom",))
    mb.box(cx - half_w - 0.08, cx + half_w + 0.08, cy - half_w - 0.08, cy + half_w + 0.08,
           z_curb_top + 0.28, z_curb_top + 0.42, "trim_silver")


def _add_framed_window(mb, wins, stage, axis, c, s, a0, a1, z0, z1, floor, unit_seq, bays=1):
    """Multi-bay window with real perimeter frame and mullions; each bay maps to unit_seq[i]."""
    if stage != 0:
        return
    m = 0.06
    mw = 0.03
    K.axbox(mb, axis, c, s, a0 - m, a1 + m, 0.0, 0.08, z0 - m, z0, "frame")
    K.axbox(mb, axis, c, s, a0 - m, a1 + m, 0.0, 0.08, z1, z1 + m, "frame")
    K.axbox(mb, axis, c, s, a0 - m, a0, 0.0, 0.08, z0, z1, "frame")
    K.axbox(mb, axis, c, s, a1, a1 + m, 0.0, 0.08, z0, z1, "frame")
    bay_w = (a1 - a0) / max(1, bays)
    for i in range(bays):
        pa0 = a0 + i * bay_w + (mw if i > 0 else 0.0)
        pa1 = a0 + (i + 1) * bay_w - (mw if i < bays - 1 else 0.0)
        if i > 0:
            mx = a0 + i * bay_w
            K.axbox(mb, axis, c, s, mx - mw, mx + mw, 0.0, 0.07, z0, z1, "frame")
        if pa1 - pa0 > 0.15:
            u_val = unit_seq[i] if isinstance(unit_seq, (list, tuple)) else unit_seq
            wins.add_face(axis, c, s, pa0, pa1, z0, z1, floor=floor, unit=u_val)


def _add_diagonal_strut_y(mb, x, y_wall, z_wall, y_tip, z_tip, half_w=0.025, region="trim_silver"):
    """Closed 3D diagonal steel canopy tie-rod/brace along Y-Z plane."""
    dy = y_wall - y_tip
    dz = z_wall - z_tip
    L = math.hypot(dy, dz)
    ny, nz = -dz / L * half_w, dy / L * half_w
    xl, xr = x - half_w, x + half_w
    a = (xl, y_tip + ny, z_tip + nz)
    b = (xr, y_tip + ny, z_tip + nz)
    c = (xr, y_wall + ny, z_wall + nz)
    d = (xl, y_wall + ny, z_wall + nz)
    e = (xl, y_tip - ny, z_tip - nz)
    f = (xr, y_tip - ny, z_tip - nz)
    g = (xr, y_wall - ny, z_wall - nz)
    h = (xl, y_wall - ny, z_wall - nz)
    mb.rect([a, b, c, d], region)
    mb.rect([f, e, h, g], region)
    mb.rect([e, a, d, h], region)
    mb.rect([b, f, g, c], region)
    mb.rect([e, f, b, a], region)
    mb.rect([c, g, h, d], region)


def _add_diagonal_strut_x(mb, y, x_wall, z_wall, x_tip, z_tip, half_w=0.025, region="trim_silver"):
    """Closed 3D diagonal steel canopy tie-rod/brace along X-Z plane (for side shutters)."""
    dx = x_wall - x_tip
    dz = z_wall - z_tip
    L = math.hypot(dx, dz)
    nx, nz = -dz / L * half_w, dx / L * half_w
    yl, yr = y - half_w, y + half_w
    a = (x_tip + nx, yl, z_tip + nz)
    b = (x_tip + nx, yr, z_tip + nz)
    c = (x_wall + nx, yr, z_wall + nz)
    d = (x_wall + nx, yl, z_wall + nz)
    e = (x_tip - nx, yl, z_tip - nz)
    f = (x_tip - nx, yr, z_tip - nz)
    g = (x_wall - nx, yr, z_wall - nz)
    h = (x_wall - nx, yl, z_wall - nz)
    mb.rect([b, a, d, c], region)
    mb.rect([e, f, g, h], region)
    mb.rect([a, e, h, d], region)
    mb.rect([f, b, c, g], region)
    mb.rect([f, e, a, b], region)
    mb.rect([d, h, g, c], region)


def _add_canopy_brace(mb, axis, c, s, pos_a, z_wall, o_tip, z_tip, half_w=0.024, region="trim_silver"):
    if axis == "y":
        _add_diagonal_strut_y(mb, pos_a, c, z_wall, c + s * o_tip, z_tip, half_w=half_w, region=region)
    else:
        _add_diagonal_strut_x(mb, pos_a, c, z_wall, c + s * o_tip, z_tip, half_w=half_w, region=region)


def _add_shutter(mb, stage, axis, c, s, center_a, w, h, z0=0.0, is_freight=True, is_track=False):
    """Roll-up freight/rail-track shutter with framed jambs, braced rain canopy, floodlight & safety bollards."""
    a0, a1 = center_a - w * 0.5, center_a + w * 0.5
    z1 = z0 + h
    if stage == 0:
        # Concrete threshold apron (plus steel track rail stubs for RailDepot)
        apron_d = 1.25 if is_track else 0.75
        K.axbox(mb, axis, c, s, a0 - 0.35, a1 + 0.35, 0.0, apron_d, 0.0, 0.05, "plinth", skip=("bottom",))
        if is_track:
            for rx in (center_a - 0.72, center_a + 0.72):
                K.axbox(mb, axis, c, s, rx - 0.05, rx + 0.05, 0.0, apron_d - 0.05, 0.05, 0.11, "trim_silver", skip=("bottom",))

        K.axbox(mb, axis, c, s, a0, a1, 0.0, 0.05, z0, z1, "shutter", skip=("bottom",))
        fw = 0.16 if is_track else 0.14
        K.axbox(mb, axis, c, s, a0 - fw, a0, 0.0, 0.15, z0, z1, "frame", skip=("bottom",))
        K.axbox(mb, axis, c, s, a1, a1 + fw, 0.0, 0.15, z0, z1, "frame", skip=("bottom",))
        # Roll-up shutter hood box + hazard height-limit stripe
        K.axbox(mb, axis, c, s, a0 - fw, a1 + fw, 0.0, 0.32, z1 + 0.14, z1 + 0.52, "frame")
        K.axbox(mb, axis, c, s, a0 - fw, a1 + fw, 0.0, 0.25, z1, z1 + 0.14, "hazard_stripe")

        if is_freight or is_track:
            aw_d = 1.10 if is_track else 0.95
            aw_z0 = z1 + 0.52
            aw_z1 = aw_z0 + 0.11
            K.axbox(mb, axis, c, s, a0 - 0.32, a1 + 0.32, 0.0, aw_d, aw_z0, aw_z1, "band_blue")
            K.axbox(mb, axis, c, s, a0 - 0.34, a1 + 0.34, aw_d, aw_d + 0.04, aw_z0 - 0.01, aw_z1 + 0.02, "trim_silver")
            K.axbox(mb, axis, c, s, center_a - 0.34, center_a + 0.34, 0.35, 0.55, aw_z0 - 0.07, aw_z0, "light_warm")
            for bx in (a0 + 0.25, a1 - 0.25):
                _add_canopy_brace(mb, axis, c, s, bx, aw_z1 + 0.65, aw_d * 0.85, aw_z1, half_w=0.022, region="trim_silver")

        if is_track:
            # Yard entry warning signal lamp on right portal jamb
            K.axbox(mb, axis, c, s, a1 + fw + 0.04, a1 + fw + 0.34, 0.0, 0.18, z1 - 1.15, z1 - 0.65, "frame")
            K.axbox(mb, axis, c, s, a1 + fw + 0.09, a1 + fw + 0.29, 0.18, 0.22, z1 - 1.08, z1 - 0.72, "signal_red")
        elif is_freight:
            for jx in (a0 - 0.12, a1 + 0.12):
                K.axbox(mb, axis, c, s, jx - 0.07, jx + 0.07, 0.15, 0.25, 0.35, 1.25, "frame")

        # Safety bollards outside jambs with dark steel base collars
        b_off0 = 0.30
        b_off1 = 0.48
        for bx in (a0 - 0.40, a1 + 0.40):
            K.axbox(mb, axis, c, s, bx - 0.10, bx + 0.10, b_off0 - 0.01, b_off1 + 0.01, 0.0, 0.12, "frame", skip=("bottom",))
            K.axbox(mb, axis, c, s, bx - 0.085, bx + 0.085, b_off0, b_off1, 0.12, 0.96, "safety_yellow", skip=("bottom",))
    elif stage == 1:
        K.paint(mb, axis, c, s, a0, a1, z0, z1, "shutter")
        K.paint(mb, axis, c, s, a0 - 0.14, a1 + 0.14, z1, z1 + 0.44, "frame")
        if is_freight or is_track:
            aw_d = 0.95 if is_track else 0.75
            K.axbox(mb, axis, c, s, a0 - 0.25, a1 + 0.25, 0.0, aw_d, z1 + 0.46, z1 + 0.58, "band_blue")
    else:
        K.paint(mb, axis, c, s, a0, a1, z0, z1, "shutter")


def _add_exit_door(mb, atlas, axis, c, s, center_a):
    """Industrial steel fire/personnel exit door with metal rain hood and warm safety light."""
    a0, a1 = center_a - 0.55, center_a + 0.55
    K.axbox(mb, axis, c, s, a0 - 0.08, a1 + 0.08, 0.0, 0.07, 0.0, 2.25, "frame", skip=("bottom",))
    mb.quad(K.face_pts(axis, c + s * 0.075, s, a0, a1, 0.0, 2.18), atlas.uv_full("exit_door"), "exit_door")
    K.axbox(mb, axis, c, s, a0 - 0.26, a1 + 0.26, 0.0, 0.65, 2.28, 2.38, "trim_silver")
    K.axbox(mb, axis, c, s, center_a - 0.18, center_a + 0.18, 0.0, 0.12, 2.40, 2.52, "light_warm")


def _add_wall_exhaust_hood(mb, atlas, axis, c, s, center_a, z0, w=1.30, h=1.30):
    """Framed wall ventilation louver with sloped/projecting galvanized rain hood."""
    hw = w * 0.5
    K.axbox(mb, axis, c, s, center_a - hw, center_a + hw, 0.0, 0.12, z0, z0 + h, "frame")
    K.axbox(mb, axis, c, s, center_a - hw + 0.08, center_a + hw - 0.08, 0.12, 0.20, z0 + 0.08, z0 + h - 0.08, "louver_vent")
    K.axbox(mb, axis, c, s, center_a - hw - 0.06, center_a + hw + 0.06, 0.0, 0.36, z0 + h - 0.04, z0 + h + 0.10, "trim_silver")


def _add_gable_louver(mb, stage, y, s, xm, span_w, eh, ridge_rise):
    """Iconic Korean gable-peak ventilation louver centered under ridge apex."""
    if ridge_rise < 1.0 or stage == 2:
        return
    lw = min(2.6, max(1.6, span_w * 0.11))
    lz0 = eh + ridge_rise * 0.42
    lz1 = min(eh + ridge_rise - 0.35, lz0 + 0.85)
    if lz1 - lz0 < 0.45:
        return
    if stage == 0:
        K.axbox(mb, "y", y, s, xm - lw * 0.5 - 0.07, xm + lw * 0.5 + 0.07, 0.0, 0.07, lz0 - 0.06, lz1 + 0.06, "frame")
        K.axbox(mb, "y", y, s, xm - lw * 0.5, xm + lw * 0.5, 0.07, 0.12, lz0, lz1, "louver_vent")
    else:
        K.paint(mb, "y", y, s, xm - lw * 0.5, xm + lw * 0.5, lz0, lz1, "louver_vent")


def _add_gutters_and_downspouts(mb, spec: FactorySpec, x0, x1, y0, y1, ry0, ry1, eh, ze_u, col_ys, eq_span=None):
    """Exterior eave rain gutters seated flush at overhang edge, collector elbows, downspouts & pilasters."""
    band_z0 = eh - 0.72
    ph = spec.plinth_h

    # Flush eave gutters against roof overhang edges (no 5mm gap)
    gx_l = x0 - spec.roof_overhang
    gx_r = x1 + spec.roof_overhang
    mb.box(gx_l - 0.12, gx_l + 0.01, ry0 + 0.03, ry1 - 0.03, ze_u - 0.14, ze_u + 0.05, "band_blue")
    mb.box(gx_r - 0.01, gx_r + 0.12, ry0 + 0.03, ry1 - 0.03, ze_u - 0.14, ze_u + 0.05, "band_blue")

    for side_x, side_s, gx_edge in ((x0, -1, gx_l), (x1, 1, gx_r)):
        for cy in col_ys:
            if side_s < 0 and eq_span and eq_span[0] - 0.35 <= cy <= eq_span[1] + 0.35:
                continue
            K.axbox(mb, "x", side_x, side_s, cy - 0.11, cy + 0.11, 0.0, 0.05, ph, band_z0, "trim_silver", skip=("bottom",))
        ds_ys = [col_ys[0], col_ys[-1]]
        for cy in col_ys[1:-1]:
            if side_s < 0 and eq_span and eq_span[0] - 0.4 <= cy <= eq_span[1] + 0.4:
                continue
            ds_ys.append(cy)
            break
        for dy in ds_ys:
            ex0, ex1 = sorted((gx_edge, side_x))
            mb.box(ex0, ex1, dy - 0.06, dy + 0.06, ze_u - 0.24, ze_u - 0.14, "trim_silver", skip=("top",))
            K.axbox(mb, "x", side_x, side_s, dy - 0.055, dy + 0.055, 0.02, 0.13, 0.20, ze_u - 0.24, "trim_silver", skip=("bottom", "top"))
            K.axbox(mb, "x", side_x, side_s, dy - 0.07, dy + 0.07, 0.02, 0.20, 0.05, 0.20, "trim_silver")
            for sz in (1.8, 0.5 * (1.8 + ze_u - 0.8), ze_u - 0.9):
                K.axbox(mb, "x", side_x, side_s, dy - 0.08, dy + 0.08, 0.0, 0.15, sz - 0.04, sz + 0.04, "frame")


def _compute_office_bounds(spec: FactorySpec):
    if not spec.office.enabled:
        return None
    x0, x1 = -spec.width * 0.5, spec.width * 0.5
    ow = min(spec.office.width, spec.width - 2.0)
    if spec.office.align == "left":
        ox0 = x0 + 0.5
        ox1 = ox0 + ow
    elif spec.office.align == "right":
        ox1 = x1 - 0.5
        ox0 = ox1 - ow
    elif spec.office.align == "full":
        ox0, ox1 = x0, x1
    else:
        ox0, ox1 = -ow * 0.5, ow * 0.5
    return ox0, ox1, -spec.office.depth, 0.0, spec.office.height


def _build_office(mb, wins, atlas, spec: FactorySpec, stage, ob):
    ox0, ox1, oy0, oy1, oh = ob
    ph = min(spec.plinth_h, 0.85)
    # Continuous plinth + horizontal Alucobond office cladding + dark rooftop membrane
    if stage < 2:
        mb.box(ox0, ox1, oy0, oy1, 0.0, ph, "plinth", skip=("bottom", "top", "back"))
        mb.box(ox0, ox1, oy0, oy1, ph, oh, dict(default="office_panel", top="plinth"), skip=("bottom", "back"))
        pt = 0.24
        ph_top = oh + spec.office.parapet_h
        mb.box(ox0 - 0.05, ox1 + 0.05, oy0 - 0.05, oy0 + pt, oh, ph_top,
               dict(default="band_blue", top="trim_silver"), skip=("bottom",))
        mb.box(ox0 - 0.05, ox0 + pt, oy0 + pt + 0.005, oy1, oh, ph_top,
               dict(default="band_blue", top="trim_silver"), skip=("bottom", "back"))
        mb.box(ox1 - pt, ox1 + 0.05, oy0 + pt + 0.005, oy1, oh, ph_top,
               dict(default="band_blue", top="trim_silver"), skip=("bottom", "back"))
    else:
        mb.box(ox0, ox1, oy0, oy1, 0.0, ph, "plinth", skip=("bottom", "top", "back"))
        mb.box(ox0, ox1, oy0, oy1, ph, oh - 0.36, "office_panel", skip=("bottom", "top", "back"))
        mb.box(ox0, ox1, oy0, oy1, oh - 0.36, oh, dict(default="band_blue", top="plinth"), skip=("bottom", "back"))

    if spec.office.door_side == "right":
        door_x = ox1 - 2.2
    elif spec.office.door_side == "center":
        door_x = 0.5 * (ox0 + ox1)
    else:
        door_x = ox0 + 2.2
    if stage == 0:
        # 2-step concrete landing pad + threshold riser
        mb.box(door_x - 1.45, door_x + 1.45, oy0 - 1.15, oy0, 0.0, 0.08, "plinth", skip=("bottom", "back"))
        mb.box(door_x - 1.32, door_x + 1.32, oy0 - 0.90, oy0, 0.08, 0.16, "plinth", skip=("bottom", "back"))
        # Flanking entrance pilasters + recessed glazed vestibule door + upper transom bar
        K.axbox(mb, "y", oy0, -1, door_x - 1.12, door_x - 0.96, 0.0, 0.12, 0.16, 2.48, "frame", skip=("bottom", "top"))
        K.axbox(mb, "y", oy0, -1, door_x + 0.96, door_x + 1.12, 0.0, 0.12, 0.16, 2.48, "frame", skip=("bottom", "top"))
        K.axbox(mb, "y", oy0, -1, door_x - 1.12, door_x + 1.12, 0.0, 0.12, 2.48, 2.66, "frame")
        mb.quad([(door_x - 0.96, oy0 - 0.05, 0.16), (door_x + 0.96, oy0 - 0.05, 0.16),
                 (door_x + 0.96, oy0 - 0.05, 2.48), (door_x - 0.96, oy0 - 0.05, 2.48)],
                atlas.uv_full("door"), "door")

        # Sleek dual-tone entrance canopy + steel tie-rod hangers + under-soffit light
        mb.box(door_x - 1.72, door_x + 1.72, oy0 - 1.45, oy0, 2.68, 2.82,
               dict(default="band_blue", top="trim_silver", bottom="trim_silver"), skip=("back",))
        mb.box(door_x - 1.74, door_x + 1.74, oy0 - 1.48, oy0 - 1.43, 2.67, 2.84, "trim_silver")
        K.axbox(mb, "y", oy0, -1, door_x - 0.36, door_x + 0.36, 0.35, 0.55, 2.62, 2.68, "light_warm")
        for rx in (door_x - 1.35, door_x + 1.35):
            _add_diagonal_strut_y(mb, rx, oy0, 3.60, oy0 - 1.20, 2.82, half_w=0.024, region="trim_silver")

        # Illuminated corporate signboard: upper 2F fascia (Large) or spandrel beside canopy (Small/Mid)
        if spec.office.sign_zone == "fascia":
            sw = min(5.4, max(2.8, (ox1 - ox0) * 0.32))
            sx_c = 0.5 * (ox0 + ox1)
            sz0 = max(5.84, oh - 1.38)
            sz1 = min(oh - 0.38, sz0 + 0.88)
        else:
            sw = min(3.8, max(2.2, (ox1 - ox0) * 0.32))
            if spec.office.door_side == "right":
                sx_c = max(ox0 + sw * 0.5 + 0.6, min(door_x - 1.65 - sw * 0.5, 0.5 * (ox0 + ox1) - 0.8))
            else:
                sx_c = min(ox1 - sw * 0.5 - 0.6, max(door_x + 1.65 + sw * 0.5, 0.5 * (ox0 + ox1) + 0.8))
            sz0, sz1 = 2.93, 3.61
        K.axbox(mb, "y", oy0, -1, sx_c - sw * 0.5 - 0.06, sx_c + sw * 0.5 + 0.06, 0.0, 0.06, sz0 - 0.05, sz1 + 0.05, "frame")
        cell, fu0, fv0, fu1, fv1 = SIGN_SUB[spec.sign_key]
        mb.quad([(sx_c - sw * 0.5, oy0 - 0.065, sz0), (sx_c + sw * 0.5, oy0 - 0.065, sz0),
                 (sx_c + sw * 0.5, oy0 - 0.065, sz1), (sx_c - sw * 0.5, oy0 - 0.065, sz1)],
                atlas.uv_sub(cell, fu0, fv0, fu1, fv1), cell)

        # Continuous horizontal spandrel sill flashing below 2F windows (clear of frames)
        K.axbox(mb, "y", oy0, -1, ox0 + 0.70, ox1 - 0.70, 0.0, 0.05, 3.84, 3.92, "trim_silver")

        # Rooftop outdoor AC condensers on mounting rails + refrigerant pipe conduit + roof hatch
        n_ac = 2 if (ox1 - ox0) < 13.0 else 3
        ac_on_left = (spec.office.align == "right")
        if ac_on_left:
            ac_x0 = ox0 + 1.8
            rail_x0, rail_x1 = ac_x0 - 0.55, ac_x0 + (n_ac - 1) * 1.45 + 0.55
            mb.box(rail_x0, rail_x1, oy0 + 1.05, oy0 + 1.70, oh, oh + 0.12, "frame", skip=("bottom",))
            for ai in range(n_ac):
                cx = ac_x0 + ai * 1.45
                mb.box(cx - 0.46, cx + 0.46, oy0 + 1.12, oy0 + 1.63, oh + 0.12, oh + 1.08,
                       dict(default="equipment", top="trim_silver"), skip=("bottom",))
            mb.box(ac_x0 - 0.3, rail_x1 - 0.2, oy0 + 1.70, oy0 + 1.86, oh + 0.18, oh + 0.30, "trim_silver")
            mb.box(rail_x1 - 0.25, rail_x1 + 0.35, oy0 + 1.65, oy0 + 2.15, oh, oh + 0.42, "trim_silver", skip=("bottom",))
            hx0, hx1 = ox1 - 2.2, ox1 - 1.0
        else:
            ac_x0 = ox1 - 1.8
            rail_x0 = ac_x0 - (n_ac - 1) * 1.45 - 0.55
            mb.box(rail_x0, ac_x0 + 0.55, oy0 + 1.05, oy0 + 1.70, oh, oh + 0.12, "frame", skip=("bottom",))
            for ai in range(n_ac):
                cx = ac_x0 - ai * 1.45
                mb.box(cx - 0.46, cx + 0.46, oy0 + 1.12, oy0 + 1.63, oh + 0.12, oh + 1.08,
                       dict(default="equipment", top="trim_silver"), skip=("bottom",))
            mb.box(rail_x0 + 0.2, ac_x0 + 0.3, oy0 + 1.70, oy0 + 1.86, oh + 0.18, oh + 0.30, "trim_silver")
            mb.box(rail_x0 - 0.35, rail_x0 + 0.25, oy0 + 1.65, oy0 + 2.15, oh, oh + 0.42, "trim_silver", skip=("bottom",))
            hx0, hx1 = ox0 + 1.0, ox0 + 2.2
        # Steel roof access hatch with curb and handle bar
        mb.box(hx0, hx1, oy0 + 1.15, oy0 + 2.35, oh, oh + 0.24, "frame", skip=("bottom",))
        mb.box(hx0 - 0.06, hx1 + 0.06, oy0 + 1.09, oy0 + 2.41, oh + 0.24, oh + 0.36, "trim_silver")
    elif stage == 1:
        K.paint(mb, "y", oy0, -1, door_x - 1.0, door_x + 1.0, 0.0, 2.50, "door")
        mb.box(door_x - 1.65, door_x + 1.65, oy0 - 1.40, oy0, 2.62, 2.80, "band_blue", skip=("back",))
    else:
        K.paint(mb, "y", oy0, -1, door_x - 1.0, door_x + 1.0, 0.0, 2.50, "door")

    # Organic per-room night-lit office windows on 1F (floor=0) and 2F (floor=1) + side flanks
    if stage == 0:
        if spec.office.door_side == "center":
            win_spans_1f = [(ox0 + 0.85, door_x - 1.95, 17), (door_x + 1.95, ox1 - 0.85, 19)]
        elif spec.office.door_side == "right":
            win_spans_1f = [(ox0 + 0.85, door_x - 1.95, 17)]
        else:
            win_spans_1f = [(door_x + 1.95, ox1 - 0.85, 17)]
        for win_x0, win_x1, w_seed in win_spans_1f:
            if win_x1 - win_x0 >= 2.0:
                bays_1f = max(2, int((win_x1 - win_x0) / 1.8))
                u_1f = [_win_unit_for(0, i // 2, seed=w_seed) for i in range(bays_1f)]
                _add_framed_window(mb, wins, stage, "y", oy0, -1, win_x0, win_x1, 0.92, 2.42,
                                   floor=0, unit_seq=u_1f, bays=bays_1f)

        wx0_2f, wx1_2f = ox0 + 0.85, ox1 - 0.85
        wxm_2f = 0.5 * (wx0_2f + wx1_2f)
        bays_half = max(2, int((wxm_2f - wx0_2f) / 1.75))
        u_2f_l = [_win_unit_for(1, i // 2, seed=23) for i in range(bays_half)]
        u_2f_r = [_win_unit_for(1, (i + 10) // 2, seed=29) for i in range(bays_half)]
        _add_framed_window(mb, wins, stage, "y", oy0, -1, wx0_2f, wxm_2f - 0.08, 4.05, 5.65,
                           floor=0, unit_seq=u_2f_l, bays=bays_half)
        _add_framed_window(mb, wins, stage, "y", oy0, -1, wxm_2f + 0.08, wx1_2f, 4.05, 5.65,
                           floor=0, unit_seq=u_2f_r, bays=bays_half)

        side_flanks = [(-1, ox0), (1, ox1)] if spec.office.align == "center" else (
            [(1, ox1)] if spec.office.align == "right" else [(-1, ox0)]
        )
        for fi, (side_s, side_x) in enumerate(side_flanks):
            u_side_2f = [_win_unit_for(1, 30 + fi * 4 + i, seed=31) for i in range(2)]
            _add_framed_window(mb, wins, stage, "x", side_x, side_s, oy0 + 0.85, oy1 - 0.85, 4.05, 5.65,
                               floor=0, unit_seq=u_side_2f, bays=2)
            u_side_1f = [_win_unit_for(0, 30 + fi * 4 + i, seed=37) for i in range(2)]
            _add_framed_window(mb, wins, stage, "x", side_x, side_s, oy0 + 0.85, oy1 - 0.85, 0.92, 2.42,
                               floor=0, unit_seq=u_side_1f, bays=2)


def _add_side_equipment(mb, spec: FactorySpec, stage, x0, eh, y0, D, stack_y):
    """Exterior dust collector, connecting duct, cyclone stack with wall brackets & utility cage."""
    cab_y1 = stack_y + 0.75
    cab_y0 = cab_y1 - 1.6
    eq_y1 = cab_y0 - 0.35
    eq_y0 = eq_y1 - 3.0
    cz0 = eh - 2.35
    cone_top = min(5.1, cz0 - 0.35)

    # Concrete utility pad + collector cabinet
    mb.box(x0 - 1.65, x0, eq_y0 - 0.12, cab_y1 + 0.12, 0.0, 0.08, "plinth", skip=("bottom", "right"))
    mb.box(x0 - 1.55, x0, eq_y0, eq_y1, 0.08, 2.65,
           dict(default="equipment", top="trim_silver"), skip=("bottom", "right"))
    if stage == 0:
        mb.box(x0 - 1.35, x0 - 0.25, cab_y0, cab_y1, 0.08, 3.5,
               dict(default="equipment", top="trim_silver"), skip=("bottom",))
        # Inter-cabinet upper transition duct + wall intake box
        mb.box(x0 - 1.15, x0 - 0.45, eq_y1, cab_y0, 2.15, 2.62, "trim_silver")
        mb.box(x0 - 0.25, x0, stack_y - 0.40, stack_y + 0.40, 2.3, 3.1, "frame", skip=("left", "right"))
        # 8-sided cyclone separator + slender exhaust stack strictly aligned on solid pier
        cx = x0 - 0.80
        _add_frustum_z(mb, cx, stack_y, 3.5, cone_top, 0.50, 0.44, 8, "trim_silver", cap_top=True)
        _add_frustum_z(mb, cx, stack_y, cone_top, eh + 1.0, 0.22, 0.22, 8, "trim_silver", cap_top=False)
        _add_frustum_z(mb, cx, stack_y, eh + 1.0, eh + 1.35, 0.38, 0.06, 8, "trim_silver", cap_top=True)
        # Wall-standoff steel pipe support brackets along the tall stack
        for bz in (cone_top + 1.2, eh - 0.5):
            if bz > cone_top + 0.3 and bz < eh + 0.8:
                mb.box(x0 - 0.84, x0, stack_y - 0.26, stack_y + 0.26, bz - 0.04, bz + 0.04, "frame", skip=("right",))
        # Adjacent gas/electrical safety cabinet on Mid/Large
        if D >= 30.0 and eq_y0 > y0 + 5.5:
            gy1 = eq_y0 - 0.6
            gy0 = gy1 - 2.2
            mb.box(x0 - 1.10, x0, gy0, gy1, 0.0, 0.08, "plinth", skip=("bottom", "right"))
            mb.box(x0 - 0.98, x0, gy0 + 0.1, gy1 - 0.1, 0.08, 2.05,
                   dict(default="louver_vent", top="trim_silver"), skip=("bottom", "right"))
            mb.box(x0 - 1.08, x0 - 1.00, gy0, gy1, 0.08, 1.05, "safety_yellow", skip=("bottom",))
            return (gy0, cab_y1)
    return (eq_y0, cab_y1)


def _add_depot_equipment(mb, stage, x0, eh, y0, D, pier_ys):
    """Rail depot substation switchgear enclosure, compressed-air receiver & eave access ladder."""
    mid_y = pier_ys[max(0, len(pier_ys) // 2)] if pier_ys else (y0 + D * 0.5)
    sub_y0, sub_y1 = mid_y - 3.0, mid_y + 0.6
    # Concrete equipment pad + substation switchgear enclosure
    mb.box(x0 - 1.80, x0, sub_y0 - 0.20, sub_y1 + 0.20, 0.0, 0.10, "plinth", skip=("bottom", "right"))
    mb.box(x0 - 1.65, x0, sub_y0, sub_y1, 0.10, 2.75,
           dict(default="equipment", left="louver_vent", top="trim_silver"), skip=("bottom", "right"))
    if stage == 0:
        # High-voltage warning stripe + crash bollards around substation
        mb.box(x0 - 1.68, x0 - 1.65, sub_y0 + 0.2, sub_y1 - 0.2, 2.20, 2.40, "hazard_stripe")
        for by in (sub_y0 - 0.15, sub_y1 + 0.15):
            mb.box(x0 - 1.98, x0 - 1.80, by - 0.09, by + 0.09, 0.0, 0.95, "safety_yellow", skip=("bottom",))
        # Vertical compressed-air receiver tank on pad just north of substation
        tx, ty = x0 - 0.95, sub_y1 + 1.45
        mb.box(x0 - 1.55, x0, ty - 0.65, ty + 0.65, 0.0, 0.10, "plinth", skip=("bottom", "right"))
        _add_frustum_z(mb, tx, ty, 0.10, 0.45, 0.34, 0.46, 8, "frame", cap_top=False)
        _add_frustum_z(mb, tx, ty, 0.45, 2.95, 0.46, 0.46, 8, "band_blue", cap_top=False)
        _add_frustum_z(mb, tx, ty, 2.95, 3.30, 0.46, 0.12, 8, "band_blue", cap_top=True)
        # Header pipe feeding depot interior
        mb.box(x0 - 0.95, x0, ty - 0.08, ty + 0.08, 2.40, 2.56, "trim_silver", skip=("right",))
        # Exterior steel roof-access cage ladder aligned strictly to solid pier
        lad_y = mid_y + 2.8 if (len(pier_ys) > 3) else mid_y
        # Find nearest pier_y not near sub_y0..ty+0.65
        for py in pier_ys:
            if py > ty + 1.2 or py < sub_y0 - 1.2:
                lad_y = py
                break
        for ry in (lad_y - 0.24, lad_y + 0.24):
            K.axbox(mb, "x", x0, -1, ry - 0.03, ry + 0.03, 0.18, 0.24, 2.40, eh + 0.25, "frame")
        for rz in np.arange(2.6, eh + 0.1, 0.38):
            K.axbox(mb, "x", x0, -1, lad_y - 0.22, lad_y + 0.22, 0.19, 0.23, float(rz), float(rz) + 0.03, "trim_silver")
        for bz in (2.5, 5.5, 8.5):
            if bz < eh - 0.5:
                K.axbox(mb, "x", x0, -1, lad_y - 0.26, lad_y + 0.26, 0.0, 0.20, bz, bz + 0.06, "frame")
        return (sub_y0 - 0.2, ty + 0.7)
    return (sub_y0 - 0.2, sub_y1 + 0.2)


def _build_stage(spec: FactorySpec, atlas, stage):
    """stage: 0=main, 1=lod1, 2=lod2"""
    mb = K.MeshBuilder(atlas, split_tiles=(stage == 0))
    wins = K.WindowSet() if stage == 0 else None

    W, D = spec.width, spec.depth
    x0, x1 = -W * 0.5, W * 0.5
    y0, y1 = 0.0, D
    eh = spec.eave_h
    ph = spec.plinth_h
    band_z0 = eh - 0.72

    # 1. Main Hall Walls (stacked closed box tiers -> eliminates floating 1cm band_blue seam holes!)
    mb.box(x0, x1, y0, y1, 0.0, ph, "plinth", skip=("bottom", "top"))
    mb.box(x0, x1, y0, y1, ph, band_z0, "wall_panel", skip=("bottom", "top"))
    mb.box(x0, x1, y0, y1, band_z0, eh, "band_blue", skip=("bottom", "top"))

    # Horizontal steel drip flashing along front & back eave transition (z = eh)
    if stage == 0:
        for fy, fs in ((y0, -1), (y1, 1)):
            K.axbox(mb, "y", fy, fs, x0, x1, 0.0, 0.04, eh - 0.05, eh + 0.01, "trim_silver")

    # 2. Gable End Triangles & Gable Roof Spans
    span_w = W / spec.gables
    slope = spec.ridge_rise / (span_w * 0.5)
    ry0 = y0 - (spec.roof_overhang if stage < 2 else 0.25)
    ry1 = y1 + (spec.roof_overhang if stage < 2 else 0.25)
    rt = spec.roof_t if stage < 2 else 0.22

    for gi in range(spec.gables):
        sx0 = x0 + gi * span_w
        sx1 = sx0 + span_w
        sxm = 0.5 * (sx0 + sx1)

        _add_gable_end_walls(mb, atlas, sx0, sx1, y0, y1, eh, spec.ridge_rise, "wall_panel", split_tiles=(stage < 2))

        oh_l = (spec.roof_overhang if stage < 2 else 0.25) if gi == 0 else 0.0
        oh_r = (spec.roof_overhang if stage < 2 else 0.25) if gi == spec.gables - 1 else 0.0
        gx0, gx1 = sx0 - oh_l, sx1 + oh_r
        ze_l_u = eh - oh_l * slope
        ze_r_u = eh - oh_r * slope
        zr_u = eh + spec.ridge_rise

        _add_gable_roof_span(
            mb, gx0, gx1, ry0, ry1, ze_l_u, ze_r_u, zr_u, rt,
            emit_left_edge=(gi == 0),
            emit_right_edge=(gi == spec.gables - 1),
            roof_reg="roof_blue",
            trim_reg="band_blue" if stage == 2 else "trim_silver",
            soffit_reg="wall_panel",
        )

        # Ridge cap flashing
        if stage < 2:
            mb.box(sxm - 0.20, sxm + 0.20, ry0 + 0.01, ry1 - 0.01, zr_u + rt, zr_u + rt + 0.07,
                   "band_blue", skip=("bottom",))

        if spec.gable_louvers and not (spec.roof_monitor and gi == 0):
            _add_gable_louver(mb, stage, y0, -1, sxm, span_w, eh, spec.ridge_rise)
            _add_gable_louver(mb, stage, y1, 1, sxm, span_w, eh, spec.ridge_rise)

        if stage == 0:
            if spec.skylight_rows > 0:
                u_l0, u_l1 = spec.skylight_u
                u_r0, u_r1 = 1.0 - u_l1, 1.0 - u_l0
                n_rows = max(1, spec.skylight_rows)
                usable_y = D - 4.4
                seg_len = usable_y / n_rows
                bay_l = (D - 4.0) / max(1, spec.clerestory_bays)

                if spec.skylight_pattern == "staggered":
                    for si in range(n_rows):
                        sy0 = y0 + 2.2 + si * seg_len + seg_len * (1.0 - spec.skylight_fill) * 0.5
                        sy1 = sy0 + seg_len * spec.skylight_fill
                        if sy1 > sy0 + 1.0:
                            if si % 2 == 0:
                                _add_skylight_strip(mb, gx0, gx1, ze_l_u, zr_u, rt, sy0, sy1, u_l0, u_l1, side="left", bay_len=bay_l)
                            else:
                                _add_skylight_strip(mb, gx0, gx1, ze_r_u, zr_u, rt, sy0, sy1, u_r0, u_r1, side="right", bay_len=bay_l)
                elif spec.skylight_pattern == "twin_varied" and spec.gables == 2:
                    # Outer slopes get full bay cassettes; inner valley slopes stay higher toward ridge & staggered
                    for si in range(n_rows):
                        sy0 = y0 + 2.2 + si * seg_len + seg_len * (1.0 - spec.skylight_fill) * 0.5
                        sy1 = sy0 + seg_len * spec.skylight_fill
                        if sy1 > sy0 + 1.0:
                            if gi == 0:
                                _add_skylight_strip(mb, gx0, gx1, ze_l_u, zr_u, rt, sy0, sy1, u_l0, u_l1, side="left", bay_len=bay_l)
                            else:
                                _add_skylight_strip(mb, gx0, gx1, ze_r_u, zr_u, rt, sy0, sy1, u_r0, u_r1, side="right", bay_len=bay_l)
                    inner_rows = max(1, n_rows - 1)
                    in_seg = usable_y / inner_rows
                    for si in range(inner_rows):
                        sy0 = y0 + 2.2 + si * in_seg + in_seg * 0.18
                        sy1 = sy0 + in_seg * 0.56
                        if sy1 > sy0 + 1.0:
                            if gi == 0:
                                _add_skylight_strip(mb, gx0, gx1, ze_r_u, zr_u, rt, sy0, sy1, 0.24, 0.39, side="right", bay_len=bay_l)
                            else:
                                _add_skylight_strip(mb, gx0, gx1, ze_l_u, zr_u, rt, sy0, sy1, 0.61, 0.76, side="left", bay_len=bay_l)
                else:
                    for si in range(n_rows):
                        sy0 = y0 + 2.2 + si * seg_len + seg_len * (1.0 - spec.skylight_fill) * 0.5
                        sy1 = sy0 + seg_len * spec.skylight_fill
                        if sy1 > sy0 + 1.0:
                            _add_skylight_strip(mb, gx0, gx1, ze_l_u, zr_u, rt, sy0, sy1, u_l0, u_l1, side="left", bay_len=bay_l)
                            _add_skylight_strip(mb, gx0, gx1, ze_r_u, zr_u, rt, sy0, sy1, u_r0, u_r1, side="right", bay_len=bay_l)

            if spec.ventilators > 0 and not spec.roof_monitor:
                if spec.vent_pattern == "ridge_rear_bias":
                    y_start, y_end = y0 + max(4.0, D * 0.26), y1 - 3.2
                    v_count = spec.ventilators
                elif spec.vent_pattern == "ridge_staggered" and gi % 2 == 1:
                    v_count = max(2, spec.ventilators - 1)
                    y_start, y_end = y0 + 5.6, y1 - 5.2
                else:
                    v_count = spec.ventilators
                    y_start, y_end = y0 + 3.6, y1 - 3.6
                for vi in range(v_count):
                    vy = y_start + (y_end - y_start) * (vi / max(1, v_count - 1)) if v_count > 1 else 0.5 * (y_start + y_end)
                    _add_ventilator(mb, sxm, vy, zr_u + rt + 0.07, slope, radius=spec.vent_radius)

            if spec.roof_box_fans > 0 and not spec.roof_monitor:
                if spec.gables == 2:
                    fan_side = "left" if gi == 0 else "right"
                    fan_u = 0.74 if fan_side == "left" else 0.26
                    fan_y = y1 - 6.5 if gi == 0 else y1 - 11.0
                    _add_roof_box_fan(mb, gx0, gx1, ze_l_u if fan_side == "left" else ze_r_u, zr_u, rt,
                                      fan_y, u_frac=fan_u, side=fan_side)
                else:
                    for fi in range(spec.roof_box_fans):
                        fan_side = "left" if fi % 2 == 0 else "right"
                        fan_u = 0.74 if fan_side == "left" else 0.26
                        fan_y = y1 - 5.2 - fi * 5.8
                        if fan_y > y0 + 6.0:
                            _add_roof_box_fan(mb, gx0, gx1, ze_l_u if fan_side == "left" else ze_r_u, zr_u, rt,
                                              fan_y, u_frac=fan_u, side=fan_side)

        if spec.solar_arrays and stage < 2:
            _add_roof_solar_bank(mb, gx0, gx1, ze_l_u, zr_u, rt, y0 + 3.2, y1 - 3.2, 0.13, 0.39, side="left", stage=stage)
            _add_roof_solar_bank(mb, gx0, gx1, ze_r_u, zr_u, rt, y0 + 3.2, y1 - 3.2, 0.61, 0.87, side="right", stage=stage)

    # Twin-gable valley gutter + rear central collector hopper & downspout
    if spec.gables == 2 and stage < 2:
        mb.box(-0.24, 0.24, ry0 + 0.02, ry1 - 0.02, eh + rt, eh + rt + 0.07, "trim_silver", skip=("bottom",))
        if stage == 0:
            mb.box(-0.18, 0.18, y1, ry1 - 0.02, eh - 0.18, eh + rt, "trim_silver")
            K.axbox(mb, "y", y1, 1, -0.07, 0.07, 0.02, 0.16, 0.20, eh - 0.18, "trim_silver", skip=("bottom", "top"))
            K.axbox(mb, "y", y1, 1, -0.08, 0.08, 0.02, 0.22, 0.05, 0.20, "trim_silver")

    # Optional raised clerestory roof monitor (Rail Depot: total apex ~14.45m matching TASK.md 14.5m)
    if spec.roof_monitor:
        mw = 6.4
        my0, my1 = y0 + 2.6, y1 - 2.6
        m_rise = 0.72
        mz0 = eh + spec.ridge_rise - (mw * 0.5) * slope
        mz1 = eh + spec.ridge_rise + rt + 0.92
        mb.box(-mw * 0.5, mw * 0.5, my0, my1, mz0, mz1, "wall_panel", skip=("bottom", "top"))
        _add_gable_end_walls(mb, atlas, -mw * 0.5, mw * 0.5, my0, my1, mz1, m_rise, "wall_panel", split_tiles=(stage < 2))
        _add_gable_roof_span(
            mb, -mw * 0.5 - 0.30, mw * 0.5 + 0.30, my0 - 0.30, my1 + 0.30,
            mz1 - 0.30 * (m_rise / (mw * 0.5)), mz1 - 0.30 * (m_rise / (mw * 0.5)), mz1 + m_rise, 0.18,
            roof_reg="roof_blue", trim_reg="band_blue" if stage == 2 else "trim_silver", soffit_reg="wall_panel",
        )
        if stage == 0:
            mb.box(-0.16, 0.16, my0 - 0.28, my1 + 0.28, mz1 + m_rise + 0.18, mz1 + m_rise + 0.24, "band_blue", skip=("bottom",))
            # Monitor end gable louvers + framed side clerestory skylight strips
            for m_y, m_s in ((my0, -1), (my1, 1)):
                K.axbox(mb, "y", m_y, m_s, -1.0, 1.0, 0.0, 0.06, mz1 - 0.20, mz1 + 0.32, "louver_vent")
            m_bays = 6
            m_step = (my1 - my0 - 2.0) / m_bays
            for side_x, side_s in ((-mw * 0.5, -1), (mw * 0.5, 1)):
                for mbi in range(m_bays):
                    ba0 = my0 + 1.0 + mbi * m_step + 0.25
                    ba1 = my0 + 1.0 + (mbi + 1) * m_step - 0.25
                    K.axbox(mb, "x", side_x, side_s, ba0 - 0.06, ba1 + 0.06, 0.0, 0.05, mz1 - 0.90, mz1 - 0.15, "frame")
                    K.axbox(mb, "x", side_x, side_s, ba0, ba1, 0.05, 0.08, mz1 - 0.84, mz1 - 0.21, "skylight_frp")
        elif stage == 1:
            for side_x, side_s in ((-mw * 0.5, -1), (mw * 0.5, 1)):
                K.axbox(mb, "x", side_x, side_s, my0 + 1.0, my1 - 1.0, 0.0, 0.05, mz1 - 0.85, mz1 - 0.20, "skylight_frp")

    # 3. Attached 2-Story Office Wing
    ob = _compute_office_bounds(spec)
    if ob is not None:
        _build_office(mb, wins, atlas, spec, stage, ob)

    # 4. Shutters / Track Portals / Rear Doors / Exhaust Louvers
    side_shutter_spans = []
    if spec.through_tracks:
        dw, dh = spec.track_door_size
        xs_c = [(-dw * 0.72 if spec.track_bays == 2 else 0.0), (dw * 0.72)] if spec.track_bays == 2 else [0.0]
        for cx in xs_c:
            _add_shutter(mb, stage, "y", y0, -1, cx, dw, dh, z0=0.0, is_freight=False, is_track=True)
            _add_shutter(mb, stage, "y", y1, 1, cx, dw, dh, z0=0.0, is_freight=False, is_track=True)
        if stage == 0:
            # Side personnel safety doors along long 55m depot flanks
            _add_exit_door(mb, atlas, "x", x1, 1, y0 + 8.5)
            _add_exit_door(mb, atlas, "x", x1, 1, y1 - 8.5)
            _add_exit_door(mb, atlas, "x", x0, -1, y0 + 8.5)
    else:
        sw, sh = spec.shutter_size
        if spec.front_shutters > 0:
            fx0 = ob[1] + 1.2 if (ob is not None and spec.office.align == "left") else x0 + 1.5
            fx1 = ob[0] - 1.2 if (ob is not None and spec.office.align == "right") else x1 - 1.5
            if ob is not None and spec.office.align == "center":
                flanks = [(x0 + 1.2, ob[0] - 1.2), (ob[1] + 1.2, x1 - 1.2)]
                for fi in range(min(spec.front_shutters, 2)):
                    a0, a1 = flanks[fi]
                    if a1 - a0 >= sw + 0.6:
                        _add_shutter(mb, stage, "y", y0, -1, 0.5 * (a0 + a1), sw, sh)
            elif fx1 - fx0 >= sw + 0.6:
                for si in range(spec.front_shutters):
                    cx = fx0 + (fx1 - fx0) * ((si + 0.5) / spec.front_shutters)
                    _add_shutter(mb, stage, "y", y0, -1, cx, sw, sh)

        rear_shutter_centers = []
        if spec.back_shutters > 0:
            for si in range(spec.back_shutters):
                cx = x0 + 2.0 + (W - 4.0) * ((si + 0.5) / spec.back_shutters)
                rear_shutter_centers.append(cx)
                _add_shutter(mb, stage, "y", y1, 1, cx, sw, sh)

        if stage == 0:
            if spec.back_shutters == 0:
                _add_exit_door(mb, atlas, "y", y1, 1, 0.0)
            elif spec.back_shutters == 1:
                _add_exit_door(mb, atlas, "y", y1, 1, x0 + 4.2)
            else:
                _add_exit_door(mb, atlas, "y", y1, 1, x0 + 3.2)

            fan_z0 = min(eh - 3.2, 5.4)
            for fx in (-0.28 * W, 0.28 * W):
                _add_wall_exhaust_hood(mb, atlas, "y", y1, 1, fx, fan_z0)

    if spec.side_shutters > 0:
        sw, sh = spec.shutter_size
        for si in range(spec.side_shutters):
            cy = y0 + 5.0 + (D - 10.0) * ((si + 0.5) / spec.side_shutters)
            _add_shutter(mb, stage, "x", x1, 1, cy, sw, sh)
            side_shutter_spans.append((cy - sw * 0.5 - 0.6, cy + sw * 0.5 + 0.6))

    # 5. High Clerestory Ribbon Windows & Structural Bay Columns / Gutters / Downspouts
    col_ys = [y0 + 0.55]
    pier_ys = []
    if spec.clerestory_bays > 0:
        cz0, cz1 = eh - 2.35, eh - 1.05
        bay_span = (D - 4.0) / spec.clerestory_bays
        for bi in range(spec.clerestory_bays):
            wa0 = y0 + 2.2 + bi * bay_span
            wa1 = wa0 + bay_span - 0.9
            if wa1 - wa0 >= 1.5 and stage == 0:
                # 본동은 한 공간: 고측창은 전부 작업장 전용 점등 칸(0..3, 전체 0..8 점등 블록 내)에 배정
                u_l = [(((bi * 2 + k) % 4) * 18) % 25 for k in range(2)]
                u_r = [(((bi * 2 + k + 2) % 4) * 18) % 25 for k in range(2)]
                _add_framed_window(mb, wins, stage, "x", x0, -1, wa0, wa1, cz0, cz1, floor=0, unit_seq=u_l, bays=2)
                _add_framed_window(mb, wins, stage, "x", x1, 1, wa0, wa1, cz0, cz1, floor=0, unit_seq=u_r, bays=2)
            col_c = y0 + 2.2 + (bi + 1) * bay_span - 0.45
            if bi < spec.clerestory_bays - 1:
                pier_ys.append(col_c)
                if not any(sa <= col_c <= sb for sa, sb in side_shutter_spans):
                    col_ys.append(col_c)
    col_ys.append(y1 - 0.55)

    # 6. Exterior Industrial / Depot Equipment (aligned to solid mullion piers)
    eq_span = None
    if spec.side_equipment and stage < 2:
        if spec.side_equipment_kind == "depot":
            eq_span = _add_depot_equipment(mb, stage, x0, eh, y0, D, pier_ys)
        else:
            stack_y = pier_ys[max(0, len(pier_ys) // 2 - 1)] if pier_ys else (y0 + D * 0.45)
            eq_span = _add_side_equipment(mb, spec, stage, x0, eh, y0, D, stack_y)

    if stage == 0:
        ze_outer_u = eh - spec.roof_overhang * slope
        _add_gutters_and_downspouts(mb, spec, x0, x1, y0, y1, ry0, ry1, eh, ze_outer_u, col_ys, eq_span=eq_span)

    return mb, wins


def build_and_export(spec: FactorySpec, out_root=None):
    if out_root is None:
        out_root = K.out_dir_from_argv("output")
    A = make_atlas(spec, size=4096)
    main_mb, wins = _build_stage(spec, A, stage=0)
    lod1_mb, _ = _build_stage(spec, A, stage=1)
    lod2_mb, _ = _build_stage(spec, A, stage=2)
    return K.export_asset(
        spec.name_base,
        spec.level,
        dict(main=main_mb, lod1=lod1_mb, lod2=lod2_mb, windows=wins),
        A,
        out_root,
        lod2_tex=1024,
        lot=spec.lot,
        front_yard=spec.front_yard,
        notes=f"Parametric Korean blue-roof industrial preset ({spec.name_base})",
    )
