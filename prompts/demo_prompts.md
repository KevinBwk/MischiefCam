# MischiefCam · Demo 片段 prompt

**目的**：Demo 影片用的片段，取代 playlist 裡畫面有問題的舊片段（v20：狗上沙發的動作不自然）。
只用來播放，**不拿來訓練、調參或評估**。

- 存成 `nap01.mp4`、`nap02.mp4` …，放在 `data/Demo-Videos/`（和開發集、測試集分開；`data/` 已被 `.gitignore` 排除）。
- 合成片段（synthetic clips），2026-10-27 生成。
- 生成後先檢查：畫面沒有疊字或邊框、狗只跳一次、跳上去後一直待在沙發上，再用 `batch_run.py --vlm either` 確認整支都不發警報。

## NAP · 狗跳上沙發、趴下休息（Michelle 保持安靜）

迭代紀錄：
1. 「先放前腳、再跳後腳」→ 跳兩段。
2. 時間軸分鏡、細寫落地順序、否定句寫「no two-step climbing」→ 仍然跳兩次。
3. 加入轉身 → 轉身動作怪異，刪掉。
4. 寫「pet-camera footage」並列出否定清單 → 畫面四周出現邊框和圖示。
5. 最終版（下方），使用者自行修訂。

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

## CHEW · 夜視遠景、狗咬沙發（Michelle 發警報）

**目的**：取代 playlist 第 4 幕的 w04（夜視畫面裡沙發一開始就破了）。存成 `chew01.mp4`、`chew02.mp4` …，放在 `data/Demo-Videos/`。
生成後先檢查：第一幀沙發完好、破損在開始咬之後才出現、狗的腳一直踩在地上，再用 `batch_run.py --vlm either` 確認咬之後有發警報。

寫法沿用 NAP 的教訓：動作只寫一次、不用「pet camera / security camera」這類字眼（容易冒出監視器邊框與圖示）。

```
A single continuous, photorealistic 8-second video of a real dog chewing the corner of a sofa cushion at night, seen from high up in the corner of a dark living room.

SCENE:
A living room at night, shown in black-and-white infrared night vision: soft gray tones, slightly grainy, eyes of the dog may glow faintly. The view looks down from high in one corner of the room and shows the whole room, with a fabric three-seat sofa in the far half of the frame and an open floor in front of it. The sofa is small in the frame but clearly visible.

The camera remains perfectly still throughout the video. No camera movement, zooming, cuts, or transitions.

At the start of the video the sofa is completely intact and clean: smooth fabric, no tears, no loose threads, and nothing on the floor.

DOG:
A medium-sized short-haired dog with natural body proportions and anatomically correct legs and paws. The dog's appearance remains completely consistent throughout.

ACTION:
The dog walks calmly from the left side of the room to the front of the sofa.

Standing on the floor with all four paws, it lowers its head, grips the front corner of the seat cushion with its teeth, and starts chewing and tugging it, pulling backward and shaking its head from side to side.

It keeps chewing the same corner until the end of the video. After a few seconds of chewing, the fabric at that corner begins to fray and tear, and a small tuft of white stuffing pokes out.

MOTION AND PHYSICS:
All movements follow realistic canine biomechanics, with natural weight transfer and gravity. The dog's paws stay planted on the floor the whole time, and the cushion moves slightly as it is tugged.

Natural everyday animal behavior, without exaggerated or overly choreographed movements.

VISUAL STYLE:
Authentic, unedited night-vision home footage. Realistic infrared lighting, realistic shadows, ordinary household textures, and believable motion.

CLEAN FRAME:
The video contains only the dog and the natural living room environment. The picture is clean and fills the frame edge to edge.

Absolutely no text, numbers, captions, subtitles, logos, watermarks, timestamps, recording indicators, red dots, symbols, icons, user interface elements, borders, or graphic overlays.

OUTPUT:
8 seconds, 16:9 landscape, 720p or higher, one uninterrupted continuous shot, natural motion speed.
```

### chew01 結果（2026-10-27）：不能用

畫面乾淨、開頭沙發完好，但影片只有 7 秒，狗走到 4.5 秒左右才咬住坐墊邊緣，而且整支都沒有破損。
模型只在 2.3 s、6.0 s 各審查一次，分類器 p 最高 0.445（門檻 0.534），VLM 都回 insufficient，沒有發警報。
和測試集 t55 一樣：**看不到破壞痕跡的輕咬，分類器抓不到**。

