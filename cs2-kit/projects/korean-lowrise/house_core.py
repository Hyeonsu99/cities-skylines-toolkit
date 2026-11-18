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


@dataclass(frozen=True)
class HouseSpec:
    name: str = "KoreanHouseA01"
    lot: tuple = (2, 2)
    width: float = 9.6
    depth: float = 9.2
    floors: int = 2
    floor_h: float = 3.05
    wall_color: tuple = (151, 79, 57)
    roof_color: tuple = (64, 111, 83)
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


def weather(ctx):
    ctx.grain(amp=3.5, scale_px=3, height=0.08, seed=71)
    ctx.stains(amount=0.085, scale_px=38, streaks=0.20, seed=73)


def mosaic(ctx):
    ctx.joints(cols=20, rows=20, width_m=0.006, depth=0.35, darken=0.24, tone=6, seed=3)
    weather(ctx)


def porcelain(ctx):
    ctx.joints(cols=4, rows=3, width_m=0.008, depth=0.38, darken=0.24, tone=5, seed=7)
    weather(ctx)


def stone(ctx):
    ctx.joints(cols=2, rows=3, width_m=0.012, depth=0.6, darken=0.28, tone=12, stagger=0.5, seed=9)
    ctx.grain(amp=10, scale_px=2, height=0.35, seed=17)


def plinth(ctx):
    ctx.joints(cols=4, rows=1, width_m=0.012, depth=0.4, darken=0.25, tone=5, seed=11)
    ctx.grain(amp=8, scale_px=2, height=0.3, seed=13)
    splash = np.clip(1-ctx.v/0.65, 0, 1) * (0.5+0.5*ctx.noise(scale_px=12, seed=15))
    ctx.rgb *= (1-0.24*splash)[..., None]


def pattern(ctx):
    x, z = ctx.meters()
    diamond = np.abs(x % 0.3 - 0.15) + np.abs(z-0.15) < 0.11
    ctx.rgb[diamond] = (78, 99, 111)
    ctx.joints(cols=8, rows=2, width_m=0.005, depth=0.2, tone=1, seed=21)


def corrugated(ctx):
    x, _ = ctx.meters()
    rib = np.cos(x * np.pi * 2 / 0.12)
    ctx.rgb += rib[..., None]*9
    ctx.height += rib*0.35
    weather(ctx)


def clay(ctx):
    x, z = ctx.meters()
    ctx.height += 0.5*np.cos(x*np.pi*2/0.18)
    ctx.rgb *= (0.82+0.18*np.cos(x*np.pi*2/0.18))[..., None]
    ctx.joints(cols=12, rows=4, width_m=0.015, depth=0.4, tone=7, seed=22)


def louver(ctx):
    rib = np.cos(ctx.v*42*np.pi) > 0.25
    ctx.rgb[rib] *= 0.43
    ctx.height[rib] -= 0.35
    ctx.grain(amp=2, scale_px=2, height=0.03, seed=24)


def streak(ctx):
    # 투명 컷아웃 얼룩. 창 아래·실외기 아래에만 작은 면으로 배치한다.
    n = ctx.noise(scale_px=7, amp=1, octaves=2, seed=35)
    stripes = (np.sin(ctx.u*73)+np.sin(ctx.u*117+2))*0.25+0.5
    mask = stripes * (0.25+0.75*ctx.v) + n*0.15 > 0.58
    ctx.alpha[...] = np.where(mask, 255, 0)


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


def address(ctx):
    text_label(ctx, "17-8", "address")


def sign(ctx):
    text_label(ctx, "DAON SHOP", "sign")


def brick(ctx):
    x, z = ctx.meters()
    row = np.floor(z / 0.075)
    joint = ((z % 0.075) < 0.009) | (((x + (row % 2) * 0.12) % 0.24) < 0.009)
    ctx.rgb[joint] = (176, 158, 137)
    ctx.height[joint] -= 0.3
    ctx.grain(amp=4, scale_px=2, height=0.1, seed=71)
    ctx.stains(amount=0.08, scale_px=36, streaks=0.16, seed=75)


