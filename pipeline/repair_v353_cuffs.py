"""Rebuild two textured cuffs and folded hems from the preserved V350 mesh.

Runs through the existing Blender MCP session. V352 files are never overwritten.
The separate cuff objects retain original UVs and interpolated deformation weights.
"""
import bpy
import bmesh
import json
import math
import numpy as np
from mathutils import Vector
from pathlib import Path

root = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
out = root / 'production_v353_cuff_repair'
scene = bpy.context.scene
if scene.get('v353_cuffs_repaired'):
    raise RuntimeError('V353 already built; do not apply the cut twice')
scene.frame_set(1)
body = scene.objects['V352_TRIPO_CHARACTER_BODY_BOUND']
rig = scene.objects['V352_CLOUDRIG_CONTROLS']
source = bpy.data.objects['V353_ORIGINAL_CUFF_REFERENCE']
samples = np.load(root / 'production_v351_cloudrig_fingers/cuff_faces_classified.npz')
skin_faces = set(map(int, samples['face'][samples['skin']]))

lining = bpy.data.materials.new('V353_Dark_Denim_Inner_Hem')
lining.use_nodes = True
lining.diffuse_color = (.013, .016, .019, 1)
shader = lining.node_tree.nodes.get('Principled BSDF')
shader.inputs['Base Color'].default_value = lining.diffuse_color
shader.inputs['Roughness'].default_value = .78
shader.inputs['Sheen Weight'].default_value = .12
noise = lining.node_tree.nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 1100
bump = lining.node_tree.nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .14
bump.inputs['Distance'].default_value = .00008
lining.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
lining.node_tree.links.new(bump.outputs['Normal'], shader.inputs['Normal'])

report = {'source': str(root / 'production_v350_tripo_cloudrig_body/Character_An_CloudRig_body_v350.blend'),
          'preserved_checkpoint': bpy.data.filepath, 'cuffs': {}}
