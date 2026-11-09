"""Shape an almond lid contour while retaining exact closed-blink targets."""
from collections import defaultdict, deque
from pathlib import Path
import json
import math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

import random

def rebuild_lashes(out):
    assert not bpy.app.is_job_running('RENDER')
    rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(rig.animation_data.drivers)==1957
    from mathutils.bvhtree import BVHTree
    body=bpy.data.objects['V416_BODY_CLEAN_JOIN']
    lidmat=list(body.data.materials).index(bpy.data.materials['V365_LID_SKIN'])
    basis=body.data.shape_keys.key_blocks['Basis']
    surface=BVHTree.FromPolygons([v.co for v in basis.data],[list(p.vertices) for p in body.data.polygons if any(1.625<basis.data[i].co.z<1.675 for i in p.vertices)],all_triangles=False)
    rng=random.Random(394);report={}
    for side in ('L','R'):
     name='V394_EYELASHES.'+side
     if name in bpy.data.objects:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
     margin=bpy.data.objects['V369_LID_MARGIN.'+side];keys=margin.data.shape_keys.key_blocks
     edges={key.name:[sum((key.data[i*6+k].co for k in range(6)),Vector())/6 for i in range(64)] for key in keys}
     closed=body.data.shape_keys.key_blocks['Blink.'+side]
     closed_surface=BVHTree.FromPolygons([v.co for v in closed.data],[list(p.vertices) for p in body.data.polygons if any(1.625<basis.data[i].co.z<1.675 for i in p.vertices)],all_triangles=False)
     neutral=edges['Basis'];xmin=min(p.x for p in neutral);xmax=max(p.x for p in neutral)
     states={key:[] for key in edges};faces=[];count=0
     for upper,n in ((True,54),(False,8)):
      for j in range(n):
       f=(j+.35+rng.random()*.3)/n
       pos=(1+30*f) if upper else (33+30*f)
       i=int(pos);a=pos-i
       root=neutral[i].lerp(neutral[(i+1)%64],a)
       u=(root.x-xmin)/(xmax-xmin)
       length=(.0022*rng.uniform(.7,1.2) if upper else rng.uniform(.00055,.00075))*(.45+.55*math.sin(math.pi*u))
       sideways=(u-.5)*.55
       direction=Vector((sideways,-.75,.75 if upper else -.65)).normalized()
       # A curved shaft projects toward the viewer before turning away from the aperture.
       base=len(states['Basis']);radius=rng.uniform(.000025,.000040)
       tangent=Vector((1,0,0));cross=direction.cross(tangent).normalized()
       for key,edge in edges.items():
        p=edge[i].lerp(edge[(i+1)%64],a)
        for step in range(6):
         t=step/5
         q=p+direction*length*t+Vector((0,-length*.35*math.sin(math.pi*t),0))
         if key in ('Basis','Blink'):
          active_surface=surface if key=='Basis' else closed_surface
          hit,_,_,_=active_surface.ray_cast(Vector((q.x,-.3,q.z)),Vector((0,1,0)),.4)
          if hit is not None:q.y=min(q.y,hit.y-.00010-.00045*t)
         rad=radius*(1-t)**.8+.000002
         for k in range(3):
          states[key].append(q+rad*(tangent*math.cos(k*math.tau/3)+cross*math.sin(k*math.tau/3)))
       for step in range(5):
        for k in range(3):
         faces.append((base+step*3+k,base+step*3+(k+1)%3,base+(step+1)*3+(k+1)%3,base+(step+1)*3+k))
       count+=1
     mesh=bpy.data.meshes.new(name);mesh.from_pydata(states['Basis'],[],faces);mesh.update()
     obj=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(obj)
     obj.parent=margin.parent;obj.parent_type=margin.parent_type;obj.parent_bone=margin.parent_bone
     obj.matrix_parent_inverse=margin.matrix_parent_inverse.copy();obj.matrix_basis=margin.matrix_basis.copy()
     mesh.materials.append(bpy.data.materials['V367_LASH_LINE'])
     for p in mesh.polygons:p.use_smooth=True
     obj.shape_key_add(name='Basis');key=obj.shape_key_add(name='Blink')
     for v,p in zip(key.data,states['Blink']):v.co=p
     d=key.driver_add('value').driver;d.type='SCRIPTED';v=d.variables.new();v.name='blink';v.type='SINGLE_PROP';v.targets[0].id=rig;v.targets[0].data_path=f'pose.bones["Head"]["Blink.{side}"]';d.expression='blink'
     report[side]={'lashes':count,'upper_lashes':54,'lower_lashes':8,'vertices':len(mesh.vertices)}
    rig.update_tag();bpy.context.view_layer.update()
    report['rig_drivers']=len(rig.animation_data.drivers)
    (out/'eyelash-report.json').write_text(json.dumps(report,indent=2))

