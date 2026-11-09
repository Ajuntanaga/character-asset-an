import json
import bpy

body = bpy.data.objects["V211_BODY_NEUTRAL"]
tokens = ("spine", "chest", "shoulder", "upper_arm", "forearm", "hand")
print("V270_DEFORM_GROUPS=" + json.dumps([g.name for g in body.vertex_groups if any(t in g.name.lower() for t in tokens)]))
