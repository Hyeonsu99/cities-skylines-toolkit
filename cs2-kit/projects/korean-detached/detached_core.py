# -*- coding: utf-8 -*-
"""신탄진형 단독주택(2000~2010년대) 공용 생성기 코어.

기준 문서:
- cs2-kit/projects/korean-detached/STYLE_BRIEF.md
- reports/korean_housing_lessons.md (재발 방지 규칙 25항 전부 준수)
"""
from dataclasses import dataclass
import json
import math
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import cs2kit as K
from local import kitext as KX


# ---------------------------------------------------------------------------
# 스펙 정의 (4대 유형 + 시드 가변 변수)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class DetachedSpec:
    name: str = "SintanjinHouse01"
    archetype: str = "front_terrace"     # front_terrace | standard_2f | ext_stairs | shop_1f
    lot: tuple = (2, 3)                  # (width_cells, depth_cells), 1 cell = 8 m
    front_yard: float = 2.2
    width: float = 13.0                  # 전체 1층 폭 (m)
    depth: float = 9.2                   # 전체 1층 깊이 (m)
    plinth_h: float = 0.62               # 기단 높이 (m)
    h1: float = 2.94                     # 1층 순층고 (기단 위 ~ 2층 바닥, 슬래브 포함)
    h2: float = 2.70                     # 2층 벽체 높이 (m)
    slab_h: float = 0.34                 # 흰 슬래브 띠 두께 (m)
    roof_type: str = "hip_tile_red"      # hip_tile_red | hip_tile_dark | flat_parapet
    roof_rise: float = 1.32              # 모임지붕 처마 위 용마루 높이 (m)
    eave_out: float = 0.46               # 처마 돌출 깊이 (m)
    wall_palette: str = "dark_brown_brick"  # dark_brown_brick | red_brown_brick | charcoal_brick | offwhite_plaster
    upper_plaster: bool = False          # 2층 회백 미장 혼합 여부
    sash_style: str = "pvc_white"        # pvc_white | sash_dark
    poly_tint: str = "poly_smoke"        # poly_smoke | poly_green
    fence_style: str = "rear_brick"      # rear_brick | brick_tiled_gate | concrete_wall | none
    stairs_side: str = "none"            # none | front_right | side_right | side_left
    shop_name: str = "대청철물·건재"     # 가상 상호 1 (실제 브랜드 금지, 규칙 19)
    shop_sub: str = "전기 · 수도 · 공구"
    shop_tel: str = "☎ 932-4108"
    shop_name2: str = "한밭분식"          # 가상 상호 2 (실제 브랜드 금지, 규칙 19)
    shop_sub2: str = "김밥 · 국수 · 만두"
    shop_tel2: str = "☎ 931-2850"
    vert_sign: str = "대청철물"           # 세로 돌출 간판 텍스트
    roof_addon: str = "none"              # none | solar | tank_box | both
    road_name: str = "한밭길"             # 가상 도로명 (규칙 20)
    road_no: str = "14"
    seed: int = 1
    rear_yard_d: float = 4.4             # 2x3 뒷마당 담장 깊이 (0 이면 생략)

    def __post_init__(self):
        lot_w = self.lot[0] * K.CELL_M
        lot_d = self.lot[1] * K.CELL_M
        if self.width > lot_w - 0.6:
            raise ValueError(f"{self.name}: width {self.width}m exceeds lot {lot_w}m")
        if self.depth + self.rear_yard_d > lot_d - 1.0:
            raise ValueError(f"{self.name}: depth+yard exceeds lot {lot_d}m")


PRESETS = {
    "01": DetachedSpec(
        name="SintanjinHouse01",
        archetype="front_terrace",
        lot=(2, 3),
        front_yard=2.2,
        width=13.0,
        depth=9.2,
        plinth_h=0.62,
        h1=2.94,
        h2=2.70,
        slab_h=0.34,
        roof_type="hip_tile_red",
        roof_rise=1.12,
        eave_out=0.46,
        wall_palette="dark_brown_brick",
        upper_plaster=False,
        sash_style="pvc_white",
        poly_tint="poly_smoke",
        fence_style="rear_brick",
        stairs_side="none",
        road_name="한밭길",
        road_no="14",
        seed=1,
        rear_yard_d=4.4,
    ),
    "02": DetachedSpec(
        name="SintanjinHouse02",
        archetype="standard_2f",
        lot=(2, 2),
        front_yard=1.0,
        width=10.2,
        depth=9.0,
        plinth_h=0.40,
        h1=2.90,
        h2=2.70,
        slab_h=0.32,
        roof_type="hip_tile_red",
        roof_rise=1.24,
        eave_out=0.50,
        wall_palette="dark_red_brown_brick",
        upper_plaster=False,
        sash_style="pvc_white",
        poly_tint="poly_green",
        fence_style="brick_gate",          # d02_gate_balcony_up: 기와 대문 대신 평 콘크리트 대문 지붕
        stairs_side="none",
        roof_addon="none",
        road_name="덕암길",
        road_no="27",
        seed=2,
        rear_yard_d=0.0,
    ),
    "03": DetachedSpec(
        name="SintanjinHouse03",
        archetype="ext_stairs",
        lot=(2, 2),
        front_yard=1.4,
        width=9.8,
        depth=9.0,
        plinth_h=0.40,
        h1=2.90,
        h2=2.72,
        slab_h=0.32,
        roof_type="hip_tile_dark",
        roof_rise=1.18,
        eave_out=0.46,
        wall_palette="charcoal_brick",
        upper_plaster=False,
        sash_style="pvc_white",
        poly_tint="poly_smoke",
        fence_style="concrete_wall",
        stairs_side="front_right",
        roof_addon="none",                 # 태양광 대신 외부계단 매스에 집중 (지붕 단순)
        road_name="석봉길",
        road_no="32",
        seed=3,
        rear_yard_d=0.0,
    ),
    "04": DetachedSpec(
        name="SintanjinHouse04",
        archetype="shop_1f",
        lot=(2, 2),
        front_yard=1.2,
        width=11.4,
        depth=10.0,
        plinth_h=0.0,
        h1=3.35,
        h2=2.85,
        slab_h=0.30,
        roof_type="flat_parapet",
        roof_rise=0.0,
        eave_out=0.0,
        wall_palette="red_brown_brick",
        upper_plaster=False,
        sash_style="pvc_white",
        poly_tint="poly_smoke",
        fence_style="none",
        stairs_side="none",
        shop_name="대청철물·건재",
        shop_sub="전기 · 수도 · 공구",
        shop_tel="☎ 932-4108",
        shop_name2="한밭분식",
        shop_sub2="김밥 · 국수 · 만두",
        shop_tel2="☎ 931-2850",
        vert_sign="대청철물",
        roof_addon="tank_box",             # 옥상 보온 물탱크 함체
        road_name="신탄길",
        road_no="8",
        seed=4,
        rear_yard_d=0.0,
    ),
}


# ---------------------------------------------------------------------------
# 텍스처 페인터 (STYLE_BRIEF 4장 픽셀 실측 sRGB 준수, 오염 띠 금지)
# ---------------------------------------------------------------------------
def _var(ctx, scale_px=6, seed=1):
    return np.tanh(ctx.noise(scale_px=scale_px, amp=1.0, octaves=2, seed=seed) * 0.65)


def _make_brick_painter(seed, mortar_rgb, course_h=0.075, brick_w=0.23):
    """한국 표준 점토벽돌(1줄 75 mm, 길이 ~230 mm, 엇갈림 쌓기) + 무채 회색 시멘트 줄눈."""
    def painter(ctx):
        x, z = ctx.meters()
        row = np.floor(z / course_h)
        shift = (row % 2) * (brick_w * 0.5)
        col = np.floor((x + shift) / brick_w)
        # 수평 줄눈 11 mm, 수직 줄눈 9 mm (멀리서도 벽돌 결이 선명하되 과하지 않게)
        h_joint = (z % course_h) < 0.011
        v_joint = ((x + shift) % brick_w) < 0.009
        joint = h_joint | v_joint

        # 벽돌별 자연스러운 명도·미세 색조 변화 (고동·적갈 벽돌의 소성 편차)
        # 변형 칸(ctx.vi)마다 다른 벽돌 배열 -> 월드 타일 반복 무늬 깨기
        vseed = seed * 37.0 + ctx.vi * 101.0
        h1 = np.sin(row * 12.9898 + col * 78.233 + vseed) * 43758.5453
        r_val = (h1 - np.floor(h1)) - 0.5                     # -0.5 ~ +0.5
        h2 = np.sin(row * 39.346 + col * 11.135 + vseed * 0.7) * 24634.6345
        r_warm = (h2 - np.floor(h2)) - 0.5
        h3 = np.sin(row * 71.13 + col * 5.731 + vseed * 1.3) * 17371.913
        r_odd = h3 - np.floor(h3)                              # 0 ~ 1 (소성 편차 큰 벽돌 선택)

        # 벽돌 안 위치 (0~1) -> 모서리 둥근 면(노멀), 아래쪽 미세 그늘
        fx_b = ((x + shift) % brick_w) / brick_w
        fz_b = (z % course_h) / course_h
        edge_d = np.minimum(np.minimum(fx_b, 1.0 - fx_b) * brick_w, np.minimum(fz_b, 1.0 - fz_b) * course_h)
        bevel = np.clip(edge_d / 0.012, 0.0, 1.0)              # 줄눈 쪽 12 mm 둥글게

        base = ctx.rgb.copy()
        tone = 1.0 + r_val * 0.24
        tone = np.where(r_odd > 0.93, tone * 0.72, tone)       # 과소성 짙은 벽돌 ~7%
        tone = np.where(r_odd < 0.05, tone * 1.14, tone)       # 덜 구운 밝은 벽돌 ~5%
        base[..., 0] *= tone + r_warm * 0.06
        base[..., 1] *= tone
        base[..., 2] *= tone - r_warm * 0.05
        # 벽돌 면 안 얼룩·철분 반점 + 위아래 미세 명암(쌓기 면 그늘)
        mott = ctx.noise(scale_px=3, amp=1.0, octaves=2, seed=113 + seed * 7)
        base *= (1.0 + 0.05 * np.tanh(mott) - 0.06 * (1.0 - bevel) + 0.03 * (fz_b - 0.5))[..., None]
        spots = ctx.noise(scale_px=1, amp=1.0, octaves=1, seed=117 + seed) > 2.3
        base[spots] *= 0.70
        ctx.rgb[...] = np.clip(base, 26, 212)

        # 줄눈: 무채 밝은~중간 회색 시멘트 (규칙 18, 베이지 금지), 모래 결 + 깊이 홈
        mvar = ctx.noise(scale_px=2, amp=1.0, octaves=2, seed=121 + seed)
        m_rgb = np.asarray(mortar_rgb, np.float32)[None, :] * (1.0 + 0.06 * np.tanh(mvar[joint]))[:, None]
        ctx.rgb[joint] = np.clip(m_rgb, 60, 200)
        ctx.height[...] = 0.30 * bevel + 0.08 * np.tanh(mott)
        ctx.height[joint] = -0.42 + 0.05 * mvar[joint]
        ctx.height[spots] -= 0.12
        # 미세 표면 거칠기
        ctx.grain(amp=3.4, scale_px=2, height=0.12, seed=101 + seed * 5)
        v = _var(ctx, scale_px=8, seed=107 + seed * 3)
        g_brick = 0.22 + 0.06 * r_val + 0.04 * v + 0.03 * bevel
        ctx.gloss = np.clip(np.where(joint, 0.11 + 0.02 * v, g_brick), 0.08, 0.36)
    return painter


def _make_soldier_painter(seed, mortar_rgb):
    """창·문 위 세워쌓기 벽돌 인방(벽돌 세로 1장 = 57 mm 폭) + 회색 줄눈. 칸 전체 UV(u 가로, v 세로)."""
    def painter(ctx):
        x, z = ctx.meters()
        bw = 0.072
        col = np.floor(x / bw)
        joint = ((x % bw) < 0.010) | (z < 0.012) | (z > ctx.tile[1] - 0.012)
        h = np.sin(col * 12.9898 + seed * 7.0) * 43758.5453
        r = (h - np.floor(h)) - 0.5
        ctx.rgb[...] = np.clip(ctx.rgb * (1.0 + 0.22 * r)[..., None], 26, 212)
        ctx.rgb[joint] = mortar_rgb
        fx = (x % bw) / bw
        ctx.height[...] = np.clip(np.minimum(fx, 1.0 - fx) * bw / 0.010, 0, 1) * 0.3
        ctx.height[joint] = -0.42
        ctx.grain(amp=3.4, scale_px=2, height=0.10, seed=401 + seed)
        ctx.gloss = np.where(joint, 0.12, np.clip(0.22 + 0.05 * r, 0.12, 0.32))
    return painter


def _make_granite_painter(seed):
    """화강석 문선·문턱·창대 (회백 반점 + 버너 마감 결)."""
    def painter(ctx):
        n1 = ctx.noise(scale_px=1, amp=1.0, octaves=1, seed=411 + seed)
        n2 = ctx.noise(scale_px=2, amp=1.0, octaves=1, seed=413 + seed)
        dark = n1 > 1.9
        lite = n2 > 2.1
        ctx.rgb[dark] *= 0.74
        ctx.rgb[lite] = np.minimum(ctx.rgb[lite] * 1.05, 212)
        ctx.rgb[...] *= (1.0 + 0.03 * np.tanh(ctx.noise(scale_px=8, amp=1.0, octaves=2, seed=415 + seed)))[..., None]
        ctx.grain(amp=5.0, scale_px=2, height=0.18, seed=417 + seed)
        ctx.height[dark] -= 0.10
        v = _var(ctx, scale_px=6, seed=419 + seed)
        ctx.gloss = np.clip(0.30 + 0.05 * v + np.where(dark, 0.06, 0.0), 0.20, 0.42)
    return painter


def _make_door_wood_painter(seed):
    """목재 무늬 시트(현관문 패널): 세로 결 + 나이테 굴곡 + 반광 도장."""
    def painter(ctx):
        u, v = ctx.u, ctx.v
        warp = ctx.noise(scale_px=24, amp=1.0, octaves=2, seed=421 + seed)
        ring = np.sin((u * 110.0 + 0.45 * warp + 0.10 * np.sin(v * 5.0)) * np.pi)
        fine = ctx.noise(scale_px=1, amp=1.0, octaves=1, seed=423 + seed)
        streak = np.repeat(fine.mean(axis=0, keepdims=True), ctx.h, axis=0)
        ctx.rgb[...] = np.clip(ctx.rgb * (0.94 + 0.05 * ring + 0.12 * np.tanh(streak * 3.0))[..., None], 24, 190)
        ctx.height[...] = 0.06 * ring
        ctx.grain(amp=1.6, scale_px=1, height=0.03, seed=427 + seed)
        ctx.gloss = np.clip(0.44 + 0.05 * ring, 0.34, 0.54)
    return painter


def _make_door_metal_painter(seed):
    """현관 방화문 도장 강판: 미세 오렌지필 + 은은한 결 + 반광."""
    def painter(ctx):
        n = ctx.noise(scale_px=2, amp=1.0, octaves=2, seed=431 + seed)
        ctx.rgb[...] = np.clip(ctx.rgb * (1.0 + 0.025 * np.tanh(n))[..., None], 20, 200)
        ctx.height[...] = 0.04 * n
        v = _var(ctx, scale_px=10, seed=433 + seed)
        ctx.gloss = np.clip(0.52 + 0.05 * v, 0.44, 0.62)
    return painter


def _make_doorlock_painter(seed):
    """디지털 도어락 전면(칸 전체 UV): 검은 유리 키패드 3x4 + 은색 테두리 + 손잡이 받침."""
    def painter(ctx):
        u, v = ctx.u, ctx.v
        rim = (u < 0.10) | (u > 0.90) | (v < 0.05) | (v > 0.95)
        pad = (u > 0.18) & (u < 0.82) & (v > 0.52) & (v < 0.90)
        ctx.rgb[...] = (40, 42, 46)
        ctx.rgb[rim] = (150, 152, 156)
        ku = ((u - 0.18) / 0.64 * 3.0) % 1.0
        kv = ((v - 0.52) / 0.38 * 4.0) % 1.0
        key = pad & (np.abs(ku - 0.5) < 0.26) & (np.abs(kv - 0.5) < 0.22)
        ctx.rgb[key] = (92, 96, 102)
        ctx.height[rim] += 0.2
        ctx.height[key] += 0.08
        ctx.emis[...] = np.where(key, 0.25, 0.0)
        ctx.gloss = np.where(rim, 0.62, np.where(pad, 0.86, 0.50))
    return painter


def _make_gate_plate_painter(seed):
    """철제 대문 하부 프레스 강판(칸 전체 UV): 돌출 사각 패널 2단 + 테두리 띠 + 도장 결."""
    def painter(ctx):
        u, v = ctx.u, ctx.v
        h = np.zeros_like(u)
        for (p0, p1) in ((0.06, 0.46), (0.54, 0.94)):
            inside = (u > 0.08) & (u < 0.92) & (v > p0) & (v < p1)
            d = np.minimum.reduce([u - 0.08, 0.92 - u, (v - p0) * 0.6, (p1 - v) * 0.6])
            h = np.where(inside, np.clip(d / 0.05, 0, 1), h)
        ctx.height[...] = 0.5 * h
        # 패널 경사면(0<h<1) 위쪽은 밝게, 아래쪽은 어둡게 -> 프레스 요철 음영
        slope = (h > 0.02) & (h < 0.98)
        upper = np.gradient(h, axis=0) < 0
        ctx.rgb[...] = np.clip(ctx.rgb * (0.90 + 0.12 * h)[..., None], 20, 200)
        ctx.rgb[slope & upper] *= 1.25
        ctx.rgb[slope & ~upper] *= 0.70
        ctx.grain(amp=1.4, scale_px=2, height=0.02, seed=441 + seed)
        ctx.gloss = np.clip(0.40 + 0.06 * h, 0.34, 0.50)
    return painter