def build(root, out, reopen=False):
    assert not bpy.app.is_job_running('RENDER')
    scene = bpy.context.scene
    rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
    head = rig.pose.bones['Head']
    body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
    assert len(rig.animation_data.drivers) == 1957
    if reopen:
        assert body.get('V544_eye_opening_applied')
        assert not body.get('V549_rounded_eyelids')
        assert not body.get('V547_blink_alignment')
    else:
        assert not body.get('V544_eye_opening_applied')
    # V578: the V575 neutral aperture still obscures too much iris in both
    # front and oblique views against the registered source portrait.
    # Raise only the upper opening; retain the lower margin, iris and canthi.
    upper_height, upper_power = (.0115, .82) if reopen else (.0070, .82)
    lower_height, lower_power = (.0023, .95) if reopen else (.0028, .95)
    mesh = body.data
    keys = mesh.shape_keys.key_blocks
    basis = keys['Basis']
    material_id = list(mesh.materials).index(bpy.data.materials['V365_LID_SKIN'])
    edge_counts = defaultdict(int)
    for polygon in mesh.polygons:
        for edge in polygon.edge_keys:
            edge_counts[tuple(sorted(edge))] += 1

    report = {'eyes':{}, 'aperture_profile': {
        'upper_height_m': upper_height, 'upper_power': upper_power,
        'lower_height_m': lower_height, 'lower_power': lower_power,
        'upper_fold_depth_m': .00045 if reopen else 0.}}
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
        order = [min(inner,key=lambda v:(basis.data[v].co-centers[0]).length_squared)]
        order.append(min(adjacent[order[0]] & inner,key=lambda v:(basis.data[v].co-centers[1]).length_squared))
        while len(order)<64:
            following=(adjacent[order[-1]] & inner)-set(order)
            assert len(following)==1
            order.append(following.pop())
        assert len(set(order)) == 64
        max_shift = 0.
        for start in inner:
            old = basis.data[start].co.copy()
            u = (old.x-xmin)/(xmax-xmin)
            baseline = zl*(1-u)+zr*u
            upper = old.z >= baseline
            new_z = baseline + (upper_height*math.sin(math.pi*u)**upper_power if upper
                                else -lower_height*math.sin(math.pi*u)**lower_power)
            change = new_z-old.z
            v = start
            for row in range(11):
                # A convex fold gives the upper lid volume between its margin
                # and brow join. It vanishes at both edges and both canthi;
                # the closed target remains unchanged for the rebuilt blink.
                fold = (.00045 * math.sin(math.pi*row/11) * math.sin(math.pi*u)**1.25
                        if reopen and upper else 0.)
                delta = Vector((0,-fold,change*(1-row/11)**1.5))
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
            radius = .00007 if top else .00010
            tangent = (edge[(i+1)%64]-edge[i-1]).normalized()
            front = Vector((0,-1,0))
            across = tangent.cross(front).normalized()
            for k in range(6):
                angle = k*math.tau/6
                mk['Basis'].data[i*6+k].co = p+front*.00007+radius*(
                    math.cos(angle)*front+math.sin(angle)*across)
            # Keep the closed target centerline, but match the open tube's
            # thinner cross section so the border does not swell on blinking.
            closed_center = sum((mk['Blink'].data[i*6+k].co for k in range(6)), Vector())/6
            for k in range(6):
                vertex = mk['Blink'].data[i*6+k]
                radial = vertex.co-closed_center
                assert radial.length > 1e-7
                vertex.co = closed_center+radial.normalized()*radius
        margin.data.update()
        closed_difference = max((keys['Blink.'+side].data[v].co
                                 -Vector(backup[side]['Blink.'+side][str(v)])).length
                                for v in distance)
        assert closed_difference == 0.
        report['eyes'][side] = {'max_opening_change_mm':max_shift*1000,
                                'closed_target_change_mm':closed_difference*1000,
                                'margin_radius_mm': {'upper': .07, 'lower': .10},
                                'eye_clearance_projections':pushed}


    body['V544_eye_opening_applied']=True
    if reopen:
        body['V549_rounded_eyelids']=True
    mesh.update()
    head['Blink.L']=head['Blink.R']=0.
    rig.update_tag();bpy.context.view_layer.update()
    report['rig_drivers']=len(rig.animation_data.drivers)
    prefix = 'rounded-' if reopen else ''
    (out/(prefix+'before_lid_coordinates.json')).write_text(json.dumps(backup))
    (out/(prefix+'eyelid-report.json')).write_text(json.dumps(report,indent=2))
    if not reopen:
        rebuild_lashes(out)
    return report
