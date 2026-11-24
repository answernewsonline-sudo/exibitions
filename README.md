# Room One: 3D gallery prototype

A browser gallery room built in Blender and shown with Three.js 0.160.0 (loaded from jsDelivr). No build step.

> **Branch `scene-2glb`:** the page shows your uploaded 2.glb (textured room, 21 posters, a mouflon scan and a rock scan). The original is 176 MB, over GitHub's 100 MB file limit, so it is not in the repo (it stays in the project files). `room.glb` (36 MB) is a web version made with `export_scan_web.py`: the mouflon is simplified from 750k to 250k faces, the rock from 650k to 60k, posters are kept at 2048 px and other textures shrunk to 1024 px. Auto mode treats textured objects inside the room as works (22: 21 posters and the mouflon) and the rock, which reaches outside the room, as scenery you can't walk through. `room-one.blend` is still the earlier room, not the source of this scene.

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