def _make_plaster_painter(seed, grain_amp=2.6):
    """깨끗한 2000~2010년대 백색·회백색 미장/도장 콘크리트 (오염 띠 없음, 명도 <= 218)."""
    def painter(ctx):
        ctx.grain(amp=grain_amp, scale_px=3, height=0.07, seed=131 + seed * 7)
        # 흙손 자국(완만한 굴곡) + 뿜칠 미세 요철 -> 근접 시 평면감 해소
        trowel = ctx.noise(scale_px=max(10, ctx.w // 14), amp=1.0, octaves=3, seed=133 + seed)
        spray = ctx.noise(scale_px=1, amp=1.0, octaves=2, seed=135 + seed)
        ctx.height += 0.09 * np.tanh(trowel) + 0.03 * spray
        ctx.rgb[...] = ctx.rgb * (1.0 + 0.018 * np.tanh(trowel) + 0.012 * spray)[..., None]
        k = ctx.stains(amount=0.035, scale_px=max(16, ctx.w // 6), streaks=0.06, seed=137 + seed * 3)
        v = _var(ctx, scale_px=12, seed=139 + seed * 5)
        ctx.rgb[...] = np.clip(ctx.rgb * (1.0 - 0.035 * k[..., None]), 40, 218)
        ctx.gloss = np.clip(0.24 + 0.03 * v - 0.03 * k + 0.02 * np.tanh(trowel), 0.14, 0.34)
    return painter


def _make_concrete_plinth_painter(seed):
    """경사지·평지 회백색 콘크리트 기단/계단 (규칙 13: 실스케일 타일, 폼타이/미세 기공)."""
    def painter(ctx):
        d = ctx.joints(cols=3, rows=2, width_m=0.008, depth=0.22, darken=0.12, tone=4, seed=151 + seed)
        ctx.grain(amp=5.2, scale_px=2, height=0.16, seed=157 + seed * 3)
        k = ctx.stains(amount=0.05, scale_px=max(12, ctx.w // 5), streaks=0.12, seed=163 + seed * 5)
        v = _var(ctx, scale_px=10, seed=167 + seed)
        ctx.rgb[...] = np.clip(ctx.rgb * (1.0 - 0.05 * k[..., None]), 40, 212)
        ctx.gloss = np.clip((0.25 + 0.04 * v - 0.04 * k) * (1.0 - d) + 0.14 * d, 0.11, 0.34)
    return painter


def _make_clay_tile_painter(seed):
    """한국형 S-골 기와(적갈/암회) — 세로 골(u 방향) + 수평 단차(v 방향) 선명한 입체감."""
    def painter(ctx):
        x, z = ctx.meters()
        # 기와 1골 폭 ~0.22 m, 수평 겹침 단차 ~0.28 m
        phase = x * (2.0 * np.pi / 0.22)
        wave = np.cos(phase)                              # -1 (골 바닥) ~ +1 (마루)
        row_f = (z % 0.28) / 0.28                         # 0 (아래 겹침 턱) ~ 1 (위)
        step_shadow = np.exp(-row_f * 9.0)                # 각 줄 아래 진한 겹침 그림자
        row_i = np.floor(z / 0.28)
        col_i = np.floor(x / 0.22)
        h = np.sin(row_i * 19.1 + col_i * 47.3 + seed * 11.0) * 15731.7
        tile_var = ((h - np.floor(h)) - 0.5) * 0.12

        shade = 0.88 + 0.14 * wave - 0.22 * step_shadow + tile_var
        ctx.rgb[...] = np.clip(ctx.rgb * shade[..., None], 24, 215)
        ctx.height[...] = 0.52 * wave + 0.22 * (1.0 - row_f) - 0.35 * step_shadow
        ctx.grain(amp=2.6, scale_px=2, height=0.05, seed=173 + seed * 3)
        v = _var(ctx, scale_px=10, seed=179 + seed)
        ctx.gloss = np.clip(0.36 + 0.08 * wave - 0.10 * step_shadow + 0.03 * v, 0.16, 0.52)
    return painter


def _make_wood_soffit_painter(seed):
    """처마 하부 목재 루버/널판 소핏 (h07_front, h12_det_roof 근거)."""
    def painter(ctx):
        x, z = ctx.meters()
        plank_w = 0.11
        seam = (x % plank_w) < 0.008
        idx = np.floor(x / plank_w)
        h = np.sin(idx * 23.7 + seed * 7.0) * 9137.3
        tone = 0.92 + ((h - np.floor(h)) - 0.5) * 0.14
        grain = 0.04 * np.sin(z * 18.0 + idx * 2.1)
        ctx.rgb[...] = np.clip(ctx.rgb * (tone + grain)[..., None], 24, 200)
        ctx.rgb[seam] *= 0.52
        ctx.height[seam] -= 0.28
        ctx.grain(amp=3.0, scale_px=2, height=0.06, seed=191 + seed)
        ctx.gloss = np.clip(np.where(seam, 0.14, 0.32 + 0.03 * _var(ctx, 8, 193 + seed)), 0.12, 0.42)
    return painter


def _make_terrace_floor_painter(seed):
    """옥상 테라스 회색 우레탄/콘크리트 방수 바닥 (구식 70년대 초록 방수 대신 2000~2010년대 회색)."""
    def painter(ctx):
        d = ctx.joints(cols=2, rows=2, width_m=0.008, depth=0.12, darken=0.10, tone=3, seed=211 + seed)
        ctx.grain(amp=3.0, scale_px=4, height=0.06, seed=213 + seed)
        k = ctx.stains(amount=0.06, scale_px=24, streaks=0.0, seed=217 + seed)
        v = _var(ctx, scale_px=12, seed=223 + seed)
        ctx.rgb[...] = np.clip(ctx.rgb * (1.0 - 0.06 * k[..., None]), 45, 205)
        ctx.gloss = np.clip((0.30 + 0.04 * v - 0.05 * k) * (1.0 - d) + 0.15 * d, 0.14, 0.42)
    return painter


def _make_polycarb_painter(seed):
    """철골 폴리카보네이트(렉산) 지붕 판재: 중공 리브 줄무늬 + 패널 이음 H-바 + 반투명 광택."""
    def painter(ctx):
        x, _ = ctx.meters()
        rib = np.cos(x * 2.0 * np.pi / 0.055)
        seam = (x % 0.65) < 0.018
        band = 0.03 * np.sin(x * 2.0 * np.pi / 0.65)
        ctx.rgb[...] = np.clip(ctx.rgb * (0.95 + 0.05 * rib + band)[..., None], 38, 215)
        ctx.rgb[seam] *= 0.66
        ctx.height[...] = 0.10 * rib - np.where(seam, 0.22, 0.0)
        ctx.grain(amp=1.2, scale_px=3, height=0.02, seed=227 + seed)
        ctx.gloss = np.clip(0.82 + 0.06 * rib - np.where(seam, 0.30, 0.0), 0.42, 0.92)
    return painter


def _make_window_painter(seed):
    """주거용 창 유리: 실내 커튼/블라인드 미세 깊이감 + 야간 따뜻한 실내 발광."""
    def painter(ctx):
        u, v = ctx.u * K.REF_GRID, ctx.v * K.REF_GRID
        cell = v.astype(int) * K.REF_GRID + u.astype(int)
        cu, cv = u % 1.0, v % 1.0
        # 커튼 주름 + 상단 살짝 어두운 실내 천장 그림자
        curtain = 0.5 + 0.5 * np.cos(cu * (2.0 * np.pi * 12.0))
        shade_v = 0.80 + 0.18 * (1.0 - cv)
        edge = (np.minimum(cu, 1.0 - cu) < 0.02) | (np.minimum(cv, 1.0 - cv) < 0.02)
        # 약 56% 세대/방 야간 점등 (따뜻하고 또렷한 실내 발광)
        lit_cells = tuple((k * 3 + seed) % (K.REF_GRID * K.REF_GRID) for k in range(14))
        lit = np.isin(cell, lit_cells) & ~edge
        ctx.rgb[...] = np.clip(ctx.rgb * (shade_v * (0.86 + 0.12 * curtain))[..., None], 22, 185)
        ctx.emis[...] = np.where(lit, (0.58 + 0.14 * (cell % 3)) * (0.76 + 0.24 * curtain), 0.0)
        nv = _var(ctx, scale_px=10, seed=241 + seed)
        ctx.gloss = np.where(edge, 0.62, np.clip(0.82 - 0.06 * curtain + 0.03 * nv, 0.68, 0.90))
    return painter


def _make_address_painter(road_name, road_no):
    """한국 도로명 건물번호판 (규칙 20: 남색 바탕·흰 테두리·가상 도로명/번호 2줄, 채도 <= 0.55)."""
    def painter(ctx):
        cache = HERE / "work" / "_sign_cache" / f"addr_{road_name}_{road_no}_{ctx.w}x{ctx.h}.npz"
        # 약간 바랜 알루미늄 남색 (전체 평균 채도 ~0.44 < 0.55 로 albedo_check 통과)
        navy = (42, 66, 108)
        white = (214, 216, 220)
        try:
            from PIL import Image, ImageDraw, ImageFont
            S = 4
            W, H = ctx.w * S, ctx.h * S
            im = Image.new("RGB", (W, H), navy)
            d = ImageDraw.Draw(im)
            m = max(4, int(min(W, H) * 0.07))
            d.rectangle([m, m, W - 1 - m, H - 1 - m], outline=white, width=max(3, int(H * 0.038)))
            f_road = ImageFont.truetype("C:/Windows/Fonts/H2GTRE.TTF", int(H * 0.22))
            f_num = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(H * 0.44))
            d.text((W * 0.5, H * 0.30), road_name, font=f_road, fill=white, anchor="mm")
            d.text((W * 0.5, H * 0.67), road_no, font=f_num, fill=white, anchor="mm")
            rgb = np.asarray(im.resize((ctx.w, ctx.h), Image.LANCZOS))
            cache.parent.mkdir(parents=True, exist_ok=True)
            np.savez(cache, rgb=rgb)
        except (ImportError, OSError):
            if cache.exists():
                rgb = np.load(cache)["rgb"]
            else:
                rgb = np.full((ctx.h, ctx.w, 3), navy, dtype=np.uint8)
        ctx.rgb[...] = rgb
        ctx.grain(amp=1.2, scale_px=2, height=0.02, seed=251)
        ctx.gloss = np.clip(0.48 + 0.03 * _var(ctx, 8, 257), 0.40, 0.56)
    return painter


def _make_louver_painter(seed):
    """에어컨 실외기 전면 그릴/루버."""
    def painter(ctx):
        rib = np.cos(ctx.v * 38.0 * np.pi) > 0.20
        ctx.rgb[rib] *= 0.46
        ctx.height[rib] -= 0.32
        ctx.grain(amp=2.0, scale_px=2, height=0.04, seed=263 + seed)
        ctx.gloss = np.clip(np.where(rib, 0.16, 0.40 + 0.03 * _var(ctx, 6, 269 + seed)), 0.12, 0.48)
    return painter


def _make_meter_painter(seed):
    """전력·가스 계량기함 전면 (회백 케이스 + 검정 검침창 + 다이얼)."""
    def painter(ctx):
        u, v = ctx.u, ctx.v
        border = (u < 0.08) | (u > 0.92) | (v < 0.08) | (v > 0.92)
        win = (u > 0.22) & (u < 0.78) & (v > 0.54) & (v < 0.80)
        dial = (u > 0.30) & (u < 0.70) & (v > 0.62) & (v < 0.72)
        ctx.rgb[border] *= 0.86
        ctx.rgb[win] = (54, 58, 62)
        ctx.rgb[dial] = (176, 178, 174)
        ctx.height[border] += 0.12
        ctx.height[win] -= 0.18
        ctx.grain(amp=2.0, scale_px=2, height=0.03, seed=271 + seed)
        ctx.gloss = np.clip(np.where(win, 0.72, 0.34), 0.20, 0.78)
    return painter


def _solid(amp=2.4, g_lo=0.28, g_hi=0.40, seed=1):
    def painter(ctx):
        ctx.grain(amp=amp, scale_px=2, height=0.05, seed=300 + seed)
        v = _var(ctx, scale_px=max(4, ctx.w // 8), seed=310 + seed)
        mid = 0.5 * (g_lo + g_hi)
        ctx.gloss = np.clip(mid + 0.5 * (g_hi - g_lo) * v, g_lo, g_hi)
    return painter


def _make_solar_painter(seed):
    """옥상 태양광/태양열 패널 (짙은 청회색 셀 + 은색 격자선 + 알루미늄 외곽)."""
    def painter(ctx):
        u, v = ctx.u, ctx.v
        border = (u < 0.03) | (u > 0.97) | (v < 0.03) | (v > 0.97)
        grid = ((u * 8.0) % 1.0 < 0.035) | ((v * 5.0) % 1.0 < 0.035)
        ctx.rgb[grid] = (138, 146, 156)
        ctx.rgb[border] = (176, 180, 184)
        ctx.height[border] += 0.14
        ctx.height[grid] -= 0.04
        ctx.grain(amp=1.5, scale_px=2, height=0.02, seed=321 + seed)
        ctx.gloss = np.where(border, 0.52, np.where(grid, 0.45, 0.80))
    return painter


def _make_awning_painter(seed):
    """상가 천막 어닝: 직물 미세 질감 + 0.45 m 간격 패널 이음줄."""
    def painter(ctx):
        u, v = ctx.u, ctx.v
        seam = ((u * 6.0) % 1.0) < 0.025
        stripe = np.cos(u * 12.0 * np.pi) * 0.03
        ctx.rgb[...] = np.clip(ctx.rgb * (1.0 + stripe)[..., None], 28, 210)
        ctx.rgb[seam] *= 0.80
        ctx.height[seam] -= 0.12
        ctx.grain(amp=3.4, scale_px=2, height=0.08, seed=331 + seed)
        ctx.gloss = np.clip(0.18 + 0.02 * _var(ctx, 8, 337 + seed), 0.12, 0.26)
    return painter


def _make_shop_signs_painter(spec: DetachedSpec):
    """T4 근린상가 한글 간판 시트 (규칙 12/19: HMKMRHD/H2HDRM 간판 글꼴, 가상 상호, uv_sub 전용).

    1024x1024 슈퍼샘플링 후 512x512 리사이즈:
    - 좌측 가로 간판 (y=0..176, 비율 5.8:1)
    - 우측 가로 간판 (y=192..410, 비율 4.7:1)
    - 세로 돌출 간판 (x=16..180, y=432..1008, 비율 1:3.5)
    - 우하단 보조 안내판 (x=208..1008, y=432..1008)
    """
    def painter(ctx):
        cache = HERE / "work" / "_sign_cache" / f"shop_{spec.seed}_{ctx.w}x{ctx.h}.npz"
        bg_sheet = (68, 72, 78)
        navy = (52, 74, 106)       # S=0.509 < 0.55
        burgundy = (144, 74, 70)   # S=0.514 < 0.55
        cream = (218, 216, 208)    # V=218 <= 225
        gold = (214, 192, 128)     # S=0.402, V=214
        try:
            from PIL import Image, ImageDraw, ImageFont
            W, H = 1024, 1024
            im = Image.new("RGB", (W, H), bg_sheet)
            d = ImageDraw.Draw(im)

            # 1) 좌측 가로 간판: 대청철물·건재 (y=4..172)
            d.rectangle([4, 4, 1020, 172], fill=navy)
            d.rectangle([10, 10, 1014, 166], outline=cream, width=4)
            f_sub1 = ImageFont.truetype("C:/Windows/Fonts/H2GTRE.TTF", 34)
            f_tel1 = ImageFont.truetype("C:/Windows/Fonts/H2HDRM.TTF", 40)
            # 상호가 업종·전화 블록과 겹치지 않게 글자 크기 자동 축소
            right_blk = max(d.textlength(spec.shop_sub, font=f_sub1), d.textlength(spec.shop_tel, font=f_tel1))
            fs = 92
            while fs > 56:
                f_main1 = ImageFont.truetype("C:/Windows/Fonts/HMKMRHD.TTF", fs)
                if 38 + d.textlength(spec.shop_name, font=f_main1) < 985 - right_blk - 28:
                    break
                fs -= 4
            d.text((38, 88), spec.shop_name, font=f_main1, fill=cream, anchor="lm")
            d.text((985, 58), spec.shop_sub, font=f_sub1, fill=gold, anchor="rm")
            d.text((985, 118), spec.shop_tel, font=f_tel1, fill=cream, anchor="rm")

            # 2) 우측 가로 간판: 한밭분식 (y=196..406)
            d.rectangle([4, 196, 1020, 406], fill=burgundy)
            d.rectangle([12, 204, 1012, 398], outline=cream, width=5)
            f_main2 = ImageFont.truetype("C:/Windows/Fonts/H2HDRM.TTF", 122)
            f_sub2 = ImageFont.truetype("C:/Windows/Fonts/H2GTRE.TTF", 40)
            f_tel2 = ImageFont.truetype("C:/Windows/Fonts/HMKMRHD.TTF", 44)
            d.text((48, 302), spec.shop_name2, font=f_main2, fill=cream, anchor="lm")
            d.text((980, 266), spec.shop_sub2, font=f_sub2, fill=gold, anchor="rm")
            d.text((980, 342), spec.shop_tel2, font=f_tel2, fill=cream, anchor="rm")

            # 3) 좌측 세로 돌출 간판: 대 청 철 물 (x=20..176, y=436..1004)
            d.rectangle([20, 436, 176, 1004], fill=navy)
            d.rectangle([28, 444, 168, 996], outline=cream, width=4)
            f_vert = ImageFont.truetype("C:/Windows/Fonts/HMKMRHD.TTF", 96)
            chars = list(spec.vert_sign)
            step_y = 510.0 / max(1, len(chars))
            for idx, ch in enumerate(chars):
                cy = 466 + (idx + 0.5) * step_y
                fill_c = gold if idx < 2 else cream
                d.text((98, cy), ch, font=f_vert, fill=fill_c, anchor="mm")

            # 4) 나머지 영역: 차분한 회청 톤 유지 (평균 채도/명도 안정화)
            d.rectangle([208, 436, 1004, 1004], fill=(102, 108, 114))

            rgb = np.asarray(im.resize((ctx.w, ctx.h), Image.LANCZOS))
            cache.parent.mkdir(parents=True, exist_ok=True)
            np.savez(cache, rgb=rgb)
        except (ImportError, OSError):
            if cache.exists():
                rgb = np.load(cache)["rgb"]
            else:
                rgb = np.full((ctx.h, ctx.w, 3), navy, dtype=np.uint8)
        ctx.rgb[...] = rgb
        # 야간 간판 은은한 백라이트 발광 (문자 영역만 살짝 더 밝게)
        lum = rgb.mean(axis=-1) / 255.0
        ctx.emis[...] = np.clip(0.14 + 0.28 * np.clip((lum - 0.45) * 2.2, 0.0, 1.0), 0.12, 0.44)
        ctx.grain(amp=1.0, scale_px=2, height=0.01, seed=347 + spec.seed)
        ctx.gloss = np.clip(0.56 + 0.03 * _var(ctx, 8, 353 + spec.seed), 0.48, 0.64)
    return painter


# ---------------------------------------------------------------------------
# 아틀라스 구성 (2048x2048, STYLE_BRIEF 4장 권장 알베도 준수)
# ---------------------------------------------------------------------------
PALETTE_RGB = {
    "dark_brown_brick": (84, 64, 60),    # S=0.286, V=84 (STYLE_BRIEF 권장 (76~98,58~76,56~70))
    "red_brown_brick":  (124, 82, 72),   # S=0.419, V=124 (STYLE_BRIEF 권장 (114~136,76~86,68~76))
    "dark_red_brown_brick": (108, 76, 70),  # S=0.352, V=108 (02: d02_street_awning 직사광 벽돌 (106,83,87) 기준 암적갈)
    "charcoal_brick":   (74, 77, 83),    # S=0.108, V=83
    "offwhite_plaster": (196, 195, 192), # S=0.020, V=196
}


def build_atlas(spec: DetachedSpec) -> K.Atlas:
    s = spec.seed
    a = K.Atlas(size=2048, pad=12)

    wall_rgb = PALETTE_RGB[spec.wall_palette]
    mortar_rgb = (176, 175, 174)  # STYLE_BRIEF 실측 줄눈 평균 (177,161,162) -> 무채 회색 시멘트

    # 외벽 주재: 변형 3칸 (월드 타일마다 다른 벽돌 배열 -> 반복 무늬 제거), 노멀 강도 상향
    if spec.wall_palette == "offwhite_plaster":
        a.add("wall_main", color=wall_rgb, ctrl=(0, 255, 0), px=384, tile=(2.4, 2.4),
              gloss=0.24, painter=_make_plaster_painter(s), variants=2, normal_strength=2.2)
    else:
        a.add("wall_main", color=wall_rgb, ctrl=(0, 255, 0), px=512, tile=(2.3, 2.4),
              gloss=0.24, painter=_make_brick_painter(s, mortar_rgb), variants=3, normal_strength=3.2)
        # 창·문 위 세워쌓기 벽돌 인방 (칸 전체 UV, 1.2 x 0.15 m 비율)
        a.add("brick_soldier", color=wall_rgb, ctrl=(0, 255, 0), px=128, tile=(1.2, 0.15),
              gloss=0.22, painter=_make_soldier_painter(s, mortar_rgb), normal_strength=3.0)

    # 흰색·회백색 미장 / 슬래브 띠 / 처마 띠 / 창 악센트 (알베도 V <= 218 준수)
    a.add("plaster_white", color=(214, 213, 210), ctrl=(0, 255, 0), px=256, tile=(2.4, 2.4),
          gloss=0.24, painter=_make_plaster_painter(s + 11), variants=2, normal_strength=2.2)

    # 회백색 콘크리트 기단 / 계단 / 갓돌 / 담장 캡 (실스케일 타일)
    a.add("concrete_light", color=(178, 180, 183), px=256, tile=(2.4, 2.4),
          gloss=0.24, painter=_make_concrete_plinth_painter(s + 23), variants=2, normal_strength=2.6)
    # 화강석 문선·문턱·창대 (반점 석재)
    a.add("granite", color=(176, 174, 172), px=128, tile=(0.9, 0.9), gloss=0.30,
          painter=_make_granite_painter(s + 25), normal_strength=2.4)

    # 지붕 기와 (적갈 / 암회)
    clay_rgb = (134, 84, 74) if spec.roof_type != "hip_tile_dark" else (68, 66, 68)
    a.add("clay_tile", color=clay_rgb, ctrl=(255, 0, 0), px=384, tile=(1.76, 1.68),
          gloss=0.36, painter=_make_clay_tile_painter(s + 31))
    a.add("clay_trim", color=clay_rgb, ctrl=(255, 0, 0), px=128,
          gloss=0.38, painter=_solid(3.0, 0.30, 0.44, s + 33))

    # 처마 하부 목재 소핏 (S=0.481 < 0.55)
    a.add("wood_soffit", color=(108, 76, 56), px=256, tile=(1.76, 1.76),
          gloss=0.30, painter=_make_wood_soffit_painter(s + 41))

    # 옥상 테라스 방수 바닥 (회색 우레탄/콘크리트)
    a.add("terrace_floor", color=(138, 141, 140), px=256, tile=(2.4, 2.4),
          gloss=0.28, painter=_make_terrace_floor_painter(s + 47))

    # 창 유리 (야간 발광) + LOD2 뒷판
    win_col = (76, 98, 110)
    a.add("window", color=win_col, px=384, gloss=0.82,
          emissive=(255, 214, 152), painter=_make_window_painter(s + 53))
    a.add("window_backing", color=win_col, px=32, gloss=0.78)

    # 창틀 (흰 PVC / 암회색 샷시)
    sash_rgb = (212, 212, 214) if spec.sash_style == "pvc_white" else (58, 62, 66)
    a.add("sash", color=sash_rgb, px=128, gloss=0.52, painter=_solid(1.8, 0.46, 0.58, s + 59))
    a.add("pvc_white", color=(212, 212, 214), px=128, gloss=0.52, painter=_solid(1.6, 0.46, 0.58, s + 61))
    a.add("sash_dark", color=(58, 62, 66), px=128, gloss=0.48, painter=_solid(2.0, 0.42, 0.54, s + 63))

    # 금속 난간 (스테인리스 / 암회색 철제)
    a.add("stainless", color=(172, 174, 178), px=128, metal=0.65, gloss=0.62,
          painter=_solid(2.0, 0.54, 0.68, s + 67))
    a.add("rail_bronze", color=(146, 142, 140), px=128, metal=0.55, gloss=0.58,
          painter=_solid(2.2, 0.48, 0.62, s + 69))
    a.add("iron_dark", color=(56, 58, 62), px=128, metal=0.45, gloss=0.42,
          painter=_solid(2.4, 0.34, 0.48, s + 71))

    # 폴리카보네이트(렉산) 차양 (청회 반투명 톤 / 암녹)
    a.add("poly_smoke", color=(142, 162, 178), px=256, tile=(1.3, 1.3), gloss=0.82,
          painter=_make_polycarb_painter(s + 73))
    a.add("poly_green", color=(88, 114, 108), px=256, tile=(1.3, 1.3), gloss=0.74,
          painter=_make_polycarb_painter(s + 79))

    # 설비·현관문·배관·계량기·도로명판·조명·깊이 그림자 (화분 식재는 사용자 요청으로 제외)
    a.add("door_wood", color=(96, 70, 54), px=256, gloss=0.44, painter=_make_door_wood_painter(s + 83))
    a.add("door_metal", color=(74, 66, 60), px=128, metal=0.30, gloss=0.52,
          painter=_make_door_metal_painter(s + 85))
    a.add("doorlock", px=64, gloss=0.6, emissive=(150, 200, 255), painter=_make_doorlock_painter(s + 87))
    a.add("gate_plate", color=(58, 60, 62), px=128, metal=0.40, gloss=0.42,
          painter=_make_gate_plate_painter(s + 91))
    a.add("equip_gray", color=(184, 186, 184), px=128, gloss=0.36, painter=_solid(2.2, 0.30, 0.42, s + 89))
    a.add("louver", color=(162, 166, 164), px=128, gloss=0.38, painter=_make_louver_painter(s + 97))
    a.add("meter_face", color=(188, 190, 188), px=128, gloss=0.36, painter=_make_meter_painter(s + 101))
    a.add("pipe_white", color=(196, 198, 198), px=64, gloss=0.48, painter=_solid(1.5, 0.42, 0.54, s + 103))
    a.add("address", px=256, gloss=0.48, painter=_make_address_painter(spec.road_name, spec.road_no))
    a.add("lamp", color=(244, 224, 182), emissive=(255, 224, 168), px=32, gloss=0.62,
          painter=_solid(1.0, 0.56, 0.66, s + 107))
    a.add("shadow_recess", color=(34, 34, 38), px=32, gloss=0.10, painter=_solid(1.2, 0.08, 0.14, s + 111))

    if spec.roof_addon in ("solar", "both"):
        a.add("solar_panel", color=(54, 68, 88), px=256, gloss=0.78,
              painter=_make_solar_painter(s + 113))

    if spec.archetype == "shop_1f":
        a.add("shop_signs", color=(68, 72, 78), px=512, gloss=0.56,
              emissive=(255, 240, 210), painter=_make_shop_signs_painter(spec))
        a.add("awning_green", color=(66, 94, 82), px=128, gloss=0.18,
              painter=_make_awning_painter(s + 121))
        a.add("awning_wine", color=(116, 68, 76), px=128, gloss=0.18,
              painter=_make_awning_painter(s + 127))

    return a


# ---------------------------------------------------------------------------
# 기하 헬퍼 (겹침 면 0, 지면 접촉 bottom skip, 정확한 타일 UV)
# ---------------------------------------------------------------------------
def _clip_poly_2d(poly, fn_inside, fn_intersect):
    """Sutherland-Hodgman 반평면 클리핑."""
    if not poly:
        return []
    out = []
    prev = poly[-1]
    prev_in = fn_inside(prev)
    for curr in poly:
        curr_in = fn_inside(curr)
        if curr_in:
            if not prev_in:
                out.append(fn_intersect(prev, curr))
            out.append(curr)
        elif prev_in:
            out.append(fn_intersect(prev, curr))
        prev, prev_in = curr, curr_in
    return out


def _clip_poly_rect(poly, u0, u1, v0, v1):
    def ix_u(p, q, uc):
        t = (uc - p[0]) / (q[0] - p[0])
        return (uc, p[1] + t * (q[1] - p[1]))

    def ix_v(p, q, vc):
        t = (vc - p[1]) / (q[1] - p[1])
        return (p[0] + t * (q[0] - p[0]), vc)

    p = _clip_poly_2d(poly, lambda pt: pt[0] >= u0 - 1e-7, lambda a, b: ix_u(a, b, u0))
    p = _clip_poly_2d(p, lambda pt: pt[0] <= u1 + 1e-7, lambda a, b: ix_u(a, b, u1))
    p = _clip_poly_2d(p, lambda pt: pt[1] >= v0 - 1e-7, lambda a, b: ix_v(a, b, v0))
    p = _clip_poly_2d(p, lambda pt: pt[1] <= v1 + 1e-7, lambda a, b: ix_v(a, b, v1))
    return p


def add_tiled_slope_poly(mb: K.MeshBuilder, pts3, region: str, stage: int):
    """임의 볼록 3D 경사 다각형(사다리꼴/삼각형)을 타일 격자로 정확히 잘라 실스케일 UV 부착.

    pts3[0]->pts3[1] 방향이 가로(u, 처마 수평), 경사 올라가는 방향이 세로(v, 용마루 방향).
    """
    A = mb.atlas
    p0 = np.asarray(pts3[0], float)
    p1 = np.asarray(pts3[1], float)
    p_last = np.asarray(pts3[-1], float)
    eu = p1 - p0
    eu /= np.linalg.norm(eu)
    nrm = np.cross(eu, p_last - p0)
    nrm /= np.linalg.norm(nrm)
    ev = np.cross(nrm, eu)
    ev /= np.linalg.norm(ev)

    poly2 = [(float(np.dot(np.asarray(p, float) - p0, eu)),
              float(np.dot(np.asarray(p, float) - p0, ev))) for p in pts3]

    def to3(uv2):
        pt = p0 + eu * uv2[0] + ev * uv2[1]
        return (float(pt[0]), float(pt[1]), float(pt[2]))

    if stage == 2 or not A.is_tiled(region):
        uv_rect = A.uv(region)
        if len(pts3) == 4:
            mb.quad(pts3, uv_rect, region)
        else:
            for k in range(1, len(pts3) - 1):
                mb.tri([pts3[0], pts3[k], pts3[k + 1]], uv_rect[:3], region)
        return

    tw, th = A.tile_size(region)
    u_min = min(pt[0] for pt in poly2)
    u_max = max(pt[0] for pt in poly2)
    v_min = min(pt[1] for pt in poly2)
    v_max = max(pt[1] for pt in poly2)
    i0, i1 = math.floor(u_min / tw), math.ceil(u_max / tw)
    j0, j1 = math.floor(v_min / th), math.ceil(v_max / th)

    au0, av0, au1, av1 = A._uvrect(region)
    e = 0.5 / A.size
    au0, av0, au1, av1 = au0 + e, av0 + e, au1 - e, av1 - e
    du, dv = au1 - au0, av1 - av0

    for j in range(j0, j1):
        vc0, vc1 = j * th, (j + 1) * th
        for i in range(i0, i1):
            uc0, uc1 = i * tw, (i + 1) * tw
            clipped = _clip_poly_rect(poly2, uc0, uc1, vc0, vc1)
            if len(clipped) < 3:
                continue
            pts_c = [to3(pt) for pt in clipped]
            uvs_c = [(au0 + ((pt[0] - uc0) / tw) * du,
                      av0 + ((pt[1] - vc0) / th) * dv) for pt in clipped]
            if len(pts_c) == 4:
                mb.quad(pts_c, uvs_c, region)
            else:
                for k in range(1, len(pts_c) - 1):
                    mb.tri([pts_c[0], pts_c[k], pts_c[k + 1]],
                           [uvs_c[0], uvs_c[k], uvs_c[k + 1]], region)


def add_beam(mb: K.MeshBuilder, p0, p1, half_w, half_h, region):
    """두 3D 점 p0->p1 을 잇는 직사각 단면 보/용마루/추녀/서까래 (닫힌 6면, 면 방향 정확)."""
    p0 = np.asarray(p0, float)
    p1 = np.asarray(p1, float)
    d = p1 - p0
    L = float(np.linalg.norm(d))
    if L < 1e-5:
        return
    u = d / L
    # 수평 옆 방향(r), 위쪽 수직 방향(up)
    if abs(u[2]) < 0.95:
        r = np.array([-u[1], u[0], 0.0], float)
        r /= np.linalg.norm(r)
    else:
        r = np.array([1.0, 0.0, 0.0], float)
    up = np.cross(r, u)
    up /= np.linalg.norm(up)
    if up[2] < 0:
        r = -r
        up = -up

    def ring(pt):
        return [
            tuple(pt - r * half_w - up * half_h),
            tuple(pt + r * half_w - up * half_h),
            tuple(pt + r * half_w + up * half_h),
            tuple(pt - r * half_w + up * half_h),
        ]

    r0, r1 = ring(p0), ring(p1)
    uv = mb.atlas.uv(region)
    # 옆면 4개 (바깥 법선: r0->r1 이 u 방향이므로 반시계 순서 확인)
    # 아래(-up): r0[1], r0[0], r1[0], r1[1] -> (r0[0]-r0[1])=-r, (r1[1]-r0[1])=+u -> (-r)x(+u) = -up
    # 오른쪽(+r): r0[2], r0[1], r1[1], r1[2] -> (-up)x(+u) = +r
    # 위(+up): r0[3], r0[2], r1[2], r1[3] -> (+r)x(+u) = +up
    # 왼쪽(-r): r0[0], r0[3], r1[3], r1[0] -> (+up)x(+u) = -r
    for a_i, b_i in ((1, 0), (2, 1), (3, 2), (0, 3)):
        mb.quad([r0[a_i], r0[b_i], r1[b_i], r1[a_i]], uv, region)
    # 양 끝단 캡: 시작면(-u), 끝면(+u)
    mb.quad([r0[0], r0[1], r0[2], r0[3]], uv, region)
    mb.quad([r1[3], r1[2], r1[1], r1[0]], uv, region)


def add_oct_tube(mb: K.MeshBuilder, p0, p1, r, region, n=8):
    """두 3D 점 p0->p1 을 잇는 다각 관 (우수관/배관, 닫힌 입체)."""
    p0 = np.asarray(p0, float)
    p1 = np.asarray(p1, float)
    d = p1 - p0
    L = float(np.linalg.norm(d))
    if L < 1e-5:
        return
    u = d / L
    rx = np.array([-u[1], u[0], 0.0], float) if abs(u[2]) < 0.92 else np.array([1.0, 0.0, 0.0], float)
    rx /= np.linalg.norm(rx)
    bx = np.cross(u, rx)
    ring0, ring1 = [], []
    for k in range(n):
        ang = k * 2.0 * math.pi / n
        off = rx * (math.cos(ang) * r) + bx * (math.sin(ang) * r)
        ring0.append(tuple(p0 + off))
        ring1.append(tuple(p1 + off))
    uv = mb.atlas.uv(region)
    for k in range(n):
        kn = (k + 1) % n
        mb.quad([ring0[k], ring0[kn], ring1[kn], ring1[k]], uv, region)
    for k in range(1, n - 1):
        mb.tri([ring0[0], ring0[k + 1], ring0[k]], uv[:3], region)
        mb.tri([ring1[0], ring1[k], ring1[k + 1]], uv[:3], region)


def add_hip_roof(mb: K.MeshBuilder, x0, x1, y0, y1, z_wall_top, eave_out, rise, stage,
                 soffit_reg="wood_soffit", fascia_reg="plaster_white",
                 tile_reg="clay_tile", trim_reg="clay_trim"):
    """한국형 낮은 모임지붕 + 목재 소핏 + 흰 계단형 처마 띠 + 3D 용마루·추녀·처마 막새 기와.

    - z_wall_top 에서 벽체 종료.
    - 소핏(목재): z_wall_top - 0.03 .. z_wall_top + 0.03 (eave_out - 0.04 돌출)
    - 흰 처마 띠: z_wall_top + 0.03 .. z_wall_top + 0.24 (eave_out 돌출, 4cm 계단 단차)
    - 4면 모임지붕: z_base = z_wall_top + 0.24 -> z_peak = z_base + rise
    """
    so = eave_out - 0.04
    z_sof0, z_sof1 = z_wall_top - 0.03, z_wall_top + 0.03
    z_fas1 = z_wall_top + 0.24

    # 1) 목재 소핏 + 흰 처마 띠 (닫힌 박스, 모서리 끊김·겹침 0)
    if stage < 2:
        mb.box(x0 - so, x1 + so, y0 - so, y1 + so, z_sof0, z_sof1,
               {"default": fascia_reg, "bottom": soffit_reg})
        mb.box(x0 - eave_out, x1 + eave_out, y0 - eave_out, y1 + eave_out, z_sof1, z_fas1,
               {"default": fascia_reg, "top": trim_reg})
    else:
        mb.box(x0 - eave_out, x1 + eave_out, y0 - eave_out, y1 + eave_out, z_sof0, z_fas1,
               {"default": fascia_reg, "top": trim_reg})

    # 2) 4면 모임지붕 경사면 (실스케일 S-골 기와 타일)
    ex0, ex1 = x0 - eave_out, x1 + eave_out
    ey0, ey1 = y0 - eave_out, y1 + eave_out
    ew, ed = ex1 - ex0, ey1 - ey0
    zb = z_fas1
    zp = zb + rise

    BL = (ex0, ey0, zb)
    BR = (ex1, ey0, zb)
    TR = (ex1, ey1, zb)
    TL = (ex0, ey1, zb)

    if ew >= ed:
        inset = min(ed * 0.5, ew * 0.36)
        ym = 0.5 * (ey0 + ey1)
        R0 = (ex0 + inset, ym, zp)
        R1 = (ex1 - inset, ym, zp)
        slopes = [
            [BL, BR, R1, R0],  # front (-Y)
            [TR, TL, R0, R1],  # back (+Y)
            [TL, BL, R0],      # left (-X)
            [BR, TR, R1],      # right (+X)
        ]
        hips = [(BL, R0), (TL, R0), (BR, R1), (TR, R1)]
    else:
        inset = min(ew * 0.5, ed * 0.36)
        xm = 0.5 * (ex0 + ex1)
        R0 = (xm, ey0 + inset, zp)
        R1 = (xm, ey1 - inset, zp)
        slopes = [
            [BL, BR, R0],      # front (-Y)
            [TR, TL, R1],      # back (+Y)
            [TL, BL, R0, R1],  # left (-X)
            [BR, TR, R1, R0],  # right (+X)
        ]
        hips = [(BL, R0), (BR, R0), (TL, R1), (TR, R1)]

    for poly in slopes:
        add_tiled_slope_poly(mb, poly, tile_reg, stage)

    # 3) 3D 용마루·추녀 마루 기와 + 처마 끝 막새 기와 (stage 0/1)
    if stage < 2:
        # 용마루 (R0 -> R1) + 추녀 4개 (약간 띄워 지붕 경사면과 겹침 0)
        z_off = np.array([0.0, 0.0, 0.045])
        add_beam(mb, np.asarray(R0) + z_off, np.asarray(R1) + z_off, 0.085, 0.065, trim_reg)
        for c_pt, r_pt in hips:
            c_v = np.asarray(c_pt) + np.array([0.0, 0.0, 0.035])
            r_v = np.asarray(r_pt) + np.array([0.0, 0.0, 0.040])
            add_beam(mb, c_v, r_v, 0.068, 0.052, trim_reg)

    if stage == 0:
        # 처마 끝 S-기와 막새 줄 (사진 user_ref, h07_front 핵심 실루엣 — 흰 처마 띠 바로 위 붉은 기와 끝)
        # 각 변에서 코너와 겹치지 않도록 0.14 m 안쪽부터 시작, 간격 0.28 m
        pitch_m = 0.28
        # 앞(-Y) & 뒤(+Y)
        nx = max(4, int(round((ew - 0.28) / pitch_m)))
        for i in range(nx):
            cx = ex0 + 0.14 + (i + 0.5) * (ew - 0.28) / nx
            mb.box(cx - 0.065, cx + 0.065, ey0 - 0.045, ey0 + 0.06, zb - 0.015, zb + 0.075, trim_reg)
            mb.box(cx - 0.065, cx + 0.065, ey1 - 0.06, ey1 + 0.045, zb - 0.015, zb + 0.075, trim_reg)
        # 좌(-X) & 우(+X)
        ny = max(4, int(round((ed - 0.28) / pitch_m)))
        for j in range(ny):
            cy = ey0 + 0.14 + (j + 0.5) * (ed - 0.28) / ny
            mb.box(ex0 - 0.045, ex0 + 0.06, cy - 0.065, cy + 0.065, zb - 0.015, zb + 0.075, trim_reg)
            mb.box(ex1 - 0.06, ex1 + 0.045, cy - 0.065, cy + 0.065, zb - 0.015, zb + 0.075, trim_reg)


def _world_tiled_rect(mb: K.MeshBuilder, pts, region: str):
    """월드 좌표 기준 연속 타일 UV 매핑 (개구부 좌우·상하 벽돌 줄눈 위상 단절 방지)."""
    A = mb.atlas
    if A is None or not A.is_tiled(region) or not mb.split_tiles:
        mb.rect(pts, region)
        return
    (p0x, p0y, p0z), (p1x, p1y, p1z), _p2, (p3x, p3y, p3z) = pts
    dx, dy, dz = p1x - p0x, p1y - p0y, p1z - p0z
    W = (dx * dx + dy * dy + dz * dz) ** 0.5
    gx, gy, gz = p3x - p0x, p3y - p0y, p3z - p0z
    H = (gx * gx + gy * gy + gz * gz) ** 0.5
    if W < 1e-6 or H < 1e-6:
        return
    ex, ey, ez = dx / W, dy / W, dz / W
    fx, fy, fz = gx / H, gy / H, gz / H
    u0_w = p0x * ex + p0y * ey + p0z * ez
    v0_w = p0x * fx + p0y * fy + p0z * fz
    u1_w, v1_w = u0_w + W, v0_w + H
    tw, th = A.tile_size(region)
    i0, i1 = math.floor(u0_w / tw), math.ceil(u1_w / tw)
    j0, j1 = math.floor(v0_w / th), math.ceil(v1_w / th)
    e = 0.5 / A.size
    quad = mb.quad
    for j in range(j0, j1):
        va = max(v0_w, j * th)
        vb = min(v1_w, (j + 1) * th)
        if vb - va < 1e-6:
            continue
        db0, db1 = va - v0_w, vb - v0_w
        fv0 = max(0.0, min(1.0, (va - j * th) / th))
        fv1 = max(0.0, min(1.0, (vb - j * th) / th))
        bx0, by0, bz0 = fx * db0, fy * db0, fz * db0
        bx1, by1, bz1 = fx * db1, fy * db1, fz * db1
        for i in range(i0, i1):
            ua = max(u0_w, i * tw)
            ub = min(u1_w, (i + 1) * tw)
            if ub - ua < 1e-6:
                continue
            da0, da1 = ua - u0_w, ub - u0_w
            fu0 = max(0.0, min(1.0, (ua - i * tw) / tw))
            fu1 = max(0.0, min(1.0, (ub - i * tw) / tw))
            ax0, ay0, az0 = ex * da0, ey * da0, ez * da0
            ax1, ay1, az1 = ex * da1, ey * da1, ez * da1
            q = [(p0x + ax0 + bx0, p0y + ay0 + by0, p0z + az0 + bz0),
                 (p0x + ax1 + bx0, p0y + ay1 + by0, p0z + az1 + bz0),
                 (p0x + ax1 + bx1, p0y + ay1 + by1, p0z + az1 + bz1),
                 (p0x + ax0 + bx1, p0y + ay0 + by1, p0z + az0 + bz1)]
            au0, av0, au1, av1 = A._uvrect(region, variant=(i * 7 + j * 3))
            ru0, rv0 = au0 + e, av0 + e
            du, dv = au1 - au0 - 2.0 * e, av1 - av0 - 2.0 * e
            uvs = [(ru0 + du * fu0, rv0 + dv * fv0),
                   (ru0 + du * fu1, rv0 + dv * fv0),
                   (ru0 + du * fu1, rv0 + dv * fv1),
                   (ru0 + du * fu0, rv0 + dv * fv1)]
            quad(q, uvs, region)


def _world_tiled_box(mb: K.MeshBuilder, x0, x1, y0, y1, z0, z1, region, skip=()):
    """월드 좌표 정렬 타일 UV 를 사용하는 축 정렬 박스."""
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
    for face, pts in F.items():
        if face in skip:
            continue
        reg = region if isinstance(region, str) else region.get(face, region.get("default"))
        if reg:
            _world_tiled_rect(mb, pts, reg)


def _world_tiled_axbox(mb: K.MeshBuilder, axis, c, s, a0, a1, o0, o1, z0, z1, region, skip=()):
    """K.axbox 와 동일한 좌표·skip 규칙을 따르며 월드 좌표 기준 타일 UV 적용."""
    if abs(o0) < 1e-9:
        skip = tuple(skip) + ({("y", -1): "back", ("y", 1): "front", ("x", -1): "right", ("x", 1): "left"}[(axis, s)],)
    if axis == "y":
        y0, y1 = sorted((c + s * o0, c + s * o1))
        _world_tiled_box(mb, a0, a1, y0, y1, z0, z1, region, skip)
    else:
        x0, x1 = sorted((c + s * o0, c + s * o1))
        _world_tiled_box(mb, x0, x1, a0, a1, z0, z1, region, skip)


def _add_lintel(mb, axis, c, side, a0, a1, z1, z_top, wall_reg, accent):
    """창 위 벽돌 세워쌓기 인방 (벽면 2 mm 띄움, 두께 14 mm). 벽돌 벽에만."""
    if wall_reg != "wall_main" or "brick_soldier" not in mb.atlas.cells or z1 + 0.17 > z_top:
        return
    e = 0.0 if accent else 0.05
    K.axbox(mb, axis, c, side, a0 - e, a1 + e, 0.002, 0.016, z1 + 0.004, z1 + 0.154, "brick_soldier")


def _add_door_casing(mb, axis, c, side, a0, a1, z0, z1, z_top, z_base=None, lo=None, hi=None):
    """현관·출입문 화강석 문선(양옆 최대 9 cm + 상부 인방 9 cm, 3.3 cm 돌출) + 문턱(5 cm 돌출).
    문선 폭은 벽 조각(lo..hi) 안으로 제한. 바닥에 얹히는 아래 면은 만들지 않는다."""
    zb = z0 if z_base is None else z_base
    cl = min(0.09, a0 - lo) if lo is not None else 0.09
    cr = min(0.09, hi - a1) if hi is not None else 0.09
    zt = min(z1 + 0.09, z_top - 0.01)
    ends = ("left", "right") if axis == "y" else ("front", "back")
    K.axbox(mb, axis, c, side, a0 - cl, a0, 0.002, 0.035, zb, zt, "granite", skip=("bottom",))
    K.axbox(mb, axis, c, side, a1, a1 + cr, 0.002, 0.035, zb, zt, "granite", skip=("bottom",))
    K.axbox(mb, axis, c, side, a0, a1, 0.002, 0.035, z1, zt, "granite", skip=ends)
    K.axbox(mb, axis, c, side, a0 + 0.002, a1 - 0.002, -0.013, 0.05, zb, z0 + 0.03, "granite", skip=("bottom",))


def add_recessed_wall(mb: K.MeshBuilder, wins: K.WindowSet, axis: str, c: float, side: int,
                      lo: float, hi: float, z_bot: float, z_top: float, wall_reg: str,
                      holes, stage: int, seed: int = 0, wall_t: float = 0.22,
                      sash_reg: str = "sash", reveal_reg: str = "concrete_light",
                      accent_plaster: bool = False):
    """개구부(창·문)가 실제로 0.16~0.20 m 후퇴한 외벽 조각 생성 (월드 좌표 연속 UV).

    holes: [(a0, a1, z0, z1, kind, floor, panes), ...]
      kind: 'window' | 'door_glass' | 'door_entry' | 'door_solid'
      panes: 2 또는 3 (창 유리 1장 유지, 샷시 세로/가로살은 유리 앞 3D 박스)
    """
    valid = [h for h in holes if h[0] > lo + 0.03 and h[1] < hi - 0.03 and h[2] >= z_bot - 1e-4 and h[3] <= z_top + 1e-4]
    cuts = sorted({lo, hi, *(v for h in valid for v in (h[0], h[1]))})

    # 벽체 조각 생성 (개구부 구간 비움, 월드 좌표 연속 타일 UV)
    for left, right in zip(cuts, cuts[1:]):
        if right - left < 1e-4:
            continue
        covered = sorted((h[2], h[3]) for h in valid if h[0] <= left + 1e-5 and h[1] >= right - 1e-5)
        z = z_bot
        for hz0, hz1 in covered + [(z_top, z_top)]:
            if hz0 > z + 1e-4:
                if stage == 2:
                    mb.rect(K.face_pts(axis, c, side, left, right, z, hz0), wall_reg)
                else:
                    _world_tiled_axbox(mb, axis, c, side, left, right, -wall_t, 0.0, z, hz0, wall_reg,
                                       skip=("bottom",) if z <= 0.001 else ())
            z = max(z, hz1)

    # 개구부 창호·문 생성
    for idx, (a0, a1, z0, z1, kind, floor, panes) in enumerate(valid):
        face_id = (2 if axis == "x" else 0) + (1 if side > 0 else 0)
        unit = face_id * 13 + idx * 3 + seed * 5
        fw = 0.095 if kind == "window" else 0.075  # 한국 두꺼운 흰 PVC 외틀 95 mm (STYLE_BRIEF 실측 100 mm)

        if kind in ("window", "door_glass"):
            # 규칙 21: 창 유리는 최소 분할 (2짝은 중앙 살이 정중앙을 가리지 않게 좌우 2장, 3짝/단창은 1장)
            if stage == 0:
                if panes == 2:
                    mid = 0.5 * (a0 + a1)
                    mw = 0.030
                    for g0, g1 in ((a0 + fw * 0.80, mid - mw), (mid + mw, a1 - fw * 0.80)):
                        wins.add_face(axis, c - side * 0.145, side, g0, g1,
                                      z0 + fw * 0.80, z1 - fw * 0.80, floor, unit)
                        wins.items[-1]["pts2"] = K.face_pts(axis, c + side * 0.025, side,
                                                            g0, g1, z0 + 0.05, z1 - 0.05)
                else:
                    wins.add_face(axis, c - side * 0.145, side, a0 + fw * 0.80, a1 - fw * 0.80,
                                  z0 + fw * 0.80, z1 - fw * 0.80, floor, unit)
                    wins.items[-1]["pts2"] = K.face_pts(axis, c + side * 0.025, side,
                                                        a0 + 0.05, a1 - 0.05, z0 + 0.05, z1 - 0.05)
            if stage == 2:
                mb.rect(K.face_pts(axis, c + side * 0.002, side, a0, a1, z0, z1), "window_backing")
            else:
                # 1) 두꺼운 외곽 PVC 창틀 (벽 외면 -0.135 ~ -0.015, 4변 맞대기로 겹침 0)
                o_in, o_out = -0.135, -0.015
                K.axbox(mb, axis, c, side, a0, a1, o_in, o_out, z0, z0 + fw, sash_reg,
                        skip=("bottom",) if z0 <= 0.001 else ())                                     # 하부 외틀
                K.axbox(mb, axis, c, side, a0, a1, o_in, o_out, z1 - fw, z1, sash_reg)                # 상부 외틀
                K.axbox(mb, axis, c, side, a0, a0 + fw, o_in, o_out, z0 + fw, z1 - fw, sash_reg)      # 좌측 외틀
                K.axbox(mb, axis, c, side, a1 - fw, a1, o_in, o_out, z0 + fw, z1 - fw, sash_reg)      # 우측 외틀

                # 2) 미닫이 짝 중간 세로살 (2짝=1개, 3짝=2개; 외틀 안쪽에서 맞대기)
                if panes >= 2:
                    fracs = (0.5,) if panes == 2 else (0.26, 0.74)
                    mw = 0.028
                    for f in fracs:
                        mx = a0 + fw + (a1 - a0 - 2 * fw) * f
                        K.axbox(mb, axis, c, side, mx - mw, mx + mw, -0.125, -0.045, z0 + fw, z1 - fw, sash_reg)

                # 3) 내부 이중창 샷시 단차 림 + 외곽 창대 (벽 바깥 o=0.002..0.055 로 벽·외틀과 겹침 0)
                if stage == 0:
                    if kind == "window":
                        # 화강석 창대 (벽면에서 6 cm 돌출, 양옆 5 cm 더 길게) + 벽돌 세워쌓기 인방
                        K.axbox(mb, axis, c, side, a0 - 0.05, a1 + 0.05, 0.002, 0.062, z0 - 0.06, z0 + 0.004, "granite")
                        _add_lintel(mb, axis, c, side, a0, a1, z1, z_top, wall_reg, accent_plaster)
                        if panes == 2:
                            mx = a0 + fw + (a1 - a0 - 2 * fw) * 0.5
                            K.axbox(mb, axis, c, side, a0 + fw, mx - 0.028, -0.095, -0.065,
                                    z0 + fw + 0.002, z0 + fw + 0.034, sash_reg)
                            K.axbox(mb, axis, c, side, a0 + fw, mx - 0.028, -0.095, -0.065,
                                    z1 - fw - 0.034, z1 - fw - 0.002, sash_reg)
                    else:
                        # 유리문 하부 킥플레이트(외틀 안쪽 +2mm 이격) + 중간 가로대 + 양짝 긴 스테인리스 손잡이
                        K.axbox(mb, axis, c, side, a0 + fw + 0.002, a1 - fw - 0.002, -0.115, -0.065,
                                z0 + fw + 0.002, z0 + 0.28, sash_reg)
                        mid = a0 + fw + (a1 - a0 - 2 * fw) * 0.5
                        for g0_, g1_ in ((a0 + fw, mid - 0.028), (mid + 0.028, a1 - fw)):
                            K.axbox(mb, axis, c, side, g0_ + 0.002, g1_ - 0.002, -0.118, -0.062,
                                    z0 + 0.98, z0 + 1.04, sash_reg)
                        for hx in ((mid - 0.085, mid + 0.085) if panes == 2 else (a0 + (a1 - a0) * 0.44,)):
                            K.axbox(mb, axis, c, side, hx - 0.012, hx + 0.012, -0.030, -0.008,
                                    z0 + 0.72, z0 + 1.42, "stainless")
                            for zs in (z0 + 0.78, z0 + 1.36):
                                K.axbox(mb, axis, c, side, hx - 0.008, hx + 0.008, -0.060, -0.030,
                                        zs - 0.012, zs + 0.012, "stainless")
                        _add_door_casing(mb, axis, c, side, a0, a1, z0, z1, z_top, z_bot, lo, hi)

                    # 개구부 옆면·상부 드러난 벽두께 리빌 정리
                    KX.paint_reveal(mb, axis, c, side, a0, a1, z0, z1, 0.014, reveal_reg,
                                    inset=0.002, sill=False, head=True)

                    # 2층 창 좌우 연한 미장 악센트 테두리 (창대 위 z0+0.006 부터 시작해 겹침 0)
                    if accent_plaster and kind == "window":
                        aw = 0.16
                        if a0 - aw > lo + 0.05:
                            K.axbox(mb, axis, c, side, a0 - aw, a0 - 0.002, 0.003, 0.020, z0 + 0.006, z1 + 0.04, "plaster_white")
                        if a1 + aw < hi - 0.05:
                            K.axbox(mb, axis, c, side, a1 + 0.002, a1 + aw, 0.003, 0.020, z0 + 0.006, z1 + 0.04, "plaster_white")
        elif kind in ("door_entry", "door_solid"):
            # 주택 전용 현관문(2000~2010년대 방화문): 다크 문틀 + 통짝 문(목재 필름/도장 강판) + 입체 패널 2단
            # + 디지털 도어락 + 레버 손잡이 + 경첩 3개 + 상부 트랜섬 유리 1장 + 화강석 문선·문턱
            # door_solid: 트랜섬 유리 없는 통짝 보조문(계단 밑 창고·상가 뒷문)
            efw = 0.075
            transom = kind == "door_entry"
            z_tr = z1 - 0.36 if transom else z1 - efw
            leaf_reg = "door_metal" if panes == 3 else "door_wood"   # panes 로 문짝 재질 선택 (1: 목재 필름, 3: 도장 강판)
            if stage == 0 and transom:
                wins.add_face(axis, c - side * 0.145, side, a0 + efw + 0.015, a1 - efw - 0.015,
                              z_tr + 0.055, z1 - efw, floor, unit)
                wins.items[-1]["pts2"] = K.face_pts(axis, c + side * 0.025, side,
                                                    a0 + 0.06, a1 - 0.06, z_tr + 0.04, z1 - 0.05)
            if stage == 2:
                mb.rect(K.face_pts(axis, c + side * 0.002, side, a0, a1, z0, z1), leaf_reg)
            else:
                df_reg = "sash_dark"
                o_in, o_out = -0.135, -0.015
                K.axbox(mb, axis, c, side, a0, a1, o_in, o_out, z0, z0 + efw, df_reg,
                        skip=("bottom",) if z0 <= 0.001 else ())
                K.axbox(mb, axis, c, side, a0, a1, o_in, o_out, z1 - efw, z1, df_reg)
                K.axbox(mb, axis, c, side, a0, a0 + efw, o_in, o_out, z0 + efw, z1 - efw, df_reg)
                K.axbox(mb, axis, c, side, a1 - efw, a1, o_in, o_out, z0 + efw, z1 - efw, df_reg)
                # 트랜섬 바
                if transom:
                    K.axbox(mb, axis, c, side, a0 + efw, a1 - efw, -0.130, -0.025, z_tr, z_tr + 0.055, df_reg)
                # 통짝 문 (문틀 안쪽 5 cm 후퇴)
                la, lb = a0 + efw, a1 - efw
                K.axbox(mb, axis, c, side, la, lb, -0.135, -0.068, z0 + efw, z_tr, leaf_reg)
                if stage == 0:
                    # 입체 패널 2단 (돌출 12 mm) + 패널 둘레 홈 몰딩(어두운 띠, 2 mm 앞)
                    pz = ((z0 + 0.20, z0 + 0.86), (z0 + 1.02, z_tr - 0.14))
                    for pz0, pz1 in pz:
                        K.axbox(mb, axis, c, side, la + 0.11, lb - 0.11, -0.066, -0.054, pz0, pz1, leaf_reg)
                        for m0, m1, n0, n1 in ((la + 0.085, lb - 0.085, pz0 - 0.025, pz0 - 0.012),
                                               (la + 0.085, lb - 0.085, pz1 + 0.012, pz1 + 0.025),
                                               (la + 0.085, la + 0.098, pz0 - 0.012, pz1 + 0.012),
                                               (lb - 0.098, lb - 0.085, pz0 - 0.012, pz1 + 0.012)):
                            K.axbox(mb, axis, c, side, m0, m1, -0.066, -0.060, n0, n1, "sash_dark")
                    # 디지털 도어락(본체 + 키패드 면) + 레버 손잡이(로제트 + 가로 레버) — 손잡이 쪽 = a1
                    hx = lb - 0.045
                    K.axbox(mb, axis, c, side, hx - 0.034, hx + 0.034, -0.066, -0.040, z0 + 1.06, z0 + 1.36, "iron_dark")
                    mb.quad(K.face_pts(axis, c - side * 0.035, side, hx - 0.030, hx + 0.030, z0 + 1.07, z0 + 1.35),
                            mb.atlas.uv_full("doorlock"), "doorlock")
                    K.axbox(mb, axis, c, side, hx - 0.026, hx + 0.026, -0.066, -0.054, z0 + 0.93, z0 + 1.01, "stainless")
                    K.axbox(mb, axis, c, side, hx - 0.012, hx + 0.012, -0.052, -0.026, z0 + 0.957, z0 + 0.983, "stainless")
                    K.axbox(mb, axis, c, side, hx - 0.135, hx - 0.012, -0.040, -0.022, z0 + 0.958, z0 + 0.982, "stainless")
                    # 경첩 3개 (문짝 바깥, 경첩 쪽 = a0)
                    for zh in (z0 + 0.28, z0 + 1.05, z_tr - 0.26):
                        K.axbox(mb, axis, c, side, la + 0.004, la + 0.024, -0.066, -0.050, zh, zh + 0.11, "rail_bronze")
                    KX.paint_reveal(mb, axis, c, side, a0, a1, z0, z1, 0.014, reveal_reg,
                                    inset=0.002, sill=False, head=True)
                    _add_door_casing(mb, axis, c, side, a0, a1, z0, z1, z_top, z_bot, lo, hi)


def add_railing_run(mb: K.MeshBuilder, p0_xy, p1_xy, z_base, height, stage,
                    reg="rail_bronze", post_step=1.80, picket_step=0.16,
                    skip_start_post=False, skip_end_post=False):
    """옥상 테라스 금속 세로살 난간 1구간 (기둥·상하레일·세로살 모두 맞대기 -> 겹침 면 0)."""
    x0, y0 = p0_xy
    x1, y1 = p1_xy
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    if L < 0.15:
        return
    is_x = abs(dx) >= abs(dy)
    # 정렬: 항상 작은 좌표 -> 큰 좌표
    if is_x and x0 > x1:
        x0, x1 = x1, x0
        skip_start_post, skip_end_post = skip_end_post, skip_start_post
    if not is_x and y0 > y1:
        y0, y1 = y1, y0
        skip_start_post, skip_end_post = skip_end_post, skip_start_post

    pw = 0.024          # 기둥 반폭 (전체 48 mm)
    rw = 0.020          # 상·하 레일 반폭 (전체 40 mm)
    bw = 0.010          # 세로살 반폭 (전체 20 mm)
    z_bot0, z_bot1 = z_base + 0.06, z_base + 0.10
    z_top0, z_top1 = z_base + height - 0.05, z_base + height

    if stage == 2:
        # LOD2: 상부 레일 1줄만 (초경량)
        if is_x:
            mb.box(x0, x1, y0 - rw, y0 + rw, z_top0, z_top1, reg)
        else:
            mb.box(x0 - rw, x0 + rw, y0, y1, z_top0, z_top1, reg)
        return

    # 기둥 위치 산출
    n_seg = max(1, int(round(L / post_step)))
    pts = [i / n_seg for i in range(n_seg + 1)]
    coords = [(x0 + f * (x1 - x0)) if is_x else (y0 + f * (y1 - y0)) for f in pts]

    # 기둥 (z_base ~ z_top0, 상부 핸드레일 아래에 맞대기)
    for idx, c in enumerate(coords):
        if idx == 0 and skip_start_post:
            continue
        if idx == len(coords) - 1 and skip_end_post:
            continue
        if is_x:
            mb.box(c - pw, c + pw, y0 - pw, y0 + pw, z_base, z_top0, reg)
        else:
            mb.box(x0 - pw, x0 + pw, c - pw, c + pw, z_base, z_top0, reg)

    # 연속 상부 핸드레일 (기둥 위 z_top0 ~ z_top1)
    if is_x:
        r0 = x0 + (pw if skip_start_post else -pw)
        r1 = x1 - (pw if skip_end_post else -pw)
        if r1 > r0 + 0.02:
            mb.box(r0, r1, y0 - rw, y0 + rw, z_top0, z_top1, reg)
    else:
        r0 = y0 + (pw if skip_start_post else -pw)
        r1 = y1 - (pw if skip_end_post else -pw)
        if r1 > r0 + 0.02:
            mb.box(x0 - rw, x0 + rw, r0, r1, z_top0, z_top1, reg)

    # 구간별 하부 레일 + 세로살 (기둥 사이 맞대기 -> 겹침 0)
    step = picket_step if stage == 0 else picket_step * 2.8
    for c_a, c_b in zip(coords, coords[1:]):
        s0, s1 = c_a + pw, c_b - pw
        if s1 - s0 < 0.08:
            continue
        if is_x:
            mb.box(s0, s1, y0 - rw * 0.8, y0 + rw * 0.8, z_bot0, z_bot1, reg)
            if stage == 0:
                # 상부 장식 보조 가로바 (user_ref 난간 상단 10 cm 아래 이중선)
                mb.box(s0, s1, y0 - bw, y0 + bw, z_top0 - 0.12, z_top0 - 0.095, reg)
        else:
            mb.box(x0 - rw * 0.8, x0 + rw * 0.8, s0, s1, z_bot0, z_bot1, reg)
            if stage == 0:
                mb.box(x0 - bw, x0 + bw, s0, s1, z_top0 - 0.12, z_top0 - 0.095, reg)

        n_pick = max(1, int(round((s1 - s0) / step)) - 1)
        z_p_top = (z_top0 - 0.12) if stage == 0 else z_top0
        for k in range(1, n_pick + 1):
            pc = s0 + (s1 - s0) * k / (n_pick + 1)
            if is_x:
                mb.box(pc - bw, pc + bw, y0 - bw, y0 + bw, z_bot1, z_p_top, reg)
                if stage == 0:
                    mb.box(pc - bw, pc + bw, y0 - bw, y0 + bw, z_top0 - 0.095, z_top0, reg)
            else:
                mb.box(x0 - bw, x0 + bw, pc - bw, pc + bw, z_bot1, z_p_top, reg)
                if stage == 0:
                    mb.box(x0 - bw, x0 + bw, pc - bw, pc + bw, z_top0 - 0.095, z_top0, reg)


def add_polycarb_canopy(mb: K.MeshBuilder, x0, x1, y0, y1, z_deck, z_lo, z_hi, stage,
                        poly_reg="poly_smoke", frame_reg="iron_dark", mid_y=None):
    """철골 폴리카보네이트(렉산) 테라스 차양.

    x0(바깥쪽, 낮음 z_lo) -> x1(건물쪽, 높음 z_hi) 로 완만하게 아치/경사.
    """
    if stage == 2:
        # LOD2: 지붕 1장만
        add_beam(mb, (x0, 0.5 * (y0 + y1), z_lo + 0.05),
                 (x1, 0.5 * (y0 + y1), z_hi + 0.05), 0.5 * (y1 - y0), 0.03, poly_reg)
        return

    pw = 0.035
    ym = mid_y if mid_y is not None else 0.5 * (y0 + y1)
    ys_post = [y0 + 0.16, ym, y1 - 0.16]
    # 1) 철골 기둥 (좌측 z_lo, 우측 z_hi 아래까지)
    for yp in ys_post:
        mb.box(x0 + 0.10 - pw, x0 + 0.10 + pw, yp - pw, yp + pw, z_deck, z_lo - 0.06, frame_reg)
        mb.box(x1 - 0.10 - pw, x1 - 0.10 + pw, yp - pw, yp + pw, z_deck, z_hi - 0.06, frame_reg)

    # 2) 종방향 도리 보 (좌·우 기둥 상단 연결) + 모서리 보강 가새 (stage == 0)
    mb.box(x0 + 0.10 - pw, x0 + 0.10 + pw, y0 + 0.05, y1 - 0.05, z_lo - 0.06, z_lo, frame_reg)
    mb.box(x1 - 0.10 - pw, x1 - 0.10 + pw, y0 + 0.05, y1 - 0.05, z_hi - 0.06, z_hi, frame_reg)
    if stage == 0:
        # 기둥-도리 접합부 짧은 대각 가새(까치발)로 철골 프레임 이음 보강
        for xp, zp_b in ((x0 + 0.10, z_lo - 0.06), (x1 - 0.10, z_hi - 0.06)):
            add_beam(mb, (xp, y0 + 0.16, zp_b - 0.34), (xp, y0 + 0.50, zp_b), 0.014, 0.014, frame_reg)
            add_beam(mb, (xp, y1 - 0.16, zp_b - 0.34), (xp, y1 - 0.50, zp_b), 0.014, 0.014, frame_reg)

    # 3) 3분할 완만한 곡면 아치형 폴리카보네이트 지붕판 + 횡방향 서까래
    n_seg = 3 if stage == 0 else 2
    arch = 0.20

    def roof_z(f):
        return z_lo + (z_hi - z_lo) * f + arch * 4.0 * f * (1.0 - f)

    # 횡방향 철골 서까래 (stage == 0: 5줄, stage == 1: 3줄)
    n_raf = 5 if stage == 0 else 3
    for ir in range(n_raf):
        yr = y0 + 0.10 + (y1 - y0 - 0.20) * ir / (n_raf - 1)
        for s_i in range(n_seg):
            f0, f1 = s_i / n_seg, (s_i + 1) / n_seg
            p_a = (x0 + (x1 - x0) * f0, yr, roof_z(f0) + 0.025)
            p_b = (x0 + (x1 - x0) * f1, yr, roof_z(f1) + 0.025)
            add_beam(mb, p_a, p_b, 0.022, 0.024, frame_reg)

    # 폴리카보네이트 지붕 패널 (서까래 위 +0.055 m 에 밀착, 상하 면 + 측면 닫힌 판재)
    t_poly = 0.018
    for s_i in range(n_seg):
        f0, f1 = s_i / n_seg, (s_i + 1) / n_seg
        xa, xb = x0 - 0.08 + (x1 - x0 + 0.12) * f0, x0 - 0.08 + (x1 - x0 + 0.12) * f1
        za, zb = roof_z(f0) + 0.056, roof_z(f1) + 0.056
        # 상면 (+Z)
        top_q = [(xa, y0, za + t_poly), (xb, y0, zb + t_poly),
                 (xb, y1, zb + t_poly), (xa, y1, za + t_poly)]
        add_tiled_slope_poly(mb, top_q, poly_reg, stage)
        # 하면 (-Z)
        bot_q = [(xa, y1, za), (xb, y1, zb), (xb, y0, zb), (xa, y0, za)]
        add_tiled_slope_poly(mb, bot_q, poly_reg, stage)
        # 앞(-Y) / 뒤(+Y) 마구리
        uvp = mb.atlas.uv(frame_reg)
        mb.quad([(xa, y0, za), (xb, y0, zb), (xb, y0, zb + t_poly), (xa, y0, za + t_poly)], uvp, frame_reg)
        mb.quad([(xb, y1, zb), (xa, y1, za), (xa, y1, za + t_poly), (xb, y1, zb + t_poly)], uvp, frame_reg)
        if s_i == 0:
            mb.quad([(xa, y1, za), (xa, y0, za), (xa, y0, za + t_poly), (xa, y1, za + t_poly)], uvp, frame_reg)
        if s_i == n_seg - 1:
            mb.quad([(xb, y0, zb), (xb, y1, zb), (xb, y1, zb + t_poly), (xb, y0, zb + t_poly)], uvp, frame_reg)
    if stage == 0:
        # 상면 렉산 이음 쫄대(H-바) 2줄 (아치 분할선 강조)
        for s_i in range(1, n_seg):
            f_j = s_i / n_seg
            xj = x0 - 0.08 + (x1 - x0 + 0.12) * f_j
            zj = roof_z(f_j) + 0.056 + t_poly
            mb.box(xj - 0.018, xj + 0.018, y0, y1, zj, zj + 0.014, frame_reg, skip=("bottom",))


def add_downspout(mb: K.MeshBuilder, axis: str, c: float, side: int, a_pos: float,
                  z_bot: float, z_top: float, eave_out: float = 0.0, reg: str = "pipe_white"):
    """흰색 PVC 원형(8각) 우수관 + 벽 클램프 + 지면 엘보우 (STYLE_BRIEF 5장)."""
    def pt(o, z):
        return (a_pos, c + side * o, z) if axis == "y" else (c + side * o, a_pos, z)

    r = 0.044
    o_wall = 0.065
    # 처마 돌출 시 백조목 연결
    if eave_out > 0.12:
        p_eave = pt(eave_out - 0.06, z_top)
        p_bend = pt(o_wall, z_top - 0.24)
        add_oct_tube(mb, p_eave, p_bend, r, reg, n=8)
        z_shaft_top = z_top - 0.24
    else:
        z_shaft_top = z_top

    z_elbow = z_bot + 0.18
    add_oct_tube(mb, pt(o_wall, z_elbow), pt(o_wall, z_shaft_top), r, reg, n=8)
    # 지면 배수 엘보우
    add_oct_tube(mb, pt(o_wall, z_elbow), pt(o_wall + 0.14, z_bot + 0.05), r, reg, n=8)

    # 클램프 밴드 + 브래킷
    n_clamps = max(2, int(round((z_shaft_top - z_elbow) / 1.45)))
    for k in range(n_clamps):
        zc = z_elbow + 0.35 + k * (z_shaft_top - 0.35 - (z_elbow + 0.35)) / max(1, n_clamps - 1)
        add_oct_tube(mb, pt(o_wall, zc - 0.018), pt(o_wall, zc + 0.018), r + 0.012, "iron_dark", n=8)
        K.axbox(mb, axis, c, side, a_pos - 0.015, a_pos + 0.015, 0.0, o_wall - r, zc - 0.015, zc + 0.015, "iron_dark")


def add_ac_unit(mb: K.MeshBuilder, axis: str, c: float, side: int, pos: float, z0: float, stage: int):
    """에어컨 실외기(0.82x0.32x0.58 m) + 전면 루버 + 원형 팬 링 + 브래킷 + 냉매관 덕트."""
    if stage == 2:
        return
    K.axbox(mb, axis, c, side, pos - 0.41, pos + 0.41, 0.08, 0.40, z0, z0 + 0.58, "equip_gray",
            skip=("bottom",) if z0 <= 0.005 else ())
    K.paint(mb, axis, c + side * 0.40, side, pos - 0.36, pos + 0.36, z0 + 0.05, z0 + 0.53, "louver")
    if stage == 0:
        K.axbox(mb, axis, c, side, pos - 0.42, pos + 0.42, 0.075, 0.405, z0 + 0.58, z0 + 0.605, "equip_gray")
        fc = (pos - 0.10, c + side * 0.40, z0 + 0.29) if axis == "y" else (c + side * 0.40, pos - 0.10, z0 + 0.29)
        fc2 = (fc[0] + (0.0 if axis == "y" else side * 0.025),
               fc[1] + (side * 0.025 if axis == "y" else 0.0), fc[2])
        add_oct_tube(mb, fc, fc2, 0.18, "iron_dark", n=8)
        if z0 > 0.20:
            for pp in (pos - 0.30, pos + 0.30):
                K.axbox(mb, axis, c, side, pp - 0.02, pp + 0.02, 0.01, 0.42, z0 - 0.05, z0, "iron_dark")
                K.axbox(mb, axis, c, side, pp - 0.02, pp + 0.02, 0.0, 0.04, z0 - 0.28, z0 - 0.05, "iron_dark")
        # 냉매관 커버
        K.axbox(mb, axis, c, side, pos + 0.41, pos + 0.49, 0.0, 0.07, z0 + 0.10, z0 + 0.85, "pipe_white")


def add_address_plate(mb: K.MeshBuilder, axis: str, c: float, side: int, a_mid: float, z_mid: float, stage: int):
    """도로명 건물번호판 (0.26 x 0.21 m, uv_full 전체 칸 매핑 -> 규칙 12 & 20)."""
    if stage == 2:
        return
    hw, hh = 0.135, 0.11
    t = 0.014
    skip_face = "front" if (axis == "y" and side == -1) else (
        "back" if (axis == "y" and side == 1) else ("left" if side == -1 else "right"))
    K.axbox(mb, axis, c, side, a_mid - hw, a_mid + hw, 0.0, t, z_mid - hh, z_mid + hh, "iron_dark",
            skip=(skip_face,))
    mb.quad(K.face_pts(axis, c + side * t, side, a_mid - hw, a_mid + hw, z_mid - hh, z_mid + hh),
            mb.atlas.uv_full("address"), "address")


# ---------------------------------------------------------------------------
# 유형 T2 빌더: 1층 앞 볼륨 + 옥상 테라스 + 폴리카보네이트 차양 + 2층 후퇴 모임지붕
# (SintanjinHouse01 — 기준: user_ref_detached_brown_brick.png, h07, h08, h12)
# ---------------------------------------------------------------------------
def _build_front_terrace(mb: K.MeshBuilder, wins: K.WindowSet, spec: DetachedSpec, stage: int):
    w, d = spec.width, spec.depth
    x0, x1 = -w / 2.0, w / 2.0                    # -6.50 .. +6.50
    x_split = -0.35                                # 1층 좌측 돌출 볼륨 / 우측 후퇴 경계
    x_2f0 = -2.00                                  # 2층 좌측 벽 (좌측 테라스 폭 4.50 m, 2층 폭 8.50 m)
    y_1f_r = 0.85                                  # 1층 우측 벽 후퇴선
    y_2f0 = 1.20                                   # 2층 전면 벽 후퇴선 (깊이 8.00 m)
    x_rail_end = 4.55                              # 2층 전면 발코니 난간 종료선

    zp = spec.plinth_h                             # 0.62 m
    z_slab0 = zp + spec.h1 - spec.slab_h           # 3.22 m
    z_slab1 = zp + spec.h1                         # 3.56 m (2층 바닥 / 테라스 바닥 기준)
    z_2f_top = z_slab1 + spec.h2                   # 6.26 m
    wall_t = 0.22
    t_pl = 0.025                                   # 기단 외벽 돌출 두께

    # =========================================================================
    # 0. LOD2 초경량 단순 매스 (겹침 0, ~130 tris + 창 2배 <= 260 << 500)
    # =========================================================================
    if stage == 2:
        # 1층 좌측 볼륨 (기단 + 본체 + 테라스 두겁)
        mb.box(x0, x_split, 0.0, d, 0.0, zp, "concrete_light", skip=("bottom",))
        mb.box(x0, x_split, 0.0, d, zp, z_slab1 - 0.04, "wall_main")
        mb.box(x0, x_split, 0.0, d, z_slab1 - 0.04, z_slab1,
               {"default": "plaster_white", "top": "terrace_floor"})
        # 1층 우측 후퇴부 (기단 + 본체) — x_split+0.002 부터 시작해 겹침 0
        mb.box(x_split + 0.002, x1, y_1f_r, d, 0.0, zp, "concrete_light", skip=("bottom",))
        mb.box(x_split + 0.002, x1, y_1f_r, d, zp, z_slab0, "wall_main")
        # 1층->2층 흰 슬래브 띠 (우측 발코니 캔틸레버 포함)
        mb.box(x_split + 0.002, x_rail_end, 0.0, d, z_slab0, z_slab1,
               {"default": "plaster_white", "top": "terrace_floor"})
        mb.box(x_rail_end + 0.002, x1, y_1f_r, d, z_slab0, z_slab1,
               {"default": "plaster_white", "top": "terrace_floor"})
        # 2층 본체 (z_slab1+0.002 ~ z_2f_top)
        mb.box(x_2f0, x1, y_2f0, d, z_slab1 + 0.002, z_2f_top, "wall_main")
        # 2층 모임지붕 + 처마
        add_hip_roof(mb, x_2f0, x1, y_2f0, d, z_2f_top, spec.eave_out, spec.roof_rise, stage)
        # 테라스 폴리카보네이트 차양 지붕판
        add_polycarb_canopy(mb, x0 + 0.12, x_2f0 - 0.06, 0.16, 4.90,
                            z_slab1, z_slab1 + 2.02, z_slab1 + 2.38, stage,
                            poly_reg=spec.poly_tint, frame_reg="iron_dark")
        # 뒷마당 담장
        if spec.rear_yard_d > 0.5:
            yd = d + spec.rear_yard_d
            mb.box(x0, x0 + 0.18, d + 0.02, yd - 0.18, 0.0, 1.55, "wall_main", skip=("bottom",))
            mb.box(x1 - 0.18, x1, d + 0.02, yd - 0.18, 0.0, 1.55, "wall_main", skip=("bottom",))
            mb.box(x0, x1, yd - 0.18, yd, 0.0, 1.55, "wall_main", skip=("bottom",))
        return

    # =========================================================================
    # 1. 내부 코어 (외벽 두께 wall_t 보다 2 cm 더 안쪽 -> 외벽·코어 겹침 0)
    # =========================================================================
    ci = wall_t + 0.02
    mb.box(x0 + ci, x_split - ci, ci, d - ci, 0.0, z_slab1 - 0.05, "wall_main", skip=("bottom",))
    mb.box(x_split - ci + 0.01, x1 - ci, y_1f_r + ci, d - ci, 0.0, z_slab0 - 0.01, "wall_main", skip=("bottom",))
    mb.box(x_2f0 + ci, x1 - ci, y_2f0 + ci, d - ci, z_slab1 + 0.01, z_2f_top - 0.01, "wall_main")

    # =========================================================================
    # 2. 1층 흰 콘크리트 기단 (z = 0 ~ zp, 완전 비중첩 분할, 문 아래 비움 -> 규칙 5·8)
    # =========================================================================
    # 좌측 볼륨 전면 (-Y): x0 - t_pl .. x_split + t_pl, y = -t_pl .. 0.0 (좌·우 코너 감싸기)
    mb.box(x0 - t_pl, x_split + t_pl, -t_pl, 0.0, 0.0, zp, "concrete_light", skip=("bottom",))
    # 좌측 볼륨 전면 외벽 밑 받침 (좌측 기단과 겹치지 않게 x0 + wall_t .. x_split)
    mb.box(x0 + wall_t, x_split, 0.0, wall_t, 0.0, zp, "concrete_light", skip=("bottom",))
    # 좌측 벽 (-X): 현관 개구부(y = 0.85 .. 2.55) 비움, 뒤쪽은 d - wall_t 에서 종료
    mb.box(x0 - t_pl, x0 + wall_t, 0.0, 0.85, 0.0, zp, "concrete_light", skip=("bottom",))
    mb.box(x0 - t_pl, x0 + wall_t, 2.55, d - wall_t, 0.0, zp, "concrete_light", skip=("bottom",))
    # 좌측 볼륨 우측 단차 리턴 (x_split .. x_split + t_pl, y = 0.0 .. y_1f_r - t_pl)
    mb.box(x_split, x_split + t_pl, 0.0, y_1f_r - t_pl, 0.0, zp, "concrete_light", skip=("bottom",))
    # 1층 우측 전면 (x_split .. x1 + t_pl, y = y_1f_r - t_pl .. y_1f_r + wall_t)
    mb.box(x_split, x1 + t_pl, y_1f_r - t_pl, y_1f_r + wall_t, 0.0, zp, "concrete_light", skip=("bottom",))
    # 1층 우측 벽 (+X, y = y_1f_r + wall_t .. d - wall_t)
    mb.box(x1 - wall_t, x1 + t_pl, y_1f_r + wall_t, d - wall_t, 0.0, zp, "concrete_light", skip=("bottom",))
    # 1층 뒷벽 (+Y, 양쪽 코너 감싸기 x0 - t_pl .. x1 + t_pl, y = d - wall_t .. d + t_pl)
    mb.box(x0 - t_pl, x1 + t_pl, d - wall_t, d + t_pl, 0.0, zp, "concrete_light", skip=("bottom",))

    # 좌측 현관 2단 진입 계단 (y = 0.85 .. 2.55, 1단 z=0..0.08, 2단 랜딩 z=0..0.16, 틈 0)
    mb.box(x0 - 0.42, x0 + wall_t, 0.85, 2.55, 0.0, 0.16, "concrete_light", skip=("bottom",))
    if stage < 2:
        mb.box(x0 - 0.78, x0 - 0.42, 0.85, 2.55, 0.0, 0.08, "concrete_light", skip=("bottom", "right"))

    # =========================================================================
    # 3. 1층 외벽 (좌측 앞 볼륨 z = zp ~ z_slab1-0.04, 우측 z = zp ~ z_slab0)
    # =========================================================================
    # 1층 좌측 앞 볼륨 전면 (-Y, y = 0.0): user_ref 핵심 2짝 흰 PVC 창
    h_1f_fl = [(-4.25, -2.50, zp + 0.74, zp + 2.00, "window", 0, 2)]
    add_recessed_wall(mb, wins, "y", 0.0, -1, x0, x_split, zp, z_slab1 - 0.04,
                      "wall_main", h_1f_fl, stage, spec.seed, wall_t=wall_t)

    # 1층 좌측 벽 (-X, x = x0): 현관 유리문(y = 0.90..2.50, z = 0.16..2.42) + 측면 창(y = 5.25..6.85)
    # 현관 개구부(0.90..2.50)가 lo(0.85)+0.03 .. hi(2.55)-0.03 안쪽에 들어오도록 설정
    h_1f_left = [
        (0.90, 2.50, 0.16, 2.42, "door_glass", 0, 2),
        (5.25, 6.85, zp + 0.76, zp + 2.00, "window", 0, 2),
    ]
    _world_tiled_axbox(mb, "x", x0, -1, wall_t, 0.85, -wall_t, 0.0, zp, z_slab1 - 0.04, "wall_main")
    add_recessed_wall(mb, wins, "x", x0, -1, 0.85, 2.55, 0.16, z_slab1 - 0.04,
                      "wall_main", [h_1f_left[0]], stage, spec.seed + 1, wall_t=wall_t, sash_reg="sash_dark")
    add_recessed_wall(mb, wins, "x", x0, -1, 2.55, d - wall_t, zp, z_slab1 - 0.04,
                      "wall_main", [h_1f_left[1]], stage, spec.seed + 2, wall_t=wall_t)

    # 좌측 볼륨 우측 단차 리턴 벽 (x = x_split, y = wall_t .. y_1f_r)
    mb.box(x_split - wall_t, x_split, wall_t, y_1f_r, zp, z_slab0, "wall_main")

    # 1층 우측 후퇴 전면 (-Y, y = y_1f_r, x = x_split .. x1, z = zp ~ z_slab0)
    h_1f_fr = [
        (-0.02, 1.28, zp + 0.74, zp + 2.00, "window", 0, 2),   # 중간 2짝 창
        (1.68, 3.92, zp + 0.68, zp + 2.04, "window", 0, 3),    # 거실 3짝 대형창
        (4.68, 6.08, zp + 0.74, zp + 2.00, "window", 0, 2),    # 우측 끝 2짝 창
    ]
    add_recessed_wall(mb, wins, "y", y_1f_r, -1, x_split, x1, zp, z_slab0,
                      "wall_main", h_1f_fr, stage, spec.seed + 3, wall_t=wall_t)

    # 1층 우측 벽 (+X, x = x1, y = y_1f_r + wall_t .. d - wall_t, z = zp ~ z_slab0)
    h_1f_right = [
        (2.40, 3.90, zp + 0.76, zp + 2.00, "window", 0, 2),
        (5.70, 7.10, zp + 0.76, zp + 2.00, "window", 0, 2),
    ]
    add_recessed_wall(mb, wins, "x", x1, 1, y_1f_r + wall_t, d - wall_t, zp, z_slab0,
                      "wall_main", h_1f_right, stage, spec.seed + 4, wall_t=wall_t)

    # 1층 뒷벽 (+Y, y = d, x = x0 .. x1): 전체 폭 z_slab0 까지 통일해 뒤쪽 흰 슬래브 띠가 끊김 없이 연속
    h_1f_back = [
        (-5.10, -3.60, zp + 0.76, zp + 2.00, "window", 0, 2),
        (-2.20, -1.10, zp + 0.90, zp + 1.95, "window", 0, 2),
        (0.50, 1.90, zp + 0.76, zp + 2.00, "window", 0, 2),
    ]
    add_recessed_wall(mb, wins, "y", d, 1, x0, x1, zp, z_slab0,
                      "wall_main", h_1f_back, stage, spec.seed + 5, wall_t=wall_t)

    # =========================================================================
    # 4. 1층->2층 흰 슬래브 띠 & 옥상 테라스 바닥 / 두겁 (user_ref 핵심 수평 분절!)
    # =========================================================================
    c_ov = 0.03
    # (A) 좌측 앞 볼륨 옥상 테라스 두겁 + 방수 바닥 (x0 .. x_split, y = 0 .. d - wall_t)
    #     전면(-Y)과 좌측(-X)은 고동 벽돌이 테라스 끝까지 올라가고 상단 흰 두겁(z_slab1-0.04..z_slab1+0.04) 마감
    mb.box(x0 - c_ov, x_split, -c_ov, 0.22, z_slab1 - 0.04, z_slab1 + 0.04, "plaster_white")
    mb.box(x0 - c_ov, x0 + 0.22, 0.22, d + c_ov, z_slab1 - 0.04, z_slab1 + 0.04, "plaster_white")
    #     뒷벽(+Y) 좌측 상단: 좌측 외벽(x0)에 딱 맞춰 돌출 단차 없이 뒷면 흰 슬래브 띠 연속 연결
    mb.box(x0, x_split, d - 0.22, d + c_ov, z_slab0, z_slab1 - 0.04, "plaster_white")
    mb.box(x0 + 0.22, x_2f0, d - 0.22, d + c_ov, z_slab1 - 0.04, z_slab1 + 0.04, "plaster_white")
    mb.box(x_2f0, x_split, d - 0.22, d + c_ov, z_slab1 - 0.04, z_slab1, "plaster_white")
    #     옥상 테라스 방수 바닥 + 2층 좌측 앞 발코니 바닥
    mb.box(x0 + 0.22, x_2f0, 0.22, d - 0.22, z_slab1 - 0.04, z_slab1, "terrace_floor")
    mb.box(x_2f0, x_split, 0.22, y_2f0, z_slab1 - 0.04, z_slab1, "terrace_floor")
    mb.box(x_2f0, x_split, y_2f0, d - 0.22, z_slab1 - 0.04, z_slab1, "plaster_white")

    # (B) 우측 1층 상단 대담한 흰 캔틸레버 슬래브 띠 (z_slab0 .. z_slab1 = 0.34 m)
    mb.box(x_split, x_rail_end, -c_ov, d + c_ov, z_slab0, z_slab1,
           {"default": "plaster_white", "top": "terrace_floor"})
    mb.box(x_rail_end, x1 + c_ov, y_1f_r - 0.06, d + c_ov, z_slab0, z_slab1,
           {"default": "plaster_white", "top": "terrace_floor"})
    # 우측 발코니 전면 얇은 두겁 림 (좌측 두겁 z_slab1+0.04 와 연속 높이 맞춤!)
    mb.box(x_split, x_rail_end, -c_ov, 0.22, z_slab1, z_slab1 + 0.04, "plaster_white")

    # =========================================================================
    # 5. 1층 우측 도로면 낮은 벽돌 기둥 + 검정 철제 방범 난간 (user_ref 핵심 디테일!)
    # =========================================================================
    if stage < 2:
        fy0, fy1 = 0.0, 0.18
        # 하부 콘크리트 기단 연속 (x = x_split + t_pl .. x_rail_end)
        mb.box(x_split + t_pl, x_rail_end, fy0 - 0.015, fy1, 0.0, 0.46, "concrete_light", skip=("bottom",))
        # 낮은 벽돌 하단 턱 (z = 0.46 .. 0.88) + 흰 두겁 (z = 0.88 .. 0.93)
        pier_xs = [0.68, 1.98, 3.28, 4.38]
        pw_p = 0.16
        # 벽돌 기둥 4개 + 흰 기둥 캡
        for px in pier_xs:
            mb.box(px - pw_p, px + pw_p, fy0 - 0.02, fy1 + 0.02, 0.46, 1.44, "wall_main")
            mb.box(px - pw_p - 0.025, px + pw_p + 0.025, fy0 - 0.04, fy1 + 0.04, 1.44, 1.50, "plaster_white")
        # 기둥 사이 낮은 벽돌 턱 + 검정 철제 세로 방범살
        bay_edges = [x_split + t_pl] + [px - pw_p for px in pier_xs]
        bay_ends = [px - pw_p for px in pier_xs]
        spans_f = [(x_split + t_pl, pier_xs[0] - pw_p)]
        for a_p, b_p in zip(pier_xs, pier_xs[1:]):
            spans_f.append((a_p + pw_p, b_p - pw_p))
        for sx0, sx1 in spans_f:
            if sx1 - sx0 < 0.15:
                continue
            mb.box(sx0, sx1, fy0, fy1, 0.46, 0.88, "wall_main")
            mb.box(sx0, sx1, fy0 - 0.015, fy1 + 0.015, 0.88, 0.93, "plaster_white")
            # 검정 철제 상·하 가로바 + 세로살
            mb.box(sx0, sx1, fy0 + 0.06, fy0 + 0.10, 0.96, 0.99, "iron_dark")
            mb.box(sx0, sx1, fy0 + 0.06, fy0 + 0.10, 1.34, 1.37, "iron_dark")
            if stage == 0:
                nb = max(3, int(round((sx1 - sx0) / 0.13)) - 1)
                for k in range(1, nb + 1):
                    bx = sx0 + (sx1 - sx0) * k / (nb + 1)
                    mb.box(bx - 0.009, bx + 0.009, fy0 + 0.07, fy0 + 0.09, 0.99, 1.34, "iron_dark")

    # =========================================================================
    # 6. 2층 후퇴 본체 외벽 (x = x_2f0 .. x1, y = y_2f0 .. d, z = z_slab1 .. z_2f_top)
    # =========================================================================
    # 2층 전면 (-Y, y = y_2f0): 3개 창 (좌·중 넓은 미닫이창 + 흰 미장 악센트, 우측 창)
    h_2f_front = [
        (-1.40, 0.55, z_slab1 + 0.72, z_slab1 + 2.12, "window", 1, 2),
        (1.45, 3.45, z_slab1 + 0.72, z_slab1 + 2.12, "window", 1, 2),
        (4.65, 6.00, z_slab1 + 0.76, z_slab1 + 2.08, "window", 1, 2),
    ]
    add_recessed_wall(mb, wins, "y", y_2f0, -1, x_2f0, x1, z_slab1, z_2f_top,
                      "wall_main", h_2f_front, stage, spec.seed + 10, wall_t=wall_t, accent_plaster=True)

    # 2층 좌측 벽 (-X, x = x_2f0, 테라스로 통하는 미닫이 문 + 뒷쪽 창)
    h_2f_left = [
        (2.05, 3.85, z_slab1 + 0.05, z_slab1 + 2.15, "door_glass", 1, 2),
        (5.75, 7.25, z_slab1 + 0.76, z_slab1 + 2.04, "window", 1, 2),
    ]
    l2_lo = y_2f0 + (wall_t if stage < 2 else 0.0)
    l2_hi = d - (wall_t if stage < 2 else 0.0)
    add_recessed_wall(mb, wins, "x", x_2f0, -1, l2_lo, l2_hi, z_slab1, z_2f_top,
                      "wall_main", h_2f_left, stage, spec.seed + 11, wall_t=wall_t)

    # 2층 우측 벽 (+X, x = x1)
    h_2f_right = [
        (2.55, 4.05, z_slab1 + 0.76, z_slab1 + 2.04, "window", 1, 2),
        (5.80, 7.20, z_slab1 + 0.76, z_slab1 + 2.04, "window", 1, 2),
    ]
    add_recessed_wall(mb, wins, "x", x1, 1, l2_lo, l2_hi, z_slab1, z_2f_top,
                      "wall_main", h_2f_right, stage, spec.seed + 12, wall_t=wall_t)

    # 2층 뒷벽 (+Y, y = d)
    h_2f_back = [
        (-0.80, 0.75, z_slab1 + 0.76, z_slab1 + 2.04, "window", 1, 2),
        (2.55, 4.35, z_slab1 + 0.76, z_slab1 + 2.04, "window", 1, 2),
    ]
    add_recessed_wall(mb, wins, "y", d, 1, x_2f0, x1, z_slab1, z_2f_top,
                      "wall_main", h_2f_back, stage, spec.seed + 13, wall_t=wall_t)

    # =========================================================================
    # 7. 2층 낮은 적갈색 기와 모임지붕 + 목재 소핏 + 흰 계단형 처마 띠
    # =========================================================================
    add_hip_roof(mb, x_2f0, x1, y_2f0, d, z_2f_top, spec.eave_out, spec.roof_rise, stage)

    # =========================================================================
    # 8. 옥상 테라스 금속 세로살 난간 + 철골 폴리카보네이트 차양
    # =========================================================================
    z_rail_base = z_slab1 + 0.04
    rail_h = 1.04
    # 전면 연속 난간 (x0 + 0.06 .. x_rail_end - 0.06)
    add_railing_run(mb, (x0 + 0.06, 0.06), (x_rail_end - 0.06, 0.06), z_rail_base, rail_h, stage)
    # 좌측 난간 (y = 0.06 .. d - 0.06, 앞 코너 기둥 공유)
    add_railing_run(mb, (x0 + 0.06, 0.06), (x0 + 0.06, d - 0.06), z_rail_base, rail_h, stage,
                    skip_start_post=True)
    # 뒤쪽 좌측 난간 (x = x0 + 0.06 .. x_2f0 - 0.06, 뒤 코너 기둥 공유)
    add_railing_run(mb, (x0 + 0.06, d - 0.06), (x_2f0 - 0.06, d - 0.06), z_rail_base, rail_h, stage,
                    skip_start_post=True)
    # 우측 발코니 끝 리턴 난간 (y = 0.06 .. y_2f0 - 0.04, 앞 코너 기둥 공유)
    add_railing_run(mb, (x_rail_end - 0.06, 0.06), (x_rail_end - 0.06, y_2f0 - 0.04), z_rail_base, rail_h, stage,
                    skip_start_post=True)

    # 옥상 테라스 철골 폴리카보네이트 차양 (좌측 테라스 앞쪽 절반 x0+0.12 .. x_2f0-0.06, y = 0.16 .. 4.90)
    add_polycarb_canopy(mb, x0 + 0.12, x_2f0 - 0.06, 0.16, 4.90,
                        z_slab1, z_slab1 + 2.02, z_slab1 + 2.38, stage,
                        poly_reg=spec.poly_tint, frame_reg="iron_dark", mid_y=1.78)

    # 1층 좌측 현관 비막이 폴리카보네이트 캐노피 + 벽면 고정 삼각 브래킷 (현관 세트화)
    if stage < 2:
        ey0, ey1 = 0.68, 2.72
        ex_out, ex_in = x0 - 0.92, x0
        ez_out, ez_in = 2.74, 2.98
        eq_top = [(ex_out, ey1, ez_out + 0.016), (ex_out, ey0, ez_out + 0.016),
                  (ex_in, ey0, ez_in + 0.016), (ex_in, ey1, ez_in + 0.016)]
        eq_bot = [(ex_in, ey1, ez_in), (ex_in, ey0, ez_in),
                  (ex_out, ey0, ez_out), (ex_out, ey1, ez_out)]
        add_tiled_slope_poly(mb, eq_top, spec.poly_tint, stage)
        add_tiled_slope_poly(mb, eq_bot, spec.poly_tint, stage)
        if stage == 0:
            # 외곽 엣지 바 + 서까래 3줄 + 양 끝단 삼각 지지 브래킷(까치발)
            mb.box(ex_out - 0.014, ex_out + 0.014, ey0, ey1, ez_out - 0.016, ez_out + 0.016, "iron_dark")
            for by in (ey0 + 0.08, 0.5 * (ey0 + ey1), ey1 - 0.08):
                add_beam(mb, (ex_out, by, ez_out - 0.012), (ex_in - 0.01, by, ez_in - 0.012),
                         0.015, 0.015, "iron_dark")
            for by in (ey0 + 0.08, ey1 - 0.08):
                mb.box(x0 - 0.035, x0, by - 0.018, by + 0.018, 2.48, ez_in - 0.015, "iron_dark", skip=("right",))
                zb_end = ez_out + (ez_in - ez_out) * (0.16 / (ex_in - ex_out)) - 0.015
                add_beam(mb, (x0 - 0.035, by, 2.52), (ex_out + 0.16, by, zb_end), 0.014, 0.014, "iron_dark")

    # 1층 우측 끝 창 상부 소형 암녹색 폴리카보네이트 미니 차양 + 벽면 삼각 브래킷 (user_ref 우측 끝 디테일!)
    if stage < 2:
        ax0, ax1 = 4.45, 6.25
        ay0, ay1 = 0.12, y_1f_r
        az_front, az_back = z_slab0 - 0.42, z_slab0 - 0.14
        # 경사 암녹 렉산 지붕판
        q_top = [(ax0, ay0, az_front + 0.016), (ax1, ay0, az_front + 0.016),
                 (ax1, ay1, az_back + 0.016), (ax0, ay1, az_back + 0.016)]
        q_bot = [(ax0, ay1, az_back), (ax1, ay1, az_back),
                 (ax1, ay0, az_front), (ax0, ay0, az_front)]
        add_tiled_slope_poly(mb, q_top, "poly_green", stage)
        add_tiled_slope_poly(mb, q_bot, "poly_green", stage)
        if stage == 0:
            mb.box(ax0, ax1, ay0 - 0.014, ay0 + 0.014, az_front - 0.014, az_front + 0.016, "iron_dark")
            for bx in (ax0 + 0.08, 0.5 * (ax0 + ax1), ax1 - 0.08):
                add_beam(mb, (bx, ay0, az_front - 0.012), (bx, ay1 - 0.01, az_back - 0.012),
                         0.015, 0.015, "iron_dark")
            # 양 끝 벽면 고정 삼각 브래킷(까치발, 창 폭 4.68..6.08 바깥 4.53/6.17 배치)
            for bx in (ax0 + 0.08, ax1 - 0.08):
                mb.box(bx - 0.018, bx + 0.018, ay1 - 0.035, ay1, az_front - 0.34, az_back - 0.015,
                       "iron_dark", skip=("back",))
                zb_m = az_front + (az_back - az_front) * (0.14 / (ay1 - ay0)) - 0.015
                add_beam(mb, (bx, ay1 - 0.035, az_front - 0.30), (bx, ay0 + 0.14, zb_m),
                         0.014, 0.014, "iron_dark")

    # =========================================================================
    # 9. 생활 디테일 (계량기 3연접 · CCTV 2대 · 현관 세트 · 테라스 생활물 · 배관 · 우수관 · 번지판 · 실외기)
    # =========================================================================
    if stage == 0:
        # 1층 전면 좌측: 전력·가스 계량기함 3개 연접 + 검정 전선관 (user_ref 핵심!)
        for k, mx in enumerate((-5.42, -5.14, -4.86)):
            mw = 0.105 if k > 0 else 0.09
            mh = 0.15 if k > 0 else 0.12
            mz = 1.56
            mb.box(mx - mw, mx + mw, -0.14, 0.0, mz - mh, mz + mh, "equip_gray", skip=("front",))
            mb.quad(K.face_pts("y", -0.14, -1, mx - mw, mx + mw, mz - mh, mz + mh),
                    mb.atlas.uv_full("meter_face"), "meter_face")
        # 계량기 -> 좌측 코너 -> CCTV 연결 검정 PVC 배선관
        mb.box(-6.18, -5.42, -0.045, -0.015, 1.32, 1.355, "iron_dark")
        mb.box(-6.18, -6.145, -0.045, -0.015, 1.355, 2.98, "iron_dark")
        # 1층 전면 좌측 상단 코너 CCTV 카메라 2대 (도로 양방향 감시, user_ref 디테일!)
        for cx_c, cy_c, dx_c, dy_c in ((-6.38, -0.05, -0.16, -0.14), (-6.12, -0.05, 0.18, -0.12)):
            add_beam(mb, (cx_c, cy_c, 2.96), (cx_c + dx_c, cy_c + dy_c, 2.91), 0.042, 0.038, "equip_gray")
            mb.box(cx_c - 0.025, cx_c + 0.025, -0.06, 0.0, 2.92, 3.00, "iron_dark")

        # 도로명 건물번호판 (좌측 코너 지상 1.52 m, 규칙 20)
        add_address_plate(mb, "y", 0.0, -1, -6.02, 1.52, stage)

        # 좌측 현관 세트 부속: 도어벨/인터폰 + 우편함 + 프레임 현관등
        mb.box(x0 - 0.032, x0, 0.62, 0.74, 1.32, 1.50, "iron_dark", skip=("right",))
        mb.box(x0 - 0.038, x0 - 0.032, 0.635, 0.725, 1.335, 1.485, "equip_gray", skip=("right",))
        mb.box(x0 - 0.044, x0 - 0.038, 0.665, 0.695, 1.42, 1.45, "iron_dark", skip=("right",))
        mb.box(x0 - 0.044, x0 - 0.038, 0.665, 0.695, 1.36, 1.385, "iron_dark", skip=("right",))
        # 좌측 현관 우편함 (본체 + 빗물 덮개 + 투입구 슬롯)
        mb.box(x0 - 0.11, x0, 2.68, 2.94, 1.24, 1.56, "equip_gray", skip=("right",))
        mb.box(x0 - 0.125, x0, 2.67, 2.95, 1.56, 1.585, "iron_dark", skip=("right",))
        mb.box(x0 - 0.118, x0 - 0.11, 2.71, 2.91, 1.485, 1.515, "iron_dark", skip=("right",))
        # 좌측 현관 상단 조명(하우징 + 발광 디퓨저) + 2층 테라스 벽등
        mb.box(x0 - 0.10, x0, 1.56, 1.84, 2.56, 2.72, "iron_dark", skip=("right",))
        mb.box(x0 - 0.115, x0 - 0.03, 1.59, 1.81, 2.58, 2.69, "lamp", skip=("right",))
        mb.box(x_2f0 - 0.10, x_2f0, 4.12, 4.34, z_slab1 + 2.08, z_slab1 + 2.24, "iron_dark", skip=("right",))
        mb.box(x_2f0 - 0.115, x_2f0 - 0.03, 4.15, 4.31, z_slab1 + 2.10, z_slab1 + 2.21, "lamp", skip=("right",))

        # 2층 옥상 테라스 경량 생활 디테일: 스테인리스 빨래대 + 배수구 + 벽 수도꼭지
        # (화분·화분대는 2026-11-24 사용자 요청으로 모델링에서 완전히 제외)
        # (2) 접이식 스테인리스 빨래 건조대 (햇빛 드는 개방 테라스 x=-4.60..-3.30, y=5.65..6.40)
        rx0, rx1, ry0, ry1 = -4.60, -3.30, 5.65, 6.40
        z_rack = z_slab1 + 0.96
        for lx in (rx0 + 0.08, rx1 - 0.08):
            add_beam(mb, (lx, ry0 + 0.06, z_slab1 + 0.01), (lx, ry1 - 0.06, z_rack), 0.012, 0.012, "stainless")
            add_beam(mb, (lx, ry1 - 0.06, z_slab1 + 0.01), (lx, ry0 + 0.06, z_rack), 0.012, 0.012, "stainless")
        mb.box(rx0, rx1, ry0, ry0 + 0.024, z_rack, z_rack + 0.024, "stainless")
        mb.box(rx0, rx1, ry1 - 0.024, ry1, z_rack, z_rack + 0.024, "stainless")
        for k in range(5):
            ry_bar = ry0 + 0.12 + k * (ry1 - ry0 - 0.24) / 4.0
            mb.box(rx0 + 0.02, rx1 - 0.02, ry_bar - 0.008, ry_bar + 0.008, z_rack + 0.004, z_rack + 0.020, "stainless")
        # (3) 바닥 배수구 그레이팅 (x=-5.95..-5.65, y=7.50..7.80)
        mb.box(-5.95, -5.65, 7.50, 7.80, z_slab1, z_slab1 + 0.012, "iron_dark", skip=("bottom",))
        mb.box(-5.91, -5.69, 7.54, 7.76, z_slab1 + 0.012, z_slab1 + 0.018, "stainless", skip=("bottom",))
        # (4) 2층 좌측 벽 물청소용 수도꼭지 + 호스 걸이 (x=x_2f0, y=4.95, z=z_slab1+0.55)
        mb.box(x_2f0 - 0.04, x_2f0, 4.91, 4.99, z_slab1 + 0.51, z_slab1 + 0.59, "iron_dark", skip=("right",))
        mb.box(x_2f0 - 0.16, x_2f0 - 0.04, 4.935, 4.965, z_slab1 + 0.535, z_slab1 + 0.565, "stainless", skip=("right",))
        mb.box(x_2f0 - 0.16, x_2f0 - 0.13, 4.935, 4.965, z_slab1 + 0.47, z_slab1 + 0.535, "stainless", skip=("top",))
        mb.box(x_2f0 - 0.11, x_2f0, 4.70, 4.82, z_slab1 + 0.72, z_slab1 + 0.84, "iron_dark", skip=("right",))

        # 흰색 원형 PVC 우수관 (전면 단차 코너 짧은 배수관 + 2층 우측/뒷쪽 모서리 우수관)
        add_downspout(mb, "y", 0.0, -1, x_split - 0.14, 0.02, 0.78, eave_out=0.0)
        add_downspout(mb, "x", x1, 1, y_2f0 + 0.25, 0.02, z_2f_top - 0.02, eave_out=spec.eave_out)
        add_downspout(mb, "y", d, 1, x1 - 0.30, 0.02, z_2f_top - 0.02, eave_out=spec.eave_out)

    # 에어컨 실외기 (좌측 테라스 뒤쪽 구석 + 1층 뒷벽)
    add_ac_unit(mb, "x", x_2f0, -1, 7.95, z_slab1 + 0.02, stage)
    add_ac_unit(mb, "y", d, 1, 2.55, 1.65, stage)

    # =========================================================================
    # 10. 뒷마당 벽돌 담장 (2x3 로트 균형, z=0 skip bottom, 모서리 갓돌 감싸기)
    # =========================================================================
    if spec.rear_yard_d > 0.5:
        yd = d + spec.rear_yard_d
        fh = 1.55
        ft = 0.18
        # 좌·우·뒤 벽돌 담장 (건물 뒷벽 y=d 에 맞대기, 코너 겹침 0)
        mb.box(x0, x0 + ft, d + t_pl, yd - ft, 0.0, fh, "wall_main", skip=("bottom",))
        mb.box(x1 - ft, x1, d + t_pl, yd - ft, 0.0, fh, "wall_main", skip=("bottom",))
        mb.box(x0, x1, yd - ft, yd, 0.0, fh, "wall_main", skip=("bottom",))
        if stage < 2:
            # 흰 콘크리트 담장 갓돌 (뒷담이 모서리 감싸고 좌우담이 맞대기)
            mb.box(x0 - 0.03, x1 + 0.03, yd - ft - 0.03, yd + 0.03, fh, fh + 0.06, "concrete_light")
            mb.box(x0 - 0.03, x0 + ft + 0.03, d + t_pl, yd - ft - 0.03, fh, fh + 0.06, "concrete_light")
            mb.box(x1 - ft - 0.03, x1 + 0.03, d + t_pl, yd - ft - 0.03, fh, fh + 0.06, "concrete_light")


# ---------------------------------------------------------------------------
# 유형 T1 빌더: 2층 벽돌 모임지붕 마당형 (SintanjinHouse02)
# 근거: work/roadview_extra/d02_*.png (석봉동 2층 벽돌 단독, SOURCES.md), STYLE_BRIEF 6.3
# 좁은 전면 벽돌 발코니 + 흰 두겁 + 장식 블록, 현관 차양, 앞마당 벽돌 담장·철제 세로살·대문
# ---------------------------------------------------------------------------
def _fence_span(mb, s0, s1, fy0, fy1, stage):
    """기둥 사이 낮은 벽돌 턱 + 흰 갓돌 + 검정 철제 세로살 (d02_brick_fence, d02_front_balcony)."""
    if s1 - s0 < 0.15:
        return
    mb.box(s0, s1, fy0, fy1, 0.0, 0.70, "wall_main", skip=("bottom",))
    mb.box(s0, s1, fy0 - 0.03, fy1 + 0.03, 0.70, 0.76, "plaster_white")
    ym = 0.5 * (fy0 + fy1)
    mb.box(s0, s1, ym - 0.02, ym + 0.02, 0.86, 0.89, "iron_dark")
    mb.box(s0, s1, ym - 0.02, ym + 0.02, 1.38, 1.41, "iron_dark")
    nb = max(2, int(round((s1 - s0) / (0.13 if stage == 0 else 0.36))) - 1)
    for k in range(1, nb + 1):
        bx = s0 + (s1 - s0) * k / (nb + 1)
        mb.box(bx - 0.009, bx + 0.009, ym - 0.009, ym + 0.009, 0.76, 1.47, "iron_dark", skip=("bottom",))


def _fence_pier(mb, cx, fy0, fy1, h=1.55, cap=True):
    """벽돌 담장 기둥(0.40 m 각) + 콘크리트 캡 (d02_brick_fence)."""
    mb.box(cx - 0.20, cx + 0.20, fy0 - 0.10, fy1 + 0.10, 0.0, h, "wall_main", skip=("bottom",))
    if cap:
        mb.box(cx - 0.24, cx + 0.24, fy0 - 0.14, fy1 + 0.14, h, h + 0.07, "concrete_light")


def _build_iron_gate(mb, g0, g1, fy0, fy1, stage):
    """철제 대문 2짝 (하부 프레스 강판 + 상부 세로살·마름모 장식 + 손잡이·자물쇠함·경첩, 중앙 2 cm 틈)."""
    gm = 0.5 * (g0 + g1)
    gy0, gy1 = 0.5 * (fy0 + fy1) - 0.03, 0.5 * (fy0 + fy1) + 0.03
    for leaf_idx, (la, lb) in enumerate(((g0 + 0.01, gm - 0.01), (gm + 0.01, g1 - 0.01))):
        if stage == 0:
            # 하부 프레스 강판: 옆·위 면은 철재, 앞·뒤 면은 돌출 패널 무늬 칸 전체 UV
            mb.box(la, lb, gy0, gy1, 0.06, 1.30, "iron_dark", skip=("front", "back"))
            mb.quad(K.face_pts("y", gy0, -1, la, lb, 0.06, 1.30), mb.atlas.uv_full("gate_plate"), "gate_plate")
            mb.quad(K.face_pts("y", gy1, 1, la, lb, 0.06, 1.30), mb.atlas.uv_full("gate_plate"), "gate_plate")
            # 상단 장식: 가로 띠 2줄 사이 원형 고리 대신 짧은 마름모 살 (철제 대문 상단 장식, 단순화)
            for k in range(3):
                cxo = la + (lb - la) * (k + 0.5) / 3.0
                add_beam(mb, (cxo - 0.10, 0.5 * (gy0 + gy1), 1.70), (cxo, 0.5 * (gy0 + gy1), 1.82), 0.008, 0.008, "iron_dark")
                add_beam(mb, (cxo, 0.5 * (gy0 + gy1), 1.82), (cxo + 0.10, 0.5 * (gy0 + gy1), 1.70), 0.008, 0.008, "iron_dark")
            mb.box(la + 0.05, lb - 0.05, gy0 + 0.015, gy1 - 0.015, 1.66, 1.69, "iron_dark")
        else:
            mb.box(la, lb, gy0, gy1, 0.06, 1.30, "iron_dark")
        mb.box(la, lb, gy0, gy1, 1.86, 1.92, "iron_dark")
        mb.box(la, la + 0.05, gy0, gy1, 1.30, 1.86, "iron_dark")
        mb.box(lb - 0.05, lb, gy0, gy1, 1.30, 1.86, "iron_dark")
        if stage == 0:
            nb = 6
            for k in range(1, nb + 1):
                bx = la + 0.05 + (lb - la - 0.10) * k / (nb + 1)
                mb.box(bx - 0.01, bx + 0.01, gy0 + 0.02, gy1 - 0.02, 1.30, 1.86, "iron_dark")
            # 하부 강판 보강 띠 + 외곽 프레임 몰딩 (평면감 해소)
            mb.box(la + 0.06, lb - 0.06, gy0 - 0.018, gy0, 0.64, 0.69, "iron_dark", skip=("back",))
            # 경첩 2개 (바깥쪽 기둥-문짝 사이 핀 배럴, 기둥·문짝 면과 비겹침)
            hx0_h, hx1_h = (g0 + 0.002, g0 + 0.036) if leaf_idx == 0 else (g1 - 0.036, g1 - 0.002)
            for zh in (0.32, 1.54):
                mb.box(hx0_h, hx1_h, gy0 - 0.016, gy1 + 0.016, zh, zh + 0.10, "rail_bronze")
            # 문고리 (양 짝 중앙 측 스테인리스 수직 손잡이)
            hx_pull = (lb - 0.13) if leaf_idx == 0 else (la + 0.11)
            mb.box(hx_pull, hx_pull + 0.024, gy0 - 0.048, gy0 - 0.024, 0.92, 1.14, "stainless")
            mb.box(hx_pull, hx_pull + 0.024, gy0 - 0.024, gy0, 0.92, 0.95, "stainless", skip=("back",))
            mb.box(hx_pull, hx_pull + 0.024, gy0 - 0.024, gy0, 1.11, 1.14, "stainless", skip=("back",))
            # 자물쇠함 (우측 문짝 내측) + 열쇠구멍 실린더
            if leaf_idx == 1:
                mb.box(la + 0.01, la + 0.09, gy0 - 0.022, gy1 + 0.022, 0.95, 1.15, "sash_dark")
                mb.box(la + 0.035, la + 0.065, gy0 - 0.030, gy0 - 0.022, 1.02, 1.06, "stainless", skip=("back",))


def _build_standard_2f(mb: K.MeshBuilder, wins: K.WindowSet, spec: DetachedSpec, stage: int):
    w, d = spec.width, spec.depth
    x0, x1 = -w / 2.0, w / 2.0                    # -5.10 .. +5.10
    zp = spec.plinth_h                             # 0.40
    z_slab1 = zp + spec.h1                         # 3.30 (2층 바닥)
    z_slab0 = z_slab1 - spec.slab_h                # 2.98
    z_top = z_slab1 + spec.h2                      # 6.00
    wall_t, t_pl, c_ov = 0.22, 0.025, 0.03

    # 좁은 전면 발코니 (d02_front_balcony: 2층 중앙, 벽돌 막힌 난간 + 흰 두겁 + 장식 블록)
    b0, b1, by0 = -1.90, 2.90, -0.90               # estimated: 폭 4.8 m, 돌출 0.9 m
    pt = 0.18
    z_pt = z_slab1 + 0.95

    # 앞마당 담장 (lot 16x16 m 안, bbox 15.3 m -> 중앙 정렬 시 경계 안)
    fy0, fy1 = -4.40, -4.20                        # 앞 담장 몸체 (도로면 y=-4.40, 앞마당 4.2 m)
    sx = 7.60                                      # 좌우 담장 바깥선
    ry0, ry1 = 10.60, 10.80                        # 뒷담 (뒷창 앞 1.6 m 확보 -> WIN_BLOCKED 0)
    g0, g1 = -4.55, -2.15                          # 대문 개구부 2.4 m
    gp = 0.40                                      # 대문 기둥 폭
    gh = 2.25                                      # 대문 기둥 높이

    if stage == 2:
        mb.box(x0 - t_pl, x1 + t_pl, -t_pl, d + t_pl, 0.0, zp, "concrete_light", skip=("bottom",))
        mb.box(x0, x1, 0.0, d, zp, z_slab0, "wall_main", skip=("bottom",))
        mb.box(x0 - c_ov, x1 + c_ov, -c_ov, d + c_ov, z_slab0, z_slab1, "plaster_white")
        mb.box(x0, x1, 0.0, d, z_slab1, z_top, "wall_main", skip=("bottom",))
        mb.box(b0, b1, by0, -c_ov, z_slab0, z_pt, "wall_main")
        add_hip_roof(mb, x0, x1, 0.0, d, z_top, spec.eave_out, spec.roof_rise, stage)
        mb.box(-sx, g0 - gp, fy0, fy1, 0.0, 1.45, "wall_main", skip=("bottom",))
        mb.box(g1 + gp, sx, fy0, fy1, 0.0, 1.45, "wall_main", skip=("bottom",))
        mb.box(g0 - gp, g0, fy0 - 0.10, fy1 + 0.10, 0.0, gh, "wall_main", skip=("bottom",))
        mb.box(g1, g1 + gp, fy0 - 0.10, fy1 + 0.10, 0.0, gh, "wall_main", skip=("bottom",))
        mb.box(g0 - gp - 0.10, g1 + gp + 0.10, fy0 - 0.35, fy1 + 0.35, gh, gh + 0.15, "plaster_white")
        mb.box(-sx, -sx + 0.20, fy1, ry0, 0.0, 1.55, "wall_main", skip=("bottom",))
        mb.box(sx - 0.20, sx, fy1, ry0, 0.0, 1.55, "wall_main", skip=("bottom",))
        mb.box(-sx, sx, ry0, ry1, 0.0, 1.55, "wall_main", skip=("bottom",))
        return

    # 1. 기단(통 블록) + 내부 코어 (외벽보다 2 cm 안쪽 -> 겹침 0)
    mb.box(x0 - t_pl, x1 + t_pl, -t_pl, d + t_pl, 0.0, zp, "concrete_light", skip=("bottom",))
    ci = wall_t + 0.02
    mb.box(x0 + ci, x1 - ci, ci, d - ci, zp, z_slab0 - 0.01, "wall_main", skip=("bottom",))
    mb.box(x0 + ci, x1 - ci, ci, d - ci, z_slab1 + 0.01, z_top - 0.01, "wall_main")

    # 2. 1층 외벽 (z = zp .. z_slab0)
    h1f_front = [
        (-4.05, -3.05, zp, zp + 2.10, "door_entry", 0, 1),       # 주택 전용 현관문 (다크 프레임 + 하부 패널 + 트랜섬)
        (-2.20, 0.60, zp + 0.62, zp + 2.06, "window", 0, 3),     # 거실 3짝 (d02_front_balcony 1층 대형창)
        (1.40, 3.00, zp + 0.78, zp + 2.02, "window", 0, 2),
        (3.70, 4.60, zp + 1.30, zp + 2.02, "window", 0, 2),      # 욕실 소창
    ]
    add_recessed_wall(mb, wins, "y", 0.0, -1, x0, x1, zp, z_slab0, "wall_main",
                      h1f_front, stage, spec.seed, wall_t=wall_t)
    h1f_back = [
        (-4.20, -2.70, zp + 0.78, zp + 2.02, "window", 0, 2),
        (-1.40, -0.40, zp + 1.20, zp + 2.00, "window", 0, 2),
        (0.80, 2.60, zp + 0.78, zp + 2.02, "window", 0, 2),
        (3.40, 4.40, zp + 1.20, zp + 2.00, "window", 0, 2),
    ]
    add_recessed_wall(mb, wins, "y", d, 1, x0, x1, zp, z_slab0, "wall_main",
                      h1f_back, stage, spec.seed + 1, wall_t=wall_t)
    add_recessed_wall(mb, wins, "x", x0, -1, wall_t, d - wall_t, zp, z_slab0, "wall_main",
                      [(1.60, 3.10, zp + 0.78, zp + 2.02, "window", 0, 2),
                       (5.60, 7.10, zp + 0.78, zp + 2.02, "window", 0, 2)],
                      stage, spec.seed + 2, wall_t=wall_t)
    add_recessed_wall(mb, wins, "x", x1, 1, wall_t, d - wall_t, zp, z_slab0, "wall_main",
                      [(1.40, 2.60, zp + 1.10, zp + 2.00, "window", 0, 2),
                       (5.20, 6.90, zp + 0.78, zp + 2.02, "window", 0, 2)],
                      stage, spec.seed + 3, wall_t=wall_t)

    # 3. 흰 슬래브 띠 (모서리 감싸는 한 덩어리) + 발코니 바닥 슬래브
    mb.box(x0 - c_ov, x1 + c_ov, -c_ov, d + c_ov, z_slab0, z_slab1, "plaster_white")
    mb.box(b0, b1, by0, -c_ov, z_slab0, z_slab1,
           {"default": "plaster_white", "top": "terrace_floor"}, skip=("back",))

    # 4. 2층 외벽 (z = z_slab1 .. z_top)
    h2f_front = [
        (-4.20, -2.80, z_slab1 + 0.80, z_slab1 + 2.04, "window", 1, 2),
        (-1.30, 0.20, z_slab1 + 0.80, z_slab1 + 2.04, "window", 1, 2),   # 난간 위 창 (d02_front_balcony)
        (0.70, 2.40, z_slab1 + 0.80, z_slab1 + 2.04, "window", 1, 2),
        (3.50, 4.60, z_slab1 + 0.80, z_slab1 + 2.04, "window", 1, 2),
    ]
    add_recessed_wall(mb, wins, "y", 0.0, -1, x0, x1, z_slab1, z_top, "wall_main",
                      h2f_front, stage, spec.seed + 10, wall_t=wall_t)
    add_recessed_wall(mb, wins, "y", d, 1, x0, x1, z_slab1, z_top, "wall_main",
                      [(-3.90, -2.40, z_slab1 + 0.80, z_slab1 + 2.04, "window", 1, 2),
                       (-0.80, 0.60, z_slab1 + 1.20, z_slab1 + 2.00, "window", 1, 2),
                       (1.80, 3.60, z_slab1 + 0.80, z_slab1 + 2.04, "window", 1, 2)],
                      stage, spec.seed + 11, wall_t=wall_t)
    for side, xc, sd in ((-1, x0, 12), (1, x1, 13)):
        add_recessed_wall(mb, wins, "x", xc, side, wall_t, d - wall_t, z_slab1, z_top, "wall_main",
                          [(1.80, 3.30, z_slab1 + 0.80, z_slab1 + 2.04, "window", 1, 2),
                           (5.60, 7.10, z_slab1 + 0.80, z_slab1 + 2.04, "window", 1, 2)],
                          stage, spec.seed + sd, wall_t=wall_t)

    # 5. 낮은 적갈 기와 모임지붕 + 목재 소핏 + 흰 처마 띠 (d02_mass_hip_roof, d02_street_awning)
    add_hip_roof(mb, x0, x1, 0.0, d, z_top, spec.eave_out, spec.roof_rise, stage)

    # 6. 좁은 전면 발코니: 벽돌 막힌 난간(월드 UV 정렬) + 장식 블록 개구부 + 어두운 깊이 그림자 + 흰 두겁
    lc0, lc1 = 0.10, 0.90                           # 장식 블록 0.8 x 0.5 m (estimated)
    lz0, lz1 = z_slab1 + 0.30, z_slab1 + 0.80
    fy_a, fy_b = by0, by0 + pt
    _world_tiled_box(mb, b0, lc0, fy_a, fy_b, z_slab1, z_pt, "wall_main", skip=("bottom",))
    _world_tiled_box(mb, lc1, b1, fy_a, fy_b, z_slab1, z_pt, "wall_main", skip=("bottom",))
    _world_tiled_box(mb, lc0, lc1, fy_a, fy_b, z_slab1, lz0, "wall_main", skip=("bottom",))
    _world_tiled_box(mb, lc0, lc1, fy_a, fy_b, lz1, z_pt, "wall_main")
    _world_tiled_box(mb, b0, b0 + pt, fy_b, 0.0, z_slab1, z_pt, "wall_main", skip=("bottom", "back", "front"))
    _world_tiled_box(mb, b1 - pt, b1, fy_b, 0.0, z_slab1, z_pt, "wall_main", skip=("bottom", "back", "front"))
    mb.box(b0 - 0.03, b1 + 0.03, fy_a - 0.03, fy_b + 0.03, z_pt, z_pt + 0.06, "plaster_white")
    mb.box(b0 - 0.03, b0 + pt + 0.03, fy_b + 0.03, 0.0, z_pt, z_pt + 0.06, "plaster_white", skip=("back",))
    mb.box(b1 - pt - 0.03, b1 + 0.03, fy_b + 0.03, 0.0, z_pt, z_pt + 0.06, "plaster_white", skip=("back",))
    ly0, ly1 = fy_a + 0.04, fy_b - 0.04
    if stage == 0:
        # 장식 블록 뒷면 어두운 그림자 깊이판 (투시 개구부 입체감 강조, 격자와 8 mm 이격)
        mb.box(lc0 + 0.002, lc1 - 0.002, ly1 + 0.008, fy_b - 0.004, lz0 + 0.002, lz1 - 0.002, "shadow_recess")
        # 흰 콘크리트 장식 블록 격자: 외곽틀·십자(맞대기) + 좌우 사각 고리(얇게 다른 깊이 -> 겹침 0)
        bw, zm, xm = 0.05, 0.5 * (lz0 + lz1), 0.5 * (lc0 + lc1)
        mb.box(lc0, lc1, ly0, ly1, lz0, lz0 + bw, "plaster_white")
        mb.box(lc0, lc1, ly0, ly1, lz1 - bw, lz1, "plaster_white")
        mb.box(lc0, lc0 + bw, ly0, ly1, lz0 + bw, lz1 - bw, "plaster_white")
        mb.box(lc1 - bw, lc1, ly0, ly1, lz0 + bw, lz1 - bw, "plaster_white")
        mb.box(xm - 0.025, xm + 0.025, ly0, ly1, lz0 + bw, lz1 - bw, "plaster_white")
        mb.box(lc0 + bw, xm - 0.025, ly0, ly1, zm - 0.025, zm + 0.025, "plaster_white")
        mb.box(xm + 0.025, lc1 - bw, ly0, ly1, zm - 0.025, zm + 0.025, "plaster_white")
        ra, rb = ly0 + 0.015, ly1 - 0.015
        for qx in (lc0 + 0.20, lc1 - 0.20):
            mb.box(qx - 0.10, qx + 0.10, ra, rb, zm + 0.07, zm + 0.10, "plaster_white")
            mb.box(qx - 0.10, qx + 0.10, ra, rb, zm - 0.10, zm - 0.07, "plaster_white")
            mb.box(qx - 0.10, qx - 0.07, ra, rb, zm - 0.07, zm + 0.07, "plaster_white")
            mb.box(qx + 0.07, qx + 0.10, ra, rb, zm - 0.07, zm + 0.07, "plaster_white")
    else:
        mb.box(lc0, lc1, ly0, ly1, lz0, lz1, "plaster_white")

    # 7. 현관: 2단 콘크리트 계단(틈 0, 기단에 맞대기) + 암녹 폴리카보네이트 차양 + 벽면 삼각 브래킷
    sx0, sx1 = -4.30, -2.80
    mb.box(sx0, sx1, -0.80, -t_pl, 0.0, 0.20, "concrete_light", skip=("bottom", "back"))
    mb.box(sx0, sx1, -0.42, -t_pl, 0.20, zp, "concrete_light", skip=("bottom", "back"))
    ax0, ax1, ay0 = -4.45, -2.65, -1.05
    az_f, az_b = 2.60, 2.84
    add_tiled_slope_poly(mb, [(ax0, ay0, az_f + 0.016), (ax1, ay0, az_f + 0.016),
                              (ax1, 0.0, az_b + 0.016), (ax0, 0.0, az_b + 0.016)], spec.poly_tint, stage)
    add_tiled_slope_poly(mb, [(ax0, 0.0, az_b), (ax1, 0.0, az_b),
                              (ax1, ay0, az_f), (ax0, ay0, az_f)], spec.poly_tint, stage)
    if stage == 0:
        mb.box(ax0, ax1, ay0 - 0.014, ay0 + 0.014, az_f - 0.014, az_f + 0.016, "iron_dark")
        for bx in (ax0 + 0.08, 0.5 * (ax0 + ax1), ax1 - 0.08):
            add_beam(mb, (bx, ay0, az_f - 0.012), (bx, -0.02, az_b - 0.012), 0.015, 0.015, "iron_dark")
        # 양 끝단 벽면 고정 삼각 브래킷(까치발, 현관문 -4.05..-3.05 바깥 -4.37/-2.73 배치)
        for bx in (ax0 + 0.08, ax1 - 0.08):
            mb.box(bx - 0.018, bx + 0.018, -0.035, 0.0, az_f - 0.44, az_b - 0.015, "iron_dark", skip=("back",))
            zb_e = az_f + (az_b - az_f) * (0.18 / abs(ay0)) - 0.015
            add_beam(mb, (bx, -0.035, az_f - 0.40), (bx, ay0 + 0.18, zb_e), 0.015, 0.015, "iron_dark")
        # 현관등(프레임 + 발광 디퓨저) + 현관 초인종/인터폰
        K.axbox(mb, "y", 0.0, -1, -3.68, -3.42, 0.0, 0.09, 2.62, 2.77, "iron_dark")
        K.axbox(mb, "y", 0.0, -1, -3.65, -3.45, 0.02, 0.105, 2.64, 2.74, "lamp")
        K.axbox(mb, "y", 0.0, -1, -2.90, -2.79, 0.0, 0.030, zp + 1.16, zp + 1.33, "iron_dark")
        K.axbox(mb, "y", 0.0, -1, -2.885, -2.805, 0.030, 0.036, zp + 1.175, zp + 1.315, "equip_gray")

    # 8. 앞마당 담장 + 대문 (d02_brick_fence, d02_front_balcony, d02_gate_balcony_up)
    # 왼쪽 구간: 모서리 기둥 + 중간 기둥 + 대문 기둥
    for cx in (-sx + 0.20, -6.20):
        _fence_pier(mb, cx, fy0, fy1)
    _fence_span(mb, -sx + 0.40, -6.40, fy0, fy1, stage)
    _fence_span(mb, -6.00, g0 - gp, fy0, fy1, stage)
    # 대문 기둥 2개 + 흰 콘크리트 대문 지붕 슬래브 (위 칠 없는 평 슬래브)
    _fence_pier(mb, g0 - gp / 2, fy0, fy1, h=gh, cap=False)
    _fence_pier(mb, g1 + gp / 2, fy0, fy1, h=gh, cap=False)
    mb.box(g0 - gp - 0.10, g1 + gp + 0.10, fy0 - 0.35, fy1 + 0.35, gh, gh + 0.15, "plaster_white")
    _build_iron_gate(mb, g0, g1, fy0, fy1, stage)
    gm = 0.5 * (g0 + g1)
    # 대문 오른쪽 막힌 벽돌 벽 (계량기·우편함 부착, d02_gate_meter) + 갓돌
    wr0, wr1 = g1 + gp, -0.55
    mb.box(wr0, wr1, fy0, fy1, 0.0, 1.55, "wall_main", skip=("bottom",))
    mb.box(wr0, wr1 - 0.04, fy0 - 0.03, fy1 + 0.03, 1.55, 1.61, "concrete_light")  # 옆 기둥 캡(-0.59)과 맞대기
    # 오른쪽 구간 기둥 + 살 담장
    piers_r = [-0.35, 1.75, 3.65, 5.55, sx - 0.20]
    for cx in piers_r:
        _fence_pier(mb, cx, fy0, fy1)
    for a_p, b_p in zip(piers_r, piers_r[1:]):
        _fence_span(mb, a_p + 0.20, b_p - 0.20, fy0, fy1, stage)
    # 좌·우·뒤 벽돌 담장 (높이 1.55, 갓돌은 기둥 캡과 맞대기)
    for s0_, s1_ in ((-sx, -sx + 0.20), (sx - 0.20, sx)):
        mb.box(s0_, s1_, fy1 + 0.10, ry0, 0.0, 1.55, "wall_main", skip=("bottom",))
        mb.box(s0_ - 0.03, s1_ + 0.03, fy1 + 0.14, ry0 - 0.03, 1.55, 1.61, "concrete_light")
    mb.box(-sx, sx, ry0, ry1, 0.0, 1.55, "wall_main", skip=("bottom",))
    mb.box(-sx - 0.03, sx + 0.03, ry0 - 0.03, ry1 + 0.03, 1.55, 1.61, "concrete_light")

    # 9. 생활 디테일 (계량기 2개·우편함 슬롯·번지판·대문등 보강·우수관·실외기)
    if stage == 0:
        for mx in (-1.62, -1.36):
            mb.box(mx - 0.10, mx + 0.10, fy0 - 0.14, fy0, 1.12, 1.42, "equip_gray", skip=("front", "back"))
            mb.quad(K.face_pts("y", fy0 - 0.14, -1, mx - 0.10, mx + 0.10, 1.12, 1.42),
                    mb.atlas.uv_full("meter_face"), "meter_face")
        mb.box(-1.60, -1.40, fy0 - 0.05, fy0, 0.30, 1.12, "iron_dark", skip=("back",))   # 전선관
        # 우편함 (본체 + 빗물 덮개 + 투입구 슬롯 + 금속 플랩)
        mb.box(-0.98, -0.72, fy0 - 0.10, fy0, 1.14, 1.44, "equip_gray", skip=("back",))
        mb.box(-0.995, -0.705, fy0 - 0.122, fy0, 1.44, 1.466, "iron_dark", skip=("back",))
        mb.box(-0.95, -0.75, fy0 - 0.108, fy0 - 0.10, 1.35, 1.378, "iron_dark", skip=("back",))
        mb.box(-0.955, -0.745, fy0 - 0.114, fy0 - 0.10, 1.378, 1.392, "stainless", skip=("back",))
        add_address_plate(mb, "y", fy0 - 0.10, -1, g0 - gp / 2, 1.70, stage)
        # 대문 상단 조명 보강 (어두운 하우징 + 넓고 밝은 발광 디퓨저, 야간 도로면 시인성 확보)
        mb.box(gm - 0.16, gm + 0.16, fy0 - 0.18, fy0 + 0.06, gh - 0.04, gh, "iron_dark", skip=("top",))
        mb.box(gm - 0.13, gm + 0.13, fy0 - 0.15, fy0 + 0.03, gh - 0.11, gh - 0.04, "lamp", skip=("top",))
        add_downspout(mb, "x", x0, -1, 0.30, 0.02, z_top - 0.02, eave_out=spec.eave_out)
        add_downspout(mb, "x", x1, 1, d - 0.30, 0.02, z_top - 0.02, eave_out=spec.eave_out)
    add_ac_unit(mb, "x", x1, 1, 4.10, 0.0, stage)
    add_ac_unit(mb, "y", d, 1, 1.20, z_slab1 + 0.30, stage)


# ---------------------------------------------------------------------------
# 공용 소형 부재 (03·04)
# ---------------------------------------------------------------------------
def _door_canopy(mb, ax0, ax1, depth, z_f, z_b, tint, stage):
    """출입문 위 경사 폴리카보네이트 차양(앞벽 y=0 기준) + 앞 테두리 바 + 서까래 + 벽 삼각 까치발."""
    if stage == 2:
        return
    ay0 = -depth
    add_tiled_slope_poly(mb, [(ax0, ay0, z_f + 0.016), (ax1, ay0, z_f + 0.016),
                              (ax1, 0.0, z_b + 0.016), (ax0, 0.0, z_b + 0.016)], tint, stage)
    add_tiled_slope_poly(mb, [(ax0, 0.0, z_b), (ax1, 0.0, z_b), (ax1, ay0, z_f), (ax0, ay0, z_f)], tint, stage)
    if stage == 0:
        mb.box(ax0, ax1, ay0 - 0.014, ay0 + 0.014, z_f - 0.014, z_f + 0.016, "iron_dark")
        for bx in (ax0 + 0.08, 0.5 * (ax0 + ax1), ax1 - 0.08):
            add_beam(mb, (bx, ay0, z_f - 0.012), (bx, -0.02, z_b - 0.012), 0.015, 0.015, "iron_dark")
        for bx in (ax0 + 0.08, ax1 - 0.08):
            mb.box(bx - 0.018, bx + 0.018, -0.035, 0.0, z_f - 0.44, z_b - 0.015, "iron_dark", skip=("back",))
            zb_e = z_f + (z_b - z_f) * (0.18 / depth) - 0.015
            add_beam(mb, (bx, -0.035, z_f - 0.40), (bx, ay0 + 0.18, zb_e), 0.015, 0.015, "iron_dark")


def _wall_meter_pair(mb, axis, c, side, a_mid, z_mid):
    """벽 계량기 2개 연접 (전면 칸 전체 UV) + 아래 전선관."""
    for k, am in enumerate((a_mid - 0.13, a_mid + 0.13)):
        K.axbox(mb, axis, c, side, am - 0.10, am + 0.10, 0.0, 0.14, z_mid - 0.15, z_mid + 0.15, "equip_gray")
        mb.quad(K.face_pts(axis, c + side * 0.142, side, am - 0.10, am + 0.10, z_mid - 0.15, z_mid + 0.15),
                mb.atlas.uv_full("meter_face"), "meter_face")
    K.axbox(mb, axis, c, side, a_mid - 0.02, a_mid + 0.02, 0.0, 0.04, 0.30, z_mid - 0.15, "iron_dark")


# ---------------------------------------------------------------------------
# 유형 T3 빌더: 2층 외부 계단형 (SintanjinHouse03)
# 근거: work/roadview_extra/d03_stair_side.png, d03_street_stair.png, d02_mass_hip_roof.png (석봉동),
#       STYLE_BRIEF T3(h13~h18 계단 치수: 폭 1.10, 막힌 난간벽 0.95 + 갓돌 0.08, 상부 스테인리스 레일)
# 흑회색 벽돌 2층 + 전면을 따라 오르는 흰 미장 외부계단 매스(막힌 난간벽·두겁·레일) + 계단 밑 창고문
# ---------------------------------------------------------------------------
def _build_ext_stairs(mb: K.MeshBuilder, wins: K.WindowSet, spec: DetachedSpec, stage: int):
    w, d = spec.width, spec.depth
    x0, x1 = -w / 2.0, w / 2.0                    # -4.90 .. +4.90
    zp = spec.plinth_h                             # 0.40
    z_slab1 = zp + spec.h1                         # 3.30
    z_slab0 = z_slab1 - spec.slab_h                # 2.98
    z_top = z_slab1 + spec.h2                      # 6.02
    wall_t, t_pl, c_ov = 0.22, 0.025, 0.03

    # 외부 계단 (앞벽을 따라 오른쪽 아래 -> 왼쪽 위 랜딩)
    y_po, y_pi = -1.30, -1.08                      # 난간벽 바깥·안쪽 면 (두께 0.22, 계단 폭 1.08)
    n_r = 18
    r = z_slab1 / n_r                              # 0.183 m 단 높이
    t = 0.27                                       # 디딤 깊이
    xr = 4.75                                      # 첫 단 오른쪽 끝
    x_lr = xr - (n_r - 1) * t                      # 0.16 랜딩 오른쪽 끝
    xl = -1.40                                     # 랜딩 왼쪽 끝
    z_land = z_slab1 + 0.012                       # 랜딩 윗면 (슬래브 띠 윗면과 1.2 cm 차 -> 같은 평면 겹침 0)
    h_par = 0.95                                   # 난간벽 높이 (+ 갓돌 0.08)

    # 담장 (흰 미장 콘크리트 담 + 대문)
    fy0, fy1 = -3.70, -3.52
    sx = 7.60
    ry0, ry1 = 10.60, 10.78                        # 뒷창 앞 1.6 m 확보 (WIN_BLOCKED 0)
    g0, g1 = -3.70, -1.30                          # 대문 2.4 m (1층 현관 앞)
    gp, gh = 0.40, 2.20
    fh = 1.45

    if stage == 2:
        mb.box(x0 - t_pl, x1 + t_pl, -t_pl, d + t_pl, 0.0, zp, "concrete_light", skip=("bottom",))
        mb.box(x0, x1, 0.0, d, zp, z_slab0, "wall_main", skip=("bottom",))
        mb.box(x0 - c_ov, x1 + c_ov, -c_ov, d + c_ov, z_slab0, z_slab1, "plaster_white")
        mb.box(x0, x1, 0.0, d, z_slab1, z_top, "wall_main", skip=("bottom",))
        add_hip_roof(mb, x0, x1, 0.0, d, z_top, spec.eave_out, spec.roof_rise, stage)
        # 계단 매스 (랜딩 블록 + 경사 프리즘 1덩어리)
        mb.box(xl, x_lr, y_po, -0.002, 0.0, z_slab1 + h_par, "plaster_white", skip=("bottom", "back"))
        prof = [(x_lr, 0.0), (xr, 0.0), (xr, r + h_par), (x_lr, z_slab1 + h_par)]
        add_tiled_slope_poly(mb, [(x, y_po, z) for x, z in prof], "plaster_white", stage)
        uvp = mb.atlas.uv("plaster_white")
        mb.quad([(x_lr, y_po, z_slab1 + h_par), (xr, y_po, r + h_par), (xr, -0.002, r + h_par),
                 (x_lr, -0.002, z_slab1 + h_par)], uvp, "plaster_white")
        mb.quad([(xr, y_po, 0.0), (xr, -0.002, 0.0), (xr, -0.002, r + h_par), (xr, y_po, r + h_par)],
                uvp, "plaster_white")
        for a_, b_ in ((-sx, g0 - gp), (g1 + gp, sx)):
            mb.box(a_, b_, fy0, fy1, 0.0, fh, "plaster_white", skip=("bottom",))
        mb.box(-sx, -sx + 0.18, fy1, ry0, 0.0, fh, "plaster_white", skip=("bottom",))
        mb.box(sx - 0.18, sx, fy1, ry0, 0.0, fh, "plaster_white", skip=("bottom",))
        mb.box(-sx, sx, ry0, ry1, 0.0, fh, "plaster_white", skip=("bottom",))
        mb.box(g0 - gp, g0, fy0 - 0.05, fy1 + 0.05, 0.0, gh, "plaster_white", skip=("bottom",))
        mb.box(g1, g1 + gp, fy0 - 0.05, fy1 + 0.05, 0.0, gh, "plaster_white", skip=("bottom",))
        return

    # 1. 기단 + 내부 코어
    mb.box(x0 - t_pl, x1 + t_pl, -t_pl, d + t_pl, 0.0, zp, "concrete_light", skip=("bottom",))
    ci = wall_t + 0.02
    mb.box(x0 + ci, x1 - ci, ci, d - ci, zp, z_slab0 - 0.01, "wall_main", skip=("bottom",))
    mb.box(x0 + ci, x1 - ci, ci, d - ci, z_slab1 + 0.01, z_top - 0.01, "wall_main")

    # 2. 1층 외벽 (앞: 현관 + 거실창만 — 오른쪽은 계단 매스가 가림)
    add_recessed_wall(mb, wins, "y", 0.0, -1, x0, x1, zp, z_slab0, "wall_main",
                      [(-3.95, -2.95, zp, zp + 2.10, "door_entry", 0, 3),
                       (-2.55, -1.65, zp + 0.78, zp + 2.02, "window", 0, 2)],
                      stage, spec.seed, wall_t=wall_t)
    add_recessed_wall(mb, wins, "y", d, 1, x0, x1, zp, z_slab0, "wall_main",
                      [(-3.90, -2.40, zp + 0.78, zp + 2.02, "window", 0, 2),
                       (-0.70, 0.30, zp + 1.20, zp + 2.00, "window", 0, 2),
                       (1.60, 3.40, zp + 0.78, zp + 2.02, "window", 0, 2)],
                      stage, spec.seed + 1, wall_t=wall_t)
    add_recessed_wall(mb, wins, "x", x0, -1, wall_t, d - wall_t, zp, z_slab0, "wall_main",
                      [(1.40, 2.90, zp + 0.78, zp + 2.02, "window", 0, 2),
                       (5.40, 6.90, zp + 0.78, zp + 2.02, "window", 0, 2)],
                      stage, spec.seed + 2, wall_t=wall_t)
    add_recessed_wall(mb, wins, "x", x1, 1, wall_t, d - wall_t, zp, z_slab0, "wall_main",
                      [(1.60, 3.10, zp + 0.78, zp + 2.02, "window", 0, 2),
                       (5.50, 6.50, zp + 1.20, zp + 2.00, "window", 0, 2)],
                      stage, spec.seed + 3, wall_t=wall_t)

    # 3. 흰 슬래브 띠
    mb.box(x0 - c_ov, x1 + c_ov, -c_ov, d + c_ov, z_slab0, z_slab1, "plaster_white")

    # 4. 2층 외벽 (앞: 창 + 랜딩 현관문)
    add_recessed_wall(mb, wins, "y", 0.0, -1, x0, x1, z_slab1, z_top, "wall_main",
                      [(-4.20, -2.70, z_slab1 + 0.80, z_slab1 + 2.04, "window", 1, 2),
                       (-1.05, -0.15, z_slab1 + 0.02, z_slab1 + 2.12, "door_entry", 1, 1),
                       (0.90, 2.40, z_slab1 + 0.80, z_slab1 + 2.04, "window", 1, 2),
                       (3.20, 4.30, z_slab1 + 0.80, z_slab1 + 2.04, "window", 1, 2)],
                      stage, spec.seed + 10, wall_t=wall_t)
    add_recessed_wall(mb, wins, "y", d, 1, x0, x1, z_slab1, z_top, "wall_main",
                      [(-3.90, -2.40, z_slab1 + 0.80, z_slab1 + 2.04, "window", 1, 2),
                       (-0.70, 0.30, z_slab1 + 1.20, z_slab1 + 2.00, "window", 1, 2),
                       (1.60, 3.40, z_slab1 + 0.80, z_slab1 + 2.04, "window", 1, 2)],
                      stage, spec.seed + 11, wall_t=wall_t)
    for side, xc, sd in ((-1, x0, 12), (1, x1, 13)):
        add_recessed_wall(mb, wins, "x", xc, side, wall_t, d - wall_t, z_slab1, z_top, "wall_main",
                          [(1.60, 3.10, z_slab1 + 0.80, z_slab1 + 2.04, "window", 1, 2),
                           (5.50, 7.00, z_slab1 + 0.80, z_slab1 + 2.04, "window", 1, 2)],
                          stage, spec.seed + sd, wall_t=wall_t)

    # 5. 낮은 모임지붕 (암회 기와) + 목재 소핏 + 흰 처마 띠
    add_hip_roof(mb, x0, x1, 0.0, d, z_top, spec.eave_out, spec.roof_rise, stage)

    # 6. 외부 계단 매스 (규칙 7: 디딤판이 바닥까지 꽉 찬 계단 블록 -> 틈 0, 벽에 밀착, 막힌 난간벽 + 갓돌 + 레일)
    # 6-1 디딤 블록: 윗면(콘크리트) + 챌면만 (앞은 난간벽, 뒤는 벽, 왼쪽은 다음 단에 가려짐)
    for i in range(n_r - 1):
        sx1_ = xr - i * t
        sx0_ = sx1_ - t
        mb.box(sx0_, sx1_, y_pi, 0.0, 0.0, (i + 1) * r,
               {"default": "plaster_white", "top": "concrete_light", "right": "concrete_light"},
               skip=("front", "back", "left", "bottom"))
        if stage == 0:
            # 디딤 코 미끄럼 방지 홈 줄 (2 cm, 디딤면 위 3 mm)
            mb.box(sx1_ - 0.05, sx1_ - 0.03, y_pi + 0.04, -0.04, (i + 1) * r, (i + 1) * r + 0.003, "iron_dark",
                   skip=("bottom",))
    # 6-2 랜딩 블록 (윗면 z_land, 왼쪽 끝 벽은 6-4 에서)
    mb.box(xl + wall_t, x_lr, y_pi, 0.0, 0.0, z_land,
           {"default": "plaster_white", "top": "concrete_light"}, skip=("front", "back", "left", "bottom"))
    # 6-3 경사 난간벽 (y_po..y_pi, 앞·뒤 면 타일 UV, 끝면 닫힘)
    top_l, top_r = z_slab1 + h_par, r + h_par
    prof_f = [(x_lr, y_po, 0.0), (xr, y_po, 0.0), (xr, y_po, top_r), (x_lr, y_po, top_l)]
    prof_b = [(xr, y_pi, 0.0), (x_lr, y_pi, 0.0), (x_lr, y_pi, top_l), (xr, y_pi, top_r)]
    add_tiled_slope_poly(mb, prof_f, "plaster_white", stage)
    add_tiled_slope_poly(mb, prof_b, "plaster_white", stage)
    uvp = mb.atlas.uv("plaster_white")
    mb.quad([(xr, y_po, 0.0), (xr, y_pi, 0.0), (xr, y_pi, top_r), (xr, y_po, top_r)], uvp, "plaster_white")
    mb.quad([(x_lr, y_po, top_l), (xr, y_po, top_r), (xr, y_pi, top_r), (x_lr, y_pi, top_l)], uvp, "plaster_white")
    # 6-4 랜딩 앞 난간벽 (계단 밑 창고문 포함, 벽 두께 0.22) + 왼쪽 끝 벽
    add_recessed_wall(mb, wins, "y", y_po, -1, xl, x_lr, 0.0, z_slab1 + h_par, "plaster_white",
                      [(xl + 0.32, xl + 1.12, 0.0, 1.95, "door_solid", 0, 3)], stage, spec.seed + 20, wall_t=wall_t)
    _world_tiled_box(mb, xl, xl + wall_t, y_pi, -0.002, 0.0, z_slab1 + h_par, "plaster_white", skip=("bottom", "back"))
    # 6-5 갓돌 (경사 + 수평, 두께 8 cm, 양쪽 2 cm 내밈)
    yc = 0.5 * (y_po + y_pi)
    zc_l, zc_r = top_l + 0.04, top_r + 0.04
    add_beam(mb, (x_lr, yc, zc_l), (xr + 0.02, yc, zc_r - 0.02 * r / t), 0.13, 0.04, "concrete_light")
    mb.box(xl - 0.02, x_lr, y_po - 0.02, y_pi + 0.02, top_l, top_l + 0.08, "concrete_light")
    mb.box(xl - 0.02, xl + wall_t + 0.02, y_pi + 0.02, -0.002, top_l, top_l + 0.08, "concrete_light")
    # 6-6 스테인리스 핸드레일 (갓돌 위 기둥 + 파이프)
    if stage == 0:
        zr = 0.20
        rail_pts = [(xl + 0.11, -0.12), (xl + 0.11, yc), (x_lr, yc)]
        z_rail_l = top_l + 0.08 + zr
        add_oct_tube(mb, (rail_pts[0][0], rail_pts[0][1], z_rail_l), (rail_pts[1][0], rail_pts[1][1], z_rail_l),
                     0.021, "stainless", n=6)
        add_oct_tube(mb, (rail_pts[1][0], rail_pts[1][1], z_rail_l), (x_lr, yc, z_rail_l), 0.021, "stainless", n=6)
        z_rail_r = top_r + 0.08 + zr
        add_oct_tube(mb, (x_lr, yc, z_rail_l), (xr - 0.10, yc, z_rail_r + 0.10 * r / t), 0.021, "stainless", n=6)
        posts = [(xl + 0.11, -0.30), (xl + 0.11, yc), (x_lr - 0.70, yc), (x_lr, yc)]
        n_p = 4
        for k in range(1, n_p + 1):
            px = x_lr + (xr - 0.10 - x_lr) * k / n_p
            posts.append((px, yc))
        for px, py in posts:
            f_ = max(0.0, (px - x_lr) / (xr - x_lr))
            zb_ = top_l + (top_r - top_l) * f_ + 0.08
            zt_ = z_rail_l if px <= x_lr + 1e-6 else z_rail_l + (z_rail_r - z_rail_l) * (px - x_lr) / (xr - x_lr)
            mb.box(px - 0.012, px + 0.012, py - 0.012, py + 0.012, zb_ + 0.004, zt_ - 0.02, "stainless",
                   skip=("bottom",))

    # 7. 1층 현관 차양 (청회 폴리카보네이트) + 현관등 + 인터폰
    _door_canopy(mb, -4.15, -2.75, 1.05, 2.66, 2.88, spec.poly_tint, stage)
    if stage == 0:
        K.axbox(mb, "y", 0.0, -1, -2.82, -2.71, 0.0, 0.030, zp + 1.16, zp + 1.33, "iron_dark")
        K.axbox(mb, "y", 0.0, -1, -2.805, -2.725, 0.030, 0.036, zp + 1.175, zp + 1.315, "equip_gray")
        # 계단 밑 창고문 위 벽등 + 랜딩 현관 벽등
        K.axbox(mb, "y", y_po, -1, xl + 0.60, xl + 0.84, 0.0, 0.09, 2.18, 2.32, "iron_dark")
        K.axbox(mb, "y", y_po, -1, xl + 0.63, xl + 0.81, 0.02, 0.105, 2.20, 2.30, "lamp")
        K.axbox(mb, "y", 0.0, -1, 0.02, 0.26, 0.0, 0.09, z_slab1 + 2.30, z_slab1 + 2.45, "iron_dark")
        K.axbox(mb, "y", 0.0, -1, 0.05, 0.23, 0.02, 0.105, z_slab1 + 2.32, z_slab1 + 2.42, "lamp")

    # 8. 담장: 흰 미장 콘크리트 담 + 콘크리트 갓돌 + 흰 기둥 대문 (d03_stair_side 흰 담)
    for a_, b_ in ((-sx + 0.18, g0 - gp), (g1 + gp, sx - 0.18)):
        _world_tiled_box(mb, a_, b_, fy0, fy1, 0.0, fh, "plaster_white", skip=("bottom",))
        mb.box(a_ + (0.03 if a_ < 0 else 0.0), b_ - (0.03 if b_ > 0 else 0.0), fy0 - 0.03, fy1 + 0.03,
               fh, fh + 0.07, "concrete_light")       # 옆담 갓돌과 맞대기 (같은 평면 겹침 0)
    for s0_, s1_ in ((-sx, -sx + 0.18), (sx - 0.18, sx)):
        _world_tiled_box(mb, s0_, s1_, fy0, ry0, 0.0, fh, "plaster_white", skip=("bottom",))
        mb.box(s0_ - 0.03, s1_ + 0.03, fy0 - 0.03, ry0 - 0.03, fh, fh + 0.07, "concrete_light")
    _world_tiled_box(mb, -sx, sx, ry0, ry1, 0.0, fh, "plaster_white", skip=("bottom",))
    mb.box(-sx - 0.03, sx + 0.03, ry0 - 0.03, ry1 + 0.03, fh, fh + 0.07, "concrete_light")
    for pa, pb in ((g0 - gp, g0), (g1, g1 + gp)):
        _world_tiled_box(mb, pa, pb, fy0 - 0.06, fy1 + 0.06, 0.0, gh, "plaster_white", skip=("bottom",))
        mb.box(pa - 0.04, pb + 0.04, fy0 - 0.10, fy1 + 0.10, gh, gh + 0.08, "concrete_light")
    _build_iron_gate(mb, g0, g1, fy0, fy1, stage)

    # 9. 생활 디테일
    if stage == 0:
        _wall_meter_pair(mb, "y", fy0, -1, 0.55, 1.10)          # 대문 오른쪽 흰 담 계량기 (d03_stair_side)
        add_address_plate(mb, "y", fy0 - 0.06, -1, g0 - gp / 2, 1.72, stage)
        # 우편함 (오른쪽 대문 기둥)
        mb.box(g1 + 0.07, g1 + 0.33, fy0 - 0.16, fy0 - 0.06, 1.14, 1.44, "equip_gray", skip=("back",))
        mb.box(g1 + 0.055, g1 + 0.345, fy0 - 0.182, fy0 - 0.06, 1.44, 1.466, "iron_dark", skip=("back",))
        mb.box(g1 + 0.10, g1 + 0.30, fy0 - 0.168, fy0 - 0.16, 1.35, 1.378, "iron_dark", skip=("back",))
        add_downspout(mb, "x", x0, -1, 0.30, 0.02, z_top - 0.02, eave_out=spec.eave_out)
        add_downspout(mb, "x", x1, 1, d - 0.30, 0.02, z_top - 0.02, eave_out=spec.eave_out)
    add_ac_unit(mb, "x", x1, 1, 4.30, 0.0, stage)
    add_ac_unit(mb, "y", d, 1, -1.60, z_slab1 + 0.30, stage)


# ---------------------------------------------------------------------------
# 유형 T4 빌더: 1층 근린상가 겸용 2층 주택 (SintanjinHouse04)
# 근거: STYLE_BRIEF T4(h19~h24: 1층 층고 3.3, 가로 판류 간판, 천막 어닝, 실외기, 측면 주택 출입구, 평지붕 파라펫),
#       work/roadview_extra/d04_alley_shop.png (석봉동 골목 1층 상가 — 실제 상호 미사용)
# ---------------------------------------------------------------------------
def _awning(mb, xa, xb, z_hi, depth, drop, region, stage):
    """상가 천막 어닝 (벽 2 cm 띄움, 경사 천 + 앞 드림 + 양끝 철제 팔)."""
    if stage == 2:
        return
    uv = mb.atlas.uv_full(region)
    y_w, y_f = -0.02, -depth
    z_f = z_hi - drop
    mb.quad([(xa, y_f, z_f), (xb, y_f, z_f), (xb, y_w, z_hi), (xa, y_w, z_hi)], uv, region)
    mb.quad([(xa, y_w, z_hi - 0.012), (xb, y_w, z_hi - 0.012), (xb, y_f, z_f - 0.012), (xa, y_f, z_f - 0.012)],
            uv, region)
    mb.box(xa, xb, y_f - 0.012, y_f, z_f - 0.10, z_f, region)            # 앞 드림 (valance)
    if stage == 0:
        for xx in (xa + 0.04, xb - 0.04):
            mb.quad([(xx, y_w, z_hi), (xx, y_f, z_f), (xx, y_f, z_f - 0.012), (xx, y_w, z_hi - 0.012)],
                    uv, region)
            add_beam(mb, (xx, -0.03, z_hi - 0.30), (xx, y_f + 0.05, z_f - 0.03), 0.012, 0.012, "iron_dark")
            K.axbox(mb, "y", 0.0, -1, xx - 0.03, xx + 0.03, 0.0, 0.03, z_hi - 0.36, z_hi - 0.24, "iron_dark")


def _build_shop_1f(mb: K.MeshBuilder, wins: K.WindowSet, spec: DetachedSpec, stage: int):
    w, d = spec.width, spec.depth
    x0, x1 = -w / 2.0, w / 2.0                    # -5.70 .. +5.70
    z_slab1 = spec.h1                              # 3.35 (기단 없음, 보도 직결)
    z_slab0 = z_slab1 - spec.slab_h                # 3.05
    z_top = z_slab1 + spec.h2                      # 6.20
    z_par = z_top + 0.75                           # 파라펫 벽 끝 (+ 두겁 0.10)
    wall_t, c_ov = 0.22, 0.03
    pr = 0.24                                      # 파라펫 링 두께 (벽 윗면 + 코어 틈 덮음)

    if stage == 2:
        mb.box(x0, x1, 0.0, d, 0.0, z_slab0, "wall_main", skip=("bottom",))
        mb.box(x0 - c_ov, x1 + c_ov, -c_ov, d + c_ov, z_slab0, z_slab1, "plaster_white")
        mb.box(x0, x1, 0.0, d, z_slab1, z_par, {"default": "wall_main", "top": "terrace_floor"})
        mb.box(x0 - 0.04, x1 + 0.04, -0.04, d + 0.04, z_par, z_par + 0.10, "plaster_white")
        mb.box(-5.60, 3.70, -0.14, -0.035, 2.40, 3.24, "shop_signs")
        mb.box(2.60, 4.40, 6.50, 8.30, z_par + 0.10, z_top + 2.10, "pvc_white")
        return

    # 1. 내부 코어 (윗면 = 옥상 바닥 마감)
    ci = wall_t + 0.02
    mb.box(x0 + ci, x1 - ci, ci, d - ci, 0.0, z_slab0 - 0.01, "wall_main", skip=("bottom",))
    mb.box(x0 + ci, x1 - ci, ci, d - ci, z_slab1 + 0.01, z_top,
           {"default": "wall_main", "top": "terrace_floor"})

    # 2. 1층 상가 전면 (암회색 알루미늄 샷시 쇼윈도·유리문 2곳 + 주택 현관)
    add_recessed_wall(mb, wins, "y", 0.0, -1, x0, x1, 0.0, z_slab0, "wall_main",
                      [(-5.30, -3.80, 0.0, 2.30, "door_glass", 0, 2),
                       (-3.55, -1.05, 0.45, 1.98, "window", 0, 3),     # 쇼윈도 위는 어닝이 덮어 상단 1.98
                       (-0.55, 1.95, 0.45, 1.98, "window", 0, 3),
                       (2.20, 3.70, 0.0, 2.30, "door_glass", 0, 2),
                       (4.35, 5.30, 0.0, 2.25, "door_entry", 0, 1)],
                      stage, spec.seed, wall_t=wall_t, sash_reg="sash_dark")
    add_recessed_wall(mb, wins, "y", d, 1, x0, x1, 0.0, z_slab0, "wall_main",
                      [(-4.60, -3.70, 0.0, 2.10, "door_solid", 0, 3),
                       (-2.40, -1.40, 1.30, 2.10, "window", 0, 2),
                       (1.20, 2.20, 1.30, 2.10, "window", 0, 2),
                       (3.60, 4.60, 1.30, 2.10, "window", 0, 2)],
                      stage, spec.seed + 1, wall_t=wall_t)
    add_recessed_wall(mb, wins, "x", x0, -1, wall_t, d - wall_t, 0.0, z_slab0, "wall_main",
                      [(3.00, 4.20, 1.20, 2.20, "window", 0, 2),
                       (6.60, 7.80, 1.20, 2.20, "window", 0, 2)],
                      stage, spec.seed + 2, wall_t=wall_t)
    add_recessed_wall(mb, wins, "x", x1, 1, wall_t, d - wall_t, 0.0, z_slab0, "wall_main",
                      [(4.40, 5.60, 1.20, 2.20, "window", 0, 2),
                       (7.20, 8.40, 1.20, 2.20, "window", 0, 2)],
                      stage, spec.seed + 3, wall_t=wall_t)

    # 3. 흰 슬래브 띠
    mb.box(x0 - c_ov, x1 + c_ov, -c_ov, d + c_ov, z_slab0, z_slab1, "plaster_white")

    # 4. 2층 주거 (넓은 흰 PVC 미닫이창)
    add_recessed_wall(mb, wins, "y", 0.0, -1, x0, x1, z_slab1, z_top, "wall_main",
                      [(-4.80, -2.70, z_slab1 + 0.75, z_slab1 + 2.10, "window", 1, 3),
                       (-1.70, 0.40, z_slab1 + 0.75, z_slab1 + 2.10, "window", 1, 3),
                       (1.40, 2.90, z_slab1 + 0.80, z_slab1 + 2.06, "window", 1, 2),
                       (3.80, 5.00, z_slab1 + 0.80, z_slab1 + 2.06, "window", 1, 2)],
                      stage, spec.seed + 10, wall_t=wall_t)
    add_recessed_wall(mb, wins, "y", d, 1, x0, x1, z_slab1, z_top, "wall_main",
                      [(-4.20, -2.70, z_slab1 + 0.80, z_slab1 + 2.06, "window", 1, 2),
                       (-0.80, 0.20, z_slab1 + 1.20, z_slab1 + 2.00, "window", 1, 2),
                       (1.60, 3.40, z_slab1 + 0.80, z_slab1 + 2.06, "window", 1, 2)],
                      stage, spec.seed + 11, wall_t=wall_t)
    for side, xc, sd in ((-1, x0, 12), (1, x1, 13)):
        add_recessed_wall(mb, wins, "x", xc, side, wall_t, d - wall_t, z_slab1, z_top, "wall_main",
                          [(1.80, 3.30, z_slab1 + 0.80, z_slab1 + 2.06, "window", 1, 2),
                           (6.20, 7.70, z_slab1 + 0.80, z_slab1 + 2.06, "window", 1, 2)],
                          stage, spec.seed + sd, wall_t=wall_t)

    # 5. 평지붕 파라펫 (벽돌 링 + 흰 두겁, 모서리 감싸기)
    _world_tiled_box(mb, x0, x1, 0.0, pr, z_top, z_par, "wall_main", skip=("bottom",))
    _world_tiled_box(mb, x0, x1, d - pr, d, z_top, z_par, "wall_main", skip=("bottom",))
    _world_tiled_box(mb, x0, x0 + pr, pr, d - pr, z_top, z_par, "wall_main", skip=("bottom", "front", "back"))
    _world_tiled_box(mb, x1 - pr, x1, pr, d - pr, z_top, z_par, "wall_main", skip=("bottom", "front", "back"))
    mb.box(x0 - 0.04, x1 + 0.04, -0.04, pr + 0.02, z_par, z_par + 0.10, "plaster_white")
    mb.box(x0 - 0.04, x1 + 0.04, d - pr - 0.02, d + 0.04, z_par, z_par + 0.10, "plaster_white")
    mb.box(x0 - 0.04, x0 + pr + 0.02, pr + 0.02, d - pr - 0.02, z_par, z_par + 0.10, "plaster_white",
           skip=("front", "back"))
    mb.box(x1 - pr - 0.02, x1 + 0.04, pr + 0.02, d - pr - 0.02, z_par, z_par + 0.10, "plaster_white",
           skip=("front", "back"))
    # 옥상 보온 물탱크 함체 (흰 샌드위치 패널, STYLE_BRIEF 5장)
    mb.box(2.60, 4.40, 6.50, 8.30, z_top, z_top + 2.10, "pvc_white", skip=("bottom",))
    if stage == 0:
        for kx in (3.05, 3.50, 3.95):
            mb.box(kx - 0.012, kx + 0.012, 6.488, 6.50, z_top + 0.05, z_top + 2.05, "equip_gray", skip=("back",))
        mb.box(2.58, 4.42, 6.48, 8.32, z_top + 2.10, z_top + 2.14, "equip_gray")

    # 6. 간판 (판류 2개 + 세로 돌출 1개, 칸 전체 UV — 규칙 12·19, 가상 상호)
    def sign_board(xa, xb, za, zb, fu0, fv0, fu1, fv1):
        K.axbox(mb, "y", 0.0, -1, xa, xb, 0.035, 0.14, za, zb, "iron_dark", skip=("front",))
        mb.quad(K.face_pts("y", -0.14, -1, xa, xb, za, zb), KX.uv_cell(mb.atlas, "shop_signs", fu0, fv0, fu1, fv1),
                "shop_signs")
    sign_board(-5.60, -1.00, 2.42, 3.24, 4 / 1024, 1 - 172 / 1024, 1020 / 1024, 1 - 4 / 1024)
    sign_board(-0.55, 3.75, 2.42, 3.24, 4 / 1024, 1 - 406 / 1024, 1020 / 1024, 1 - 196 / 1024)
    if stage < 2:
        sx_a, sx_b = -5.52, -5.42
        sy_a, sy_b = -0.64, -0.16
        sz_a, sz_b = 3.62, 5.12
        mb.box(sx_a, sx_b, sy_a, sy_b, sz_a, sz_b, "iron_dark", skip=("left", "right"))
        uv_v = KX.uv_cell(mb.atlas, "shop_signs", 20 / 1024, 1 - 1004 / 1024, 176 / 1024, 1 - 436 / 1024)
        mb.quad(K.face_pts("x", sx_a, -1, sy_a, sy_b, sz_a, sz_b), uv_v, "shop_signs")
        mb.quad(K.face_pts("x", sx_b, 1, sy_a, sy_b, sz_a, sz_b), uv_v, "shop_signs")
        if stage == 0:
            for zz in (sz_a + 0.10, sz_b - 0.14):
                mb.box(sx_a + 0.03, sx_b - 0.03, sy_b, -0.0, zz, zz + 0.04, "iron_dark", skip=("back",))

    # 7. 천막 어닝 (쇼윈도 위, 녹색·자주) + 주택 현관 차양
    _awning(mb, -3.62, -0.98, 2.36, 0.95, 0.24, "awning_green", stage)
    _awning(mb, -0.62, 2.02, 2.36, 0.95, 0.24, "awning_wine", stage)
    _door_canopy(mb, 4.12, 5.53, 0.95, 2.52, 2.74, spec.poly_tint, stage)

    # 8. 생활 디테일 (계량기·번지판·실외기·우수관·보도 쪽 상가 소품 없음 — z=0 바닥 메시 금지)
    if stage == 0:
        _wall_meter_pair(mb, "x", x1, 1, 1.10, 1.50)
        add_address_plate(mb, "x", x1, 1, 0.45, 1.75, stage)
        add_downspout(mb, "x", x0, -1, d - 0.30, 0.02, z_par - 0.05)
        add_downspout(mb, "x", x1, 1, d - 0.30, 0.02, z_par - 0.05)
        # 주택 현관 인터폰 (현관문 왼쪽 벽기둥)
        K.axbox(mb, "y", 0.0, -1, 4.05, 4.16, 0.0, 0.030, 1.16, 1.33, "iron_dark")
        K.axbox(mb, "y", 0.0, -1, 4.065, 4.145, 0.030, 0.036, 1.175, 1.315, "equip_gray")
    add_ac_unit(mb, "x", x1, 1, 2.60, 0.0, stage)
    add_ac_unit(mb, "y", d, 1, -2.00, z_slab1 + 0.30, stage)
    add_ac_unit(mb, "x", x0, -1, 5.40, 0.0, stage)


# ---------------------------------------------------------------------------
# 통합 빌드 및 익스포트
# ---------------------------------------------------------------------------
def build_stage(spec: DetachedSpec, a: K.Atlas, stage: int):
    mb = K.MeshBuilder(a, split_tiles=(stage == 0))
    wins = K.WindowSet()
    if spec.archetype == "front_terrace":
        _build_front_terrace(mb, wins, spec, stage)
    elif spec.archetype == "standard_2f":
        _build_standard_2f(mb, wins, spec, stage)
    elif spec.archetype == "ext_stairs":
        _build_ext_stairs(mb, wins, spec, stage)
    elif spec.archetype == "shop_1f":
        _build_shop_1f(mb, wins, spec, stage)
    else:
        raise NotImplementedError(f"Archetype {spec.archetype} pending checkpoint approval")
    return mb, wins


def build_and_export(spec: DetachedSpec, out_root=None):
    a = build_atlas(spec)
    main, wins = build_stage(spec, a, 0)
    l1, _ = build_stage(spec, a, 1)
    l2, _ = build_stage(spec, a, 2)
    folder, result = K.export_asset(
        spec.name, 1,
        dict(main=main, lod1=l1, lod2=l2, windows=wins),
        a,
        out_root or K.out_dir_from_argv("output"),
        lod2_tex=512,
        lot=spec.lot,
        front_yard=spec.front_yard,
        notes=dict(archetype=spec.archetype, palette=spec.wall_palette,
                   roof=spec.roof_type, seed=spec.seed),
    )
    print(f"[detached_core] {result['asset']}: main={main.tri_count} lod1={l1.tri_count} "
          f"lod2={l2.tri_count} wins={len(wins.items)} (lod2+2w={l2.tri_count + len(wins.items)*2})")
    return folder, result
