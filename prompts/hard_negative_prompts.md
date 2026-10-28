# MischiefCam · Targeted hard-negative prompts (H01–H10)

Almost all false alarms in the 2026-10-22 tests came from two categories; this batch targets them. **All are negatives**; the sofa is the only forbidden object.
Save the clips as `H01.mp4` … `H10.mp4` (IDs only, so labelling stays blind) in `data/HardNeg-Videos/`.

- **Category A (H01–H05)**: the dog chews **a rag, old towel or torn plush toy on the floor**; the sofa itself is intact (v01 type).
- **Category B (H06–H10)**: the dog **chews a toy or bone on the sofa**, especially when the toy is small, close to the sofa's colour, or the dog is small in frame (w08 type).

The video generator sometimes makes the dog bite the sofa anyway; label what is visible, and relabel such clips as positive.

| ID | View | Category | Target |
|---|---|---|---|
| H01 | close | A | old towel scrap on the floor |
| H02 | close | A | torn plush toy with white filling on the floor |
| H03 | medium | A | fabric scrap on the floor |
| H04 | medium | A | stuffed toy on the floor at night |
| H05 | wide | A | rope scrap on the floor near the sofa |
| H06 | close | B | small toy the same color as the sofa |
| H07 | medium | B | bone on sofa cushion |
| H08 | medium | B | rope toy on sofa armrest |
| H09 | wide | B | toy on sofa, dog small in frame |
| H10 | wide | B | plush toy on sofa, shaking it |

## H01 · close · Category A · old towel scrap on the floor

```text
A photorealistic CCTV-style video of a golden retriever in a bright living room during daytime, seen from a fixed indoor camera on a shelf facing a gray fabric sofa. The sofa fills most of the frame. At the start of the clip the sofa is completely undamaged. The dog lies on the floor directly in front of the sofa, holding a torn old gray towel between its front paws and chewing and tugging it, shaking its head. The towel lies on the floor; the dog's mouth never touches the sofa. The sofa itself stays completely intact for the whole clip: its fabric is never bitten, torn or pulled, and no stuffing comes out of the sofa. The camera never zooms in, pans or follows the dog. Close CCTV view of the sofa, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## H02 · close · Category A · torn plush toy with white filling on the floor

```text
A photorealistic CCTV-style video of a beagle in a cozy living room in the early evening under warm lamp light, seen from a fixed fisheye home security camera with a dark circular vignette mounted on the wall opposite a beige sofa. At the start of the clip the sofa is completely undamaged. A torn plush dog toy lies on the rug in front of the sofa with white polyester filling spilling out of it. The dog lies next to the toy and chews it, pulling out tufts of filling that land on the rug. The filling clearly comes from the toy, not from the sofa. The sofa itself stays completely intact for the whole clip: its fabric is never bitten, torn or pulled, and no stuffing comes out of the sofa. The camera never zooms in, pans or follows the dog. Close CCTV view of the sofa, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## H03 · medium · Category A · fabric scrap on the floor

```text
A photorealistic CCTV-style video of a living room on an overcast afternoon, recorded by a fixed security camera mounted high in a corner. The frame shows the whole navy blue fabric sofa and part of the floor in front of it. A black Labrador retriever occupies about one tenth of the image. At the start of the clip the sofa is completely undamaged. The dog lies on the floor beside the sofa armrest and chews a loose piece of blue fabric held between its paws, tugging it with its teeth. The fabric scrap is on the floor; the dog never bites the sofa. The sofa itself stays completely intact for the whole clip: its fabric is never bitten, torn or pulled, and no stuffing comes out of the sofa. The camera never zooms in, pans or follows the dog. Medium-wide shot, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## H04 · medium · Category A · stuffed toy on the floor at night

```text
A photorealistic CCTV-style video of a living room at night, recorded in black-and-white infrared night-vision mode by a fixed ceiling-mounted camera looking down at an angle. The frame shows the whole light fabric sofa, a coffee table and part of a rug. A boxer occupies about one tenth of the image. At the start of the clip the sofa is completely undamaged. The dog lies on the rug pressed against the front of the sofa, chewing a stuffed toy; bits of white filling from the toy scatter on the rug. Its head is next to the sofa but only the toy is ever in its mouth. The sofa itself stays completely intact for the whole clip: its fabric is never bitten, torn or pulled, and no stuffing comes out of the sofa. The camera never zooms in, pans or follows the dog. Medium-wide shot, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic infrared night-vision footage, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## H05 · wide · Category A · rope scrap on the floor near the sofa

