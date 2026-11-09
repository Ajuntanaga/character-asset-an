import bpy
import json
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
mat = body.data.materials[0]
nodes = []
for n in mat.node_tree.nodes:
    nodes.append({'name':n.name,'type':n.type,
      'inputs':{s.name:{'value':list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value,
                         'links':[(l.from_node.name,l.from_socket.name) for l in s.links]}
                for s in n.inputs if hasattr(s,'default_value')}})
print(json.dumps({'material':mat.name,'nodes':nodes,
 'eye_objects':[(o.name,len(o.data.vertices),bool(o.data.shape_keys)) for o in bpy.data.objects if o.name.startswith(('V374_EYE.','V374_CORNEA.'))],
 'rig_drivers':len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers)}))
