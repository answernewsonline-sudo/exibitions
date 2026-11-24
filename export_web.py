import bpy, sys
src, out = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src, load_ui=False)
# Shrink textures for the web (does not touch the source .blend)
for img in bpy.data.images:
    if img.size[0] == 0: continue
    lim = 1024 if max(img.size) >= 2048 else 512 if max(img.size) > 512 else None
    if lim and max(img.size) > lim:
        s = lim / max(img.size); img.scale(max(1,int(img.size[0]*s)), max(1,int(img.size[1]*s)))
props = bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
kw = dict(filepath=out, export_format='GLB', use_visible=True, export_apply=True,
          export_cameras=False, export_lights=False, export_animations=False, export_yup=True)
if 'export_image_format' in props: kw['export_image_format'] = sys.argv[-3]
if 'export_image_quality' in props: kw['export_image_quality'] = 80
if 'export_jpeg_quality' in props: kw['export_jpeg_quality'] = 80
if 'export_image_add_webp' in props: pass
print("KW", kw)
bpy.ops.export_scene.gltf(**kw)
print("EXPORTED")
