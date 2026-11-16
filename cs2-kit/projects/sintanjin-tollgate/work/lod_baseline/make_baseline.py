import bpy, bmesh, os, sys
out = sys.argv[sys.argv.index("--") + 1]
for name, missing in (("BaselineClosed", False), ("BaselineOpen", True)):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_cube_add(size=2)
    obj = bpy.context.active_object
    obj.name = name
    if missing:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        faces = [f for f in bm.faces if f.normal.y < -0.5]
        bmesh.ops.delete(bm, geom=faces, context="FACES_ONLY")
        bm.to_mesh(obj.data)
        bm.free()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, name + ".blend"))
