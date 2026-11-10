"""Create a short native thumb release study, preserving the fitted endpoints."""
import math


def build():
    import bpy
    main = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
    assert main.animation_data.action is None
    assert not main.animation_data.nla_tracks
    assert len(main.animation_data.drivers) == 1957
    control = main.pose.bones['IK-Hand.R']
    props = ['V593_Thumb_CMC', 'V593_Thumb_MCP', 'V593_Thumb_IP', 'V593_Thumb_Opposition']
    assert all(name in control and control[name] == 0.0 for name in props)
    action = bpy.data.actions.new('V594_Thumb_Release_Study')
    action.use_fake_user = True
    main.animation_data.action = action
    for frame, angles in [(1, (0, 0, 0, 0)), (9, (6, 8, 6, 0)), (17, (6, 8, 6, 0)), (25, (0, 0, 0, 0))]:
        for name, angle in zip(props, angles):
            control[name] = math.radians(angle)
            control.keyframe_insert(data_path=f'["{name}"]', frame=frame, group='Picking thumb')
    # Explicit flat handles prevent interpolation overshoot beyond the study range.
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for point in curve.keyframe_points:
                        point.interpolation = 'BEZIER'
                        point.handle_left_type = 'AUTO_CLAMPED'
                        point.handle_right_type = 'AUTO_CLAMPED'
    bpy.context.scene.frame_set(1)
    return action
