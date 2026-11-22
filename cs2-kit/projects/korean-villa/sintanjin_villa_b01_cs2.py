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
    for x, y in cols:
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
        mb.box(ca, cb, 0, rear, 0, zp, "granite", skip=("bottom",))
        mb.box(x0, x1, rear, D, 0, zp, "wall_main", skip=("bottom",))
        mb.box(x0, x1, 0, D, zu, zroof+.90, "wall_main", skip=("bottom",))
        K.paint(mb, "y", 0, -1, ca+.45, cb-.45, zu+.10, zroof-.10, "window_backing")
        for axis, c, s, lo, hi, hs in faces:
            for f in range(3):
                z = 3 + f*2.8
                for a, b, sill, head, panes in hs:
                    K.paint(mb, axis, c, s, a, b, z+sill, z+head, "window_backing")
    else:
        rh = DC.add_recessed_wall
        rh(mb, wins, "y", 0, -1, ca, cb, 0, zp, "granite",
           [(ca+.48, cb-.48, .03, 2.16, "door_glass", 0, 2)], stage, 13, sash_reg="sash_dark")
        # Core side walls and rear rooms, with actual openings into the parking area.
        for c, s in ((ca, -1), (cb, 1)):
            rh(mb, wins, "x", c, s, .22, rear-.002, 0, zp, "granite", [], stage, 14)
        rh(mb, wins, "y", rear, -1, x0, x1, 0, zp, "wall_main",
           [(-4.8, -3.8, 1.20, 2.10, "window", 0, 2),
            (1.1, 2.05, .03, 2.12, "door_solid", 0, 1)], stage, 15)
        for c, s in ((x0,-1),(x1,1)):
            rh(mb, wins, "x", c, s, rear+.22, D-.22, 0, zp, "wall_main", [], stage, 16)
        rh(mb, wins, "y", D, 1, x0, x1, 0, zp, "wall_main",
           [(-4.5,-3.4,1.20,2.10,"window",0,2),(2.1,3.2,1.20,2.10,"window",0,2)], stage, 17)
        mb.box(ca+.24, cb-.24, .24, rear-.02, 0, zp-.01, "concrete_light", skip=("bottom",))
        mb.box(x0+.24, x1-.24, rear+.24, D-.24, 0, zp-.01, "concrete_light", skip=("bottom",))
        for k, (axis,c,s,lo,hi,hs) in enumerate(faces):
            holes = [(a,b,3+f*2.8+sill,3+f*2.8+head,"window",f+1,panes)
                     for f in range(3) for a,b,sill,head,panes in hs]
            if k == 0:
                # Continuous dark stair glazing, opening through the brick rather than painted on it.
                holes.append((ca+.45,cb-.45,zu+.12,zroof-.10,"window",1,1))
            rh(mb,wins,axis,c,s,lo,hi,zu,zroof+.90,"wall_main",holes,stage,30+k)
        mb.box(x0+.24,x1-.24,.24,D-.24,zu+.01,zroof,"wall_main")
        # Dark aluminium cross-mullions at half-landings, in front of the one glass face.
        for z in (4.15,5.55,6.95,8.35,9.75,11.15):
            K.axbox(mb,"y",0,-1,ca+.55,cb-.55,-.115,-.02,z,z+.055,"sash_dark")
        # Closed parapet above the filled roof deck; caps wrap corners by abutting.
        mb.box(x0+.219,x1-.219,.219,D-.219,zroof,zroof+.14,"roof_deck")
    # All stages retain the thin black coping silhouette (b08_full).
    mb.box(x0-.05,x1+.05,-.05,.23,zroof+.90,zroof+1.00,"granite")
    mb.box(x0-.05,x1+.05,D-.23,D+.05,zroof+.90,zroof+1.00,"granite")
    mb.box(x0-.05,x0+.23,.23,D-.23,zroof+.90,zroof+1.00,"granite")
    mb.box(x1-.23,x1+.05,.23,D-.23,zroof+.90,zroof+1.00,"granite")
    if stage == 0:
        # Closed steel canopy, no real building name; soffit is a solid lower box.
        mb.box(ca+.16,cb-.16,-.65,-.005,2.24,2.32,"granite")
        for x,y in cols:
            V.decal_plate(mb,"y",y-.25,-1,x-.21,x+.21,.35,1.15,.005,"bumper")
        for x in (-4.45, .9, 3.7):
            mb.box(x-.65,x+.65,6.90,7.08,0,.12,"stopper",skip=("bottom",))
            mb.box(x-.30,x+.30,3.8,4.1,zp-.035,zp,"lamp")
        K.axbox(mb,"y",0,-1,ca+.08,ca+.36,0,.045,1.28,1.55,"equip_gray")
        V.decal_plate(mb,"y",0,-1,cb-.34,cb-.07,1.80,2.02,.014,"address")
        K.axbox(mb,"x",cb,1,.65,1.35,0,.15,1.0,1.75,"stainless")
        # Separate letter slots, not a solid featureless mailbox block.
        for z in (1.12,1.34,1.56):
            K.axbox(mb,"x",cb+.15,1,.70,1.30,.002,.008,z,z+.025,"iron_dark")
        for axis,c,s,lo,hi,hs in faces:
            for f in range(3):
                z = 3+f*2.8
                for a,b,sill,head,panes in hs:
                    if panes != 3:
                        continue
                    o=c+s*.16
                    p0,p1=((a,o),(b,o)) if axis=="y" else ((o,a),(o,b))
                    DC.add_railing_run(mb,p0,p1,z+sill,.62,stage,reg="iron_dark",post_step=1.15,picket_step=.14)
        for f in range(3):
            DC.add_ac_unit(mb,"y",0,-1,4.95,3+f*2.8+.60,stage)
            DC.add_ac_unit(mb,"y",D,1,1.05,3+f*2.8+.32,stage)
        for x in (x0+.33,x1-.33):
            DC.add_downspout(mb,"y",D,1,x,.15,zroof+.70)
        DC.add_ac_unit(mb,"y",rear,-1,4.65,.10,stage)
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
