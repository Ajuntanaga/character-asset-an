"""Separate coherent curl sheets into varied tapered fiber clusters; roots fixed."""
import bpy,json,numpy as np
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v485_hair_isolation'
assert not bpy.app.is_job_running('RENDER')
old=bpy.data.objects['V449_CURL_GROOM']; assert bpy.data.objects.get('V485_CURL_GROOM') is None
obj=old.copy();obj.data=old.data.copy();obj.name='V485_CURL_GROOM';bpy.context.scene.collection.objects.link(obj)
obj.hide_render=False;obj.hide_set(False)
a=np.empty(len(obj.data.points)*3,np.float32);obj.data.position_data.foreach_get('vector',a)
a=a.reshape(-1,92,25,3);original=a.copy();rng=np.random.default_rng(485)
t=np.linspace(0,1,25,dtype=np.float32)
for block in a:
 fibers=block[:80].copy();center=fibers.mean(axis=0)
 # Eight smaller clusters have distinct length, reducing the common cut tip.
 lengths=np.repeat(rng.uniform(.76,1.,8),10)
 lengths=np.clip(lengths+rng.uniform(-.035,.035,80),.70,1.)
 for k in range(80):
  u=t*lengths[k]*24; lo=np.floor(u).astype(int);hi=np.minimum(lo+1,24);w=(u-lo)[:,None]
  curve=fibers[k,lo]*(1-w)+fibers[k,hi]*w
  c=center[lo]*(1-w)+center[hi]*w
  taper=(1-.72*t**1.4)[:,None]
  curve=c+(curve-c)*taper
  # Smooth independent deviations break parallel specular bands, not root attachment.
  axis=rng.normal(size=3);axis/=np.linalg.norm(axis)
  amp=rng.uniform(.00015,.00065)
  curve+=axis[None,:]*(amp*np.sin(np.pi*t)*np.sin(t*np.pi*rng.uniform(1,2.5)))[:,None]
  curve[0]=fibers[k,0];block[k]=curve
assert np.isfinite(a).all()
root_error=float(np.abs(a[:,:,0]-original[:,:,0]).max())
assert root_error==0
obj.data.position_data.foreach_set('vector',a.ravel());obj.data.update_tag();bpy.context.view_layer.update()
report={'roots_unchanged':True,'max_displacement_mm':float(np.linalg.norm(a-original,axis=-1).max()*1000),'strands':len(a)*92,'drivers':len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers)}
(out/'trial.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v485_hair_isolation/trial.png','resolution':[700,800],'samples':32,'scale':.46,'camera':[.1,-2,1.67],'target':[0,0,1.65]}))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