```text
A photorealistic CCTV-style video of an entire modern living room during bright daytime, seen from a fixed security camera mounted high in a corner near the ceiling. The whole room is visible: a cream fabric sofa against the far wall, a coffee table, a TV stand, a rug and a dog bed. A border collie is small in the frame, occupying less than one tenth of the image. At the start of the clip the sofa is completely undamaged. The dog lies on the floor right next to the sofa armrest, chewing a frayed rope scrap that lies on the floor, tugging it with its teeth. It never bites the sofa. The sofa itself stays completely intact for the whole clip: its fabric is never bitten, torn or pulled, and no stuffing comes out of the sofa. The camera never zooms in, pans or follows the dog. Wide establishing shot, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## H06 · close · Category B · small toy the same color as the sofa

```text
A photorealistic CCTV-style video of a French bulldog in a minimalist living room during bright daytime, seen from a fixed indoor camera facing a light gray fabric sofa. The sofa fills most of the frame. At the start of the clip the sofa is completely undamaged. The dog lies on the seat cushion chewing a small light gray rubber toy, almost the same color as the sofa, held between its paws. Only the toy is in its mouth; its teeth never touch the cushion. The sofa itself stays completely intact for the whole clip: its fabric is never bitten, torn or pulled, and no stuffing comes out of the sofa. The camera never zooms in, pans or follows the dog. Close CCTV view of the sofa, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## H07 · medium · Category B · bone on sofa cushion

```text
A photorealistic CCTV-style video of a mid-century living room in the late morning with strong sunlight across the sofa, recorded by a fixed security camera in a high corner. The frame shows the whole brown leather sofa and part of the room around it. A chocolate Labrador retriever occupies about one tenth of the image. At the start of the clip the sofa is completely undamaged. The dog lies on the sofa with its head down on the seat cushion, gnawing a large chew bone held between its paws for the whole clip. Only the bone is in its mouth. The sofa itself stays completely intact for the whole clip: its fabric is never bitten, torn or pulled, and no stuffing comes out of the sofa. The camera never zooms in, pans or follows the dog. Medium-wide shot, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## H08 · medium · Category B · rope toy on sofa armrest

```text
A photorealistic CCTV-style video of a living room at night, recorded in black-and-white infrared night-vision mode by a fixed fisheye home security camera with a dark circular vignette on the wall opposite the sofa. The frame shows the whole fabric sofa with cushions. A Siberian husky occupies about one tenth of the image. At the start of the clip the sofa is completely undamaged. The dog lies on the sofa with its chin resting on the armrest, chewing and tugging a rope toy draped over the armrest. Only the rope toy is in its mouth; the armrest fabric is never bitten. The sofa itself stays completely intact for the whole clip: its fabric is never bitten, torn or pulled, and no stuffing comes out of the sofa. The camera never zooms in, pans or follows the dog. Medium-wide shot, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic infrared night-vision footage, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## H09 · wide · Category B · toy on sofa, dog small in frame

```text
A photorealistic CCTV-style video of an entire open-plan living room on an overcast afternoon, seen from a fixed wide-angle camera on a high shelf. Everything is visible at once: a gray sectional sofa, a dining table, a kitchen counter, a rug and a TV. A Shiba Inu is small in the frame, occupying less than one twentieth of the image. At the start of the clip the sofa is completely undamaged. The dog lies on the sofa chaise chewing a red rubber chew toy held between its paws for the whole clip. Only the toy is in its mouth; it never bites the sofa. The sofa itself stays completely intact for the whole clip: its fabric is never bitten, torn or pulled, and no stuffing comes out of the sofa. The camera never zooms in, pans or follows the dog. Wide establishing shot, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## H10 · wide · Category B · plush toy on sofa, shaking it

```text
A photorealistic CCTV-style video of an entire family living room during bright daytime, seen from a fixed security camera mounted high on the wall. The whole room is visible: a blue fabric sofa with throw pillows, a coffee table, a toy chest, a rug and a doorway. A Jack Russell terrier occupies about one tenth of the image. At the start of the clip the sofa is completely undamaged. The dog stands on the sofa shaking a small plush toy in its mouth from side to side, then lies down on the seat and keeps chewing the toy. The throw pillows are never touched and the sofa is never bitten. The sofa itself stays completely intact for the whole clip: its fabric is never bitten, torn or pulled, and no stuffing comes out of the sofa. The camera never zooms in, pans or follows the dog. Wide establishing shot, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```
