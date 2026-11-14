"""Align the original sleeve wrist to the fitted donor; isolated trial only."""
import math
import bpy
from build_v545_fretting_hand import frame


def build():
    main = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
    donor = bpy.data.objects['V545_NATIVE_RIG.L']
    hand = bpy.data.objects['V545_NATIVE_HAND.L']
    control = main.pose.bones['IK-Hand.L']
    bone = main.pose.bones['DEF-Hand.L']
    donor_world = donor.matrix_world.copy()
    target_position = donor_world @ donor.pose.bones['DEF-Hand.R'].head
    donor_deform = (donor_world @ donor.pose.bones['DEF-Hand.R'].matrix
                    @ donor.data.bones['DEF-Hand.R'].matrix_local.inverted())
    target_frame = (donor_deform.to_3x3() @ frame(donor.data.bones, 'R')).to_quaternion()

    def surface():
        obj = hand.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = obj.to_mesh()
        try:
            return [obj.matrix_world @ v.co for v in mesh.vertices]
        finally:
            obj.to_mesh_clear()

    original = surface()
    steps = []
    for _ in range(16):
        deform = main.matrix_world @ bone.matrix @ bone.bone.matrix_local.inverted()
        actual_frame = (deform.to_3x3() @ frame(main.data.bones, 'L')).to_quaternion()
        correction = target_frame @ actual_frame.inverted()
        angle = abs(correction.angle)
        angle = min(angle, 2 * math.pi - angle)
        error = target_position - main.matrix_world @ bone.head
        steps.append({'angle_deg': math.degrees(angle), 'position_error_m': error.length})
        if angle < math.radians(.25) and error.length < .0001:
            break
        world = main.matrix_world @ control.matrix
        location = world.translation.copy()
        world = correction.to_matrix().to_4x4() @ world
        world.translation = location + error
        control.matrix = main.matrix_world.inverted() @ world
        bpy.context.view_layer.update()
    else:
        raise RuntimeError(f'Wrist alignment did not converge: {steps}')

    # Preserve the fitted donor placement despite moving its bone parent.
    parent = (donor.matrix_world @ donor.matrix_basis.inverted()
              @ donor.matrix_parent_inverse.inverted())
    donor.matrix_parent_inverse = (parent.inverted() @ donor_world
                                   @ donor.matrix_basis.inverted())
    bpy.context.view_layer.update()
    final = surface()
    assert len(original) == len(final)
    displacement = max((a - b).length for a, b in zip(original, final))
    assert displacement < .00001, f'Fitted hand moved {displacement}m'
    return {'status': 'UNPROMOTED_WRIST_ALIGNMENT_TRIAL', 'iterations': steps,
            'max_donor_surface_displacement_m': displacement,
            'visual_and_deformation_acceptance': False}
