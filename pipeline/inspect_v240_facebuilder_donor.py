"""Inspect the V240 FaceBuilder identity donor for animation integration."""

from pathlib import Path
import json
import bpy
from mathutils import Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v240_identity_clean_rig" / "Character_An_identity_clean_rig_v240.blend"


def bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "min": [min(point[i] for point in points) for i in range(3)],
        "max": [max(point[i] for point in points) for i in range(3)],
        "center": [sum(point[i] for point in points) / len(points) for i in range(3)],
    }


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    records = {}
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        if "HEAD" not in obj.name.upper() and "FACE" not in obj.name.upper() and "EYE" not in obj.name.upper():
            continue
        records[obj.name] = {
            "vertices": len(obj.data.vertices),
            "faces": len(obj.data.polygons),
            "uv_layers": [layer.name for layer in obj.data.uv_layers],
            "materials": [material.name if material else None for material in obj.data.materials],
            "shape_keys": [key.name for key in obj.data.shape_keys.key_blocks] if obj.data.shape_keys else [],
            "modifiers": [{"name": modifier.name, "type": modifier.type, "object": getattr(getattr(modifier, "object", None), "name", None)} for modifier in obj.modifiers],
            "parent": obj.parent.name if obj.parent else None,
            "parent_type": obj.parent_type,
            "bounds": bounds(obj),
        }
    curves = {
        obj.name: {"splines": len(obj.data.splines), "bevel": obj.data.bevel_depth, "parent": obj.parent.name if obj.parent else None}
        for obj in bpy.data.objects if obj.type == "CURVE" and ("HAIR" in obj.name.upper() or "GROOM" in obj.name.upper() or "BROW" in obj.name.upper() or "BEARD" in obj.name.upper())
    }
    material_records = {}
    for material in bpy.data.materials:
        if not material.use_nodes:
            continue
        images = []
        for node in material.node_tree.nodes:
            if node.bl_idname == "ShaderNodeTexImage" and node.image:
                images.append({"node": node.name, "image": node.image.name, "filepath": bpy.path.abspath(node.image.filepath), "packed": bool(node.image.packed_file), "size": list(node.image.size)})
        if images:
            material_records[material.name] = images
    print("V240_FACEBUILDER_DONOR=" + json.dumps({"meshes": records, "curves": curves, "materials": material_records}, sort_keys=True))


if __name__ == "__main__":
    main()
