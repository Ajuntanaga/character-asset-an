import bpy,json,math
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];b=r.pose.bones['FK-Finger_Middle1.R'];d=r.pose.bones['DEF-Finger_Middle3.R'];o=bpy.data.objects['V357_ANATOMICAL_HAND.R'];old=b.rotation_euler.copy();out=[]
assert not bpy.app.is_job_running('RENDER')
try:
 for angle in (35,10):
  b.rotation_euler.x=math.radians(angle);r.update_tag();bpy.context.view_layer.update()
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
  out.append({'angle':angle,'mode':b.rotation_mode,'control_head':list(b.head),'def_tail':list(d.tail),'sample':list(m.vertices[1000].co),'finger_samples':[list(v.co) for v in m.vertices if any(o.vertex_groups[g.group].name=='DEF-Finger_Middle3.R' and g.weight>.9 for g in v.groups)][:3],'matrix':list(b.matrix[0])});e.to_mesh_clear()
finally:b.rotation_euler=old;r.update_tag();bpy.context.view_layer.update()
print(json.dumps(out))
