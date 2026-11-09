"""Raycast landmarks selected on the actual orthographic head render."""
import bpy, json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'production_v362_face_anatomy'
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
mesh = body.data
bvh = BVHTree.FromPolygons([body.matrix_world @ v.co for v in mesh.vertices], [list(p.vertices) for p in mesh.polygons])
pixels = {
 'L': {'iris': (714,701), 'upper': [(666,710),(681,698),(697,688),(715,686),(733,689),(751,697),(768,707)],
       'lower': [(666,710),(682,715),(699,719),(717,722),(735,721),(752,716),(768,707)]},
 'R': {'iris': (493,701), 'upper': [(444,705),(460,695),(477,687),(493,686),(511,692),(529,702),(543,713)],
       'lower': [(444,705),(459,715),(476,720),(494,722),(512,720),(528,718),(543,713)]},
 'mouth': {'upper': [(494,932),(520,923),(549,918),(575,919),(597,917),(619,919),(645,920),(671,923),(703,933)],
           'lower': [(494,932),(520,932),(549,930),(575,929),(597,929),(619,929),(645,930),(671,932),(703,933)]},
}

def sample(pixel):
    px, py = pixel
    x = (px/1200-.5)*.4
    z = 1.68+(.5-py/1200)*.4
    hit, normal, face_index, distance = bvh.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
    if hit is None: raise RuntimeError('Missing face landmark '+str(pixel))
    return {'pixel': list(pixel), 'world':list(hit),'normal':list(normal),'face_index':face_index,'vertices':list(mesh.polygons[face_index].vertices)}

landmarks = {side:{k:sample(v) if k=='iris' else [sample(p) for p in v] for k,v in parts.items()} for side,parts in pixels.items()}
head=rig.pose.bones['DEF-Head']
transform=rig.matrix_world @ head.matrix @ head.bone.matrix_local.inverted()
data={'landmarks':landmarks,'head_rest_to_pose':list(map(list,transform)),
      'body_modifiers':[(m.name,m.type) for m in body.modifiers],
      'body_shape_keys':[k.name for k in body.data.shape_keys.key_blocks] if body.data.shape_keys else [],
      'materials':{m.name:[(n.name,n.bl_idname) for n in m.node_tree.nodes] for m in body.data.materials}}
for asset in ['third_party/blenderkit_free/procedural_eye.blend','third_party/blender_human_base_meshes/v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend']:
    path=ROOT/asset
    if path.exists():
        with bpy.data.libraries.load(str(path),link=False) as (source,dest):
            data[asset]={'objects':[n for n in source.objects if any(t in n.lower() for t in ('eye','jaw','tooth','teeth','tongue','mouth'))],'materials':list(source.materials)}
(OUT/'actual_face_landmarks.json').write_text(json.dumps(data,indent=2))
print(json.dumps(data))
