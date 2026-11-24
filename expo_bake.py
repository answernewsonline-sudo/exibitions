"""Rebuild 2.glb as a lit expo hall and bake lighting/shadows into textures.

Usage: python3 expo_bake.py <src.glb> <out.glb> <samples> <floor_px> <other_px>
"""
import bpy, bmesh, sys, math, time
import numpy as np
from mathutils import Vector

src, out, SAMPLES, FLOOR_PX, OTHER_PX = sys.argv[-5], sys.argv[-4], int(sys.argv[-3]), int(sys.argv[-2]), int(sys.argv[-1])
t0 = time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
objs = bpy.data.objects

def select_only(o):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o

# ---------- Simplify heavy scans (applied, so baking is fast) ----------
for o in list(objs):
    if o.type == 'MESH' and len(o.data.polygons) > 120000:
        target = 250000 if o.name.startswith("Corentin") else 60000
        m = o.modifiers.new("Decimate", 'DECIMATE'); m.ratio = target / len(o.data.polygons)
        select_only(o); bpy.ops.object.modifier_apply(modifier=m.name)
        print("decimated", o.name, len(o.data.polygons))

# ---------- Room shell: replace the textured cube with floor + walls ----------
cube = objs["Cube"]
bb = [cube.matrix_world @ Vector(c) for c in cube.bound_box]
X0, X1 = min(p.x for p in bb), max(p.x for p in bb)
Y0, Y1 = min(p.y for p in bb), max(p.y for p in bb)
H = max(p.z for p in bb)
bpy.data.objects.remove(cube)

def mesh_obj(name, verts, faces):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); return o

floor = mesh_obj("Room_Floor", [(X0, Y0, 0), (X1, Y0, 0), (X1, Y1, 0), (X0, Y1, 0)], [(0, 1, 2, 3)])
uvl = floor.data.uv_layers.new(name="UVMap")
for li, loop in enumerate(floor.data.loops):
    v = floor.data.vertices[loop.vertex_index].co
    uvl.data[li].uv = ((v.x - X0) / (X1 - X0), (v.y - Y0) / (Y1 - Y0))

# Walls facing inward
wv = [(X0, Y0, 0), (X1, Y0, 0), (X1, Y1, 0), (X0, Y1, 0), (X0, Y0, H), (X1, Y0, H), (X1, Y1, H), (X0, Y1, H)]
walls = mesh_obj("Room_Walls", wv, [(0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)])
# ensure normals point inward
select_only(walls); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=True); bpy.ops.object.mode_set(mode='OBJECT')

# ---------- Booth back walls + header fascias behind every poster ----------
posters = [o for o in objs if o.type == 'MESH' and o.name.startswith("Plane")]
bm = bmesh.new()
navy_faces, white_faces = [], []
def add_box(center, xaxis, w, h, d, z0, tag):
    x = xaxis.normalized(); y = Vector((0, 0, 1)).cross(x).normalized()
    pts = []
    for dz in (0, h):
        for dx in (-w / 2, w / 2):
            for dy in (-d / 2, d / 2):
                pts.append(bm.verts.new(center + x * dx + y * dy + Vector((0, 0, z0 + dz))))
    idx = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    for f in idx:
        face = bm.faces.new([pts[i] for i in f]); face.material_index = 0 if tag == 'navy' else 1; (navy_faces if tag == 'navy' else white_faces).append(face)
for p in posters:
    mw = p.matrix_world
    n = (mw.to_3x3() @ p.data.polygons[0].normal).normalized(); n.z = 0; n.normalize()
    pb = [mw @ Vector(c) for c in p.bound_box]
    c = sum(pb, Vector()) / 8; c.z = 0
    w = max(max(q.x for q in pb) - min(q.x for q in pb), max(q.y for q in pb) - min(q.y for q in pb))
    along = Vector((0, 0, 1)).cross(n)
    back = c - n * 0.07
    add_box(back, along, w + 0.36, 3.7, 0.1, 0.0, 'navy')               # backer
    add_box(back + n * 0.02, along, w + 0.36, 0.45, 0.16, 3.7, 'white')  # header fascia
booths_me = bpy.data.meshes.new("Room_Booths"); bm.to_mesh(booths_me); bm.free()
booths = bpy.data.objects.new("Room_Booths", booths_me); sc.collection.objects.link(booths)
bmesh.ops.recalc_face_normals  # (box winding already outward)