### 修正版 v2（chew02 起用這版）

改動：狗從第一秒就在沙發前、很快開始咬，咬的時間拉長到 6 秒以上；破損和填充物明確出現；鏡頭改成中景，讓狗和沙發在畫面裡大一點。

```
A single continuous, photorealistic 8-second video of a real dog chewing and tearing the front corner of a sofa seat cushion at night in a dark living room.

SCENE:
A living room at night, shown in black-and-white infrared night vision: soft gray tones, slightly grainy, the dog's eyes may glow faintly. The view looks down at an angle from high on the wall across the room. A fabric three-seat sofa fills about half of the frame, with an open floor in front of it.

The camera remains perfectly still throughout the video. No camera movement, zooming, cuts, or transitions.

At the very start of the video the sofa is completely intact and clean, with smooth fabric and nothing on the floor.

DOG:
A medium-sized short-haired dog with natural body proportions and anatomically correct legs and paws, already standing on the floor right in front of the sofa when the video begins. The dog's appearance remains completely consistent throughout.

ACTION:
Within the first second, the dog lowers its head, bites the front corner of the seat cushion, and starts chewing and tugging it hard, pulling backward and shaking its head from side to side.

It keeps chewing and tugging the same corner for the rest of the video. By the third second the fabric rips open at that corner, and from then on the dog pulls out clumps of white stuffing, which fall onto the cushion and the floor and keep piling up until the end.

MOTION AND PHYSICS:
All movements follow realistic canine biomechanics, with natural weight transfer and gravity. The dog's paws stay planted on the floor the whole time, and the cushion moves as it is tugged.

Natural everyday animal behavior, without exaggerated or overly choreographed movements.

VISUAL STYLE:
Authentic, unedited night-vision home footage. Realistic infrared lighting, realistic shadows, ordinary household textures, and believable motion.

CLEAN FRAME:
The video contains only the dog and the natural living room environment. The picture is clean and fills the frame edge to edge.

Absolutely no text, numbers, captions, subtitles, logos, watermarks, timestamps, recording indicators, red dots, symbols, icons, user interface elements, borders, or graphic overlays.

OUTPUT:
8 seconds, 16:9 landscape, 720p or higher, one uninterrupted continuous shot, natural motion speed.
```

### 修正版 v3：長時間咬、不出棉絮（測試「沒有破損也抓得到」）

改動（相對 v2）：從第 0.5 秒咬到最後，整段約 7 秒都在咬；用動作本身表現「在咬」（反覆咬合、甩頭、把坐墊角拉離原位），布料只會被拉皺、沾濕，始終完整。
風險：分類器對沒有破損的輕咬信心低（t55、chew01 都沒發警報），這支可能不發警報；生成後一定要先跑模型確認。

```
A single continuous, photorealistic 8-second video of a real dog persistently chewing and tugging the front corner of a sofa seat cushion at night in a dark living room.

SCENE:
A living room at night, shown in black-and-white infrared night vision: soft gray tones, slightly grainy, the dog's eyes may glow faintly. The view looks down at an angle from high on the wall across the room. A fabric three-seat sofa fills about half of the frame, with an open floor in front of it.

The camera remains perfectly still throughout the video. No camera movement, zooming, cuts, or transitions.

DOG:
A medium-sized short-haired dog with natural body proportions and anatomically correct legs and paws, already standing on the floor right in front of the sofa when the video begins, its head close to the front corner of the seat cushion. The dog's appearance remains completely consistent throughout.

ACTION:
Half a second into the video, the dog clamps its teeth onto the front corner of the seat cushion and does not let go for the rest of the video.

For the whole remaining seven seconds it chews the corner continuously: its jaws open and close again and again on the fabric, it braces its front legs and pulls backward, shakes its head from side to side, then bites down and pulls again in a steady, determined rhythm.

Each pull drags the cushion corner forward off the sofa frame and the fabric stretches, bunches up and darkens slightly where it is wet from the dog's mouth, while the cover itself stays in one piece.

MOTION AND PHYSICS:
All movements follow realistic canine biomechanics, with natural weight transfer and gravity. The dog's paws stay planted on the floor the whole time, and the cushion shifts and springs back as it is tugged.

Natural everyday animal behavior, without exaggerated or overly choreographed movements.

VISUAL STYLE:
Authentic, unedited night-vision home footage. Realistic infrared lighting, realistic shadows, ordinary household textures, and believable motion.

CLEAN FRAME:
The video contains only the dog, the sofa and the natural living room environment. The picture is clean and fills the frame edge to edge.

Absolutely no text, numbers, captions, subtitles, logos, watermarks, timestamps, recording indicators, red dots, symbols, icons, user interface elements, borders, or graphic overlays.

OUTPUT:
8 seconds, 16:9 landscape, 720p or higher, one uninterrupted continuous shot, natural motion speed.
```

