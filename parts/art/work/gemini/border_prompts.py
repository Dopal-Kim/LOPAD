#!/usr/bin/env python3
"""53라운드 Q6 — 1층 나머지 4지역 테두리 + 5지역 골목 입구 조각 프롬프트 (단일 기준).

python3 parts/art/work/gemini/border_prompts.py   → border_<id>/style_border.txt, prompt_<band>.txt, prompt_<band>_full.txt
실제 전송문 = style + 빈 줄 + 띠 프롬프트 (외곽 시범과 같은 순서). 연대·작품 이름·글자 없음.
참고 이미지 순서(띠): 1 = keyart_<id> 채택안(문체 주 참고), 2 = concept_v2_<id> 채택안(카메라만),
  3 = 북: border_outer/raw_north_a(축척만) / 서·동·남·조각: 그 지역 raw_north_a(축척·문체 이어 받기), 4 = 서 띠(남·조각).
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

KEYART = {"outer": "keyart_outer/raw_a.jpg", "waste": "keyart_waste/raw_a.jpg", "gate": "keyart_gate/raw_a.jpg",
          "brewery": "keyart_brewery/raw_b.jpg", "hall": "keyart_hall/raw_b.jpg"}
CONCEPT = {"outer": "concept_v2_outer/raw_a.jpg", "waste": "concept_v2_waste/raw_b.jpg", "gate": "concept_v2_gate/raw_a.jpg",
           "brewery": "concept_v2_brewery/raw_b.jpg", "hall": "concept_v2_hall/raw_b.jpg"}

STYLE_HEAD = ("REFERENCE IMAGES: Image 1 is the key art of this game region. It is the PRIMARY reference: match its rendering style "
              "exactly - a dark, grim, detailed pixel-art scene painting with chunky, clearly readable shapes and flat shading "
              "(no soft airbrush, no photo texture, no film grain), {look}, the same night mood and darkness. "
              "Image 2 is only a CAMERA reference: it shows the in-game camera - an orthographic top-down three-quarter view looking "
              "down from the south at about 40 degrees, no vanishing point, vertical edges stay vertical, every structure shows its "
              "south-facing front and its top surface or roof sloping away. Do not copy image 2's composition or its brighter flat look; "
              "take only its camera angle.")
STYLE_PAL = ("PALETTE: near-black charcoal and cold ash greys carry the whole image, dark umber wood and earth; ONE warm accent only - "
             "amber / ember orange to pale gold (#8b4d22, #d67a11, #e8b858, #faeec0) - used only for {lights} and their small glow. "
             "No other hues: no blue, no green, no purple, no red, no copper-orange metal (metal is dark iron grey).")
STYLE_LIGHT = ("LIGHTING: dim, even, cold night light on all surfaces (this art will be lit again by the game engine). Light sources "
               "{lightdesc} glow, but do NOT throw big bright pools onto walls or the ground. Keep stone, plaster and earth mid-dark grey, "
               "never bright white.")
STYLE_TAIL = ("STRICT: no people, no characters, no animals, no corpses. No text, no letters, no numbers, no logos, no UI, no watermark, "
              "no frame or border line. Fill the whole canvas edge to edge.")

REGION = {
    "waste": dict(
        look="the same cracked dry earth and churned dark mud, broken pikes and swords stuck in the ground at angles, torn banners "
             "hanging from leaning poles, dented helmets and round shields half buried, broken wooden carts, small ember-coloured "
             "soul flames drifting over the fallen gear, a heavy overcast sky",
        lights="soul flames (will-o'-the-wisps), a campfire, a burning cart wreck and tiny distant windows",
        lightdesc="(small pale-amber soul flames, one campfire, a smouldering cart)",
        world="WORLD: grounded early-gunpowder battlefield wasteland outside the walled liquor empire \"Zan\": "
              "abandoned siege earthworks, palisades of sharpened stakes, a ruined farmhouse, scattered weapons. Desolate and bleak."),
    "gate": dict(
        look="the same massive grim stone curtain wall of big dark dressed blocks, square towers with battlements, an iron portcullis "
             "half raised with warm amber light spilling from the gate tunnel, tattered banners with a simple goblet emblem, torches "
             "on the towers, black moat water, a churned muddy road, wagons loaded with oak barrels",
        lights="the gate tunnel light, torches, a toll-table lantern and their small glow",
        lightdesc="(the gate tunnel glow - the brightest - and small torches and lanterns)",
        world="WORLD: grounded early-gunpowder fortress gate of the liquor empire \"Zan\": toll stations, barrel "
              "wagons, barricades, guard posts. Grim, heavy, oppressive."),
    "brewery": dict(
        look="the same huge dark iron pot stills and boilers with open furnace doors glowing amber beneath them, tangled pipes and "
             "valves, soot-blackened brick, wooden gantries and cranes hauling barrels on chains, pyramids of enormous oak casks, "
             "steam lit amber from below, a stone canal of glowing amber liquor, a smoky sky",
        lights="furnace mouths, the liquor canal surface, small lanterns",
        lightdesc="(furnace mouths - the brightest - the glowing liquor canal and small lanterns)",
        world="WORLD: grounded early-gunpowder distillery district of the liquor empire \"Zan\": brick still houses, "
              "furnaces, cask yards, cranes, pipes, liquor canals. Grimy, hot, oppressive."),
    "hall": dict(
        look="the same open-air banquet terrace of the ruler at night: dark polished stone, a stone balustrade with the city "
             "rooftops far below, heavy dark drapes with a simple goblet emblem, a tall throne built from stacked oak casks, a big "
             "brazier fire behind it as back light, guttering candelabras, spilled liquor, a dark smoky sky",
        lights="the brazier fire, candle flames, tiny distant city windows and spilled liquor glints",
        lightdesc="(the brazier fire - the brightest - candelabras and tiny far city windows)",
        world="WORLD: grounded early-gunpowder palace terrace of the drunken ruler of the liquor empire \"Zan\": "
              "decadent, wrecked after an endless feast, menacing and grotesque yet darkly comic."),
}

SCALE3 = ("SCALE: Image 3 is a strip from another arena of this same game, given ONLY for scale and pixel density: match its pixel "
          "density and object scale exactly (same doorway height, same barrel size, same storey height) but take none of its "
          "content or buildings.")
CONT3 = ("Image 3 is the north border strip already painted for THIS arena: match its pixel density, object scale (doorway and barrel "
         "size), darkness and amber accent exactly.")
SIDE_CAM = ("CAMERA: the in-game three-quarter top-down view from the south (image 2): every structure shows its FRONT face facing "
            "DOWN toward the bottom of the image, with its top or roof above it sloping away (up the image). Things further north "
            "appear higher in the strip, and a nearer (lower) object overlaps the bottom of the next one. No vanishing point.")
SOUTH_HEAD = ("TASK: Images 3 and 4 are strips already painted for this arena (north border, and the west side seen from the in-game "
              "camera). Match their crisp, chunky pixel-art rendering exactly - clean readable shapes, flat shading, NO smears, NO fog, "
              "NO haze. Paint ONE extremely wide, low horizontal strip: the SOUTH BORDER of the arena, the FOREGROUND nearest to the "
              "camera. The arena floor lies just ABOVE this image.")
SOUTH_TAIL = ("TOP EDGE: the top line of the foreground is almost perfectly straight and horizontal at about one fifth of the image "
              "height from the top, along the WHOLE width, continuous, with no gaps; only posts, stakes or chimneys poke above it. "
              "Above that line: plain flat dark charcoal (it will be cut away).\n"
              "VALUES: this foreground is a bit darker than images 3 and 4 but every shape stays readable; a faint cold grey rim light "
              "on the upper edges facing the arena.\n"
              "TILING: the strip repeats horizontally - make the far left and far right ends similar and at the same height.")
NORTH_TAIL = ("GROUND LINE: the bottom of the front structures sits on a perfectly straight, horizontal ground line at the very bottom "
              "edge of the image (a thin strip of ground at most). Nothing sticks out below it.\n"
              "TILING: the strip will repeat horizontally - make the far left and far right ends similar and at the same height so they "
              "can be joined.")


def side_tail(side):
    edge = "right" if side == "west" else "left"
    return ("{E} EDGE: {wall} runs perfectly straight and vertical along the full {e} edge (its top surface visible as a narrow strip), "
            "separating this strip from the arena floor. Nothing crosses it.\n"
            "TILING: the strip will repeat vertically - make the top end and the bottom end similar.").format(E=edge.upper(), e=edge, wall="{wall}")


BANDS = {
    # ------------------------------------------------------------------ 황무지
    "waste": {
        "north": "TASK: paint ONE very wide horizontal strip that is the NORTH BORDER of a top-down action-game arena on the battlefield "
                 "wasteland outside the liquor city \"Zan\" at night. The arena floor (open cracked dry earth) lies just BELOW this "
                 "image and is not painted here.\n"
                 "CONTENT (left to right, one continuous front): a tall EARTHEN EMBANKMENT of old siege works - its south-facing front "
                 "face fully visible: cut layers of packed dark earth with roots and stones, held in places by rotten wooden revetment "
                 "planks - about two doorways high; along its top a PALISADE of SHARPENED WOODEN STAKES, bundled in clusters and leaning "
                 "out toward the viewer; set into the embankment, the FRONT of a RUINED ABANDONED FARMHOUSE (cracked stone walls, a black "
                 "empty doorway, broken shutters, a collapsed roof with bare broken rafters); broken pikes, spears and swords stuck in the "
                 "bank at angles; torn banners on leaning poles; dented helmets and round shields half buried at the foot of the bank; a "
                 "toppled supply cart with a broken wheel; four or five small pale-amber SOUL FLAMES (will-o'-the-wisps: small teardrop "
                 "flames trailing ember sparks) hovering just above helmets and shields; one small campfire.\n"
                 "DEPTH: behind the embankment the battlefield continues in two or three darker, hazier ridges with more stuck pikes and "
                 "banners; far on the horizon the low dark silhouette of a walled city with a few tiny amber windows and thin smoke columns. "
                 "A dark overcast sky only in the top fifth of the image.\n" + NORTH_TAIL + "\n" + SCALE3,
        "west": "TASK: " + CONT3 + " Now paint ONE tall vertical strip that is the WEST (left) BORDER of the same top-down arena on the "
                "battlefield wasteland. The open cracked-earth arena floor lies just to the RIGHT of this image and is not painted here.\n"
                + SIDE_CAM + "\n"
                "CONTENT (top to bottom): abandoned siege works seen this way - a muddy trench line with timber revetments; rows of "
                "sharpened stake palisades; a burnt-out shell of a small hut (front wall with an empty doorway, broken roof beams); a "
                "cold cannon on a broken carriage; heaps of broken weapons, dented helmets and round shields; tattered banners on leaning "
                "poles; puddles of dark mud; two or three small pale-amber soul flames hovering over helmets; one small campfire.\n"
                + side_tail("west").format(wall="a low wall of stacked SANDBAGS and rough stones"),
        "east": "TASK: " + CONT3 + " Now paint ONE tall vertical strip that is the EAST (right) BORDER of the same top-down arena on the "
                "battlefield wasteland. The open cracked-earth arena floor lies just to the LEFT of this image and is not painted here.\n"
                + SIDE_CAM + "\n"
                "CONTENT (top to bottom): a looted supply dump of the dead army seen this way - a smouldering wreck of a covered supply "
                "wagon with small flames (the main light), scattered crates, broken barrels and sacks; a collapsed army tent; a mound of "
                "fresh earth with swords planted in it as grave markers; another short earth bank with leaning stakes; a broken wooden "
                "watch platform; spears stuck in the mud; two or three small pale-amber soul flames over helmets and shields.\n"
                + side_tail("east").format(wall="a low wall of stacked SANDBAGS and rough stones"),
        "south": SOUTH_HEAD + "\n"
                 "CONTENT: one CONTINUOUS low rampart of earth and stacked SANDBAGS seen from above and behind (three-quarter top-down "
                 "from the south, like image 4) - its top runs along the top of the strip; on it, at intervals, short clusters of "
                 "sharpened stakes, a broken pike, a dented helmet, a round shield leaning on the bags, a torn banner on a short pole lying "
                 "flat; below it (nearer the camera) dark churned mud with wheel ruts. At most two tiny amber soul flames in the whole "
                 "strip.\n" + SOUTH_TAIL,
        "doors": None,   # 아래 DOORS
    },
    # ------------------------------------------------------------------ 성문
    "gate": {
        "north": "TASK: paint ONE very wide horizontal strip that is the NORTH BORDER of a top-down action-game arena in front of the "
                 "great gate of the liquor city \"Zan\" at night. The arena floor (a muddy approach yard) lies just BELOW this image and "
                 "is not painted here.\n"
                 "CONTENT (one continuous front): a massive grim stone CURTAIN WALL - its south-facing front face fully visible: big dark "
                 "dressed stone blocks, arrow slits, a sloped stone plinth at its foot, battlements and a walkway along its top - the wall "
                 "face is about THREE times as tall as a doorway. In the exact CENTER a fortified GATEHOUSE flanked by two square TOWERS "
                 "that rise higher, with battlements and torches; the gate arch has a HALF-RAISED IRON PORTCULLIS and warm amber light "
                 "fills the gate tunnel (the brightest spot of the image). Along the rest of the wall: two more smaller square towers near "
                 "the ends, stone buttresses, tattered banners with a simple goblet emblem hanging from the battlements, torches in iron "
                 "brackets, a small iron-bound postern door. At the foot of the wall: stacked oak barrels, crates, sacks, a wooden "
                 "toll-booth hut with a lantern, an X-shaped wooden barricade, a stone horse trough.\n"
                 "DEPTH: above and behind the wall top, the roofs, towers and chimneys of the city rise in two hazy darker layers with thin "
                 "smoke. A dark overcast night sky only in the top eighth of the image.\n" + NORTH_TAIL + "\n" + SCALE3,
        "west": "TASK: " + CONT3 + " Now paint ONE tall vertical strip that is the WEST (left) BORDER of the same top-down arena in front "
                "of the city gate. The muddy arena floor lies just to the RIGHT of this image and is not painted here.\n" + SIDE_CAM + "\n"
                "CONTENT (top to bottom): the outer guard yard along the city wall seen this way - a lower stone guard wall with "
                "crenellations whose walkway runs up the strip; a squat stone guardhouse front with a heavy door and one lit window; a "
                "timber stable shed with a cart; racks of halberds; a stone stair climbing to the wall walk; a well; stacks of barrels and "
                "sacks for the toll; torches in iron brackets.\n"
                + side_tail("west").format(wall="a low dark stone wall with a cut-stone coping"),
        "east": "TASK: " + CONT3 + " Now paint ONE tall vertical strip that is the EAST (right) BORDER of the same top-down arena in front "
                "of the city gate. The muddy arena floor lies just to the LEFT of this image and is not painted here.\n" + SIDE_CAM + "\n"
                "CONTENT (top to bottom): the toll queue lane seen this way - a muddy road running up the strip with deep wheel ruts and "
                "a line of waiting WAGONS loaded with oak barrels (no horses, no people); a small wooden toll booth with a counter and a "
                "lantern; a timber watchtower on stilts with a torch; X-shaped wooden barricades; a stone horse trough; crates and sacks; "
                "a short section of the moat bank with black water at the far side of the strip.\n"
                + side_tail("east").format(wall="a low dark stone wall with a cut-stone coping"),
        "south": SOUTH_HEAD + "\n"
                 "CONTENT: the MOAT in front of the fortress seen from above (three-quarter top-down from the south, like image 4): along "
                 "the top of the strip runs the cut-stone NORTH BANK of the moat (a continuous low stone coping, its top visible); below "
                 "it, a continuous band of still BLACK MOAT WATER with faint ripples and a few faint amber reflections of torches; below "
                 "that (nearest the camera) the muddy SOUTH BANK with broken stakes, reeds-like dry stalks, a half-sunken barrel and a "
                 "broken cart wheel.\n" + SOUTH_TAIL,
    },
    # ------------------------------------------------------------------ 양조 구역
    "brewery": {
        "north": "TASK: paint ONE very wide horizontal strip that is the NORTH BORDER of a top-down action-game arena in the distillery "
                 "district of the liquor city \"Zan\" at night. The arena floor (a yard of worn wet flagstones) lies just BELOW this image "
                 "and is not painted here.\n"
                 "CONTENT (left to right, one continuous front): a long two-storey soot-blackened BRICK DISTILLERY - its south-facing "
                 "front wall fully visible - with TWO big arched FURNACE MOUTHS at ground level, iron doors open, glowing amber inside "
                 "(the brightest spots); thick iron pipes, valves and pressure gauges running along the wall; small barred windows, two "
                 "dimly lit; on its roof, seen from above behind the front wall, TWO HUGE dark iron POT STILLS with domed lids and "
                 "swan-neck pipes, and tall brick chimneys with dark smoke; beside the distillery a wooden GANTRY CRANE with a barrel "
                 "hanging on a chain; a wooden loading platform; at the foot of the wall: barrel stacks, coiled ropes, a hand cart, a hot "
                 "iron cauldron, steam vents with steam lit amber from below; small hanging lanterns.\n"
                 "DEPTH: behind it more still houses, chimneys, cranes and boiler towers rise in two hazy darker layers with smoke. A dark "
                 "smoky night sky only in the top eighth of the image.\n" + NORTH_TAIL + "\n" + SCALE3,
        "west": "TASK: " + CONT3 + " Now paint ONE tall vertical strip that is the WEST (left) BORDER of the same top-down arena in the "
                "distillery district. The flagstone arena floor lies just to the RIGHT of this image and is not painted here.\n"
                + SIDE_CAM + "\n"
                "CONTENT (top to bottom): the cask yard seen this way - big PYRAMIDS of stacked oak casks; a wooden gantry CRANE with a "
                "cask hanging on a chain; squat iron storage tanks; a small boiler house with a glowing furnace door; a steam vent with "
                "steam; pipes running along the ground; coiled ropes, wooden pallets, a hand cart; a narrow lane between the stacks.\n"
                + side_tail("west").format(wall="a low soot-blackened brick kerb wall"),
        "east": "TASK: " + CONT3 + " Now paint ONE tall vertical strip that is the EAST (right) BORDER of the same top-down arena in the "
                "distillery district. The flagstone arena floor lies just to the LEFT of this image and is not painted here.\n"
                + SIDE_CAM + "\n"
                "CONTENT (top to bottom): a stone LIQUOR CANAL runs straight down the middle of the strip, parallel to the left edge, "
                "full of slowly flowing liquor that glows warm amber with foam and glints; it has cut-stone banks; one narrow wooden plank "
                "footbridge crosses it; beyond the canal (right side of the strip) pot stills with furnace mouths, stacked casks and "
                "pipes; on the near bank a few casks and a sluice gate with a wheel.\n"
                + side_tail("east").format(wall="a low soot-blackened brick kerb wall"),
        "south": SOUTH_HEAD + "\n"
                 "CONTENT: one CONTINUOUS row of low soot-stained shed roofs and the TOPS of huge oak vats seen from above and behind "
                 "(three-quarter top-down from the south, like image 4) - roofs and vat rims touch, no gaps; thick iron pipes run along "
                 "the top edge; variety: a brick chimney stub, a steam vent, a stack of casks on a flat roof, a coiled rope, a crane beam "
                 "lying across. At most two tiny amber points (a vent glow) in the whole strip.\n" + SOUTH_TAIL,
    },
    # ------------------------------------------------------------------ 연회장 (보스)
    "hall": {
        "north": "TASK: paint ONE very wide horizontal strip that is the NORTH BORDER of a top-down action-game boss arena: the open-air "
                 "banquet terrace of the drunken ruler of the liquor city \"Zan\" at night. The arena floor (big polished dark stone "
                 "slabs) lies just BELOW this image and is not painted here.\n"
                 "CONTENT (strictly symmetric, centered): in the exact CENTER of the strip a wide stepped stone DAIS, its three front steps "
                 "fully visible; on it a tall THRONE built from stacked oak casks, EMPTY - nobody sits on it; right behind the throne a big "
                 "iron BRAZIER with a roaring fire (the brightest spot, back-lighting the throne); spilled liquor running down the dais "
                 "steps, a few overturned goblets and a tipped cask on the steps. On both sides of the dais: tall dark stone PILLARS with "
                 "heavy dark DRAPES bearing a simple goblet emblem hanging between them; tall candelabras with guttering candles; then, "
                 "toward both ends, a stone BALUSTRADE with the CITY rooftops far below and beyond it (tiny amber windows, thin smoke).\n"
                 "DEPTH: behind the dais and pillars, the night city far below and far away in hazy layers; a dark smoky sky in the top "
                 "fifth.\n" + NORTH_TAIL + "\n" + SCALE3,
        "west": "TASK: " + CONT3 + " Now paint ONE tall vertical strip that is the WEST (left) BORDER of the same top-down boss arena on "
                "the ruler's banquet terrace. The polished stone arena floor lies just to the RIGHT of this image and is not painted here.\n"
                + SIDE_CAM + "\n"
                "CONTENT (top to bottom): the terrace edge seen this way - inside the balustrade, a narrow strip of terrace with tall stone "
                "pillars draped with heavy dark goblet-emblem drapes, tall candelabras, an overturned banquet bench, tipped casks and "
                "bottles; beyond the balustrade (left part of the strip) a sheer drop into darkness with the CITY rooftops far below - "
                "tiny dark roofs, a few tiny amber windows, thin smoke.\n"
                + side_tail("west").format(wall="a stone BALUSTRADE (balusters and a heavy top rail)"),
        "east": "TASK: " + CONT3 + " Now paint ONE tall vertical strip that is the EAST (right) BORDER of the same top-down boss arena on "
                "the ruler's banquet terrace. The polished stone arena floor lies just to the LEFT of this image and is not painted here.\n"
                + SIDE_CAM + "\n"
                "CONTENT (top to bottom): the terrace edge seen this way - inside the balustrade, a serving corner: a sideboard with "
                "stacked goblets and bottles, a row of casks with taps, a tall candelabra, a heavy drape on a pillar, a fallen tray with "
                "spilled liquor; beyond the balustrade (right part of the strip) a sheer drop into darkness with the CITY rooftops far "
                "below - tiny dark roofs, a few tiny amber windows, thin smoke.\n"
                + side_tail("east").format(wall="a stone BALUSTRADE (balusters and a heavy top rail)"),
        "south": SOUTH_HEAD + "\n"
                 "CONTENT: one CONTINUOUS stone BALUSTRADE seen from above and behind (three-quarter top-down from the south, like image "
                 "4): its heavy top rail runs along the top of the strip; below it the row of balusters; below that (nearest the camera) a "
                 "sheer drop into darkness with the night city far below - tiny dark rooftops and only two or three tiny amber windows. "
                 "Every few metres a square stone post with a stone urn.\n" + SOUTH_TAIL,
    },
}

# 골목 입구 조각 (지역당 1회, 16:9 한 장에 세 패널)
DOOR_HEAD = ("TASK: paint a sheet of THREE SEPARATE PANELS side by side on a flat pure black background, separated by wide pure black "
             "gaps (each gap at least one tenth of the image width); nothing crosses the gaps. These are overlay pieces for doorways "
             "of the same top-down arena: {ctx} Match their pixel density, object scale (doorway and barrel size), darkness and amber "
             "accent exactly.\n")
DOOR_PANELS = {
    "outer": ("Image 3 is its north street front, image 4 its west side seen from the in-game camera.",
              "PANEL 1 (left, tall, about one third of the width, full height): an ALLEY ENTRANCE in the north street front: two "
              "half-timbered house fronts with a narrow dark ALLEY between them, a stone ARCHWAY over the alley mouth, wet cobbles "
              "leading north into darkness, a hanging lantern on the arch; the bottom of the house fronts sits on a straight ground "
              "line at the bottom of the panel.",
              "PANEL 2 (middle): a SIDE STREET ENTRANCE in the west side, in the in-game camera: the low kerb wall is interrupted by a "
              "gap; a narrow cobbled street leads away to the LEFT into darkness; along the far (upper) side of the street, small house "
              "fronts facing down; along the near (lower) side, dark roofs; a lantern on a bracket at the corner.",
              "PANEL 3 (right): a SOUTH EXIT in the foreground row of roofs seen from above and behind: a gap in the roof row where a "
              "worn stone STAIR goes DOWN toward the camera between two roofs, a broken handrail, darkness below."),
    "waste": ("Image 3 is its north embankment strip, image 4 its west side seen from the in-game camera.",
              "PANEL 1 (left, tall, about one third of the width, full height): a BREACH in the north earth embankment: the embankment "
              "front is cut through by a muddy track that climbs north into darkness; on both sides the cut earth face and the stake "
              "palisade; a broken wooden gate of lashed stakes hangs open; a soul flame hovers by the gate; the foot of the embankment "
              "sits on a straight ground line at the bottom of the panel.",
              "PANEL 2 (middle): a GAP in the west sandbag wall, in the in-game camera: the low sandbag wall is interrupted; a muddy "
              "track with wheel ruts leads away to the LEFT into darkness between stake palisades; a leaning banner pole at the corner.",
              "PANEL 3 (right): a SOUTH EXIT in the foreground earth rampart seen from above and behind: a gap in the sandbag rampart "
              "where a muddy track goes DOWN toward the camera between the bags, broken stakes on both sides."),
    "gate": ("Image 3 is its north curtain wall strip, image 4 its west side seen from the in-game camera.",
             "PANEL 1 (left, tall, about one third of the width, full height): a SIDE GATE in the north curtain wall: a smaller arched "
             "gate with an iron portcullis raised, warm amber light in a short tunnel, a torch on each side, the big stone blocks of the "
             "wall around it; the wall foot sits on a straight ground line at the bottom of the panel.",
             "PANEL 2 (middle): a GAP in the west guard wall, in the in-game camera: the low stone wall is interrupted by an opening with "
             "two stone gate posts and an open iron-bound wooden gate; a muddy lane leads away to the LEFT into darkness; a torch on one "
             "post.",
             "PANEL 3 (right): a DRAWBRIDGE over the moat seen from above and behind (south exit): the cut-stone moat bank along the top, "
             "a wooden drawbridge of heavy planks with iron chains crossing the black water DOWN toward the camera."),
    "brewery": ("Image 3 is its north distillery strip, image 4 its west side seen from the in-game camera.",
                "PANEL 1 (left, tall, about one third of the width, full height): a CART ENTRANCE in the north brick distillery wall: a "
                "big brick arch with heavy wooden double doors swung open, a dim warm glow and casks inside, a hanging lantern, pipes "
                "running over the arch; the wall foot sits on a straight ground line at the bottom of the panel.",
                "PANEL 2 (middle): a GAP in the west cask yard, in the in-game camera: the low brick kerb wall is interrupted; a narrow "
                "lane leads away to the LEFT into darkness between tall stacks of casks; a lantern on a post at the corner.",
                "PANEL 3 (right): a SOUTH EXIT in the foreground shed roofs seen from above and behind: a gap in the roofs where an iron "
                "grated stair goes DOWN toward the camera between two vats, pipes on both sides."),
    "hall": ("Image 3 is its north dais strip, image 4 its west side seen from the in-game camera.",
             "PANEL 1 (left, tall, about one third of the width, full height): an ARCHED DOORWAY between two stone pillars of the "
             "terrace: heavy dark drapes pulled aside, a dark corridor with a faint warm glow, a candelabra on each side; the pillar "
             "bases sit on a straight ground line at the bottom of the panel.",
             "PANEL 2 (middle): a GAP in the west balustrade, in the in-game camera: the balustrade is interrupted by two square stone "
             "posts with urns, and a wide stone STAIR goes DOWN to the LEFT out of view.",
             "PANEL 3 (right): the SOUTH ENTRANCE STAIR seen from above and behind: a gap in the stone balustrade between two square "
             "posts with urns, a wide stone STAIR going DOWN toward the camera into darkness."),
}
DOOR_TAIL = ("Each panel's outer area fades to pure black at its left and right sides. Keep the openings dark (they lead away into "
             "darkness); only small lights glow.")


def style(rid):
    if rid == "outer":
        return open(os.path.join(HERE, "border_outer/style_border.txt"), encoding="utf-8").read().strip().replace("Renaissance-era ", "")
    r = REGION[rid]
    return "\n".join([STYLE_HEAD.format(look=r["look"]), STYLE_PAL.format(lights=r["lights"]),
                      STYLE_LIGHT.format(lightdesc=r["lightdesc"]), r["world"], STYLE_TAIL])


def doors_prompt(rid):
    ctx, p1, p2, p3 = DOOR_PANELS[rid]
    return "\n".join([DOOR_HEAD.format(ctx=ctx), p1, p2, p3, DOOR_TAIL])


def write(rid):
    d = os.path.join(HERE, f"border_{rid}")
    os.makedirs(d, exist_ok=True)
    st = style(rid)
    if rid != "outer":
        open(os.path.join(d, "style_border.txt"), "w", encoding="utf-8").write(st + "\n")
        bands = {k: v for k, v in BANDS[rid].items() if v}
    else:
        bands = {}
    bands["doors"] = doors_prompt(rid)
    for k, v in bands.items():
        open(os.path.join(d, f"prompt_{k}.txt"), "w", encoding="utf-8").write(v + "\n")
        open(os.path.join(d, f"prompt_{k}_full.txt"), "w", encoding="utf-8").write(st + "\n\n" + v + "\n")


if __name__ == "__main__":
    for rid in ("outer", "waste", "gate", "brewery", "hall"):
        write(rid)
    print("ok")
