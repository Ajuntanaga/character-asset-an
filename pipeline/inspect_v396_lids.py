import bpy,json
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert not bpy.app.is_job_running('RENDER')
r={"file":bpy.data.filepath,"drivers":len(rig.animation_data.drivers),"materials":{}}
for name in ('V365_LID_SKIN','V367_LASH_LINE'):
 m=bpy.data.materials[name];r['materials'][name]=[{'name':n.name,'type':n.type,'inputs':{s.name:list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value for s in n.inputs if hasattr(s,'default_value') and not s.is_linked and s.type in ('VALUE','RGBA')}} for n in m.node_tree.nodes]
print(json.dumps(r))
