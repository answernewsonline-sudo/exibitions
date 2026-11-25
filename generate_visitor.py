"""
Builds a simple low-poly "gallery visitor" character from scratch (no external
assets): a small hierarchy of empties (joints) each parenting a box/sphere mesh
segment, animated with keyframes on the joints only (no skinning needed).
Exports visitor.glb with three looping/poseable actions: Idle, Walk, Sit.

Run with the pip `bpy` module:  python3 -I generate_visitor.py
"""
import bpy, math, random

random.seed(7)

# ---------- clean scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.frame_start = 1

def new_empty(name, parent, local_offset):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.05
    scene.collection.objects.link(e)
    if parent is not None:
        e.parent = parent  # matrix_parent_inverse left as identity: location is a LOCAL offset, stacking hierarchically
    e.location = local_offset
    return e

def new_box(name, parent, size, local_offset, color):
    bpy.ops.mesh.primitive_cube_add(size=1)
    m = bpy.context.active_object
    m.name = name
    m.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    mat = bpy.data.materials.new(name + "_mat")
    mat.diffuse_color = color
    m.data.materials.append(mat)
    m.parent = parent
    m.location = local_offset
    return m

def new_sphere(name, parent, radius, local_offset, color):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=10, ring_count=7)
    m = bpy.context.active_object
    m.name = name
    mat = bpy.data.materials.new(name + "_mat")
    mat.diffuse_color = color
    m.data.materials.append(mat)
    m.parent = parent
    m.location = local_offset
    return m

# ---------- palette: quiet graphite / paper, matching the gallery HUD ----------
SKIN   = (0.86, 0.73, 0.60, 1)
SHIRT  = (0.50, 0.63, 0.73, 1)   # --accent-ish gallery blue
PANTS  = (0.14, 0.15, 0.17, 1)   # --ink
SHOE   = (0.09, 0.10, 0.11, 1)

# ---------- segment lengths (m) ----------
HIP_H, THIGH, SHIN, CHEST, NECK_HEAD = 0.90, 0.45, 0.45, 0.28, 0.27
SHOULDER_X, UPPER_ARM, LOWER_ARM = 0.20, 0.27, 0.24
HIP_X = 0.11

root = new_empty("Visitor_Root", None, (0, 0, 0))
hips = new_empty("J_Hips", root, (0, 0, HIP_H))
new_box("B_Pelvis", hips, (0.28, 0.18, 0.18), (0, 0, -0.04), PANTS)

chest = new_empty("J_Chest", hips, (0, 0, CHEST))
new_box("B_Torso", chest, (0.32, 0.20, CHEST * 1.05), (0, 0, CHEST * 0.5), SHIRT)

head = new_empty("J_Head", chest, (0, 0, NECK_HEAD))
new_sphere("B_Head", head, 0.11, (0, 0, 0.12), SKIN)

arms = {}
for side, sx in (("L", 1), ("R", -1)):
    ua = new_empty(f"J_UpperArm_{side}", chest, (sx * SHOULDER_X, 0, CHEST * 0.92))
    new_box(f"B_UpperArm_{side}", ua, (0.09, 0.09, UPPER_ARM), (0, 0, -UPPER_ARM * 0.5), SHIRT)
    la = new_empty(f"J_LowerArm_{side}", ua, (0, 0, -UPPER_ARM))
    new_box(f"B_LowerArm_{side}", la, (0.08, 0.08, LOWER_ARM), (0, 0, -LOWER_ARM * 0.5), SKIN)
    hd = new_empty(f"J_Hand_{side}", la, (0, 0, -LOWER_ARM))
    new_box(f"B_Hand_{side}", hd, (0.07, 0.04, 0.10), (0, 0, -0.05), SKIN)
    arms[side] = (ua, la, hd)

legs = {}
for side, sx in (("L", 1), ("R", -1)):
    ul = new_empty(f"J_UpperLeg_{side}", hips, (sx * HIP_X, 0, -0.03))
    new_box(f"B_UpperLeg_{side}", ul, (0.14, 0.14, THIGH), (0, 0, -THIGH * 0.5), PANTS)
    ll = new_empty(f"J_LowerLeg_{side}", ul, (0, 0, -THIGH))
    new_box(f"B_LowerLeg_{side}", ll, (0.12, 0.12, SHIN), (0, 0, -SHIN * 0.5), PANTS)
    ft = new_empty(f"J_Foot_{side}", ll, (0, 0, -SHIN))
    new_box(f"B_Foot_{side}", ft, (0.10, 0.24, 0.06), (0, -0.07, -0.03), SHOE)
    legs[side] = (ul, ll, ft)

