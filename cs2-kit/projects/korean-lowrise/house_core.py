"""한국형 저층 주택 공통 코어. M1은 평지붕 A형만 구현한다."""
from dataclasses import dataclass
import json
from pathlib import Path
import sys

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

    def __post_init__(self):
        if not (1 <= self.floors <= 2 and self.width >= 7 and self.depth >= 8):
            raise ValueError("M1 A형 범위: 1~2층, 폭 7m 이상, 깊이 8m 이상")
        if self.width + 4.4 > self.lot[0] * K.CELL_M or self.depth + 6 > self.lot[1] * K.CELL_M:
            raise ValueError("담장·외부계단 포함 형상이 lot를 넘음")


PRESETS = {"a01": HouseSpec()}


def brick(ctx):
    x, z = ctx.meters()
    row = np.floor(z / 0.075)
    joint = ((z % 0.075) < 0.009) | (((x + (row % 2) * 0.12) % 0.24) < 0.009)
    ctx.rgb[joint] = (176, 158, 137)
    ctx.height[joint] -= 0.3
    ctx.grain(amp=4, scale_px=2, height=0.1, seed=71)


def waterproof(ctx):
    ctx.grain(amp=3, scale_px=8, height=0.06, seed=17)
    ctx.stains(amount=0.07, scale_px=40, streaks=0, seed=19)


def windows(ctx):
    # 창 발광은 0. 작은 현관 등기구만 발광한다.
    ctx.rgb[...] = (91, 120, 130)
    line = ((ctx.u * 5 % 1) < 0.07) | ((ctx.v * 5 % 1) < 0.07)
    ctx.rgb[line] = (48, 57, 60)
    curtain = (ctx.u * 75 % 1) < 0.28
    ctx.rgb[curtain & ~line] *= 0.86
    ctx.emis[...] = 0


def atlas(spec):
    a = K.Atlas(size=2048, pad=12)
    a.add("wall", color=spec.wall_color, ctrl=(0, 255, 0), px=768,
          tile=(2.4, 2.4), painter=brick)
    a.add("roof", color=spec.roof_color, ctrl=(255, 0, 0), px=384,
          tile=(3.2, 3.2), painter=waterproof)
    a.add("window", color=(91, 120, 130), px=512, gloss=0.65, painter=windows)
    for name, color, px in [("stone", (174, 167, 151), 128),
                            ("frame", (194, 195, 184), 64),
                            ("steel", (63, 72, 70), 64),
                            ("door", (89, 75, 60), 128),
                            ("roof_equipment", (175, 181, 167), 128),
                            ("tank", (182, 187, 180), 128),
                            ("paving", (133, 131, 124), 128)]:
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
            if axis == "x" and side == 1 and pos == (0.23 if f == 0 else 0.77):
                continue  # 외부계단 상부 출입문·계단 참 확보
            c = start + pos * length
            result.append((c - 0.85, c + 0.85, f * spec.floor_h + 1.0,
                           f * spec.floor_h + 2.35, "window", f))
    if axis == "y" and side == -1:
        result.append((-0.55, 0.55, 0.16, 2.35, "door", 0))
    if axis == "x" and side == 1 and spec.floors == 2:
        result.append((5.10, 6.05, spec.floor_h + 0.04, spec.floor_h + 2.22, "door", 1))
    return sorted(result)