for side, sign in (('L', 1), ('R', -1)):
    # Fit the sloping garment edge to the lowest reliable cloth samples.
    co = samples['co']
    cloth = co[(co[:, 0] * sign > .24) & (co[:, 2] > .85) &
               (co[:, 2] < .913) & ~samples['skin']]
    angles = np.arctan2((cloth[:, 1] - .008) / .063,
                        (cloth[:, 0] * sign - .302) / .047)
    rim = []
    for theta in np.linspace(-math.pi, math.pi, 25)[:-1]:
        group = cloth[np.abs(np.angle(np.exp(1j * (angles - theta)))) < math.pi / 12]
        if len(group):
            rim.append(np.median(group[group[:, 2] <= np.quantile(group[:, 2], .15)], axis=0))
    rim = np.asarray(rim)
    design = np.column_stack((np.ones(len(rim)), rim[:, 0] * sign - .302, rim[:, 1] - .008))
    intercept, dx, dy = np.linalg.lstsq(design, rim[:, 2], rcond=None)[0]
    plane_co = Vector((sign * .302, .008, float(intercept + .001)))
    plane_no = Vector((-float(dx) * sign, -float(dy), 1)).normalized()

    bm = bmesh.new()
    bm.from_mesh(source.data)
    bm.faces.ensure_lookup_table()
    delete = []
    for face in bm.faces:
        center = face.calc_center_median()
        if center.x * sign < .235 or center.z < .835 or center.z > .950:
            delete.append(face)
        elif face.index in skin_faces:
            face.material_index = len(source.data.materials)
    bmesh.ops.delete(bm, geom=delete, context='FACES')
    # Weld only this replacement cuff; per-loop UVs are preserved at atlas seams.
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=.00003)
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                          plane_co=plane_co, plane_no=plane_no,
                          dist=.000001, clear_inner=True)
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                          plane_co=(0, 0, .945), plane_no=(0, 0, 1),
                          dist=.000001, clear_outer=True)
    bottom = [e for e in bm.edges if e.is_boundary and
              all(abs((v.co - plane_co).dot(plane_no)) < .00002 for v in e.verts)]
    if len(bottom) < 30:
        raise RuntimeError(f'Incomplete {side} cuff rim: {len(bottom)} edges')
    # Fold the cut edge inward, then run an inner liner up the sleeve.
    for amount, lift in ((.0015, .0007), (.003, .010)):
        extruded = bmesh.ops.extrude_edge_only(bm, edges=bottom)['geom']
        new_vertices = [v for v in extruded if isinstance(v, bmesh.types.BMVert)]
        for vertex in new_vertices:
            radial = Vector((vertex.co.x - sign * .302, vertex.co.y - .008, 0))
            if radial.length:
                vertex.co -= radial.normalized() * amount
            vertex.co.z += lift
        for face in extruded:
            if isinstance(face, bmesh.types.BMFace):
                face.material_index = len(source.data.materials)
        new_set = set(new_vertices)
        bottom = [e for e in bm.edges if e.is_boundary and all(v in new_set for v in e.verts)]
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    # The upper overlap sits just under the retained source jacket.
    for vertex in bm.verts:
        if vertex.co.z > .933:
            radial = Vector((vertex.co.x - sign * .302, vertex.co.y - .008, 0))
            if radial.length:
                vertex.co -= radial.normalized() * .00015
    mesh = bpy.data.meshes.new('V353_Cuff_Surface.' + side)
    bm.to_mesh(mesh)
    bm.free()
    patch = bpy.data.objects.new('V353_CUFF_PATCH.' + side, mesh)
    scene.collection.objects.link(patch)
    for material in source.data.materials:
        mesh.materials.append(material)
    mesh.materials.append(lining)
    for group in source.vertex_groups:
        patch.vertex_groups.new(name=group.name)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    patch.parent = rig
    patch.matrix_world = body.matrix_world
    modifier = patch.modifiers.new('Existing CloudRig deformation', 'ARMATURE')
    modifier.object = rig
    modifier.use_deform_preserve_volume = True
    patch['source'] = 'V350 original cuff topology, UVs and weights; planar edge fit and folded lining'
    unweighted = sum(not vertex.groups for vertex in mesh.vertices)
    if unweighted:
        raise RuntimeError(f'{side} cuff has {unweighted} unweighted vertices')
    report['cuffs'][side] = {'vertices': len(mesh.vertices), 'faces': len(mesh.polygons),
                            'unweighted_vertices': unweighted,
                            'edge_plane': [float(intercept + .001), float(dx), float(dy)],
                            'plane_fit_rms_mm': float(np.std(rim[:, 2] - design @ [intercept, dx, dy]) * 1000)}

# The new cuffs overlap this retained jacket by 10 mm; no duplicate visible faces.
body.data = body.data.copy()
bm = bmesh.new()
bm.from_mesh(body.data)
remove = [f for f in bm.faces if abs(f.calc_center_median().x) > .235 and
          .83 < f.calc_center_median().z < .935]
report['replaced_jagged_faces'] = len(remove)
bmesh.ops.delete(bm, geom=remove, context='FACES')
bm.to_mesh(body.data)
bm.free()
body.data.update()
bpy.data.objects.remove(source, do_unlink=True)
scene.name = 'V353_CLOUDRIG_CUFFS'
for obj in scene.objects:
    if obj.name.startswith('V352_'):
        obj.name = obj.name.replace('V352_', 'V353_', 1)
scene['v353_cuffs_repaired'] = True
scene['quality_status'] = 'Cuff repair candidate; face, hair, final skin and guitar contact unfinished'
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.threads_mode = 'FIXED'
scene.render.threads = 1
scene.frame_set(1)
bpy.context.view_layer.update()
(out / 'cuff_repair_report.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'Character_An_CloudRig_cuffs_v353.blend'), compress=True)
print(json.dumps(report))
