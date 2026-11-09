import bpy

path = "/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v205_wardrobe/ant_wardrobe_boots_v205.blend"
with bpy.data.libraries.load(path, link=False) as (data_from, _data_to):
    print([name for name in data_from.objects if name.startswith("V205_")])
