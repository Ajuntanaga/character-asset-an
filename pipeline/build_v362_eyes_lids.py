"""Fit separate eyes and UV-matched eyelid loops to the actual Tripo face."""
import bpy, bmesh, json, math
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'production_v362_face_anatomy'
scene=bpy.context.scene
body=bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(rig.animation_data.drivers)==1957
source=bpy.data.meshes.get('V362_BODY_BEFORE_EYE_SOCKETS')
if source is None:
    source=body.data.copy(); source.name='V362_BODY_BEFORE_EYE_SOCKETS'; source.use_fake_user=True
else:
    body.data=source.copy()
for obj in list(bpy.data.objects):
    if obj.name.startswith(('V362_LIDS.','V362_EYE.','V362_CORNEA.','V362_GAZE.','V362_EYE_ANCHOR.')):
        bpy.data.objects.remove(obj,do_unlink=True)
collection=bpy.data.collections.get('V362_FACIAL_ANATOMY') or bpy.data.collections.new('V362_FACIAL_ANATOMY')
if collection.name not in scene.collection.children: scene.collection.children.link(collection)
coords=[body.matrix_world@v.co for v in source.vertices]
bvh=BVHTree.FromPolygons(coords,[list(p.vertices) for p in source.polygons])
landmarks=json.loads((OUT/'actual_face_landmarks.json').read_text())['landmarks']
head=rig.pose.bones['Head'] if 'Head' in rig.pose.bones else rig.pose.bones['DEF-Head']
for prop,low,high in [('Blink.L',0,1),('Blink.R',0,1),('GazeHorizontal',-25,25),('GazeVertical',-20,20)]:
    head[prop]=0.0; head.id_properties_ui(prop).update(min=low,max=high,soft_min=low,soft_max=high)

def drive(owner,path,index,prop,expression='v'):
    curve=owner.driver_add(path,index) if index is not None else owner.driver_add(path)
    driver=curve.driver;driver.type='SCRIPTED';var=driver.variables.new();var.name='v';var.type='SINGLE_PROP'
    var.targets[0].id=rig;var.targets[0].data_path=f'pose.bones["{head.name}"]["{prop}"]'
    driver.expression=expression

def head_parent(obj,world):
    bone=rig.pose.bones['DEF-Head']
    frame=rig.matrix_world@bone.matrix@Matrix.Translation((0,bone.bone.length,0))
    obj.parent=rig;obj.parent_type='BONE';obj.parent_bone=bone.name
    obj.matrix_parent_inverse=frame.inverted();obj.matrix_basis=world

def surface(x,z):
    p,n,i,d=bvh.ray_cast(Vector((x,-.7,z)),Vector((0,1,0)))
    if p is None: raise RuntimeError(f'Missing facial surface at {x},{z}')
    face=source.polygons[i]
    vi=list(face.vertices)[:3];li=list(face.loop_indices)[:3]
    uv=[Vector((*source.uv_layers.active.data[j].uv,0)) for j in li]
    return p,barycentric_transform(p,*[coords[j] for j in vi],*uv).xy

def interp(points,x):
    for a,b in zip(points,points[1:]):
        if a.x<=x<=b.x:
            t=(x-a.x)/(b.x-a.x)
            return a.lerp(b,t)
    return points[0].copy() if x<points[0].x else points[-1].copy()

def point_inside(x,z,poly):
    inside=False
    for i,a in enumerate(poly):
        b=poly[(i+1)%len(poly)]
        if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:inside=not inside
    return inside

eye_source=bpy.data.objects['V362_SOURCE_Eyeball']
cornea_source=bpy.data.objects['V362_SOURCE_Cornea']
eye_material=eye_source.data.materials[0].copy();eye_material.name='V362_BROWN_PROCEDURAL_EYE'
group=next(n for n in eye_material.node_tree.nodes if n.type=='GROUP')
colors={'Iris Primary':(.055,.021,.008,1),'Iris Secondary':(.14,.063,.021,1),'Iris Tertiary':(.08,.031,.008,1),'Iris Dark Gaps':(.008,.003,.001,1),'Splotches':(.12,.05,.015,1),'Limbus Primary':(.012,.005,.002,1),'Limbus Secondary':(.004,.002,.001,1),'Scelera':(.68,.62,.53,1)}
for name,value in colors.items():group.inputs[name].default_value=value
group.inputs['Blood Vessels'].default_value=.30
group.inputs['Blood Vessels Coverage'].default_value=.45
eye_material.diffuse_color=(.55,.47,.39,1)
report={'license':'BlenderKit royalty_free, local metadata retained','eyes':{},'control_bone':head.name}
cutouts=[]