### chew03 結果（v3，2026-10-27）：不能用

畫面乾淨、8 秒、沙發完好，坐墊上有一塊沾濕的深色痕跡；但生成的動作很弱：狗站在坐墊旁、嘴巴靠近邊緣開合，看不出咬住拉扯，坐墊也沒有被拖動。
跑兩次都沒發警報：分類器 p 0.426–0.468（門檻 0.534），VLM 都回 insufficient。
結論：Demo 的警報場景改用 v2（有破損與棉絮）；「沒有破損的輕咬」列為已知限制。

### 修正版 v4：布料破損、不出棉絮（白天中近景）

改動（相對 v3）：改白天、鏡頭拉近，讓嘴巴咬住布料的接觸點清楚可見；咬的動作明確（咬住 → 拉起布料繃緊 → 甩頭）；破損只到「布料磨毛、線頭被拉出、縫線邊緣裂開一小段」，用正面描述，不提填充物。
存成 `chew04.mp4` 起。生成後挑一支「看得出咬住拉扯」的再跑模型。

```
A single continuous, photorealistic 8-second video of a real dog chewing and tugging the fabric on the front edge of a sofa seat cushion in a bright living room.

SCENE:
A modern living room in soft afternoon daylight coming from a window on the left. A light beige woven-fabric three-seat sofa fills about two thirds of the frame, seen from slightly above and in front at about two meters away, with a wooden floor in front of it. The front edge of the seat cushion, where the dog bites, is clearly visible in the middle of the frame.

The camera remains perfectly still throughout the video. No camera movement, zooming, cuts, or transitions.

At the very start of the video the sofa is completely intact, with smooth, even fabric.

DOG:
A medium-sized short-haired brown dog with natural body proportions and anatomically correct legs and paws, already standing on the floor right in front of the sofa when the video begins, its head at the front edge of the seat cushion. The dog's appearance remains completely consistent throughout.

ACTION:
Half a second into the video, the dog bites into the fabric on the front edge of the seat cushion, gripping a fold of the cover firmly between its teeth so its mouth and the fabric are clearly in contact.

For the rest of the video it chews and tugs that same spot: it pulls its head back so the fabric lifts and stretches tight, shakes its head from side to side, lets the fabric slacken, then bites down and pulls again in a steady, determined rhythm.

As it keeps chewing, the woven fabric around the spot frays and becomes fuzzy, loose threads are pulled out and dangle from the dog's mouth, and by the end a short section of the seam along the front edge has split open, leaving a small ragged gap with frayed edges.

MOTION AND PHYSICS:
All movements follow realistic canine biomechanics, with natural weight transfer and gravity. The dog's paws stay planted on the floor the whole time, and the cushion shifts slightly with each pull.

Natural everyday animal behavior, without exaggerated or overly choreographed movements.

VISUAL STYLE:
Authentic, unedited home video footage. Natural lighting, realistic shadows, ordinary household textures, and believable motion.

CLEAN FRAME:
The video contains only the dog, the sofa and the natural living room environment. The picture is clean and fills the frame edge to edge.

Absolutely no text, numbers, captions, subtitles, logos, watermarks, timestamps, recording indicators, red dots, symbols, icons, user interface elements, borders, or graphic overlays.

OUTPUT:
8 seconds, 16:9 landscape, 720p or higher, one uninterrupted continuous shot, natural motion speed.
```

### chew04 結果（v4，2026-10-27）：畫面可用，警報不穩

畫面乾淨、沒有棉絮：狗約 1 秒咬住坐墊前緣，6 秒後拉出長條布料與線頭。
5 次跑法只有 3 次發警報（6.2–7.1 s，分類器 p 0.538–0.540，剛過門檻 0.534）；前 5 秒分類器 p 0.43–0.46，只有布料被拉出來之後才過門檻，且最後一次審查的時間點每次略有不同。
Demo 現場播放可能不發警報，不建議當第 4 幕；若要再生，讓布料破損提早到 2–3 秒出現。

### 修正版 v5：正面咬、破損提早（chew05 起）

