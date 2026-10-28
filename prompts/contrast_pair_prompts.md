# MischiefCam · Contrast-pair prompts (P01–P10, two clips a/b per pair)

**Each scene is generated twice**: `a` is the dog biting the sofa itself (positive); `b` looks similar but the dog is not biting the sofa (negative).
This teaches the model the real difference between "a dog chewing something near or on the sofa" and "a dog biting the sofa".

- Save the clips as `P01a.mp4`, `P01b.mp4` … `P10b.mp4` (IDs only, so labelling stays blind) in `data/Pairs-Videos/`.
- **Ideally generate a and b of a pair from the same start image (image-to-video) or the same seed**, so the two clips differ only in the action and the contrast is cleanest.
- When evaluating, keep a and b of a pair on the same side (train or test), because they are the same scene.

| Pair | View | Targeted false alarm | a (positive) bites | b (negative) |
|---|---|---|---|---|
| P01 | close | toy on sofa vs biting the cushion | seat cushion edge | bone on the cushion |
| P02 | close | long sniffing vs biting the armrest | armrest | sofa (sniffing only) |
| P03 | close | towel on the floor vs biting the sofa skirt | sofa bottom edge | towel on the floor |
| P04 | close | licking vs biting the armrest | armrest | sofa (licking only) |
| P05 | medium | plush toy stuffing on the floor vs sofa stuffing | seat cushion | plush toy on the floor |
| P06 | medium (night vision) | rope over the armrest vs biting the armrest (night) | armrest | rope toy on the armrest |
| P07 | medium | bone on leather sofa vs biting the leather | leather seat cushion | bone on the sofa |
| P08 | medium | throw pillow vs plush toy on the sofa | throw pillow on the sofa | plush toy on the sofa |
| P09 | wide | toy on the chaise vs biting the chaise (dog small) | chaise corner | toy on the chaise |
| P10 | wide (night vision) | rug corner vs sofa skirt at night (dog small) | sofa bottom edge | rug corner |

## P01a · positive · close · seat cushion edge

```text
A photorealistic CCTV-style video of a black Labrador retriever in a cozy living room in the early evening under warm lamp light, seen from a fixed indoor camera facing a gray tufted fabric sofa. The dog lies on the seat cushion with a white chew bone between its front paws. At the start of the clip the sofa is completely undamaged and there is no stuffing anywhere. The dog pushes the bone aside, grips the front edge of the seat cushion with its teeth and chews and tugs at the fabric, shaking its head. The fabric becomes frayed and a little stuffing appears. The camera never zooms in, pans or follows the dog. Close CCTV view of the sofa, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## P01b · negative · close · bone on the cushion

```text
A photorealistic CCTV-style video of a black Labrador retriever in a cozy living room in the early evening under warm lamp light, seen from a fixed indoor camera facing a gray tufted fabric sofa. The dog lies on the seat cushion with a white chew bone between its front paws. At the start of the clip the sofa is completely undamaged and there is no stuffing anywhere. The dog chews the white bone held between its paws for the whole clip. Only the bone is ever in its mouth; its teeth never touch the cushion. The sofa itself stays completely intact for the whole clip: its fabric is never bitten, torn or pulled, and no stuffing comes out of the sofa. The camera never zooms in, pans or follows the dog. Close CCTV view of the sofa, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## P02a · positive · close · armrest

