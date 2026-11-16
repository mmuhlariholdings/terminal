# Enclosure and 3D model

The whole Terminal 1, inside and out, as one Onshape custom feature written in FeatureScript: mid-frame, carbon back with radio
window, cover glass, screen, keyboard deck, Q20 keyboard and navigation keys, trackpad, both circuit boards, the CM4, thermal
pad, battery, USB-C socket and power button. It proves the boards, battery and screen fit before anything is ordered.

| File | What |
|---|---|
| [`terminal-1.fs`](terminal-1.fs) | **The model.** Source of the Onshape Feature Studio "Terminal 1 FS". Every number comes from [`system/plan/interfaces.md`](../../system/plan/interfaces.md) |
| [`terminal-1-check.fs`](terminal-1-check.fs) | Test feature: mass, bounding box and interference between every pair of parts |
| [`build-sheet.md`](build-sheet.md) | Design spec: coordinates, parts, materials, mass, open items |
| [`terminal-1.glb`](terminal-1.glb) | glTF export (2026-11-17, internal parts hidden: 13 parts). Same file as `website/public/assets/models/terminal-1.glb` |

**Onshape document:** [Terminal 1](https://cad.onshape.com/documents/8bfe7e43f7d7ec8135f9a829/w/29c38cad0998e4a6472b08e0/e/69201118ddf43601f28283ef)
· Feature Studio **Terminal 1 FS** (element `3bc3af66b798a4c48861a367`).

## Put the model in the Part Studio (one time, about 2 minutes)

1. Open the Onshape document (link above). Click the **Part Studio** tab at the bottom.
2. In the toolbar, click the **Custom features** icon (a puzzle piece / "Add custom features"). Choose the **Current document**
   tab, tick **Terminal 1 FS**, and click **Add**. The **Terminal 1** button now appears at the right end of the toolbar.
3. Click **Terminal 1**. A dialog opens with two fields:
   - **Exploded view spacing**: leave at 0 mm for the assembled device; try 12 mm to pull the layers apart.
   - **Show internal parts**: ticked shows boards, CM4 and battery.
4. Click the green tick. 18 named parts appear in the parts list. The feature's info line shows the estimated mass (about 291 g).

To see a cross-section: right-click the empty canvas → **Section view** → pick the **Right** plane.

## Export the 3D model for the website

1. In the Part Studio, right-click the **Part Studio tab** at the bottom → **Export...**
2. Format **GLTF** (choose the binary `.glb` option if offered), resolution **Medium**, tick **Export as one file**. Click **Export**.
3. Save the downloaded file as `hardware/enclosure/terminal-1.glb` (rename it: lowercase, hyphens), **and** copy it to
   `website/public/assets/models/terminal-1.glb`. The website's 3D viewer picks it up automatically.
4. Optional: edit the feature to **Exploded view spacing 12 mm** with **Show internal parts** ticked, export again, and save it as
   `website/public/assets/models/terminal-1-exploded.glb`. The website then shows an **Exploded view** button that swaps to it.

Colours: Onshape writes its colours into glTF without converting them, so they look washed out. The website corrects this
when it loads the model (`finishMaterials` in `website/public/assets/js/site.js`, keyed on the `T1_C_*` colours in
`terminal-1.fs`), so a fresh export needs no other changes. If you change a colour in the FeatureScript, update that table too.

## Changing the model

1. Change the number in [`system/plan/interfaces.md`](../../system/plan/interfaces.md) first (and its changelog).
2. Edit [`terminal-1.fs`](terminal-1.fs) to match.
3. **Verify with a real regeneration** before saving to the Feature Studio: paste into a scratch Feature Studio or run it through
   the Onshape MCP `create_geometry` tool; run [`terminal-1-check.fs`](terminal-1-check.fs) and expect **0 clashes**.
4. Paste the file into **Terminal 1 FS** (select all, paste, save). Existing Terminal 1 features update; if you added dialog
   fields, delete and re-insert the feature.
5. Re-export the `.glb` files (above) and update [`build-sheet.md`](build-sheet.md).

FeatureScript lessons learned (they cost real API calls to find):

- `type` is a reserved word: read map fields as `c["type"]`, not `c.type`.
- Don't name your own functions after standard-library ones (`hole` exists); this file prefixes everything with `t1` / `T1_`.
- All sub-operations of one id (`id + "frame" + ...`) must be contiguous: create cutting tools *before* the part, under a sibling id.
- A compile error in `test_feature` only says "no features found": bisect with small pieces.
- `test_feature` runs the **first** feature in the file; put the check feature first.
