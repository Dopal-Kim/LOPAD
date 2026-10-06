"""61 단계 5 개성 카드 그림 65장 목록 — 파일 id · 무기 · 이름 · 한 줄 콘셉트(요청 노트 §2) · Gemini 장면 프롬프트(영문).

공명 9장은 같은 무기·같은 태그 개성 2장이 엮이는 그림(pair = 엮이는 개성 id).
"""

STYLE = (
    "Square game-card illustration (1:1) for a dark modern 2D pixel-art roguelike action game. "
    "ONE single frozen moment of combat, seen from a high three-quarter top-down camera (quarter view, like the game itself), "
    "key light from the upper left. CLOSE framing: the figures and the effect are LARGE and fill most of the square "
    "(the main figures are about 70-80% of the image height); only 2-3 figures. "
    "Chunky, bold, high-contrast pixel-art shapes that stay readable when shrunk to a tiny 128x128 pixel icon: big clear "
    "silhouettes with thick near-black outlines, flat cel shading with one shadow and one highlight step, no tiny details, "
    "no texture noise, no soft airbrush. The figures stand on a SMALL, low irregular patch of MEDIUM-GREY stone flagstones "
    "(clearly lighter than the near-black hero, so he stands out). EVERYTHING outside the figures, effects and that floor patch is "
    "a perfectly flat, solid pure magenta (#FF00FF) background - no gradient, no cast shadow and no glow spilling onto the magenta. "
    "Never use magenta or pink inside the scene. No text, no letters, no numbers, no UI, no key caps, no card frame, no border, "
    "no watermark."
)

CAST = (
    "CAST (see the reference sheet - match these designs): THE HERO is a gaunt, hunched war-ghost revenant made of a cracked "
    "dark charcoal-ash shell, glowing amber soul-fire cracks across chest and head, one small burning amber eye, a dark featureless "
    "face, shards of broken armour, bandaged hands, a small leather pouch at the hip; no clothes, no hat, no cape, no hair. "
    "ENEMIES are grim Renaissance-era foot soldiers: big shield-bearers in brown leather with a tall flat-topped iron bucket helmet "
    "and a war hammer, archers in a pale shirt with a black tricorn hat, a liquor peddler in a wide straw hat with a pack of "
    "bottles and a lantern, a porter hauling oak barrels. Setting details: dark stone tavern-fortress floor, spilled amber liquor "
    "puddles, oak barrels, grey stone pillars and walls."
)

WEAPON = {
    "katana": (
        "WEAPON AND COLOUR LANGUAGE OF THIS CARD SET (katana): the hero wields a slender curved katana with a cold polished "
        "blue-grey steel blade and one bright silver-white edge line, black lacquered scabbard. Its cuts are razor-thin, "
        "precise silver-white light lines and thin arcs (never thick brush strokes, never fire on the blade). Palette: cold ash "
        "and blue-grey steel, silver-white light, pale moonlight blue (#c8d8f0) only for moon clones and moon light; amber only "
        "as tiny embers, the hero's cracks and spilled liquor."
    ),
    "greatsword": (
        "WEAPON AND COLOUR LANGUAGE OF THIS CARD SET (greatsword): the hero wields a huge, heavy, notched dark-iron greatsword "
        "as tall as himself. Its impacts are brutal and heavy: shattered stone, ground cracks, dust clouds, shock rings. "
        "Palette: dark iron and charcoal greys plus HOT amber-orange (#d67a11, #e2a33c, #f4de9b) glowing like molten metal in "
        "the blade cracks, ground fissures and impact flashes. No blue, no cold colours."
    ),
    "dagger": (
        "WEAPON AND COLOUR LANGUAGE OF THIS CARD SET (dagger): the hero wields a short curved karambit claw-dagger in a reverse "
        "grip, dark ash-steel blade whose inner edge glows as a thin amber ember line. Its strikes are fast, thin, needle-like "
        "curved claw streaks ending in small X-shaped sparks; shadow techniques are ink-black smoky silhouettes and ink pools; "
        "brands are glowing dark-red claw-mark sigils (#b04848) burned on the enemy body. Palette: ink black, ash grey, ember "
        "amber claws, a little dark red."
    ),
    "bow": (
        "WEAPON AND COLOUR LANGUAGE OF THIS CARD SET (bow): the hero wields a tall dark weathered-wood longbow and shoots long "
        "arrows with bone-white fletching; flying arrows leave long straight thin pale-gold light streaks (#f4de9b). Bindings "
        "and nets are pale steel-blue lines (#9ab0d8). Palette: dark wood brown, bone white, ash grey, pale-gold arrow light; "
        "amber-orange fire only where liquor burns."
    ),
}