# ---------- Floor albedo: polished grey, blue carpet aisles, yellow guide lines ----------
def floor_albedo(px):
    W = X1 - X0; D = Y1 - Y0
    xs = X0 + (np.arange(px) + 0.5) / px * W
    ys = Y0 + (np.arange(px) + 0.5) / px * D
    X, Y = np.meshgrid(xs, ys)
    col = np.zeros((px, px, 3)); col[:] = (0.62, 0.63, 0.65)
    rng = np.random.default_rng(3)
    col *= (0.97 + 0.03 * rng.random((px, px, 1)))
    tile = ((np.abs(((X - X0) % 1.2) - 0.6) > 0.59) | (np.abs(((Y - Y0) % 1.2) - 0.6) > 0.59))
    col[tile] *= 0.88
    blue = (0.04, 0.12, 0.42)
    carpets = [
        (X0 + 0.6, X0 + 4.2, Y0 + 0.6, Y1 - 0.6),   # along the west poster wall
        (X0 + 0.6, X1 - 3.5, Y0 + 0.6, Y0 + 4.2),   # along the south poster wall
        (-5.6, 4.0, -1.0, 1.4),                     # centre island in front of the poster row
    ]
    yellow = (0.95, 0.62, 0.05)
    for (a, b, c, d) in carpets:
        m = (X > a) & (X < b) & (Y > c) & (Y < d)
        col[m] = blue
        e = 0.14
        edge = m & ((X < a + e) | (X > b - e) | (Y < c + e) | (Y > d - e))
        col[edge] = yellow
    # Write a PNG directly and load it (setting pixels on a new image proved unreliable here)
    import zlib, struct
    rgb8 = (np.clip(col, 0, 1) ** (1 / 2.2) * 255 + 0.5).astype(np.uint8)[::-1]  # PNG rows top-down
    raw = b"".join(b"\x00" + rgb8[r].tobytes() for r in range(px))
    def chunk(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", px, px, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")
    path = "/tmp/claude-0/-home-user/8d67c560-e606-5302-9439-e54e56ac5c4d/scratchpad/expo/FloorAlbedo.png"; open(path, "wb").write(png)
    img = bpy.data.images.load(path); img.name = "FloorAlbedo"; img.pack()
    return img

# ---------- Materials for the bake ----------
def bake_material(name, albedo, bake_img):
    mt = bpy.data.materials.new(name); mt.use_nodes = True
    nt = mt.node_tree; bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.6
    if isinstance(albedo, tuple): bsdf.inputs["Base Color"].default_value = (*albedo, 1)
    else:
        tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = albedo
        nt.links.new(tx.outputs["Color"], bsdf.inputs["Base Color"])
    tgt = nt.nodes.new("ShaderNodeTexImage"); tgt.image = bake_img; tgt.name = "BAKE"
    nt.nodes.active = tgt
    return mt

def uv_unwrap(o, margin=0.02):
    select_only(o); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=margin, area_weight=1.0)
    bpy.ops.object.mode_set(mode='OBJECT')

bake_floor = bpy.data.images.new("Baked_Floor", FLOOR_PX, FLOOR_PX, float_buffer=True)
bake_walls = bpy.data.images.new("Baked_Walls", OTHER_PX, OTHER_PX, float_buffer=True)
bake_booth = bpy.data.images.new("Baked_Booths", OTHER_PX, OTHER_PX, float_buffer=True)
floor.data.materials.append(bake_material("Baked_Floor", floor_albedo(FLOOR_PX), bake_floor))
uv_unwrap(walls, 0.01)
walls.data.materials.append(bake_material("Baked_Walls", (0.86, 0.87, 0.88), bake_walls))
uv_unwrap(booths, 0.004)
booths.data.materials.append(bake_material("Baked_BoothNavy", (0.03, 0.10, 0.38), bake_booth))
booths.data.materials.append(bake_material("Baked_BoothWhite", (0.90, 0.91, 0.92), bake_booth))

# Blue fascia stripe along the top of the walls (part of the wall albedo would need a texture; use a thin band mesh)
band = mesh_obj("Room_Band", [(X0 + .02, Y0 + .02, 5.2), (X1 - .02, Y0 + .02, 5.2), (X1 - .02, Y1 - .02, 5.2), (X0 + .02, Y1 - .02, 5.2),
                               (X0 + .02, Y0 + .02, 5.8), (X1 - .02, Y0 + .02, 5.8), (X1 - .02, Y1 - .02, 5.8), (X0 + .02, Y1 - .02, 5.8)],
                [(0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)])
bmat = bpy.data.materials.new("Band"); bmat.use_nodes = True
em = bmat.node_tree.nodes["Principled BSDF"]
em.inputs["Base Color"].default_value = (0.05, 0.35, 1.0, 1); em.inputs["Emission Color"].default_value = (0.05, 0.35, 1.0, 1); em.inputs["Emission Strength"].default_value = 3.0
band.data.materials.append(bmat)

# Posters glow like light boxes during the bake (light spills onto floor and booths)
poster_mats = {m for p in posters for m in p.data.materials if m}
for m in poster_mats:
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tx = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
    nt.links.new(tx.outputs["Color"], bsdf.inputs["Emission Color"]); bsdf.inputs["Emission Strength"].default_value = 1.2

# ---------- Expo hall lighting ----------
def light(name, kind, loc, energy, color, size=None, rot=(0, 0, 0), spot=None):
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = color
    if size: d.size = size
    if spot: d.spot_size, d.spot_blend = spot
    o = bpy.data.objects.new(name, d); o.location = loc; o.rotation_euler = rot; sc.collection.objects.link(o); return o
nx, ny = 4, 4
for i in range(nx):
    for j in range(ny):
        x = X0 + (i + 0.5) * (X1 - X0) / nx; y = Y0 + (j + 0.5) * (Y1 - Y0) / ny
        light(f"Hall_{i}{j}", 'AREA', (x, y, H - 0.6), 1400, (0.93, 0.96, 1.0), size=3.0)
