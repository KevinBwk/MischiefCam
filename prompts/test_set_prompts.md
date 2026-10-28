# MischiefCam · Held-out test set prompts (T01–T60, 50 clips actually generated)

**This batch is for the final evaluation only: do not use it to train, pick thresholds, pick crops or tune prompts.** Run it once, after all settings are final; that score is the performance to report in the proposal. If settings change afterwards, this set is no longer clean and a new one is needed.

- Save the clips as `T01.mp4` … `T60.mp4` in `data/Test-Videos/` (IDs only).
- **Reduced to 50 clips on 2026-10-24**: the 10 rows marked "not generated" below are skipped. In each "view × type" cell, the scenario most similar to an already generated clip was omitted, so the positive/negative, hard-negative and view proportions match the original 60.
- There are also 5 damaged-sofa negatives in `test_damaged_sofa_prompts.md` (D01–D05), saved in `data/Test-Videos/` as well.
- **Blind-label them yourself**: run the label tool without `--suggest`; label what actually happens on screen, not what the prompt intended.
- Dog breeds, sofas and rooms are all absent from the training prompts; camera positions and phrasing are deliberately different too, to test whether detection survives a change of style.
- Positives and negatives were shuffled before numbering, so IDs reveal nothing; the intended outcomes are only in `test_set_prompts.json`, so do not open it until labelling is done.
- Composition: 50 clips in total: 19 close, 18 medium, 13 wide.
- If you have real footage (your own or a teammate's dog), save it as `R01.mp4` … in the same folder and blind-label it together.
  Real footage best answers the question the judges will ask: does a model trained on synthetic data work in the real world?

| ID | View | Status |
|---|---|---|
| T01 | medium | generated |
| T02 | wide | generated |
| T03 | medium | generated |
| T04 | medium | generated |
| T05 | wide | generated |
| T06 | close | generated |
| T07 | medium | generated |
| T08 | close | generated |
| T09 | close | generated |
| T10 | close | generated |
| T11 | close | generated |
| T12 | close | generated |
| T13 | close | generated |
| T14 | wide | generated |
| T15 | wide | generated |
| T16 | medium | generated |
| T17 | medium | generated |
| T18 | medium | generated |
| T19 | close | generated |
| T20 | wide | generated |
| T21 | wide | generated |
| T22 | medium | generated |
| T23 | wide | generated |
| T24 | close | generated |
| T25 | wide | generated |
| T26 | close | generated |
| T27 | medium | generated |
| T28 | close | generated |
| T29 | medium | generated |
| T30 | medium | generated |
| T31 | close | **not generated** |
| T32 | medium | generated |
| T33 | medium | **not generated** |
| T34 | medium | **not generated** |
| T35 | close | generated |
| T36 | wide | **not generated** |
| T37 | close | **not generated** |
| T38 | medium | generated |
| T39 | close | generated |
| T40 | close | generated |
| T41 | close | generated |
| T42 | wide | **not generated** |
| T43 | close | **not generated** |
| T44 | medium | generated |
| T45 | wide | generated |
| T46 | close | generated |
| T47 | wide | generated |
| T48 | medium | **not generated** |
| T49 | close | **not generated** |
| T50 | wide | generated |
| T51 | medium | generated |
| T52 | medium | generated |
| T53 | wide | **not generated** |
| T54 | close | generated |
| T55 | medium | generated |
| T56 | close | generated |
| T57 | wide | generated |
| T58 | close | generated |
| T59 | wide | generated |
| T60 | medium | generated |

## T01 · medium

```text
Home security footage, late-morning sunlight with hard shadows and glare on the floor. Recorded by a camera on a windowsill looking across at the sofa from the side. The room is a cluttered student apartment with a blue-and-white striped canvas sofa. A black-and-rust Doberman pulls a toy out from between two seat cushions with its teeth, without biting the cushions. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. The view is locked off for the whole clip: one continuous take, no camera motion, no zoom. Realistic animal motion, realistic lighting, no people, no on-screen text.
```

## T02 · wide

```text
Static wide shot from a fisheye camera in the room's corner near the ceiling, the dog small in the frame in a Japanese-style room with tatami mats, black-and-white infrared night vision. In the frame is an emerald green velvet Chesterfield sofa. During the clip a gray greyhound lies on the sofa and chews the backrest, tufts of stuffing visible. At the start of the clip the sofa looks undamaged. Nothing else moves the camera: no pan, no zoom, no cuts. Looks like real footage from a home camera, with no people and no captions or overlays.
```

## T03 · medium

```text
A real-looking clip from a pet-monitoring camera (a camera on a windowsill looking across at the sofa from the side). Setting: high-rise apartment with a city view, mixed warm lamp light and cool TV glow, with a dusty pink velvet loveseat. What happens: a fluffy white Bichon frise chews the side of the sofa near the floor, small pieces of fabric falling down. At the start of the clip the sofa looks undamaged. Single uninterrupted shot, fixed framing, no zoom, natural dog behaviour, no humans, no text, not stylised or cinematic.
```

## T04 · medium

```text
Flat overcast daylight. A coastal beach house living room seen through a camera on a windowsill looking across at the sofa from the side. A floral-patterned fabric sofa is in view, and a red-and-white Akita carries a plush toy across the sofa and drops it on the seat. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. The footage is one fixed, continuous shot with ordinary home-camera image quality: no camera movement, no zoom, no people, no subtitles, no animation look.
```

## T05 · wide

```text
Home security footage, strong backlight from a window behind the sofa. Recorded by a fisheye camera in the room's corner near the ceiling, the dog small in the frame. The room is a playroom with a colorful foam floor mat with a rattan-frame sofa with cream cushions. A harlequin Great Dane trots around the room and lies down on the rug far from the sofa. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. The view is locked off for the whole clip: one continuous take, no camera motion, no zoom. Realistic animal motion, realistic lighting, no people, no on-screen text.
```

## T06 · close

```text
Static close-up shot from a tabletop pet camera on the coffee table facing the sofa in a farmhouse living room with exposed beams, dim blue dusk light from the window. In the frame is a white leather modular sofa. During the clip a black Newfoundland puppy chews the zipper and the cover of a seat cushion until the cover rips. At the start of the clip the sofa looks undamaged. Nothing else moves the camera: no pan, no zoom, no cuts. Looks like real footage from a home camera, with no people and no captions or overlays.
```

## T07 · medium

```text
A real-looking clip from a pet-monitoring camera (a camera on a windowsill looking across at the sofa from the side). Setting: open-plan kitchen and living area, late-morning sunlight with hard shadows and glare on the floor, with a denim-blue fabric sofa. What happens: a Dalmatian bites a seat cushion and shakes its head, white stuffing spreading on the seat. At the start of the clip the sofa looks undamaged. Single uninterrupted shot, fixed framing, no zoom, natural dog behaviour, no humans, no text, not stylised or cinematic.
```

## T08 · close

```text
Black-and-white infrared night vision. A sunroom full of plants seen through a tabletop pet camera on the coffee table facing the sofa. A sage green slipcovered sofa is in view, and a white Samoyed naps curled up on the seat cushion, breathing slowly. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. The footage is one fixed, continuous shot with ordinary home-camera image quality: no camera movement, no zoom, no people, no subtitles, no animation look.
```

## T09 · close

```text
Home security footage, mixed warm lamp light and cool TV glow. Recorded by a small camera clipped to a bookshelf right next to the sofa, angled slightly down. The room is a basement den with wood-paneled walls with a low Japanese-style floor sofa in oatmeal fabric. A Boston terrier pants with its mouth open, head resting on the armrest. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. The view is locked off for the whole clip: one continuous take, no camera motion, no zoom. Realistic animal motion, realistic lighting, no people, no on-screen text.
```

## T10 · close

```text
Static close-up shot from a small camera clipped to a bookshelf right next to the sofa, angled slightly down in an industrial loft with concrete walls, flat overcast daylight. In the frame is a tan suede sofa. During the clip a brindle Cane Corso rests its chin on the armrest and watches the room, blinking. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. Nothing else moves the camera: no pan, no zoom, no cuts. Looks like real footage from a home camera, with no people and no captions or overlays.
```

## T11 · close

```text
A real-looking clip from a pet-monitoring camera (a tabletop pet camera on the coffee table facing the sofa). Setting: cluttered student apartment, strong backlight from a window behind the sofa, with a burgundy velvet sofa. What happens: an orange Pomeranian licks the seat cushion fabric with its tongue but never bites it. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. Single uninterrupted shot, fixed framing, no zoom, natural dog behaviour, no humans, no text, not stylised or cinematic.
```

## T12 · close

```text
Dim blue dusk light from the window. A Japanese-style room with tatami mats seen through a tabletop pet camera on the coffee table facing the sofa. A terracotta linen sofa is in view, and a Belgian Malinois chews a bully stick held between its paws on the seat cushion. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. The footage is one fixed, continuous shot with ordinary home-camera image quality: no camera movement, no zoom, no people, no subtitles, no animation look.
```

## T13 · close

```text
Home security footage, late-morning sunlight with hard shadows and glare on the floor. Recorded by a small camera clipped to a bookshelf right next to the sofa, angled slightly down. The room is a high-rise apartment with a city view with a blue-and-white striped canvas sofa. An Airedale terrier rolls onto its back on the sofa and wiggles, mouth closed. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. The view is locked off for the whole clip: one continuous take, no camera motion, no zoom. Realistic animal motion, realistic lighting, no people, no on-screen text.
```

## T14 · wide

```text
Static wide shot from a wide-angle camera above the doorway showing the entire room, the sofa in the far half in a coastal beach house living room, black-and-white infrared night vision. In the frame is an emerald green velvet Chesterfield sofa. During the clip a sable Shetland sheepdog walks into the room, sniffs the air, and leaves without touching the sofa. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. Nothing else moves the camera: no pan, no zoom, no cuts. Looks like real footage from a home camera, with no people and no captions or overlays.
```

## T15 · wide

```text
A real-looking clip from a pet-monitoring camera (a fisheye camera in the room's corner near the ceiling, the dog small in the frame). Setting: playroom with a colorful foam floor mat, mixed warm lamp light and cool TV glow, with a dusty pink velvet loveseat. What happens: a blue-gray pit bull terrier chews a slipper on the rug in the middle of the room. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. Single uninterrupted shot, fixed framing, no zoom, natural dog behaviour, no humans, no text, not stylised or cinematic.
```

## T16 · medium

```text
Flat overcast daylight. A farmhouse living room with exposed beams seen through a wall-mounted camera at shoulder height, framing the sofa and the rug in front of it. A floral-patterned fabric sofa is in view, and a golden cocker spaniel jumps onto the sofa, grabs the armrest in its mouth and tugs hard. At the start of the clip the sofa looks undamaged. The footage is one fixed, continuous shot with ordinary home-camera image quality: no camera movement, no zoom, no people, no subtitles, no animation look.
```

## T17 · medium

```text
Home security footage, strong backlight from a window behind the sofa. Recorded by a camera on a windowsill looking across at the sofa from the side. The room is an open-plan kitchen and living area with a rattan-frame sofa with cream cushions. A fawn whippet tugs a rope toy tied to the sofa leg, pulling only the rope. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. The view is locked off for the whole clip: one continuous take, no camera motion, no zoom. Realistic animal motion, realistic lighting, no people, no on-screen text.
```

## T18 · medium

```text
Static medium shot from a camera on a windowsill looking across at the sofa from the side in a sunroom full of plants, dim blue dusk light from the window. In the frame is a white leather modular sofa. During the clip a white-and-brown English bulldog sits on the sofa looking out of the window. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. Nothing else moves the camera: no pan, no zoom, no cuts. Looks like real footage from a home camera, with no people and no captions or overlays.
```

## T19 · close

```text
A real-looking clip from a pet-monitoring camera (a small camera clipped to a bookshelf right next to the sofa, angled slightly down). Setting: basement den with wood-paneled walls, late-morning sunlight with hard shadows and glare on the floor, with a denim-blue fabric sofa. What happens: a Saint Bernard puppy chews the piping along the front edge of the seat cushion. At the start of the clip the sofa looks undamaged. Single uninterrupted shot, fixed framing, no zoom, natural dog behaviour, no humans, no text, not stylised or cinematic.
```

## T20 · wide

```text
Black-and-white infrared night vision. An industrial loft with concrete walls seen through a fisheye camera in the room's corner near the ceiling, the dog small in the frame. A sage green slipcovered sofa is in view, and a Cavalier King Charles spaniel rips a stuffed toy on the floor near the sofa, white filling on the rug. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. The footage is one fixed, continuous shot with ordinary home-camera image quality: no camera movement, no zoom, no people, no subtitles, no animation look.
```

## T21 · wide

```text
Home security footage, mixed warm lamp light and cool TV glow. Recorded by a fisheye camera in the room's corner near the ceiling, the dog small in the frame. The room is a cluttered student apartment with a low Japanese-style floor sofa in oatmeal fabric. A basset hound pulls the sofa skirt with its teeth from the floor side. At the start of the clip the sofa looks undamaged. The view is locked off for the whole clip: one continuous take, no camera motion, no zoom. Realistic animal motion, realistic lighting, no people, no on-screen text.
```

## T22 · medium

```text
Static medium shot from a wall-mounted camera at shoulder height, framing the sofa and the rug in front of it in a Japanese-style room with tatami mats, flat overcast daylight. In the frame is a tan suede sofa. During the clip a salt-and-pepper miniature schnauzer jumps onto the sofa, turns around twice and lies down. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. Nothing else moves the camera: no pan, no zoom, no cuts. Looks like real footage from a home camera, with no people and no captions or overlays.
```

## T23 · wide

```text
A real-looking clip from a pet-monitoring camera (a ceiling-corner security camera with a high, steep angle over the whole room). Setting: high-rise apartment with a city view, strong backlight from a window behind the sofa, with a burgundy velvet sofa. What happens: a tan short-haired chihuahua after napping on the rug, gets up and chews the sofa's front edge. At the start of the clip the sofa looks undamaged. Single uninterrupted shot, fixed framing, no zoom, natural dog behaviour, no humans, no text, not stylised or cinematic.
```

## T24 · close

```text
Dim blue dusk light from the window. A coastal beach house living room seen through a pet camera placed low on the floor about one meter from the sofa. A terracotta linen sofa is in view, and a rust-colored Vizsla finds a loose thread on the seat cushion seam and gnaws and tugs it until the seam opens. At the start of the clip the sofa looks undamaged. The footage is one fixed, continuous shot with ordinary home-camera image quality: no camera movement, no zoom, no people, no subtitles, no animation look.
```

## T25 · wide

```text
Home security footage, late-morning sunlight with hard shadows and glare on the floor. Recorded by a fisheye camera in the room's corner near the ceiling, the dog small in the frame. The room is a playroom with a colorful foam floor mat with a blue-and-white striped canvas sofa. A black-and-rust Doberman chews a chew toy on the sofa seat, small in the frame. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. The view is locked off for the whole clip: one continuous take, no camera motion, no zoom. Realistic animal motion, realistic lighting, no people, no on-screen text.
```

## T26 · close

```text
Static close-up shot from a pet camera placed low on the floor about one meter from the sofa in a farmhouse living room with exposed beams, black-and-white infrared night vision. In the frame is an emerald green velvet Chesterfield sofa. During the clip a gray greyhound yawns widely while lying on the armrest, then lays its head down. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. Nothing else moves the camera: no pan, no zoom, no cuts. Looks like real footage from a home camera, with no people and no captions or overlays.
```

## T27 · medium

```text
A real-looking clip from a pet-monitoring camera (a wall-mounted camera at shoulder height, framing the sofa and the rug in front of it). Setting: open-plan kitchen and living area, mixed warm lamp light and cool TV glow, with a dusty pink velvet loveseat. What happens: a fluffy white Bichon frise scratches its own ear with a hind leg while sitting on the sofa. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. Single uninterrupted shot, fixed framing, no zoom, natural dog behaviour, no humans, no text, not stylised or cinematic.
```

## T28 · close

```text
Flat overcast daylight. A sunroom full of plants seen through a tabletop pet camera on the coffee table facing the sofa. A floral-patterned fabric sofa is in view, and a red-and-white Akita nibbles and tears the skirt along the bottom of the sofa while lying on the floor. At the start of the clip the sofa looks undamaged. The footage is one fixed, continuous shot with ordinary home-camera image quality: no camera movement, no zoom, no people, no subtitles, no animation look.
```

## T29 · medium

```text
Home security footage, strong backlight from a window behind the sofa. Recorded by a wall-mounted camera at shoulder height, framing the sofa and the rug in front of it. The room is a basement den with wood-paneled walls with a rattan-frame sofa with cream cushions. A harlequin Great Dane licks its own leg while sitting on the sofa. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. The view is locked off for the whole clip: one continuous take, no camera motion, no zoom. Realistic animal motion, realistic lighting, no people, no on-screen text.
```

## T30 · medium

```text
Static medium shot from a wall-mounted camera at shoulder height, framing the sofa and the rug in front of it in an industrial loft with concrete walls, dim blue dusk light from the window. In the frame is a white leather modular sofa. During the clip a black Newfoundland puppy chews a sneaker on the floor right next to the sofa. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. Nothing else moves the camera: no pan, no zoom, no cuts. Looks like real footage from a home camera, with no people and no captions or overlays.
```

## T31 · close (not generated)

```text
A real-looking clip from a pet-monitoring camera (a pet camera placed low on the floor about one meter from the sofa). Setting: cluttered student apartment, late-morning sunlight with hard shadows and glare on the floor, with a denim-blue fabric sofa. What happens: a Dalmatian gnaws an antler chew on the armrest, the armrest itself untouched. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. Single uninterrupted shot, fixed framing, no zoom, natural dog behaviour, no humans, no text, not stylised or cinematic.
```

## T32 · medium

```text
Black-and-white infrared night vision. A Japanese-style room with tatami mats seen through a camera on a windowsill looking across at the sofa from the side. A sage green slipcovered sofa is in view, and a white Samoyed grooms another dog lying next to it on the sofa, licking its fur. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. The footage is one fixed, continuous shot with ordinary home-camera image quality: no camera movement, no zoom, no people, no subtitles, no animation look.
```

## T33 · medium (not generated)

```text
Home security footage, mixed warm lamp light and cool TV glow. Recorded by a camera on the TV stand across the room, showing the whole sofa and some floor around it. The room is a high-rise apartment with a city view with a low Japanese-style floor sofa in oatmeal fabric. A Boston terrier walks past the sofa, drinks from a water bowl nearby and leaves. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. The view is locked off for the whole clip: one continuous take, no camera motion, no zoom. Realistic animal motion, realistic lighting, no people, no on-screen text.
```

## T34 · medium (not generated)

```text
Static medium shot from a camera on the TV stand across the room, showing the whole sofa and some floor around it in a coastal beach house living room, flat overcast daylight. In the frame is a tan suede sofa. During the clip a brindle Cane Corso bites the sofa skirt and backs away, stretching the fabric. At the start of the clip the sofa looks undamaged. Nothing else moves the camera: no pan, no zoom, no cuts. Looks like real footage from a home camera, with no people and no captions or overlays.
```

## T35 · close

```text
A real-looking clip from a pet-monitoring camera (a tabletop pet camera on the coffee table facing the sofa). Setting: playroom with a colorful foam floor mat, strong backlight from a window behind the sofa, with a burgundy velvet sofa. What happens: an orange Pomeranian after sniffing the armrest for a few seconds, starts biting it and pulls the fabric loose. At the start of the clip the sofa looks undamaged. Single uninterrupted shot, fixed framing, no zoom, natural dog behaviour, no humans, no text, not stylised or cinematic.
```

## T36 · wide (not generated)

```text
Dim blue dusk light from the window. A farmhouse living room with exposed beams seen through a wide-angle camera above the doorway showing the entire room, the sofa in the far half. A terracotta linen sofa is in view, and a Belgian Malinois plays fetch alone with a bouncing ball across the floor. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. The footage is one fixed, continuous shot with ordinary home-camera image quality: no camera movement, no zoom, no people, no subtitles, no animation look.
```

## T37 · close (not generated)

```text
Home security footage, late-morning sunlight with hard shadows and glare on the floor. Recorded by a tabletop pet camera on the coffee table facing the sofa. The room is an open-plan kitchen and living area with a blue-and-white striped canvas sofa. An Airedale terrier lies on the seat and slowly chews the edge of the cushion it is lying on. At the start of the clip the sofa looks undamaged. The view is locked off for the whole clip: one continuous take, no camera motion, no zoom. Realistic animal motion, realistic lighting, no people, no on-screen text.
```

## T38 · medium

```text
Static medium shot from a camera on a windowsill looking across at the sofa from the side in a sunroom full of plants, black-and-white infrared night vision. In the frame is an emerald green velvet Chesterfield sofa. During the clip a sable Shetland sheepdog chews a blanket that is draped over the sofa, the sofa underneath untouched. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. Nothing else moves the camera: no pan, no zoom, no cuts. Looks like real footage from a home camera, with no people and no captions or overlays.
```

## T39 · close

```text
A real-looking clip from a pet-monitoring camera (a small camera clipped to a bookshelf right next to the sofa, angled slightly down). Setting: basement den with wood-paneled walls, mixed warm lamp light and cool TV glow, with a dusty pink velvet loveseat. What happens: a blue-gray pit bull terrier stands with front paws on the seat and bites into the backrest fabric, pulling out stuffing. At the start of the clip the sofa looks undamaged. Single uninterrupted shot, fixed framing, no zoom, natural dog behaviour, no humans, no text, not stylised or cinematic.
```

## T40 · close

```text
Flat overcast daylight. An industrial loft with concrete walls seen through a tabletop pet camera on the coffee table facing the sofa. A floral-patterned fabric sofa is in view, and a golden cocker spaniel chews a tan rope toy that is almost the same color as the sofa, on the seat. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. The footage is one fixed, continuous shot with ordinary home-camera image quality: no camera movement, no zoom, no people, no subtitles, no animation look.
```

## T41 · close

```text
Home security footage, strong backlight from a window behind the sofa. Recorded by a tabletop pet camera on the coffee table facing the sofa. The room is a cluttered student apartment with a rattan-frame sofa with cream cushions. A fawn whippet chews its own front paw while lying on the sofa. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. The view is locked off for the whole clip: one continuous take, no camera motion, no zoom. Realistic animal motion, realistic lighting, no people, no on-screen text.
```

## T42 · wide (not generated)

```text
Static wide shot from a fisheye camera in the room's corner near the ceiling, the dog small in the frame in a Japanese-style room with tatami mats, dim blue dusk light from the window. In the frame is a white leather modular sofa. During the clip a white-and-brown English bulldog chews the corner of the seat cushion while the rest of the room stays still. At the start of the clip the sofa looks undamaged. Nothing else moves the camera: no pan, no zoom, no cuts. Looks like real footage from a home camera, with no people and no captions or overlays.
```

## T43 · close (not generated)

```text
A real-looking clip from a pet-monitoring camera (a pet camera placed low on the floor about one meter from the sofa). Setting: high-rise apartment with a city view, late-morning sunlight with hard shadows and glare on the floor, with a denim-blue fabric sofa. What happens: a Saint Bernard puppy sneezes and shakes its head while sitting on the seat cushion. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. Single uninterrupted shot, fixed framing, no zoom, natural dog behaviour, no humans, no text, not stylised or cinematic.
```

## T44 · medium

```text
Black-and-white infrared night vision. A coastal beach house living room seen through a camera on a windowsill looking across at the sofa from the side. A sage green slipcovered sofa is in view, and a Cavalier King Charles spaniel pulls a back cushion onto the floor with its teeth and keeps biting it. At the start of the clip the sofa looks undamaged. The footage is one fixed, continuous shot with ordinary home-camera image quality: no camera movement, no zoom, no people, no subtitles, no animation look.
```

## T45 · wide

```text
Home security footage, mixed warm lamp light and cool TV glow. Recorded by a ceiling-corner security camera with a high, steep angle over the whole room. The room is a playroom with a colorful foam floor mat with a low Japanese-style floor sofa in oatmeal fabric. A basset hound noses under the sofa looking for a ball, mouth never on the sofa. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. The view is locked off for the whole clip: one continuous take, no camera motion, no zoom. Realistic animal motion, realistic lighting, no people, no on-screen text.
```

## T46 · close

```text
Static close-up shot from a tabletop pet camera on the coffee table facing the sofa in a farmhouse living room with exposed beams, flat overcast daylight. In the frame is a tan suede sofa. During the clip a salt-and-pepper miniature schnauzer at an existing small worn spot on the seat, bites and widens the hole, pulling out stuffing. Nothing else moves the camera: no pan, no zoom, no cuts. Looks like real footage from a home camera, with no people and no captions or overlays.
```

## T47 · wide

```text
A real-looking clip from a pet-monitoring camera (a wide-angle camera above the doorway showing the entire room, the sofa in the far half). Setting: open-plan kitchen and living area, strong backlight from a window behind the sofa, with a burgundy velvet sofa. What happens: a tan short-haired chihuahua sleeps on the sofa the whole time. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. Single uninterrupted shot, fixed framing, no zoom, natural dog behaviour, no humans, no text, not stylised or cinematic.
```

## T48 · medium (not generated)

```text
Dim blue dusk light from the window. A sunroom full of plants seen through a wall-mounted camera at shoulder height, framing the sofa and the rug in front of it. A terracotta linen sofa is in view, and a rust-colored Vizsla tears apart a cardboard box beside the sofa, scraps on the floor. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. The footage is one fixed, continuous shot with ordinary home-camera image quality: no camera movement, no zoom, no people, no subtitles, no animation look.
```

## T49 · close (not generated)

```text
Home security footage, late-morning sunlight with hard shadows and glare on the floor. Recorded by a tabletop pet camera on the coffee table facing the sofa. The room is a basement den with wood-paneled walls with a blue-and-white striped canvas sofa. A black-and-rust Doberman bites the corner of the armrest and pulls at the fabric, head shaking side to side. At the start of the clip the sofa looks undamaged. The view is locked off for the whole clip: one continuous take, no camera motion, no zoom. Realistic animal motion, realistic lighting, no people, no on-screen text.
```

## T50 · wide

```text
Static wide shot from a fisheye camera in the room's corner near the ceiling, the dog small in the frame in an industrial loft with concrete walls, black-and-white infrared night vision. In the frame is an emerald green velvet Chesterfield sofa. During the clip a gray greyhound two dogs wrestle playfully on the rug in front of the sofa, mouths on each other only. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. Nothing else moves the camera: no pan, no zoom, no cuts. Looks like real footage from a home camera, with no people and no captions or overlays.
```

## T51 · medium

```text
A real-looking clip from a pet-monitoring camera (a camera on the TV stand across the room, showing the whole sofa and some floor around it). Setting: cluttered student apartment, mixed warm lamp light and cool TV glow, with a dusty pink velvet loveseat. What happens: a fluffy white Bichon frise plays with a ball on the floor for a few seconds, then turns and bites the sofa armrest. At the start of the clip the sofa looks undamaged. Single uninterrupted shot, fixed framing, no zoom, natural dog behaviour, no humans, no text, not stylised or cinematic.
```

## T52 · medium

```text
Flat overcast daylight. A Japanese-style room with tatami mats seen through a camera on the TV stand across the room, showing the whole sofa and some floor around it. A floral-patterned fabric sofa is in view, and a red-and-white Akita digs at the seat with its paws and then bites and tears the cushion fabric. At the start of the clip the sofa looks undamaged. The footage is one fixed, continuous shot with ordinary home-camera image quality: no camera movement, no zoom, no people, no subtitles, no animation look.
```

## T53 · wide (not generated)

```text
Home security footage, strong backlight from a window behind the sofa. Recorded by a wide-angle camera above the doorway showing the entire room, the sofa in the far half. The room is a high-rise apartment with a city view with a rattan-frame sofa with cream cushions. A harlequin Great Dane chews a towel on the floor beside the sofa at night. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. The view is locked off for the whole clip: one continuous take, no camera motion, no zoom. Realistic animal motion, realistic lighting, no people, no on-screen text.
```

## T54 · close

```text
Static close-up shot from a pet camera placed low on the floor about one meter from the sofa in a coastal beach house living room, dim blue dusk light from the window. In the frame is a white leather modular sofa. During the clip a black Newfoundland puppy grips the top corner of a back cushion in its teeth and drags the cushion half off the sofa. At the start of the clip the sofa looks undamaged. Nothing else moves the camera: no pan, no zoom, no cuts. Looks like real footage from a home camera, with no people and no captions or overlays.
```

## T55 · medium

```text
A real-looking clip from a pet-monitoring camera (a camera on a windowsill looking across at the sofa from the side). Setting: playroom with a colorful foam floor mat, late-morning sunlight with hard shadows and glare on the floor, with a denim-blue fabric sofa. What happens: a Dalmatian chews the front corner of the seat cushion while standing on the rug. At the start of the clip the sofa looks undamaged. Single uninterrupted shot, fixed framing, no zoom, natural dog behaviour, no humans, no text, not stylised or cinematic.
```

## T56 · close

```text
Black-and-white infrared night vision. A farmhouse living room with exposed beams seen through a tabletop pet camera on the coffee table facing the sofa. A sage green slipcovered sofa is in view, and a white Samoyed holds a tennis ball in its mouth while lying with its head on the cushion. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. The footage is one fixed, continuous shot with ordinary home-camera image quality: no camera movement, no zoom, no people, no subtitles, no animation look.
```

## T57 · wide

```text
Home security footage, mixed warm lamp light and cool TV glow. Recorded by a ceiling-corner security camera with a high, steep angle over the whole room. The room is an open-plan kitchen and living area with a low Japanese-style floor sofa in oatmeal fabric. A Boston terrier walks to the sofa, bites the armrest and tugs it repeatedly. At the start of the clip the sofa looks undamaged. The view is locked off for the whole clip: one continuous take, no camera motion, no zoom. Realistic animal motion, realistic lighting, no people, no on-screen text.
```

## T58 · close

```text
Static close-up shot from a tabletop pet camera on the coffee table facing the sofa in a sunroom full of plants, flat overcast daylight. In the frame is a tan suede sofa. During the clip a brindle Cane Corso sniffs along the seat seam intensely, nose pressed into the fabric, without biting. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. Nothing else moves the camera: no pan, no zoom, no cuts. Looks like real footage from a home camera, with no people and no captions or overlays.
```

## T59 · wide

```text
A real-looking clip from a pet-monitoring camera (a wide-angle camera above the doorway showing the entire room, the sofa in the far half). Setting: basement den with wood-paneled walls, strong backlight from a window behind the sofa, with a burgundy velvet sofa. What happens: an orange Pomeranian bites a seat cushion and drags it off the sofa onto the floor. At the start of the clip the sofa looks undamaged. Single uninterrupted shot, fixed framing, no zoom, natural dog behaviour, no humans, no text, not stylised or cinematic.
```

## T60 · medium

```text
Dim blue dusk light from the window. An industrial loft with concrete walls seen through a camera on a windowsill looking across at the sofa from the side. A terracotta linen sofa is in view, and a Belgian Malinois digs and paws at the seat cushion to make a bed, mouth never touching it. Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, no loose threads, no stuffing from the sofa. The footage is one fixed, continuous shot with ordinary home-camera image quality: no camera movement, no zoom, no people, no subtitles, no animation look.
```
