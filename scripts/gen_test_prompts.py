"""Generate the held-out TEST set prompts (T01-T60): evaluated once, never trained or tuned on.

    uv run python scripts/gen_test_prompts.py
    # writes prompts/test_set_prompts.{md,json} and prompts/test_damaged_sofa_prompts.{md,json}

The set is deliberately shifted from every training prompt so it measures generalisation, not
memorised generator style: dog breeds, sofas and rooms that never appear in the training prompts,
other camera placements, and four sentence structures different from the training template.
Positives and negatives are shuffled before ids are assigned, so an id says nothing about its label.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261022

# Breeds, sofas and rooms below are all absent from gen_video_prompts.py and the other prompt files.
DOGS = [
    "white Samoyed", "black-and-rust Doberman", "gray greyhound", "red-and-white Akita",
    "Cavalier King Charles spaniel", "salt-and-pepper miniature schnauzer", "Dalmatian", "sable Shetland sheepdog",
    "tan short-haired chihuahua", "harlequin Great Dane", "blue-gray pit bull terrier", "fluffy white Bichon frise",
    "basset hound", "rust-colored Vizsla", "golden cocker spaniel", "Belgian Malinois",
    "black Newfoundland puppy", "orange Pomeranian", "fawn whippet", "Airedale terrier",
    "Boston terrier", "Saint Bernard puppy", "white-and-brown English bulldog", "brindle Cane Corso",
]
SOFAS = [
    "emerald green velvet Chesterfield sofa", "terracotta linen sofa", "dusty pink velvet loveseat",
    "blue-and-white striped canvas sofa", "floral-patterned fabric sofa", "rattan-frame sofa with cream cushions",
    "tan suede sofa", "white leather modular sofa", "burgundy velvet sofa", "sage green slipcovered sofa",
    "denim-blue fabric sofa", "low Japanese-style floor sofa in oatmeal fabric",
]
ROOMS = [
    "Japanese-style room with tatami mats", "basement den with wood-paneled walls", "sunroom full of plants",
    "open-plan kitchen and living area", "cluttered student apartment", "coastal beach house living room",
    "industrial loft with concrete walls", "farmhouse living room with exposed beams",
    "high-rise apartment with a city view", "playroom with a colorful foam floor mat",
]
CAMERAS = {
    "close": [
        "a pet camera placed low on the floor about one meter from the sofa",
        "a small camera clipped to a bookshelf right next to the sofa, angled slightly down",
        "a tabletop pet camera on the coffee table facing the sofa",
    ],
    "medium": [
        "a camera on the TV stand across the room, showing the whole sofa and some floor around it",
        "a wall-mounted camera at shoulder height, framing the sofa and the rug in front of it",
        "a camera on a windowsill looking across at the sofa from the side",
    ],
    "wide": [
        "a ceiling-corner security camera with a high, steep angle over the whole room",
        "a wide-angle camera above the doorway showing the entire room, the sofa in the far half",
        "a fisheye camera in the room's corner near the ceiling, the dog small in the frame",
    ],
}
LIGHTS = [
    "late-morning sunlight with hard shadows and glare on the floor", "dim blue dusk light from the window",
    "mixed warm lamp light and cool TV glow", "black-and-white infrared night vision",
    "flat overcast daylight", "strong backlight from a window behind the sofa",
]

# (view, label, what happens). Positive = the dog's mouth bites / chews / tugs the sofa itself.
POSITIVE = [
    ("close", "bites the corner of the armrest and pulls at the fabric, head shaking side to side"),
    ("close", "finds a loose thread on the seat cushion seam and gnaws and tugs it until the seam opens"),
    ("close", "chews the piping along the front edge of the seat cushion"),
    ("close", "grips the top corner of a back cushion in its teeth and drags the cushion half off the sofa"),
    ("close", "nibbles and tears the skirt along the bottom of the sofa while lying on the floor"),
    ("close", "chews the zipper and the cover of a seat cushion until the cover rips"),
    ("close", "stands with front paws on the seat and bites into the backrest fabric, pulling out stuffing"),
    ("close", "after sniffing the armrest for a few seconds, starts biting it and pulls the fabric loose"),
    ("close", "at an existing small worn spot on the seat, bites and widens the hole, pulling out stuffing"),
    ("close", "lies on the seat and slowly chews the edge of the cushion it is lying on"),
    ("medium", "jumps onto the sofa, grabs the armrest in its mouth and tugs hard"),
    ("medium", "chews the front corner of the seat cushion while standing on the rug"),
    ("medium", "pulls a back cushion onto the floor with its teeth and keeps biting it"),
    ("medium", "bites the sofa skirt and backs away, stretching the fabric"),
    ("medium", "plays with a ball on the floor for a few seconds, then turns and bites the sofa armrest"),
    ("medium", "digs at the seat with its paws and then bites and tears the cushion fabric"),
    ("medium", "chews the side of the sofa near the floor, small pieces of fabric falling down"),
    ("medium", "bites a seat cushion and shakes its head, white stuffing spreading on the seat"),
    ("wide", "walks to the sofa, bites the armrest and tugs it repeatedly"),
    ("wide", "chews the corner of the seat cushion while the rest of the room stays still"),
    ("wide", "lies on the sofa and chews the backrest, tufts of stuffing visible"),
    ("wide", "pulls the sofa skirt with its teeth from the floor side"),
    ("wide", "bites a seat cushion and drags it off the sofa onto the floor"),
    ("wide", "after napping on the rug, gets up and chews the sofa's front edge"),
]
NEGATIVE = [  # ordinary behaviour around the sofa
    ("close", "naps curled up on the seat cushion, breathing slowly", "normal"),
    ("close", "rests its chin on the armrest and watches the room, blinking", "normal"),
    ("close", "rolls onto its back on the sofa and wiggles, mouth closed", "normal"),
    ("medium", "jumps onto the sofa, turns around twice and lies down", "normal"),
    ("medium", "walks past the sofa, drinks from a water bowl nearby and leaves", "normal"),
    ("medium", "sits on the sofa looking out of the window", "normal"),
    ("medium", "scratches its own ear with a hind leg while sitting on the sofa", "normal"),
    ("wide", "trots around the room and lies down on the rug far from the sofa", "normal"),
    ("wide", "plays fetch alone with a bouncing ball across the floor", "normal"),
    ("wide", "walks into the room, sniffs the air, and leaves without touching the sofa", "normal"),
    ("wide", "sleeps on the sofa the whole time", "normal"),
    ("close", "yawns widely while lying on the armrest, then lays its head down", "hard"),
    # hard negatives: mouth near the sofa, or chewing something that is not the sofa
    ("close", "licks the seat cushion fabric with its tongue but never bites it", "hard"),
    ("close", "sniffs along the seat seam intensely, nose pressed into the fabric, without biting", "hard"),
    ("close", "chews a bully stick held between its paws on the seat cushion", "hard"),
    ("close", "chews a tan rope toy that is almost the same color as the sofa, on the seat", "hard"),
    ("close", "chews its own front paw while lying on the sofa", "hard"),
    ("close", "pants with its mouth open, head resting on the armrest", "hard"),
    ("medium", "chews a blanket that is draped over the sofa, the sofa underneath untouched", "hard"),
    ("medium", "digs and paws at the seat cushion to make a bed, mouth never touching it", "hard"),
    ("medium", "chews a sneaker on the floor right next to the sofa", "hard"),
    ("medium", "tears apart a cardboard box beside the sofa, scraps on the floor", "hard"),
    ("medium", "tugs a rope toy tied to the sofa leg, pulling only the rope", "hard"),
    ("medium", "carries a plush toy across the sofa and drops it on the seat", "hard"),
    ("medium", "grooms another dog lying next to it on the sofa, licking its fur", "hard"),
    ("wide", "chews a chew toy on the sofa seat, small in the frame", "hard"),
    ("wide", "rips a stuffed toy on the floor near the sofa, white filling on the rug", "hard"),
    ("wide", "two dogs wrestle playfully on the rug in front of the sofa, mouths on each other only", "hard"),
    ("wide", "chews a towel on the floor beside the sofa at night", "hard"),
    ("wide", "noses under the sofa looking for a ball, mouth never on the sofa", "hard"),
    ("close", "holds a tennis ball in its mouth while lying with its head on the cushion", "hard"),
    ("medium", "licks its own leg while sitting on the sofa", "hard"),
    ("close", "gnaws an antler chew on the armrest, the armrest itself untouched", "hard"),
    ("medium", "pulls a toy out from between two seat cushions with its teeth, without biting the cushions", "hard"),
    ("wide", "chews a slipper on the rug in the middle of the room", "normal"),
    ("close", "sneezes and shakes its head while sitting on the seat cushion", "normal"),
]

# Trimmed to 50 on 2026-10-24 (not enough generation time for 60). T01-T29 were already generated;
# from T30-T60 one or two scenes were dropped per (view x positive / hard / normal) cell so the 50 keep
# the 60's proportions (20 positive, 20 hard, 10 normal; 19 close, 18 medium, 13 wide), dropping the
# scene most similar to one already generated.
DROPPED = {"T31", "T33", "T34", "T36", "T37", "T42", "T43", "T48", "T49", "T53"}

# Extra negatives D01-D05: the sofa is ALREADY damaged and the dog does not chew it. Almost every
# positive clip shows damage appearing, so a model could learn "torn fabric / stuffing = alert"
# instead of the chewing itself; these clips test for that shortcut.
DAMAGED = [
    ("close", "lies asleep on the seat cushion right next to the existing tear, breathing slowly"),
    ("close", "sits beside the frayed armrest and briefly sniffs the loose threads, then looks away; "
              "its mouth never touches the fabric"),
    ("medium", "walks past the sofa, sniffs the stuffing lying on the floor for a moment and leaves"),
    ("medium", "lies on the rug in front of the sofa with its head on its paws, not chewing anything"),
    ("wide", "jumps onto the sofa, turns around twice and lies down next to the ripped backrest"),
]
DAMAGE = {
    "close": "Before the clip starts the sofa is already damaged: one seat cushion has a large old tear "
             "with white stuffing poking out, and the front of the armrest is frayed with loose threads.",
    "medium": "Before the clip starts the sofa is already damaged: the skirt along the bottom is ripped and "
              "hanging, and a few tufts of old stuffing lie on the floor in front of it.",
    "wide": "Before the clip starts the sofa is already damaged: the backrest has a long old rip with "
            "white stuffing bulging out, large enough to see from across the room.",
}
DAMAGED_GUARD = ("The damage is already there at the start and does not change during the clip: the dog's "
                 "mouth never bites, chews or pulls the sofa and no new tears or stuffing appear. ")

NO_BITE = ("Its mouth never bites, chews or pulls the sofa, and the sofa stays completely intact: no tears, "
           "no loose threads, no stuffing from the sofa.")
TEMPLATES = [
    "Home security footage, {light}. Recorded by {camera}. The room is a {room} with a {sofa}. "
    "A {dog} {action}. {guard}The view is locked off for the whole clip: one continuous take, no camera motion, "
    "no zoom. Realistic animal motion, realistic lighting, no people, no on-screen text.",
    "Static {view_word} shot from {camera} in a {room}, {light}. In the frame is a {sofa}. "
    "During the clip a {dog} {action}. {guard}Nothing else moves the camera: no pan, no zoom, no cuts. "
    "Looks like real footage from a home camera, with no people and no captions or overlays.",
    "A real-looking clip from a pet-monitoring camera ({camera}). Setting: {room}, {light}, with a {sofa}. "
    "What happens: a {dog} {action}. {guard}Single uninterrupted shot, fixed framing, no zoom, natural dog "
    "behaviour, no humans, no text, not stylised or cinematic.",
    "{light_cap}. A {room} seen through {camera}. A {sofa} is in view, and a {dog} {action}. {guard}"
    "The footage is one fixed, continuous shot with ordinary home-camera image quality: no camera movement, "
    "no zoom, no people, no subtitles, no animation look.",
]
VIEW_WORD = {"close": "close-up", "medium": "medium", "wide": "wide"}


def main() -> int:
    rng = random.Random(SEED)
    scenes = [dict(view=v, label="positive", group="positive", action=a) for v, a in POSITIVE]
    scenes += [dict(view=v, label="negative", group=g, action=a) for v, a, g in NEGATIVE]
    rng.shuffle(scenes)
    dogs, sofas, rooms, lights = (rng.sample(x, len(x)) for x in (DOGS, SOFAS, ROOMS, LIGHTS))
    prompts = []
    for i, s in enumerate(scenes):
        light = lights[i % len(lights)]
        attrs = dict(dog=dogs[i % len(dogs)], sofa=sofas[i % len(sofas)], room=rooms[i % len(rooms)],
                     camera=rng.choice(CAMERAS[s["view"]]), light=light)
        if s["label"] == "negative":
            guard = NO_BITE + " "
        else:  # positives start undamaged, except the one that widens an existing worn spot
            guard = "" if "existing" in s["action"] else "At the start of the clip the sofa looks undamaged. "
        text = TEMPLATES[i % len(TEMPLATES)].format(**attrs, action=s["action"], guard=guard,
                                                    view_word=VIEW_WORD[s["view"]], light_cap=light[0].upper() + light[1:])
        text = re.sub(r"\b([Aa]) (?=[aeiouAEIOU])", r"\1n ", text)  # "a emerald" -> "an emerald"
        pid = f"T{i + 1:02d}"
        prompts.append(dict(id=pid, view=s["view"], intended=s["label"], group=s["group"],
                            status="dropped" if pid in DROPPED else "use",
                            template=i % len(TEMPLATES), **attrs, action=s["action"], prompt=text))

    used = [p for p in prompts if p["status"] == "use"]
    counts = {"total": len(used), "dropped": len(prompts) - len(used),
              **{v: sum(p["view"] == v for p in used) for v in VIEW_WORD},
              "intended_positive": sum(p["intended"] == "positive" for p in used),
              "intended_negative": sum(p["intended"] == "negative" for p in used),
              "hard_negative": sum(p["group"] == "hard" for p in used)}
    data = {
        "version": 1,
        "purpose": "Held-out test set. Evaluated once after all settings are frozen; never used for training, "
                   "threshold picking, prompt or crop choices. Distribution-shifted from the training prompts.",
        "how_to_use": [
            "Save clips as T01.mp4 … T60.mp4 in data/Test-Videos (id only); skip the ten with status 'dropped'.",
            "Label blind in the label tool WITHOUT --suggest, and label what is visible, not the intended label.",
            "Never pass data/Test-Videos to mcam-train, eval_probe.py or experiment scripts (build_dataset refuses it).",
            "Run the final evaluation once; if settings change afterwards, the set is no longer clean.",
        ],
        "counts": counts,
        "prompts": prompts,
    }
    (ROOT / "prompts/test_set_prompts.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n",
                                                        encoding="utf-8")

    md = [
        "# MischiefCam · Held-out test set prompts (T01–T60, 50 clips actually generated)",
        "",
        "**This batch is for the final evaluation only: do not use it to train, pick thresholds, pick crops or tune prompts.** Run it once, after all settings are final; "
        "that score is the performance to report in the proposal. If settings change afterwards, this set is no longer clean and a new one is needed.",
        "",
        "- Save the clips as `T01.mp4` … `T60.mp4` in `data/Test-Videos/` (IDs only).",
        f"- **Reduced to 50 clips on 2026-10-24**: the {counts['dropped']} rows marked \"not generated\" below are skipped. In each \"view × type\""
        " cell, the scenario most similar to an already generated clip was omitted, so the positive/negative, hard-negative and view proportions match the original 60.",
        "- There are also 5 damaged-sofa negatives in `test_damaged_sofa_prompts.md` (D01–D05), saved in `data/Test-Videos/` as well.",
        "- **Blind-label them yourself**: run the label tool without `--suggest`; label what actually happens on screen, not what the prompt intended.",
        "- Dog breeds, sofas and rooms are all absent from the training prompts; camera positions and phrasing are deliberately different too, to test whether detection survives a change of style.",
        "- Positives and negatives were shuffled before numbering, so IDs reveal nothing; the intended outcomes are only in `test_set_prompts.json`, so do not open it until labelling is done.",
        f"- Composition: {counts['total']} clips in total: {counts['close']} close, {counts['medium']} medium, {counts['wide']} wide.",
        "- If you have real footage (your own or a teammate's dog), save it as `R01.mp4` … in the same folder and blind-label it together.",
        "  Real footage best answers the question the judges will ask: does a model trained on synthetic data work in the real world?",
        "",
        "| ID | View | Status |",
        "|---|---|---|",
        *[f"| {p['id']} | {p['view']} | {'**not generated**' if p['status'] == 'dropped' else 'generated'} |" for p in prompts],
        "",
    ]
    for p in prompts:
        title = f"## {p['id']} · {p['view']}" + (" (not generated)" if p["status"] == "dropped" else "")
        md += [title, "", "```text", p["prompt"], "```", ""]
    (ROOT / "prompts/test_set_prompts.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(counts))
    write_damaged(random.Random(SEED + 1))
    return 0


def write_damaged(rng: random.Random) -> None:
    # no night vision here: if the detector misses the dog (as on T08) the clip passes without testing
    # the damage shortcut at all
    day = [light for light in LIGHTS if "infrared" not in light]
    dogs, sofas, rooms, lights = (rng.sample(x, len(x)) for x in (DOGS, SOFAS, ROOMS, day))
    prompts = []
    for i, (view, action) in enumerate(DAMAGED):
        light = lights[i % len(lights)]
        attrs = dict(dog=dogs[i], sofa=sofas[i], room=rooms[i], camera=rng.choice(CAMERAS[view]), light=light)
        text = TEMPLATES[i % len(TEMPLATES)].format(**attrs, action=action, guard=DAMAGE[view] + " " + DAMAGED_GUARD,
                                                    view_word=VIEW_WORD[view], light_cap=light[0].upper() + light[1:])
        text = re.sub(r"\b([Aa]) (?=[aeiouAEIOU])", r"\1n ", text)
        prompts.append(dict(id=f"D{i + 1:02d}", view=view, intended="negative", group="damaged_sofa",
                            **attrs, action=action, prompt=text))
    data = {
        "version": 1,
        "purpose": "Held-out negatives with an already-damaged sofa and no chewing: does the model alert on "
                   "visible damage instead of the chewing itself? Evaluated once with the test set.",
        "how_to_use": ["Save clips as D01.mp4 … D05.mp4 in data/Test-Videos and label them blind with the "
                       "test set; label what is visible (a clip where the dog does bite the sofa is positive)."],
        "prompts": prompts,
    }
    (ROOT / "prompts/test_damaged_sofa_prompts.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n",
                                                                 encoding="utf-8")
    md = [
        "# MischiefCam · Damaged-sofa negative prompts (D01–D05)",
        "",
        "**Purpose**: almost every positive clip shows \"dog bites, then the sofa tears and stuffing comes out\", so the model may take a shortcut and learn \"alert whenever a hole or stuffing is visible\"."
        "These 5 clips show **a sofa that is already damaged, with no chewing**, to check for that shortcut.",
        "",
        "- Save as `D01.mp4` … `D05.mp4` in `data/Test-Videos/`; blind-label with the T series, evaluate once together with it, never train on them.",
        "- Label what is visible: if the video generator makes the dog bite the sofa, label that clip positive.",
        "- When generating: the damage must be **present from the first frame** and must not grow during the clip.",
        "",
        "| ID | View |",
        "|---|---|",
        *[f"| {p['id']} | {p['view']} |" for p in prompts],
        "",
    ]
    for p in prompts:
        md += [f"## {p['id']} · {p['view']}", "", "```text", p["prompt"], "```", ""]
    (ROOT / "prompts/test_damaged_sofa_prompts.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
