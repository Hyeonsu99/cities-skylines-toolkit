# -*- coding: utf-8 -*-
"""cs2-kit 로컬 확장. 원본 cs2kit.py 는 고치지 않는다 (git subtree 업스트림 충돌 방지).

생성기에서:  import cs2kit as K;  from local import kitext as KX
모두 opt-in: 부르는 생성기에만 적용되고 기존 에셋은 바뀌지 않는다.

1. 위치 기반 오염·그늘  add_grime_cells() + grime_band() / under_shadow()
2. 모서리 베벨          bevel_box()
3. 개구부 옆면 재질      paint_reveal()
4. 단색 칸 기본 질감     solid_weather(), stone_trim()   (Atlas.add(painter=...) 에 넘김)
5. 알베도 상한 검사      저장소 루트 tools/albedo_check.py (sync_cs2_import.py 가 자동 실행)
"""
import math

import numpy as np

import cs2kit as K


# ---------------------------------------------------------------------------
# 공용: 지정한 바깥 방향을 보도록 사각형 꼭짓점 순서를 맞춘다
# ---------------------------------------------------------------------------
def _facing(pts, normal):
    p0, p1, _, p3 = (np.asarray(p, float) for p in pts)
    if np.dot(np.cross(p1 - p0, p3 - p0), normal) < 0:
        return [pts[1], pts[0], pts[3], pts[2]]
    return pts


def _wall_pt(axis, c, s, a, o, z):
    """벽면 좌표(a: 벽을 따라, o: 바깥쪽 거리) -> 월드 좌표."""
    return (a, c + s * o, z) if axis == "y" else (c + s * o, a, z)


def _axis_vec(axis, which):
    """axis='y' 벽: 벽을 따르는 방향 = x, 바깥 방향 = y. axis='x' 벽은 반대."""
    along = (1.0, 0.0, 0.0) if axis == "y" else (0.0, 1.0, 0.0)
    out = (0.0, 1.0, 0.0) if axis == "y" else (1.0, 0.0, 0.0)
    return np.array(along if which == "along" else out)


# ---------------------------------------------------------------------------
# 1. 위치 기반 오염·그늘 (알파 컷아웃 칠 면, 벽 전체 폭 기준이라 타일 반복과 무관)
# ---------------------------------------------------------------------------
def _grime_painter(mode, seed):
    def painter(ctx):
        base = ctx.rgb[0, 0].copy()
        n1 = ctx.noise(scale_px=12, amp=1.0, octaves=3, seed=501 + seed * 7)
        n2 = ctx.noise(scale_px=4, amp=1.0, octaves=2, seed=509 + seed * 11)
        if mode == "bot":        # 지면 튐·습기: 아래로 갈수록 진함
            dens = np.clip(1.0 - ctx.v * 1.1, 0.0, 1.0)
            mask = dens * 0.75 + 0.20 * n1 + 0.14 * n2 > 0.60
        elif mode == "under":    # 처마·차양·슬래브 아래 그늘: 위로 갈수록 진함, 세로 빗물 줄
            col = ctx.noise(scale_px=5, amp=1.0, octaves=2, seed=521 + seed).mean(axis=0, keepdims=True)
            dens = np.clip(ctx.v * 1.1 - 0.05, 0.0, 1.0)
            mask = dens * 0.78 + 0.22 * col + 0.14 * n1 + 0.10 * n2 > 0.58
        else:                    # "streak": 창대·코핑 아래 흘러내린 자국
            stripes = 0.5 + 0.25 * (np.sin(ctx.u * 61 + seed) + np.sin(ctx.u * 97 + 2 * seed))
            mask = stripes * (0.30 + 0.70 * ctx.v) + 0.15 * n1 > 0.60
        ctx.alpha[...] = np.where(mask, 255, 0)
        ctx.rgb[...] = base * (0.86 + 0.12 * n1[..., None] + 0.06 * n2[..., None])
        ctx.height[...] = 0.05 * n2
        ctx.gloss[...] = np.clip(0.13 + 0.03 * n1, 0.08, 0.20)
    return painter


def add_grime_cells(atlas, color=(66, 62, 54), seed=0, px=128):
    """오염 칸 3종(kx_grime_bot / kx_grime_under / kx_grime_streak, 각 2변형)을 아틀라스에 등록."""
    for mode in ("bot", "under", "streak"):
        atlas.add(f"kx_grime_{mode}", color=color, px=px, variants=2, gloss=0.14,
                  painter=_grime_painter(mode, seed))


def grime_band(mb, axis, c, s, a0, a1, z0, z1, mode="bot", blocked=(), layer=2, variant=0, end_trim=0.02):
    """벽 앞 오염 띠. blocked = [(a0, a1), ...] 개구부·부착물 구간은 비운다. 끝은 모서리에서 end_trim 만큼 줄인다."""
    spans = [(a0 + end_trim, a1 - end_trim)]
    for b0, b1 in blocked:
        nxt = []
        for s0, s1 in spans:
            if b1 <= s0 or b0 >= s1:
                nxt.append((s0, s1))
                continue
            if b0 > s0 + 0.08:
                nxt.append((s0, b0))
            if b1 < s1 - 0.08:
                nxt.append((b1, s1))
        spans = nxt
    uv = mb.atlas.uv_full(f"kx_grime_{mode}", variant=variant)
    for s0, s1 in spans:
        if s1 - s0 > 0.12:
            mb.quad(K.face_pts(axis, c + s * K.PAINT_OFF * layer, s, s0, s1, z0, z1), uv, f"kx_grime_{mode}")


