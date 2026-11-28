# -*- coding: utf-8 -*-
"""눈높이(1.6 m) 원근 근접 검토 렌더 (Blender 전용, 검토 도구 — 에셋 산출물에는 영향 없음).

사용:
  blender -b output/<asset>/<asset>.blend --python eye_render.py -- <out.png> <cx,cy,cz> <tx,ty,tz> (키트 좌표) <day|night> [lens_mm]
키트 render.py 는 직교 투영이라 사람 눈높이 원근 시점을 볼 수 없어 추가했다. main 메시 + BaseColor/Normal/MaskMap/Emissive
텍스처를 그대로 쓰고, 지면 판(검토용, 에셋 아님)과 해/달 조명만 더한다.
"""
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
out, cam_s, tgt_s, mode = argv[:4]
lens = float(argv[4]) if len(argv) > 4 else 24.0
night = mode == "night"
cam = Vector(tuple(float(v) for v in cam_s.split(",")))
tgt = Vector(tuple(float(v) for v in tgt_s.split(",")))

blend = Path(bpy.data.filepath)
asset = blend.stem
texdir = blend.parent
# 키트 좌표(앞벽 y=0) -> 내보낸 메시 좌표 (manifest pivot_shift 만큼 이동)
_sh = json.loads((texdir / "manifest.json").read_text(encoding="utf-8")).get("pivot_shift", [0.0, 0.0])
_shift = Vector((_sh[0], _sh[1], 0.0))
cam += _shift
tgt += _shift

for o in list(bpy.data.objects):
    if o.name in ("Cube", "Camera", "Light") or "_LOD" in o.name:
        bpy.data.objects.remove(o, do_unlink=True)


def img(name, noncolor=False):
    p = texdir / f"{asset}_{name}.png"
    im = bpy.data.images.load(str(p), check_existing=True)
    if noncolor:
        im.colorspace_settings.name = "Non-Color"
    return im


mat = bpy.data.materials.new("eye_main")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
outn = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(bsdf.outputs["BSDF"], outn.inputs["Surface"])
t_bc = nt.nodes.new("ShaderNodeTexImage"); t_bc.image = img("BaseColor")
nt.links.new(t_bc.outputs["Color"], bsdf.inputs["Base Color"])
t_n = nt.nodes.new("ShaderNodeTexImage"); t_n.image = img("Normal", True)
nm = nt.nodes.new("ShaderNodeNormalMap")
nt.links.new(t_n.outputs["Color"], nm.inputs["Color"])
nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
t_m = nt.nodes.new("ShaderNodeTexImage"); t_m.image = img("MaskMap", True)
sep = nt.nodes.new("ShaderNodeSeparateColor")
nt.links.new(t_m.outputs["Color"], sep.inputs["Color"])
nt.links.new(sep.outputs["Red"], bsdf.inputs["Metallic"])
inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
nt.links.new(t_m.outputs["Alpha"], inv.inputs[1])
nt.links.new(inv.outputs["Value"], bsdf.inputs["Roughness"])
t_e = nt.nodes.new("ShaderNodeTexImage"); t_e.image = img("Emissive")
nt.links.new(t_e.outputs["Color"], bsdf.inputs["Emission Color"])
bsdf.inputs["Emission Strength"].default_value = 4.0 if night else 0.0

glass = bpy.data.materials.new("eye_glass")
glass.use_nodes = True
gb = glass.node_tree.nodes["Principled BSDF"]
gb.inputs["Base Color"].default_value = (0.05, 0.07, 0.08, 1)
gb.inputs["Roughness"].default_value = 0.08
gb.inputs["Metallic"].default_value = 0.3
if night:
    gb.inputs["Emission Color"].default_value = (1.0, 0.72, 0.42, 1)
    gb.inputs["Emission Strength"].default_value = 1.2

for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    o.data.materials.clear()
    o.data.materials.append(glass if o.name.endswith("_Win") else mat)

# 검토용 지면 판 (에셋 아님)
bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, -0.002))
gm = bpy.data.materials.new("eye_ground")
gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.16, 0.16, 0.15, 1)
gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
bpy.context.object.data.materials.append(gm)

scn = bpy.context.scene
world = bpy.data.worlds.new("eye_world"); scn.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.012, 0.016, 0.03, 1) if night else (0.55, 0.66, 0.82, 1)
bg.inputs["Strength"].default_value = 0.6 if night else 1.0

sun = bpy.data.lights.new("sun", "SUN")
sun.energy = 0.08 if night else 3.2
sun.color = (0.6, 0.7, 1.0) if night else (1.0, 0.96, 0.9)
so = bpy.data.objects.new("sun", sun); scn.collection.objects.link(so)
so.rotation_euler = (0.85, 0.15, -0.6)
if night:   # 골목 가로등 느낌의 약한 점광원 (카메라 뒤 위)
    pl = bpy.data.lights.new("street", "POINT"); pl.energy = 600; pl.color = (1.0, 0.85, 0.65)
    po = bpy.data.objects.new("street", pl); scn.collection.objects.link(po)
    po.location = cam + Vector((1.5, -2.0, 3.5))

cd = bpy.data.cameras.new("eye"); cd.lens = lens; cd.clip_start = 0.05
co = bpy.data.objects.new("eye", cd); scn.collection.objects.link(co)
co.location = cam
co.rotation_euler = (tgt - cam).to_track_quat("-Z", "Y").to_euler()
scn.camera = co

scn.render.engine = "BLENDER_EEVEE"
scn.render.resolution_x, scn.render.resolution_y = 1280, 800
scn.view_settings.view_transform = "Standard"
scn.render.filepath = out
bpy.ops.render.render(write_still=True)
print("[eye_render]", out)
