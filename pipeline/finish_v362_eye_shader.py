"""Metric eye shading that works in the live EEVEE preview and in Cycles."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'production_v362_face_anatomy'
mat=bpy.data.materials.get('V362_BROWN_EYE_SURFACE') or bpy.data.materials.new('V362_BROWN_EYE_SURFACE')
mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear();nodes=nt.nodes;links=nt.links
def node(kind,name):
    n=nodes.new(kind);n.label=name;return n
def mathnode(op,a,b=None):
    n=node('ShaderNodeMath',op);n.operation=op
    for i,v in enumerate([a,b]):
        if v is None:continue
        if isinstance(v,(float,int)):n.inputs[i].default_value=v
        else:links.new(v,n.inputs[i])
    return n.outputs[0]
def ramp(value,stops):
    n=node('ShaderNodeValToRGB','Radial mask / iris pigment');links.new(value,n.inputs[0])
    for e in list(n.color_ramp.elements)[1:]:n.color_ramp.elements.remove(e)
    for i,(position,color) in enumerate(stops):
        e=n.color_ramp.elements[0] if i==0 else n.color_ramp.elements.new(position)
        e.position=position;e.color=color
    return n.outputs['Color']
def mix(fac,a,b):
    n=node('ShaderNodeMixRGB','Blend eye tissue');n.blend_type='MIX';links.new(fac,n.inputs[0])
    for i,v in [(1,a),(2,b)]:
        if isinstance(v,tuple):n.inputs[i].default_value=v
        else:links.new(v,n.inputs[i])
    return n.outputs[0]
tex=node('ShaderNodeTexCoord','Eye-local metric coordinates')
xyz=node('ShaderNodeSeparateXYZ','Eye local axes');links.new(tex.outputs['Object'],xyz.inputs[0])
rad=mathnode('SQRT',mathnode('ADD',mathnode('MULTIPLY',xyz.outputs['X'],xyz.outputs['X']),mathnode('MULTIPLY',xyz.outputs['Y'],xyz.outputs['Y'])))
angle=mathnode('ARCTAN2',xyz.outputs['Y'],xyz.outputs['X'])
polar=node('ShaderNodeCombineXYZ','Stretched radial iris fibers')
links.new(mathnode('MULTIPLY',angle,18.0),polar.inputs[0]);links.new(mathnode('MULTIPLY',rad,330.0),polar.inputs[1])
noise=node('ShaderNodeTexNoise','Iris radial fibers');noise.inputs['Scale'].default_value=3.0;noise.inputs['Detail'].default_value=3.0;noise.inputs['Roughness'].default_value=.72
links.new(polar.outputs[0],noise.inputs['Vector'])
iris=ramp(noise.outputs['Fac'],[(.22,(.012,.0037,.0014,1)),(.5,(.048,.016,.0048,1)),(.8,(.135,.060,.018,1))])
unitrad=mathnode('MULTIPLY',rad,200.0)
iris_mask=ramp(unitrad,[(.67,(1,1,1,1)),(.74,(0,0,0,1))])
limbus=ramp(unitrad,[(.58,(1,1,1,1)),(.70,(0,0,0,1))])
iris=mix(limbus,(.008,.0027,.0015,1),iris)
color=mix(iris_mask,(.62,.54,.47,1),iris)
pupil=ramp(unitrad,[(.28,(1,1,1,1)),(.32,(0,0,0,1))])
color=mix(pupil,color,(.0006,.00035,.0002,1))
bsdf=node('ShaderNodeBsdfPrincipled','Moist eye tissue');links.new(color,bsdf.inputs['Base Color'])
for k,v in [('Roughness',.24),('IOR',1.38),('Specular IOR Level',.32),('Coat Weight',.3),('Coat Roughness',.045),('Subsurface Weight',.025),('Subsurface Scale',.001)]:
    if k in bsdf.inputs:bsdf.inputs[k].default_value=v
out=node('ShaderNodeOutputMaterial','Eye output');links.new(bsdf.outputs[0],out.inputs['Surface'])
for side in ('L','R'):
    eye=bpy.data.objects['V362_EYE.'+side];eye.data.materials.clear();eye.data.materials.append(mat)
    lids=bpy.data.objects['V362_LIDS.'+side]
    if not lids.get('v362_overlap_offset'):
        for key in lids.data.shape_keys.key_blocks:
            for v in key.data:v.co.y-=.00065
        lids['v362_overlap_offset']=.00065
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];head=rig.pose.bones['Head'];scene=bpy.context.scene
scene.camera.location=(0,-1.4,1.66);scene.camera.rotation_euler=(Vector((0,0,1.66))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
def render(name):
    rig.update_tag();bpy.context.view_layer.update();scene.render.filepath=str(OUT/f'{name}.png');bpy.ops.render.render(write_still=True)
head['Blink.L']=head['Blink.R']=0.0;head['GazeHorizontal']=head['GazeVertical']=0.0
render('v362_brown_eyes_front')
head['Blink.L']=head['Blink.R']=1.0;render('v362_brown_eyes_blink')
head['Blink.L']=head['Blink.R']=0.0;head['GazeHorizontal']=15.0;render('v362_brown_eyes_gaze')
head['GazeHorizontal']=0.0;rig.update_tag();bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_eyes_lids_v362.blend'),compress=True)
print(json.dumps({'eye_material':mat.name,'rig_drivers':len(rig.animation_data.drivers),'controls_restored':True}))
