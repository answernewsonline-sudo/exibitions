import bpy, sys
fmt, src, out = sys.argv[-3], sys.argv[-2], sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
# Decimate very dense scans so phones can draw them
for o in bpy.data.objects:
    if o.type == 'MESH' and len(o.data.polygons) > 120000:
        m = o.modifiers.new("Decimate", 'DECIMATE'); m.ratio = (250000 if o.name.startswith("Corentin") else 60000) / len(o.data.polygons); m.use_collapse_triangulate = True
        print("DECIMATE", o.name, len(o.data.polygons), "->", round(m.ratio, 3))
for img in bpy.data.images:
    if not img.size[0]: continue
    lim = 2048 if img.name.startswith("98f59f_") else 1024
    if max(img.size) > lim:
        s = lim / max(img.size); img.scale(int(img.size[0]*s), int(img.size[1]*s))
bpy.ops.export_scene.gltf(filepath=out, export_format=fmt, export_apply=True, export_image_format='JPEG', export_jpeg_quality=85,
    export_cameras=False, export_lights=False, export_animations=False)
print("EXPORTED")
