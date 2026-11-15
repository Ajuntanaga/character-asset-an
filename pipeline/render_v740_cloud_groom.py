"""Cloud groom review; neutral by default, optionally using the staged photo atlas."""
from pathlib import Path
import json
import math
import bpy
from mathutils import Matrix, Vector

OUT = Path('results/renders')
OUT.mkdir(parents=True, exist_ok=True)
names = ['V740_NATIVE_FACE', 'V737_GAZE.L', 'V737_GAZE.R', 'V737_EYE.L', 'V737_EYE.R',
         'V738_CORNEA.L', 'V738_CORNEA.R', 'V739_ORAL_CAVITY', 'V737_DENTAL_UPPER',
         'V739_DENTAL_LOWER', 'V739_DENTAL_TONGUE', 'V740_NATIVE_CURLS',
         'V740_NATIVE_UNDERCOAT', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS']
names += list(globals().get('EXTRA_OBJECTS', []))
excluded = set(globals().get('EXCLUDE_OBJECTS', []))
assert excluded <= set(names), excluded
names = [name for name in names if name not in excluded]
head = bpy.data.objects['V740_NATIVE_FACE']
texture_path = globals().get('TEXTURE_PATH')
if texture_path:
    texture_path = Path(texture_path).resolve()
    assert texture_path.is_file(), texture_path
    # Load a fresh file image rather than reloading the checkpoint's packed image.
    atlas = bpy.data.images.load(str(texture_path), check_existing=False)
    assert atlas.size[0] > 0 and atlas.size[1] > 0, 'Photo atlas has no pixels'
    matched = 0
    for material in head.data.materials:
        if material and material.use_nodes:
            for node in material.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image and Path(node.image.filepath).name == globals().get('TEXTURE_SOURCE_NAME', texture_path.name):
                    node.image = atlas
                    matched += 1
    assert matched, 'Expected native face basecolor image node missing'
elif not globals().get('PRESERVE_MATERIALS', False):
    clay = bpy.data.materials.new('Cloud groom review neutral head')
    clay.use_nodes = True
    shader = clay.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (.25, .25, .25, 1)
    shader.inputs['Roughness'].default_value = .7
    head.data.materials.clear()
    head.data.materials.append(clay)
    for polygon in head.data.polygons:
        polygon.material_index = 0
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
head_ctrl = rig.pose.bones['Head']
head_fk = rig.pose.bones['FK-Head']
head_basis = head_fk.matrix_basis.copy()
head_turn = float(globals().get('HEAD_TURN_DEGREES', 0.))
head_turn_evaluated = 0.
source_scene = bpy.context.scene
production = bpy.data.filepath
assert not bpy.app.is_job_running('RENDER')
assert bpy.data.scenes.get('V740_LIVE_PREVIEW') is None
assert all(name in bpy.data.objects for name in names)
scene = bpy.data.scenes.new('V740_LIVE_PREVIEW')
visibility, created, results, saved_props = {}, [], [], {}
camera_records = {}
world = None
target = Vector(globals().get('CAMERA_TARGET', (0, -.015, 1.640)))

def add(name, data):
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    created.append((obj, data))
    return obj

def aim(obj):
    obj.rotation_euler = (target-obj.location).to_track_quat('-Z', 'Y').to_euler()

try:
    for name in names+[rig.name]:
        obj = bpy.data.objects[name]
        visibility[name] = (obj.hide_render, obj.hide_viewport)
        obj.hide_render = False
        obj.hide_viewport = False
        scene.collection.objects.link(obj)
        obj.hide_set(False, view_layer=scene.view_layers[0])
    # Head is constrained to FK-Head; its local Y axis runs up the neck.
    before_head = head_ctrl.matrix.to_quaternion()
    if head_turn:
        head_fk.matrix_basis = head_basis @ Matrix.Rotation(math.radians(head_turn), 4, 'Y')
    for prop, value in globals().get('POSE', {}).items():
        saved_props[prop] = head_ctrl[prop]
        head_ctrl[prop] = value
    rig.update_tag(refresh={'OBJECT'})
    bpy.context.view_layer.update()
    if head_turn:
        head_turn_evaluated = math.degrees(before_head.rotation_difference(head_ctrl.matrix.to_quaternion()).angle)
        assert head_turn_evaluated > abs(head_turn)*.8, 'FK head turn did not reach evaluated head'
    camera = add('V740_PREVIEW_CAMERA', bpy.data.cameras.new('V740_PREVIEW_CAMERA'))
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = globals().get('ORTHO_SCALE', .35)
    scene.camera = camera
    for label, location, power, size in [('KEY',(-.5,-.7,2.15),65,.14),('FILL',(.55,-.5,1.72),25,.30),('RIM',(.4,.45,2),45,.25)]:
        light = add('V740_PREVIEW_'+label, bpy.data.lights.new('V740_PREVIEW_'+label, 'AREA'))
        light.location = location
        light.data.energy = power
        light.data.shape = 'DISK'
        light.data.size = size
        aim(light)
    world = bpy.data.worlds.new('V740_PREVIEW_WORLD')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (.18,.18,.18,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = .35
    scene.world = world
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = globals().get('SAMPLES', 24)
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = globals().get('ADAPTIVE_THRESHOLD', .08)
    scene.cycles.use_denoising = globals().get('DENOISE', True)
    scene.cycles.max_bounces = 6
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 2
    scene.render.resolution_x, scene.render.resolution_y = globals().get('RESOLUTION', (512, 640))
    border = globals().get('BORDER')
    if border:
        x0, x1, y0, y1 = border
        assert 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1
        scene.render.use_border = True
        scene.render.use_crop_to_border = True
        scene.render.border_min_x, scene.render.border_max_x = x0, x1
        scene.render.border_min_y, scene.render.border_max_y = y0, y1
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = globals().get('VIEW_TRANSFORM', 'AgX')
    scene.view_settings.exposure = globals().get('EXPOSURE', -1.3)
    for view in globals().get('VIEWS', ['front', 'three_quarter', 'three_quarter_reference_side']):
        if view == 'reference_orientation':
            # The donor was nonlinearly rescaled: reuse orientation only, not its
            # original translation or perspective fit. Keep framing comparable.
            fitted = json.loads((Path(__file__).resolve().parent.parent /
                'references/derived/photoreal_facebuilder_v1/fitted_cameras_v326.json').read_text())
            rotation = Matrix(fitted['three_quarter']['matrix']).to_3x3()
            camera.location = target + rotation.col[2].normalized()*.9
            camera.rotation_euler = rotation.to_euler()
        else:
            camera.location = {'front': (0,-.9,1.640), 'profile': (-.9,-.015,1.640),
                               'three_quarter': (-.65,-.665,1.640),
                               'three_quarter_reference_side': (.65,-.665,1.640)}[view]
            aim(camera)
        camera_records[view] = {'location': list(camera.location),
            'rotation_euler': list(camera.rotation_euler), 'type': camera.data.type,
            'ortho_scale': camera.data.ortho_scale,
            'reference_orientation_only': view == 'reference_orientation'}
        scene.render.filepath = str(OUT/(globals().get('TAG','v740_neutral')+'_'+view+'.png'))
        bpy.ops.render.render(write_still=True, scene=scene.name)
        results.append(scene.render.filepath)
finally:
    head_fk.matrix_basis = head_basis
    for prop, value in saved_props.items():
        head_ctrl[prop] = value
    rig.update_tag(refresh={'OBJECT'})
    for name, flags in visibility.items():
        obj = bpy.data.objects[name]
        obj.hide_render, obj.hide_viewport = flags
    bpy.data.scenes.remove(scene)
    for obj, data in created:
        bpy.data.objects.remove(obj, do_unlink=True)
        if isinstance(data, bpy.types.Camera):
            bpy.data.cameras.remove(data)
        elif isinstance(data, bpy.types.Light):
            bpy.data.lights.remove(data)
    if world:
        bpy.data.worlds.remove(world)
    bpy.context.view_layer.update()
# Record the actual inherited ocular setup alongside every preview. This is
# read-only and avoids loading a second Blender locally to inspect the checkpoint.
def describe_eye_tree(tree, ancestors=()):
    if tree is None:
        return {'nodes': [], 'links': []}
    if tree.as_pointer() in ancestors:
        return {'recursive_group': tree.name}
    ancestors = (*ancestors, tree.as_pointer())
    nodes = []
    for node in tree.nodes:
        inputs = {}
        for socket in node.inputs:
            if not hasattr(socket, 'default_value'):
                continue
            value = socket.default_value
            if isinstance(value, (bool, int, float, str)):
                inputs[socket.name] = value
            elif hasattr(value, '__len__'):
                inputs[socket.name] = list(value)
        record = {'name': node.name, 'type': node.bl_idname, 'inputs': inputs,
                  'image': node.image.name if node.type == 'TEX_IMAGE' and node.image else None}
        if node.type == 'GROUP' and node.node_tree:
            record['group_name'] = node.node_tree.name
            record['group_tree'] = describe_eye_tree(node.node_tree, ancestors)
        nodes.append(record)
    return {'nodes': nodes, 'links': [
        {'from_node': link.from_node.name, 'from_socket': link.from_socket.name,
         'to_node': link.to_node.name, 'to_socket': link.to_socket.name}
        for link in tree.links]}


eye_setup = {}
for name in ['V737_EYE.L', 'V737_EYE.R', 'V738_CORNEA.L', 'V738_CORNEA.R']:
    obj = bpy.data.objects[name]
    materials = []
    for material in obj.data.materials:
        if material is None:
            materials.append(None)
            continue
        materials.append({'name': material.name,
                          **describe_eye_tree(material.node_tree if material.use_nodes else None)})
    eye_setup[name] = {'parent': obj.parent.name if obj.parent else None,
                       'dimensions': list(obj.dimensions),
                       'matrix_world': [list(row) for row in obj.matrix_world],
                       'materials': materials}
report = {'review_scope': ('native photo skin and groom appearance; animation not evaluated' if texture_path else 'scalp, brow and beard shape and coverage; skin and animation not evaluated'), 'renders': results, 'eye_setup': eye_setup, 'cameras': camera_records, 'excluded_objects': sorted(excluded), 'restored_properties': saved_props,
          'render_settings': {'resolution': globals().get('RESOLUTION', (512, 640)),
              'border': globals().get('BORDER'), 'samples': globals().get('SAMPLES', 24),
              'denoise': globals().get('DENOISE', True)},
          'head_turn_degrees': head_turn, 'evaluated_head_turn_degrees': head_turn_evaluated,
          'head_basis_restored': all(abs(head_fk.matrix_basis[i][j]-head_basis[i][j]) < 1e-6 for i in range(4) for j in range(4)),
          'rig_drivers': len(rig.animation_data.drivers),
          'production_unchanged': bpy.data.filepath == production and bpy.context.scene == source_scene}
(OUT.parent/(globals().get('TAG','v740_neutral')+'_render_report.json')).write_text(json.dumps(report, indent=2))
print(json.dumps(report))
