"""Report spatial and shader facts needed to clean the V323 identity transfer."""

from pathlib import Path
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v323_identity_on_male" / "Character_An_identity_on_male_v323.blend"
OUTPUT = ROOT / "production_v323_identity_on_male" / "audit" / "v323_identity_probe.json"


def bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "min": [min(point[axis] for point in points) for axis in range(3)],
        "max": [max(point[axis] for point in points) for axis in range(3)],
    }


def scalar(value):
    try:
        if len(value) <= 4:
            return [float(item) for item in value]
    except (TypeError, ValueError):
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def material_report(obj):
    result = []
    for slot in obj.material_slots:
        material = slot.material
        item = {"slot": slot.name, "material": material.name if material else None}
        if material and material.node_tree:
            nodes = []
            for node in material.node_tree.nodes:
                if node.type in {"BSDF_PRINCIPLED", "BSDF_HAIR_PRINCIPLED", "TEX_IMAGE", "RGB", "ATTRIBUTE"}:
                    node_item = {"name": node.name, "type": node.type}
                    if node.type == "TEX_IMAGE":
                        node_item["image"] = node.image.filepath if node.image else None
                    inputs = {}
                    for socket in node.inputs:
                        if socket.is_linked:
                            inputs[socket.name] = {"linked": True}
                        elif hasattr(socket, "default_value"):
                            inputs[socket.name] = scalar(socket.default_value)
                    node_item["inputs"] = inputs
                    nodes.append(node_item)
            item["nodes"] = nodes
        result.append(item)
    return result


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    names = [
        "V322_MB_MALE_BODY",
        "V216_REFERENCE_FITTED_HEAD",
        "V216_EYE_L",
        "V216_EYE_R",
        "V217_TIGHT_CURL_GROOM",
    ]
    report = {"source": str(SOURCE), "objects": {}}
    for name in names:
        obj = bpy.data.objects[name]
        report["objects"][name] = {
            "type": obj.type,
            "location": list(obj.matrix_world.translation),
            "bounds": bounds(obj),
            "dimensions": list(obj.dimensions),
            "materials": material_report(obj),
            "modifiers": [
                {"name": modifier.name, "type": modifier.type, "show_render": modifier.show_render}
                for modifier in obj.modifiers
            ],
        }
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("V323_IDENTITY_PROBE_OK=" + str(OUTPUT))


if __name__ == "__main__":
    main()