def waterproof(ctx):
    ctx.grain(amp=3, scale_px=8, height=0.06, seed=17)
    ctx.stains(amount=0.07, scale_px=40, streaks=0, seed=19)


def windows(ctx):
    # 창 발광은 0. 작은 현관 등기구만 발광한다.
    line = ((ctx.u * 5 % 1) < 0.07) | ((ctx.v * 5 % 1) < 0.07)
    ctx.rgb[line] = (48, 57, 60)
    curtain = (ctx.u * 75 % 1) < 0.28
    ctx.rgb[curtain & ~line] *= 0.86
    ctx.emis[...] = 0


def atlas(spec):
    a = K.Atlas(size=2048, pad=12)
    a.add("brick", color=spec.wall_color, ctrl=(0, 255, 0), px=512,
          tile=(2.4, 2.4), painter=brick)
    a.add("mosaic", color=(210, 210, 197), ctrl=(0, 255, 0), px=512, tile=(1.6, 1.6), painter=mosaic)
    a.add("plaster", color=(214, 209, 192), ctrl=(0, 255, 0), px=384, tile=(2.4, 2.4), painter=weather)
    a.add("plaster_gray", color=(191, 195, 192), ctrl=(0, 255, 0), px=256, tile=(2.4, 2.4), painter=weather)
    a.add("fence_white", color=(227, 226, 215), ctrl=(0, 255, 0), px=256, tile=(2.4, 2.4), painter=weather)
    a.add("porcelain", color=(164, 158, 146), ctrl=(0, 255, 0), px=512, tile=(2.4, 2.4), painter=porcelain)
    a.add("pattern", color=(212, 209, 190), ctrl=(0, 255, 0), px=256, tile=(1.2, 0.3), painter=pattern)
    a.add("plinth", color=(77, 79, 74), px=256, tile=(2.4, 0.6), painter=plinth)
    a.add("roof", color=spec.roof_color, ctrl=(255, 0, 0), px=256,
          tile=(3.2, 3.2), painter=waterproof)
    window_color = {"70s": (85, 107, 110), "80s": (91, 120, 130), "90s": (123, 146, 150)}[spec.era]
    a.add("window", color=window_color, px=384, gloss=0.65, painter=windows)
    a.add("stone", color=(164, 161, 147), px=256, tile=(1.0, 1.2), painter=stone)
    a.add("clay", color=(163, 73, 48), px=256, tile=(2.16, 0.8), painter=clay)
    a.add("blue", color=(53, 100, 129), px=128, tile=(2, 2), painter=corrugated)
    a.add("orange", color=(183, 99, 48), px=128, tile=(2, 2), painter=corrugated)
    a.add("shutter", color=(134, 139, 132), ctrl=(0, 0, 255), px=256, painter=louver)
    a.add("equipment_face", color=(169, 177, 168), px=128, painter=louver)
    a.add("drip", color=(95, 89, 68), px=128, painter=streak)
    a.add("rust", color=(132, 74, 40), px=128, painter=streak)
    a.add("address", px=128, painter=address)
    a.add("sign", px=256, painter=sign)
    for name, color, px in [("cement", (163, 166, 158), 64),
                            ("frame", {"70s": (157, 145, 118), "80s": (180, 184, 179), "90s": (215, 217, 207)}[spec.era], 64),
                            ("steel", (31, 39, 38), 64),
                            ("door", (89, 75, 60), 128),
                            ("roof_equipment", (175, 181, 167), 128),
                            ("tank", (182, 187, 180), 128),
                            ("paving", (133, 131, 124), 64), ("gas", (206, 177, 69), 64),
                            ("wood", (133, 99, 64), 64), ("jar", (87, 56, 39), 64),
                            ("solar", (43, 71, 91), 64)]:
        a.add(name, color=color, px=px, metal=0.4 if name in ("steel", "tank") else 0)
    a.add("awning", color=(97, 112, 100), ctrl=(0, 0, 255), px=64)
    a.add("lamp", color=(255, 229, 175), emissive=(255, 214, 145), px=32)
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
            for j, (b0, b1) in enumerate(((a0+0.065, mid-0.03), (mid+0.03, a1-0.065))):
                wins.add_face(axis, c - side * 0.22, side, b0, b1, z0+0.05, z1-0.05, floor, i*2+j)
                wins.items[-1]["pts2"] = K.face_pts(axis, c+side*0.02, side, b0, b1, z0+0.05, z1-0.05)
            if stage == 2:
                mb.rect(K.face_pts(axis, c+side*0.001, side, a0, a1, z0, z1), "window")
        else:
            reg = "shutter" if kind == "shutter" else "door"
            if stage == 2:
                mb.rect(K.face_pts(axis, c+side*0.001, side, a0, a1, z0, z1), reg)
            else:
                K.axbox(mb, axis, c, side, a0+0.065, a1-0.065, -0.219, -0.20,
                        z0+0.05, z1-0.05, reg)
        if stage == 0:
            for b0, b1 in ((a0, a0 + 0.06), (a1 - 0.06, a1)):
                K.axbox(mb, axis, c, side, b0, b1, -0.21, -0.12, z0+0.04, z1-0.04, "frame")
            if kind == "window":
                mid = (a0 + a1) / 2
                K.axbox(mb, axis, c, side, mid - 0.025, mid + 0.025, -0.20, -0.12, z0+0.04, z1-0.04, "frame")
                if floor == 0 or spec.grille_up:
                    for u in (0.06, 0.30, 0.5, 0.70, 0.94):
                        x = a0+(a1-a0)*u
                        K.axbox(mb, axis, c, side, x-0.012, x+0.012, 0.10, 0.13, z0+0.10, z1-0.10, "steel")
                    for z in (z0+0.07, z0+(z1-z0)*0.44, z1-0.07):
                        K.axbox(mb, axis, c, side, a0+0.05, a1-0.05, 0.13, 0.15, z-0.012, z+0.012, "steel")
                K.paint(mb, axis, c, side, a0+0.08, a1-0.08, max(0.65, z0-0.50), z0-0.08, "drip")
        if stage < 2:
            for b0, b1 in ((z0 - 0.07, z0 + 0.04), (z1 - 0.04, z1 + 0.09)):
                K.axbox(mb, axis, c, side, a0 - 0.08, a1 + 0.08, -0.23, 0.10, b0, b1, "stone")
    K.paint(mb, axis, c, side, lo, hi, 0.16, 0.62, "plinth")
    if spec.finish == "mosaic":
        K.paint(mb, axis, c, side, lo, hi, spec.floor_h-0.42, spec.floor_h-0.12, "pattern")


