"""61 단계 6 (P14 §3) — 그림 속 입구 표 · 수련장 지도 프롬프트 (Gemini 콘셉트 → 톤 보정).

키·자격 증명은 여기에 없다(프록시가 붙임). 프롬프트 전문은 gen.py 가 raw/<id>_<tag>.json 과 prompts.json 에 남긴다.

DOORS: (region, nodeKind) → 장면 문장 · 입구 안 빛(light) · 참고 키아트(문체 맞춤용 첨부)
1층에서 실제로 쓰는 조합(data/route.json 읽기만 — 61 단계 6 시점):
  단(col) → 지역 = regionByCol [waste, waste, gate, outer, outer, brewery, brewery, hall]
  여정 birth·road(waste) · post(gate, 쉼터) / 단1 outer 전투·전투 / 단2 outer 전투·이벤트 / 단3 brewery 전투·전투 /
  단4 brewery 상점·쉼터 / 보스 hall. 엘리트(도전 성소 2차 묶음 위험 노드)는 단2·단3 전투 중 하나 → outer·brewery.
  지역 desc 가 outer 에 shop·rest, brewery 에 event 문장을 들고 있어(배치가 바뀔 수 있음) 그 셋도 만든다.
"""

STYLE = (
    "STYLE (keep identical across the series): a dark, grim key-art illustration for a 2D pixel-art roguelike, rendered as a "
    "detailed pixel-art scene painting with chunky, clearly readable shapes and flat shading (no soft airbrush, no photo texture, "
    "no film grain). Limited palette: near-black charcoal and cold ash grays carry the whole image; ONE warm accent only - amber / "
    "ember orange to pale gold (#8b4d22, #d67a11, #e8b858, #faeec0) - used sparingly for fire, embers, lantern light, spilled liquor "
    "and glowing eyes. No other hues at all: no blue, no green, no purple. Strong value structure: deep black silhouettes against dim "
    "gray midtones, the brightest values only in the amber accents. World: grounded, realistic Renaissance-era early-gunpowder "
    "setting (pikes, longbows, matchlock muskets, mud, supply wagons, timber-and-plaster houses, oak barrels); fantasy appears only as "
    "rare eerie touches. Mood: desperate and bleak, dry and weary. No text, no letters, no logos, no UI, no watermark, no frame or border."
)

STYLE_TRAINING = (
    "STYLE (same series, but this is a calm memory scene): a key-art illustration for a 2D pixel-art roguelike, rendered as a detailed "
    "pixel-art scene painting with chunky, clearly readable shapes and flat shading (no soft airbrush, no photo texture). Limited "
    "palette: soft ash grays and pale warm grays, lighter and quieter than the rest of the series (early dawn haze, faded like a "
    "remembered place); ONE warm accent only - pale amber / gold (#d67a11, #e8b858, #faeec0) - for lanterns and dawn light. No blue, "
    "no green, no purple, no red. World: grounded Renaissance-era early-gunpowder setting. Mood: still, quiet, a little wistful. "
    "No text, no letters, no logos, no UI, no watermark, no frame or border."
)

COMPOSITION = (
    "COMPOSITION (strict - this picture is a scene-transition card, the camera will fly INTO the entrance): ONE entrance stands in "
    "the exact centre of a frontal, nearly symmetrical view. The entrance OPENING (doorway / gate arch / cave mouth / passage) is "
    "centred horizontally, about 22-30% of the image width wide and about 45-60% of the image height tall, its bottom edge about "
    "80% down the image. The inside of the opening is deep near-black darkness that reads as a way in; only a faint glow far inside "
    "is allowed (described below). Nothing stands in front of or inside the opening - no people, no bars across it. The surroundings "
    "frame the entrance on both sides and above; ground in front leads the eye into it."
)

REF_NOTE = ("REFERENCE IMAGE: the attached image is an earlier piece of the same series. Match its rendering style, pixel density, "
            "palette and darkness - but paint a completely different scene as described below. Do not reuse its composition.")

KEYART = "assets/sprites/ui/keyart_{}.png"