def under_shadow(mb, axis, c, s, a0, a1, z_top, depth=0.35, layer=2, variant=1):
    """처마·차양·슬래브 바로 아래 벽에 그늘 띠 (z_top 은 돌출부 아랫면 높이)."""
    grime_band(mb, axis, c, s, a0, a1, z_top - depth, z_top, mode="under", layer=layer, variant=variant, end_trim=0.0)


def streak_below(mb, axis, c, s, a0, a1, z_top, length=0.45, layer=2, variant=0):
    """창대·코핑 아래 흘러내린 자국."""
    grime_band(mb, axis, c, s, a0, a1, z_top - length, z_top, mode="streak", layer=layer, variant=variant, end_trim=0.0)


# ---------------------------------------------------------------------------
# 2. 모서리 베벨 박스 (세로 4모서리 + 윗면 테두리 45도 모따기)
# ---------------------------------------------------------------------------
def _chamfer_rect(x0, x1, y0, y1, ch):
    ch = max(0.0, min(ch, (x1 - x0) * 0.45, (y1 - y0) * 0.45))
    if ch <= 1e-6:
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [(x0 + ch, y0), (x1 - ch, y0), (x1, y0 + ch), (x1, y1 - ch),
            (x1 - ch, y1), (x0 + ch, y1), (x0, y1 - ch), (x0, y0 + ch)]


def _inset(poly, d):
    """반시계 볼록 다각형을 d 만큼 안쪽으로 평행 이동 (변이 평행하게 유지돼 모따기 면이 평면)."""
    n = len(poly)
    lines = []
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        L = math.hypot(ex, ey)
        nx, ny = -ey / L, ex / L              # 왼쪽 법선 = 안쪽 (반시계)
        lines.append(((ax + nx * d, ay + ny * d), (ex, ey)))
    out = []
    for i in range(n):
        (p, r), (q, t) = lines[i - 1], lines[i]
        den = r[0] * t[1] - r[1] * t[0]
        u = ((q[0] - p[0]) * t[1] - (q[1] - p[1]) * t[0]) / den
        out.append((p[0] + r[0] * u, p[1] + r[1] * u))
    return out


def bevel_box(mb, x0, x1, y0, y1, z0, z1, region, bevel=0.03, edge_region=None, bottom=False):
    """모서리를 모따기한 박스. 실루엣 모서리에 하이라이트 띠가 생긴다 (박스 12 tris -> 약 40 tris).
    매스 외곽·파라펫·기단·창대처럼 눈에 띄는 큰 부재에만 쓴다."""
    b = max(0.0, min(bevel, (x1 - x0) * 0.3, (y1 - y0) * 0.3, (z1 - z0) * 0.45))
    edge = edge_region or region
    ring = _chamfer_rect(x0, x1, y0, y1, b)
    top_ring = _inset(ring, b) if b > 1e-6 else ring
    zb = z1 - b
    n = len(ring)
    for i in range(n):
        (ax, ay), (bx, by) = ring[i], ring[(i + 1) % n]
        side = [(ax, ay, z0), (bx, by, z0), (bx, by, zb), (ax, ay, zb)]
        big = math.hypot(bx - ax, by - ay) > 2.5 * b + 1e-6
        if big:
            mb.rect(side, region)
        else:
            mb.quad(side, mb.atlas.uv(edge), edge)
        if b > 1e-6:
            (cx, cy), (dx, dy) = top_ring[i], top_ring[(i + 1) % n]
            mb.quad([(ax, ay, zb), (bx, by, zb), (dx, dy, z1), (cx, cy, z1)], mb.atlas.uv(edge), edge)
    uv = mb.atlas.uv(region)
    for i in range(1, len(top_ring) - 1):
        mb.tri([(*top_ring[0], z1), (*top_ring[i], z1), (*top_ring[i + 1], z1)], uv[:3], region)
    if bottom:
        for i in range(1, n - 1):
            mb.tri([(*ring[0], z0), (*ring[i + 1], z0), (*ring[i], z0)], uv[:3], region)


def ax_bevel(mb, axis, c, s, a0, a1, o0, o1, z0, z1, region, bevel=0.025, edge_region=None):
    """벽에 붙은 부재(창대·인방·차양 등)를 bevel_box 로. 인자는 K.axbox 와 같다."""
    lo, hi = sorted((c + s * o0, c + s * o1))
    if axis == "y":
        bevel_box(mb, a0, a1, lo, hi, z0, z1, region, bevel, edge_region, bottom=True)
    else:
        bevel_box(mb, lo, hi, a0, a1, z0, z1, region, bevel, edge_region, bottom=True)


