"""56라운드 Q62 미리보기 — 대검 가드 자세(greatsword_special)·뽑기(draw)·넣기(sheathe)에 울분 오버레이.

preview_q62_grudge_guard.png  가드 유지 칸(f3) · 밀쳐내기 칸(f8) × 4방향 × (원본 · grudge1~3)
preview_q62_grudge_drawsheathe.png  뽑기 f4 · 넣기 f2 × 4방향 × (원본 · grudge1~3)
gif/q62_grudge_greatsword_special_<dir>.gif  가드 전체(원본 · 1 · 2 · 3단 나란히)
"""
import prev
import prev_q55

ROWS_GUARD = [("greatsword_special", 3), ("greatsword_special", 8)]
ROWS_DS = [("greatsword_draw", 4), ("greatsword_sheathe", 2)]


def grid(rows, out, title):
    cells, labels = [], []
    for w, i in rows:
        j, _ = prev.sheet("weapons/v3/" + w)
        W_, H_, o = prev_q55.geom(w)
        for d in j["directions"]:
            for lv in (0, 1, 2, 3):
                cells.append(prev.compose(w, None if lv == 0 else "%s_grudge%d" % (w, lv), d, i, W=W_, H=H_, origin=o))
                labels.append("%s %s f%d %s" % (w.replace("greatsword_", "gs_"), d, i, "base" if lv == 0 else "grudge%d" % lv))
    return prev.grid(cells, 8, out, scale=1, labels=labels, title=title)


def main():
    outs = [grid(ROWS_GUARD, "preview_q62_grudge_guard.png", "56라운드 Q62 울분 — 대검 가드 자세(유지 f3 · 밀쳐내기 f8)"),
            grid(ROWS_DS, "preview_q62_grudge_drawsheathe.png", "56라운드 Q62 울분 — 대검 뽑기 f4 · 넣기 f2")]
    for d in ("down", "up", "left", "right"):
        outs.append(prev_q55.gif("greatsword_special", "grudge", d, "q62_grudge_greatsword_special_%s.gif" % d))
    return outs


if __name__ == "__main__":
    print("\n".join(str(o) for o in main()))
