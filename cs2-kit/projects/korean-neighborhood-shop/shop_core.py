# -*- coding: utf-8 -*-
"""한국형 근린상가 (모퉁이 3층 + 박공 파라펫 + 옥탑) 생성기 코어.

근거 (shape_notes.md / work/roadview_extra/SOURCES.md):
- 사용자 기준 사진 user_ref_corner_shop_2026-11-09.png (2026-11-09 Codex 세션 첨부, 위치 미확인)
  -> 3층, 베이지 석재 + 갈색 석재 기둥, 3층 띠창·난간, 2층 유리 글자 간판, 1층 노란 간판·파란 차양, 박공형 상부
- 신탄진동 화강석 상가 거리뷰 s01~s03 (2026-10-08) -> 석재 타일 규격, 석재 띠 위 입체 글자, 짙은 창틀
- 2026-11-09 시제품 assets/korean_neighborhood_shop/ (원본 삭제, 세션 도구 입력에서 스크립트만 복구) 의
  마지막 방향(3층+옥탑, 14 x 12 m)을 cs2-kit 파이프라인으로 재구성. 평면 칠 창 -> 실제 후퇴 창호로 교체.

재사용: korean-detached/detached_core.py 의 칠 함수·add_recessed_wall·실외기·우수관·다각 관.
원본 키트, detached_core, kitext 는 수정하지 않는다.
"""
from dataclasses import dataclass
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / "korean-detached"))
import cs2kit as K
import detached_core as DC
from local import kitext as KX


@dataclass(frozen=True)
class ShopSpec:
    name: str = "SintanjinCornerShop01"
    lot: tuple = (2, 2)            # 16 x 16 m 상업 Growable 후보 # estimated
    front_yard: float = 2.0
    width: float = 14.0            # 정면 # estimated (시제품 14 m, 사용자 사진 정면 5칸)
    depth: float = 12.0            # 깊이 # estimated
    z1: float = 4.20               # 1층 층고 (상가 유리 + 간판 띠) # estimated
    z2: float = 7.60               # 3층 바닥 (2층 층고 3.40)
    z3: float = 11.00              # 옥상 슬래브
    z_par: float = 12.00           # 파라펫 상단
    road_name: str = "신탄상가길"   # 가상 도로명 (규칙 20)
    road_no: str = "12"
    seed: int = 5


PRESETS = {"01": ShopSpec()}
WT = 0.25          # 외벽 두께
LEDGE_O = 0.08     # 석재 띠 돌출
PIER_O = 0.10      # 갈색 석재 기둥 돌출

# 가상 상호 (실제 상호·브랜드 금지, 규칙 19). (칸 이름, 가로:세로 비, 그리기 함수 키)
SIGNS = [
    ("sg_yellow", 6.30),   # 1층 좌 노란 공인중개사 간판 5.6 x 0.9
    ("sg_dark", 6.30),     # 1층 우 짙은 띠 + 흰 글자
    ("sg_glass_l", 5.40),  # 2층 유리 글자 (좌)
    ("sg_glass_m", 5.40),  # 2층 유리 글자 (중)
    ("sg_glass_r", 5.40),  # 2층 유리 글자 (우)
    ("sg_stone", 18.7),    # 3층 아래 석재 띠 입체 글자 11.2 x 0.6
]
SIGN_STRIP_H = 1024

# 2026-11-24 인게임: 간판·조명이 블룸으로 하얗게 날아감 -> 발광 배율 대폭 하향 (게임 블룸 기준 노브)
EMIS_SIGN = 0.22    # 간판 글자 (이전 0.90). 바탕 발광은 이 배율의 약 1/3
EMIS_VSIGN = 0.20   # 세로 돌출 간판 (이전 0.85)
EMIS_LAMP = 0.28    # 처마 다운라이트·옥탑등 (이전 1.00)
EMIS_WIN = 0.55     # 창 실내등 (DC 창 0.58~0.86 -> 0.32~0.47)


# ---------------------------------------------------------------------------
# 간판 그림 (굵은 한글 간판 글꼴, 칸 전체 UV — 규칙 12·19)
# ---------------------------------------------------------------------------
F_HEAD = "C:/Windows/Fonts/HMKMRHD.TTF"   # 휴먼둥근헤드라인
F_GOTH = "C:/Windows/Fonts/H2GTRE.TTF"    # HY견고딕
F_HDRM = "C:/Windows/Fonts/H2HDRM.TTF"    # HY헤드라인M
F_NUM = "C:/Windows/Fonts/arialbd.ttf"


def _sign_layout():
    rows, y = {}, 0
    for name, aspect in SIGNS:
        h = int(round(SIGN_STRIP_H / aspect))
        rows[name] = (y, y + h)
        y += h
    assert y <= SIGN_STRIP_H, y
    return rows


def _draw_signs(W):
    from PIL import Image, ImageDraw, ImageFont
    rows = _sign_layout()
    im = Image.new("RGB", (W, W), (40, 40, 42))
    em = Image.new("L", (W, W), 0)
    d, de = ImageDraw.Draw(im), ImageDraw.Draw(em)
    s = W / SIGN_STRIP_H

    def F(path, px):
        return ImageFont.truetype(path, max(8, int(px)))

    def strip(name):
        r0, r1 = rows[name]
        return int(r0 * s), int(r1 * s)

    def text(x, y, t, font, fill, glow=None, stroke=0, sc=None):
        d.text((x, y), t, font=font, fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=sc or fill)
        if glow is not None:
            de.text((x, y), t, font=font, fill=glow, anchor="mm", stroke_width=stroke)

    # 1층 좌: 노란 바탕 + 검정 굵은 글자 + 빨간 전화번호 (사용자 사진 'OK 공인중개사' 문법, 가상 상호)
    y0, y1 = strip("sg_yellow"); h = y1 - y0
    d.rectangle([0, y0, W - 1, y1 - 1], fill=(222, 178, 40))
    d.rectangle([int(W * 0.012), y0 + int(h * 0.07), W - 1 - int(W * 0.012), y1 - 1 - int(h * 0.07)],
                outline=(60, 50, 40), width=max(2, int(h * 0.035)))
    # 밤: 노란 아크릴 바탕만 내부 조명으로 은은하게, 검정·빨강 글자는 어둡게 남겨 대비 유지 (11-24 과발광 수정)
    de.rectangle([0, y0, W - 1, y1 - 1], fill=200)
    text(W * 0.12, y0 + h * 0.52, "한빛", F(F_HEAD, h * 0.60), (24, 26, 34), glow=0)
    text(W * 0.44, y0 + h * 0.38, "공인중개사", F(F_GOTH, h * 0.36), (24, 26, 34), glow=0)
    text(W * 0.44, y0 + h * 0.76, "아파트 · 상가 · 토지", F(F_GOTH, h * 0.20), (40, 40, 44), glow=0)
    text(W * 0.81, y0 + h * 0.52, "938-1472", F(F_NUM, h * 0.38), (172, 32, 36), glow=0)

    # 1층 우: 짙은 회색 간판 띠 + 흰·청록 글자 (분식)
    y0, y1 = strip("sg_dark"); h = y1 - y0
    d.rectangle([0, y0, W - 1, y1 - 1], fill=(52, 54, 58))
    d.rectangle([0, y0 + int(h * 0.82), W - 1, y1 - 1], fill=(64, 120, 118))
    text(W * 0.30, y0 + h * 0.44, "금강분식", F(F_HEAD, h * 0.54), (236, 236, 232), glow=255)
    text(W * 0.77, y0 + h * 0.28, "김밥 · 라면 · 떡볶이", F(F_GOTH, h * 0.19), (210, 214, 214), glow=220)
    text(W * 0.77, y0 + h * 0.58, "☎ 932-6018", F(F_GOTH, h * 0.21), (210, 214, 214), glow=220)

    # 2층 유리 글자: 짙은 유리 바탕 + 흰 시트 글자 (사용자 사진 2층)
    glass = (40, 58, 66)
    for name, t, sub in (("sg_glass_l", "세무회계", "T. 935-2081"),
                         ("sg_glass_m", "바른길", "세무사 사무소"),
                         ("sg_glass_r", "무 료 상 담", "기장 · 신고 · 컨설팅")):
        y0, y1 = strip(name); h = y1 - y0
        d.rectangle([0, y0, W - 1, y1 - 1], fill=glass)
        text(W * 0.5, y0 + h * 0.40, t, F(F_GOTH, h * 0.56), (232, 234, 230), glow=200)
        text(W * 0.5, y0 + h * 0.84, sub, F(F_GOTH, h * 0.20), (214, 218, 216), glow=150)

    # 3층 아래 석재 띠: 석재 바탕 + 짙은 입체 글자 (s01: 석재 위 입체 글자)
    y0, y1 = strip("sg_stone"); h = y1 - y0
    d.rectangle([0, y0, W - 1, y1 - 1], fill=(168, 160, 150))
    text(W * 0.5, y0 + h * 0.52, "신 탄 영 어 수 학 학 원", F(F_HDRM, h * 0.66), (46, 46, 52), glow=0)
    return im, em