def facade(mb, wins, spec, axis, c, side, stage):
    """외벽을 개구부 주위 조각으로 만들어 유리가 실제 0.20m 후퇴한다."""
    lo, hi = (-spec.width / 2, spec.width / 2) if axis == "y" else (0, spec.depth)
    if axis == "x" and stage < 2:
        lo, hi = lo + 0.24, hi - 0.24  # 앞·뒤 벽이 모서리 두께를 담당
    holes = openings(spec, axis, side)
    top = spec.floors * spec.floor_h - 0.1
    cuts = sorted({lo, hi, *(v for h in holes for v in h[:2])})
    for left, right in zip(cuts, cuts[1:]):
        covered = sorted((h[2], h[3]) for h in holes if h[0] <= left and h[1] >= right)
        z = 0.15
        for z0, z1 in covered + [(top, top)]:
            if z0 > z:
                if stage == 2:
                    mb.rect(K.face_pts(axis, c, side, left, right, z, z0), "wall")
                else:
                    K.axbox(mb, axis, c, side, left, right, -0.24, 0, z, z0, "wall")
            z = max(z, z1)
    for i, (a0, a1, z0, z1, kind, floor) in enumerate(holes):
        if kind == "window":
            mid = (a0 + a1) / 2
            for j, (b0, b1) in enumerate(((a0+0.065, mid-0.03), (mid+0.03, a1-0.065))):
                wins.add_face(axis, c - side * 0.22, side, b0, b1, z0+0.05, z1-0.05, floor, i*2+j)
        else:
            K.axbox(mb, axis, c, side, a0+0.065, a1-0.065, -0.219, -0.20, z0+0.05, z1-0.05, "door")
        if stage == 0:
            for b0, b1 in ((a0, a0 + 0.06), (a1 - 0.06, a1)):
                K.axbox(mb, axis, c, side, b0, b1, -0.21, -0.12, z0+0.04, z1-0.04, "frame")
            if kind == "window":
                mid = (a0 + a1) / 2
                K.axbox(mb, axis, c, side, mid - 0.025, mid + 0.025, -0.20, -0.12, z0+0.04, z1-0.04, "frame")
        if stage < 2:
            for b0, b1 in ((z0 - 0.07, z0 + 0.04), (z1 - 0.04, z1 + 0.09)):
                K.axbox(mb, axis, c, side, a0 - 0.08, a1 + 0.08, -0.23, 0.10, b0, b1, "stone")


def build_stage(spec, a, stage):
    mb = K.MeshBuilder(a, split_tiles=stage == 0)
    wins = K.WindowSet()
    w, d, h = spec.width, spec.depth, spec.floors * spec.floor_h
    # 매스 코어가 창 뒤에 있고 별도 외벽 셸에 실제 개구부가 있다.
    meta = K.volume_prism(a, [(-w/2+0.24, 0.24), (w/2-0.24, 0.24),
                             (w/2-0.24, d-0.24), (-w/2+0.24, d-0.24)],
                          h, volume_id="house", wall="wall", roof="roof", mb=mb)
    mb.box(-w/2, w/2, 0, d, 0.041, 0.15, "stone")
    mb.box(-w/2, w/2, 0, d, h-0.1, h+0.08, "roof")
    for axis, c, side in (("y", 0, -1), ("y", d, 1), ("x", -w/2, -1), ("x", w/2, 1)):
        facade(mb, wins, spec, axis, c, side, stage)
    for x0, x1, y0, y1 in ((-w/2, w/2, 0, 0.18), (-w/2, w/2, d-0.18, d),
                            (-w/2, -w/2+0.18, 0.18, d-0.18), (w/2-0.18, w/2, 0.18, d-0.18)):
        mb.box(x0, x1, y0, y1, h+0.08, h+0.62, "roof")
        if stage == 0:
            mb.box(x0, x1, y0, y1, h+0.62, h+0.69, "stone")
    mb.box(-2.7, -0.4, d-2.5, d-0.5, h+0.08, h+2.05, "wall")
    mb.box(-2.8, -0.3, d-2.6, d-0.4, h+2.05, h+2.18, "roof")
    if stage < 2:
        K.axbox(mb, "y", d-2.5, -1, -2.1, -1.2, 0, 0.03, h+0.08, h+1.85, "door")
        K.feature_roof_equipment(meta, "house", size=(0.9, 0.65), height=0.62,
                                 center=(2.5, d-2), quality_stage=stage)
    if spec.tank:
        n = 12 if stage == 0 else 8
        cx, cy, z = 1.7, d-3.0, h+0.22
        ring = [(cx+0.66*np.cos(t*2*np.pi/n), cy+0.66*np.sin(t*2*np.pi/n)) for t in range(n)]
        K.volume_prism(a, ring, 1.1, z0=z, wall="tank", roof="tank", mb=mb)
        if stage == 0:
            for zz in (z+0.12, z+0.94):
                collar = [(cx+0.69*np.cos(t*2*np.pi/n), cy+0.69*np.sin(t*2*np.pi/n)) for t in range(n)]
                K.volume_prism(a, collar, 0.04, z0=zz, wall="tank", roof="tank", mb=mb)
            mb.box(cx+0.52, cx+0.60, cy-0.05, cy+0.05, h+0.08, z+1.2, "steel")
    if spec.stairs and spec.floors == 2:
        x0, x1 = w/2+0.08, w/2+1.25
        count = 17 if stage == 0 else 6
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
            mb.box(x0, x1, y0, y1, 0, 1.15, "wall", skip=("bottom",))
        mb.box(-1.12, 1.12, -2.48, -2.40, 0.10, 1.45, "steel")
        if stage == 0:
            for i in range(13):
                x = -1.05 + i*2.1/12
                mb.box(x-0.02, x+0.02, -2.51, -2.47, 0.15, 1.40, "frame")
    mb.rect([(-w/2-2, -2.7, 0), (w/2+2, -2.7, 0), (w/2+2, d+1.6, 0), (-w/2-2, d+1.6, 0)], "paving")
    mb.box(-0.8, 0.8, -0.65, -0.001, 0, 0.16, "stone", skip=("bottom",))
    if stage < 2:
        mb.box(-0.9, 0.9, -0.9, 0.08, 2.45, 2.55, "awning")
    if stage == 0:
        mb.box(0.68, 0.84, -0.12, -0.04, 2.1, 2.23, "lamp")
    return mb, wins