```text
A photorealistic CCTV-style video of a Jack Russell terrier in a bright living room with a brick wall during daytime, seen from a fixed indoor camera low on a shelf facing a mustard yellow two-seat sofa. The dog walks up to the sofa armrest. At the start of the clip the sofa is completely undamaged and there is no stuffing anywhere. The dog sniffs the armrest briefly, then opens its mouth, bites into the armrest fabric and chews and pulls it for several seconds. The fabric becomes visibly frayed. The camera never zooms in, pans or follows the dog. Close CCTV view of the sofa, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## P02b · negative · close · sofa (sniffing only)

```text
A photorealistic CCTV-style video of a Jack Russell terrier in a bright living room with a brick wall during daytime, seen from a fixed indoor camera low on a shelf facing a mustard yellow two-seat sofa. The dog walks up to the sofa armrest. At the start of the clip the sofa is completely undamaged and there is no stuffing anywhere. The dog sniffs slowly along the armrest and the seat cushion for several seconds with its nose close to the fabric and its mouth closed, then walks away. The sofa itself stays completely intact for the whole clip: its fabric is never bitten, torn or pulled, and no stuffing comes out of the sofa. The camera never zooms in, pans or follows the dog. Close CCTV view of the sofa, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## P03a · positive · close · sofa bottom edge

```text
A photorealistic CCTV-style video of a golden retriever in a bright living room during daytime, seen from a fixed fisheye home security camera with a dark circular vignette facing a gray sectional sofa. The dog lies on the rug directly in front of the sofa next to an old gray towel. At the start of the clip the sofa is completely undamaged and there is no stuffing anywhere. The dog ignores the towel, turns its head to the sofa and bites and tugs the fabric at the bottom front edge of the sofa. The fabric tears and a small amount of stuffing appears. The camera never zooms in, pans or follows the dog. Close CCTV view of the sofa, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## P03b · negative · close · towel on the floor

```text
A photorealistic CCTV-style video of a golden retriever in a bright living room during daytime, seen from a fixed fisheye home security camera with a dark circular vignette facing a gray sectional sofa. The dog lies on the rug directly in front of the sofa next to an old gray towel. At the start of the clip the sofa is completely undamaged and there is no stuffing anywhere. The dog chews and tugs the old gray towel lying on the rug for the whole clip. The towel stays on the floor; the dog's mouth never touches the sofa. The sofa itself stays completely intact for the whole clip: its fabric is never bitten, torn or pulled, and no stuffing comes out of the sofa. The camera never zooms in, pans or follows the dog. Close CCTV view of the sofa, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## P04a · positive · close · armrest

```text
A photorealistic CCTV-style video of a white standard poodle in a minimalist living room during bright daytime, seen from a fixed indoor camera facing a light beige linen sofa. The dog stands with its front paws on the floor and its head at the armrest. At the start of the clip the sofa is completely undamaged and there is no stuffing anywhere. The dog bites the armrest and chews it repeatedly, pulling at the linen with its teeth. The fabric frays and a little stuffing appears. The camera never zooms in, pans or follows the dog. Close CCTV view of the sofa, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## P04b · negative · close · sofa (licking only)

```text
A photorealistic CCTV-style video of a white standard poodle in a minimalist living room during bright daytime, seen from a fixed indoor camera facing a light beige linen sofa. The dog stands with its front paws on the floor and its head at the armrest. At the start of the clip the sofa is completely undamaged and there is no stuffing anywhere. The dog licks the armrest a few times with its tongue, without opening its jaws to bite or pull, then sits down on the floor. The sofa itself stays completely intact for the whole clip: its fabric is never bitten, torn or pulled, and no stuffing comes out of the sofa. The camera never zooms in, pans or follows the dog. Close CCTV view of the sofa, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## P05a · positive · medium · seat cushion

```text
A photorealistic CCTV-style video of a beagle in a family living room on an overcast afternoon, recorded by a fixed security camera mounted high in a corner. The frame shows the whole beige fabric sofa and the rug in front of it. A plush toy lies on the rug. The dog occupies about one tenth of the image. At the start of the clip the sofa is completely undamaged and there is no stuffing anywhere. The dog ignores the plush toy, climbs onto the sofa and bites into a seat cushion, tearing it so that white stuffing comes out of the sofa onto the cushion. The camera never zooms in, pans or follows the dog. Medium-wide shot, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## P05b · negative · medium · plush toy on the floor

```text
A photorealistic CCTV-style video of a beagle in a family living room on an overcast afternoon, recorded by a fixed security camera mounted high in a corner. The frame shows the whole beige fabric sofa and the rug in front of it. A plush toy lies on the rug. The dog occupies about one tenth of the image. At the start of the clip the sofa is completely undamaged and there is no stuffing anywhere. The dog lies on the rug and chews the plush toy until white filling comes out of the toy and scatters on the rug. The filling comes only from the toy; the sofa is never touched. The sofa itself stays completely intact for the whole clip: its fabric is never bitten, torn or pulled, and no stuffing comes out of the sofa. The camera never zooms in, pans or follows the dog. Medium-wide shot, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## P06a · positive · medium · armrest