# (id, weapon, name, concept_ko, scene_en, pair)
CARDS = [
    # ---- katana ----
    ("katana_k_shadowThrust", "katana", "그림자 찌르기", "쓰러지는 적 뒤로 그림자 칼끝이 다음 적의 가슴을 꿰뚫는다",
     "On the left a shield soldier collapses forward, defeated. Out of his falling body's shadow an ink-black shadow copy of the hero lunges to the right and pierces the chest of a second soldier with a long, thin, straight silver-white thrust line ending in a small bright star spark. The real hero stands at the far left after a thrust, katana extended.", None),
    ("katana_k_edgeLift", "katana", "칼등 띄우기", "휘청이는 병사를 칼등으로 쳐올려 공중에 띄운 순간",
     "The hero, low on the left, swings the katana upward with the BACK of the blade; a staggering shield soldier is knocked high into the air above the right side of the frame, tumbling, his bucket helmet flying off. A thin silver arc trail rises from the floor to the soldier; a little dust puff on the floor below.", None),
    ("katana_k_parryShove", "katana", "흘려 밀기", "칼을 비스듬히 대어 흘린 적이 돌기둥에 처박힌다",
     "The hero on the left holds the katana slanted in a parry, a thin silver half-moon shock curve around the blade. The deflected shield soldier is shoved backwards and slams into a grey stone pillar on the right, the pillar cracking with stone chips flying.", None),
    ("katana_k_bladeBind", "katana", "칼 감기", "칼날이 상대 창대를 감아 앞으로 끌어당긴다",
     "Side view, two figures only: the hero on the left blocks with his katana held across, and the katana blade is wrapped around the long wooden shaft of a pikeman's pike by a bright, clearly visible silver-white SPIRAL light coil; the hero yanks the pike toward himself and the off-balance pikeman on the right is pulled forward, stumbling, feet off balance.", None),
    ("katana_k_shadowVault", "katana", "그림자 넘기", "내리찍는 칼끝을 스치며 적의 등 뒤로 넘어가는 실루엣",
     "A big shield soldier's war hammer smashes down into the floor (crack, dust) exactly where the hero was. The hero, as an ink-black smoky silhouette, vaults in a smooth arc over the soldier's shoulder and lands behind his back, katana drawn for a slash; a thin silver arc traces the vault path.", None),
    ("katana_k_issenBack", "katana", "물러서며 베기", "일섬 끝에 뒤로 미끄러지며 그리는 둥근 칼 궤적",
     "The hero slides backward on one knee in the centre, the katana drawing a perfect thin silver-white circle around him on the floor; two soldiers at the edges of the circle reel back, cut.", None),
    ("katana_k_iaiWave", "katana", "발도풍", "칼집에서 뽑힌 칼끝에서 초승달 바람이 날아간다",
     "The hero crouches low on the left, drawing the katana from the black scabbard in one stroke; a large pale silver-blue crescent-moon wind blade flies off the blade tip to the right toward a soldier.", None),
    ("katana_k_iaiChain", "katana", "연쇄 발도", "쓰러지는 적을 지나 다음 적 앞으로 미끄러지는 낮은 자세",
     "Low sliding stance: the hero glides to the right close to the floor with the katana held low behind him, leaving a long low streak of grey afterimages; behind him on the left a soldier falls, cut; ahead on the right the next soldier is just about to be reached.", None),
    ("katana_bloodGale", "katana", "피바람", "회전 베기의 핏빛 고리가 한 바퀴 더 감긴다",
     "The hero spins in the centre in a whirlwind slash; a dark blood-red (#b04848) ring of wind wraps around him twice like a spiral gale, red droplets flying, a soldier thrown off the ring.", None),
    ("katana_liquorWhirl", "katana", "술 회오리", "바닥의 술이 칼을 따라 감겨 불 회오리가 된다",
     "The hero spins in the centre with the katana extended; spilled amber liquor from the floor is sucked up into a spiral that wraps around the blade and ignites into a ring-shaped amber-orange fire whirlwind around him.", None),
    ("katana_k_sparkCleave", "katana", "불똥 내려베기", "내려친 칼이 돌바닥을 긁으며 술 웅덩이에 불똥을 튀긴다",
     "The hero brings down a heavy overhead katana chop; the blade tip scrapes a long glowing line in the stone floor, throwing bright amber sparks forward into a liquor puddle on the right, which catches fire, an oak barrel beside it bursting.", None),
    ("katana_k_groundPin", "katana", "땅에 박기", "투구가 갈라진 적이 무릎까지 바닥에 박혀 있다",
     "In the centre, a shield soldier is sunk into the floor up to his knees: his legs disappear into a round hole of broken flagstones with big radiating cracks, his iron bucket helmet is split in two by a thin silver cut line; he is stuck and cannot move. The hero stands on the left with the katana raised high for the next blow.", None),
    ("katana_k_moonRelay", "katana", "달빛 잇기", "달 분신이 쓰러진 적에서 다음 적으로 건너가는 청백 선",
     "A glowing pale moon-blue (#c8d8f0) ghostly copy of the hero leaps from a fallen soldier lying on the left to the next soldier on the right, leaving a thin moon-blue line connecting them, with a small crescent moon at the start of the line.", None),
    ("katana_k_moonPools", "katana", "취월", "술 웅덩이마다 비친 달에서 분신이 솟아 칼을 든다",
     "Three round amber liquor puddles on the dark floor each reflect a pale full moon; from each reflection a pale moon-blue (#c8d8f0) ghost copy of the hero rises with katana raised; the real hero stands in the middle after a parry.", None),
    ("res_katana_insight", "katana", "공명 되받는 달", "흘려 밀기·칼 감기로 밀치거나 끌어온 적에게 달 분신이 따라붙어 벤다",
     "Two linked moves in one picture: on the left the hero parries with a slanted katana, shoving one soldier away and pulling another in with a silver spiral around a pike; right beside the displaced soldier a pale moon-blue (#c8d8f0) ghost copy of the hero appears and slashes him with a thin silver line. A small crescent moon links the hero and the clone.", ["k_parryShove", "k_bladeBind"]),
    ("res_katana_breach", "katana", "공명 칼바람 길", "그림자 넘기·물러서며 베기의 대쉬 길에 칼바람이 남아 다시 벤다",
     "A long straight diagonal lane across the floor marks the path the hero just dashed along (the hero stands at its far end on the right, katana lowered). Along that whole lane, a row of tall, thin, bright silver-white crescent wind blades rises out of the floor like a wall of slashes, cutting two soldiers who stand on the lane.", ["k_shadowVault", "k_issenBack"]),
    ("res_katana_chain", "katana", "공명 끊이지 않는 칼", "개성 기술로 쓰러뜨린 자리에서 칼바람 고리가 퍼진다",
     "Where a soldier has just fallen in the centre, a ring of thin silver wind blades bursts outward around the body, cutting the surrounding soldiers; the hero stands at the left flicking his katana, an ink-black shadow copy and a moon-blue copy fading behind him (the chain of techniques).", ["k_shadowThrust", "k_iaiChain", "bloodGale", "k_moonRelay"]),
    # ---- greatsword ----
    ("greatsword_g_launch", "greatsword", "날려 보내기", "넷째 타에 날아간 병사가 벽에 부딪혀 돌가루가 튄다",
     "The hero on the left finishes a huge horizontal greatsword swing; a shield soldier flies away to the right and smashes into a grey stone wall, cracking it with an explosion of stone dust and debris and a hot amber impact flash.", None),
    ("greatsword_g_swatBack", "greatsword", "쳐내기", "대검 면이 날아오는 술병을 쳐서 던진 행상에게 돌려보낸다",
     "The hero swings the flat of the greatsword like a bat and hits an incoming liquor bottle in mid-air with a bright amber metallic flash; the bottle flies back to the right toward a liquor peddler in a wide straw hat.", None),
    ("greatsword_g_quakeGuard", "greatsword", "되받는 땅울림", "막아 낸 충격이 땅을 타고 번져 앞줄 적이 떠오른다",
     "Uncluttered: the hero on the left braces behind his huge greatsword planted point-down like a shield, a bright amber spark where a hammer blow hit the blade. From the blade a single straight glowing amber crack runs forward to the right through the floor, and at its end two soldiers are thrown up into the air by a burst of rock.", None),
    ("greatsword_g_guardPull", "greatsword", "끌어당기기", "대검을 내리며 둘레 적을 앞으로 끌어당기는 손짓",
     "The hero stands in the centre on a flagstone floor patch and sweeps his huge greatsword toward himself; a swirling ring of dust with amber streaks spirals INWARD toward him and drags two shield soldiers, one on each side, toward him, their feet skidding and leaving dust trails.", None),
    ("greatsword_g_shoulderFlip", "greatsword", "어깨 너머", "태클로 들어 올린 적을 등 뒤 바닥에 메친다",
     "Side view, two figures only: the hero (greatsword in one hand) has lifted a shield soldier over his shoulder in a big arc, and the soldier is upside-down in mid-air behind the hero, about to slam head-first onto the floor, where a ring of dust and glowing amber cracks already bursts. A curved motion arc shows the throw over the shoulder.", None),
    ("greatsword_g_ramWall", "greatsword", "들이받기", "어깨로 밀고 나간 적이 기둥에 처박힌다",
     "Side view, two figures and one pillar only: the hero charges shoulder-first to the right with speed lines behind him, his greatsword held low behind; he rams a shield soldier backwards into a big grey stone pillar, which cracks with stone chunks flying and a hot amber impact flash between the soldier's back and the pillar.", None),
    ("greatsword_g_boilingSteel", "greatsword", "끓는 쇠", "모으는 대검에 술이 빨려 들어 칼날이 끓는다",
     "The hero holds the greatsword low, charging power; amber liquor from puddles around him spirals and is sucked into the blade, which glows orange-hot with bubbling, boiling cracks and rising steam.", None),
    ("greatsword_g_crackPull", "greatsword", "빨아들이는 균열", "균열 양옆의 적이 금 쪽으로 미끄러져 들어간다",
     "A long glowing amber crack splits the floor diagonally from the hero's greatsword; soldiers on both sides of it slide and tumble into the crack as the floor tilts toward it, dust streaks showing the pull.", None),
    ("greatsword_splitRoad", "greatsword", "갈라진 길", "갈라진 바닥 위를 달리며 날아온 화살을 튕겨 낸다",
     "The hero runs fast along a glowing amber floor fissure, greatsword dragged behind; a chunk of stone bursting up from the crack deflects an incoming arrow with a bright flash.", None),
    ("greatsword_g_leapToss", "greatsword", "띄워 올리기", "도약 찍기 착지에 둘레 적이 공중으로 떠오른다",
     "The hero lands from a leaping overhead slam in the centre, the greatsword buried in the floor; a shockwave ring of dust and amber cracks erupts and soldiers around him are flung up into the air.", None),
    ("greatsword_g_crushedBreath", "greatsword", "짓눌린 숨", "진동 한가운데로 끌려온 적들이 서로 머리를 박는다",
     "From the centre of a vibrating amber shock ring, three soldiers are dragged inward and smash their iron helmets together in the middle with a burst of impact stars; the hero behind them with greatsword planted.", None),
    ("greatsword_jarCrush", "greatsword", "술독 짓누르기", "진동이 모은 술 웅덩이에 불이 붙어 크게 터진다",
     "The shockwave has gathered the spilled liquor into one big puddle in the centre, which ignites into a large amber-orange fire explosion with an oak barrel blowing apart; the hero on the left shields himself with the greatsword.", None),
    ("greatsword_g_rageRoar", "greatsword", "포효", "폭주하는 전사의 포효에 적들이 벽까지 밀려난다",
     "The enraged hero roars in the centre with the greatsword raised, red-amber glow pouring from his cracks; a huge circular shockwave ring pushes two soldiers backwards, slamming them into the walls at the sides.", None),
    ("greatsword_g_rageFire", "greatsword", "술기운 폭주", "불붙은 술 위를 밟으며 붉게 달아오른 대검",
     "The rampaging hero stomps through a pool of burning amber liquor, flames licking up his legs; the greatsword held high glows red-hot orange along its whole edge, embers swirling.", None),
    ("res_greatsword_weight", "greatsword", "공명 무너뜨림", "날려 보내기·들이받기로 처박힌 자리 바닥이 갈라져 둘레가 튀어 오른다",
     "Uncluttered: a soldier crashes back-first into the floor in the centre (thrown there by the hero, who stands on the left after a big greatsword swing). The flagstones under the crash break into a large star of glowing amber cracks and the floor slabs around it tilt and pop up into the air, lifting one more soldier off his feet.", ["g_launch", "g_ramWall"]),
    ("res_greatsword_insight", "greatsword", "공명 막고 되치는 대검", "쳐내기·되받는 땅울림으로 막아 낸 순간 둘레 탄을 모두 되쳐 보낸다",
     "The hero completes a perfect guard with the greatsword held across his body; a bright amber ring bursts 360 degrees around him and all incoming arrows and liquor bottles bounce back outward in every direction.", ["g_swatBack", "g_quakeGuard"]),
    # ---- dagger ----
    ("dagger_d_pullThrow", "dagger", "뽑아 던지기", "쓰러진 적에게서 뽑은 단검이 다음 적에게 날아간다",
     "The hero rips a karambit dagger out of a falling soldier on the left and in the same motion throws it; the dagger flies as a thin curved amber needle streak to the chest of a second soldier on the right, X-shaped spark at impact.", None),
    ("dagger_d_brandChain", "dagger", "낙인 사슬", "붉은 낙인 사슬에 묶인 두 적이 서로 부딪친다",
     "Two soldiers, each marked with a glowing dark-red claw-mark brand on the chest, are yanked together by a glowing red chain stretched between their brands and collide head-first in the centre with an impact flash; the hero in the foreground, dagger ready.", None),
    ("dagger_d_shadowKnot", "dagger", "그림자 매듭", "적의 그림자가 매듭처럼 발목을 묶는다",
     "A single shield soldier in the centre: his own ink-black shadow on the floor has risen up as thick black ribbons that are tied into one big clear KNOT (a bow-like knot shape) around both his ankles; he is stuck, struggling; a dark-red claw-mark brand glows on his chest. The hero crouches on the left with the dagger in reverse grip.", None),
    ("dagger_d_stepBack", "dagger", "되짚어 걷기", "그림자 걸음 뒤 처음 자리로 되돌아오며 그은 검은 선",
     "The hero reappears at his starting point on the left; a straight ink-black slash line runs back along the path he travelled, cutting a soldier in the middle; a fading ink silhouette of the hero dissolves at the far right end where he had been.", None),
    ("dagger_d_dashBrand", "dagger", "스치는 낙인", "스쳐 지나간 적의 옆구리에 붉은 낙인이 남는다",
     "The hero dashes low and fast past a shield soldier from left to right, a thin streak behind him; on the soldier's side a fresh glowing dark-red claw-mark brand of three parallel curved scratches is left burning.", None),
    ("dagger_d_dashPierce", "dagger", "꿰찌르기", "한 번의 찌르기가 두 적을 한 줄로 꿰뚫는다",
     "Side view: the hero lunges low and far to the right in one dash-stab, his arm and karambit dagger fully extended; one long, straight, thin bright amber needle line goes straight THROUGH two soldiers standing one behind the other (both doubled over), and ends behind the second soldier in a bright X-shaped spark.", None),
    ("dagger_d_flurryPull", "dagger", "휘감는 난타", "난타의 바람에 둘레 적이 빨려 든다",
     "The hero in the centre performs a blindingly fast flurry of stabs, many thin curved claw streaks around him forming a whirlpool of wind that sucks two soldiers inward from the sides.", None),
    ("dagger_d_sparkFlurry", "dagger", "불티 난타", "난타 끝 불티가 술 웅덩이에 떨어져 불이 붙는다",
     "At the end of a fast flurry a burst of amber sparks scatters from the hero's dagger and rains down into a liquor puddle on the floor, which catches fire around a soldier's feet.", None),
    ("dagger_twinBrand", "dagger", "쌍낙인", "분신이 교차 베기로 옆 적에게 낙인을 옮긴다",
     "Two soldiers stand apart on the left and right. Between them, the hero and an ink-black shadow clone of himself pass each other, their two amber claw-slash streaks forming one big clear X. A glowing dark-red claw-mark brand jumps along a dotted red arc from the left soldier's chest to the right soldier's chest.", None),
    ("dagger_d_cloneShield", "dagger", "분신 방패", "날아든 칼을 분신이 대신 맞고 흩어진다",
     "A thrown knife hits an ink-black shadow clone standing in front of the hero, and the clone shatters into black ink smoke and shards while the real hero behind it stays safe, dagger ready.", None),
    ("dagger_d_galeReturn", "dagger", "돌아오는 칼", "되돌아오는 단검이 꿰인 적을 끌고 손으로 온다",
     "A thrown claw-dagger returns through the air along a curved amber streak back to the hero's open hand on the left, dragging a hooked soldier along behind it, the soldier's feet skidding on the floor.", None),
    ("dagger_liquorThrow", "dagger", "독주 투척", "부채꼴 단검 사이에 술병 하나가 깨진다",
     "The hero throws a fan of five daggers to the right; among the thin amber streaks, the middle one is a liquor bottle that shatters on the floor, splashing a wide amber liquor puddle among the enemies.", None),
    ("dagger_d_ghostBind", "dagger", "그림자 사냥", "그림자 손이 적의 발목을 붙잡는다",
     "Black ink shadow hands rise from a soldier's own shadow on the floor and grab his ankles, holding him in place; he strains to move; a red claw brand glows on him.", None),
    ("dagger_d_ghostFire", "dagger", "취한 그림자", "그림자가 지나간 웅덩이에 불이 옮겨 붙는다",
     "An ink-black shadow copy of the hero sweeps low across the floor from left to right; behind it, the amber liquor puddles along the path it crossed burst into flame.", None),
    ("res_dagger_vital", "dagger", "공명 얽힌 급소", "묶이거나 끌려온 적의 낙인이 터져 사슬이 옆 적까지 뻗는다",
     "Two linked moves: a soldier bound at the ankles by his own ink shadow has his red claw brand explode in an X burst, and a glowing red chain shoots out from it to the neighbouring soldier, binding both together.", ["d_brandChain", "d_shadowKnot"]),
    ("res_dagger_breach", "dagger", "공명 그림자 길", "대쉬·그림자 걸음이 지나간 길의 그림자가 밟은 적에게 낙인을 붙인다",
     "The hero dashes away to the right leaving a long ink-black shadow trail on the floor; a soldier stepping on the trail gets a dark-red claw brand burned onto him from the shadow rising up his legs.", ["d_dashBrand", "d_stepBack"]),
    # ---- bow ----
    ("bow_b_pointBlank", "bow", "코앞 사격", "코앞 화살에 날아간 병사가 벽에 부딪힌다",
     "The hero on the left shoots an arrow at point-blank range into a soldier right in front of him; the soldier is blasted backward to the right into a stone wall with a burst of dust, the arrow stuck in his chest, a pale-gold streak behind.", None),
    ("bow_b_ricochet", "bow", "튕기는 화살", "쓰러진 적에서 꺾인 화살이 옆 적에게 튄다",
     "An arrow drops a soldier in the centre, then bends and ricochets off him in a sharp pale-gold zigzag streak into a second soldier on the right; the hero with the longbow on the left.", None),
    ("bow_b_perfectPin", "bow", "꿰어 박기", "화살째 밀려간 적이 기둥에 꽂혀 있다",
     "A soldier is pinned to a grey stone pillar on the right by a single thick arrow through his shoulder, the arrow vibrating, cracks in the stone around it; the hero on the left lowering the longbow after a full draw.", None),
    ("bow_b_fullBounce", "bow", "되튀는 화살", "가득 당긴 화살이 벽에 닿아 되튀어 돌아온다",
     "A fully drawn arrow flies to the right, strikes a stone wall with a flash and bounces straight back as a pale-gold streak, cutting a soldier on the way back toward the hero on the left.", None),
    ("bow_b_dropShot", "bow", "낙하 사격", "구르며 쏜 화살이 하늘로 솟았다 세 발로 떨어진다",
     "The hero rolls on the ground on the left while shooting an arrow up into the sky (a curving pale-gold streak upward); on the right three arrows plunge down onto a soldier, with a small target mark on the floor.", None),
    ("bow_b_arrowTrap", "bow", "화살 덫", "떠난 자리에 세워 둔 화살 덫을 적이 밟는다",
     "Three arrows stuck upright in the floor form a trap; a soldier steps into it and the arrows snap closed around his legs with pale steel-blue binding lines; the hero is already far away at the left edge.", None),
    ("bow_b_rainSnare", "bow", "화살 그물", "화살비가 그물처럼 오므라들어 적을 한데 묶는다",
     "Uncluttered: in the centre, a ring of arrows stuck in the floor, and a NET of clearly visible pale steel-blue lines stretched between the arrows is closing like a drawstring bag, pulling three soldiers tightly together back-to-back in the middle, bound. A few more arrows fall from above as pale-gold streaks. The hero stands small at the left edge with the longbow.", None),
    ("bow_b_rainEcho", "bow", "이어지는 비", "쓰러진 자리에 화살 한 다발이 더 떨어진다",
     "Where a soldier just fell in the centre, a whole bundle of extra arrows falls from the sky onto the spot, pale-gold streaks from above, arrows sticking in the floor around the fallen body.", None),
    ("bow_b_scatterVolley", "bow", "흩날리는 살", "연사에 쓰러진 적 자리에서 화살이 꽃처럼 흩어진다",
     "From the spot of a falling soldier in the centre, arrows burst outward in all directions like a blooming flower of pale-gold streaks; the hero rapid-firing at the left.", None),
    ("bow_b_rapidStride", "bow", "걸으며 연사", "걸음을 멈추지 않고 쏟아붓는 연사",
     "The hero walks forward steadily in mid-stride while rapid-firing the longbow to the right, a row of several arrows in flight as pale-gold streaks, small dust puffs at his feet.", None),
    ("bow_b_skewer", "bow", "꿰미", "한 화살에 꿰인 적들이 꼬챙이처럼 끌려간다",
     "One long arrow has skewered three soldiers in a row like a kebab and drags them along together to the right; pale-gold streak behind it; the hero on the left.", None),
    ("bow_fireArrow", "bow", "불화살 한 발", "완벽하게 놓은 화살이 술 웅덩이 줄을 불태운다",
     "A perfect arrow flies low from the hero on the left over a row of amber liquor puddles, each puddle bursting into amber-orange flame along its path.", None),
    ("bow_b_starWell", "bow", "별 표적", "하늘 화살 자리로 둘레 적이 빨려 든다",
     "A sky arrow lands in the floor in the centre, and a swirling pale-gold starlight vortex pulls three surrounding soldiers into the spot.", None),
    ("bow_b_starDrunk", "bow", "술별", "하늘 화살이 술 웅덩이에 떨어져 불꽃이 핀다",
     "A glowing sky arrow falls like a shooting star into a liquor puddle, which bursts into a bloom of amber-orange fire; a soldier recoils.", None),
    ("res_bow_weight", "bow", "공명 말뚝 박기", "밀쳐 내거나 끌어모은 적에게 화살이 따라 꽂혀 묶는다",
     "Uncluttered: the hero on the left has just shot (bow still raised); a single shield soldier, knocked backwards, is being pinned to the floor by one huge, thick stake-like arrow plunging down from above through his shoulder into the flagstones; pale steel-blue binding lines run from the stake to the floor; cracks around the stake.", ["b_pointBlank", "b_rainSnare"]),
    ("res_bow_breach", "bow", "공명 덫 비", "화살 덫에 묶인 적 위로 하늘 화살이 떨어진다",
     "A soldier caught in an arrow trap on the floor, legs bound by upright arrows with pale steel-blue lines, while a glowing sky arrow plunges straight down on top of him from above.", ["b_arrowTrap", "b_dropShot"]),
]

WEAPONS = ("katana", "greatsword", "dagger", "bow")


def prompt_for(card):
    cid, weapon, name, ko, scene, pair = card
    return f"{STYLE}\n\n{CAST}\n\n{WEAPON[weapon]}\n\nTHE MOMENT: {scene}"


def by_id():
    return {c[0]: c for c in CARDS}


if __name__ == "__main__":
    from collections import Counter
    print(len(CARDS), Counter(c[1] for c in CARDS))
