"""56라운드 Q55 미리보기 — 검기·울분 오버레이를 새 칼·대검 기본기 6종 + 옛 칼 시트(draw·sheathe·special)에 적용한 결과.

preview_q55_ki_overlay.png      칼 5시트 × 4방향 × (원본 · ki1 · ki2 · ki3), 판정 프레임(없으면 가운데 프레임)
preview_q55_grudge_overlay.png  대검 4시트 × 4방향 × (원본 · grudge1~3), 판정 프레임
preview_q55_leap_flip.png       공중제비 칸(bodyInOverlayFrames f3~f5) × 8방향 — 원본 / grudge3 / 오버레이만(몸을 달구지 않는지)
gif/q55_*.gif                   한 동작 전체(원본 · 1 · 2 · 3단 나란히)
"""
from PIL import Image

import prev

KI = ["katana_counter", "katana_iai", "katana_draw", "katana_sheathe", "katana_special"]
GR = ["greatsword_tackle", "greatsword_brace_upswing", "greatsword_leap_slam", "greatsword_guard_rush"]


def geom(w):
    return (300, 360, (150, 262)) if w.startswith("greatsword") else (200, 230, (100, 190))


def pick(j):
    g = j.get("glowFrames") or []
    return g[0] if g else j["frames"] // 2


def grid(sheets, kind, out):
    cells, labels = [], []
    for w in sheets:
        j, _ = prev.sheet("weapons/v3/" + w)
        i = pick(j)
        W_, H_, o = geom(w)
        for d in j["directions"][:4]:
            for lv in (0, 1, 2, 3):
                ov = None if lv == 0 else "%s_%s%d" % (w, kind, lv)
                cells.append(prev.compose(w, ov, d, i, W=W_, H=H_, origin=o))
                labels.append("%s %s f%d %s" % (w.replace("greatsword_", "gs_").replace("katana_", "k_"), d, i,
                                                "base" if lv == 0 else "%s%d" % (kind, lv)))
    return prev.grid(cells, 8, out, scale=1, labels=labels,
                     title="56라운드 Q55 %s 오버레이 — 새 동작 적용(원본 · 1 · 2 · 3단)" % ("검기" if kind == "ki" else "울분"))


def leap_flip(out):
    w = "greatsword_leap_slam"
    j, wf = prev.sheet("weapons/v3/" + w)
    _, of = prev.sheet("weapons/v3/%s_grudge3" % w)
    W_, H_, o = geom(w)
    cells, labels = [], []
    for d in j["directions"]:
        for i in j["bodyInOverlayFrames"]:
            cells.append(prev.compose(w, None, d, i, W=W_, H=H_, origin=o))
            cells.append(prev.compose(w, "%s_grudge3" % w, d, i, W=W_, H=H_, origin=o))
            # 오버레이만 + 원본은 어둡게(몸 자리에 오버레이 픽셀이 없는지)
            base = prev.compose(w, None, d, i, W=W_, H=H_, origin=o)
            dim = Image.eval(base.convert("RGB"), lambda v: v // 4).convert("RGBA")
            off = j["playerFrameOffset"]
            dim.alpha_composite(of[d][i], (o[0] - 48 - off["x"], o[1] - 138 - off["y"]))
            cells.append(dim)
            labels += ["%s f%d base" % (d, i), "%s f%d grudge3" % (d, i), "%s f%d 오버레이만" % (d, i)]
    return prev.grid(cells, 9, out, scale=1, labels=labels,
                     title="Q55 공중제비 칸(몸이 무기 시트에 그려진 칸) — 울분은 칼날만 달굼(오른쪽 = 원본 어둡게 + 오버레이만)")


def gif(w, kind, d, out):
    j, _ = prev.sheet("weapons/v3/" + w)
    W_, H_, o = geom(w)
    frames = []
    for i in range(j["frames"]):
        cv = Image.new("RGBA", (W_ * 4, H_), prev.BG)
        for k, L in enumerate((0, 1, 2, 3)):
            cv.paste(prev.compose(w, None if L == 0 else "%s_%s%d" % (w, kind, L), d, i, W=W_, H=H_, origin=o), (k * W_, 0))
        frames.append(cv)
    return prev.gif(frames, j["frameDurationsMs"], out, scale=2 if not w.startswith("greatsword") else 1)


def main():
    outs = [grid(KI, "ki", "preview_q55_ki_overlay.png"), grid(GR, "grudge", "preview_q55_grudge_overlay.png"),
            leap_flip("preview_q55_leap_flip.png")]
    outs.append(gif("katana_counter", "ki", "right", "q55_ki_katana_counter_right.gif"))
    outs.append(gif("katana_iai", "ki", "right", "q55_ki_katana_iai_right.gif"))
    outs.append(gif("katana_draw", "ki", "down", "q55_ki_katana_draw_down.gif"))
    outs.append(gif("greatsword_leap_slam", "grudge", "right", "q55_grudge_greatsword_leap_slam_right.gif"))
    outs.append(gif("greatsword_leap_slam", "grudge", "down", "q55_grudge_greatsword_leap_slam_down.gif"))
    outs.append(gif("greatsword_tackle", "grudge", "down-right", "q55_grudge_greatsword_tackle_downright.gif"))
    outs.append(gif("greatsword_brace_upswing", "grudge", "left", "q55_grudge_greatsword_brace_upswing_left.gif"))
    return outs


if __name__ == "__main__":
    print("\n".join(main()))