def build_and_export(spec):
    a = atlas(spec)
    main, wins = build_stage(spec, a, 0)
    l1, _ = build_stage(spec, a, 1)
    l2, _ = build_stage(spec, a, 2)
    folder, result = K.export_asset(spec.name, 1, dict(main=main, lod1=l1, lod2=l2, windows=wins),
                                    a, K.out_dir_from_argv("output"), lod2_tex=512, lot=spec.lot,
                                    front_yard=2.7, notes="A형 시제품; lot·성장·야간은 사용자 인게임 확인 대기")
    sx, sy = result["pivot_shift"]
    items = [dict(kind="planter", suggest="작은 사각 화분 (에디터 내장 소품)",
                  x=-3.5+sx, y=-1.2+sy, z=0, rot_deg=0, scale=[0.55, 0.55, 0.5],
                  source="A형 대문 옆 제안; 실측 아님")]
    (HERE / "work").mkdir(exist_ok=True)
    (HERE / "work" / "subobjects.json").write_text(json.dumps(
        dict(asset=result["asset"], coord="CS2 asset local: x right, y back, z up; metres; pivot applied",
             items=items), ensure_ascii=False, indent=2), encoding="utf-8")
    return folder, result


def self_check():
    s = PRESETS["a01"]
    a = atlas(s)
    meshes = [build_stage(s, a, i) for i in range(3)]
    main, wins = meshes[0]
    assert 2000 <= main.tri_count <= 4000, main.tri_count
    assert meshes[1][0].tri_count < main.tri_count * 0.5
    assert meshes[2][0].tri_count <= 500, meshes[2][0].tri_count
    assert len(wins.items) == 28
    assert abs(wins.items[0]["pts"][0][1] - 0.20) < 1e-6
    assert not any("plant" in tag or "soil" in tag for tag in main.tags)
    print("A형 예산·개구부 후퇴·창수·조경 제외 검사 PASS", [m.tri_count for m, _ in meshes])


if __name__ == "__main__":
    self_check()
