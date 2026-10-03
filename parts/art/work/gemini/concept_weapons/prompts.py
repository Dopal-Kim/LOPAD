#!/usr/bin/env python3
"""53라운드 Q18 — 무기 4종 개념 시안 프롬프트 (참고용 그림, 게임 도트 아님).

방향 A = 전장에서 주운 녹슨 실전 무기에 혼불이 스민 것 (salvage)
방향 B = 재와 흙이 굳어 혼불로 벼린 망령의 무기 (ash-forged)
참고 이미지: concept_char/hero3_b.jpg (주인공 확정 개념도) + keyart_waste/raw_a.jpg (키아트 문체).
교훈(52라운드 3.8·7.1): 대문자 강조어는 그림 속 라벨 글자가 되므로 쓰지 않는다.
실행: python3 prompts.py → prompt_<weapon>_<A|B>.txt 생성
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

HEAD = (
    "Weapon concept sheet, reference art only (not a game asset), for a dark modern 2D pixel-art roguelike action game "
    "set on an endless, grim Renaissance-era early-gunpowder battlefield (pikes, longbows, matchlock muskets, mud, ash, supply wagons). "
    "The first attached image is the hero's approved character sheet: keep him exactly as drawn there - a war ghost, a hunched revenant "
    "made of cracked dark ash and scorched battlefield earth, a smooth dark shadowed face with only one fierce amber burning eye "
    "(his left eye, on the viewer's right in front view), amber soul-fire glowing through fissures in the chest and back, one small flame "
    "on the left shoulder, shards of armor (fractured breastplate, bent vambrace, dented greave), broken arrow shafts and rusty nails stuck "
    "in his shoulders and back, dirty bandages on hands and shins, a ragged leather scrap at the hips and a small battered diary on a cord "
    "at the right hip. No clothes, no hat, no hood, no cloak, no chains. "
    "The second attached image only shows the mood, palette and rendering of the game's key art - do not copy its scene. "
    "Rendering: crisp high-detail modern pixel art drawn at large scale, chunky readable shapes, cel shading with one shadow and one "
    "highlight step, dark 1-pixel outlines, light from the upper left, flat shading, no airbrush, no photo texture. "
    "The weapon must have a strong, unique, instantly recognisable silhouette and personality, and must clearly belong to this hero: "
    "same materials, same wear, same single amber soul-fire accent. Grounded and realistic first; the uncanny part is only the soul-fire. "
)

LAYOUT = (
    "Layout, one row on a flat plain dark slate-gray background with soft floor shadows, evenly spaced, no overlap, no scenery: "
    "(1) on the left, the weapon alone, very large, in clean side view{weapon_pose}, with its details clearly visible; "
    "(2) the hero holding it in a ready combat stance, three-quarter view{hold}; "
    "(3) the hero at rest, standing, carrying it {carry}; "
    "(4) on the right, one or two small frozen moments of his basic attack with this weapon showing the attack effect: {fx}. "
)

TAIL = (
    "Palette: charcoal, ash and cold soil grays, dark rusty iron (dark gray-brown), dark umber leather, dirty off-white bandage, plus "
    "ONE warm amber/ember accent only (#8b4d22, #d67a11, #e8b858, #faeec0) for soul-fire, the burning eye, embers and the attack trail. "
    "No saturated blue, green, purple or red; no other glowing colors; no magic runes, no gems, no ornate fantasy filigree. "
    "No text, no letters, no labels, no captions, no numbers, no logos, no heraldry, no UI, no watermark, no frame."
)

W = {
    # ---------------------------------------------------------------- 칼
    ("katana", "A"): dict(
        weapon=(
            "Weapon: a katana - a long, slightly curved, single-edged sword with a long two-handed grip and a small round guard - "
            "salvaged from the mud of the battlefield, the blade of a foreign mercenary long dead. The steel is dark, pitted with rust, "
            "its edge chipped and notched in several places; a thin hairline crack runs along the blade near the spine and amber "
            "soul-fire seeps out of it like molten light, brightest near the tip. The grip is rewrapped in dirty battle bandage, the "
            "guard is a rough, rusted iron disk, and a bent iron nail is driven through the wrap as a crude peg. The scabbard is old "
            "cracked dark lacquered wood, split near the mouth and bound tight with bandage and a frayed cord. "
        ),
        weapon_pose=", blade drawn and lying horizontally, with its scabbard drawn just below it",
        hold=", gripping it low and forward with both hands, blade angled down, body coiled",
        carry="sheathed at his left hip, his left hand gripping the scabbard just behind the guard, thumb on the guard",
        fx=("a fast draw-cut leaving a thin, sharp crescent arc of amber soul-fire that frays at its tail into drifting ash "
            "and a few sparks, plus a small shower of rust flakes off the blade"),
    ),
    ("katana", "B"): dict(
        weapon=(
            "Weapon: a katana - a long, slightly curved, single-edged sword with a long two-handed grip and a small guard - that is not "
            "made of steel at all: it is ash and battlefield earth packed hard and fired by his own soul-fire, the same cracked dark ash "
            "shell as his body. The blade is matte charcoal-black with a faint layered texture like dried mud, and its whole cutting edge "
            "is one bright, thin amber fissure glowing from inside, as if the blade were cracked open along the edge; small flakes of ash "
            "peel off the back of the blade. The guard is a fused shard of a broken breastplate, the grip is wrapped in dirty bandage. "
            "The scabbard is a hollow sleeve of hardened ash and earth with a glowing seam, tied with a scrap of leather strap. "
        ),
        weapon_pose=", blade drawn and lying horizontally, with its scabbard drawn just below it",
        hold=", gripping it low and forward with both hands, blade angled down, body coiled",
        carry="sheathed at his left hip, his left hand gripping the scabbard just behind the guard, thumb on the guard",
        fx=("a fast draw-cut leaving a crescent of hot amber light that immediately crumbles into a curtain of falling gray ash and "
            "glowing ember specks, with a thin afterimage of the blade's glowing edge"),
    ),
    # ---------------------------------------------------------------- 대검
    ("greatsword", "A"): dict(
        weapon=(
            "Weapon: a huge two-handed greatsword of the Renaissance foot soldier kind (a zweihander), as tall as the hero, with long "
            "straight quillons, a pair of small parrying hooks above a leather-wrapped ricasso and a long grip - salvaged from a fallen "
            "pikeman's field. The blade is heavy dark iron, rusted brown-gray, with deep notches and one broken corner near the tip; a "
            "spent arrowhead is still embedded in the blade. Amber soul-fire smoulders inside the notches and cracks like coals in a "
            "forge, glowing brightest in the deepest notch. The ricasso and grip are bound in old leather and bandage, held with rusted "
            "nails. A worn leather strap and buckle hang from the cross-guard so it can be slung on the back. "
        ),
        weapon_pose=", lying horizontally, point to the right",
        hold=", both hands on the long grip, the heavy blade resting over one shoulder, ready to swing, knees bent under its weight",
        carry="slung diagonally across his back by the strap, the grip rising above his right shoulder, his hands empty",
        fx=("a heavy horizontal sweep leaving a wide, thick arc of dim amber glow that drags a cloud of ash and dirt, and an "
            "overhead smash into the ground cracking the mud with amber light in the cracks and ash bursting up"),
    ),
    ("greatsword", "B"): dict(
        weapon=(
            "Weapon: a huge two-handed greatsword, as tall as the hero, that is a slab of battlefield debris fused together by soul-fire: "
            "compacted ash and scorched earth hardened like stone, with broken pike heads, a cracked breastplate plate, arrowheads and "
            "nails half-sunk into it, shaped into a broad, crude, straight blade with a blunt-squared tip. Deep glowing amber fissures "
            "run through the blade like the cracks in the hero's chest, and faint soul-fire smoke rises from them. The cross-guard is a "
            "bent pike shaft, the long grip is wrapped in bandage. No strap: it clings to his back as if held by threads of soul-fire. "
        ),
        weapon_pose=", lying horizontally, point to the right",
        hold=", both hands on the long grip, the heavy blade resting over one shoulder, ready to swing, knees bent under its weight",
        carry=("on his back, hanging diagonally with no strap, held to his back by faint threads of amber soul-fire running from "
               "the fissures of his back into the blade, the grip above his right shoulder, his hands empty"),
        fx=("a heavy horizontal sweep where chunks of ash and earth flake off the blade and scatter like a burst of hot ash, leaving a "
            "broad smouldering arc, and an overhead smash that splits the ground with glowing fissures"),
    ),
    # ---------------------------------------------------------------- 단검
    ("dagger", "A"): dict(
        weapon=(
            "Weapon: a single rondel dagger of the Renaissance battlefield - a narrow, stiff, armour-piercing thrusting blade with a "
            "disk-shaped guard and a disk pommel, the kind used to finish fallen knights through the gaps of their armor. Rusted dark "
            "iron, the tip whetted bright, one disk cracked and dented, the grip wrapped in dirty bandage and pinned with a bent nail. "
            "Soul-fire seeps out where the blade meets the guard and through the crack in the disk, and drips like molten droplets "
            "from the tip. "
        ),
        weapon_pose=", lying horizontally",
        hold=", low crouch, the dagger in his right hand in reverse grip, blade along the forearm, his empty left hand raised in front of his chest as a guard",
        carry="held loosely in reverse grip in his right bandaged hand at his side, the blade lying back along his forearm, left hand empty",
        fx=("three very fast short stabs leaving short, sharp amber streaks like sparks from a grindstone, and droplets of soul-fire "
            "flicking off the blade tips"),
    ),
    ("dagger", "B"): dict(
        weapon=(
            "Weapon: a single dagger that is a long jagged shard broken from his own cracked ash shell - like a splinter of black "
            "volcanic glass or fired clay - sharp, slightly curved like a fang, with a glowing amber core visible through its fissures "
            "and an ember-bright point. The base of the shard is wrapped in dirty bandage as a grip, bound with a rusted nail. On his "
            "right forearm, the fresh crack where the shard broke off glows faintly. "
        ),
        weapon_pose=", lying horizontally",
        hold=", low crouch, the shard in his right hand in reverse grip, point along the forearm, his empty left hand raised in front of his chest as a guard",
        carry="held loosely in reverse grip in his right bandaged hand at his side, the point lying back along his forearm, left hand empty",
        fx=("three very fast short slashes that leave thin crackling lines of amber in the air, which flake away into ash, and a "
            "brief afterimage of his hands in glowing ash"),
    ),
    # ---------------------------------------------------------------- 활
    ("bow", "A"): dict(
        weapon=(
            "Weapon: an English longbow, as tall as the hero, salvaged from the battlefield - a dark, weathered yew stave, cracked in the "
            "middle and splinted with bandage and two rusted nails, with a frayed hemp string. His arrows are the broken arrows pulled "
            "out of his own body: mismatched shafts, ragged fletching, rusty bodkin heads; when nocked, soul-fire runs from his fingers "
            "along the shaft and the arrowhead glows amber. A small battered leather quiver hangs at his right thigh. "
        ),
        weapon_pose=", unstrung profile shown vertically beside a strung profile, with two arrows below",
        hold=", drawing the longbow to his jaw, arrow nocked with a glowing amber head",
        carry="the longbow in his left hand at his side, pointing down, while his right hand pulls a broken arrow out of his own shoulder",
        fx=("an arrow in flight leaving a long, thin straight streak of amber soul-fire and a short trail of drifting ash, and the impact "
            "point bursting into a small ring of embers"),
    ),
    ("bow", "B"): dict(
        weapon=(
            "Weapon: a longbow, as tall as the hero, grown from his own body's material - a stave of hardened ash and scorched earth "
            "bent around a charred pike shaft, cracked along its length with glowing amber fissures, tipped at both ends with broken "
            "armor shards. Its bowstring is a taut, thin thread of amber soul-fire, the only glowing line. When he draws, an arrow forms "
            "from ash and soul-fire along the string: a dark ash shaft with a burning amber point. "
        ),
        weapon_pose=", shown vertically, strung, with one ash arrow below",
        hold=", drawing the bow to his jaw, the ash arrow forming on the soul-fire string",
        carry="the bow in his left hand at his side, pointing down, the soul-fire string dimmed to a faint glow",
        fx=("an ash arrow in flight leaving a trail of gray ash and ember specks behind its burning point, and the bowstring "
            "snapping back with a brief flare of amber light"),
    ),
}


def build(weapon, way):
    w = W[(weapon, way)]
    return HEAD + w["weapon"] + LAYOUT.format(weapon_pose=w["weapon_pose"], hold=w["hold"], carry=w["carry"], fx=w["fx"]) + TAIL


if __name__ == "__main__":
    for (weapon, way) in W:
        p = os.path.join(HERE, "prompt_%s_%s.txt" % (weapon, way))
        with open(p, "w", encoding="utf-8") as f:
            f.write(build(weapon, way) + "\n")
        print(p, len(build(weapon, way)))


# ---------------------------------------------------------------------------
# 2회차(재생성, 무기당 1회) — 1회차 비평 반영. 번호 매긴 배치 문장이 라벨 글자를 부르는 것으로 보여
# 배치를 산문으로 바꾸고 '글자 없음'을 앞에도 둔다. 참고 이미지는 1회차와 같음(새로 생성, 편집형 아님).
# ---------------------------------------------------------------------------
LAYOUT2 = (
    "Arrange it as one clean row on a flat plain dark slate-gray background with soft floor shadows, evenly spaced, nothing "
    "overlapping, no scenery. At the far left, the weapon by itself, very large, in clean side view{weapon_pose}. Next to it, the hero "
    "holding it in a ready combat stance, three-quarter view{hold}. Next, the hero at rest, standing, carrying it {carry}. At the far "
    "right, one or two small frozen moments of his basic attack with this weapon showing the attack effect: {fx}. "
    "The figures stand on their own with nothing written under or over them - this sheet has no captions and no titles at all. "
)

FIX2 = {
    ("katana", "B"): (
        "Important shape note: the weapon is clearly a katana in every view - a gently curved, single-edged, slender blade with a "
        "small round guard made from a fused shard of breastplate, no cross-guard, no spikes, no straight double-edged blade. "
        "Its scabbard is a slim curved sleeve following the blade's curve, not a log. "
    ),
    ("greatsword", "A"): (
        "Show the at-rest pose from a back three-quarter view so the greatsword slung diagonally on his back by its leather strap is "
        "clearly visible, blade pointing down behind his left leg, grip above his right shoulder. "
    ),
    ("dagger", "A"): (
        "Important grip note: in the combat stance, at rest, and in the attack, he always holds the dagger in an icepick reverse "
        "grip - the blade comes out of the bottom of his fist, on the little-finger side, pointing down and back along the forearm "
        "toward the elbow; the thumb is on the pommel. The soul-fire on the blade is a seeping glow and small molten drips, not a "
        "large flame. "
    ),
    ("bow", "A"): "",
}


def build2(weapon, way):
    w = W[(weapon, way)]
    return ("No text, no letters, no labels anywhere in the image. " + HEAD + w["weapon"] + FIX2[(weapon, way)]
            + LAYOUT2.format(weapon_pose=w["weapon_pose"], hold=w["hold"], carry=w["carry"], fx=w["fx"]) + TAIL)


def write2():
    for (weapon, way) in FIX2:
        p = os.path.join(HERE, "prompt_%s_%s2.txt" % (weapon, way))
        with open(p, "w", encoding="utf-8") as f:
            f.write(build2(weapon, way) + "\n")
        print(p)


if __name__ == "__main__":
    write2()