# Downlights on each booth
for p in posters:
    mw = p.matrix_world; n = (mw.to_3x3() @ p.data.polygons[0].normal).normalized(); n.z = 0; n.normalize()
    pb = [mw @ Vector(c) for c in p.bound_box]; c = sum(pb, Vector()) / 8
    loc = c + n * 1.6; loc.z = 5.0
    o = light("Booth_" + p.name, 'SPOT', loc, 250, (1.0, 0.95, 0.88), spot=(math.radians(60), 0.6))
    o.rotation_euler = (c - loc).to_track_quat('-Z', 'Y').to_euler()
# Galaxy glow from above (the page draws the animated galaxy on the ceiling)
glow = mesh_obj("CeilingGlow", [(X0, Y0, H), (X1, Y0, H), (X1, Y1, H), (X0, Y1, H)], [(3, 2, 1, 0)])
gm = bpy.data.materials.new("Glow"); gm.use_nodes = True
gb = gm.node_tree.nodes["Principled BSDF"]
gb.inputs["Base Color"].default_value = (0, 0, 0, 1); gb.inputs["Emission Color"].default_value = (0.25, 0.2, 0.6, 1); gb.inputs["Emission Strength"].default_value = 0.35
glow.data.materials.append(gm)
w = bpy.data.worlds.new("W"); w.use_nodes = True; w.node_tree.nodes["Background"].inputs[1].default_value = 0.05; sc.world = w

# ---------- Bake ----------
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SAMPLES
sc.render.bake.margin = 6
sc.cycles.max_bounces = 4
for o, img in ((floor, bake_floor), (walls, bake_walls), (booths, bake_booth)):
    t = time.time()
    select_only(o)
    bpy.ops.object.bake(type='COMBINED')
    # Light denoise: small box blur (lighting is low-frequency)
    a = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)
    k = 1
    pad = np.pad(a[..., :3], ((k, k), (k, k), (0, 0)), mode='edge')
    acc = sum(pad[k + dy:k + dy + a.shape[0], k + dx:k + dx + a.shape[1]] for dy in (-k, 0, k) for dx in (-k, 0, k)) / 9
    a[..., :3] = acc
    img.pixels.foreach_set(a.ravel())
    print("baked", o.name, img.size[:], round(time.time() - t), "s")

# ---------- Exposure: one scale for all maps, soft highlight roll-off ----------
def lum(a): return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
arrs = {img: np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4) for img in (bake_floor, bake_walls, bake_booth)}
ref = np.percentile(np.concatenate([lum(arrs[bake_floor]).ravel(), lum(arrs[bake_walls]).ravel()]), 90)
scale = 1.0 / max(ref, 1e-6)
print("exposure scale", scale, "p90", ref)
for img, a in arrs.items():
    x = a[..., :3] * scale
    a[..., :3] = 1.0 - np.exp(-1.0 * x)    # p90 -> ~0.63 linear (~0.82 sRGB)
    img.pixels.foreach_set(a.ravel())

# ---------- Swap to export materials ----------
def export_material(name, img):
    mt = bpy.data.materials.new(name); mt.use_nodes = True; nt = mt.node_tree
    bsdf = nt.nodes["Principled BSDF"]; bsdf.inputs["Roughness"].default_value = 1.0
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img
    nt.links.new(tx.outputs["Color"], bsdf.inputs["Base Color"]); return mt
for o, img, nm in ((floor, bake_floor, "Baked_Floor"), (walls, bake_walls, "Baked_Walls")):
    o.data.materials.clear(); o.data.materials.append(export_material(nm, img))
bm_mat = export_material("Baked_Booths", bake_booth)
booths.data.materials.clear(); booths.data.materials.append(bm_mat)
for poly in booths.data.polygons: poly.material_index = 0
for m in poster_mats:
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    for l in list(bsdf.inputs["Emission Color"].links): nt.links.remove(l)
    bsdf.inputs["Emission Strength"].default_value = 0.0
for o in list(objs):
    if o.type == 'LIGHT' or o.name in ("CeilingGlow",): bpy.data.objects.remove(o)
# Band keeps its emissive look (exported as emissive)
for img in (bake_floor, bake_walls, bake_booth):
    img.filepath_raw = f"/tmp/claude-0/-home-user/8d67c560-e606-5302-9439-e54e56ac5c4d/scratchpad/expo/{img.name}.png"
    img.file_format = 'PNG'; img.save()
# Shrink remaining textures
for img in bpy.data.images:
    if not img.size[0] or img.name.startswith("Baked_") or img.name == "FloorAlbedo": continue
    lim = 2048 if img.name.startswith("98f59f_") else 1024
    if max(img.size) > lim:
        s = lim / max(img.size); img.scale(int(img.size[0] * s), int(img.size[1] * s))
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_image_format='JPEG', export_jpeg_quality=88,
                          export_cameras=False, export_lights=False, export_animations=False)
print("EXPORTED", round(time.time() - t0), "s")
