#!/usr/bin/env python3
"""56라운드 — 무기별 공격 수단 키아트 프롬프트 생성 (moves.py → prompt_<weapon>_<A|B>[<retry>].txt).

참고 이미지(호출마다 3장): ref_hero3b_views.png(주인공 hero3_b 확정 개념도의 글자 없는 부분 잘라냄)
 + ../concept_weapons/raw_<무기 확정안>.jpg + ../keyart_waste/raw_a.jpg(문체·분위기만).
실행: python3 prompts.py  (2회차 = prompt_<weapon>_<A|B>2.txt, FIX2 패널만 교체)
"""
import os
from moves import WEAPONS

HERE = os.path.dirname(os.path.abspath(__file__))

POS = {
    (2, 2): ["Top-left panel", "Top-right panel", "Bottom-left panel", "Bottom-right panel"],
    (2, 1): ["Left panel", "Right panel"],
}
GRID_TXT = {
    (2, 2): "a two-by-two grid of four equal panels separated by thin pure-black gutters",
    (2, 1): "two equal side-by-side panels separated by one thin pure-black gutter",
}

HEAD = (
    "No text, no letters, no captions, no titles, no numbers anywhere in the image. "
    "Key art for a dark modern 2D pixel-art roguelike action game, shown as {grid}. Every panel is a separate dramatic moment "
    "showing a different attack technique of the same hero with the same weapon; the panels share one style, one palette and one "
    "lighting. The first attached image shows the hero's approved design - keep him exactly as drawn there: a war ghost born on the "
    "battlefield, a hunched, gaunt revenant made of cracked dark ash and scorched battlefield earth, a smooth dark shadowed face with no "
    "features except one fierce amber burning eye (his left eye) glaring with pure hatred, amber soul-fire glowing through fissures in "
    "his chest and back, one small flame on his left shoulder, shards of armor (fractured breastplate, bent vambrace, dented greave), "
    "broken arrow shafts and rusty nails stuck in his shoulders and back, dirty bandages on hands and shins, a ragged leather scrap at "
    "the hips. No clothes, no hat, no hood, no cloak, no chains. He exists only to fight: every pose is coiled, predatory and full of "
    "loathing - nothing heroic, noble or elegant about him. "
    "The second attached image shows the approved design of his weapon - keep the weapon exactly as drawn there. "
    "The third attached image only shows the mood, darkness and palette of the series key art - do not copy its scene. "
)

COMMON = (
    "Camera in every panel: a high three-quarter top-down angle looking down at the battlefield ground at roughly fifty degrees, like "
    "a modern top-down action roguelike game scene, but staged cinematically as key art, with the hero at medium size, enemies around "
    "him, and the attack effect large and clear. Ground: dark trampled mud, ash, broken pikes and spent arrows, lit only by the attack "
    "and the hero's soul-fire. Enemies: grim Renaissance-era soldiers rendered in the same dark grays - drunken conscripts in battered "
    "barrel-stave armor with clubs, tricorn-hat musketeers with matchlocks, pikemen, and a bucket-helmed brute behind a tall rectangular "
    "pavise shield; their faces are lost in shadow; struck enemies burst into gray ash and amber sparks, no red blood. "
    "Attack effects are simple brush strokes, like a single stroke of an ink brush: thin at the start, thick in the middle, splitting "
    "into ragged ash at the end - not filled crescents, not full glowing circles. "
)

TAIL = (
    "Rendering: crisp high-detail modern pixel art drawn at large scale, chunky readable shapes, cel shading with one shadow and one "
    "highlight step, dark 1-pixel outlines, strong value contrast - deep black silhouettes, dim gray midtones, the brightest values only "
    "in the amber effects. Palette: charcoal, ash and cold soil grays, dark rusty iron, dark umber leather, dirty off-white bandage, plus "
    "one warm amber accent only (#8b4d22, #d67a11, #e8b858, #faeec0, white-hot = #faeec0) for soul-fire, the burning eye, embers and "
    "the attack effects. No saturated blue, green, purple or red; no magic runes, no gems. "
    "Panels carry no captions, no titles and no numbers. No text, no letters, no logos, no UI, no watermark, no outer frame."
)

REFS = ["ref_hero3b_views.png", None, "../keyart_waste/raw_a.jpg"]