def uv_cell(atlas, name, fu0, fv0, fu1, fv1, margin=0.5):
    """칸 전체(변형 여러 개를 이어 붙인 넓은 칸 포함) 안의 비율 영역 UV.
    간판·번호판처럼 칸을 통째로 한 그림으로 쓸 때. A.uv() 는 칸 가운데 절반만, uv_sub 는 변형 하나만 쓴다.
    painter 는 ctx.u 0~1 (칸 전체 너비) 기준으로 그린다."""
    atlas.layout()
    x, y, w, h = atlas.cells[name]["rect"]
    S, e = float(atlas.size), margin / atlas.size
    u0, u1 = x / S + e, (x + w) / S - e
    v0, v1 = 1.0 - (y + h) / S + e, 1.0 - y / S - e
    U = lambda f: u0 + (u1 - u0) * f
    V = lambda f: v0 + (v1 - v0) * f
    return [(U(fu0), V(fv0)), (U(fu1), V(fv0)), (U(fu1), V(fv1)), (U(fu0), V(fv1))]


# ---------------------------------------------------------------------------
# 3. 개구부 옆면(측벽·인방 밑·창대 위) 재질 — 벽 타일이 옆면에 늘어져 보이는 것을 덮는다
# ---------------------------------------------------------------------------
def paint_reveal(mb, axis, c, s, a0, a1, z0, z1, depth, region, inset=0.004, sill=True, head=True):
    """개구부(a0..a1, z0..z1, 벽 두께 depth)의 안쪽 면에 칠 면 4장.
    벽 바깥면에서 depth 만큼 안쪽까지 덮는다. 문이면 sill=False."""
    along = _axis_vec(axis, "along")
    up = np.array((0.0, 0.0, 1.0))
    o_in, o_out = -depth, 0.0
    faces = [((a0 + inset, a0 + inset, z0, z1), along),        # 왼쪽 측벽: 개구부 안쪽(+along)을 본다
             ((a1 - inset, a1 - inset, z0, z1), -along)]
    for (aa, ab, za, zb), nrm in faces:
        pts = [_wall_pt(axis, c, s, aa, o_in, za), _wall_pt(axis, c, s, aa, o_out, za),
               _wall_pt(axis, c, s, aa, o_out, zb), _wall_pt(axis, c, s, aa, o_in, zb)]
        mb.rect(_facing(pts, nrm), region)
    for zz, nrm, on in ((z1 - inset, -up, head), (z0 + inset, up, sill)):
        if not on:
            continue
        pts = [_wall_pt(axis, c, s, a0, o_in, zz), _wall_pt(axis, c, s, a1, o_in, zz),
               _wall_pt(axis, c, s, a1, o_out, zz), _wall_pt(axis, c, s, a0, o_out, zz)]
        mb.rect(_facing(pts, nrm), region)


# ---------------------------------------------------------------------------
# 4. 단색 칸 기본 질감 (Atlas.add(painter=...) 로 넘김)
# ---------------------------------------------------------------------------
def solid_weather(grain=3.0, stain=0.06, gloss_amp=0.05, seed=0):
    """단색 칸용: 미세 결 + 얼룩 + 광택 변주.
    주의: 단색 칸은 면 크기와 무관하게 칸 가운데 절반(uv inset 0.25)을 늘여 쓴다. 1 m 넘는 면이 많은
    재질(콘크리트 차양·코핑 등)은 Atlas.add(tile=(1.2, 1.2)) 타일 재질로 바꾸고 stone_trim 을 쓴다."""
    def painter(ctx):
        ctx.grain(amp=grain, scale_px=2, height=0.06, seed=601 + seed)
        k = ctx.stains(amount=stain, scale_px=max(8, ctx.w // 6), streaks=0.15, seed=607 + seed)
        n = ctx.noise(scale_px=max(4, ctx.w // 10), amp=1.0, octaves=2, seed=613 + seed)
        ctx.gloss[...] = np.clip(ctx.gloss + gloss_amp * np.tanh(n * 0.7) - 0.05 * k, 0.05, 0.95)
    return painter


def stone_trim(seed=0):
    """석재·콘크리트 창대·인방·차양: 굵은 반점 + 기공 + 얼룩."""
    def painter(ctx):
        ctx.grain(amp=7.0, scale_px=2, height=0.25, seed=631 + seed)
        pores = ctx.noise(scale_px=1, amp=1.0, octaves=1, seed=637 + seed) > 2.2
        ctx.rgb[pores] *= 0.72
        ctx.height[pores] -= 0.3
        k = ctx.stains(amount=0.10, scale_px=max(8, ctx.w // 5), streaks=0.35, seed=641 + seed)
        n = ctx.noise(scale_px=6, amp=1.0, octaves=2, seed=643 + seed)
        ctx.gloss[...] = np.clip(0.24 + 0.04 * np.tanh(n) - 0.06 * k, 0.10, 0.34)
    return painter