```text
A photorealistic CCTV-style video of a Siberian husky in a living room at night, recorded in black-and-white infrared night-vision mode by a fixed fisheye home security camera with a dark circular vignette. The frame shows the whole fabric sofa. A rope toy is draped over the left armrest and the dog lies on the sofa with its head at that armrest. The dog occupies about one tenth of the image. At the start of the clip the sofa is completely undamaged and there is no stuffing anywhere. The dog lets go of the rope and bites the armrest fabric itself, chewing and tugging it. The fabric frays and stuffing appears. The camera never zooms in, pans or follows the dog. Medium-wide shot, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic infrared night-vision footage, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## P06b · negative · medium · rope toy on the armrest

```text
A photorealistic CCTV-style video of a Siberian husky in a living room at night, recorded in black-and-white infrared night-vision mode by a fixed fisheye home security camera with a dark circular vignette. The frame shows the whole fabric sofa. A rope toy is draped over the left armrest and the dog lies on the sofa with its head at that armrest. The dog occupies about one tenth of the image. At the start of the clip the sofa is completely undamaged and there is no stuffing anywhere. The dog chews and tugs the rope toy draped over the armrest for the whole clip. Only the rope is in its mouth; the armrest fabric is never bitten. The sofa itself stays completely intact for the whole clip: its fabric is never bitten, torn or pulled, and no stuffing comes out of the sofa. The camera never zooms in, pans or follows the dog. Medium-wide shot, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic infrared night-vision footage, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## P07a · positive · medium · leather seat cushion

```text
A photorealistic CCTV-style video of a chocolate Labrador retriever in a mid-century living room in the late morning with sunlight across the floor, recorded by a fixed security camera in a high corner. The frame shows the whole brown leather sofa. The dog lies on the sofa with a chew bone. The dog occupies about one tenth of the image. At the start of the clip the sofa is completely undamaged and there is no stuffing anywhere. The dog drops the bone and bites the leather of the seat cushion, chewing it until visible tooth marks and a small tear appear in the leather. The camera never zooms in, pans or follows the dog. Medium-wide shot, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## P07b · negative · medium · bone on the sofa

```text
A photorealistic CCTV-style video of a chocolate Labrador retriever in a mid-century living room in the late morning with sunlight across the floor, recorded by a fixed security camera in a high corner. The frame shows the whole brown leather sofa. The dog lies on the sofa with a chew bone. The dog occupies about one tenth of the image. At the start of the clip the sofa is completely undamaged and there is no stuffing anywhere. The dog gnaws the chew bone held between its paws for the whole clip. Only the bone is in its mouth; the leather is never bitten. The sofa itself stays completely intact for the whole clip: its fabric is never bitten, torn or pulled, and no stuffing comes out of the sofa. The camera never zooms in, pans or follows the dog. Medium-wide shot, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## P08a · positive · medium · throw pillow on the sofa

