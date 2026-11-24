# Room One: 3D gallery prototype

A browser gallery room built in Blender and shown with Three.js 0.160.0 (loaded from jsDelivr). No build step.

> **Branch `scene-2glb`:** the page shows your uploaded 2.glb restyled as an expo hall: light grey polished floor with blue carpet aisles and yellow guide lines, white walls with a glowing blue band, navy booth backers and white header fascias behind every poster, an animated galaxy on the ceiling. Lighting (16 hall area lights, a downlight per booth, posters glowing like light boxes, ceiling glow) is baked with Cycles into `Baked_Floor` (2048 px), `Baked_Walls` and `Baked_Booths` (1024 px); the page shows those surfaces unlit, so shadows cost nothing at runtime. `room.glb` is 11.3 MB (was 36.5 MB): meshopt geometry compression and WebP textures. Rebuild: `python3 expo_bake.py 2.glb expo.glb 32 2048 1024` with Blender's `bpy`, then `gltf-transform webp expo.glb w.glb --quality 82 && gltf-transform meshopt w.glb room.glb`. The 176 MB original 2.glb is over GitHub's file limit and is kept in the project files only.

## Files
- `room-one.blend`: the Blender scene (source of truth). Room, seven works, desk and chair, figure.
- `room.glb`: web export of the visible objects in `room-one.blend`, textures shrunk to 1024 px JPEG/PNG (about 14 MB).
- `index.html`: the page. Loads `room.glb`, adds lights, walking, artwork clicks and the label panel.
- `gallery.html`: same page without the HTML shell (used for the Claude artifact preview).
- `export_web.py`: makes `room.glb` from the .blend.

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