def slope_box(mb, bounds, region, axis, rise):
    part = K.MeshBuilder(mb.atlas, split_tiles=mb.split_tiles)
    part.box(*bounds, region)
    origin = bounds[axis*2]
    span = bounds[axis*2+1]-origin
    part.verts = [(x, y, z+((x, y)[axis]-origin)*rise/span) for x, y, z in part.verts]
    mb.merge(part)


def roof_objects(mb, spec, h, stage):
    if stage == 2:
        return
    x, y = 1.2 + (spec.seed % 3)*0.45, 2.0 + (spec.seed % 2)*0.8
    z = h+0.12
    kind = spec.roof_prop
    if kind == "rack":
        for xx in (x-0.7, x+0.7):
            mb.box(xx-0.025, xx+0.025, y-0.4, y+0.4, z, z+0.04, "steel")
            mb.box(xx-0.02, xx+0.02, y-0.02, y+0.02, z+0.04, z+1.0, "steel")
        for yy in (y-0.35, y, y+0.35):
            mb.box(x-0.75, x+0.75, yy-0.015, yy+0.015, z+1.02, z+1.05, "steel")
    elif kind == "platform":
        for xx in (x-0.6, x+0.6):
            for yy in (y-0.5, y+0.5):
                mb.box(xx-0.04, xx+0.04, yy-0.04, yy+0.04, z, z+0.3, "wood")
        for i in range(6):
            mb.box(x-0.75+i*0.25, x-0.52+i*0.25, y-0.65, y+0.65, z+0.3, z+0.38, "wood")
    elif kind == "jars":
        for i, radius in enumerate((0.25, 0.19, 0.29)):
            cx = x+(i-1)*0.60
            n = 10 if stage == 0 else 6
            ring = [(cx+radius*np.cos(t*2*np.pi/n), y+radius*np.sin(t*2*np.pi/n)) for t in range(n)]
            K.volume_prism(mb.atlas, ring, radius*1.8, z0=z, wall="jar", roof="jar", mb=mb)
            if stage == 0:
                mb.box(cx-radius*0.9, cx+radius*0.9, y-radius*0.9, y+radius*0.9,
                       z+radius*1.8+0.015, z+radius*1.8+0.06, "jar")
    elif kind == "dish":
        mb.box(x-0.45, x+0.45, y-0.35, y+0.35, z, z+0.08, "cement")
        mb.box(x-0.035, x+0.035, y-0.035, y+0.035, z+0.08, z+0.9, "steel")
        ring = [(x+0.50*np.cos(t*np.pi/6), y+0.50*np.sin(t*np.pi/6)) for t in range(12)]
        part = K.MeshBuilder(mb.atlas)
        K.volume_prism(mb.atlas, ring, 0.05, wall="tank", roof="tank", mb=part)
        part.verts = [(vx, y+(vy-y)*0.5-vz*0.866, z+0.95+(vy-y)*0.866+vz*0.5) for vx, vy, vz in part.verts]
        mb.merge(part)
    else:
        for xx in (x-0.7, x+0.7):
            mb.box(xx-0.04, xx+0.04, y-0.6, y+0.6, z, z+0.15, "steel")
        slope_box(mb, (x-0.8, x+0.8, y-0.65, y+0.65, z+0.16, z+0.23), "solar", 1, 0.65)
        # 온수기 저장 탱크: 원통을 가로로 돌린다.
        part = K.MeshBuilder(mb.atlas)
        ring = [(0.22*np.cos(t*np.pi/5), 0.22*np.sin(t*np.pi/5)) for t in range(10)]
        K.volume_prism(mb.atlas, ring, 1.7, wall="tank", roof="tank", mb=part)
        part.verts = [(x-0.85+vz, y+0.65+vy, z+1+vx) for vx, vy, vz in part.verts]
        mb.merge(part)


