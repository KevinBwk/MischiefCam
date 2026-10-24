# MischiefCam · 破沙發負例 prompt（D01–D05）

**目的**：幾乎所有正例影片都是「狗咬 → 沙發被扯破、填充物跑出來」，模型可能偷學成「看到破洞或填充物就通知」。這 5 支是**沙發本來就破了，但狗沒有咬**，用來檢查有沒有這種偷吃步。

- 存成 `D01.mp4` … `D05.mp4`，放在 `data/Test-Videos/`，跟 T 系列一起盲標、一起只評估一次，不拿來訓練。
- 照畫面實際發生的標：生成工具如果讓狗真的咬了沙發，那支就標正例。
- 生成時注意：破洞要**從第一格就存在**，而且整支影片裡不變大。

| ID | 視角 |
|---|---|
| D01 | close |
| D02 | close |
| D03 | medium |
| D04 | medium |
| D05 | wide |

## D01 · close

```text
Home security footage, mixed warm lamp light and cool TV glow. Recorded by a pet camera placed low on the floor about one meter from the sofa. The room is a Japanese-style room with tatami mats with a sage green slipcovered sofa. A tan short-haired chihuahua lies asleep on the seat cushion right next to the existing tear, breathing slowly. Before the clip starts the sofa is already damaged: one seat cushion has a large old tear with white stuffing poking out, and the front of the armrest is frayed with loose threads. The damage is already there at the start and does not change during the clip: the dog's mouth never bites, chews or pulls the sofa and no new tears or stuffing appear. The view is locked off for the whole clip: one continuous take, no camera motion, no zoom. Realistic animal motion, realistic lighting, no people, no on-screen text.
```

## D02 · close

```text
Static close-up shot from a pet camera placed low on the floor about one meter from the sofa in a playroom with a colorful foam floor mat, late-morning sunlight with hard shadows and glare on the floor. In the frame is a tan suede sofa. During the clip a brindle Cane Corso sits beside the frayed armrest and briefly sniffs the loose threads, then looks away; its mouth never touches the fabric. Before the clip starts the sofa is already damaged: one seat cushion has a large old tear with white stuffing poking out, and the front of the armrest is frayed with loose threads. The damage is already there at the start and does not change during the clip: the dog's mouth never bites, chews or pulls the sofa and no new tears or stuffing appear. Nothing else moves the camera: no pan, no zoom, no cuts. Looks like real footage from a home camera, with no people and no captions or overlays.
```

## D03 · medium

```text
A real-looking clip from a pet-monitoring camera (a camera on the TV stand across the room, showing the whole sofa and some floor around it). Setting: cluttered student apartment, dim blue dusk light from the window, with a dusty pink velvet loveseat. What happens: a Dalmatian walks past the sofa, sniffs the stuffing lying on the floor for a moment and leaves. Before the clip starts the sofa is already damaged: the skirt along the bottom is ripped and hanging, and a few tufts of old stuffing lie on the floor in front of it. The damage is already there at the start and does not change during the clip: the dog's mouth never bites, chews or pulls the sofa and no new tears or stuffing appear. Single uninterrupted shot, fixed framing, no zoom, natural dog behaviour, no humans, no text, not stylised or cinematic.
```

## D04 · medium

```text
Flat overcast daylight. A sunroom full of plants seen through a camera on the TV stand across the room, showing the whole sofa and some floor around it. A floral-patterned fabric sofa is in view, and an orange Pomeranian lies on the rug in front of the sofa with its head on its paws, not chewing anything. Before the clip starts the sofa is already damaged: the skirt along the bottom is ripped and hanging, and a few tufts of old stuffing lie on the floor in front of it. The damage is already there at the start and does not change during the clip: the dog's mouth never bites, chews or pulls the sofa and no new tears or stuffing appear. The footage is one fixed, continuous shot with ordinary home-camera image quality: no camera movement, no zoom, no people, no subtitles, no animation look.
```

## D05 · wide

```text
Home security footage, strong backlight from a window behind the sofa. Recorded by a wide-angle camera above the doorway showing the entire room, the sofa in the far half. The room is a coastal beach house living room with an emerald green velvet Chesterfield sofa. A fluffy white Bichon frise jumps onto the sofa, turns around twice and lies down next to the ripped backrest. Before the clip starts the sofa is already damaged: the backrest has a long old rip with white stuffing bulging out, large enough to see from across the room. The damage is already there at the start and does not change during the clip: the dog's mouth never bites, chews or pulls the sofa and no new tears or stuffing appear. The view is locked off for the whole clip: one continuous take, no camera motion, no zoom. Realistic animal motion, realistic lighting, no people, no on-screen text.
```
