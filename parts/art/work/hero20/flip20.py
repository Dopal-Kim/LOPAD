"""P20 — 대검 공중제비 도약 찍기(greatsword_leap_slam f3~f5): 몸이 무기 오버레이 안에 함께 그려진 칸(bodyInOverlayFrames)을 새 몸으로.

옛 합성(combo56_moves_kg.kg_gs.flip_frame)을 그대로 다시 돌려(원본과 픽셀 동일함을 확인) 옛 몸만 차지한 픽셀(회전한 옛 몸 − 회전한 칼)을 지우고,
같은 회전·중심으로 새 리그 몸(웅크려 구르는 자세, 손 = 옛 손 자리)을 칼 아래에 넣는다. 몸이 없던 오버레이(울분 glow 등)는 건드리지 않는다.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import body20 as B  # noqa: E402
import rig20  # noqa: E402
import sync19 as S  # noqa: E402
import gen20  # noqa: E402

NAME = "greatsword_leap_slam"


def _kg():
    sys.path.insert(0, os.path.join(WORK, "combo56_moves_kg"))
    sys.path.insert(0, os.path.join(WORK, "combo58"))
    import kg_gs
    import rig34
    rig34.install()
    return kg_gs


def tuck_pose(d, handAt):
    if d in ("left", "right"):
        return rig20.pose(crouch=12.0, tilt=28.0, lean_body=0.4, foot=((-3.0, 9), (5.0, 11)), handAt=handAt, head=2, flame=2,
                          eyeHot=1, pulse=1, reachFrac=1.06)
    if d in ("down", "up"):
        return rig20.pose(crouch=12.0, squash=0.22, lift=(9, 10), step=(1.0, -1.0), handAt=handAt, head=2, flame=2, eyeHot=1,
                          pulse=1, reachFrac=1.06, stanceW=1.0)
    return gen20.rig34.pose34(crouch=12.0, lean_f=2.0, lift=(9, 10), handAt=handAt, head=2, flame=2, eyeHot=1, pulse=1,
                              feet=((6.0, -1.0), (-6.0, 1.5)), reachFrac=1.06)


def flip_parts(KG, d, i, angle):
    """→ (옛 몸만 마스크, 새 몸 합성 RGBA) — 448 캔버스 좌표."""
    ox, oy = KG.GS.CANVAS_OFF
    side = d in ("left", "right")
    if side:
        src_d, key, rot = d, KG.FLIP_SIDE, (-angle if d == "right" else angle)
    elif angle == 180:
        src_d, key, rot = KG.OPP[d], KG.FLIP_SIDE, 180
    else:
        src_d, key, rot = d, KG.FLIP_FRONT[angle], 0
    k, R, im, tip = KG._one(NAME, src_d, key, i)
    bb = R.image.getbbox()
    c = (round(ox + (bb[0] + bb[2]) / 2.0), round(oy + (bb[1] + bb[3]) / 2.0))
    hands = {h[-1]: R.anchors[h] for h in ("handR", "handL")}
    Rn = rig20.draw_rig(src_d, B.clean(tuck_pose(src_d, hands)))

    def canvas(img):
        cv = Image.new("RGBA", KG.GS.CANVAS, (0, 0, 0, 0))
        cv.alpha_composite(img, (ox, oy))
        return cv.rotate(rot, resample=Image.NEAREST, center=c) if rot else cv
    old_body = canvas(R.image)
    wcv = Image.new("RGBA", KG.GS.CANVAS, (0, 0, 0, 0))
    wcv.alpha_composite(im)
    weapon = wcv.rotate(rot, resample=Image.NEAREST, center=c) if rot else wcv
    ob, wp = old_body.getchannel("A").load(), weapon.getchannel("A").load()
    mask = Image.new("L", KG.GS.CANVAS, 0)
    mp = mask.load()
    for y in range(KG.GS.CANVAS[1]):
        for x in range(KG.GS.CANVAS[0]):
            if ob[x, y] and not wp[x, y]:
                mp[x, y] = 255
    return mask, canvas(Rn.image), (KG.GS.CANVAS_OFF)


def build(log):
    KG = _kg()
    body = "player_" + NAME
    meta = S.src_meta("player/v3/" + body)
    flips = meta.get("bodyInOverlayFrames") or [3, 4, 5]
    angles = {int(k): v for k, v in meta["flipAngles"].items()}
    parts = {}
    for d in meta["directions"]:
        for i in flips:
            parts[(d, i)] = flip_parts(KG, d, i, angles[i])
    changed = []
    import gridsheet
    for rel in gen20.family(body):
        jp = os.path.join(S.GRID, rel + ".json")
        if not os.path.exists(jp):
            continue
        m = gridsheet.load_meta(jp)
        im = Image.open(os.path.join(S.GRID, rel + ".png")).convert("RGBA")
        fw, fh, n = m["frameWidth"], m["frameHeight"], m["frames"]
        po = m["playerFrameOffset"]
        cells = S.cells(m, im)
        touched = False
        for (d, i), (mask, newb, coff) in parts.items():
            if d not in cells:
                continue
            cell = cells[d][i]
            dx, dy = coff[0] - po["x"], coff[1] - po["y"]
            mk = mask.crop((dx, dy, dx + fw, dy + fh))
            nb = newb.crop((dx, dy, dx + fw, dy + fh))
            mkp, cp = mk.load(), cell.load()
            hit = sum(1 for y in range(fh) for x in range(fw) if mkp[x, y] and cp[x, y][3])
            if hit < 30:
                continue
            keep = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
            kp = keep.load()
            for y in range(fh):
                for x in range(fw):
                    if cp[x, y][3] and not mkp[x, y]:
                        kp[x, y] = cp[x, y]
            out = nb.copy()
            out.alpha_composite(keep)
            cells[d][i] = out
            touched = True
        if touched:
            m["p20Flip"] = "P20: 공중제비 칸(%s)의 몸을 새 리그 몸으로 다시 합성(같은 회전·중심 — flipRender)" % flips
            S.write_grid(rel, cells, m)
            changed.append(rel)
    log["flip"] = changed
    print("flip", changed)