def living_details(mb, spec, stage):
    if stage == 2:
        return
    w, d = spec.width, spec.depth
    # 뒷벽 중앙은 창 사이. 앵글 받침과 실외기 몸통·전면 그릴.
    y = d if not spec.notch else d-2.6
    cx = 0.2 if not spec.notch else -w/2+1.3
    K.axbox(mb, "y", y, 1, cx-0.48, cx+0.48, 0.12, 0.48, 1.85, 2.48, "roof_equipment")
    K.paint(mb, "y", y+0.48, 1, cx-0.43, cx+0.43, 1.90, 2.43, "equipment_face")
    if stage == 0:
        for xx in (cx-0.35, cx+0.35):
            K.axbox(mb, "y", y, 1, xx-0.025, xx+0.025, 0.03, 0.50, 1.78, 1.82, "steel")
            K.axbox(mb, "y", y, 1, xx-0.025, xx+0.025, 0.02, 0.07, 1.52, 1.78, "steel")
        K.paint(mb, "y", y, 1, cx-0.4, cx+0.4, 1.10, 1.74, "rust")
        # 정면 빈 벽띠의 노란 가스관·계량기, 창과 간섭하지 않는다.
        gx = -0.82
        mb.box(gx-0.023, gx+0.023, -0.105, -0.055, 0.18, spec.floor_h+0.35, "gas")
        mb.box(gx-0.08, gx+0.08, -0.13, -0.04, 1.05, 1.36, "cement")
        mb.box(gx-0.35, gx+0.18, -0.14, -0.09, 0.28, 0.32, "gas")
    # 썬라이트 차양은 불투명 청록 면과 외곽 프레임.
    if not spec.shop:
        slope_box(mb, (-1.1, 1.1, -1.00, -0.02, 2.42, 2.48), "awning", 1, 0.22)
        if stage == 0:
            for xx in (-1.08, 0, 1.08):
                slope_box(mb, (xx-0.02, xx+0.02, -1.00, -0.02, 2.485, 2.515), "frame", 1, 0.22)
    else:
        slope_box(mb, (-w*0.44, w*0.44, -1.15, -0.02, 2.51, 2.57), "awning", 1, 0.36)
        mb.box(-w*0.44, w*0.44, -1.18, -1.15, 2.32, 2.57, "awning")
        mb.box(-w*0.35, w*0.35, -0.08, -0.015, 2.93, 3.20, {"front": "sign", "default": "steel"})


