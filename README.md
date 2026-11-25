# Room One: 3D gallery prototype

A browser gallery room built in Blender and shown with Three.js 0.160.0 (loaded from jsDelivr). No build step.

## Files
- `room-one.blend`: the Blender scene (source of truth). Room, seven works, desk and chair, figure.
- `room.glb`: web export of the visible objects in `room-one.blend`, textures shrunk to 1024 px JPEG/PNG (about 14 MB).
- `index.html`: the page. Loads `room.glb` and `visitor.glb`, adds lights, walking, artwork clicks, the label panel and the wandering visitors.
- `gallery.html`: same page without the HTML shell (used for the Claude artifact preview).
- `export_web.py`: makes `room.glb` from the .blend.
- `generate_visitor.py`: builds `visitor.glb` — a small procedural low-poly "gallery visitor" character (no external model or Mixamo/manual rigging needed) with three baked clips: `Idle` (quiet standing, head turning to look around), `Walk` (in-place leg/arm cycle — `index.html` drives the actual room translation), and `Sit` (seated pose). Run with `python3 -I generate_visitor.py` (needs the `bpy` pip package: `pip install bpy`).
- `visitor.glb`: output of `generate_visitor.py`. No skeleton/skinning — each limb is a plain parented node, so `index.html` clones instances with `.clone(true)` rather than `SkeletonUtils`.

## Visitors (wandering figures)
`index.html` loads `visitor.glb`, spawns a few clones (`V_COUNT`), and runs a small per-character state machine: `idle` (look around, wait) → `walk` (to a random floor point, or to the one office chair if it's free — reusing the room's existing `obstacles`/floor-bounds logic) → `sitting` (holds the `Sit` pose for a while) → back to `idle`. The chair's seat position (`SEATS` in `index.html`) is hand-estimated from the `Chair` node's transform in `room.glb`; nudge `x`/`z`/`seatY`/`yaw` there by eye, and add more entries if more chairs are added to the room. There's no real pathfinding — only the *destination* of a random walk is checked against obstacles, so a character can still clip room furniture mid-stride; good enough for a prototype, not production-grade crowd AI.

To regenerate or restyle the visitor (recolor, add a clip, change timing), edit `generate_visitor.py` and rerun it — it's plain Python/`bpy`, no manual Blender rigging required.

## Updating the room from Blender
1. Edit `room-one.blend` and save.
2. Re-export: in Blender use File › Export › glTF 2.0 (.glb), Include: Visible Objects, no cameras, lights or animation; or run
   `blender -b room-one.blend -P export_web.py -- JPEG room-one.blend room.glb`
3. Commit both files.

The page finds artworks by object name: anything under an object named `Cat01_…` to `Cat07_…` opens that work's label. Canvases must be named `…_Canvas`, the sculpture `…_Bronze`. Floor must be `Room_Floor`; the room size comes from it. Objects starting with `Room_` are treated as walls/floor/ceiling; every other object standing on the floor blocks walking.

Lighting is added in the page (soft fill, one shadow light, a spotlight per work), not taken from Blender. For best looks and speed, bake lighting into the textures in Blender before export.

## Previewing locally
ES modules and the .glb need http(s): run `npx serve .` in this folder and open the printed address. Any static host (Netlify, Vercel, GitHub Pages) works.

## Controls
- Desktop: drag to look, click floor to walk, click artwork for its label, WASD/arrows to move (Q/E or ←/→ turn, Shift faster), wheel to step, `[` `]` previous/next, Esc closes the label.
- Touch: drag to look, tap floor to walk, tap artwork for its label.

Works, artists and texts are placeholders; edit the `WORKS` array at the top of the script.
