"""GPU Cycles render worker for packed Character Asset_An checkpoints."""
from pathlib import Path

import modal

APP_NAME = "character-asset-an-render"
VOLUME_NAME = "character-asset-an"

app = modal.App(APP_NAME)
image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install(
        "libx11-6",
        "libxrender1",
        "libxfixes3",
        "libxi6",
        "libxxf86vm1",
        "libxkbcommon0",
        "libgl1",
        "libsm6",
        "libice6",
    )
    .pip_install("bpy==5.2.2")
)
volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)


@app.function(
    image=image,
    gpu="L4",
    timeout=3600,
    volumes={"/assets": volume},
)
def render_view(remote_blend: str, view_name: str, resolution_x: int, resolution_y: int, samples: int = 128):
    import bpy

    source = "/assets" + remote_blend
    bpy.ops.wm.open_mainfile(filepath=source)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT" if view_name == "smoke" else "CYCLES"
    scene.render.resolution_x = resolution_x
    scene.render.resolution_y = resolution_y
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    if scene.render.engine == "CYCLES":
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True
        scene.cycles.device = "GPU"
        prefs = bpy.context.preferences.addons.get("cycles")
        if prefs:
            cprefs = prefs.preferences
            for backend in ("OPTIX", "CUDA"):
                try:
                    cprefs.compute_device_type = backend
                    cprefs.get_devices()
                    for device in cprefs.devices:
                        device.use = device.type != "CPU"
                    break
                except Exception:
                    continue

    camera = scene.camera or bpy.data.objects.get("V323_CAMERA")
    if camera is None:
        raise RuntimeError("V323_CAMERA is missing")
    scene.camera = camera
    views = {
        "full_front": ((.18, -3.75, 1.10), (.10, -.10, 1.08), 67),
        "guitar_beauty": ((1.25, -2.25, 1.42), (.33, -.30, 1.35), 82),
        "guitar_front": ((.68, -2.25, 1.46), (.34, -.30, 1.34), 96),
        "three_quarter": ((1.45, -3.25, 1.18), (.12, -.12, 1.10), 64),
        "smoke": ((1.25, -2.25, 1.42), (.33, -.30, 1.35), 82),
        "wardrobe_front": ((0., -3.30, 1.25), (0., 0., 1.25), 70),
        "wardrobe_back": ((0., 3.30, 1.25), (0., 0., 1.25), 70),
        "wardrobe_side": ((2.65, -1.8, 1.25), (0., 0., 1.25), 70),
        "wardrobe_full": ((.12, -4.10, .98), (0., 0., .92), 60),
        "wardrobe_full_back": ((.12, 4.10, .98), (0., 0., .92), 60),
        "asset_front": ((0., -4.10, 1.0), (0., 0., .94), 60),
        "asset_back": ((0., 4.10, 1.0), (0., 0., .94), 60),
        "asset_three_quarter": ((2.6, -4.10, 1.10), (0., 0., .94), 68),
        "asset_face": ((0., -1.22, 1.66), (0., 0., 1.65), 85),
        "lineup_front": ((0., -7., 1.05), (0., 0., .90), 60),
        "lineup_back": ((0., 7., 1.05), (0., 0., .90), 60),
    }
    if view_name not in views:
        raise ValueError(f"unknown view {view_name!r}")
    location, target, lens = views[view_name]
    if view_name.startswith("wardrobe_"):
        guitar = bpy.data.objects.get("V206_GUITAR_ROOT")
        if guitar:
            for obj in [guitar, *guitar.children_recursive]:
                obj.hide_render = True
        for obj in scene.objects:
            if obj.name.startswith(("V206_", "V340_", "V341_", "V342_", "V343_")):
                obj.hide_render = True
    camera.location = location
    camera.data.lens = lens
    from mathutils import Vector
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
    output = f"/tmp/{view_name}.png"
    scene.render.filepath = output
    bpy.ops.render.render(write_still=True)
    return Path(output).read_bytes()


@app.local_entrypoint()
def main(
    blend: str = "production_v342_graphite_contour_guitar/modal/Character_An_v342_packed.blend",
    output_dir: str = "production_v342_graphite_contour_guitar/modal/renders",
    samples: int = 128,
    views: str = "full_front,guitar_beauty,guitar_front,three_quarter",
    prefix: str = "v342",
):
    source = Path(blend).resolve()
    destination = Path(output_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    if not source.is_file():
        raise FileNotFoundError(source)
    import hashlib
    remote_blend = "/input/" + hashlib.sha256(source.read_bytes()).hexdigest()[:16] + ".blend"
    with volume.batch_upload(force=True) as upload:
        upload.put_file(source, remote_blend)

    specs = {
        "full_front": (1000, 1200),
        "guitar_beauty": (1100, 900),
        "guitar_front": (900, 1000),
        "three_quarter": (1000, 1200),
        "wardrobe_front": (1200, 1100),
        "wardrobe_back": (1200, 1100),
        "wardrobe_side": (1000, 1200),
        "wardrobe_full": (1000, 1400),
        "wardrobe_full_back": (1000, 1400),
        "asset_front": (1000, 1400),
        "asset_back": (1000, 1400),
        "asset_three_quarter": (1000, 1400),
        "asset_face": (1200, 1200),
        "lineup_front": (1800, 1200),
        "lineup_back": (1800, 1200),
    }
    selected = [name.strip() for name in views.split(",")]
    calls = [(remote_blend, name, *specs[name], samples) for name in selected]
    for args, png in zip(calls, render_view.starmap(calls)):
        name = args[1]
        path = destination / f"{prefix}_modal_cycles_{name}.png"
        path.write_bytes(png)
        print(path)