def build_stage(spec, a, stage):
    mb = K.MeshBuilder(a, split_tiles=stage == 0)
    wins = K.WindowSet()
    w, d, h = spec.width, spec.depth, spec.floors * spec.floor_h
    x0, x1 = -w/2, w/2
    if spec.notch:
        ring = [(x0, 0), (x1, 0), (x1, d), (x0+2.6, d), (x0+2.6, d-2.6), (x0, d-2.6)]
        inner = [(x0+0.24, 0.24), (x1-0.24, 0.24), (x1-0.24, d-0.24),
                 (x0+2.84, d-0.24), (x0+2.84, d-2.84), (x0+0.24, d-2.84)]
        walls = [("y", 0, -1, x0, x1), ("x", x1, 1, 0, d),
                 ("y", d, 1, x0+2.6, x1), ("x", x0+2.6, -1, d-2.6, d),
                 ("y", d-2.6, 1, x0, x0+2.6), ("x", x0, -1, 0, d-2.6)]
    else:
        ring = [(x0, 0), (x1, 0), (x1, d), (x0, d)]
        inner = [(x0+0.24, 0.24), (x1-0.24, 0.24), (x1-0.24, d-0.24), (x0+0.24, d-0.24)]
        walls = [("y", 0, -1, x0, x1), ("y", d, 1, x0, x1),
                 ("x", x0, -1, 0, d), ("x", x1, 1, 0, d)]
    # 매스 코어가 창 뒤에 있고 별도 외벽 셸에 실제 개구부가 있다.
    meta = K.volume_prism(a, inner, h, volume_id="house", wall=spec.finish, roof="roof", mb=mb)
    if stage < 2:
        K.volume_prism(a, ring, 0.109, z0=0.041, wall="plinth", roof="cement", mb=mb)
    K.volume_prism(a, ring, 0.18, z0=h-0.1, wall=spec.finish, roof="roof", mb=mb)
    for axis, c, side, lo, hi in walls:
        facade(mb, wins, spec, axis, c, side, stage, lo, hi)
        pa, pb = (lo+0.18, hi-0.18) if axis == "x" else (lo, hi)
        if stage == 2:
            K.axbox(mb, axis, c, side, pa, pb, -0.18, 0, h+0.08, h+0.62,
                    {"default": spec.finish, "top": "cement"}, skip=("bottom",))
        else:
            K.axbox(mb, axis, c, side, pa, pb, -0.18, 0, h+0.08, h+0.55, spec.finish)
            K.axbox(mb, axis, c, side, pa, pb, -0.18, 0, h+0.55, h+0.62, "cement")
        if spec.eaves:
            part = K.MeshBuilder(a, split_tiles=stage == 0)
            ea, eb = (lo+0.48, hi-0.48) if axis == "x" else (lo-0.48, hi+0.48)
            K.axbox(part, axis, c, side, ea, eb, 0.01, 0.48, h-0.08, h+0.03, "clay")
            part.verts = [(vx, vy, vz-side*((vx, vy)[0 if axis == "x" else 1]-c)*0.65)
                          for vx, vy, vz in part.verts]
            mb.merge(part)
        if stage == 0:
            K.axbox(mb, axis, c, side, pa, pb, -0.18, 0, h+0.62, h+0.65, "cement")
    hx = 0.3 if spec.notch else -2.7
    if stage == 2:
        mb.box(hx, hx+2.3, d-2.5, d-0.5, h+0.08, h+1.98, {"default": spec.addon, "top": "cement"})
    else:
        mb.box(hx, hx+2.3, d-2.5, d-0.5, h+0.08, h+1.85, spec.addon)
        mb.box(hx-0.08, hx+2.38, d-2.58, d-0.42, h+1.85, h+1.98, "cement")
    if stage < 2:
        K.axbox(mb, "y", d-2.5, -1, hx+0.6, hx+1.5, 0, 0.03, h+0.08, h+1.75, "door")
        K.feature_roof_equipment(meta, "house", size=(0.9, 0.65), height=0.62,
                                 center=(-0.1, d-3.1) if spec.notch else (2.5, d-2), quality_stage=stage)
    if spec.tank:
        n = 12 if stage == 0 else 6
        cx, cy, z = 1.7, d-3.45, h+0.22
        ring = [(cx+0.66*np.cos(t*2*np.pi/n), cy+0.66*np.sin(t*2*np.pi/n)) for t in range(n)]
        K.volume_prism(a, ring, 1.1, z0=z, wall="tank", roof="tank", mb=mb)
        if stage == 0:
            for zz in (z+0.12, z+0.94):
                collar = [(cx+0.69*np.cos(t*2*np.pi/n), cy+0.69*np.sin(t*2*np.pi/n)) for t in range(n)]
                K.volume_prism(a, collar, 0.04, z0=zz, wall="tank", roof="tank", mb=mb)
            mb.box(cx+0.52, cx+0.60, cy-0.05, cy+0.05, h+0.08, z+1.2, "steel")
    if spec.stairs and spec.floors == 2:
        x0, x1 = w/2+0.08, w/2+1.25
        count = 17 if stage == 0 else (6 if stage == 1 else 1)
        if stage == 2:
            slope_box(mb, (x0, x1, 0.25, 5.10, 0.02, 0.10), "steel", 1, spec.floor_h-0.10)
        else:
            for i in range(count):
                y0, y1 = 0.25 + i*4.85/count, 0.25+(i+1)*4.85/count
                z = (i+1)*spec.floor_h/count
                mb.box(x0, x1, y0, y1, max(0, z-0.10), z, "steel")
        mb.box(w/2, x1, 5.10, 6.2, spec.floor_h-0.12, spec.floor_h, "steel")
        for xx in (x0+0.04, x1-0.04):
            if stage < 2:
                for dz in (0.02, 0.95):
                    beam = K.MeshBuilder(a)
                    beam.box(xx-0.02, xx+0.02, 0.25, 5.1, dz, dz+0.05, "steel")
                    beam.verts = [(x, y, z+(y-0.25)*spec.floor_h/4.85) for x, y, z in beam.verts]
                    mb.merge(beam)
            if stage == 0:
                for i in range(9):
                    y = 0.25 + i*4.85/8
                    z = i*spec.floor_h/8
                    mb.box(xx-0.025, xx+0.025, y-0.025, y+0.025, z+0.04, z+1, "steel")
        if stage < 2:
            mb.box(x1-0.05, x1, 5.1, 6.2, spec.floor_h+0.92, spec.floor_h+1, "steel")
            for yy in (5.2, 6.1):
                mb.box(x1-0.18, x1-0.06, yy-0.06, yy+0.06, 0.0, spec.floor_h-0.12, "steel", skip=("bottom",))
    # 담장·대문은 구조물. 조경·화분·화단 틀·흙면은 메시 금지.
    if spec.fence:
        half = w/2+2
        for x0, x1, y0, y1 in ((-half, -half+0.18, -2.32, d+1.42),
                                (half-0.18, half, -2.32, d+1.42),
                                (-half, half, d+1.42, d+1.6),
                                (-half, -1.15, -2.5, -2.32), (1.15, half, -2.5, -2.32)):
            mb.box(x0, x1, y0, y1, 0, 1.15, spec.fence_finish, skip=("bottom",))
        mb.box(-1.12, 1.12, -2.48, -2.40, 0.10, 1.45, "steel")
        if stage == 0:
            for i in range(13):
                x = -1.05 + i*2.1/12
                mb.box(x-0.02, x+0.02, -2.51, -2.47, 0.15, 1.40, "steel")
        for px in (-1.13, 1.13):
            if stage == 2:
                mb.box(px-0.18, px+0.18, -2.60, -2.24, 0, 1.73, {"default": "stone", "top": "cement"}, skip=("bottom",))
            else:
                mb.box(px-0.18, px+0.18, -2.60, -2.24, 0, 1.65, "stone", skip=("bottom",))
                mb.box(px-0.20, px+0.20, -2.62, -2.22, 1.65, 1.73, "cement")
            if stage < 2:
                mb.box(px-0.09, px+0.09, -2.50, -2.32, 1.73, 1.88, "lamp")
        if stage < 2:
            K.paint(mb, "y", -2.61, -1, -1.29, -0.98, 1.22, 1.45, "address")
            mb.box(1.40, 1.75, -2.65, -2.51, 0.85, 1.12, "steel")
    mb.rect([(-w/2-2, -2.7, 0), (w/2+2, -2.7, 0), (w/2+2, d+1.6, 0), (-w/2-2, d+1.6, 0)], "paving")
    mb.box(-0.8, 0.8, -0.65, -0.001, 0, 0.16, "stone", skip=("bottom",))
    living_details(mb, spec, stage)
    roof_objects(mb, spec, h, stage)
    if spec.balcony != "none":
        bw = w*0.34
        fh = spec.floor_h
        if spec.balcony != "enclosed" or stage < 2:
            mb.box(-bw, bw, -0.95, -0.001, fh-0.14, fh, "cement")
        if spec.balcony == "rail":
            mb.box(-bw, bw, -0.95, -0.90, fh+0.86, fh+0.92, "steel")
            if stage < 2:
                for bx in np.linspace(-bw+0.03, bw-0.03, 13 if stage == 0 else 5):
                    mb.box(bx-0.014, bx+0.014, -0.94, -0.91, fh+0.02, fh+0.86, "steel")
        else:
            if stage == 2:
                mb.box(-bw, bw, -0.95, -0.001, fh-0.14, fh+0.76, spec.finish)
            else:
                mb.box(-bw, bw, -0.95, -0.80, fh, fh+0.76, spec.finish)
            for sx in (-bw, bw-0.08):
                if stage == 2:
                    side = -1 if sx < 0 else 1
                    mb.rect(K.face_pts("x", -bw if side < 0 else bw, side, -0.95, -0.001, fh+0.76, fh+2.42), "frame")
                else:
                    mb.box(sx, sx+0.08, -0.95, -0.001, fh+0.76, fh+2.42, "frame")
            mb.box(-bw, bw, -0.95, -0.001, fh+2.42, fh+2.50, "cement")
            if stage == 2:
                mb.rect(K.face_pts("y", -0.951, -1, -bw, bw, fh+0.76, fh+2.42), "window")
            for i in range(6):
                ba = -bw+0.10+i*(2*bw-0.20)/6
                bb = -bw+0.10+(i+1)*(2*bw-0.20)/6
                wins.add_face("y", -0.95, -1, ba+0.025, bb-0.025, fh+0.80, fh+2.38, 1, 50+i)
                if stage < 2:
                    mb.box(ba-0.012, ba+0.012, -0.98, -0.93, fh+0.77, fh+2.41, "frame")
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
    items = [dict(kind="planter", suggest="작은 사각 화분 (에디터 내장 소품)",
                  x=-3.5+sx, y=-1.2+sy, z=0, rot_deg=0, scale=[0.55, 0.55, 0.5],
                  source="A형 대문 옆 제안; 실측 아님")]
    (HERE / "work").mkdir(exist_ok=True)
    content = json.dumps(
        dict(asset=result["asset"], coord="CS2 asset local: x right, y back, z up; metres; pivot applied",
             items=items), ensure_ascii=False, indent=2)
    if subobjects:
        for filename in ("subobjects.json", f"subobjects_{result['asset']}.json"):
            (HERE / "work" / filename).write_text(content, encoding="utf-8")
    return folder, result


def self_check():
    finishes, props = set(), set()
    for era in ("70s", "80s", "90s"):
        signatures = set()
        for seed in range(12):
            s = seeded(era, seed)
            assert s == seeded(era, seed)
            a = atlas(s)
            meshes = [build_stage(s, a, i) for i in range(3)]
            main, wins = meshes[0]
            counts = [m.tri_count for m, _ in meshes]
            assert counts[0] <= 8000, (era, seed, counts)
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
    print("3시대×12시드 재현성·예산·조합·조경 제외 검사 PASS")


if __name__ == "__main__":
    self_check()