針對 chew04 失敗原因：
1. 狗和沙發平行 → 截圖變成整隻狗、嘴巴落在邊緣。改成狗**正面朝向沙發**、鏡頭從斜前方約 45 度拍，讓「狗頭＋坐墊接觸點」成為狗與沙發重疊的區域（v32、t54 都是這種姿勢，都抓到）。
2. 破損 6 秒後才出現 → 改成約 2 秒開始磨毛、出線頭，之後裂口逐漸變大，讓每次審查（約 2、4、6 秒）都看得到破壞痕跡。
3. 長布條看起來不自然 → 改成短線頭、毛邊與小裂口。
生成後先看：狗是否正對沙發、2 秒左右是否已有磨毛或線頭，再跑模型。

```
A single continuous, photorealistic 8-second video of a real dog chewing into the front edge of a sofa seat cushion in a bright living room.

SCENE:
A modern living room in soft afternoon daylight from a window on the left. A light beige woven-fabric three-seat sofa is seen from the front-left at about a 45-degree angle, about two meters away and slightly from above, filling about two thirds of the frame, with a wooden floor in front of it.

The camera remains perfectly still throughout the video. No camera movement, zooming, cuts, or transitions.

At the very start of the video the sofa is completely intact, with smooth, even fabric.

DOG:
A medium-sized short-haired brown dog with natural body proportions and anatomically correct legs and paws. When the video begins it is already standing on the floor directly in front of the middle seat cushion, facing the sofa head-on, its body pointing straight at the sofa and its head at the front edge of the cushion. Its face and mouth are clearly visible from the camera's angle. The dog's appearance remains completely consistent throughout.

ACTION:
Half a second into the video, the dog bites into the front edge of the middle seat cushion, gripping the fabric firmly between its teeth.

It keeps chewing that same spot for the rest of the video, working its jaws, pulling its head back so the fabric lifts and stretches, and shaking its head from side to side before biting down again, in a steady, determined rhythm. It stays facing the sofa the whole time.

The damage appears early and grows steadily: by the second second the fabric under its teeth is already fuzzy and frayed with short loose threads sticking out; by the fourth second a small ragged tear has opened along the front edge; by the end the tear is a hand-width wide, with frayed edges and loose threads hanging from it and from the dog's mouth.

MOTION AND PHYSICS:
All movements follow realistic canine biomechanics, with natural weight transfer and gravity. The dog's paws stay planted on the floor the whole time, and the cushion shifts slightly with each pull.

Natural everyday animal behavior, without exaggerated or overly choreographed movements.

VISUAL STYLE:
Authentic, unedited home video footage. Natural lighting, realistic shadows, ordinary household textures, and believable motion.

CLEAN FRAME:
The video contains only the dog, the sofa and the natural living room environment. The picture is clean and fills the frame edge to edge.

Absolutely no text, numbers, captions, subtitles, logos, watermarks, timestamps, recording indicators, red dots, symbols, icons, user interface elements, borders, or graphic overlays.

OUTPUT:
8 seconds, 16:9 landscape, 720p or higher, one uninterrupted continuous shot, natural motion speed.
```

### chew05 結果（v5，2026-10-27）：不穩，比 chew04 差

畫面乾淨、沒有棉絮，約 1.5 秒開始出現線頭，破損逐漸變大（符合 v5）；但**狗仍然和沙發平行側身站**，只把頭轉向坐墊，鏡頭也是正前方而非 45 度（v5 最關鍵的改動沒有生成出來）。
自然度：腿和身體 8 秒幾乎不動、只有頭在咬，略僵硬；後段線頭拉得很長、垂到地上，和 chew04 一樣略不自然。
5 次跑法 2 次發警報，兩次都由 VLM 發出（6.9 s、7.3 s）；分類器 p 0.422–0.506，一次都沒過門檻 0.534。

### 修正版 v6：前腳搭上坐墊咬（chew06 起）

chew04、chew05 都被畫成「狗和沙發平行側身站」，文字要求「正對沙發」會被忽略。v6 改用本身就讓身體朝向沙發的動作：**兩隻前腳搭在坐墊上咬**（v32、t54 都是這個姿勢，都穩定抓到）。
其他沿用：白天、無棉絮、約 2 秒開始磨毛出線頭；另外寫明身體隨拉扯前後移動，改善 chew05 的僵硬感；線頭寫短，避免垂到地上的長條。
生成後先看：前腳是否搭在坐墊上、狗頭是否疊在沙發上、2 秒左右是否已有磨毛或線頭。

