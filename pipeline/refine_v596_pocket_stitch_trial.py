"""Separate rigged topstitch trial on existing jacket pocket panels."""
import math


def build(name='V596_POCKET_TOPSTITCH_TRIAL', interpolate_weights=True):
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
    assert name not in bpy.data.objects
    from mathutils.geometry import barycentric_transform
    evaluated=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    snapshot=evaluated.to_mesh()
    try:
        assert len(snapshot.vertices)==len(body.data.vertices)
        snapshot.calc_loop_triangles()
        triangles=[tuple(t.vertices) for t in snapshot.loop_triangles if snapshot.polygons[t.polygon_index].material_index==6]
        posed=[v.co.copy() for v in snapshot.vertices]
    finally:
        evaluated.to_mesh_clear()
    tree=BVHTree.FromPolygons(posed,triangles,all_triangles=True)
    # Trace existing inset contours in the documented orthographic chest view.
    # Project onto evaluated triangles, then map back to rest coordinates.
    pixels=[[(136,240),(220,272),(216,297),(145,288),(136,240)],
            [(140,308),(140,410),(171,417),(207,409),(207,310)],
            [(435,275),(552,257),(551,302),(507,320),(437,305),(435,275)],
            [(445,324),(447,428),(502,446),(537,432),(536,318)]]
    paths=[[( (x-320)*.4956/640,1.29+(320-y)*.4956/640) for x,y in path] for path in pixels]
    vertices, faces, weights = [], [], []
    stitches = 0
    for path in paths:
        for start, end in zip(path,path[1:]):
            a,b = Vector(start),Vector(end)
            length=(b-a).length
            for k in range(max(1,int(length/.003))):
                t=(k+.5)/max(1,int(length/.003))
                x,z=a.lerp(b,t)
                p,n,index,d=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),1.2)
                if p is None or p.y > .02:continue
                tri=triangles[index]
                rest=[body.data.vertices[i].co for i in tri]
                posed_tri=[posed[i] for i in tri]
                location=barycentric_transform(p,*posed_tri,*rest)
                n=(rest[1]-rest[0]).cross(rest[2]-rest[0]).normalized()
                if n.y>0:n=-n
                direction=Vector((b.x-a.x,0,b.y-a.y)).normalized()
                ahead=barycentric_transform(p+direction*.001,*posed_tri,*rest)
                tangent=(ahead-location).normalized()
                tangent=(tangent-n*tangent.dot(n)).normalized()
                cross=n.cross(tangent).normalized()
                center=location+n*.0004
                nearest=min(tri,key=lambda i:(body.data.vertices[i].co-location).length_squared)
                skin=[(g.group,g.weight) for g in body.data.vertices[nearest].groups]
                if interpolate_weights:
                    bary=barycentric_transform(p,*posed_tri,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
                    combined={}
                    for vertex,factor in zip(tri,bary):
                        for group in body.data.vertices[vertex].groups:
                            combined[group.group]=combined.get(group.group,0.)+max(0.,factor)*group.weight
                    total=sum(combined.values())
                    assert total>0
                    skin=[(group,weight/total) for group,weight in combined.items() if weight>0]
                assert skin
                base=len(vertices)
                for along in (-.00095,.00095):
                    for j in range(6):
                        angle=math.tau*j/6
                        vertices.append(center+tangent*along+.00018*(n*math.cos(angle)+cross*math.sin(angle)))
                        weights.append(skin)
                for j in range(6):faces.append((base+j,base+(j+1)%6,base+6+(j+1)%6,base+6+j))
                faces.extend([tuple(base+j for j in reversed(range(6))),tuple(base+6+j for j in range(6))])
                stitches+=1
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    ob=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(ob)
    for group in body.vertex_groups:ob.vertex_groups.new(name=group.name)
    for i,skin in enumerate(weights):
        for group,weight in skin:ob.vertex_groups[group].add([i],weight,'REPLACE')
    arm=ob.modifiers.new('Existing jacket skin weights','ARMATURE')
    src=next(m for m in body.modifiers if m.type=='ARMATURE')
    arm.object=src.object;arm.use_deform_preserve_volume=src.use_deform_preserve_volume
    material=bpy.data.materials.new('V596_DULL_TAN_TOPSTITCH');material.use_nodes=True
    material.diffuse_color=(.16,.105,.055,1)
    shader=material.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=(.16,.105,.055,1);shader.inputs['Roughness'].default_value=.85
    ob.data.materials.append(material)
    for p in mesh.polygons:p.use_smooth=True
    ob['status']='POCKET_ALIGNMENT_AND_DEFORMATION_REVIEW_REQUIRED'
    return {'object':ob.name,'stitches':stitches,'vertices':len(vertices),'interpolated_weights':interpolate_weights}