def _signs_painter():
    def painter(ctx):
        cache = HERE / "work" / "_sign_cache" / f"signs_{ctx.w}.npz"
        try:
            from PIL import Image
            im, em = _draw_signs(ctx.w * 2)
            rgb = np.asarray(im.resize((ctx.w, ctx.h), Image.LANCZOS))
            e = np.asarray(em.resize((ctx.w, ctx.h), Image.LANCZOS)) / 255.0
            cache.parent.mkdir(parents=True, exist_ok=True)
            np.savez(cache, rgb=rgb, e=e)
        except (ImportError, OSError):
            z = np.load(cache)
            rgb, e = z["rgb"], z["e"]
        ctx.rgb[...] = rgb
        ctx.emis[...] = e * EMIS_SIGN
        ctx.grain(amp=1.0, scale_px=2, height=0.02, seed=701)
        ctx.gloss = np.clip(0.50 + 0.03 * DC._var(ctx, 8, 703), 0.42, 0.58)
    return painter


def _plate_painter(name, draw):
    def painter(ctx):
        cache = HERE / "work" / "_sign_cache" / f"{name}_{ctx.w}x{ctx.h}.npz"
        try:
            from PIL import Image
            rgb = np.asarray(draw(ctx.w * 4, ctx.h * 4).resize((ctx.w, ctx.h), Image.LANCZOS))
            cache.parent.mkdir(parents=True, exist_ok=True)
            np.savez(cache, rgb=rgb)
        except (ImportError, OSError):
            rgb = np.load(cache)["rgb"]
        ctx.rgb[...] = rgb
        ctx.gloss = np.clip(0.46 + 0.03 * DC._var(ctx, 8, 257), 0.38, 0.54)
    return painter


def _draw_address(road_name, road_no):
    def draw(W, H):
        from PIL import Image, ImageDraw, ImageFont
        navy, white = (42, 66, 108), (214, 216, 220)
        im = Image.new("RGB", (W, H), navy)
        d = ImageDraw.Draw(im)
        m = max(4, int(min(W, H) * 0.07))
        d.rectangle([m, m, W - 1 - m, H - 1 - m], outline=white, width=max(3, int(H * 0.038)))
        d.text((W * 0.5, H * 0.30), road_name, font=ImageFont.truetype(F_GOTH, int(H * 0.22)), fill=white, anchor="mm")
        d.text((W * 0.5, H * 0.67), road_no, font=ImageFont.truetype(F_NUM, int(H * 0.44)), fill=white, anchor="mm")
        return im
    return draw


VSIGN_W, VSIGN_H = 0.70, 3.00   # 모퉁이 세로 돌출 간판 판 크기 (m) # estimated, 상가 세로 간판 0.45~0.8 x 2.4~3.2


