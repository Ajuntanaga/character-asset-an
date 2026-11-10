"""Reversible native thumb controls; zero preserves the fitted picking pose."""
import math


def build():
    import bpy
    from mathutils import Quaternion
    main = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
    donor = bpy.data.objects['V528_NATIVE_RIG.R']
    control = main.pose.bones['IK-Hand.R']
    names = ['V593_Thumb_CMC', 'V593_Thumb_MCP', 'V593_Thumb_IP']
    opposition_name = 'V593_Thumb_Opposition'
    assert len(main.animation_data.drivers) == 1957
    assert not any(n in control for n in names + [opposition_name])
    bones = [donor.pose.bones[f'DEF-Finger_Thumb{i}.R'] for i in (1, 2, 3)]
    assert all(b.rotation_mode == 'QUATERNION' and not b.constraints for b in bones)
    paths = {b.path_from_id('rotation_quaternion') for b in bones}
    assert not any(f.data_path in paths for f in donor.animation_data.drivers)
    rest = donor.data.bones
    along = (rest['DEF-Finger_Middle1.R'].head_local - rest['DEF-Hand.R'].head_local).normalized()
    across = (rest['DEF-Finger_Index1.R'].head_local - rest['DEF-Finger_Pinky1.R'].head_local).normalized()
    normal = across.cross(along).normalized()
    for name in names + [opposition_name]:
        control[name] = 0.0
        control.id_properties_ui(name).update(min=-math.pi/4, max=math.pi/4, soft_min=-math.pi/9, soft_max=math.pi/9, subtype='ANGLE', description='Angle relative to fitted grip; zero restores grip')
    report = {'main_drivers': 1957, 'properties': names + [opposition_name], 'base_quaternions': {}}
    for index, bone in enumerate(bones):
        base = bone.rotation_quaternion.copy()
        report['base_quaternions'][bone.name] = list(base)
        axis = bone.bone.matrix_local.to_3x3().inverted() @ normal.cross(bone.bone.tail_local - bone.bone.head_local).normalized()
        opp = bone.bone.matrix_local.to_3x3().inverted() @ normal
        qa = Quaternion((0., *axis.normalized()))
        qb = Quaternion((0., *opp.normalized()))
        coefficients = [base, qa @ base, qb @ base, qb @ qa @ base]
        a = '(a/2)'
        b = '(b/2)'
        terms = [f'cos({a})*cos({b})', f'sin({a})*cos({b})', f'cos({a})*sin({b})', f'sin({a})*sin({b})'] if index == 0 else [f'cos({a})', f'sin({a})']
        for component in range(4):
            driver = bone.driver_add('rotation_quaternion', component).driver
            driver.type = 'SCRIPTED'
            for varname, prop in [('a', names[index])] + ([('b', opposition_name)] if index == 0 else []):
                variable = driver.variables.new()
                variable.name = varname
                variable.type = 'SINGLE_PROP'
                variable.targets[0].id = main
                variable.targets[0].data_path = control.path_from_id() + f'["{prop}"]'
            driver.expression = '+'.join(f'({coefficients[k][component]:.10g})*{term}' for k, term in enumerate(terms))
    main.update_tag()
    donor.update_tag()
    bpy.context.view_layer.update()
    report['zero_pose_max_error'] = max(abs(b.rotation_quaternion[i]-report['base_quaternions'][b.name][i]) for b in bones for i in range(4))
    assert report['zero_pose_max_error'] < 1e-6
    assert len(main.animation_data.drivers) == 1957
    return report
