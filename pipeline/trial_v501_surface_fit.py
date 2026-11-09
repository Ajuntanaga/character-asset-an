import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');out=root/'production_v501_pick_refit'
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];h=bpy.data.objects['V357_ANATOMICAL_HAND.R'];bs=[r.pose.bones[f'FK-Finger_Index{i}.R'] for i in (1,2,3)]
for name,mat in json.loads((out/'original_pose.json').read_text()).items():r.pose.bones[name].matrix_basis=Matrix(mat)
bs[0].scale.y=1;bpy.context.view_layer.update()
e=h.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
coords=[e.matrix_world@v.co for v in m.vertices]
groups=[h.vertex_groups[max(v.groups,key=lambda w:w.weight).group].name for v in m.vertices]
ids=[i for i,g in enumerate(groups) if g=='DEF-Finger_Index3.R']
thumb=[i for i,g in enumerate(groups) if g=='DEF-Finger_Thumb3.R']
# Closest actual pad vertices in the previous working pinch.
a,b=min(((a,b) for a in ids for b in thumb),key=lambda ab:(coords[ab[0]]-coords[ab[1]]).length_squared)
target=np.array(coords[a]);e.to_mesh_clear()
d=r.pose.bones['DEF-Finger_Index3.R'];direction=np.array((d.tail-d.head).normalized())
bs[0].scale.y=1.25
x0=np.array([*bs[0].rotation_euler,bs[1].rotation_euler.x,bs[2].rotation_euler.x]);x=x0.copy()
def setx(v):
 bs[0].rotation_euler=v[:3];bs[1].rotation_euler.x=v[3];bs[2].rotation_euler.x=v[4];bpy.context.view_layer.update()
def residual(v):
 setx(v);ev=h.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
 try:pos=np.array(ev.matrix_world@mesh.vertices[a].co)
 finally:ev.to_mesh_clear()
 d=r.pose.bones['DEF-Finger_Index3.R'];vec=np.array((d.tail-d.head).normalized())
 return np.r_[(pos-target)*1000,(vec-direction)*20,(v-x0)*.1]
for it in range(45):
 f=residual(x);J=np.column_stack([(residual(x+np.eye(5)[k]*.001)-f)/.001 for k in range(5)])
 step=np.linalg.solve(J.T@J+np.eye(5)*.5,-J.T@f);step*=min(1,.12/max(abs(step)))
 improved=False
 for alpha in (1,.5,.25,.125,.0625):
  y=np.clip(x+alpha*step,x0-1.2,x0+1.2)
  if np.linalg.norm(residual(y))<np.linalg.norm(f):x=y;improved=True;break
 if not improved:break
f=residual(x);report={'pad_vertex':a,'thumb_vertex':b,'pad_error_mm':float(np.linalg.norm(f[:3])),'orientation_residual':f[3:6].tolist(),'delta_degrees':np.degrees(x-x0).tolist()};(out/'surface_fit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
f=root/'pipeline/check_v458_grip_fit.py';exec(f.read_text().replace('production_v458_grip_fit/check.json','production_v501_pick_refit/surface_check.json'),{})
