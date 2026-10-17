"""Generate a diverse, reproducible set of video-generation prompts for training/evaluation clips.

    uv run python scripts/gen_video_prompts.py            # writes prompts/training_video_prompts.{json,txt}

Diversity is built in by assigning every prompt its own combination of dog, room, sofa,
camera and lighting, cycling through each list so no combination repeats and every value is used.
Each entry records those attributes so train/test splits can later be made by scene, not by clip.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261018

DOGS = [
    "golden retriever", "black Labrador retriever", "chocolate Labrador retriever", "yellow Labrador puppy",
    "Siberian husky", "black-and-white border collie", "tricolor beagle", "Pembroke Welsh corgi",
    "fawn French bulldog", "brindle French bulldog", "long-haired dachshund", "red Shiba Inu",
    "white standard poodle", "apricot toy poodle", "German shepherd", "Jack Russell terrier",
    "black pug", "brindle boxer", "scruffy medium-sized mixed-breed dog", "Australian shepherd with a merle coat",
    "Bernese mountain dog puppy", "cream-colored Maltese", "gray Weimaraner", "black-and-tan Rottweiler puppy",
]
ROOMS = [
    "modern Scandinavian living room", "small city apartment living room", "cozy rustic living room with a brick wall",
    "minimalist white living room", "family living room with a few kids' toys on the floor",
    "mid-century modern living room with wood paneling", "bright loft with large windows",
    "compact studio apartment", "suburban living room with a fireplace", "living room with dark green walls and plants",
]
SOFAS = [
    ("gray fabric sectional sofa", "fabric"), ("brown leather three-seat sofa", "leather"),
    ("navy blue velvet sofa", "fabric"), ("beige linen two-seat sofa", "fabric"),
    ("olive green corduroy loveseat", "fabric"), ("white boucle sofa", "fabric"),
    ("cream fabric sofa with a chaise", "fabric"), ("charcoal tweed sofa with wooden legs", "fabric"),
    ("cognac faux-leather sofa", "leather"), ("light blue slipcovered sofa", "fabric"),
    ("mustard yellow two-seat sofa", "fabric"), ("black fabric futon sofa", "fabric"),
]
CAMERAS = [
    "Fixed wide-angle surveillance camera view from a high corner of the room",
    "Fixed fisheye home security camera with a dark circular vignette, mounted on the wall opposite the sofa",
    "Fixed indoor pet camera placed on a bookshelf at about seat height, looking across the room",
    "Fixed ceiling-mounted camera looking down at the room at a steep angle",
    "Fixed indoor camera on a side table, slightly tilted, with the sofa seen from the side",
    "Fixed wide-angle camera above the TV, facing the sofa straight on",
]
LIGHTS = [
    ("during bright daytime", "realistic indoor lighting"),
    ("on an overcast afternoon with soft, flat daylight", "realistic indoor lighting"),
    ("in the early evening under warm lamp light", "realistic indoor lighting"),
    ("in the late morning with strong sunlight and sharp shadows across the floor", "realistic indoor lighting"),
    ("at night, recorded in black-and-white infrared night-vision mode", "realistic infrared night-vision footage"),
]
POS_PARTS = {
    "fabric": ["the sofa armrest", "the front edge of a seat cushion", "the corner of a back cushion",
               "a throw pillow lying on the sofa", "the fabric skirt at the bottom of the sofa", "the corner of the chaise"],
    "leather": ["the sofa armrest", "the front edge of a seat cushion", "the corner of a back cushion",
                "a throw pillow lying on the sofa"],
}
POS_DAMAGE = {
    "fabric": "The fabric becomes visibly frayed and a small amount of stuffing appears.",
    "leather": "Visible tooth marks and a small tear appear in the leather.",
}
POS_ACTIONS = [
    "The dog walks up to the sofa, grips {part} with its teeth and starts chewing and tugging at it, shaking its head from side to side.",
    "The dog is lying on the floor next to the sofa, then turns and gnaws on {part} for several seconds, pulling at it with its teeth.",
    "The dog climbs onto the sofa and bites into {part}, pulling hard with its teeth for several seconds.",
    "The dog stands with its front paws on the sofa and repeatedly chews on {part}, pausing briefly and then biting again.",
    "The dog lies on the sofa and chews on {part} slowly and steadily, holding it in place with one paw.",
]
POS_ENDINGS = [
    "It then pauses, hears a sound, and looks directly toward the camera with an innocent expression.",
    "It keeps chewing until the end of the clip.",
    "It then stops, steps back and lies down next to the damage.",
    "It then lets go, wags its tail and walks away from the sofa.",
]
INTACT = "The sofa stays completely intact: no biting of the sofa, no torn fabric, no stuffing."
NEGATIVES = [
    # (id, behavior, label, weight, action, allows_humans, needs_intact)
    ("N01", "resting", "negative", 5,
     "The dog walks to the sofa, climbs onto it, circles once and lies down with its head on its front paws. It falls asleep and barely moves for the rest of the clip.", False, True),
    ("N02", "resting", "negative", 4,
     "The dog stands beside the sofa and rests its chin on the armrest with its mouth closed, tail wagging slowly, then lifts its head and looks around the room.", False, True),
    ("N03", "sitting", "negative", 4,
     "The dog jumps onto the sofa, turns around and sits upright on the seat cushion, calmly looking out of the window, then lies down.", False, True),
    ("N04", "licking_self", "negative", 4,
     "The dog lies on the sofa and repeatedly licks its own front paw. Its mouth only ever touches its own paw, never the sofa.", False, True),
    ("N05", "sniffing", "negative", 6,
     "The dog walks up to the sofa and sniffs slowly along the seat cushion and the armrest with its nose close to the fabric, mouth closed, then loses interest and walks away.", False, True),
    ("N06", "licking_object", "negative", 4,
     "The dog briefly licks the sofa armrest once or twice with its tongue, without biting or pulling, then sits down on the floor and scratches its ear.", False, True),
    ("N07", "chewing_toy", "negative", 7,
     "The dog lies on the floor right next to the sofa, holding a bright rubber chew toy between its front paws and chewing it enthusiastically. Only the toy is ever in its mouth.", False, True),
    ("N08", "chewing_toy", "negative", 7,
     "The dog lies on the sofa chewing and tugging a rope toy held between its paws. Only the rope toy is in its mouth; its teeth never touch the sofa.", False, True),
    ("N09", "chewing_toy", "negative", 4,
     "The dog lies on the sofa gnawing a large chew bone. Only the bone is in its mouth; its teeth never touch the sofa.", False, True),
    ("N10", "walking", "negative", 4,
     "The dog trots across the room, passing in front of the sofa without stopping or touching it, and walks out of the frame.", False, True),
    ("N11", "carrying", "negative", 4,
     "The dog walks past the sofa carrying a tennis ball in its mouth without stopping, then lies down on the rug away from the sofa and drops the ball.", False, True),
    ("N12", "playing", "negative", 3,
     "The dog plays with a squeaky toy on the floor in front of the sofa, tossing it into the air and pouncing on it. The dog never bites the sofa.", False, True),
    ("N13", "scratching_self", "negative", 3,
     "The dog sits on the sofa and scratches behind its ear with its hind leg, then shakes its head and lies down.", False, True),
    ("N14", "rolling", "negative", 3,
     "The dog rolls onto its back on the sofa, wiggling happily with its paws in the air, then settles down and rests.", False, True),
    ("N15", "person_present", "negative", 3,
     "A person walks into the room and rearranges the sofa cushions while the dog sits calmly on the floor and watches. The dog never touches the sofa. The person then leaves.", True, True),
    ("N16", "person_present", "negative", 2,
     "A person sits on the sofa and gently pets the dog, which rests its head on the person's lap with its mouth closed. The person then gets up and leaves the room.", True, True),
    ("N17", "unobservable", "uncertain", 3,
     "The dog stands on the far side of the sofa facing away from the camera, its head hidden behind the backrest so its mouth is never visible, then lies down out of view.", False, False),
]


def build_prompt(opening: str, action: str, ending: str, state: str, camera: str, realism: str, humans: bool) -> str:
    tail = (f"{camera}, single continuous shot, no cuts, no camera movement, realistic dog behaviour, {realism}, "
            f"{'' if humans else 'no humans, '}no text overlays, no subtitles, no cartoon style, no dramatic cinematic effects.")
    # damage / "stays intact" comes right after the action, before the closing beat
    return " ".join(s for s in (opening, action, state, ending, tail) if s)


def scene_cycler(rng: random.Random):
    """Yield (dog, room, sofa, camera, light) tuples that cycle every list and never repeat."""
    seen = set()
    lists = [DOGS[:], ROOMS[:], SOFAS[:], CAMERAS[:], LIGHTS[:]]
    pools = [[] for _ in lists]
    while True:
        combo = []
        for i, lst in enumerate(lists):
            if not pools[i]:
                pools[i] = lst[:]
                rng.shuffle(pools[i])
            combo.append(pools[i].pop())
        key = (combo[0], combo[1], combo[2][0])
        if key in seen:
            continue
        seen.add(key)
        yield tuple(combo)


def main() -> int:
    rng = random.Random(SEED)
    scenes = scene_cycler(rng)
    entries = []

    n_pos = 50
    for i in range(n_pos):
        dog, room, (sofa, material), camera, (light, realism) = next(scenes)
        part = POS_PARTS[material][i % len(POS_PARTS[material])]
        action = POS_ACTIONS[i % len(POS_ACTIONS)].format(part=part)
        ending = POS_ENDINGS[(i // len(POS_ACTIONS)) % len(POS_ENDINGS)]
        opening = f"A photorealistic CCTV-style video of a {dog} in a {room} {light}. There is a {sofa} in the room."
        entries.append({
            "label": "positive", "behavior": "chewing_furniture", "template": f"P{i % len(POS_ACTIONS) + 1:02d}",
            "target": part.replace("the ", "").replace("a ", ""),
            "prompt": build_prompt(opening, action, ending, POS_DAMAGE[material], camera, realism, False),
            "scene": {"dog": dog, "room": room, "sofa": sofa, "camera": camera.split(",")[0], "lighting": light},
        })

    neg_templates = [t for t in NEGATIVES for _ in range(t[3])]  # weighted: hard negatives appear more often
    for i, (tid, behavior, label, _w, action, humans, intact) in enumerate(neg_templates):
        dog, room, (sofa, _m), camera, (light, realism) = next(scenes)
        opening = f"A photorealistic CCTV-style video of a {dog} in a {room} {light}. There is a {sofa} in the room."
        entries.append({
            "label": label, "behavior": behavior, "template": tid, "target": "sofa",
            "prompt": build_prompt(opening, action, "", INTACT if intact else "", camera, realism, humans),
            "scene": {"dog": dog, "room": room, "sofa": sofa, "camera": camera.split(",")[0], "lighting": light},
        })

    # Order so that any prefix (e.g. the first 40) is already balanced and diverse.
    pos = [e for e in entries if e["label"] == "positive"]
    neg = [e for e in entries if e["label"] != "positive"]
    rng.shuffle(neg)
    ordered, pi, ni = [], 0, 0
    while pi < len(pos) or ni < len(neg):
        if pi < len(pos):
            ordered.append(pos[pi]); pi += 1
        for _ in range(2 if ni + 2 <= len(neg) else len(neg) - ni):
            ordered.append(neg[ni]); ni += 1
    # The interleaving above is 1 positive : 2 negatives; leftover negatives are appended.
    for k, e in enumerate(ordered, start=1):
        prefix = "pos" if e["label"] == "positive" else ("unc" if e["label"] == "uncertain" else "neg")
        e["id"] = f"V{k:03d}"
        e["priority"] = 1 if k <= 45 else (2 if k <= 90 else 3)
        e["suggested_filename"] = f"{e['id']}_{prefix}_{e['behavior']}.mp4"

    out = {
        "version": 1,
        "seed": SEED,
        "how_to_use": [
            "Generate clips in id order; priority 1 (first 45) is already balanced (about 1 positive : 2 negatives).",
            "Save each clip with its suggested_filename so labels can be pre-filled automatically.",
            "Label every clip from what is actually visible (the labeling tool shows the expected label as a hint only).",
            "Generators sometimes add chewing or stuffing to negative prompts: relabel or discard those clips.",
        ],
        "counts": {
            "total": len(ordered),
            "positive": sum(e["label"] == "positive" for e in ordered),
            "negative": sum(e["label"] == "negative" for e in ordered),
            "uncertain": sum(e["label"] == "uncertain" for e in ordered),
        },
        "prompts": [{k: e[k] for k in ("id", "priority", "label", "behavior", "template", "target",
                                       "suggested_filename", "prompt", "scene")} for e in ordered],
    }
    (ROOT / "prompts").mkdir(exist_ok=True)
    (ROOT / "prompts" / "training_video_prompts.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (ROOT / "prompts" / "training_video_prompts.txt").open("w", encoding="utf-8") as fh:
        for e in out["prompts"]:
            fh.write(f"### {e['id']}  [{e['label']}] {e['behavior']}  ->  {e['suggested_filename']}\n{e['prompt']}\n\n")
    print(json.dumps(out["counts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
