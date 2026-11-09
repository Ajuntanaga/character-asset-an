from pathlib import Path

import bpy
from mathutils import Vector

from pipeline import build_v204_groom as build


ROOT = Path(__file__).resolve().parents[1]


def make_material() -> bpy.types.Material:
    material = bpy.data.materials.get("MAT_V204_SCALP_SUBSTRATE") or bpy.data.materials.new("MAT_V204_SCALP_SUBSTRATE")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.inputs["Base Color"].default_value = (0.003, 0.002, 0.0015, 1.0)
    principled.inputs["Roughness"].default_value = 0.50
    principled.inputs["Specular IOR Level"].default_value = 0.22
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 210.0
    noise.inputs["Detail"].default_value = 5.0
    noise.inputs["Roughness"].default_value = 0.72
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.34
    bump.inputs["Distance"].default_value = 0.0012
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], principled.inputs["Normal"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    return material


def main() -> None:
    for name in ("V204_HAIRLINE_CURLS", "V204_SCALP_SUBSTRATE"):
        old = bpy.data.objects.get(name)
        if old is not None:
            bpy.data.objects.remove(old, do_unlink=True)

    body = bpy.data.objects["V202_BODY"]
    mesh = body.data
    selected = []
    used = set()
    for poly in mesh.polygons:
        world_center = body.matrix_world @ poly.center
        front_factor = max(0.0, min(1.0, (-world_center.y - 0.015) / 0.080))
        side_factor = min(1.0, abs(world_center.x) / 0.090)
        hairline = 1.715 + 0.045 * front_factor + 0.015 * side_factor
        if world_center.z < hairline:
            continue
        selected.append(poly)
        used.update(poly.vertices)
    mapping = {old: new for new, old in enumerate(sorted(used))}
    vertices = []
    for index in sorted(used):
        vertex = mesh.vertices[index]
        vertices.append(vertex.co + vertex.normal * 0.00055)
    faces = [tuple(mapping[index] for index in poly.vertices) for poly in selected]
    cap_mesh = bpy.data.meshes.new("V204_SCALP_SUBSTRATE_MESH")
    cap_mesh.from_pydata(vertices, [], faces)
    cap_mesh.update()
    cap = bpy.data.objects.new("V204_SCALP_SUBSTRATE", cap_mesh)
    bpy.data.collections["V204_GROOM_SYSTEMS"].objects.link(cap)
    cap.matrix_world = body.matrix_world.copy()
    cap.data.materials.append(make_material())
    cap["purpose"] = "dense short-curl scalp substrate beneath explicit fibers"

    build.configure_render()
    scene = bpy.context.scene
    scene.camera = bpy.data.objects["V204_CAM_FRONT"]
    scene.render.resolution_x = 640
    scene.render.resolution_y = 640
    scene.cycles.samples = 20
    path = ROOT / "production_v204_groom" / "analysis" / "scalp_substrate_preview.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    print(f"V204_SCALP_SUBSTRATE_PREVIEW_OK path={path.relative_to(ROOT)} faces={len(faces)}")


if __name__ == "__main__":
    main()
