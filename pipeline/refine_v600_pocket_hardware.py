"""Reversible brass pocket snap covers on the current jacket, with skin weights."""
import math


def build(clear_surface=True):
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from mathutils.geometry import barycentric_transform
    body=bpy.data.objects['V416_BODY_CLEAN_JOIN']
    assert 'V600_POCKET_SNAP_COVERS' not in bpy.data.objects
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
    try:
        assert len(mesh.vertices)==len(body.data.vertices)
        mesh.calc_loop_triangles()
        triangles=[tuple(t.vertices) for t in mesh.loop_triangles if mesh.polygons[t.polygon_index].material_index==6]
        posed=[v.co.copy() for v in mesh.vertices]
    finally:ev.to_mesh_clear()
    tree=BVHTree.FromPolygons(posed,triangles,all_triangles=True)
    rest_tree=BVHTree.FromPolygons([v.co for v in body.data.vertices], [tuple(p.vertices) for p in body.data.polygons]) if clear_surface else None
    vertices=[];faces=[];weights=[];report=[]
    for px,py in [(149,265),(507,302)]:
        x=(px-320)*.4956/640;z=1.29+(320-py)*.4956/640
        hit,normal,index,_=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),1.2)
        assert hit is not None and hit.y<0
        tri=triangles[index];posed_tri=[posed[i] for i in tri];rest=[body.data.vertices[i].co for i in tri]
        center=barycentric_transform(hit,*posed_tri,*rest)
        surrounding=[]
        for dx,dz in [(.012,0),(-.012,0),(0,.012),(0,-.012)]:
            q,_,face,_=tree.ray_cast(Vector((x+dx,-1,z+dz)),Vector((0,1,0)),1.2)
            assert q is not None
            ids=triangles[face]
            surrounding.append(barycentric_transform(q,*[posed[i] for i in ids],*[body.data.vertices[i].co for i in ids]))
        normal=(surrounding[0]-surrounding[1]).cross(surrounding[2]-surrounding[3]).normalized()
        if normal.y>0:normal=-normal
        u=normal.cross(Vector((0,0,1))).normalized();v=normal.cross(u).normalized()
        clearance_lift=0.
        if rest_tree is not None:
            heights=[]
            for radius in (0., .004, .008):
                for j in range(24):
                    angle=math.tau*j/24
                    radial=radius*(u*math.cos(angle)+v*math.sin(angle))
                    q,_,_,_=rest_tree.ray_cast(center+radial+normal*.025,-normal,.05)
                    if q is not None:heights.append((q-center-radial).dot(normal))
            assert heights
            clearance_lift=max(0.,max(heights)+.0003)
            assert clearance_lift<.012, clearance_lift
            center+=normal*clearance_lift
        bary=barycentric_transform(hit,*posed_tri,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
        skin={}
        for vertex,factor in zip(tri,bary):
            for group in body.data.vertices[vertex].groups:skin[group.group]=skin.get(group.group,0.)+max(0.,factor)*group.weight
        total=sum(skin.values());assert total>0
        skin={g:w/total for g,w in skin.items()}
        base=len(vertices);segments=48
        profile=[(.0055,.00015),(.0055,.00075),(.0050,.0010),(.00455,.0008),(.00425,.0007),(.0025,.00085)]
        for radius,height in profile:
            radius *= 16./11.
            for j in range(segments):
                angle=math.tau*j/segments
                vertices.append(center+normal*height+radius*(u*math.cos(angle)+v*math.sin(angle)));weights.append(skin)
        for ring in range(len(profile)-1):
            for j in range(segments):
                a=base+ring*segments+j;b=base+ring*segments+(j+1)%segments
                faces.append((a,b,b+segments,a+segments))
        pole=len(vertices);vertices.append(center+normal*.00095);weights.append(skin)
        last=base+(len(profile)-1)*segments
        for j in range(segments):faces.append((last+j,last+(j+1)%segments,pole))
        report.append({'center_rest':list(center),'source_pixel':[px,py],'diameter_mm':16.0,'clearance_lift_mm':clearance_lift*1000})
    data=bpy.data.meshes.new('V600_POCKET_SNAP_COVERS');data.from_pydata(vertices,[],faces);data.update()
    ob=bpy.data.objects.new('V600_POCKET_SNAP_COVERS',data);bpy.context.scene.collection.objects.link(ob)
    for group in body.vertex_groups:ob.vertex_groups.new(name=group.name)
    for i,skin in enumerate(weights):
        for group,weight in skin.items():ob.vertex_groups[group].add([i],weight,'REPLACE')
    src=next(m for m in body.modifiers if m.type=='ARMATURE');mod=ob.modifiers.new('Jacket skin','ARMATURE');mod.object=src.object;mod.use_deform_preserve_volume=src.use_deform_preserve_volume
    mat=bpy.data.materials.new('V600_AGED_BRASS_SNAPS');mat.use_nodes=True;mat.diffuse_color=(.32,.19,.06,1)
    shader=mat.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=mat.diffuse_color;shader.inputs['Metallic'].default_value=.85;shader.inputs['Roughness'].default_value=.38
    ob.data.materials.append(mat)
    for poly in data.polygons:poly.use_smooth=True
    ob['status']='REFERENCE_HARDWARE_TRIAL_PENDING_VISUAL_REVIEW'
    return {'object':ob.name,'snaps':report,'vertices':len(vertices)}
