"""그로기 미리보기 — 몸 + 휴대 무기 + 머리 위 소용돌이."""
import prev
import rk
from PIL import Image


def cell(weapon, d, i, W=200, H=230, origin=(100, 200)):
    bj, bf = prev.sheet("player/v3/player_groggy")
    wj, wf = prev.sheet("weapons/v3/%s_carry_groggy" % weapon)
    sj, sf = prev.sheet("fx/v3/player_groggy_swirl")
    cv = Image.new("RGBA", (W, H), prev.BG)
    bx, by = origin[0] - bj["pivot"]["x"], origin[1] - bj["pivot"]["y"]
    cv.alpha_composite(bf[d][i], (bx, by))
    off = wj["playerFrameOffset"]
    cv.alpha_composite(wf[d][i], (origin[0] - 48 - off["x"], origin[1] - 138 - off["y"]))
    ht = bj["headTopAnchors"][d][i]
    si = int(sum(bj["frameDurationsMs"][:i]) // 125) % 6
    cv.alpha_composite(sf["any"][si], (int(bx + ht[0] - sj["pivot"]["x"]), int(by + ht[1] + bj["swirlOffsetY"] - sj["pivot"]["y"])))
    return cv


def main():
    outs = []
    for weapon in ("katana", "greatsword"):
        cells, labels = [], []
        for d in ("down", "up", "left", "right"):
            for i in range(10):
                cells.append(cell(weapon, d, i)); labels.append("%s %s f%d" % (weapon[:2], d, i))
        outs.append(prev.grid(cells, 10, "preview_groggy_%s_x2.png" % weapon, scale=2, labels=labels,
                              title="player_groggy + %s_carry_groggy + player_groggy_swirl · 10 × 150ms = 1.5초 루프" % weapon))
        for d in ("down", "right"):
            outs.append(prev.gif([cell(weapon, d, i) for i in range(10)] * 2, 150, "groggy_%s_%s.gif" % (weapon, d)))
    return outs


if __name__ == "__main__":
    print(main())