# id: (region, nodeKind, 참고 키아트 지역, 장면, light{color, intensity, note}, 이름(한국어 메모))
DOORS = {
    "waste_battle": ("waste", "battle", "waste",
                     "SCENE: a collapsed, half-buried fortress gate standing alone on an ash-gray battlefield wasteland. A crumbling stone "
                     "archway with a broken lintel and a fallen wooden gate leaf leaning aside; broken pikes, snapped longbows and torn "
                     "banners stuck in the cracked mud in front; a few dying embers and wisps of ghost-fire drifting near the ground. "
                     "Overcast dusk sky. Inside the arch: darkness, with a very faint ember glow deep inside.",
                     {"color": "#8b4d22", "intensity": 0.25}, "무너진 성문(전장)"),
    "gate_rest": ("gate", "rest", "gate",
                  "SCENE: the stone vault of a frontier guard post built into the thick city wall at night - a low rough rock-and-masonry "
                  "cave-like hollow, like a cave mouth in the wall. Deep inside the darkness a small campfire glows warm amber, lighting "
                  "a bedroll and a hanging kettle only faintly. Firewood stacked at the sides, an old spear leaning on the rock, a "
                  "lantern hook. Soot stains above the opening.",
                  {"color": "#e8b858", "intensity": 0.75}, "초소 모닥불 동굴(쉼터)"),
    "gate_battle": ("gate", "battle", "gate",
                    "SCENE: a massive city gate tunnel in a dark stone wall at night; the iron portcullis is pulled up and hangs at the "
                    "very top of the arch (not blocking it); the long gate passage beyond is pitch black. Wagon ruts and spilled barrels "
                    "in the mud in front, braziers on both sides of the arch giving small amber glows.",
                    {"color": "#d67a11", "intensity": 0.35}, "성문 통로(전투)"),
    "outer_battle": ("outer", "battle", "outer",
                     "SCENE: the mouth of a narrow, pitch-black back alley between two leaning timber-and-plaster houses at night, the "
                     "upper floors overhanging so they almost touch above the alley, forming a dark tunnel-like passage. Broken bottles, a "
                     "toppled barrel and muddy cobbles in front; a single shuttered window leaking amber light high on one side; laundry "
                     "line across the top.",
                     {"color": "#b0611a", "intensity": 0.3}, "골목 입구(전투)"),
    "outer_elite": ("outer", "elite", "outer",
                    "SCENE: a fortified alley gate in the slum at night, a heavy timber gateway with the double doors flung open onto "
                    "darkness. Two tall war banners of deep blood-red cloth (dark rusty crimson, the only red in the picture) hang on "
                    "poles flanking the doorway, torn and stained; skulls of mugs and crossed pikes nailed above; two torches burning hot. "
                    "Feels like a challenge - a dangerous fighter waits inside.",
                    {"color": "#d65457", "intensity": 0.55}, "붉은 깃발 문(엘리트)"),
    "outer_event": ("outer", "event", "outer",
                    "SCENE: a small old wayside shrine squeezed between slum houses at night - a weathered timber shrine house with a "
                    "steep little roof, its narrow wooden door hanging open onto darkness. Offering cups, melted candle stubs and a few "
                    "coins on the worn steps, faded paper charms and dried flower strings on the door posts, one candle still flickering. "
                    "Mysterious and quiet.",
                    {"color": "#eecc78", "intensity": 0.4}, "낡은 사당 문(이벤트)"),
    "outer_shop": ("outer", "shop", "outer",
                   "SCENE: the front of a cramped slum tavern-shop at night: a heavy wooden door standing half open onto a dark interior "
                   "with a warm amber glow deep inside; a glowing iron lantern hangs on a bracket right beside the door; a hanging "
                   "tankard sign with only a carved tankard picture, crates of bottles, barrels as a counter at the side.",
                   {"color": "#e8b858", "intensity": 0.8}, "주막 문의 등불(상점)"),
    "outer_rest": ("outer", "rest", "outer",
                   "SCENE: behind the closed tavern, a low stone cellar mouth like a cave opening in an old wall at night; deep inside "
                   "the darkness a small campfire glows amber, with a resting bedroll and a hanging pot barely visible. Moss-less old "
                   "stones, a broken barrel used as a seat, a hung lantern unlit, quiet.",
                   {"color": "#e8b858", "intensity": 0.75}, "모닥불 동굴(쉼터)"),
    "brewery_battle": ("brewery", "battle", "brewery",
                       "SCENE: the dark loading-bay doorway of a huge brewery warehouse at night, a tall rectangular opening with heavy "
                       "sliding timber doors pushed aside; stacked oak barrel pyramids on both sides, a hoist chain hanging from a beam "
                       "above, copper still chimneys and smoke behind the roof, spilled glowing liquor trickling out of the doorway.",
                       {"color": "#d67a11", "intensity": 0.4}, "양조 창고 하역문(전투)"),
    "brewery_elite": ("brewery", "elite", "brewery",
                      "SCENE: an iron-banded brewery gate at night, doors flung open onto darkness, flanked by two tall war banners of deep "
                      "blood-red cloth (dark rusty crimson, the only red in the picture), stacked barrels and two blazing braziers, "
                      "copper stills looming behind. A dangerous champion waits inside.",
                      {"color": "#d65457", "intensity": 0.55}, "붉은 깃발 문(엘리트)"),
    "brewery_event": ("brewery", "event", "brewery",
                      "SCENE: an abandoned brewery storehouse with an old shrine niche built into it at night - a weathered small shrine "
                      "door of dark wood set in a brick wall, hanging open onto darkness; offering cups and a cracked cask on the steps, "
                      "faded paper charms, cobwebs, one candle stub flickering. Eerie and quiet.",
                      {"color": "#eecc78", "intensity": 0.4}, "낡은 사당 문(이벤트)"),
    "brewery_shop": ("brewery", "shop", "brewery",
                     "SCENE: a tasting-room door at the side of a brewery at night: a heavy arched wooden door half open onto a dark "
                     "interior with warm amber glow far inside, a bright iron lantern hanging on a bracket beside the door, a hanging "
                     "goblet sign (no letters), small casks and bottle crates stacked at the sides.",
                     {"color": "#e8b858", "intensity": 0.8}, "주막 문의 등불(상점)"),
    "brewery_rest": ("brewery", "rest", "brewery",
                     "SCENE: a rough cave-like opening of an old cellar in the brewery quarter at night, rock and broken brick around it; "
                     "deep inside the darkness a small campfire glows amber with a bedroll beside it; old casks and a resting pole at the "
                     "sides, quiet.",
                     {"color": "#e8b858", "intensity": 0.75}, "모닥불 동굴(쉼터)"),
    "hall_boss": ("hall", "boss", "hall",
                  "SCENE: the colossal double doors of the tyrant's banquet hall at night, at the top of wide stone steps: tall dark carved "
                  "wooden doors standing slightly open, a gap of darkness between them with festive firelight flickering deep inside; a "
                  "huge carved goblet emblem above the doors; overturned goblets, spilled wine and a sprawled drunk guest on the steps; "
                  "braziers and heavy banners on both sides. Ominous and grand.",
                  {"color": "#d67a11", "intensity": 0.6}, "연회장 큰 문(보스)"),
    "training_training": ("training", "training", None,
                          "SCENE: the gate of a quiet training yard in early dawn mist, remembered like an old memory: a simple timber "
                          "gatehouse with a small tiled roof and open wooden doors onto darkness. Beside the gate, weapon racks with "
                          "practice swords, a big sword, short daggers and a bow; a straw training dummy; raked sand ground with old "
                          "footprints; a paper lantern glowing pale gold. Clean, peaceful, a little faded.",
                          {"color": "#f4de9b", "intensity": 0.5}, "수련장 문"),
    "training_boss": ("training", "boss", None,
                      "SCENE: a remembered banquet door in the training grounds, half-faded like a memory painted in mist: tall carved "
                      "wooden double doors slightly open onto darkness, a carved goblet above, a single paper lantern; scattered empty "
                      "cups on the steps; the shapes at the edges dissolve into pale haze as if the memory is incomplete. Still and "
                      "uncanny, not violent.",
                      {"color": "#eecc78", "intensity": 0.45}, "만취 그림자 방 문(수련장 보스 연습)"),
}

