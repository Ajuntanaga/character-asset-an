"""Replace the distorted legacy iris surface with continuous metric eye rings."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parents[1]/'production_v362_face_anatomy'
def material(name,color,roughness,coat=0):
    mat=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes=True; mat.node_tree.nodes.clear()
    out=mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
    bs=mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=roughness
    bs.inputs['IOR'].default_value=1.376
    bs.inputs['Coat Weight'].default_value=coat
    bs.inputs['Coat Roughness'].default_value=.12
    mat.node_tree.links.new(bs.outputs[0],out.inputs['Surface'])
    return mat,bs

sclera,bs=material('V362_SCLERA',(0.40,.345,.29),.28,.18)
bs.inputs['Subsurface Weight'].default_value=.035
bs.inputs['Subsurface Scale'].default_value=.0006
iris,bs=material('V362_IRIS_PIGMENT',(.045,.017,.006),.30,.12)
nodes=iris.node_tree.nodes;links=iris.node_tree.links
uv=nodes.new('ShaderNodeTexCoord');separate=nodes.new('ShaderNodeSeparateXYZ')
links.new(uv.outputs['UV'],separate.inputs[0])
polar=nodes.new('ShaderNodeCombineXYZ')
for axis,factor in [('X',180.),('Y',3.)]:
    mul=nodes.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=factor
    links.new(separate.outputs[axis],mul.inputs[0]);links.new(mul.outputs[0],polar.inputs[axis])
noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1.;noise.inputs['Detail'].default_value=4.
links.new(polar.outputs[0],noise.inputs['Vector'])
ramp=nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position=.20;ramp.color_ramp.elements[0].color=(.008,.0027,.0009,1)
ramp.color_ramp.elements[1].position=.8;ramp.color_ramp.elements[1].color=(.11,.044,.012,1)
links.new(noise.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs[0],bs.inputs['Base Color'])
limbus,_=material('V362_LIMBAL_RING',(.008,.003,.001),.30,.10)
pupil,_=material('V362_PUPIL_CAVITY',(.0003,.0002,.0001),.5,0)
mats=[sclera,limbus,iris,pupil]
segments=96;radius=.01155
# Back-to-front rings, then a concave iris and closed pupil cavity.
rings=[(radius*math.sin(t),radius*math.cos(t),0) for t in [math.pi-.015-(math.pi-.015-.303)*i/39 for i in range(40)]]
rings += [(.00336,.01105,1),(.00323,.01100,1),(.00312,.01092,2),(.00282,.01076,2),(.00242,.01060,2),(.00198,.01046,2),(.00155,.01038,2),(.00137,.01034,2),(.00135,.01022,3),(.00005,.01020,3)]
verts=[];faces=[];face_mats=[]
for r,z,_ in rings:
    for i in range(segments):
        a=2*math.pi*i/segments;verts.append((r*math.cos(a),r*math.sin(a),z))
for j in range(len(rings)-1):
    for i in range(segments):
        n=(i+1)%segments
        faces.append((j*segments+i,j*segments+n,(j+1)*segments+n,(j+1)*segments+i))
        face_mats.append(rings[j+1][2])
faces += [tuple(reversed(range(segments))),tuple((len(rings)-1)*segments+i for i in range(segments))]
face_mats += [0,3]
for side in ('L','R'):
    obj=bpy.data.objects['V362_EYE.'+side]
    old=obj.data;old.use_fake_user=True
    mesh=bpy.data.meshes.new('V362_CONTINUOUS_EYE.'+side);mesh.from_pydata(verts,[],faces);mesh.update()
    for m in mats:mesh.materials.append(m)
    uv=mesh.uv_layers.new(name='IrisPolar')
    for poly,mi in zip(mesh.polygons,face_mats):
        poly.material_index=mi;poly.use_smooth=True
        ids=[mesh.loops[k].vertex_index%segments for k in poly.loop_indices]
        crosses=0 in ids and segments-1 in ids
        for li in poly.loop_indices:
            vi=mesh.loops[li].vertex_index;u=(vi%segments)/segments
            if crosses and u==0:u=1.
            uv.data[li].uv=(u,rings[vi//segments][0]/.00336)
    obj.data=mesh
    for mod in list(obj.modifiers):obj.modifiers.remove(mod)
    bpy.data.objects['V362_CORNEA.'+side].hide_render=True
    bpy.data.objects['V362_CORNEA.'+side].hide_set(True)
scene=bpy.context.scene;rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];head=rig.pose.bones['Head']
def render(name,gaze=0,blink=0):
    head['GazeHorizontal']=gaze;head['Blink.L']=head['Blink.R']=blink
    rig.update_tag();bpy.context.view_layer.update()
    scene.render.filepath=str(OUT/f'{name}.png');bpy.ops.render.render(write_still=True)
render('v362_continuous_eyes_front')
render('v362_continuous_eyes_gaze',15)
head['GazeHorizontal']=0.;rig.update_tag();bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_eyes_lids_v362.blend'),compress=True)
print(json.dumps({'continuous_eye_vertices':len(verts),'eye_faces':len(faces),'rig_drivers':len(rig.animation_data.drivers)}))
