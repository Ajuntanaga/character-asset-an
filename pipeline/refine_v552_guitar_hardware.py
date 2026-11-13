"""Reversible rounded bridge housings, pickup covers and blade selector.

Dimensions follow the supplied Strandberg product photograph. Saddle positions,
strings, pickups, controls and the guitar root keep their existing transforms.
"""
import math
import bpy
from mathutils import Matrix, Vector


def build():
    assert not bpy.data.objects.get('V552_Housing_S1')
    guitar = bpy.data.objects['V206_GUITAR_ROOT']
    rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
    assert len(rig.animation_data.drivers) == 1957
    saddles = {f'V206_SADDLE_S{i}': bpy.data.objects[f'V206_SADDLE_S{i}'].matrix_world.copy()
               for i in range(1, 9)}
    created, hidden = [], {}

    def material(name, color, roughness, metallic):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        node = mat.node_tree.nodes.get('Principled BSDF')
        node.inputs['Base Color'].default_value = (*color, 1)
        node.inputs['Roughness'].default_value = roughness
        node.inputs['Metallic'].default_value = metallic
        return mat

    black = material('V552_Black_Anodized', (.009, .011, .012), .32, .80)
    cover = material('V552_Pickup_Cover', (.009, .011, .012), .43, .05)
    recess = material('V552_Recess', (.002, .0025, .003), .53, .15)
    steel = material('V552_Machined_Steel', (.23, .25, .26), .25, .95)
    lettering = material('V552_Pickup_Lettering', (.16, .17, .17), .48, .10)

    def mesh(name, vertices, faces, mat, parent=guitar, bevel=0, smooth=False):
        data = bpy.data.meshes.new(name)
        data.from_pydata(vertices, [], faces)
        data.update()
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
        obj.parent = parent
        obj.matrix_parent_inverse = Matrix.Identity(4)
        data.materials.append(mat)
        for face in data.polygons:
            face.use_smooth = smooth and len(face.vertices) == 4
        if bevel:
            mod = obj.modifiers.new('Machined edge radius', 'BEVEL')
            mod.width = bevel
            mod.segments = 3
            mod.limit_method = 'ANGLE'
            mod.harden_normals = True
            obj.modifiers.new('Face normals', 'WEIGHTED_NORMAL')
        created.append(obj.name)
        return obj

    def capsule(length, radius, center=(0, 0), count=20):
        half = length / 2 - radius
        return [(center[0] + end * half + radius * math.cos(angle),
                 center[1] + radius * math.sin(angle))
                for end, start in ((1, -math.pi / 2), (-1, math.pi / 2))
                for angle in [start + math.pi * i / count for i in range(count + 1)]]

    def extrude(name, outline, bottom, top, mat, parent=guitar, bevel=0):
        n = len(outline)
        vertices = [(x, y, z) for z in (bottom, top) for x, y in outline]
        faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
        faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
        return mesh(name, vertices, faces, mat, parent, bevel)

    def hide(obj):
        hidden[obj.name] = {'hide_render': obj.hide_render, 'hide_set': obj.hide_get()}
        obj.hide_render = True
        obj.hide_set(True)

    for obj in list(bpy.data.objects):
        if obj.name.startswith(('V476_TUNER_', 'V477_')):
            hide(obj)
    for name in ('V206_CONTROL_SWITCH_BASE', 'V206_CONTROL_SWITCH_TOGGLE'):
        hide(bpy.data.objects[name])

    for index in range(1, 9):
        saddle = bpy.data.objects[f'V206_SADDLE_S{index}']
        # Reference saddles are black; only the small adjuster sockets are steel.
        # Copy mesh data so shared source materials and string endpoints stay intact.
        saddle.data = saddle.data.copy()
        saddle.data.materials.clear()
        saddle.data.materials.append(black)
        x, y, _ = saddle.location
        outer = capsule(.043, .0048, (x + .0135, y))
        inner = capsule(.029, .0029, (x + .009, y))
        n = len(outer)
        vertices = [(a, b, .009) for a, b in outer]
        # Curved top follows a barrel section; the inset is an actual open slot.
        for outline in (outer, inner):
            vertices += [(a, b, .021 + .011 * math.sqrt(max(0, 1 - ((b - y) / .006) ** 2)))
                         for a, b in outline]
        vertices += [(a, b, .019) for a, b in inner]
        faces = [tuple(reversed(range(n))), tuple(range(3 * n, 4 * n))]
        for ring in range(3):
            for i in range(n):
                j = (i + 1) % n
                faces.append((ring * n + i, ring * n + j, (ring + 1) * n + j, (ring + 1) * n + i))
        mesh(f'V552_Housing_S{index}', vertices, faces, black, bevel=.00016, smooth=True)

        # Axial tuner with shallow longitudinal knurling.
        rings = ((.034, .0043), (.035, .0047), (.050, .0047), (.051, .0042))
        count = 96
        vertices = []
        for dx, radius in rings:
            for k in range(count):
                angle = math.tau * k / count
                rad = radius - (.00020 if k % 3 == 1 and .035 <= dx <= .050 else 0)
                vertices.append((x + dx, y + rad * math.cos(angle), .0205 + rad * math.sin(angle)))
        faces = [tuple(reversed(range(count))), tuple(range(3 * count, 4 * count))]
        faces += [(r * count + i, r * count + (i + 1) % count,
                   (r + 1) * count + (i + 1) % count, (r + 1) * count + i)
                  for r in range(3) for i in range(count)]
        mesh(f'V552_Tuner_S{index}', vertices, faces, black, bevel=.00008, smooth=True)
        # Socket head remains below the string in the open bridge slot.
        rings = ((.0017, .023), (.0017, .0242), (.0008, .0242), (.0008, .0233))
        vertices = [(x + .013 + radius * math.cos(math.tau * k / 24),
                     y + radius * math.sin(math.tau * k / 24), height)
                    for radius, height in rings for k in range(24)]
        faces = [(r * 24 + i, r * 24 + (i + 1) % 24,
                  (r + 1) * 24 + (i + 1) % 24, (r + 1) * 24 + i)
                 for r in range(3) for i in range(24)] + [tuple(range(72, 96))]
        mesh(f'V552_Adjuster_S{index}', vertices, faces, steel, bevel=.00006)

    # The photographed selector is a narrow slot and inclined blade, not a post.
    axis = Vector((.91, .41)); axis.normalize()
    across = Vector((-axis.y, axis.x))
    center = Vector((.650, .101))

    def switch_outline(length, radius):
        return [tuple(center + axis * x + across * y) for x, y in capsule(length, radius)]

    extrude('V552_Selector_Rim', switch_outline(.034, .0019), .0051, .0055, steel)
    extrude('V552_Selector_Slot', switch_outline(.032, .0013), .0055, .0057, recess)
    vertices = []
    for height, lean in ((.0057, 0), (.017, .004)):
        for a, b in ((-.0014, -.00055), (.0014, -.00055), (.0014, .00055), (-.0014, .00055)):
            point = center + axis * (a + lean) + across * b
            vertices.append((*point, height))
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh('V552_Selector_Blade', vertices, faces, steel, bevel=.00012)
    tip = [tuple(center + axis * (x + .004) + across * y) for x, y in capsule(.0065, .0016)]
    extrude('V552_Selector_Tip', tip, .0155, .019, cover, bevel=.00035)
    for side in (-1, 1):
        at = center + side * .0215 * axis
        disk = [(at.x + .0018 * math.cos(math.tau * k / 24), at.y + .0018 * math.sin(math.tau * k / 24)) for k in range(24)]
        extrude(f'V552_Selector_Screw_{side}', disk, .0051, .0059, black, bevel=.00012)
        slot = [tuple(at + axis * a + across * b) for a, b in ((-.0012, -.00016), (.0012, -.00016), (.0012, .00016), (-.0012, .00016))]
        extrude(f'V552_Selector_Screw_Slot_{side}', slot, .0059, .00595, recess)

    for name in ('NECK', 'BRIDGE'):
        pickup = bpy.data.objects[f'V206_PICKUP_{name}']
        # Rounded rectangular face panel, retaining the original pickup body.
        outline = []
        radius = .002
        for cx, cy, start in ((.0225, .0435, 0), (-.0225, .0435, 90),
                              (-.0225, -.0435, 180), (.0225, -.0435, 270)):
            outline += [(cx + radius * math.cos(math.radians(start + 90 * k / 8)),
                         cy + radius * math.sin(math.radians(start + 90 * k / 8))) for k in range(9)]
        extrude(f'V552_Pickup_Face_{name}', outline, .00705, .0076, cover, pickup, .00012)
        data = bpy.data.curves.new(f'V552_Pickup_Seam_{name}', 'CURVE')
        data.dimensions = '3D'
        data.resolution_u = 16
        data.bevel_depth = .00019
        data.bevel_resolution = 3
        spline = data.splines.new('BEZIER')
        coords = ((.009, -.044), (.008, -.013), (-.008, .012), (-.009, .044))
        spline.bezier_points.add(len(coords) - 1)
        for point, (x, y) in zip(spline.bezier_points, coords):
            point.co = (x, y, .00756)
            point.handle_left_type = point.handle_right_type = 'AUTO'
        obj = bpy.data.objects.new(data.name, data)
        bpy.context.scene.collection.objects.link(obj)
        obj.parent = pickup
        data.materials.append(recess)
        created.append(obj.name)
        data = bpy.data.curves.new(f'V552_Pickup_Mark_{name}', 'FONT')
        data.body = 'FISHMAN'
        data.size = .0022
        data.space_character = 1.05
        obj = bpy.data.objects.new(data.name, data)
        bpy.context.scene.collection.objects.link(obj)
        obj.parent = pickup
        obj.location = (.019, .029, .00785)
        obj.rotation_euler.z = math.pi / 2
        data.materials.append(lettering)
        created.append(obj.name)

    # Reference markers have pale centers bounded by a narrow dark rim.
    # Keep the existing markers and their fret placement; add only a face cap.
    inlay_center = material('V552_Inlay_Center', (.48, .53, .47), .42, 0)
    inlay_names = []
    for marker in list(guitar.children_recursive):
        if not marker.name.startswith('V206_INLAY_') or marker.type != 'MESH':
            continue
        coords = [v.co for v in marker.data.vertices]
        cx = (min(v.x for v in coords) + max(v.x for v in coords)) / 2
        cy = (min(v.y for v in coords) + max(v.y for v in coords)) / 2
        radius = .72 * min(max(v.x for v in coords) - min(v.x for v in coords),
                           max(v.y for v in coords) - min(v.y for v in coords)) / 2
        z = max(v.z for v in coords) + .000015
        vertices = [(cx + radius * math.cos(2 * math.pi * i / 48),
                     cy + radius * math.sin(2 * math.pi * i / 48), z)
                    for i in range(48)]
        cap = mesh(marker.name.replace('V206_', 'V552_Center_'), vertices,
                   [tuple(range(48))], inlay_center, parent=marker)
        inlay_names.append(cap.name)

    bpy.context.view_layer.update()
    for name, original in saddles.items():
        assert max(abs(a - b) for row_a, row_b in zip(original, bpy.data.objects[name].matrix_world)
                   for a, b in zip(row_a, row_b)) < 1e-9, name
    assert len(rig.animation_data.drivers) == 1957
    return {'created': created, 'hidden_originals': hidden,
            'ring_inlay_centers': inlay_names,
            'saddle_transforms_unchanged': True, 'main_drivers': 1957,
            'reference': 'references/props/strandberg/strandberg_full_product.jpg'}