# 여정 노드(birth·road·post)와 대체 규칙 — 매니페스트로 내보낸다
ALIASES = {
    "waste_birth": "waste_battle",
    "waste_road": "waste_battle",
    "gate_post": "gate_rest",
    "boss_boss": "hall_boss",
    "hall_battle": "hall_boss",
}

MAP_TRAINING = (
    "SCENE: an unrolled old paper scroll map (fills the whole image edge to edge, dark aged parchment, same parchment look as the "
    "attached reference map) of a quiet training ground compound seen from a high three-quarter bird's-eye view, drawn as small "
    "pictorial symbols in ink with a few pale gold accents. Eight small distinct training areas are spread around the scroll, "
    "connected by thin winding sandy paths, with generous empty paper space around each area for a map marker:\n"
    "1 (lower left) a sand ring with footprints and a few stepping stones - the first steps;\n"
    "2 (left middle) a small fenced yard with shields and a wooden practice wall;\n"
    "3 (top left) a dojo pavilion with a sword rack;\n"
    "4 (top centre) an open yard with a big two-handed sword planted in a stone;\n"
    "5 (top right) a narrow pavilion with daggers stuck in a wooden post;\n"
    "6 (right middle) an archery range with round straw targets;\n"
    "7 (lower right) a small storehouse with barrels and a fire pit;\n"
    "8 (bottom centre) a misty banquet-hall shape drawn faintly, half dissolved in mist, a large goblet symbol.\n"
    "In the middle of the scroll a small gatehouse where the paths start. Keep a lot of open paper. No text, no letters, no "
    "numbers, no compass labels, no legend."
)

MAP_STYLE = (
    "STYLE: a hand-drawn diary map on dark, dirty sepia parchment, ink line drawings with flat simple shading, chunky readable "
    "pixel-art-like line work, muted sepia browns and grays, a few pale amber/gold accents only. No other hues. No text, no letters, "
    "no numbers, no UI, no watermark."
)
