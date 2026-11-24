import bpy, math, mathutils
print("BLENDER", bpy.app.version_string)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='/mnt/project-files/gallery-prototype/room-one.glb')
sc = bpy.context.scene
# Collections
def coll(name):
    c = bpy.data.collections.new(name); sc.collection.children.link(c); return c
cRoom, cArt, cLight = coll("Room"), coll("Artworks"), coll("Lighting")
for o in list(bpy.data.objects):
    target = cLight if o.type=='LIGHT' else cArt if o.name.startswith("Cat") else cRoom
    for c in o.users_collection: c.objects.unlink(o)
    target.objects.link(o)
# Re-light: remove imported lights, add Blender-native ones
for o in [o for o in bpy.data.objects if o.type=='LIGHT']: bpy.data.objects.remove(o)
for o in [o for o in bpy.data.objects if o.type=='EMPTY' and not o.children and not o.name.startswith(('Cat','RoomOne'))]: bpy.data.objects.remove(o)
def add_light(name, kind, loc, energy, rot=None, size=None, color=(1,0.95,0.88), spot=None):
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = color
    if size and kind=='AREA': d.shape='RECTANGLE'; d.size, d.size_y = size
    if spot: d.spot_size, d.spot_blend = spot
    o = bpy.data.objects.new(name, d); o.location = loc
    if rot: o.rotation_euler = rot
    cLight.objects.link(o); return o
# Skylight slots (glTF Y-up z=-3.6,0,3.6 -> Blender y=3.6,0,-3.6), ceiling 4.4
for i,y in enumerate((3.6,0,-3.6)):
    add_light(f"Skylight_{i+1}", 'AREA', (0,y,4.35), 110, size=(12.8,0.5), color=(0.96,0.98,1.0))
# Picture lights aimed at each canvas
for o in bpy.data.objects:
    if o.name.endswith("_Canvas"):
        p = o.matrix_world.translation.copy()
        n = (o.matrix_world.to_3x3() @ mathutils.Vector((0,0,1))).normalized()
        n.z = 0; n.normalize()
        loc = p + n*1.8; loc.z = 4.2
        l = add_light("Picture_"+o.name.split('_')[0], 'SPOT', loc, 450, spot=(math.radians(55), 0.7))
        l.rotation_euler = (p - loc).to_track_quat('-Z','Y').to_euler()
knot = next(o for o in bpy.data.objects if o.name.endswith("_Bronze"))
kl = add_light("Picture_Cat07", 'SPOT', knot.matrix_world.translation + mathutils.Vector((1.6,1.6,3.0)), 220, spot=(math.radians(30),0.5))
kl.rotation_euler = (knot.matrix_world.translation - kl.location).to_track_quat('-Z','Y').to_euler()
# World
w = bpy.data.worlds.new("Gallery"); w.use_nodes=True
w.node_tree.nodes["Background"].inputs[0].default_value=(0.85,0.86,0.85,1); w.node_tree.nodes["Background"].inputs[1].default_value=0.1
sc.world = w
# Camera at entrance, eye height 1.62 (web start: z=4.7 in glTF -> y=-4.7)
cam = bpy.data.objects.new("Camera_Entrance", bpy.data.cameras.new("Camera_Entrance"))
cam.data.lens = 22; cam.location = (0,-4.7,1.62); cam.rotation_euler = (math.radians(88),0,0)
sc.collection.objects.link(cam); sc.camera = cam
# Render settings
sc.render.engine = 'CYCLES'; sc.cycles.samples = 64; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 800
sc.view_settings.view_transform = 'AgX' if 'AgX' in [i.identifier for i in sc.view_settings.bl_rna.properties['view_transform'].enum_items] else 'Filmic'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath='/mnt/project-files/gallery-prototype/room-one.blend', compress=True)
sc.render.filepath = '/mnt/project-files/gallery-prototype/room-one-render.png'
bpy.ops.render.render(write_still=True)
print("DONE")
