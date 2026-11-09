"""Weld deformable lids into the Tripo sockets and add driven lid margins."""
import bpy, bmesh, json, math
from collections import defaultdict
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

root=Path(__file__).resolve().parents[1]
out=root/'production_v367_continuous_eyelids';out.mkdir(exist_ok=True)
scene=bpy.context.scene
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
body=bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
head=rig.pose.bones['Head']
assert len(rig.animation_data.drivers)==1957
backup=bpy.data.meshes.get('V367_BEFORE_BODY')
if backup is None:
    assert 'Blink.L' not in body.data.shape_keys.key_blocks, 'Run only on V366'
    backup=body.data.copy();backup.name='V367_BEFORE_BODY';backup.use_fake_user=True
else:body.data=backup.copy()
for obj in list(bpy.data.objects):
    if obj.name.startswith('V367_LID_MARGIN.'):bpy.data.objects.remove(obj,do_unlink=True)
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
    center=bpy.data.objects['V362_EYE_ANCHOR.'+side].location.copy()
    radius=json.loads((root/'production_v362_face_anatomy/eyes_lids_build.json').read_text())['eyes'][side]['radius']
    upper=[Vector(p['world']) for p in landmarks[side]['upper']]
    lower=[Vector(p['world']) for p in landmarks[side]['lower']]
    midx=(upper[0].x+upper[-1].x)/2;half=(upper[-1].x-upper[0].x)/2
    midz=sum(p.z for p in upper+lower)/14
    edges=[e for e in bm.edges if e.is_boundary and all(.009<sign*v.co.x<.075 and 1.615<v.co.z<1.68 and v.co.y<-.045 for v in e.verts)]
    graph=defaultdict(list)
    for e in edges:
        a,b=e.verts;graph[a].append(b);graph[b].append(a)
    assert all(len(a)==2 for a in graph.values())
    start=min(graph,key=lambda v:v.co.x);boundary=[start]
    prev=start;cur=max(graph[start],key=lambda v:v.co.z)
    while cur!=start:
        boundary.append(cur);nxt=next(v for v in graph[cur] if v!=prev);prev,cur=cur,nxt
    assert len(boundary)==len(graph)
    angles=[]
    for v in boundary:
        a=math.atan2((v.co.z-midz)/.0135,-(v.co.x-midx)/(half*1.35))
        if angles:
            while a<angles[-1]-math.pi:a+=2*math.pi
            while a>angles[-1]+math.pi:a-=2*math.pi
        angles.append(a)
    # The actual boundary is slightly jagged; retain its edge order and smooth
    # the parameter only, never its coordinates or existing face UVs.
    for _ in range(3):
        aa=angles[:]
        for i in range(len(angles)):
            before=aa[i-1] if i else aa[-1]-2*math.pi
            after=aa[i+1] if i+1<len(aa) else aa[0]+2*math.pi
            angles[i]=.5*aa[i]+.25*(before+after)
    assert all(b>a for a,b in zip(angles,angles[1:])),angles
    n=len(boundary);rows=12;loops=[];uvs={};clean={};edge_neutral=[];edge_closed=[]

    def globe(x,z):
        q=radius**2-(x-center.x)**2-(z-center.z)**2
        return center.y-math.sqrt(q) if q>0 else None

    for j in range(rows):
        t=j/(rows-1);ring=[]
        for i,(bv,a) in enumerate(zip(boundary,angles)):
            sine=math.sin(a);top=sine>=0;x=midx-half*math.cos(a)
            edge=interp(upper if top else lower,x)
            edge.z+=(-.0012 if top else .0006)*abs(sine)
            seam=interp(upper,x).z*.23+interp(lower,x).z*.77
            outer=bv.co.copy();_,normal,_=sample(outer.x,outer.z)
            values=[]
            for closed,ez in [(False,edge.z),(True,seam+(.000025 if top else -.000025))]:
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
    mesh=bpy.data.meshes.new('V367_LID_MARGIN.'+side);mesh.from_pydata(points[0],[],faces);mesh.update()
    obj=bpy.data.objects.new('V367_LID_MARGIN.'+side,mesh);scene.collection.objects.link(obj);parent_head(obj)
    mesh.materials.append(lashmat);mesh.materials.append(wetmat)
    for p,m in zip(mesh.polygons,materials):p.use_smooth=True;p.material_index=m
    obj.shape_key_add(name='Basis');key=obj.shape_key_add(name='Blink')
    for v,p in zip(key.data,points[1]):v.co=p
    drive(key,side)
    report['eyes'][side]={'welded_boundary_vertices':n,'new_vertices':n*(rows-1),'new_quads':n*(rows-1)}

bm.normal_update();bm.to_mesh(body.data);bm.free();body.data.update()
for side in ('L','R'):drive(body.data.shape_keys.key_blocks['Blink.'+side],side)
rig.update_tag();bpy.context.view_layer.update()
report['body_vertices']=len(body.data.vertices);report['rig_drivers']=len(rig.animation_data.drivers)
report['shape_keys']=list(body.data.shape_keys.key_blocks.keys())
(out/'continuous_lids_report.json').write_text(json.dumps(report,indent=2))
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32
scene.render.threads_mode='FIXED';scene.render.threads=1
scene.render.resolution_x=scene.render.resolution_y=700
scene.camera.data.ortho_scale=.40;scene.camera.location=(0,-1.4,1.66)
scene.camera.rotation_euler=(Vector((0,0,1.66))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
for name,closed in [('v367_neutral',0.),('v367_blink',1.)]:
    head['Blink.L']=head['Blink.R']=closed;rig.update_tag();bpy.context.view_layer.update()
    scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
head['Blink.L']=head['Blink.R']=0.;rig.update_tag();bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Character_An_continuous_eyelids_v367.blend'),compress=True)
print(json.dumps(report))
