# MischiefCam · Demo clip prompts

Prompts for the two synthetic clips added to the Stage I demo playlist (`demo/playlist.json`).
They are for playback only: **never used for training, tuning or evaluation**, and kept out of
the development and test sets. Clips are stored as `data/Demo-Videos/nap01.mp4` and
`data/Demo-Videos/chew08.mp4` (`data/` is not committed).

Before a clip went into the playlist it was checked for a clean frame (no text, borders or
overlays), physically plausible motion (one jump, no floating, paws on the right surfaces) and an
intact sofa in the first frame, then played with `scripts/batch_run.py --vlm either`.

Prompt lessons: describe each action once; avoid words such as "pet camera" or "security camera"
(they invite on-screen interface graphics); a negation can prime the very thing it forbids.

## NAP · dog jumps onto the sofa and settles down (Michelle stays quiet)

Replaces v20 (unnatural climb onto the sofa). Result: no alert over the whole clip.

```
A single continuous, photorealistic 8-second video showing a real dog naturally jumping onto a sofa and settling down in a bright, modern living room.

SCENE:
A light gray fabric sofa with wooden flooring in front of it. Soft afternoon daylight enters from the left. The entire sofa and surrounding floor are visible in a fixed, wide 16:9 composition.

The camera remains perfectly still throughout the video. No camera movement, zooming, cuts, or transitions.

DOG:
A medium-sized, short-haired tan dog with natural body proportions, realistic fur, and anatomically correct legs and paws. The dog's appearance remains completely consistent throughout.

ACTION:
The dog enters from the right side of the frame and walks calmly toward the sofa.

It approaches the sofa, bends its hind legs slightly, and performs one smooth, confident jump directly onto the seat cushion.

The entire jump is completed as a single fluid movement lasting approximately one second. Both front paws land first, immediately followed by both hind paws. All four paws are fully on the sofa before the dog begins its next movement.

The dog briefly adjusts its position with a couple of natural steps, then gradually lowers its body into a comfortable lying position.

Its chest settles onto the cushion, its front legs extend naturally forward, and its chin gently rests near its paws.

For the final two seconds, the dog remains relaxed and mostly still, breathing gently and blinking naturally.

MOTION AND PHYSICS:
All movements follow realistic canine biomechanics, including natural joint bending, muscle movement, weight transfer, gravity, and momentum.

The dog's paws maintain proper contact with the floor and sofa. The cushions compress subtly under its weight.

The jump must be physically believable, with no floating, sliding, prolonged balancing between the floor and sofa, or sudden changes in body position.

Natural everyday animal behavior, without exaggerated or overly choreographed movements.

VISUAL STYLE:
Authentic, unedited home video footage. Natural lighting, realistic shadows, ordinary household textures, and believable motion.

No cinematic effects, dramatic lighting, slow motion, artificial camera movement, or stylized animation.

CLEAN FRAME:
The video contains only the dog and the natural living room environment.

No visible filming equipment, tripods, cameras, or camera stands.

Absolutely no text, numbers, captions, subtitles, logos, watermarks, timestamps, recording indicators, red dots, symbols, icons, user interface elements, aspect ratio labels, borders, or graphic overlays.

Do not imitate a security camera interface or video player interface.

OUTPUT:
8 seconds, 16:9 landscape, 720p or higher, one uninterrupted continuous shot, natural motion speed.
```

## CHEW · night vision, dog chews the sofa armrest (Michelle alerts)

Replaces w04 (sofa already torn in the first frame). What made the alert reliable: the dog is at
the armrest from the first frame and bites within half a second, front paws on the armrest with
its face in profile so the mouth is visible, a medium shot where the sofa fills about half the
frame, and fabric damage (fraying, then a tear) that starts around two seconds in, with no
stuffing.

Result: alert in 5 of 5 batch runs (classifier, p = 0.538 at 4.2 s; threshold 0.534) and in 3 of 3
live playbacks (VLM, at 00:02).

```
A single continuous, photorealistic 8-second video of a real dog with its front paws up on a sofa armrest, chewing the top of the armrest at night in a dark living room.

SCENE:
A living room at night, shown in black-and-white infrared night vision: soft gray tones, slightly grainy, the dog's eyes may glow faintly. The view is from slightly above, about two meters from the side of a fabric three-seat sofa, so the near armrest is in the middle of the frame and the sofa fills about half of the frame, with the floor below and the dark room behind.

The camera remains perfectly still throughout the video. No camera movement, zooming, cuts, or transitions.

At the very start of the video the sofa is completely intact, with smooth, even fabric.

DOG:
A medium-sized short-haired dog with natural body proportions and anatomically correct legs and paws. When the video begins it is already standing on its hind legs on the floor beside the near armrest, with both front paws on top of the armrest and its body in profile to the camera, so that its face, open mouth and teeth are clearly visible from the side. The dog's appearance remains completely consistent throughout.

ACTION:
Half a second into the video, the dog bites into the top edge of the armrest, its teeth sinking into the fabric.

For the rest of the video it chews and tugs the armrest with steady, determined energy: it grips the fabric, pulls its head back so the fabric lifts and stretches, shakes its head from side to side, then bites down again. Its shoulders and body rock with each pull and its hind legs shift their footing, while its front paws stay braced on top of the armrest and its face stays turned in profile to the camera.

The damage appears early and grows steadily: by the second second the fabric on top of the armrest is visibly fuzzy and frayed with loose threads; by the fourth second a ragged tear has opened; by the end the tear is about a hand-width wide, with frayed edges and a few short threads caught in the dog's mouth.

MOTION AND PHYSICS:
All movements follow realistic canine biomechanics, with natural weight transfer and gravity. The front paws stay on top of the armrest and the hind paws stay on the floor, and the armrest fabric dents and shifts under the dog's weight as it pulls.

Natural everyday animal behavior, without exaggerated or overly choreographed movements.

VISUAL STYLE:
Authentic, unedited night-vision home footage. Realistic infrared lighting, realistic shadows, ordinary household textures, and believable motion.

CLEAN FRAME:
The video contains only the dog, the sofa and the natural living room environment. The picture is clean and fills the frame edge to edge.

Absolutely no text, numbers, captions, subtitles, logos, watermarks, timestamps, recording indicators, red dots, symbols, icons, user interface elements, borders, or graphic overlays.

OUTPUT:
8 seconds, 16:9 landscape, 720p or higher, one uninterrupted continuous shot, natural motion speed.
```
