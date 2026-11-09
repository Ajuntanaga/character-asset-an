"""Replace incompatible silhouette layers and fit the photographed guitar at waist."""
import json
import math
from pathlib import Path
import bpy
from mathutils import Matrix, Vector

ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
OUT=ROOT/'production_v356_reference_guitar'
scene=bpy.context.scene
guitar=bpy.data.objects['V206_GUITAR_ROOT']
rig=next(o for o in scene.objects if o.name.endswith('_CLOUDRIG_CONTROLS'))
points=json.loads((OUT/'wood_outline.json').read_text())['points']
uv_bounds=json.loads((OUT/'wood_uv.json').read_text())

def simple(name,color,roughness,metallic=0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    m.diffuse_color=(*color,1)
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=roughness
    p.inputs['Metallic'].default_value=metallic
    return m

maple=simple('V356_PALE_MAPLE',(.56,.36,.17),.34)
n=maple.node_tree.nodes; l=maple.node_tree.links
coord=n.new('ShaderNodeTexCoord'); mapping=n.new('ShaderNodeVectorMath'); mapping.operation='MULTIPLY'
mapping.inputs[1].default_value=(1.0,85,12)
noise=n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=4; noise.inputs['Detail'].default_value=3
ramp=n.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position=.24; ramp.color_ramp.elements[0].color=(.26,.13,.047,1)
ramp.color_ramp.elements[1].position=.72; ramp.color_ramp.elements[1].color=(.69,.49,.28,1)
l.new(coord.outputs['Generated'],mapping.inputs[0]); l.new(mapping.outputs[0],noise.inputs['Vector'])
l.new(noise.outputs['Fac'],ramp.inputs[0]); l.new(ramp.outputs[0],n['Principled BSDF'].inputs['Base Color'])
edge=simple('V356_NATURAL_MAPLE_EDGE',(.21,.125,.057),.32)
black=simple('V356_BLACK_HARDWARE',(.009,.011,.013),.29,.25)
steel=simple('V356_NICKEL_FRETS',(.43,.45,.48),.23,.9)
top=simple('V356_GRAYBURST_FLAMED_MAPLE',(.16,.17,.155),.29)
n=top.node_tree.nodes; l=top.node_tree.links; p=n['Principled BSDF']
p.inputs['Coat Weight'].default_value=.2; p.inputs['Coat Roughness'].default_value=.25
coord=n.new('ShaderNodeTexCoord')
wave=n.new('ShaderNodeTexWave'); wave.wave_type='BANDS'; wave.bands_direction='X'
wave.inputs['Scale'].default_value=12.5; wave.inputs['Distortion'].default_value=3.2
wave.inputs['Detail'].default_value=2; wave.inputs['Detail Scale'].default_value=.8
l.new(coord.outputs['Generated'],wave.inputs['Vector'])
ramp=n.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position=.05
ramp.color_ramp.elements[0].color=(.065,.071,.063,1)
ramp.color_ramp.elements[1].position=.95; ramp.color_ramp.elements[1].color=(.29,.31,.27,1)
l.new(wave.outputs['Color'],ramp.inputs[0])
burst=n.new('ShaderNodeTexImage'); burst.image=bpy.data.images.load(str(OUT/'wood_edge_distance.png'),check_existing=True)
burst.image.colorspace_settings.name='Non-Color'; burst.extension='CLIP'; burst.image.pack()
l.new(coord.outputs['UV'],burst.inputs['Vector'])
mix=n.new('ShaderNodeMixRGB'); mix.inputs[1].default_value=(.009,.012,.011,1)
l.new(burst.outputs['Color'],mix.inputs[0]); l.new(ramp.outputs[0],mix.inputs[2]); l.new(mix.outputs[0],p.inputs['Base Color'])
grain_map=n.new('ShaderNodeVectorMath'); grain_map.operation='MULTIPLY'; grain_map.inputs[1].default_value=(1,95,3)
grain=n.new('ShaderNodeTexNoise'); grain.inputs['Scale'].default_value=5; grain.inputs['Detail'].default_value=2
bump=n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.055; bump.inputs['Distance'].default_value=.00012
l.new(coord.outputs['Generated'],grain_map.inputs[0]); l.new(grain_map.outputs[0],grain.inputs['Vector'])
l.new(grain.outputs['Fac'],bump.inputs['Height']); l.new(bump.outputs['Normal'],p.inputs['Normal'])

def replace_mesh(name,xy,bottom,upper,material,bevel):
    obj=bpy.data.objects.get(name)
    if obj is None:
        obj=bpy.data.objects.new(name,bpy.data.meshes.new(name+'_mesh'))
        scene.collection.objects.link(obj)
    mesh=bpy.data.meshes.new(name+'_V356_MESH'); count=len(xy)
    vertices=[(x,y,bottom) for x,y in xy]+[(x,y,upper) for x,y in xy]
    # The trace is clockwise in XY; flip it for outward normals if necessary.
    area=sum(xy[i][0]*xy[(i+1)%count][1]-xy[(i+1)%count][0]*xy[i][1] for i in range(count))
    if area<0:
        xy=list(reversed(xy)); vertices=[(x,y,bottom) for x,y in xy]+[(x,y,upper) for x,y in xy]
    faces=[tuple(reversed(range(count))),tuple(range(count,count*2))]
    faces.extend((i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count))
    mesh.from_pydata(vertices,[],faces); mesh.update()
    obj.data=mesh; obj.parent=guitar; obj.matrix_parent_inverse=Matrix.Identity(4); obj.matrix_basis=Matrix.Identity(4)
    obj.hide_render=False; obj.hide_viewport=False; obj.hide_set(False)
    mesh.materials.append(material)
    uv=mesh.uv_layers.new(name='WoodProjection')
    low,high=uv_bounds['lo'],uv_bounds['hi']
    for loop in mesh.loops:
        v=mesh.vertices[loop.vertex_index].co
        uv.data[loop.index].uv=((v.x-low[0])/(high[0]-low[0]),(v.y-low[1])/(high[1]-low[1]))
    for poly in mesh.polygons:
        poly.use_smooth=len(poly.vertices)==4
    obj.modifiers.clear()
    mod=obj.modifiers.new('Rounded wooden perimeter','BEVEL'); mod.width=bevel; mod.segments=4
    mod.limit_method='ANGLE'; mod.angle_limit=.4; mod.harden_normals=True
    norm=obj.modifiers.new('Surface normals','WEIGHTED_NORMAL'); norm.keep_sharp=True
    return obj

replace_mesh('V206_BODY_CORE',points,-.037,.0005,edge,.004)
replace_mesh('V206_FIGURED_TOP',points,.0005,.005,top,.0016)
reveal=bpy.data.objects.get('V318_BODY_REVEAL')
if reveal: reveal.hide_render=True; reveal.hide_set(True)
# Match the real fan at both ends instead of extending the board past the nut.
replace_mesh('V206_FRETBOARD',[(.021,-.0305),(.034,.0305),(.5475,.039),(.5635,-.039)],.008,.016,maple,.0009)
replace_mesh('V206_NECK',[(.010,-.032),(.023,.032),(.602,.043),(.602,-.043)],-.027,.008,maple,.003)
# Electronics cover remains wholly inside the treble-side body and flush on the rear.
replace_mesh('V206_REAR_ELECTRONICS_COVER',[(.64,.070),(.66,.117),(.702,.134),(.733,.082),(.704,.050)],-.0375,-.0365,black,.001)
for i,xy in enumerate(((.652,.074),(.666,.114),(.700,.125),(.722,.081)),1):
    obj=bpy.data.objects.get(f'V206_REAR_COVER_SCREW_{i}')
    if obj: obj.location=(*xy,-.038)
for prefix,x,angle in [('NECK',.578,8),('BRIDGE',.670,12)]:
    a=math.radians(angle); pickup=bpy.data.objects[f'V206_PICKUP_{prefix}']
    pickup.location=(x,0,.014); pickup.rotation_euler.z=a
    for i,y in enumerate((-.041,.041),1):
        obj=bpy.data.objects.get(f'V206_{prefix}_MOUNT_SCREW_{i}')
        if obj: obj.location=(x-math.sin(a)*y,math.cos(a)*y,.0218)
for name,loc in {'V206_CONTROL_KNOB_1':(.704,.077,.016),'V206_CONTROL_KNOB_2':(.699,.132,.016),
                 'V206_CONTROL_SWITCH_BASE':(.650,.101,.010),
                 'V206_STRAP_BUTTON_1':(.824,-.087,-.017),'V206_STRAP_BUTTON_2':(.402,-.132,-.017)}.items():
    bpy.data.objects[name].location=loc
toggle=bpy.data.objects['V206_CONTROL_SWITCH_TOGGLE'].data.splines[0]
toggle.points[0].co=(.650,.101,.014,1); toggle.points[1].co=(.658,.101,.031,1)
lock=bpy.data.objects['V206_HEADLESS_STRING_LOCK']; lock.location=(.015,0,.013); lock.rotation_euler.z=-.253
for obj in guitar.children_recursive:
    if obj.type not in {'MESH','CURVE'}: continue
    if obj.name.startswith(('V206_PICKUP','V206_BRIDGE_','V206_CONTROL_','V206_NUT_LOCK_','V206_HEADLESS_')):
        obj.data.materials.clear(); obj.data.materials.append(black)
    elif obj.name.startswith(('V206_INLAY_')):
        obj.data.materials.clear(); obj.data.materials.append(black)
    elif obj.name.startswith(('V206_STRING_','V206_FRETS','V206_SADDLE_')):
        obj.data.materials.clear(); obj.data.materials.append(steel)
# Waist placement: body centre at x=-.12, z=.99, near the jacket front.
theta=math.radians(27)
x=Vector((-math.cos(theta),0,-math.sin(theta)))
z=Vector((0,-1,0)); y=z.cross(x)
rotation=Matrix((x,y,z)).transposed()
centre=Vector((-.12,-.225,1.00))
location=centre-rotation@Vector((.665,0,0))
guitar.matrix_world=rotation.to_4x4(); guitar.location=location
for obj in scene.objects:
    if obj.name.startswith('V355_'): obj.name=obj.name.replace('V355_','V356_',1)
scene.name='V356_REFERENCE_GUITAR'
scene['quality_status']='Reference silhouette and waist placement rebuilt; hands not fitted yet'
bpy.context.view_layer.update()
camera=scene.camera
scene.render.engine='BLENDER_WORKBENCH'; scene.display.shading.color_type='TEXTURE'
scene.render.threads_mode='FIXED'; scene.render.threads=1
scene.render.resolution_x=900; scene.render.resolution_y=1100
scene.render.resolution_percentage=100; scene.render.image_settings.file_format='PNG'
camera.data.type='ORTHO'; camera.data.ortho_scale=2.05
for label,position,target,scale in (
    ('front',(.10,-4,1.02),(.10,0,.96),2.05),
    ('side',(3.5,-2.5,1.10),(.10,0,.96),2.05),
    ('guitar',guitar.matrix_world@Vector((.43,0,2.0)),guitar.matrix_world@Vector((.43,0,0)),.96)):
    camera.location=position; camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=scale
    scene.render.filepath=str(OUT/f'v356_{label}.png'); bpy.ops.render.render(write_still=True)
camera.location=(.10,-4,1.02); camera.rotation_euler=(Vector((.10,0,.96))-camera.location).to_track_quat('-Z','Y').to_euler(); camera.data.ortho_scale=2.05
report=dict(outline_vertices=len(points),driver_count=len(rig.animation_data.drivers),
            guitar_matrix=[list(r) for r in guitar.matrix_world],
            source='references/props/strandberg/strandberg_full_product.jpg',
            changes=['coherent smooth wood silhouette','correct bass/treble side','maple fretboard',
                     'pickup angles follow string fan','rear cover inside body','waist placement'],
            pending=['arm and finger contact','full material lighting render'])
(OUT/'guitar_rebuild.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_reference_guitar_v356.blend'),compress=True)
print(json.dumps(report))
