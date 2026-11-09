from __future__ import annotations

from pathlib import Path
from typing import Mapping


HEAD_CAMERAS = {
    "front": "V95_CAM_HEAD_FRONT",
    "left_3q": "V95_CAM_HEAD_LEFT_THREEQUARTER",
    "right_3q": "V95_CAM_HEAD_RIGHT_THREEQUARTER",
    "right_profile": "V95_CAM_HEAD_RIGHT_PROFILE",
    "back": "V95_CAM_HEAD_BACK",
}

BODY_CAMERAS = {
    "front": "V151_FRONT_CAMERA",
    "front_right_3q": "V151_FRONT_RIGHT_3Q_CAMERA",
    "right_profile": "V151_RIGHT_PROFILE_CAMERA",
    "rear_right_3q": "V151_REAR_RIGHT_3Q_CAMERA",
    "back": "V151_BACK_CAMERA",
    "rear_left_3q": "V151_REAR_LEFT_3Q_CAMERA",
    "left_profile": "V151_LEFT_PROFILE_CAMERA",
    "front_left_3q": "V151_FRONT_LEFT_3Q_CAMERA",
}


def render_group(
    source: Path,
    output_dir: Path,
    cameras: Mapping[str, str],
    resolution: tuple[int, int] = (720, 720),
) -> dict[str, str]:
    import bpy

    if Path(bpy.data.filepath).resolve() != source.resolve():
        raise RuntimeError(f"Loaded scene mismatch: {bpy.data.filepath} != {source}")
    output_dir.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    outputs: dict[str, str] = {}
    for label, camera_name in cameras.items():
        camera = bpy.data.objects.get(camera_name)
        if camera is None or camera.type != "CAMERA":
            raise RuntimeError(f"Missing camera: {camera_name}")
        scene.camera = camera
        output = output_dir / f"{label}.png"
        scene.render.filepath = str(output)
        bpy.ops.render.render(write_still=True)
        outputs[label] = str(output)
    return outputs
