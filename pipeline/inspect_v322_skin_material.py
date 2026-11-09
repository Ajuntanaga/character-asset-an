"""Print editable inputs in the MB male skin material stack."""

import json

import bpy


body = bpy.data.objects["V322_MB_MALE_BODY"]
materials = []
for slot in body.material_slots:
    material = slot.material
    if material is None or material.node_tree is None:
        continue
    nodes = []
    for node in material.node_tree.nodes:
        entry = {"name": node.name, "label": node.label, "type": node.type}
        if node.type == "GROUP":
            entry["inputs"] = {
                socket.name: list(socket.default_value) if hasattr(socket.default_value, "__len__") and not isinstance(socket.default_value, str) else socket.default_value
                for socket in node.inputs
                if hasattr(socket, "default_value")
            }
        nodes.append(entry)
    materials.append({"name": material.name, "nodes": nodes})
print("V322_SKIN_MATERIALS=" + json.dumps(materials, sort_keys=True))