```text
A photorealistic CCTV-style video of a long-haired dachshund in a cozy living room in the early evening under warm lamp light, recorded by a fixed indoor camera on a bookshelf. The frame shows the whole olive green sofa with an orange throw pillow and a small brown plush toy on the seat. The dog occupies about one tenth of the image. At the start of the clip the sofa is completely undamaged and there is no stuffing anywhere. The dog grabs the orange throw pillow in its mouth and shakes and chews it on the sofa, tearing a seam so that stuffing comes out of the pillow. The camera never zooms in, pans or follows the dog. Medium-wide shot, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## P08b · negative · medium · plush toy on the sofa

```text
A photorealistic CCTV-style video of a long-haired dachshund in a cozy living room in the early evening under warm lamp light, recorded by a fixed indoor camera on a bookshelf. The frame shows the whole olive green sofa with an orange throw pillow and a small brown plush toy on the seat. The dog occupies about one tenth of the image. At the start of the clip the sofa is completely undamaged and there is no stuffing anywhere. The dog grabs the small brown plush toy in its mouth and shakes and chews it on the sofa. The orange throw pillow is never touched. The sofa itself stays completely intact for the whole clip: its fabric is never bitten, torn or pulled, and no stuffing comes out of the sofa. The camera never zooms in, pans or follows the dog. Medium-wide shot, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## P09a · positive · wide · chaise corner

```text
A photorealistic CCTV-style video of an entire open-plan living room on an overcast afternoon, seen from a fixed wide-angle camera on a high shelf. Everything is visible at once: a gray sectional sofa with a chaise, a dining table, a kitchen counter, a rug and a TV. A red Shiba Inu lies on the chaise with a red rubber toy. The dog is small in the frame, occupying less than one twentieth of the image. At the start of the clip the sofa is completely undamaged and there is no stuffing anywhere. The dog pushes the toy away and bites and tugs the corner of the chaise cushion. The fabric tears and a tuft of stuffing comes out. The camera never zooms in, pans or follows the dog. Wide establishing shot, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## P09b · negative · wide · toy on the chaise

```text
A photorealistic CCTV-style video of an entire open-plan living room on an overcast afternoon, seen from a fixed wide-angle camera on a high shelf. Everything is visible at once: a gray sectional sofa with a chaise, a dining table, a kitchen counter, a rug and a TV. A red Shiba Inu lies on the chaise with a red rubber toy. The dog is small in the frame, occupying less than one twentieth of the image. At the start of the clip the sofa is completely undamaged and there is no stuffing anywhere. The dog chews the red rubber toy held between its paws for the whole clip. Only the toy is in its mouth; the chaise is never bitten. The sofa itself stays completely intact for the whole clip: its fabric is never bitten, torn or pulled, and no stuffing comes out of the sofa. The camera never zooms in, pans or follows the dog. Wide establishing shot, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic indoor lighting, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## P10a · positive · wide · sofa bottom edge

```text
A photorealistic CCTV-style video of an entire living room at night, recorded in black-and-white infrared night-vision mode by a fixed security camera mounted high on the wall. The whole room is visible: a light fabric sofa, a coffee table, a TV stand, a rug and a doorway. A boxer lies on the floor right next to the sofa, at the corner of the rug. The dog occupies about one tenth of the image. At the start of the clip the sofa is completely undamaged and there is no stuffing anywhere. The dog bites and pulls the fabric at the bottom of the sofa, tearing it so that stuffing comes out. The camera never zooms in, pans or follows the dog. Wide establishing shot, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic infrared night-vision footage, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```

## P10b · negative · wide · rug corner

```text
A photorealistic CCTV-style video of an entire living room at night, recorded in black-and-white infrared night-vision mode by a fixed security camera mounted high on the wall. The whole room is visible: a light fabric sofa, a coffee table, a TV stand, a rug and a doorway. A boxer lies on the floor right next to the sofa, at the corner of the rug. The dog occupies about one tenth of the image. At the start of the clip the sofa is completely undamaged and there is no stuffing anywhere. The dog chews and tugs the corner of the rug next to the sofa for the whole clip. Only the rug is in its mouth; the sofa is never bitten. The sofa itself stays completely intact for the whole clip: its fabric is never bitten, torn or pulled, and no stuffing comes out of the sofa. The camera never zooms in, pans or follows the dog. Wide establishing shot, single continuous shot, no cuts, no camera movement, no zoom, realistic dog behaviour, realistic infrared night-vision footage, no humans, no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.
```
