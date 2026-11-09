"""Restore the graphite material lost when V340 replaced the guitar body mesh."""
from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v341_clean_contour_guitar" / "Character_An_clean_contour_guitar_v341.blend"
STAGE = ROOT / "production_v342_graphite_contour_guitar"
OUTPUT = STAGE / "Character_An_graphite_contour_guitar_v342.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit" / "v342_graphite_contour_guitar.json"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, path, location, target, lens, resolution):
    camera.location = location
    camera.data.lens = lens
    aim(camera, target)
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for path in (STAGE, RENDERS, AUDIT.parent):
        path.mkdir(parents=True, exist_ok=True)

    body = bpy.data.objects["V206_BODY_CORE"]
    graphite = bpy.data.materials.get("V338_GRAPHITE_SATIN")
    if graphite is None:
        graphite = bpy.data.materials.new("V338_GRAPHITE_SATIN")
        graphite.use_nodes = True
        nodes = graphite.node_tree.nodes
        links = graphite.node_tree.links
        principled = nodes.get("Principled BSDF")
        principled.inputs["Base Color"].default_value = (.035, .045, .055, 1)
        principled.inputs["Roughness"].default_value = .38
        principled.inputs["Metallic"].default_value = .18
        if "Specular IOR Level" in principled.inputs:
            principled.inputs["Specular IOR Level"].default_value = .32
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 48
        noise.inputs["Detail"].default_value = 5
        noise.inputs["Roughness"].default_value = .64
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = .07
        bump.inputs["Distance"].default_value = .0007
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], principled.inputs["Normal"])
    body.data.materials.clear()
    body.data.materials.append(graphite)

    root = bpy.data.objects["V206_GUITAR_ROOT"]
    root_names = {root.name}
    pending = list(root.children)
    while pending:
        obj = pending.pop()
        root_names.add(obj.name)
        pending.extend(obj.children)
    nearby_meshes = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.hide_render:
            continue
        center = obj.matrix_world.translation
        if (center - root.matrix_world.translation).length < 1.1:
            nearby_meshes.append({
                "name": obj.name,
                "under_guitar_root": obj.name in root_names,
                "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
            })

    scene = bpy.context.scene
    scene["V342_STATUS"] = "GRAPHITE_CONTOUR_GUITAR_VISUAL_REVIEW_REQUIRED"
    camera = bpy.data.objects["V323_CAMERA"]
    renders = {
        "full_front": render(scene, camera, RENDERS / "v342_full_front.png", (.18, -3.75, 1.10), (.10, -.10, 1.08), 67, (1000, 1200)),
        "guitar_beauty": render(scene, camera, RENDERS / "v342_guitar_beauty.png", (1.25, -2.25, 1.42), (.33, -.30, 1.35), 82, (1100, 900)),
        "guitar_front": render(scene, camera, RENDERS / "v342_guitar_front.png", (.68, -2.25, 1.46), (.34, -.30, 1.34), 96, (900, 1000)),
    }
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v342-graphite-contour-guitar-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "body_material": graphite.name,
        "nearby_meshes": nearby_meshes,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    AUDIT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V342_GRAPHITE_CONTOUR_OK=" + json.dumps(record["output"], sort_keys=True))


if __name__ == "__main__":
    main()