```
A single continuous, photorealistic 8-second video of a real dog with its front paws up on a sofa, chewing the fabric of the seat cushion in a bright living room.

SCENE:
A modern living room in soft afternoon daylight from a window on the left. A light beige woven-fabric three-seat sofa is seen from the front, slightly to the left and slightly from above, about two meters away, filling about two thirds of the frame, with a wooden floor in front of it.

The camera remains perfectly still throughout the video. No camera movement, zooming, cuts, or transitions.

At the very start of the video the sofa is completely intact, with smooth, even fabric.

DOG:
A medium-sized short-haired brown dog with natural body proportions and anatomically correct legs and paws. When the video begins, it is already standing on its hind legs on the floor in front of the middle seat cushion, with both front paws resting on the cushion, its chest leaning against the front of the sofa and its head bent down over the cushion between its paws. The dog's appearance remains completely consistent throughout.

ACTION:
Half a second into the video, the dog bites into the fabric of the seat cushion just in front of its paws.

For the rest of the video it chews and tugs that spot with steady, determined energy: it grips the fabric, pulls its head back so the fabric lifts and stretches, shakes its head from side to side, then bites down again. Its shoulders and body rock backward and forward with each pull, its hind legs shift their footing on the floor, and its front paws press into the cushion to brace, while it stays up on the sofa the whole time.

The damage appears early and grows steadily: by the second second the fabric under its teeth is fuzzy and frayed with short loose threads; by the fourth second a small ragged tear has opened; by the end the tear is about a hand-width wide, with frayed edges and a few short threads caught in the dog's mouth.

MOTION AND PHYSICS:
All movements follow realistic canine biomechanics, with natural weight transfer and gravity. The front paws stay on the cushion and the hind paws stay on the floor, and the cushion sinks and shifts under the dog's weight as it pulls.

Natural everyday animal behavior, without exaggerated or overly choreographed movements.

VISUAL STYLE:
Authentic, unedited home video footage. Natural lighting, realistic shadows, ordinary household textures, and believable motion.

CLEAN FRAME:
The video contains only the dog, the sofa and the natural living room environment. The picture is clean and fills the frame edge to edge.

Absolutely no text, numbers, captions, subtitles, logos, watermarks, timestamps, recording indicators, red dots, symbols, icons, user interface elements, borders, or graphic overlays.

OUTPUT:
8 seconds, 16:9 landscape, 720p or higher, one uninterrupted continuous shot, natural motion speed.
```

### chew06 結果（v6，2026-10-27）：姿勢對了，警報仍不穩

姿勢照 v6 生成：前腳搭在中間坐墊、頭低在坐墊上、後腳站地，身體隨拉扯晃動，約 1.5 秒出現破口，沒有棉絮；自然度是 chew 系列裡最好的。鏡頭偏從狗的側後方拍，咬的位置常被狗頭擋住；破口的布片有時像紙片。
分類器截圖終於集中在「狗頭＋坐墊」，但 p 只有 0.476 → 0.495–0.499 → 0.524–0.527，5 次都沒過門檻 0.534；2 次由 VLM 在 4.8 s 發警報，3 次沒有警報。
觀察：Demo-Videos 這批新生成影片的分類器分數都擠在 0.42–0.54（nap01 不咬也有 0.44–0.49），咬與不咬差距很小，推測（未驗證）是這批影片的畫風和訓練用的影片不同。

### 修正版 v7：側面鏡頭、咬扶手（chew07 起）

chew06 姿勢對了，但鏡頭從狗的側後方拍，咬的位置常被狗頭擋住，分類器最高 0.527。v7 參考穩定抓到的 v32（咬扶手）與 t54（咬椅背墊）：**鏡頭在沙發側邊、看得到狗臉側面與嘴巴咬住布料**；咬的位置改成扶手上緣，狗頭抬高不擋嘴；鏡頭拉近；破損再明顯一點（仍無棉絮）。
若這支分類器仍過不了門檻，代表問題可能是這批生成影片的畫風（見 chew06 觀察），第 4 幕改用 t54 或維持 chew06。
生成後先看：狗臉側面朝鏡頭、嘴巴咬住扶手清楚可見、2 秒左右已有磨毛或線頭。

