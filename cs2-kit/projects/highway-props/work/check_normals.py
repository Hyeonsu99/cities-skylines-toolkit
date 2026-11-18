"""자체 검사: prism·extrude 의 모든 면 법선이 바깥(무게중심 반대)을 향하는지."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import hwprops_common as H


def outward_ok(mb, center):
    V = np.array(mb.verts, float)
    bad = 0
    for f in mb.faces:
        idx = f[0] if isinstance(f[0], (list, tuple)) else f
        p = V[list(idx)[:3]]
        n = np.cross(p[1] - p[0], p[2] - p[1])
        if np.dot(n, p.mean(0) - center) <= 0:
            bad += 1
    return bad


A = H.make_atlas(["galv"])
mb = H.K.MeshBuilder(A)
H.prism(mb, A, (0, 0, 0), (0, 0, 1), 0.1, "galv", sides=8, caps=(True, True))
assert outward_ok(mb, np.array([0, 0, 0.5])) == 0, "prism"
mb = H.K.MeshBuilder(A)
H.prism(mb, A, (0, 0, 0), (1, 0, 1), 0.1, "galv", sides=4, caps=(True, True))
assert outward_ok(mb, np.array([0.5, 0, 0.5])) == 0, "prism diag"
mb = H.K.MeshBuilder(A)
H.extrude(mb, A, [(-0.4, 0), (-0.4, 0.1), (-0.1, 1.0), (0.1, 1.0), (0.4, 0.1), (0.4, 0)], 0, 2, "galv", cap="fan")
assert outward_ok(mb, np.array([1.0, 0, 0.35])) == 0, "extrude fan"
print("normals OK")
mb = H.K.MeshBuilder(A)
mb.box(0, 1, 0, 1, 0, 1, "galv")
assert outward_ok(mb, np.array([0.5, 0.5, 0.5])) == 0, "box (기준 확인)"
print("box reference OK")
