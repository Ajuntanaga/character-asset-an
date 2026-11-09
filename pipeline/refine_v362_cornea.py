"""Reduce the iris diameter and fit shallow transparent corneas inside the lids."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'production_v362_face_anatomy'
scene=bpy.context.scene
source=bpy.data.objects['V362_SOURCE_Eyeball'].data
mat=bpy.data.materials.get('V362_CORNEA_PHYSICAL') or bpy.data.materials.new('V362_CORNEA_PHYSICAL')
mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear();links=mat.node_tree.links
out=nodes.new('ShaderNodeOutputMaterial');mix=nodes.new('ShaderNodeMixShader')
transparent=nodes.new('ShaderNodeBsdfTransparent');gloss=nodes.new('ShaderNodeBsdfGlossy')
gloss.inputs['Color'].default_value=(1,1,1,1);gloss.inputs['Roughness'].default_value=.025
fresnel=nodes.new('ShaderNodeFresnel');fresnel.inputs['IOR'].default_value=1.376
links.new(fresnel.outputs[0],mix.inputs[0]);links.new(transparent.outputs[0],mix.inputs[1]);links.new(gloss.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs['Surface'])
mat.surface_render_method='DITHERED'
for side in ('L','R'):
    eye=bpy.data.objects['V362_EYE.'+side]
    for target_key,source_key in zip(eye.data.shape_keys.key_blocks,source.shape_keys.key_blocks):
        for v,original in zip(target_key.data,source_key.data):
            x,y,z=original.co
            radial=math.hypot(x,y)
            if z>.005 and radial<.0105:
                t=max(0,min(1,(radial-.0045)/.006))
                factor=.64+.36*(3*t*t-2*t*t*t)
                x*=factor;y*=factor
            v.co=(x,y,z)
    eye.data.shape_keys.key_blocks['Dilation'].value=.23
    cornea=bpy.data.objects['V362_CORNEA.'+side]
    verts=[(0,0,.01165)];faces=[];segments=64;rings=12
    for j in range(1,rings+1):
        r=.00465*j/rings
        z=math.sqrt(.01155**2-r*r)+.00010*(1-(j/rings)**2)
        for i in range(segments):
            a=i*2*math.pi/segments;verts.append((r*math.cos(a),r*math.sin(a),z))
    for i in range(segments):faces.append((0,1+i,1+(i+1)%segments))
    for j in range(rings-1):
        a=1+j*segments;b=a+segments
        for i in range(segments):
            n=(i+1)%segments;faces.append((a+i,b+i,b+n,a+n))
    mesh=bpy.data.meshes.new('V362_CORNEA_FITTED.'+side);mesh.from_pydata(verts,[],faces);mesh.update()
    for p in mesh.polygons:p.use_smooth=True
    mesh.materials.append(mat);cornea.data=mesh
    cornea.matrix_basis=Matrix.Identity(4);cornea.matrix_parent_inverse=Matrix.Identity(4)
    for mod in list(cornea.modifiers):cornea.modifiers.remove(mod)
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];head=rig.pose.bones['Head']
scene.render.resolution_x=scene.render.resolution_y=1000
scene.camera.data.ortho_scale=.34
def render(label,pos,target):
    scene.camera.location=pos;scene.camera.rotation_euler=(Vector(target)-scene.camera.location).to_track_quat('-Z','Y').to_euler()
    rig.update_tag();bpy.context.view_layer.update()
    scene.render.filepath=str(OUT/f'v362_{label}.png');bpy.ops.render.render(write_still=True)
render('eyes_refined_front',(0,-1.4,1.66),(0,0,1.66))
head['Blink.L']=head['Blink.R']=1.0
render('blink_front',(0,-1.4,1.66),(0,0,1.66))
head['Blink.L']=head['Blink.R']=0.0
render('eyes_refined_three_quarter',(.8,-1.2,1.66),(0,0,1.66))
scene.camera.location=(0,-1.4,1.66);scene.camera.rotation_euler=(Vector((0,0,1.66))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_eyes_lids_v362.blend'),compress=True)
print(json.dumps({'rig_driver_count':len(rig.animation_data.drivers),'eye_key_values':[(k.name,k.value) for k in bpy.data.objects['V362_EYE.L'].data.shape_keys.key_blocks],'blink_values':[head['Blink.L'],head['Blink.R']]}))
