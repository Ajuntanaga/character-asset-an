import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');out=root/'production_v504_distal_pad';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];h=bpy.data.objects['V357_ANATOMICAL_HAND.R'];p=bpy.data.objects['V361_NYLON_PICK']
assert len(r.animation_data.drivers)==1957
bs=[r.pose.bones[f'FK-Finger_Index{i}.R'] for i in (1,2,3)]
backup={'file':bpy.data.filepath,'index':{b.name:[list(row) for row in b.matrix_basis] for b in bs},'pick':[list(row) for row in p.matrix_world]}
assert not (out/'original.json').exists(),'Trial already run'
(out/'original.json').write_text(json.dumps(backup,indent=2))
def coords():
 e=h.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
 c=[e.matrix_world@v.co for v in m.vertices];groups=[h.vertex_groups[max(v.groups,key=lambda w:w.weight).group].name for v in m.vertices];e.to_mesh_clear();return c,groups
c,groups=coords();thumb=c[5953].copy();old=c[7664].copy()
bs[2].rotation_euler.x=math.radians(48);bpy.context.view_layer.update()
c,groups=coords();d=r.pose.bones['DEF-Finger_Index3.R'];head=r.matrix_world@d.head;axis=r.matrix_world.to_3x3()@(d.tail-d.head)
candidates=[i for i,g in enumerate(groups) if g=='DEF-Finger_Index3.R' and .6<=(c[i]-head).dot(axis)/axis.length_squared<=.85]
a=min(candidates,key=lambda i:(c[i]-thumb).length_squared)
# Opposing pad surface separated by one pick thickness plus a small allowance.
target=thumb+(old-thumb).normalized()*.0011
x0=np.array([*bs[0].rotation_euler,bs[1].rotation_euler.x]);x=x0.copy()
def setx(v):
 bs[0].rotation_euler=v[:3];bs[1].rotation_euler.x=v[3];bpy.context.view_layer.update()
def residual(v):
 setx(v);c,_=coords();return np.r_[(np.array(c[a])-np.array(target))*1000,(v-x0)*.5]
for it in range(35):
 f=residual(x);J=np.column_stack([(residual(x+np.eye(4)[k]*.001)-f)/.001 for k in range(4)])
 step=np.linalg.solve(J.T@J+np.eye(4)*.3,-J.T@f);step*=min(1,.15/max(abs(step)))
 improved=False
 for alpha in (1,.5,.25,.125):
  y=np.clip(x+alpha*step,x0-.9,x0+.9);y[3]=np.clip(y[3],math.radians(20),math.radians(110))
  if np.linalg.norm(residual(y))<np.linalg.norm(f):x=y;improved=True;break
 if not improved:break
f=residual(x);c,_=coords()
report={'vertex':a,'distal_fraction':float((c[a]-(r.matrix_world@d.head)).dot(r.matrix_world.to_3x3()@(d.tail-d.head))/(r.matrix_world.to_3x3()@(d.tail-d.head)).length_squared),'pad_error_mm':float(np.linalg.norm(f[:3])),'DIP_degrees':48,'delta_degrees':np.degrees(x-x0).tolist(),'drivers':len(r.animation_data.drivers)}
(out/'fit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