JOINTS = [hips, chest, head] + [b for s in arms.values() for b in s] + [b for s in legs.values() for b in s]

def key(obj, frame, rot_euler_deg=None, loc=None):
    if rot_euler_deg is not None:
        obj.rotation_euler = tuple(math.radians(d) for d in rot_euler_deg)
        obj.keyframe_insert("rotation_euler", frame=frame)
    if loc is not None:
        obj.location = loc
        obj.keyframe_insert("location", frame=frame)

FPS = 24
scene.render.fps = FPS

# ---------- IDLE: quiet standing, head turning to "look around", gentle breathing ----------
def build_idle(end):
    ua_l, la_l, hd_l = arms["L"]; ua_r, la_r, hd_r = arms["R"]
    key(hips, 1, rot_euler_deg=(0, 0, 0))
    key(chest, 1, rot_euler_deg=(1, 0, 0))
    key(chest, end // 2, rot_euler_deg=(2.5, 0, 0))
    key(chest, end, rot_euler_deg=(1, 0, 0))
    # head looks around: left, centre, right, centre
    pts = [(1, 0), (0.28, -28), (0.52, 10), (0.76, 24), (1.0, 0)]
    for t, yaw in pts:
        key(head, max(1, round(t * end)), rot_euler_deg=(-4, 0, yaw))
    for ua, la, hd, sx in ((ua_l, la_l, hd_l, 1), (ua_r, la_r, hd_r, -1)):
        key(ua, 1, rot_euler_deg=(4, 0, sx * 4)); key(ua, end, rot_euler_deg=(4, 0, sx * 4))
        key(la, 1, rot_euler_deg=(8, 0, 0)); key(la, end, rot_euler_deg=(8, 0, 0))
    for ul, ll, ft in (legs["L"], legs["R"]):
        key(ul, 1, rot_euler_deg=(0, 0, 0)); key(ul, end, rot_euler_deg=(0, 0, 0))
        key(ll, 1, rot_euler_deg=(0, 0, 0)); key(ll, end, rot_euler_deg=(0, 0, 0))
        key(ft, 1, rot_euler_deg=(0, 0, 0)); key(ft, end, rot_euler_deg=(0, 0, 0))
    key(root, 1, loc=(0, 0, 0)); key(root, end, loc=(0, 0, 0))

# ---------- WALK: in-place cycle; JS drives world translation/heading ----------
def build_walk(end):
    ua_l, la_l, _ = arms["L"]; ua_r, la_r, _ = arms["R"]
    ul_l, ll_l, ft_l = legs["L"]; ul_r, ll_r, ft_r = legs["R"]
    SWING = 26  # hip swing amplitude deg
    for frac in (0, 0.25, 0.5, 0.75, 1.0):
        f = max(1, round(frac * end))
        ang = frac * 2 * math.pi
        legL = math.sin(ang) * SWING
        legR = math.sin(ang + math.pi) * SWING
        kneeL = max(0, -math.sin(ang + 0.6) * 48)       # bends while leg swings forward-to-back
        kneeR = max(0, -math.sin(ang + math.pi + 0.6) * 48)
        footL = -legL * 0.3
        footR = -legR * 0.3
        key(ul_l, f, rot_euler_deg=(legL, 0, 0)); key(ul_r, f, rot_euler_deg=(legR, 0, 0))
        key(ll_l, f, rot_euler_deg=(kneeL, 0, 0)); key(ll_r, f, rot_euler_deg=(kneeR, 0, 0))
        key(ft_l, f, rot_euler_deg=(footL, 0, 0)); key(ft_r, f, rot_euler_deg=(footR, 0, 0))
        key(ua_l, f, rot_euler_deg=(-legL * 0.7, 0, 4)); key(ua_r, f, rot_euler_deg=(-legR * 0.7, 0, -4))
        key(la_l, f, rot_euler_deg=(14, 0, 0)); key(la_r, f, rot_euler_deg=(14, 0, 0))
        key(chest, f, rot_euler_deg=(3, 0, -legL * 0.15))
        key(head, f, rot_euler_deg=(-2, 0, 0))
        key(hips, f, rot_euler_deg=(0, 0, legR * 0.08))
        bob = abs(math.sin(ang * 2)) * 0.018
        key(root, f, loc=(0, 0, bob))

# ---------- SIT: seated pose (world placement handled by the caller at runtime) ----------
def build_sit(end):
    ua_l, la_l, _ = arms["L"]; ua_r, la_r, _ = arms["R"]
    ul_l, ll_l, ft_l = legs["L"]; ul_r, ll_r, ft_r = legs["R"]
    for ul, ll, ft in ((ul_l, ll_l, ft_l), (ul_r, ll_r, ft_r)):
        key(ul, 1, rot_euler_deg=(-92, 0, 0)); key(ul, end, rot_euler_deg=(-92, 0, 0))
        key(ll, 1, rot_euler_deg=(96, 0, 0)); key(ll, end, rot_euler_deg=(96, 0, 0))
        key(ft, 1, rot_euler_deg=(10, 0, 0)); key(ft, end, rot_euler_deg=(10, 0, 0))
    for ua, la, sx in ((ua_l, la_l, 1), (ua_r, la_r, -1)):
        key(ua, 1, rot_euler_deg=(2, 0, sx * 6)); key(ua, end, rot_euler_deg=(2, 0, sx * 6))
        key(la, 1, rot_euler_deg=(26, 0, 0)); key(la, end, rot_euler_deg=(26, 0, 0))
    key(chest, 1, rot_euler_deg=(4, 0, 0))
    key(chest, end // 2, rot_euler_deg=(6, 0, 0))
    key(chest, end, rot_euler_deg=(4, 0, 0))
    pts = [(1, 0), (0.4, 18), (0.75, -16), (1.0, 0)]
    for t, yaw in pts:
        key(head, max(1, round(t * end)), rot_euler_deg=(2, 0, yaw))
    key(root, 1, loc=(0, 0, -THIGH))
    key(root, end, loc=(0, 0, -THIGH))

for o in [root, hips, chest, head] + [b for s in arms.values() for b in s] + [b for s in legs.values() for b in s]:
    o.rotation_mode = 'XYZ'

actions_spec = [("Idle", 3.0, build_idle), ("Walk", 1.0, build_walk), ("Sit", 3.0, build_sit)]
all_objs = [root, hips, chest, head] + [b for s in arms.values() for b in s] + [b for s in legs.values() for b in s]

# Build each action, then push each object's resulting Action into its NLA
# track (named after the clip) so glTF export emits one named animation that
# drives every joint together.
for o in all_objs:
    o.rotation_mode = 'XYZ'

for clip_name, length_s, builder in actions_spec:
    # Note: do NOT call animation_data_clear() here — it would also wipe the
    # NLA tracks already pushed for earlier clips. Each object's
    # animation_data.action was reset to None after the previous clip was
    # pushed, so keyframe_insert below starts a fresh Action for this clip.
    builder(int(length_s * FPS))
    for o in all_objs:
        if not (o.animation_data and o.animation_data.action):
            o.animation_data_create()
            if o.animation_data.action is None:
                continue
        act = o.animation_data.action
        act.name = f"{clip_name}__{o.name}"
        track = o.animation_data.nla_tracks.new()
        track.name = clip_name
        strip = track.strips.new(clip_name, 1, act)
        strip.name = clip_name
        o.animation_data.action = None

bpy.ops.object.select_all(action='SELECT')

bpy.ops.export_scene.gltf(
    filepath="visitor.glb",
    export_format='GLB',
    use_visible=True,
    export_animations=True,
    export_animation_mode='NLA_TRACKS',
    export_nla_strips=True,
    export_merge_animation='NLA_TRACK',
    export_nla_strips_merged_animation_name='Animation',
    export_force_sampling=True,
    export_optimize_animation_size=False,
    export_optimize_animation_keep_anim_object=True,
    export_frame_range=False,
    export_cameras=False,
    export_lights=False,
    export_yup=True,
)
print("EXPORTED visitor.glb")
