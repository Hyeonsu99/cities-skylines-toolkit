# -*- coding: utf-8 -*-
"""덕암동 실사 기반 B01 대표형. 사진·추정 차이는 shape_notes.md 참고."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import villa_core as V

K, DC = V.K, V.DC
SPEC = V.VillaSpec(name="SintanjinVillaB01", lot=(2, 3), width=11.6, depth=12.0,
                   z_pil=2.45, road_no="31", seed=13)


def build_stage(spec, atlas, stage):
    mb, wins = K.MeshBuilder(atlas, split_tiles=stage == 0), K.WindowSet()
    x0, x1, D = -spec.width / 2, spec.width / 2, spec.depth
    zp, zu, zroof = spec.z_pil, 3.10, 11.40
    # Left-of-centre stair core leaves one parking bay left, two right (b08_left/right).
    ca, cb, rear = -3.10, -0.70, 8.0
    cols = [(x, y) for x in (x0 + .25, x1 - .25) for y in (.25, 5.70)]
    # 11/24 인게임 피드백: 8 m 길이 현관 코어를 없애고 공동현관을 주차 후면 벽(y=rear) 라인으로 옮김.
    # 계단실 코어 아래는 기둥 2열이 받치는 보행 통로(폭 1.4 m)가 된다.
    walk_cols = [(x, y) for x in (ca + .25, cb - .25) for y in (.25, 5.70)]
    ent = (ca + .48, cb - .48, .02, 2.24)          # 공동현관 개구부 (후면 벽)
    svc = (9.40, 10.30, .02, 2.10)                  # 보조문: 후면실 우측 벽(측면 마당)
    for x, y in cols + (walk_cols if stage < 2 else []):
        if stage == 0:
            V.KX.bevel_box(mb, x-.25, x+.25, y-.25, y+.25, 0, zp, "granite", bevel=.018)
        else:
            mb.box(x-.25, x+.25, y-.25, y+.25, 0, zp, "granite", skip=("bottom",))
    # One wraparound closed slab, no white inter-floor ribbons or A roof.
    mb.box(x0-.08, x1+.08, -.08, D+.08, zp, zu, "granite")
    front = [(-5.10, -3.65, .90, 2.28, 2), (-.10, 1.40, 1.16, 2.28, 2),
             (2.35, 4.65, .90, 2.28, 3)]
    side = [(1.1, 3.3, .90, 2.28, 3), (4.65, 5.80, 1.20, 2.28, 2),
            (7.25, 9.45, .90, 2.28, 3), (10.25, 11.30, 1.20, 2.28, 2)]
    back = [(-4.85, -2.70, .90, 2.28, 3), (-1.00, .20, 1.20, 2.28, 2),
            (2.25, 4.45, .90, 2.28, 3)]
    faces = [("y", 0, -1, x0, x1, front),
             ("x", x0, -1, .22, D-.22, side),
             ("x", x1, 1, .22, D-.22, side),
             ("y", D, 1, x0, x1, back)]
    if stage == 2:
        mb.box(x0, x1, rear, D, 0, zp, "wall_main", skip=("bottom",))
        K.paint(mb, "y", rear, -1, ent[0], ent[1], ent[2], ent[3], "window_backing")
        mb.box(x0, x1, 0, D, zu, zroof+.90, "wall_main", skip=("bottom",))
        # 옥탑 매스 (좌측 계단실 코어 상부)
        mb.box(ca, cb, 0.55, 3.75, zroof+.14, zroof+2.50, "wall_main", skip=("bottom",))
        K.paint(mb, "y", 0, -1, ca+.45, cb-.45, zu+.10, zroof-.10, "window_backing")
        for axis, c, s, lo, hi, hs in faces:
            for f in range(3):
                z = 3 + f*2.8
                for a, b, sill, head, panes in hs:
                    K.paint(mb, axis, c, s, a, b, z+sill, z+head, "window_backing")
    else:
        rh = DC.add_recessed_wall
        lit_win_indices = []
        # 주차 후면 벽: 공동현관(통로 정면) + 창, 카스토퍼 라인과 같은 깊이
        V.wall_with_doors(mb, wins, "y", rear, -1, x0, x1, 0, zp, "wall_main",
                          [(-4.8, -3.8, 1.20, 2.10, "window", 0, 2)], stage, 15, [ent])
        V.add_glass_entry_door(mb, wins, "y", rear, -1, *ent, stage, unit=71, lit=lit_win_indices)
        rh(mb, wins, "x", x0, -1, rear+.22, D-.22, 0, zp, "wall_main", [], stage, 16)
        V.wall_with_doors(mb, wins, "x", x1, 1, rear+.22, D-.22, 0, zp, "wall_main", [], stage, 18, [svc])
        V.add_steel_door(mb, "x", x1, 1, *svc, stage, handle_right=False)
        rh(mb, wins, "y", D, 1, x0, x1, 0, zp, "wall_main",
           [(-4.5,-3.4,1.20,2.10,"window",0,2),(2.1,3.2,1.20,2.10,"window",0,2)], stage, 17)
        mb.box(x0+.24, x1-.24, rear+.24, D-.24, 0, zp-.01, "concrete_light", skip=("bottom",))
        for k, (axis,c,s,lo,hi,hs) in enumerate(faces):
            holes = [(a,b,3+f*2.8+sill,3+f*2.8+head,"window",f+1,panes)
                     for f in range(3) for a,b,sill,head,panes in hs]
            if k == 0:
                # Continuous dark stair glazing, opening through the brick rather than painted on it.
                holes.append((ca+.45,cb-.45,zu+.12,zroof-.10,"window",1,1))
            w_pre = len(wins.items)
            rh(mb,wins,axis,c,s,lo,hi,zu,zroof+.90,"wall_main",holes,stage,30+k)
            if k == 0 and stage == 0 and len(wins.items) > w_pre:
                # 좌측 4층 수직 계단실 유리 띠를 3개 층별 발광 패널로 교체해 상시·층별 점등 보장
                wins.items.pop()
                st_a0, st_a1 = ca + .45, cb - .45
                g0, g1 = st_a0 + 0.095 * 0.80, st_a1 - 0.095 * 0.80
                for sf, (gz0, gz1) in enumerate(((zu + .20, 5.55), (5.61, 8.35), (8.41, zroof - .18)), start=1):
                    wins.add_face("y", 0.145, -1, g0, g1, gz0, gz1, sf, 80 + sf)
                    wins.items[-1]["pts2"] = K.face_pts("y", -0.025, -1, st_a0 + 0.05, st_a1 - 0.05, gz0, gz1)
                    lit_win_indices.append(len(wins.items) - 1)
        mb.box(x0+.24,x1-.24,.24,D-.24,zu+.01,zroof,"wall_main")
        # Dark aluminium cross-mullions at half-landings, in front of the glass faces (clear of pane centers).
        for z in (4.10,5.55,6.85,8.35,9.65,11.15):
            K.axbox(mb,"y",0,-1,ca+.55,cb-.55,-.115,-.02,z,z+.055,"sash_dark")
        # Closed parapet above the filled roof deck; caps wrap corners by abutting.
        zdeck = zroof + .14
        mb.box(x0+.219,x1-.219,.219,D-.219,zroof,zdeck,"roof_deck")
        # 옥상 계단실 옥탑 (좌측 코어 상부, 차콜 벽돌 + 흑화강석 갓돌 + 철제 방화문) # estimated
        px0, px1, py0, py1, ph = ca, cb, 0.55, 3.75, 2.36
        zt = zdeck + ph - 0.20
        mb.box(px0, px1, py0, py1, zdeck, zt, "wall_main", skip=("bottom",))
        mb.box(px0 - 0.05, px1 + 0.05, py0 - 0.05, py1 + 0.05, zt, zdeck + ph, "granite")
        da0, da1, dz0, dz1 = 1.65, 2.55, zdeck, zdeck + 2.02
        V.add_rooftop_door(mb, "x", px1, 1, da0, da1, dz0, dz1, stage)
        # 옥상 설비: 환기 팬 2기 + 옥상 배관/벤트 스택 + TV 안테나 (main 전용) # estimated
        if stage == 0:
            # 환기 팬 2기 (콘크리트 패드 + 덕트 원통 + 버섯형 루버 후드)
            for fx, fy in ((2.80, 3.20), (2.80, 8.60)):
                mb.box(fx - 0.42, fx + 0.42, fy - 0.42, fy + 0.42, zdeck, zdeck + 0.14, "concrete_light", skip=("bottom",))
                DC.add_oct_tube(mb, (fx, fy, zdeck + 0.14), (fx, fy, zdeck + 0.62), 0.24, "stainless", n=10)
                V.add_frustum(mb, fx, fy, zdeck + 0.62, zdeck + 0.80, 0.38, 0.18, "iron_dark", n=10, cap_top=True)
            # 옥상 배관 라인 (지지 침목 + 수평 배관 + 수직 벤트 스택 2개)
            for sx in (0.60, 2.20, 3.80):
                mb.box(sx - 0.12, sx + 0.12, 9.60 - 0.08, 9.60 + 0.08, zdeck, zdeck + 0.12, "concrete_light", skip=("bottom",))
            DC.add_oct_tube(mb, (0.20, 9.60, zdeck + 0.16), (4.20, 9.60, zdeck + 0.16), 0.042, "stainless", n=6)
            DC.add_oct_tube(mb, (0.20, 9.60, zdeck), (0.20, 9.60, zdeck + 1.05), 0.045, "pipe_white", n=6)
            V.add_frustum(mb, 0.20, 9.60, zdeck + 1.05, zdeck + 1.14, 0.09, 0.02, "iron_dark", n=6, cap_top=True)
            DC.add_oct_tube(mb, (4.20, 9.60, zdeck), (4.20, 9.60, zdeck + 0.92), 0.042, "stainless", n=6)
            V.add_frustum(mb, 4.20, 9.60, zdeck + 0.92, zdeck + 1.00, 0.085, 0.02, "iron_dark", n=6, cap_top=True)
            # TV/통신 안테나 (옥탑 좌후방 상단 장착)
            ax, ay, az0 = px0 + 0.35, py1 - 0.35, zdeck + ph
            mb.box(ax - 0.10, ax + 0.10, ay - 0.10, ay + 0.10, az0, az0 + 0.05, "iron_dark", skip=("bottom",))
            DC.add_oct_tube(mb, (ax, ay, az0 + 0.05), (ax, ay, az0 + 1.65), 0.020, "stainless", n=6)
            DC.add_oct_tube(mb, (ax - 0.48, ay, az0 + 1.48), (ax + 0.48, ay, az0 + 1.48), 0.012, "stainless", n=6)
            for dy in (-0.34, -0.14, 0.08, 0.30):
                DC.add_oct_tube(mb, (ax - 0.28, ay + dy, az0 + 1.48), (ax + 0.28, ay + dy, az0 + 1.48), 0.009, "iron_dark", n=6)
            DC.add_oct_tube(mb, (ax, ay - 0.42, az0 + 1.16), (ax, ay + 0.42, az0 + 1.16), 0.012, "stainless", n=6)
    # All stages retain the thin black coping silhouette (b08_full).
    mb.box(x0-.05,x1+.05,-.05,.23,zroof+.90,zroof+1.00,"granite")
    mb.box(x0-.05,x1+.05,D-.23,D+.05,zroof+.90,zroof+1.00,"granite")
    mb.box(x0-.05,x0+.23,.23,D-.23,zroof+.90,zroof+1.00,"granite")
    mb.box(x1-.23,x1+.05,.23,D-.23,zroof+.90,zroof+1.00,"granite")
    if stage == 0:
        # 공동현관 앞 문턱(스텐 논슬립) + 천장 LED: 캐노피 없이 필로티 슬래브가 비막이 역할 (정면 돌출 0)
        mb.box(ent[0], ent[1], rear-.30, rear-.002, 0, .036, "concrete_light", skip=("bottom",))
        mb.box(ent[0]+.02, ent[1]-.02, rear-.30, rear-.265, .036, .044, "stainless", skip=("bottom",))
        for ly in (1.30, 4.30, rear-.70):
            V.add_ceiling_lamp(mb, -2.20, -1.60, ly, ly+.40, zp)
        for x,y in cols + walk_cols:
            V.decal_plate(mb,"y",y-.25,-1,x-.21,x+.21,.35,1.15,.005,"bumper")
        # 카스토퍼: 좌측 1면(-4.45) + 우측 2면(1.75, 4.00), 가운데 통로(-2.6..-1.2)는 공동현관까지 개방
        for x in (-4.45, 1.75, 4.00):
            mb.box(x-.60,x+.60,6.90,7.08,0,.12,"stopper",skip=("bottom",))
            # 필로티 천장 LED 평판등 (전면 열 + 후면 열)
            V.add_ceiling_lamp(mb, x-.32, x+.32, 1.15, 1.55, zp)
            V.add_ceiling_lamp(mb, x-.32, x+.32, 4.25, 4.60, zp)
        # 공동현관 인터폰(문 왼쪽) · 우편함(문 오른쪽) · 남색 번호판(도로 쪽 통로 기둥)
        V.add_intercom(mb, "y", rear, -1, ent[0] - .40, ent[0] - .16, 1.28, 1.58)
        V.decal_plate(mb,"y",0,-1,cb-.25-.135,cb-.25+.135,1.80,2.02,.014,"address")
        K.axbox(mb,"y",rear,-1,ent[1]+.20,ent[1]+.80,0,.15,1.0,1.75,"stainless")
        K.axbox(mb,"y",rear,-1,ent[1]+.18,ent[1]+.82,0,.18,1.75,1.775,"stainless")
        # Separate letter slots, not a solid featureless mailbox block.
        for z in (1.12,1.34,1.56):
            K.axbox(mb,"y",rear-.15,-1,ent[1]+.25,ent[1]+.75,.002,.008,z,z+.025,"iron_dark")
        for axis,c,s,lo,hi,hs in faces:
            for f in range(3):
                z = 3+f*2.8
                for a,b,sill,head,panes in hs:
                    if panes != 3:
                        continue
                    o=c+s*.16
                    p0,p1=((a,o),(b,o)) if axis=="y" else ((o,a),(o,b))
                    DC.add_railing_run(mb,p0,p1,z+sill,.62,stage,reg="iron_dark",post_step=1.15,picket_step=.14)
        # 우측 실외기: 난간(x<=4.65) 및 모서리(x=5.80)와 간섭 없이 창대 아래(z+0.30, x=5.18)로 정돈
        for f in range(3):
            DC.add_ac_unit(mb,"y",0,-1,5.18,3+f*2.8+.30,stage)
            DC.add_ac_unit(mb,"y",D,1,1.05,3+f*2.8+.32,stage)
        for x in (x0+.33,x1-.33):
            DC.add_downspout(mb,"y",D,1,x,.15,zroof+.70)
        DC.add_ac_unit(mb,"y",rear,-1,4.95,.10,stage)
        # 계단실 수직 유리 띠(3개 층) + 공동현관 유리문 야간 점등 보장
        V.ensure_lit_windows(wins, lit_win_indices, spec.seed + 53)
    return mb,wins


def build_and_export():
    a=V.build_atlas(SPEC,charcoal=True)
    main,wins=build_stage(SPEC,a,0)
    lod1,_=build_stage(SPEC,a,1)
    lod2,_=build_stage(SPEC,a,2)
    assert lod1.tri_count < main.tri_count*.5
    assert lod2.tri_count+len(wins.items)*2 <= 500
    result=K.export_asset(SPEC.name,1,dict(main=main,lod1=lod1,lod2=lod2,windows=wins),a,
                          K.out_dir_from_argv("output"),lod2_tex=512,lot=SPEC.lot,front_yard=SPEC.front_yard,
                          notes=dict(archetype="villa_B_charcoal_piloti",seed=SPEC.seed))
    print(f"[B01] main={main.tri_count} lod1={lod1.tri_count} lod2={lod2.tri_count} windows={len(wins.items)}")
    return result


if __name__ == "__main__":
    build_and_export()
