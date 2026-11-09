"""Round the lid aperture and simplify eye reflections, preserving full blinks."""
from collections import defaultdict, deque
from pathlib import Path
import json
import math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'production_v396_lower_lids'
OUT.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
scene = bpy.context.scene
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
head = rig.pose.bones['Head']
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
assert len(rig.animation_data.drivers) == 1957
assert not body.get('V396_eye_opening_applied')
mesh = body.data
keys = mesh.shape_keys.key_blocks
basis = keys['Basis']
material_id = list(mesh.materials).index(bpy.data.materials['V365_LID_SKIN'])
edge_counts = defaultdict(int)
for polygon in mesh.polygons:
    for edge in polygon.edge_keys:
        edge_counts[tuple(sorted(edge))] += 1

report = {'eyes':{}}
backup = {}
for side in ('L','R'):
    sign = 1 if side == 'L' else -1
    polygons = [p for p in mesh.polygons if p.material_index == material_id
                and basis.data[p.vertices[0]].co.x*sign > 0]
    adjacent = defaultdict(set)
    for polygon in polygons:
        for a,b in polygon.edge_keys:
            adjacent[a].add(b)
            adjacent[b].add(a)
    inner = {v for v, neighbors in adjacent.items()
             if any(edge_counts[tuple(sorted((v,n)))] == 1 for n in neighbors)}
    assert len(inner) == 64
    distance = {v:0 for v in inner}
    queue = deque(inner)
    while queue:
        v = queue.popleft()
        for n in adjacent[v]:
            if n not in distance:
                distance[n] = distance[v]+1
                queue.append(n)
    assert max(distance.values()) == 11
    backup[side] = {key.name:{str(v):list(key.data[v].co) for v in distance}
                    for key in keys}
    left = min(inner,key=lambda v:basis.data[v].co.x)
    right = max(inner,key=lambda v:basis.data[v].co.x)
    xmin,xmax = basis.data[left].co.x,basis.data[right].co.x
    zl,zr = basis.data[left].co.z,basis.data[right].co.z
    margin = bpy.data.objects['V369_LID_MARGIN.'+side]
    mk = margin.data.shape_keys.key_blocks
    centers = [sum((mk['Basis'].data[i*6+k].co for k in range(6)),Vector())/6
               for i in range(64)]
    order = [min(inner,key=lambda v:(basis.data[v].co-p).length_squared)
             for p in centers]
    assert len(set(order)) == 64
    max_shift = 0.
    for start in inner:
        old = basis.data[start].co.copy()
        u = (old.x-xmin)/(xmax-xmin)
        baseline = zl*(1-u)+zr*u
        upper = old.z >= baseline
        new_z = baseline + (.0080*math.sin(math.pi*u)**.52 if upper
                            else -.0022*math.sin(math.pi*u)**.58)
        change = new_z-old.z
        v = start
        for row in range(11):
            delta = Vector((0,0,change*(1-row/11)**1.5))
            for key in keys:
                if key.name != 'Blink.'+side:
                    key.data[v].co += delta
            max_shift = max(max_shift,delta.length)
            children = [n for n in adjacent[v] if distance[n] == row+1]
            assert len(children) == 1
            v = children[0]
    dg = bpy.context.evaluated_depsgraph_get()
    verts,faces = [],[]
    for name in ('V374_EYE.','V374_CORNEA.'):
        obj = bpy.data.objects[name+side].evaluated_get(dg)
        evaluated_mesh = obj.to_mesh()
        offset = len(verts)
        verts.extend(body.matrix_world.inverted()@obj.matrix_world@v.co
                     for v in evaluated_mesh.vertices)
        faces.extend([offset+i for i in p.vertices] for p in evaluated_mesh.polygons)
        obj.to_mesh_clear()
    surface = BVHTree.FromPolygons(verts,faces,all_triangles=False)
    pushed = 0
    for v,row in distance.items():
        if row == 11:
            continue
        for key in keys:
            if key.name == 'Blink.'+side:
                continue
            p = key.data[v].co
            hit,_,_,_ = surface.ray_cast(Vector((p.x,-.25,p.z)),Vector((0,1,0)),.4)
            if hit is not None and p.y > hit.y-.00055:
                p.y = hit.y-.00055
                pushed += 1
    edge = [basis.data[v].co.copy() for v in order]
    for i,p in enumerate(edge):
        top = i <= 32
        radius = .00012 if top else .00020
        tangent = (edge[(i+1)%64]-edge[i-1]).normalized()
        front = Vector((0,-1,0))
        across = tangent.cross(front).normalized()
        for k in range(6):
            angle = k*math.tau/6
            mk['Basis'].data[i*6+k].co = p+front*.00007+radius*(
                math.cos(angle)*front+math.sin(angle)*across)
    margin.data.update()
    closed_difference = max((keys['Blink.'+side].data[v].co
                             -Vector(backup[side]['Blink.'+side][str(v)])).length
                            for v in distance)
    assert closed_difference == 0.
    report['eyes'][side] = {'max_opening_change_mm':max_shift*1000,
                            'closed_target_change_mm':closed_difference*1000,
                            'eye_clearance_projections':pushed}


body['V396_eye_opening_applied']=True
mesh.update()
head['Blink.L']=head['Blink.R']=0.
rig.update_tag();bpy.context.view_layer.update()
report['rig_drivers']=len(rig.animation_data.drivers)
(OUT/'before_lid_coordinates.json').write_text(json.dumps(backup))
(OUT/'report.json').write_text(json.dumps(report,indent=2))
lash_source=(ROOT/'pipeline/refine_v394_eyelashes.py').read_text()
lash_source=lash_source[:lash_source.index('bpy.ops.wm.save_as_mainfile')]
exec(compile(lash_source, 'rebuild_lashes', 'exec'), {'__file__':str(ROOT/'pipeline/refine_v394_eyelashes.py')})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_lower_lids_v396.blend'),compress=True)
print(json.dumps(report))
