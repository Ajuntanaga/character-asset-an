import json
import bpy

material = bpy.data.materials["V216_REFERENCE_FITTED_HEAD_preview_mat"]
nodes = []
for node in material.node_tree.nodes:
    nodes.append({"name": node.name, "type": node.bl_idname, "image": node.image.filepath if hasattr(node, "image") and node.image else None})
links = [{"from": link.from_node.name + "." + link.from_socket.name, "to": link.to_node.name + "." + link.to_socket.name} for link in material.node_tree.links]
print("V276_HEAD_MATERIAL=" + json.dumps({"nodes": nodes, "links": links}, sort_keys=True))