```
A single continuous, photorealistic 8-second video of a real dog with its front paws up on a sofa armrest, chewing the top of the armrest in a bright living room.

SCENE:
A modern living room in soft afternoon daylight from a window behind the camera. The camera is at the side of a light beige woven-fabric sofa, about one and a half meters from its near armrest, at about the height of the armrest and angled slightly down. The near armrest and the first seat cushion fill most of the frame, with the rest of the sofa receding into the background and a wooden floor below.

The camera remains perfectly still throughout the video. No camera movement, zooming, cuts, or transitions.

At the very start of the video the sofa is completely intact, with smooth, even fabric.

DOG:
A medium-sized short-haired brown dog with natural body proportions and anatomically correct legs and paws. When the video begins it is standing on its hind legs on the floor beside the near armrest, with both front paws on top of the armrest, its body in profile to the camera, so that its face, open mouth and teeth are clearly visible from the side. The dog's appearance remains completely consistent throughout.

ACTION:
Half a second into the video, the dog bites into the top edge of the armrest, its teeth sinking into the fabric.

For the rest of the video it chews and tugs the armrest with steady, determined energy: it grips the fabric, pulls its head back so the fabric lifts and stretches, shakes its head from side to side, then bites down again. Its shoulders and body rock with each pull and its hind legs shift their footing, while its front paws stay braced on the armrest and its face stays turned in profile to the camera.

The damage appears early and grows steadily: by the second second the fabric on top of the armrest is visibly fuzzy and frayed with loose threads; by the fourth second a ragged tear has opened; by the end the tear is about a hand-width wide, with frayed edges and a few short threads caught in the dog's mouth.

MOTION AND PHYSICS:
All movements follow realistic canine biomechanics, with natural weight transfer and gravity. The front paws stay on the armrest and the hind paws stay on the floor, and the armrest fabric dents and shifts under the dog's weight as it pulls.

Natural everyday animal behavior, without exaggerated or overly choreographed movements.

VISUAL STYLE:
Authentic, unedited home video footage. Natural lighting, realistic shadows, ordinary household textures, and believable motion.

CLEAN FRAME:
The video contains only the dog, the sofa and the natural living room environment. The picture is clean and fills the frame edge to edge.

Absolutely no text, numbers, captions, subtitles, logos, watermarks, timestamps, recording indicators, red dots, symbols, icons, user interface elements, borders, or graphic overlays.

OUTPUT:
8 seconds, 16:9 landscape, 720p or higher, one uninterrupted continuous shot, natural motion speed.
```

### chew07 結果（v7，2026-10-27）：可用，警報穩定

照 v7 生成：側面鏡頭、前腳搭在扶手、臉側面朝鏡頭、咬扶手上緣，約 2 秒出現磨毛線頭、之後裂口變大，沒有棉絮。小瑕疵：後段前腳有時貼在扶手側面而非頂面。
批次 5/5 在 2.1 s 發警報；Demo 現場播放 3/3 在 00:04 發警報（第一次審查回 insufficient、第二次判 suspect）。警報都由 VLM 發出，分類器 p 約 0.52（未過門檻 0.534）。

### 修正版 v8：夜視版強化（以 chew01 為基礎，chew08 起）

chew01（夜視遠景）失敗原因：狗 4.5 秒才咬、只有 7 秒、沒有破損、狗在畫面裡太小、側身與沙發平行。v8 保留夜視氣氛，套用 chew07 成功的做法：
- 狗**一開始就站在扶手旁**，0.5 秒就咬下去，咬到最後（不再花時間走過去）。
- **前腳搭在扶手上、臉側面朝鏡頭**，嘴巴咬住扶手上緣清楚可見（chew07 的姿勢）。
- 鏡頭從房間角落高處改成**中景**，沙發佔畫面約一半，狗不會太小。
- 約 2 秒開始磨毛、出線頭，之後裂口變大；不提填充物。
生成後先看：狗一開始就在扶手旁、臉側面朝鏡頭、2 秒左右已有磨毛或線頭。

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

### chew08 結果（v8 夜視，2026-10-27）：可用，警報穩定

照 v8 生成：夜視、側面中景、前腳搭在扶手、臉側面朝鏡頭，一開始就在咬，約 2 秒出現線頭、之後裂口變大，沒有棉絮。動作自然（身體隨拉扯晃動、後腳換位）；小瑕疵：後段破口的線頭偏深色、略雜亂。
批次 5/5 在 4.2 s 由分類器發警報（p=0.538，剛過門檻 0.534）；Demo 現場 3/3 在 00:02 由 VLM 發警報。兩條路徑都會觸發，是目前最穩的夜視片段。