def _draw_vsign(W, H):
    """모퉁이 세로 돌출 간판: 남색 머리띠 + 흰 '학원', 흰 바탕 + 남색 '영어수학'.
    W:H 는 실제 판 비율(0.70:3.00)로 받는다. 반환: (RGB, 발광 마스크 L)."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (W, H), (206, 208, 206))
    em = Image.new("L", (W, H), 0)
    d, de = ImageDraw.Draw(im), ImageDraw.Draw(em)
    m = int(W * 0.06)
    hb = int(H * 0.17)                                   # 머리띠
    d.rectangle([0, 0, W - 1, hb], fill=(48, 70, 120))
    d.rectangle([m, hb + m, W - 1 - m, H - 1 - m], outline=(48, 70, 120), width=max(2, int(W * 0.025)))
    # 밤: 흰 바탕은 약하게 비치고(내부 조명), 남색 글자는 그대로 어두워 대비가 남는다
    de.rectangle([0, hb + 1, W - 1, H - 1], fill=70)
    fh = ImageFont.truetype(F_HEAD, int(W * 0.40))
    d.text((W * 0.5, hb * 0.52), "학원", font=fh, fill=(236, 236, 232), anchor="mm")
    de.text((W * 0.5, hb * 0.52), "학원", font=fh, fill=230, anchor="mm")
    step = (H - hb - 2 * m) / 4.0
    fc = ImageFont.truetype(F_HEAD, int(min(W * 0.70, step * 0.80)))
    for k, ch in enumerate("영어수학"):
        cy = hb + m + step * (k + 0.5)
        d.text((W * 0.5, cy), ch, font=fc, fill=(40, 60, 110), anchor="mm")
        de.text((W * 0.5, cy), ch, font=fc, fill=0, anchor="mm", stroke_width=max(1, int(W * 0.02)), stroke_fill=0)
    return im, em


def _vsign_painter():
    """정사각 칸에 실제 판 비율로 그린 그림을 맞춰 넣는다 (칸 전체 UV -> 판에서 원래 비율로 복원)."""
    def painter(ctx):
        cache = HERE / "work" / "_sign_cache" / f"vsign_{ctx.w}x{ctx.h}.npz"
        try:
            from PIL import Image
            Hd = ctx.h * 4
            Wd = max(8, int(round(Hd * VSIGN_W / VSIGN_H)))
            im, em = _draw_vsign(Wd, Hd)
            rgb = np.asarray(im.resize((ctx.w, ctx.h), Image.LANCZOS))
            e = np.asarray(em.resize((ctx.w, ctx.h), Image.LANCZOS)) / 255.0
            cache.parent.mkdir(parents=True, exist_ok=True)
            np.savez(cache, rgb=rgb, e=e)
        except (ImportError, OSError):
            z = np.load(cache)
            rgb, e = z["rgb"], z["e"]
        ctx.rgb[...] = rgb
        ctx.emis[...] = e * EMIS_VSIGN
        ctx.gloss = np.clip(0.46 + 0.03 * DC._var(ctx, 8, 257), 0.38, 0.54)
    return painter


def _granite_painter(seed, cols=2, rows=2):
    """석재 판 (0.9 x 0.6 m 줄눈, 반점) — 사용자 사진 베이지 석재, s01 화강석 판.
    11-24 인게임 '디테일 아쉬움': 줄눈 폭·깊이·명암, 판별 색조·광택 편차, 흑백 반점을 키워 원경에서도 판 결이 읽히게."""
    def painter(ctx):
        d = ctx.joints(cols=cols, rows=rows, width_m=0.010, depth=0.60, darken=0.36, tone=8, seed=801 + seed)
        ctx.grain(amp=9.0, scale_px=1, height=0.14, seed=803 + seed)
        dark = ctx.noise(scale_px=1, amp=1.0, octaves=1, seed=805 + seed) > 1.9
        light = ctx.noise(scale_px=1, amp=1.0, octaves=1, seed=806 + seed) > 2.2
        ctx.rgb[dark] *= 0.74
        ctx.rgb[light] *= 1.12
        ctx.height[dark] -= 0.12
        # 판마다 광택·색 온도 편차 (연마 화강석 판의 로트 차이)
        x, z = ctx.meters()
        pid = np.floor(x / (ctx.tile[0] / cols)) * 7.0 + np.floor(z / (ctx.tile[1] / rows)) * 13.0 + ctx.vi * 31.0
        h = np.sin(pid * 12.9898 + seed * 78.233) * 43758.5453
        pg = (h - np.floor(h)) - 0.5
        ctx.rgb[..., 0] *= 1.0 + 0.025 * pg
        ctx.rgb[..., 2] *= 1.0 - 0.025 * pg
        v = DC._var(ctx, scale_px=10, seed=807 + seed)
        ctx.rgb[...] = np.clip(ctx.rgb, 30, 212)
        ctx.gloss = np.clip((0.38 + 0.12 * pg + 0.05 * v) * (1.0 - d) + 0.12 * d, 0.10, 0.52)
    return painter


def _dim(painter, k):
    """페인터 결과 발광만 k 배 (DC 창·단색 칸 재사용)."""
    def p(ctx):
        painter(ctx)
        ctx.emis[...] *= k
    return p


def _awning_painter(seed):
    """파란·하늘 줄무늬 천막 (사용자 사진 1층 좌). 줄 0.20 m. 평균 채도 <= 0.5."""
    def painter(ctx):
        x, _ = ctx.meters()
        band = (np.floor(x / 0.20) % 2) == 0
        ctx.rgb[band] = (58, 92, 150)
        ctx.rgb[~band] = (128, 152, 188)
        ctx.grain(amp=3.0, scale_px=2, height=0.06, seed=821 + seed)
        ctx.gloss = np.clip(0.20 + 0.02 * DC._var(ctx, 8, 823 + seed), 0.14, 0.26)
    return painter


def build_atlas(spec: ShopSpec) -> K.Atlas:
    s = spec.seed
    a = K.Atlas(size=2048, pad=12)
    # 베이지 석재: 사용자 사진 중앙 석재 (그늘 제외 추정) # estimated, 채도 0.12
    a.add("stone", color=(172, 164, 152), ctrl=(0, 255, 0), px=512, tile=(1.8, 1.2), gloss=0.34,
          painter=_granite_painter(s))
    # 갈색 석재 기둥·띠: 사용자 사진 좌·우 기둥, s01 갈회 화강석
    a.add("stone_brown", color=(126, 108, 98), ctrl=(0, 255, 0), px=384, tile=(1.8, 1.2), gloss=0.36,
          painter=_granite_painter(s + 3))
    a.add("plaster", color=(190, 186, 178), ctrl=(0, 255, 0), px=256, tile=(2.4, 2.4), gloss=0.24,
          painter=DC._make_plaster_painter(s + 5))
    a.add("concrete_light", color=(178, 180, 183), px=256, tile=(2.4, 2.4), gloss=0.24,
          painter=DC._make_concrete_plinth_painter(s + 7))
    a.add("roof_deck", color=(124, 140, 128), px=256, tile=(2.4, 2.4), gloss=0.30,
          painter=DC._make_terrace_floor_painter(s + 9))
    win_col = (66, 88, 100)
    a.add("window", color=win_col, px=384, gloss=0.84, emissive=(255, 226, 184),
          painter=_dim(DC._make_window_painter(s + 11), EMIS_WIN))
    a.add("window_backing", color=win_col, px=32, gloss=0.80)
    a.add("sash", color=(64, 68, 72), px=128, gloss=0.50, painter=DC._solid(1.8, 0.44, 0.56, s + 13))
    a.add("sash_dark", color=(54, 58, 62), px=128, gloss=0.50, painter=DC._solid(1.8, 0.44, 0.56, s + 15))
    a.add("stainless", color=(176, 178, 182), px=128, metal=0.65, gloss=0.62, painter=DC._solid(2.0, 0.54, 0.68, s + 17))
    a.add("iron_dark", color=(56, 58, 62), px=128, metal=0.45, gloss=0.42, painter=DC._solid(2.4, 0.34, 0.48, s + 19))
    a.add("door_wood", color=(118, 122, 126), px=128, gloss=0.40, painter=DC._solid(2.2, 0.34, 0.46, s + 21))
    a.add("equip_gray", color=(184, 186, 184), px=128, gloss=0.36, painter=DC._solid(2.2, 0.30, 0.42, s + 23))
    a.add("louver", color=(162, 166, 164), px=128, gloss=0.38, painter=DC._make_louver_painter(s + 25))
    a.add("pipe_white", color=(196, 198, 198), px=64, gloss=0.48, painter=DC._solid(1.5, 0.42, 0.54, s + 27))
    a.add("awning", color=(92, 122, 168), px=256, tile=(1.2, 1.2), gloss=0.20, painter=_awning_painter(s))
    a.add("sign_frame", color=(70, 72, 76), px=64, gloss=0.40, painter=DC._solid(1.6, 0.34, 0.46, s + 29))
    a.add("signs", px=1024, gloss=0.52, emissive=(255, 244, 222), painter=_signs_painter())
    a.add("vsign", px=256, gloss=0.50, emissive=(255, 244, 222), painter=_vsign_painter())
    a.add("address", px=256, gloss=0.48,
          painter=_plate_painter(f"addr_{spec.road_name}_{spec.road_no}", _draw_address(spec.road_name, spec.road_no)))
    a.add("lamp", color=(232, 220, 196), emissive=(255, 218, 156), px=32, gloss=0.62,
          painter=_dim(DC._solid(1.0, 0.56, 0.66, s + 31), EMIS_LAMP))
    return a


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------
def _skip_face(axis, side):
    if axis == "y":
        return "front" if side < 0 else "back"
    return "left" if side < 0 else "right"


def sign_uv(atlas, name):
    r0, r1 = _sign_layout()[name]
    H = float(SIGN_STRIP_H)
    return KX.uv_cell(atlas, "signs", 0.0, 1.0 - r1 / H, 1.0, 1.0 - r0 / H)


def sign_board(mb, axis, c, side, a0, a1, z0, z1, t, uv, region="signs", o0=0.0, frame=True):
    """간판 판재: 3D 판(두께 t) + 앞면 칸 UV. 앞면은 판 박스에서 빼고 따로 붙여 겹침 0."""
    K.axbox(mb, axis, c, side, a0, a1, o0, o0 + t, z0, z1, "sign_frame", skip=(_skip_face(axis, side),))
    mb.quad(K.face_pts(axis, c + side * (o0 + t), side, a0, a1, z0, z1), uv, region)


def solid_face(mb, pts, outward, region, stage):
    """볼록 다각형 면을 바깥 방향에 맞춰 감고 타일 UV 로 붙인다."""
    p = np.asarray(pts, float)
    n = np.cross(p[1] - p[0], p[-1] - p[0])
    if np.dot(n, outward) < 0:
        pts = list(pts)[::-1]
    DC.add_tiled_slope_poly(mb, pts, region, stage)


def prism_x(mb, poly_yz, x0, x1, region, stage, cap_region=None, skip_edges=()):
    """(y,z) 볼록 다각형을 x0..x1 로 뽑은 닫힌 입체 (차양용)."""
    n = len(poly_yz)
    cy = sum(p[0] for p in poly_yz) / n
    cz = sum(p[1] for p in poly_yz) / n
    for i in range(n):
        if i in skip_edges:
            continue
        (y0, z0), (y1, z1) = poly_yz[i], poly_yz[(i + 1) % n]
        out = np.array([0.0, (y0 + y1) / 2 - cy, (z0 + z1) / 2 - cz])
        solid_face(mb, [(x0, y0, z0), (x1, y0, z0), (x1, y1, z1), (x0, y1, z1)], out, region, stage)
    for x, sx in ((x0, -1.0), (x1, 1.0)):
        solid_face(mb, [(x, y, z) for (y, z) in poly_yz], np.array([sx, 0, 0]), cap_region or region, stage)


def prism_y(mb, poly_xz, y0, y1, region, stage, skip_edges=()):
    """(x,z) 볼록 다각형을 y0..y1 로 뽑은 닫힌 입체 (박공 파라펫용)."""
    n = len(poly_xz)
    cx = sum(p[0] for p in poly_xz) / n
    cz = sum(p[1] for p in poly_xz) / n
    for i in range(n):
        if i in skip_edges:
            continue
        (xa, za), (xb, zb) = poly_xz[i], poly_xz[(i + 1) % n]
        out = np.array([(xa + xb) / 2 - cx, 0.0, (za + zb) / 2 - cz])
        solid_face(mb, [(xa, y0, za), (xb, y0, zb), (xb, y1, zb), (xa, y1, za)], out, region, stage)
    for y, sy in ((y0, -1.0), (y1, 1.0)):
        solid_face(mb, [(x, y, z) for (x, z) in poly_xz], np.array([0, sy, 0]), region, stage)


def _rect_facing(mb, pts, outward, region):
    p = np.asarray(pts, float)
    if np.dot(np.cross(p[1] - p[0], p[-1] - p[0]), outward) < 0:
        pts = list(pts)[::-1]
    mb.rect(pts, region)


def awning_plate(mb, x0, x1, stage):
    """경사 천막 판: 윗면·밑면은 줄무늬 타일, 양 끝·앞 끝은 단색 면 (볼록 사각 단면 -> 클립 조각 없음)."""
    yw, yf = 0.0, -1.10
    zt0, zt1, t = 2.90, 2.62, 0.05
    DC.add_tiled_slope_poly(mb, [(x0, yf, zt1), (x1, yf, zt1), (x1, yw, zt0), (x0, yw, zt0)], "awning", stage)
    DC.add_tiled_slope_poly(mb, [(x1, yf, zt1 - t), (x0, yf, zt1 - t), (x0, yw, zt0 - t), (x1, yw, zt0 - t)], "awning", stage)
    _rect_facing(mb, [(x0, yf, zt1 - t), (x1, yf, zt1 - t), (x1, yf, zt1), (x0, yf, zt1)], (0, -1, 0), "awning")
    for x, sx in ((x0, -1.0), (x1, 1.0)):
        _rect_facing(mb, [(x, yw, zt0 - t), (x, yf, zt1 - t), (x, yf, zt1), (x, yw, zt0)], (sx, 0, 0), "awning")


def gable_parapet(mb, zb, zt, stage, xb=5.4, xt=1.8, y0=0.0, y1=WT):
    """박공형 파라펫 (사용자 사진 상부). 석재 타일 1.8 m 에 꼭짓점을 맞춰 클립 조각을 없앤다."""
    # 앞·뒤 면: 0.9 m 세로 띠로 나눠 띠마다 타일 1칸 안에 들게 한다 (클립 조각·영면적 면 0)
    def ztop(x):
        ax = abs(x)
        return zt if ax <= xt else zt - (zt - zb) * (ax - xt) / (xb - xt)
    n = int(round(2 * xb / 0.9))
    xs = [-xb + 2 * xb * k / n for k in range(n + 1)]
    for xa, xc in zip(xs, xs[1:]):
        for pts in ([(xa, y0, zb), (xc, y0, zb), (xc, y0, ztop(xc)), (xa, y0, ztop(xa))],
                    [(xc, y1, zb), (xa, y1, zb), (xa, y1, ztop(xa)), (xc, y1, ztop(xc))]):
            pts = [q for q in pts if q[2] > zb + 1e-6 or (q[0], q[2]) in ((xa, zb), (xc, zb))]
            pts = [q for i, q in enumerate(pts) if q not in pts[:i]]
            DC.add_tiled_slope_poly(mb, pts, "stone", stage)
    _rect_facing(mb, [(-xt, y0, zt), (xt, y0, zt), (xt, y1, zt), (-xt, y1, zt)], (0, 0, 1), "stone_brown")
    _rect_facing(mb, [(-xb, y0, zb), (-xt, y0, zt), (-xt, y1, zt), (-xb, y1, zb)], (-1, 0, 1), "stone_brown")
    _rect_facing(mb, [(xb, y0, zb), (xt, y0, zt), (xt, y1, zt), (xb, y1, zb)], (1, 0, 1), "stone_brown")


def steel_door_details(mb, axis, c, side, a0, a1, z0, z1, *, leaf_o=-0.10, fw=0.06, handle_right=True):
    """철제 방화문 디테일: 상·하 패널 요철, 킥플레이트, 레버 손잡이, 도어클로저.
    (korean-villa/villa_core.add_steel_door_details 와 같은 문법. 병렬 작업 폴더 의존을 피하려 복사)"""
    la0, la1, lz1 = a0 + fw, a1 - fw, z1 - fw
    w, h = la1 - la0, lz1 - z0
    K.axbox(mb, axis, c, side, la0 + 0.015, la1 - 0.015, leaf_o + 0.002, leaf_o + 0.010, z0 + 0.015, z0 + 0.14, "iron_dark")
    pm = min(0.11, w * 0.15)
    for pz0, pz1 in ((z0 + 0.22, z0 + h * 0.45), (z0 + h * 0.53, lz1 - 0.18)):
        K.axbox(mb, axis, c, side, la0 + pm, la1 - pm, leaf_o + 0.002, leaf_o + 0.014, pz0, pz1, "sash_dark")
        K.axbox(mb, axis, c, side, la0 + pm + 0.028, la1 - pm - 0.028, leaf_o + 0.014, leaf_o + 0.024,
                pz0 + 0.028, pz1 - 0.028, "door_wood")
    hx = (la1 - 0.095) if handle_right else (la0 + 0.095)
    hz = z0 + 0.96
    K.axbox(mb, axis, c, side, hx - 0.024, hx + 0.024, leaf_o + 0.002, leaf_o + 0.014, hz - 0.085, hz + 0.055, "iron_dark")
    K.axbox(mb, axis, c, side, hx - 0.011, hx + 0.011, leaf_o + 0.014, leaf_o + 0.052, hz - 0.011, hz + 0.011, "stainless")
    lx0, lx1 = (hx - 0.115, hx + 0.012) if handle_right else (hx - 0.012, hx + 0.115)
    K.axbox(mb, axis, c, side, lx0, lx1, leaf_o + 0.044, leaf_o + 0.062, hz - 0.011, hz + 0.011, "stainless")
    cx0, cx1 = (la0 + 0.08, la0 + 0.30) if handle_right else (la1 - 0.30, la1 - 0.08)
    K.axbox(mb, axis, c, side, cx0, cx1, leaf_o + 0.002, leaf_o + 0.042, lz1 - 0.095, lz1 - 0.025, "iron_dark")
    ax0, ax1 = (cx1 - 0.02, cx1 + 0.12) if handle_right else (cx0 - 0.12, cx0 + 0.02)
    K.axbox(mb, axis, c, side, ax0, ax1, leaf_o + 0.028, leaf_o + 0.046, lz1 - 0.052, lz1 - 0.004, "iron_dark")


def door_canopy(mb, axis, c, side, a0, a1, z, depth, stage, lamp=True):
    """출입문 위 콘크리트 캔틸레버 차양 (물끊기 턱) + 밑면 등."""
    if stage == 0:
        KX.ax_bevel(mb, axis, c, side, a0, a1, 0.0, depth, z, z + 0.10, "concrete_light", bevel=0.015)
        K.axbox(mb, axis, c, side, a0 + 0.01, a1 - 0.01, depth - 0.05, depth - 0.03, z - 0.025, z - 0.002, "concrete_light")
        if lamp:
            m = 0.5 * (a0 + a1)
            K.axbox(mb, axis, c, side, m - 0.09, m + 0.09, 0.14, 0.26, z - 0.022, z - 0.002, "lamp")
    else:
        K.axbox(mb, axis, c, side, a0, a1, 0.0, depth, z, z + 0.10, "concrete_light")


def _penthouse_door(mb, c, a0, a1, z0, z1, stage):
    """옥탑 계단실 철문 (-Y 면): 3D 문틀 + 문짝 + 패널·손잡이·클로저 + 문턱 + 차양·등."""
    if stage == 2:
        return
    fw = 0.06
    K.axbox(mb, "y", c, -1, a0, a1, 0.0, 0.06, z1 - fw, z1, "sash_dark")
    K.axbox(mb, "y", c, -1, a0, a0 + fw, 0.0, 0.06, z0 + 0.05, z1 - fw, "sash_dark")
    K.axbox(mb, "y", c, -1, a1 - fw, a1, 0.0, 0.06, z0 + 0.05, z1 - fw, "sash_dark")
    K.axbox(mb, "y", c, -1, a0 - 0.04, a1 + 0.04, 0.0, 0.10, z0, z0 + 0.05, "concrete_light", skip=("bottom",))
    K.axbox(mb, "y", c, -1, a0 + fw, a1 - fw, 0.0, 0.034, z0 + 0.05, z1 - fw, "door_wood")
    if stage == 0:
        steel_door_details(mb, "y", c, -1, a0, a1, z0 + 0.05, z1, leaf_o=0.034, fw=fw)
    door_canopy(mb, "y", c, -1, a0 - 0.15, a1 + 0.15, z1 + 0.22, 0.45, stage)


# ---------------------------------------------------------------------------
# 창·문 배치 (a0, a1, z0, z1, kind, floor, panes)
# ---------------------------------------------------------------------------
BAYS2 = ((-6.10, -2.30), (-1.90, 1.90), (2.30, 6.10))
def holes(spec):
    D = spec.depth
    z1, z2 = spec.z1, spec.z2
    f2 = (z1 + 0.40, z1 + 2.95)      # 2층 유리 4.60..7.15
    f3 = (z2 + 0.85, z2 + 2.85)      # 3층 띠창 8.45..10.45 (아래 석재 띠 글자)
    front = {
        0: [(-6.10, -4.70, 0.03, 2.75, "door_glass", 0, 2), (-4.40, -0.60, 0.50, 2.75, "window", 0, 3),
            (0.60, 4.40, 0.50, 2.75, "window", 0, 3), (4.70, 6.10, 0.03, 2.75, "door_glass", 0, 2)],
        # 2층: 칸마다 아래·위 유리 + 가운데 간판 띠(유리 글자 시트 자리) — 사용자 사진 2층 유리 간판
        1: [(h0, h1, zz0, zz1, "window", 1, 3) for (h0, h1) in BAYS2 for (zz0, zz1) in ((z1 + 0.40, z1 + 1.28), (z1 + 2.05, z1 + 2.95))],
        2: [(-6.10, -3.25, *f3, "window", 2, 2), (-2.95, -0.10, *f3, "window", 2, 2),
            (0.10, 2.95, *f3, "window", 2, 2), (3.25, 6.10, *f3, "window", 2, 2)],
    }
    right = {
        0: [(1.00, 4.60, 0.50, 2.75, "window", 0, 3)],
        1: [(1.00, 3.00, *f2[:1], f2[0] + 2.0, "window", 1, 2), (4.60, 6.60, f2[0], f2[0] + 2.0, "window", 1, 2),
            (8.60, 10.60, f2[0], f2[0] + 2.0, "window", 1, 2)],
        2: [(1.00, 3.00, z2 + 0.85, z2 + 2.65, "window", 2, 2), (4.60, 6.60, z2 + 0.85, z2 + 2.65, "window", 2, 2),
            (8.60, 10.60, z2 + 0.85, z2 + 2.65, "window", 2, 2)],
    }
    back = {
        0: [(-5.00, -3.80, 1.20, 2.30, "window", 0, 2), (2.60, 3.60, 0.03, 2.20, "door_solid", 0, 1)],
        1: [(-5.20, -3.40, z1 + 0.90, z1 + 2.30, "window", 1, 2), (-0.90, 0.90, z1 + 0.90, z1 + 2.30, "window", 1, 2),
            (3.40, 5.20, z1 + 0.90, z1 + 2.30, "window", 1, 2)],
        2: [(-5.20, -3.40, z2 + 0.90, z2 + 2.30, "window", 2, 2), (-0.90, 0.90, z2 + 0.90, z2 + 2.30, "window", 2, 2),
            (3.40, 5.20, z2 + 0.90, z2 + 2.30, "window", 2, 2)],
    }
    left = {   # 옆 건물과 붙는 쪽: 계단실 창만
        0: [],
        1: [(D - 3.20, D - 2.20, z1 + 1.40, z1 + 2.60, "window", 1, 2)],
        2: [(D - 3.20, D - 2.20, z2 + 1.40, z2 + 2.60, "window", 2, 2)],
    }
    return front, right, back, left


# ---------------------------------------------------------------------------
# 빌더
# ---------------------------------------------------------------------------
def build_stage(spec: ShopSpec, a: K.Atlas, stage: int):
    mb = K.MeshBuilder(a, split_tiles=(stage == 0))
    wins = K.WindowSet()
    W2, D = spec.width / 2.0, spec.depth
    x0, x1 = -W2, W2
    z1, z2, z3, zp = spec.z1, spec.z2, spec.z3, spec.z_par
    ledges = [(z1, z1 + 0.12), (z2, z2 + 0.12)]
    segs = [(0.0, z1), (z1 + 0.12, z2), (z2 + 0.12, z3)]
    front, right, back, left = holes(spec)

    if stage == 2:
        mb.box(x0, x1, 0.0, D, 0.0, zp, "stone", skip=("bottom",))
        mb.box(x0 - PIER_O, x0 + 0.60, -PIER_O, 0.0, 0.0, zp, "stone_brown", skip=("bottom",))
        mb.box(x1 - 0.60, x1 + PIER_O, -PIER_O, 0.0, 0.0, zp, "stone_brown", skip=("bottom",))
        gable_parapet(mb, zp, zp + 1.10, stage)   # LOD2 는 갓돌이 없어 본체 상단에 바로 얹는다
        mb.box(2.0, 5.0, 6.0, 9.0, zp, zp + 1.40, "stone", skip=("bottom",))
        for (axis, c, side), hs in ((("y", 0.0, -1), front), (("x", x1, 1), right), (("y", D, 1), back), (("x", x0, -1), left)):
            for fl in hs.values():
                for (h0, h1, hz0, hz1, *_r) in fl:
                    K.paint(mb, axis, c, side, h0, h1, hz0, hz1, "window_backing")
        # 1층 간판 (LOD2 에서도 원거리 인상 유지)
        K.paint(mb, "y", -PIER_O, -1, -6.30, -0.40, 2.95, 3.85, "sign_frame")
        return mb, wins

    rh = DC.add_recessed_wall
    faces = [("y", 0.0, -1, x0, x1, front, "stone"),
             ("x", x1, 1, WT, D - WT, right, "stone"),
             ("y", D, 1, x0, x1, back, "plaster"),
             ("x", x0, -1, WT, D - WT, left, "plaster")]
    for k, (axis, c, side, lo, hi, hs, reg) in enumerate(faces):
        for f, (za, zb) in enumerate(segs):
            sash = "sash_dark" if f == 0 and reg == "stone" else "sash"
            rh(mb, wins, axis, c, side, lo, hi, za, zb, reg, hs[f], stage, spec.seed + k * 5 + f,
               wall_t=WT, sash_reg=sash, reveal_reg="concrete_light")
        # 파라펫 (z3..zp)
        if axis == "y":
            K.axbox(mb, axis, c, side, lo, hi, -WT, 0.0, z3, zp, reg)
        else:
            K.axbox(mb, axis, c, side, lo, hi, -WT, 0.0, z3, zp, reg)
    # 실내 막음·옥상 바닥 (외벽 안쪽 2 cm)
    ci = WT + 0.02
    mb.box(x0 + ci, x1 - ci, ci, D - ci, 0.0, z3 - 0.11, "concrete_light", skip=("bottom",))
    mb.box(x0 + WT, x1 - WT, WT, D - WT, z3 - 0.10, z3, {"default": "concrete_light", "top": "roof_deck"})

    # 석재 띠 (모서리 감싸기, 규칙 8) + 파라펫 갓돌 (4변 링)
    for b0, b1 in ledges:
        mb.box(x0 - LEDGE_O, x1 + LEDGE_O, -LEDGE_O, D + LEDGE_O, b0, b1, "stone_brown")
    cw, co = WT + 0.04, 0.04
    zc = (zp, zp + 0.08)
    mb.box(x0 - co, x1 + co, -co - PIER_O, WT, *zc, "stone_brown")
    mb.box(x0 - co, x1 + co, D - WT, D + co, *zc, "stone_brown")
    mb.box(x0 - co, x0 + WT, WT, D - WT, *zc, "stone_brown")
    mb.box(x1 - WT, x1 + co, WT, D - WT, *zc, "stone_brown")

    # 정면 갈색 석재 기둥 (사용자 사진 좌·우), 모퉁이 측면 리턴
    mb.box(x0 - PIER_O, x0 + 0.60, -PIER_O, 0.0, 0.0, zp, "stone_brown", skip=("bottom",))
    mb.box(x1 - 0.60, x1 + PIER_O, -PIER_O, 0.0, 0.0, zp, "stone_brown", skip=("bottom",))
    mb.box(x1, x1 + PIER_O, 0.0, 0.60, 0.0, zp, "stone_brown", skip=("bottom",))
    # 1층 가운데 석재 기둥 (두 점포 경계)
    mb.box(-0.45, 0.45, -PIER_O, 0.0, 0.0, z1, "stone_brown", skip=("bottom",))

    # 박공 파라펫 (사용자 사진 상부 삼각 실루엣) + 작은 띠창 칠
    gable_parapet(mb, zp + 0.08, zp + 1.10, stage)
    if stage == 0:
        K.paint(mb, "y", 0.0, -1, -1.5, 1.5, zp + 0.40, zp + 0.70, "window_backing")
        K.axbox(mb, "y", 0.0, -1, -1.56, 1.56, 0.0, 0.03, zp + 0.34, zp + 0.40, "sash")
        K.axbox(mb, "y", 0.0, -1, -1.56, 1.56, 0.0, 0.03, zp + 0.70, zp + 0.76, "sash")

    # 옥탑 계단실 # estimated
    mb.box(2.0, 5.0, 6.0, 9.0, z3, z3 + 2.50, "plaster", skip=("bottom",))
    mb.box(1.94, 5.06, 5.94, 9.06, z3 + 2.50, z3 + 2.60, {"default": "stone_brown", "top": "concrete_light"})
    _penthouse_door(mb, 6.0, 3.0, 3.9, z3, z3 + 2.05, stage)

    # ---------------- 1층 간판·차양 (사용자 사진) ----------------
    ys = -PIER_O                    # 간판 뒷면: 기둥 앞면과 같은 선에서 시작 (판 두께 0.12)
    sign_board(mb, "y", 0.0, -1, -6.30, -0.50, 2.95, 3.85, 0.14, sign_uv(a, "sg_yellow"), o0=0.0)
    sign_board(mb, "y", 0.0, -1, 0.50, 6.30, 2.95, 3.85, 0.14, sign_uv(a, "sg_dark"), o0=0.0)
    # 파란 줄무늬 차양 (좌 점포): 벽 z 2.90 -> 앞 1.10 m z 2.62, 판 두께 5 cm + 앞 가림막 (닫힌 입체, 규칙 9·11).
    # 가림막 하단 2.50 m: 진열창·문 유리(머리 2.65)를 가리지 않게 (WIN_BLOCKED 0)
    ax0, ax1 = -6.25, -0.55
    awning_plate(mb, ax0, ax1, stage)
    mb.box(ax0, ax1, -1.10, -1.06, 2.48, 2.57, "awning")   # 판 앞 끝면(2.57~2.62) 아래에 맞대기
    if stage == 0:
        for xa in (-6.25, -4.55, -0.52):
            K.axbox(mb, "y", 0.0, -1, xa - 0.035, xa + 0.035, 0.0, 0.03, 2.18, 2.32, "iron_dark")
            DC.add_oct_tube(mb, (xa, -0.03, 2.25), (xa, -0.98, 2.575), 0.017, "iron_dark", n=6)
        # 벽 쪽 천막 걸이 레일 (판 윗면 2.90 위 5 mm, 간판 아래 5 mm)
        K.axbox(mb, "y", 0.0, -1, ax0, ax1, 0.0, 0.05, 2.905, 2.945, "iron_dark")

    # ---------------- 2층 유리 간판 띠 (아래·위 유리 사이 불투명 띠 위 글자 판) ----------------
    if stage == 0:
        for (h0, h1), nm in zip(BAYS2, ("sg_glass_l", "sg_glass_m", "sg_glass_r")):
            zg0, zg1 = z1 + 1.35, z1 + 1.98          # 아래 창 머리(1.28)·위 창대(2.005) 사이
            cx, hw = 0.5 * (h0 + h1), (zg1 - zg0) * 5.40 / 2.0
            sign_board(mb, "y", 0.0, -1, cx - hw, cx + hw, zg0, zg1, 0.012, sign_uv(a, nm), o0=0.0)

    # ---------------- 3층 아래 석재 띠 입체 글자 ----------------
    zs0 = z2 + 0.16
    sign_board(mb, "y", 0.0, -1, -5.60, 5.60, zs0, zs0 + 0.60, 0.05, sign_uv(a, "sg_stone"), o0=0.0)

    if stage == 0:
        # 3층 띠창 난간 (스텐 가로대 2줄 + 브래킷, 사용자 사진)
        zr = z2 + 0.85
        for (h0, h1, *_r) in front[2]:
            for zb in (zr + 0.38, zr + 0.70):
                K.axbox(mb, "y", 0.0, -1, h0 - 0.05, h1 + 0.05, 0.16, 0.21, zb, zb + 0.04, "stainless")
            for xb in (h0 + 0.10, 0.5 * (h0 + h1), h1 - 0.10):
                # 창대 앞면(0.052)에 맞댄 팔 + 가로대보다 얇은 기둥 (겹침 면 0)
                K.axbox(mb, "y", 0.0, -1, xb - 0.015, xb + 0.015, 0.052, 0.165, zr - 0.040, zr - 0.004, "stainless")
                K.axbox(mb, "y", 0.0, -1, xb - 0.015, xb + 0.015, 0.165, 0.205, zr - 0.040, zr + 0.72, "stainless")

        # 모퉁이 세로 돌출 간판 (+X 측면 앞쪽, 2~3층)
        vx0, vx1, vy0, vy1 = x1 + PIER_O, x1 + PIER_O + VSIGN_W, 0.62, 0.80
        vz0 = z1 + 0.60; vz1 = vz0 + VSIGN_H        # 4.80..7.80 (2층~3층 띠 높이)
        mb.box(vx0, vx1, vy0, vy1, vz0, vz1, "sign_frame", skip=("front", "back"))
        uv = a.uv_full("vsign")
        mb.quad([(vx0, vy0, vz0), (vx1, vy0, vz0), (vx1, vy0, vz1), (vx0, vy0, vz1)], uv, "vsign")   # -Y 면
        mb.quad([(vx1, vy1, vz0), (vx0, vy1, vz0), (vx0, vy1, vz1), (vx1, vy1, vz1)], uv, "vsign")   # +Y 면
        for zb in (vz0 + 0.30, vz1 - 0.35):
            mb.box(x1, vx0, 0.68, 0.74, zb, zb + 0.05, "iron_dark")

        # 번호판 (우측 기둥 앞, 규칙 20)
        sign_board(mb, "y", -PIER_O, -1, x1 - 0.48, x1 - 0.21, 1.70, 1.92, 0.014, a.uv_full("address"), region="address")

        # 실외기: 측면 2·3층, 후면 각 층, 옥상 2대
        for zf in (z1, z2):
            DC.add_ac_unit(mb, "x", x1, 1, 7.60, zf + 0.30, stage)
            DC.add_ac_unit(mb, "y", D, 1, 1.80, zf + 0.30, stage)
        DC.add_ac_unit(mb, "y", D, 1, -1.80, 0.0, stage)
        for xa in (-4.6, -2.6):
            mb.box(xa - 0.45, xa + 0.45, 7.20, 7.55, z3, z3 + 0.75, "equip_gray", skip=("bottom",))
            K.paint(mb, "y", 7.20, -1, xa - 0.40, xa + 0.40, z3 + 0.06, z3 + 0.70, "louver")
        # 우수관 (후면 양 모서리)
        for xd in (x0 + 0.40, x1 - 0.40):
            DC.add_downspout(mb, "y", D, 1, xd, 0.0, z3 + 0.6)
    _detail_pass(mb, spec, stage, front, right, back)
    return mb, wins


def _sill(mb, axis, c, side, a0, a1, ztop, reg, stage, depth=0.07, h=0.06):
    """창대 (DC 창 하부 림 아래 2 mm). main 은 모따기."""
    if stage == 0:
        KX.ax_bevel(mb, axis, c, side, a0 - 0.08, a1 + 0.08, 0.0, depth, ztop - h, ztop, reg, bevel=0.012)
    else:
        K.axbox(mb, axis, c, side, a0 - 0.08, a1 + 0.08, 0.0, depth, ztop - h, ztop, reg)


def _detail_pass(mb, spec, stage, front, right, back):
    """11-24 인게임 '디테일 아쉬움' 보강: 상가 전면 (셔터박스·가이드레일·걸레받이·간판 테·문 손잡이/중간대/문턱),
    상층 창대·인방, 코핑 아래 띠, 측·후면 실외기 배관, 후면 계단실 철문·차양."""
    W2, D = spec.width / 2.0, spec.depth
    x0, x1 = -W2, W2
    z1, z2, zp = spec.z1, spec.z2, spec.z_par
    main = stage == 0

    # ---- 1층 상가 전면 ----
    for (a0, a1, hz0, hz1, kind, *_r) in front[0]:
        if kind == "window":   # 진열창 아래 화강석 걸레받이 (DC 창 림 0.455 아래)
            K.axbox(mb, "y", 0.0, -1, a0 - 0.02, a1 + 0.02, 0.0, 0.035, 0.0, hz0 - 0.05, "stone_brown", skip=("bottom",))
        else:                  # 유리문 화강석 문턱
            K.axbox(mb, "y", 0.0, -1, a0, a1, 0.002, 0.24, 0.0, 0.03, "stone_brown", skip=("bottom",))
        if a0 > 0.0:           # 우측 점포 셔터 가이드 레일 (창 림 바깥)
            for r0 in (a0 - 0.08, a1 + 0.035):
                K.axbox(mb, "y", 0.0, -1, r0, r0 + 0.045, 0.0, 0.06, 0.0, 2.76, "iron_dark", skip=("bottom",))
        if main and kind == "door_glass":
            mid, fw = 0.5 * (a0 + a1), 0.075
            # 중간 가로대 (중앙 세로살과 맞대기)
            for t0, t1 in ((a0 + fw, mid - 0.028), (mid + 0.028, a1 - fw)):
                K.axbox(mb, "y", 0.0, -1, t0, t1, -0.125, -0.045, 2.20, 2.255, "sash_dark")
            # 긴 스테인리스 당김 손잡이 + 받침
            for hx in (mid - 0.12, mid + 0.12):
                K.axbox(mb, "y", 0.0, -1, hx - 0.0125, hx + 0.0125, -0.030, -0.006, 0.72, 1.78, "stainless")
                for hz in (0.80, 1.70):
                    K.axbox(mb, "y", 0.0, -1, hx - 0.010, hx + 0.010, -0.045, -0.030, hz - 0.010, hz + 0.010, "stainless")
    # 우측 점포 셔터 박스 (창·문 머리 2.75 위, 간판 2.95 아래) + 밑면 등
    sb0, sb1 = 0.55, 6.15
    if main:
        KX.ax_bevel(mb, "y", 0.0, -1, sb0, sb1, 0.0, 0.20, 2.76, 2.94, "sash", bevel=0.012)
        for xl in (2.5, 5.4):
            K.axbox(mb, "y", 0.0, -1, xl - 0.08, xl + 0.08, 0.06, 0.14, 2.745, 2.758, "lamp")
    else:
        K.axbox(mb, "y", 0.0, -1, sb0, sb1, 0.0, 0.20, 2.76, 2.94, "sash")
    # 1층 간판 테 (판 앞면 둘레 몰딩 -> 상자 간판 입체감)
    if main:
        for g0, g1 in ((-6.30, -0.50), (0.50, 6.30)):
            o0, o1, e = 0.14, 0.165, 0.045
            K.axbox(mb, "y", 0.0, -1, g0, g1, o0, o1, 2.95, 2.95 + e, "stainless")
            K.axbox(mb, "y", 0.0, -1, g0, g1, o0, o1, 3.85 - e, 3.85, "stainless")
            K.axbox(mb, "y", 0.0, -1, g0, g0 + e, o0, o1, 2.95 + e, 3.85 - e, "stainless")
            K.axbox(mb, "y", 0.0, -1, g1 - e, g1, o0, o1, 2.95 + e, 3.85 - e, "stainless")

    # ---- 상층 창대·인방 ----
    for (h0, h1, hz0, hz1, *_r) in front[1]:
        if hz0 < z1 + 1.0:      # 2층 아래 유리: 창대
            _sill(mb, "y", 0.0, -1, h0, h1, hz0 - 0.047, "stone_brown", stage)
        else:                   # 2층 위 유리: 인방 (아래는 유리 간판)
            K.axbox(mb, "y", 0.0, -1, h0 - 0.06, h1 + 0.06, 0.0, 0.04, hz1 + 0.005, hz1 + 0.085, "stone_brown")
    for (h0, h1, hz0, hz1, *_r) in front[2]:   # 3층 띠창: 인방 (창대 자리는 난간 팔·석재 글자 띠)
        K.axbox(mb, "y", 0.0, -1, h0 - 0.06, h1 + 0.06, 0.0, 0.04, hz1 + 0.005, hz1 + 0.085, "stone_brown")
    for f in (1, 2):
        for (h0, h1, hz0, hz1, *_r) in right[f]:
            _sill(mb, "x", x1, 1, h0, h1, hz0 - 0.047, "stone_brown", stage)
            K.axbox(mb, "x", x1, 1, h0 - 0.06, h1 + 0.06, 0.0, 0.04, hz1 + 0.005, hz1 + 0.085, "stone_brown")
        for (h0, h1, hz0, hz1, *_r) in back[f]:
            _sill(mb, "y", D, 1, h0, h1, hz0 - 0.047, "concrete_light", stage)
    # 측면 1층 진열창 걸레받이
    for (a0, a1, hz0, hz1, *_r) in right[0]:
        K.axbox(mb, "x", x1, 1, a0 - 0.02, a1 + 0.02, 0.0, 0.035, 0.0, hz0 - 0.05, "stone_brown", skip=("bottom",))

    # ---- 코핑 아래 2단 띠 (모서리: 후면 띠가 감싸고 측면 띠는 맞댐) ----
    zb0, ob = zp - 0.10, 0.025
    K.axbox(mb, "y", 0.0, -1, x0 + 0.60, x1 - 0.60, 0.0, ob, zb0, zp, "stone_brown")
    mb.box(x0 - ob, x1 + ob, D, D + ob, zb0, zp, "stone_brown")
    mb.box(x1, x1 + ob, 0.602, D, zb0, zp, "stone_brown")
    mb.box(x0 - ob, x0, 0.002, D, zb0, zp, "stone_brown")

    # ---- 후면 계단실 철문 + 차양 ----
    for (a0, a1, hz0, hz1, kind, *_r) in back[0]:
        if kind == "door_solid":
            if main:
                steel_door_details(mb, "y", D, 1, a0 + 0.06, a1 - 0.06, hz0, hz1 - 0.06, leaf_o=-0.10, fw=0.0,
                                   handle_right=False)
                K.axbox(mb, "y", D, 1, a0 - 0.03, a1 + 0.03, 0.002, 0.24, 0.0, 0.03, "concrete_light", skip=("bottom",))
            door_canopy(mb, "y", D, 1, a0 - 0.30, a1 + 0.30, hz1 + 0.18, 0.70, stage)

    if not main:
        return
    # ---- 실외기 추가 (측면 1층) + 냉매관 입상 덕트 (석재 띠에서 끊어 맞댐) ----
    DC.add_ac_unit(mb, "x", x1, 1, 5.60, 0.0, stage)
    for axis, c, side, pos in (("x", x1, 1, 7.60), ("y", D, 1, 1.80)):
        d0, d1 = pos + 0.41, pos + 0.49
        for za, zb in ((z1 + 0.30 + 0.85, z2), (z2 + 0.12, z2 + 0.30 + 0.10)):
            K.axbox(mb, axis, c, side, d0, d1, 0.0, 0.07, za, zb, "pipe_white")


def build_and_export(spec: ShopSpec, out_root=None):
    a = build_atlas(spec)
    main, wins = build_stage(spec, a, 0)
    l1, _ = build_stage(spec, a, 1)
    l2, _ = build_stage(spec, a, 2)
    folder, result = K.export_asset(
        spec.name, 1, dict(main=main, lod1=l1, lod2=l2, windows=wins), a,
        out_root or K.out_dir_from_argv("output"), lod2_tex=512, lot=spec.lot, front_yard=spec.front_yard,
        notes=dict(archetype="corner_shop_3f_gable", seed=spec.seed))
    print(f"[shop_core] {result['asset']}: main={main.tri_count} lod1={l1.tri_count} "
          f"lod2={l2.tri_count} wins={len(wins.items)} (lod2+2w={l2.tri_count + len(wins.items) * 2})")
    return folder, result
