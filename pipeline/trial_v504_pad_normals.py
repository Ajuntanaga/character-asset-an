import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');out=root/'production_v504_distal_pad'
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];h=bpy.data.objects['V357_ANATOMICAL_HAND.R'];bs=[r.pose.bones[f'FK-Finger_Index{i}.R'] for i in (1,2,3)]
a=json.loads((out/'fit.json').read_text())['vertex']
def surface():
 e=h.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();normal=e.matrix_world.to_3x3().inverted().transposed()
 result=[(np.array(e.matrix_world@m.vertices[i].co),np.array((normal@m.vertices[i].normal).normalized())) for i in (a,5953)]
 e.to_mesh_clear();return result
ip,tp=surface();target=tp[0]+tp[1]*.0011;targetnormal=-tp[1]
x0=np.array([*bs[0].rotation_euler,bs[1].rotation_euler.x,bs[2].rotation_euler.x]);x=x0.copy()
def residual(v):
 bs[0].rotation_euler=v[:3];bs[1].rotation_euler.x=v[3];bs[2].rotation_euler.x=v[4];bpy.context.view_layer.update()
 ip,_=surface();return np.r_[(ip[0]-target)*1000,(ip[1]-targetnormal)*15,(v-x0)*.15]
for it in range(40):
 f=residual(x);J=np.column_stack([(residual(x+np.eye(5)[k]*.001)-f)/.001 for k in range(5)])
 step=np.linalg.solve(J.T@J+np.eye(5)*.4,-J.T@f);step*=min(1,.12/max(abs(step)));improved=False
 for alpha in (1,.5,.25,.125):
  y=np.clip(x+alpha*step,x0-.9,x0+.9);y[3]=np.clip(y[3],math.radians(20),math.radians(110));y[4]=np.clip(y[4],math.radians(30),math.radians(80))
  if np.linalg.norm(residual(y))<np.linalg.norm(f):x=y;improved=True;break
 if not improved:break
f=residual(x);report={'vertex':a,'pad_error_mm':float(np.linalg.norm(f[:3])),'normal_error':float(np.linalg.norm(f[3:6])/15),'angles_degrees':np.degrees(x).tolist(),'drivers':len(r.animation_data.drivers)}
(out/'normal_fit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
