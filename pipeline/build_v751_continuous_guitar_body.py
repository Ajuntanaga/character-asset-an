"""Reversible single-shell trial removing the inset cap's stacked rim."""
import bpy


def build(core, top, maple, charcoal):
    name = 'V751_CONTINUOUS_GUITAR_BODY'
    assert name not in bpy.data.objects
    assert all(abs(core.matrix_world[r][c] - top.matrix_world[r][c]) < 1e-6
               for r in range(4) for c in range(4))
    # Recover the existing planar UV transform from the actual input mesh.
    source_uv = top.data.uv_layers['WoodProjection']
    transforms = []
    for axis in (0, 1):
        samples = [(top.data.vertices[loop.vertex_index].co[axis],
                    source_uv.data[loop.index].uv[axis]) for loop in top.data.loops]
        low, high = min(samples), max(samples)
        assert high[0] - low[0] > .01
        scale = (high[1] - low[1]) / (high[0] - low[0])
        offset = low[1] - scale * low[0]
        assert max(abs(u - (scale * x + offset)) for x, u in samples) < 1e-5
        transforms.append((scale, offset))
    shell = core.copy()
    shell.data = core.data.copy()
    shell.name = name
    for collection in core.users_collection:
        collection.objects.link(shell)
    upper = max(v.co.z for v in shell.data.vertices)
    target = max(v.co.z for v in top.data.vertices)
    for vertex in shell.data.vertices:
        if abs(vertex.co.z - upper) < 1e-6:
            vertex.co.z = target
    shell.data.materials.clear()
    shell.data.materials.append(maple)
    shell.data.materials.append(charcoal)
    for polygon in shell.data.polygons:
        is_top = all(abs(shell.data.vertices[i].co.z - target) < 1e-6
                     for i in polygon.vertices)
        polygon.material_index = 0 if is_top else 1
    uv = shell.data.uv_layers.get('WoodProjection')
    if uv is None:
        uv = shell.data.uv_layers.new(name='WoodProjection')
    shell.data.uv_layers.active = uv
    uv.active_render = True
    for loop in shell.data.loops:
        co = shell.data.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = tuple(co[a] * transforms[a][0] + transforms[a][1]
                                       for a in (0, 1))
    bevels = [m for m in shell.modifiers if m.type == 'BEVEL']
    assert len(bevels) == 1
    bevels[0].width = .004
    bevels[0].segments = 6
    bevels[0].material = 0
    shell.data.update()
    shell.hide_render = False
    shell.hide_viewport = False
    shell.hide_set(False)
    originals = {}
    for obj in (core, top):
        originals[obj.name] = {'hide_render': obj.hide_render,
                               'hide_viewport': obj.hide_viewport,
                               'hide_set': obj.hide_get()}
        obj.hide_render = True
        obj.hide_set(True)
    return shell, {'object': shell.name, 'original_visibility': originals,
                   'top_z': target, 'bevel_m': .004,
                   'source_outline': core.name, 'uv_transform': transforms,
                   'status': 'TRIAL_REQUIRES_VISUAL_REVIEW'}
