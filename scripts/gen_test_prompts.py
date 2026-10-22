"""Generate the held-out TEST set prompts (T01-T60): evaluated once, never trained or tuned on.

    uv run python scripts/gen_test_prompts.py     # writes prompts/test_set_prompts.{md,json}

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
        prompts.append(dict(id=f"T{i + 1:02d}", view=s["view"], intended=s["label"], group=s["group"],
                            template=i % len(TEMPLATES), **attrs, action=s["action"], prompt=text))

    counts = {"total": len(prompts), **{v: sum(p["view"] == v for p in prompts) for v in VIEW_WORD},
              "intended_positive": sum(p["intended"] == "positive" for p in prompts),
              "intended_negative": sum(p["intended"] == "negative" for p in prompts),
              "hard_negative": sum(p["group"] == "hard" for p in prompts)}
    data = {
        "version": 1,
        "purpose": "Held-out test set. Evaluated once after all settings are frozen; never used for training, "
                   "threshold picking, prompt or crop choices. Distribution-shifted from the training prompts.",
        "how_to_use": [
            "Save clips as T01.mp4 … T60.mp4 in data/Test-Videos (id only).",
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
        "# MischiefCam · 保留測試集 prompt（T01–T60）",
        "",
        "**這批只用來做最後一次評估，不拿來訓練、選門檻、選裁切或改 prompt。** 所有設定定案後才跑一次，"
        "跑出來的分數才是提案要寫的效能。跑完如果又改設定，這批就不算乾淨了，要另外再做一批。",
        "",
        "- 影片存成 `T01.mp4` … `T60.mp4`，放在 `data/Test-Videos/`（只用編號）。",
        "- **自己盲標**：標註工具不要加 `--suggest`；照畫面實際發生的標，不要參考 prompt 原本想要的結果。",
        "- 狗品種、沙發、房間都是訓練 prompt 沒出現過的；鏡頭位置與句型也刻意不同，用來測「換了風格還抓不抓得到」。",
        "- 正例、負例已經打散後才編號，編號看不出答案；預期結果只寫在 `test_set_prompts.json`，標完之前不要看。",
        f"- 組成：共 {counts['total']} 支，近景 {counts['close']}、中景 {counts['medium']}、廣角 {counts['wide']}。",
        "- 如果有真實影片（自家或隊友的狗），另外存成 `R01.mp4`…，放在同一個資料夾，一起盲標。",
        "  真實影片最能回答評審會問的「合成資料訓練的模型，真實世界有沒有用」。",
        "",
        "| ID | 視角 |",
        "|---|---|",
        *[f"| {p['id']} | {p['view']} |" for p in prompts],
        "",
    ]
    for p in prompts:
        md += [f"## {p['id']} · {p['view']}", "", "```text", p["prompt"], "```", ""]
    (ROOT / "prompts/test_set_prompts.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