# 2회차(재생성) — 1회차 자기 비평에서 약했던 패널만 문장을 바꾸고, 공통 고칠 점을 덧붙인다(편집형 아님: 같은 참고 이미지로 새로 생성).
FIX_COMMON = (
    "Enemy skin is ash-gray like everything else, and their faces are hidden in deep shadow under helmets and hat brims - no pink skin, "
    "no clearly drawn human faces. "
)
FIX2 = {
    ("katana", 0): {1: (
        "the lightning-flash draw cut: a straight line of three enemies stands in the middle of the panel; the hero has just blinked "
        "straight through all three of them, about four body-lengths in one dash, and is now crouched low beyond the last one, his back "
        "to them, blade fully extended behind him; one perfectly straight, razor-thin glowing amber line runs along the ground from the "
        "near edge of the panel, straight through the bodies of all three enemies, to his blade - each enemy is cut cleanly in two by "
        "that line, frozen mid-step a split second before bursting into ash; a trail of ash and ember sparks follows the line.")},
    ("katana", 1): {1: (
        "the standoff, the instant after: the hero and a tall armored duelist have just passed each other with a single cut; the hero "
        "is in the foreground, low and calm, sliding the blade back into the scabbard at his left hip with the last few centimetres of "
        "blade still showing; behind him the duelist stands frozen with his sword raised, and one thin glowing amber diagonal line "
        "crosses his whole body from shoulder to hip, ash beginning to pour out of it; drifting ash hangs perfectly still in the air.")},
    ("dagger", 0): {
        2: ("brand and detonate: a single heavily armored enemy seen from the side, five separate small glowing amber marks burned onto "
            "his armor and back - each mark a sharp three-claw scratch glyph, clearly distinct and countable, glowing like hot coals but "
            "not burning with flames; the hero has just appeared behind him in a puff of ash, and the five marks are cracking open "
            "with bright light, about to explode."),
        3: ("the backstab, seen from behind the victim: a big bucket-helmed brute faces away from the hero toward the right edge of the "
            "panel, holding his tall pavise shield uselessly in front of himself; the hero is directly behind his back and drives the "
            "reverse-grip fang dagger down into the gap between helm and back plate at the nape of the neck; a sharp white-hot flash and "
            "a starburst of amber sparks at the point; the brute arches in shock."),
    },
    ("bow", 1): {
        0: ("breath, slowed-time precision aim: time has almost stopped - the battlefield around him is drained to flat dull gray with "
            "pale ripples of slowed air, a musket ball and puffs of powder smoke hang frozen in mid-air, falling ash flakes are frozen "
            "as still dots; only the hero at full draw, his burning eye, the glowing soul-fire string and the burning arrowhead keep "
            "their color; a thin amber aim line stretches perfectly straight to the head of a distant musketeer frozen mid-shot; one "
            "slow wisp of ash leaves his face like an exhaled breath."),
        1: ("reload from his own body, close up: holding the bow low in his left hand, with his right hand he wrenches a broken arrow "
            "shaft out of his own shoulder - ash crumbles from the hole and a flicker of soul-fire escapes from it - and in the same "
            "motion its arrowhead bursts into amber flame as he brings it to the soul-fire string."),
    },
}


def build(weapon, si, extra="", fix=False):
    w = WEAPONS[weapon]
    sh = w["sheets"][si]
    g = tuple(sh["grid"])
    rep = FIX2.get((weapon, si), {}) if fix else {}
    body = " ".join(f"{p} - {rep.get(i, m['en'])}" for i, (p, m) in enumerate(zip(POS[g], sh["panels"])))
    if fix:
        extra = FIX_COMMON + extra
    return HEAD.format(grid=GRID_TXT[g]) + w["weapon_en"] + COMMON + body + " " + extra + TAIL


def refs(weapon):
    return [REFS[0], WEAPONS[weapon]["ref_img"], REFS[2]]


if __name__ == "__main__":
    for wk, w in WEAPONS.items():
        for si, _ in enumerate(w["sheets"]):
            fn = os.path.join(HERE, f"prompt_{wk}_{'AB'[si]}.txt")
            open(fn, "w", encoding="utf-8").write(build(wk, si) + "\n")
            print(fn, len(open(fn).read()))
            if (wk, si) in FIX2:
                fn2 = os.path.join(HERE, f"prompt_{wk}_{'AB'[si]}2.txt")
                open(fn2, "w", encoding="utf-8").write(build(wk, si, fix=True) + "\n")
                print(fn2)
