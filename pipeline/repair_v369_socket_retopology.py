"""Replace folded orbital scan triangles with a constrained annulus and quad lids."""
import bpy, bmesh, json, math
from collections import defaultdict
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform, delaunay_2d_cdt

root=Path(__file__).resolve().parents[1]
out=root/'production_v369_socket_retopology';out.mkdir(exist_ok=True)
scene=bpy.context.scene
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
body=bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
head=rig.pose.bones['Head']
assert len(rig.animation_data.drivers)==1957
# V367 is preserved on disk; regenerate only this local orbital repair from
# the pre-ring mesh, keeping mouth topology, hand weights and rig drivers.
body.data=bpy.data.meshes['V367_BEFORE_BODY'].copy()
for obj in list(bpy.data.objects):
    if obj.name.startswith(('V367_LID_MARGIN.','V368_LID_MARGIN.','V369_LID_MARGIN.')):
        bpy.data.objects.remove(obj,do_unlink=True)
for prop in ('Blink.L','Blink.R','JawOpen','GazeHorizontal','GazeVertical'):head[prop]=0.
rig.update_tag();bpy.context.view_layer.update()
landmarks=json.loads((root/'production_v362_face_anatomy/actual_face_landmarks.json').read_text())['landmarks']
source=bpy.data.meshes['V362_BODY_BEFORE_EYE_SOCKETS']
coords=[v.co.copy() for v in source.vertices]
bvh=BVHTree.FromPolygons(coords,[list(p.vertices) for p in source.polygons])

def sample(x,z):
    p,n,index,_=bvh.ray_cast(Vector((x,-.7,z)),Vector((0,1,0)))
    if p is None:raise ValueError((x,z))
    face=source.polygons[index];vi=list(face.vertices)[:3];li=list(face.loop_indices)[:3]
    uv=[Vector((*source.uv_layers.active.data[j].uv,0)) for j in li]
    return p,n,barycentric_transform(p,*[coords[j] for j in vi],*uv).xy

def interp(points,x):
    for a,b in zip(points,points[1:]):
        if a.x<=x<=b.x:return a.lerp(b,(x-a.x)/(b.x-a.x))
    return (points[0] if x<points[0].x else points[-1]).copy()

def smooth(v):
    t=max(0.,min(1.,v));return t*t*(3-2*t)

def drive(key,side):
    d=key.driver_add('value').driver;d.type='SCRIPTED'
    v=d.variables.new();v.name='v';v.type='SINGLE_PROP';v.targets[0].id=rig
    v.targets[0].data_path=f'pose.bones["Head"]["Blink.{side}"]';d.expression='v'

def parent_head(obj):
    bone=rig.pose.bones['DEF-Head']
    frame=rig.matrix_world@bone.matrix@Matrix.Translation((0,bone.bone.length,0))
    obj.parent=rig;obj.parent_type='BONE';obj.parent_bone=bone.name
    obj.matrix_parent_inverse=frame.inverted();obj.matrix_basis=Matrix.Identity(4)

def material(name,color,roughness):
    if name in bpy.data.materials:return bpy.data.materials[name]
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=roughness
    return m

lashmat=material('V367_LASH_LINE',(.009,.004,.002),.48)
wetmat=material('V367_WATERLINE',(.13,.049,.024),.27)
wetmat.node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value=.22
for side in ('L','R'):
    key=body.shape_key_add(name='Blink.'+side)
    for vertex,basis in zip(key.data,body.data.shape_keys.key_blocks['Basis'].data):
        vertex.co=basis.co
skin=bpy.data.materials['V365_LID_SKIN']
oldshader=body.data.materials[0].node_tree.nodes.get('Principled BSDF')
newshader=skin.node_tree.nodes.get('Principled BSDF')
for name in ('Roughness','Specular IOR Level','Subsurface Weight'):
    newshader.inputs[name].default_value=oldshader.inputs[name].default_value
