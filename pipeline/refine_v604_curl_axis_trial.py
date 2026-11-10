"""Reversible anchored primary-fiber yaw trial; undercoat and radii unchanged."""
def build(primary_strands=117818, steps=41):
    import bpy
    import numpy as np
    ob=bpy.data.objects['V546_CURL_GROOM']
    original=ob.data
    assert len(original.points)==186522*steps
    data=original.copy();data.name='V604_CURL_AXIS_TRIAL'
    coordinates=np.empty((len(data.points),3),dtype=np.float32)
    data.position_data.foreach_get('vector',coordinates.ravel())
    strands=coordinates.reshape(-1,steps,3)
    points=strands[:primary_strands]
    roots=points[:,0].copy()
    normal=(roots-np.array([0.,.012,1.682],dtype=np.float32))/np.array([.095**2,.115**2,.118**2],dtype=np.float32)
    normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-8)
    t=np.linspace(0,1,steps,dtype=np.float32)
    angles=np.radians(np.array([-12.,-6.,0.,6.,12.],dtype=np.float32))[np.arange(primary_strands)%5,None]*(1-np.exp(-t[None,:]/.18))**2
    offset=points-roots[:,None,:]
    c=np.cos(angles)[:,:,None];s=np.sin(angles)[:,:,None];n=normal[:,None,:]
    rotated=offset*c+np.cross(n,offset)*s+n*np.sum(n*offset,axis=2)[:,:,None]*(1-c)
    changed=roots[:,None,:]+rotated
    report={'primary_strands':primary_strands,'steps':steps,'max_displacement_mm':float(np.linalg.norm(changed-points,axis=2).max()*1000),'max_root_change':float(np.abs(changed[:,0]-roots).max()),'yaw_degrees':[-12,12],'undercoat_changed':False}
    assert np.isfinite(changed).all() and report['max_root_change']==0
    points[:]=changed
    data.position_data.foreach_set('vector',coordinates.ravel());data.update_tag()
    ob.data=data;bpy.context.view_layer.update()
    return original,report