for side,center,radius in [('L',(.03533604,-.07521055,1.64403063),.02296506),('R',(-.02908892,-.07647847,1.64401738),.02506396)]:
    center=Vector(center)
    data=landmarks[side]
    upper=[Vector(p['world']) for p in data['upper']]
    lower=[Vector(p['world']) for p in data['lower']]
    xmin,xmax=upper[0].x,upper[-1].x
    midx=(xmin+xmax)/2;midz=sum(p.z for p in upper+lower)/14
    def globe_y(x,z):return center.y-math.sqrt(max(.000001,radius**2-(x-center.x)**2-(z-center.z)**2))
    # The original imported iris looks upward. Aim the new eyes straight ahead.
    aim=Vector((midx,globe_y(midx,midz),midz))
    direction=(aim-center).normalized()
    anchor=bpy.data.objects.new('V362_EYE_ANCHOR.'+side,None);collection.objects.link(anchor)
    anchor.empty_display_size=.006
    head_parent(anchor,Matrix.Translation(center)@direction.to_track_quat('Z','Y').to_matrix().to_4x4())
    gaze=bpy.data.objects.new('V362_GAZE.'+side,None);collection.objects.link(gaze);gaze.parent=anchor
    gaze.empty_display_size=.004;gaze.rotation_mode='XYZ'
    drive(gaze,'rotation_euler',1,'GazeHorizontal','v*pi/180')
    drive(gaze,'rotation_euler',0,'GazeVertical','-v*pi/180')
    eye=eye_source.copy();eye.data=eye_source.data.copy();eye.name='V362_EYE.'+side;collection.objects.link(eye)
    eye.parent=gaze;eye.matrix_parent_inverse=Matrix.Identity(4);eye.matrix_basis=Matrix.Identity(4)
    # Keep the asset's iris aperture, corneal bulge and dilation shape keys.
    scale=radius/.01155;eye.scale=(scale,scale,scale)
    eye.data.materials.clear();eye.data.materials.append(eye_material)
    cornea=cornea_source.copy();cornea.data=cornea_source.data.copy();cornea.name='V362_CORNEA.'+side;collection.objects.link(cornea)
    cornea.parent=eye
    cornea.matrix_parent_inverse=cornea_source.matrix_parent_inverse.copy()
    cornea.matrix_basis=cornea_source.matrix_basis.copy()
    for ob in (eye,cornea):
        ob.hide_render=False;ob.hide_viewport=False;ob.hide_set(False)
    # 64 angular samples and eight concentric loops give a local deformable patch.
    count=64;rows=8;verts=[];uvs=[];closed=[];outer=[]
    for j in range(rows):
        t=j/(rows-1)
        for i in range(count):
            theta=2*math.pi*i/count
            x=midx-(xmax-xmin)/2*math.cos(theta)
            top=math.sin(theta)>=0
            edge=interp(upper if top else lower,x)
            ox=midx+(x-midx)*1.45
            oz=midz+(edge.z-midz)*2.65
            px=x+(ox-x)*t;pz=edge.z+(oz-edge.z)*t
            sample,uv=surface(px,pz)
            inner_y=min(edge.y-.00015,globe_y(x,edge.z)-.00035)
            py=sample.y-.00012+(inner_y-edge.y)*(1-t)**2
            verts.append((px,py,pz));uvs.append(tuple(uv))
            up=interp(upper,x).z;down=interp(lower,x).z
            seam=up*.23+down*.77
            target=seam+(.000035 if top else -.000035)
            bz=pz+(target-edge.z)*(1-t)**1.35
            gy=globe_y(px,bz)-.00045
            by=py+(gy-py)*(1-t)**1.4
            closed.append((px,by,bz))
            if j==rows-1:outer.append((px,pz))
    faces=[]
    for j in range(rows-1):
        for i in range(count):
            ni=(i+1)%count
            faces.append((j*count+i,j*count+ni,(j+1)*count+ni,(j+1)*count+i))
    mesh=bpy.data.meshes.new('V362_LIDS_MESH.'+side);mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new('V362_LIDS.'+side,mesh);collection.objects.link(obj)
    mesh.materials.append(body.data.materials[0])
    uv_layer=mesh.uv_layers.new(name=source.uv_layers.active.name)
    for loop in mesh.loops:uv_layer.data[loop.index].uv=uvs[loop.vertex_index]
    for poly in mesh.polygons:poly.use_smooth=True
    obj.shape_key_add(name='Basis');key=obj.shape_key_add(name='Blink')
    for v,p in zip(key.data,closed):v.co=p
    drive(key,'value',None,'Blink.'+side)
    head_parent(obj,Matrix.Identity(4))
    sub=obj.modifiers.new('Eyelid surface smoothing','SUBSURF');sub.levels=1;sub.render_levels=2
    # Delete only the patch interior; preserve a small overlap under its outer ring.
    cutouts.append([(midx+(x-midx)*.90,midz+(z-midz)*.90) for x,z in outer])
    report['eyes'][side]={'center':list(center),'radius':radius,'lid_vertices':len(verts),'lid_quads':len(faces),'source_cornea_basis':list(map(list,cornea_source.matrix_basis)),'source_cornea_parent_inverse':list(map(list,cornea_source.matrix_parent_inverse))}

bm=bmesh.new();bm.from_mesh(body.data)
remove=[]
for f in bm.faces:
    p=f.calc_center_median()
    if p.y<-.03 and 1.62<p.z<1.68 and abs(p.x)<.08 and any(point_inside(p.x,p.z,poly) for poly in cutouts):remove.append(f)
bmesh.ops.delete(bm,geom=remove,context='FACES')
bm.to_mesh(body.data);bm.free();body.data.update()
report['removed_original_faces']=len(remove)
report['rig_driver_count']=len(rig.animation_data.drivers)
rig.update_tag();bpy.context.view_layer.update()
report['eye_world_bounds']={side:[list(bpy.data.objects['V362_EYE.'+side].matrix_world@Vector(v)) for v in bpy.data.objects['V362_EYE.'+side].bound_box] for side in ('L','R')}
(OUT/'eyes_lids_build.json').write_text(json.dumps(report,indent=2))
scene.render.threads_mode='FIXED';scene.render.threads=1
scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.engine='BLENDER_EEVEE'
scene.render.image_settings.file_format='PNG'
camera=scene.camera;camera.data.type='ORTHO';camera.data.ortho_scale=.40
camera.location=(0,-1.4,1.68);camera.rotation_euler=(Vector((0,0,1.68))-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_eyes_lids_v362.blend'),compress=True)
scene.render.filepath=str(OUT/'v362_eyes_open_front.png');bpy.ops.render.render(write_still=True)
print(json.dumps(report))