if skin.name not in body.data.materials:body.data.materials.append(skin)
skin_index=list(body.data.materials).index(skin)
bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table()
shape_layers={k.name:bm.verts.layers.shape.get(k.name) for k in body.data.shape_keys.key_blocks}
assert all(shape_layers.values())
# V366 changed the reference shape, not the stored mesh positions. BMesh's
# default coordinates would otherwise revert those orbital adjustments when
# writing the reference key, putting the surrounding face inside the globe.
for v in bm.verts:v.co=v[shape_layers['Basis']]
uv0=bm.loops.layers.uv.active
uvclean=bm.loops.layers.uv.get('V365_CleanSkin') or bm.loops.layers.uv.new('V365_CleanSkin')
blend=bm.verts.layers.float.get('V365_LidAlbedoBlend') or bm.verts.layers.float.new('V365_LidAlbedoBlend')
deform=bm.verts.layers.deform.verify()
headgroup=body.vertex_groups['DEF-Head'].index
report={'eyes':{}}

for side,sign in [('L',1),('R',-1)]:
    oldlid=bpy.data.objects['V362_LIDS.'+side];oldlid.hide_render=True;oldlid.hide_set(True)
    upper=[Vector(p['world']) for p in landmarks[side]['upper']]
    lower=[Vector(p['world']) for p in landmarks[side]['lower']]
    midx=(upper[0].x+upper[-1].x)/2;half=(upper[-1].x-upper[0].x)/2
    midz=sum(p.z for p in upper+lower)/14
    radius=.0195
    center=Vector((midx,sample(midx,midz)[0].y+radius-.0007,midz))
    anchor=bpy.data.objects['V362_EYE_ANCHOR.'+side]
    anchor.location=center
    anchor.rotation_euler=Vector((0,-1,0)).to_track_quat('Z','Y').to_euler()
    bpy.data.objects['V362_EYE.'+side].scale=(radius/.01155,)*3
    # Replace the folded scan annulus. Keep the outer cut boundary in its
    # original position, then triangulate to a regular inner lid boundary.
    cut=[]
    for f in bm.faces:
        if all(v.co.y<-.045 for v in f.verts) and any(
                ((v.co.x-midx)/.0315)**2+((v.co.z-midz)/.0235)**2<1.
                for v in f.verts):
            cut.append(f)
    cutverts={v for f in cut for v in f.verts}
    bmesh.ops.delete(bm,geom=cut,context='FACES')
    edges=[e for e in bm.edges if e.is_boundary and all(
        abs(v.co.x-midx)<.037 and abs(v.co.z-midz)<.030 and v.co.y<-.045
        for v in e.verts)]
    graph=defaultdict(list)
    for e in edges:
        a,b=e.verts;graph[a].append(b);graph[b].append(a)
    assert graph and all(len(ns)==2 for ns in graph.values()),{v.index:len(ns) for v,ns in graph.items() if len(ns)!=2}
    start=min(graph,key=lambda v:v.co.x);outer_boundary=[start]
    prev=start;cur=max(graph[start],key=lambda v:v.co.z)
    while cur!=start:
        outer_boundary.append(cur)
        nxt=next(v for v in graph[cur] if v!=prev);prev,cur=cur,nxt
    assert len(outer_boundary)==len(graph)
    # Reset the old V366 projection on the outer boundary without moving XZ.
    for v in outer_boundary:
        delta=Vector((0,sample(v.co.x,v.co.z)[0].y-v.co.y,0))
        v.co+=delta
        for layer in shape_layers.values():v[layer]+=delta
    angles=[2*math.pi*i/64 for i in range(64)]
    boundary=[]
    for a in angles:
        x=midx-half*1.35*math.cos(a)
        z=midz+(.0158 if math.sin(a)>=0 else .0145)*math.sin(a)
        p=sample(x,z)[0]
        q=radius**2-(x-center.x)**2-(z-center.z)**2
        if q>0:p.y=min(p.y,center.y-math.sqrt(q)-.0008)
        v=bm.verts.new(p);v[deform][headgroup]=1.
        for layer in shape_layers.values():v[layer]=p
        boundary.append(v)
    inputs=outer_boundary+boundary
    constraints=[]
    for base,loop in ((0,outer_boundary),(len(outer_boundary),boundary)):
        constraints.extend((base+i,base+(i+1)%len(loop)) for i in range(len(loop)))
    # Two intermediate rings give the new annulus a similar density to the
    # surrounding scan. Only the cut and lid boundaries are constraints.
    for t in (.34,.68):
        for a in angles:
            rx=half*1.35*(1-t)+.0315*t
            rz=(.0158 if math.sin(a)>=0 else .0145)*(1-t)+.0235*t
            p=sample(midx-rx*math.cos(a),midz+rz*math.sin(a))[0]
            q=radius**2-(p.x-center.x)**2-(p.z-center.z)**2
            if q>0:p.y=min(p.y,center.y-math.sqrt(q)-.0008)
            v=bm.verts.new(p);v[deform][headgroup]=1.
            for layer in shape_layers.values():v[layer]=p
            inputs.append(v)
    points=[Vector((v.co.x,v.co.z)) for v in inputs]
    triangulated=delaunay_2d_cdt(points,constraints,[],1,1e-8,True)
    cpoints,_,cfaces,originals,_,_=triangulated
    assert all(len(ids)==1 for ids in originals), 'Intersecting cut boundary'
    mapped=[inputs[ids[0]] for ids in originals]
    def inside(point,polygon):
        x,y=point;hit=False
        for i,a in enumerate(polygon):
            b=polygon[i-1]
            if (a.y>y)!=(b.y>y) and x<(b.x-a.x)*(y-a.y)/(b.y-a.y)+a.x:
                hit=not hit
        return hit
    op=points[:len(outer_boundary)]
    ip=points[len(outer_boundary):len(outer_boundary)+len(boundary)]
    annulus=[]
    for indices in cfaces:
        center2=sum((cpoints[i] for i in indices),Vector((0,0)))/len(indices)
        if not inside(center2,op) or inside(center2,ip):continue
        verts=[mapped[i] for i in indices]
        if (verts[1].co-verts[0].co).cross(verts[2].co-verts[0].co).y>0:verts.reverse()
        f=bm.faces.new(verts);f.material_index=0;f.smooth=True;annulus.append(f)
        for loop in f.loops:
            uv=sample(loop.vert.co.x,loop.vert.co.z)[2]
            loop[uv0].uv=uv;loop[uvclean].uv=uv
    assert all(len(v.link_faces)>0 for v in inputs)
    region=inputs
    n=len(boundary);rows=12;loops=[];uvs={};clean={};edge_neutral=[];edge_closed=[]

    def globe(x,z):
        q=radius**2-(x-center.x)**2-(z-center.z)**2
        return center.y-math.sqrt(q) if q>0 else None

    for j in range(rows):
        t=j/(rows-1);ring=[]
        for i,(bv,a) in enumerate(zip(boundary,angles)):
            sine=math.sin(a);top=sine>=0;x=midx-half*math.cos(a)
            edge=interp(upper if top else lower,x)
            edge.z+=(-.0012 if top else .0006)*sine*sine
            seam=interp(upper,x).z*.23+interp(lower,x).z*.77
            outer=bv.co.copy();_,normal,_=sample(outer.x,outer.z)
            values=[]
            for closed,ez in [(False,edge.z),(True,seam+(.000025 if top else -.000025)*abs(sine))]:
                inner=Vector((x,globe(x,ez)-.00075,ez));p=inner.lerp(outer,t)
                dx,dz=outer.x-inner.x,outer.z-inner.z
                denom=max(.002,center.y-globe(inner.x,inner.z))
                slope0=((inner.x-center.x)*dx+(inner.z-center.z)*dz)/denom
                slope1=-(normal.x*dx+normal.z*dz)/normal.y if abs(normal.y)>.1 else 0.
                slope0=max(-.020,min(.020,slope0));slope1=max(-.020,min(.020,slope1))
                p.y=((2*t**3-3*t*t+1)*inner.y+(t**3-2*t*t+t)*slope0
                     +(-2*t**3+3*t*t)*outer.y+(t**3-t*t)*slope1)
                # A shallow upper-lid fold unfolds during the blink.
                if top:p.y+=(.00025 if closed else .0008)*math.exp(-((t-.56)/.13)**2)*abs(sine)
                gy=globe(p.x,p.z)
                if gy is not None and j<rows-1:
                    limit=gy-.00075;p.y=.5*(p.y+limit-math.sqrt((p.y-limit)**2+.00018**2))
                values.append(p)
            neutral,closed=values
            if j==0:edge_neutral.append(neutral.copy());edge_closed.append(closed.copy())
            if j==rows-1:v=bv
            else:
                v=bm.verts.new(neutral);v[deform][headgroup]=1.
                for name,layer in shape_layers.items():v[layer]=closed if name=='Blink.'+side else neutral
            v[blend]=1-smooth((t-.40)/.60)
            uvs[v]=sample(neutral.x,neutral.z)[2]
            cz=interp(upper if top else lower,x).z+(.0045 if top else -.0045)
            clean[v]=sample(neutral.x,cz)[2]
            ring.append(v)
        loops.append(ring)
    for j in range(rows-1):
        for i in range(n):
            ni=(i+1)%n
            f=bm.faces.new((loops[j][i],loops[j][ni],loops[j+1][ni],loops[j+1][i]))
            f.material_index=skin_index;f.smooth=True
            for loop in f.loops:loop[uv0].uv=uvs[loop.vert];loop[uvclean].uv=clean[loop.vert]
    # A small separate tube represents the lid margin, with the same blink.
    points=[[],[]];faces=[];materials=[];cross=6
    for state,edgepoints in enumerate((edge_neutral,edge_closed)):
        for i,(p,a) in enumerate(zip(edgepoints,angles)):
            top=math.sin(a)>=0;r=.00013 if top else .00020
            tangent=(edgepoints[(i+1)%n]-edgepoints[i-1]).normalized()
            front=Vector((0,-1,0));across=tangent.cross(front).normalized()
            for k in range(cross):
                q=p+front*.00005+r*(math.cos(k*2*math.pi/cross)*front+math.sin(k*2*math.pi/cross)*across)
                points[state].append(q)
    for i in range(n):
        for k in range(cross):
            faces.append((i*cross+k,((i+1)%n)*cross+k,((i+1)%n)*cross+(k+1)%cross,i*cross+(k+1)%cross))
            materials.append(0 if math.sin(angles[i])>=0 else 1)
    mesh=bpy.data.meshes.new('V369_LID_MARGIN.'+side);mesh.from_pydata(points[0],[],faces);mesh.update()
    obj=bpy.data.objects.new('V369_LID_MARGIN.'+side,mesh);scene.collection.objects.link(obj);parent_head(obj)
    mesh.materials.append(lashmat);mesh.materials.append(wetmat)
    for p,m in zip(mesh.polygons,materials):p.use_smooth=True;p.material_index=m
    obj.shape_key_add(name='Basis');key=obj.shape_key_add(name='Blink')
    for v,p in zip(key.data,points[1]):v.co=p
    drive(key,side)
    report['eyes'][side]={'welded_boundary_vertices':n,'new_vertices':n*(rows-1),'new_quads':n*(rows-1),'orbital_vertices':len(region),'removed_scan_faces':len(cut),'annulus_triangles':len(annulus),'outer_boundary_vertices':len(outer_boundary),'eye_center':list(center),'eye_radius':radius}

bm.normal_update();bm.to_mesh(body.data);bm.free();body.data.update()
for side in ('L','R'):drive(body.data.shape_keys.key_blocks['Blink.'+side],side)
rig.update_tag();bpy.context.view_layer.update()
report['body_vertices']=len(body.data.vertices);report['rig_drivers']=len(rig.animation_data.drivers)
report['shape_keys']=list(body.data.shape_keys.key_blocks.keys())
(out/'continuous_lids_report.json').write_text(json.dumps(report,indent=2))
# Inspect geometry in clay before spending time on textured renders.
scene.render.engine='BLENDER_WORKBENCH'
scene.render.threads_mode='FIXED';scene.render.threads=1
scene.render.resolution_x=800;scene.render.resolution_y=500
scene.camera.data.ortho_scale=.255;scene.camera.location=(0,-1.4,1.65)
scene.camera.rotation_euler=(Vector((0,0,1.65))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.display.shading.light='STUDIO';scene.display.shading.studio_light='paint.sl'
scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.55,.55,.55)
scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH'
for name,closed in [('v369_clay_neutral',0.),('v369_clay_blink',1.)]:
    head['Blink.L']=head['Blink.R']=closed;rig.update_tag();bpy.context.view_layer.update()
    scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
head['Blink.L']=head['Blink.R']=0.;rig.update_tag();bpy.context.view_layer.update()
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Character_An_socket_retopology_v369.blend'),compress=True)
print(json.dumps(report))
