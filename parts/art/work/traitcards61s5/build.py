#!/usr/bin/env python3
"""61 단계 5 개성 카드 그림 65장 — Gemini 콘셉트(raw/<id>_<tag>.jpg) → LOPAD 팔레트 도트 128×128 → assets/sprites/ui_traits/<id>.png.

python3 build.py [id ...] [--dry]   (결정적 — raw 와 이 파일의 OPTS/FIX 만 입력)
이후 python3 preview.py 로 무기별 모음 미리보기·검사.
"""
import os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit, cards as C  # noqa

OUT = os.path.join(kit.ROOT, "assets/sprites/ui_traits")
DEFAULT_TAG = "b"
# id → 채택한 원본 태그 (기본 b). c = 1차 검수에서 복잡해 1배에서 안 읽힌 카드를 단순한 장면 문장으로 다시 받은 것
CHOICE = {cid: "c" for cid in (
    "katana_k_bladeBind", "katana_k_groundPin", "res_katana_breach",
    "greatsword_g_quakeGuard", "greatsword_g_guardPull", "greatsword_g_shoulderFlip", "greatsword_g_ramWall",
    "res_greatsword_weight", "dagger_d_dashPierce", "dagger_d_shadowKnot", "dagger_twinBrand",
    "bow_b_rainSnare", "res_bow_weight")}
OPTS = {}        # id → card_pixels 인자(crop·zoom·dx·dy·contrast·lift …)
FIX = {}         # id → [("px", x, y, 색) | ("line", x0, y0, x1, y1, 색[, "opaque"]), ...] 손 보정(128 좌표, 외곽선 뒤에 칠함)

# 단검 쌍낙인: 낙인이 '옮겨 붙는' 표시가 1배에서 안 보임 → 왼쪽 병사 가슴 → 오른쪽 병사 가슴으로 X 위를 넘는 붉은 점선 호
# + 양쪽 가슴 낙인 발톱 자국 3줄(R2) + 도착 쪽 화살촉
def _claw(x, y):
    return [("line", x + i * 2, y, x + i * 2 + 2, y + 4, "R2", "opaque") for i in range(3)]


FIX["dagger_twinBrand"] = (
    [("arc", 26, 40, 64, -2, 102, 44, "R0", 4, 2), ("arc", 26, 39, 64, -3, 102, 43, "R2", 4, 2)]
    + _claw(21, 45) + _claw(101, 48)
    + [("line", 98, 39, 102, 43, "R2"), ("line", 104, 38, 102, 43, "R2")])

# 활 화살 그물: 원본의 2px 청회 그물줄이 축소에서 사라짐 → 바닥 화살 8개를 잇는 고리 + 화살→묶인 무리 살 + 몸을 감는 띠 2줄(C1 #9ab0d8)
_NET_ARROWS = [(46, 48), (37, 75), (40, 95), (61, 102), (86, 96), (100, 93), (109, 66), (98, 56)]
_NET_HUB = [(60, 70), (64, 78), (72, 80), (80, 78), (86, 72), (84, 62), (70, 58), (62, 62)]
FIX["bow_b_rainSnare"] = (
    [("line", *a, *b, "C0") for a, b in zip(_NET_ARROWS, _NET_ARROWS[1:] + _NET_ARROWS[:1])]
    + [("line", *a, *h, "C1") for a, h in zip(_NET_ARROWS, _NET_HUB)]
    + [("line", 56, 66, 90, 64, "C1", "opaque"), ("line", 57, 75, 89, 74, "C1", "opaque")])


def make(cid, tag=None):
    card = C.by_id()[cid]
    tag = tag or CHOICE.get(cid, DEFAULT_TAG)
    raw = Image.open(os.path.join(HERE, "raw", f"{cid}_{tag}.jpg")).convert("RGB")
    idx = kit.card_pixels(raw, card[1], **OPTS.get(cid, {}))
    for op in FIX.get(cid, []):
        if op[0] == "px":
            idx[op[2]][op[1]] = op[3]
        elif op[0] == "arc":   # 2차 베지어 점선 ("arc", x0,y0, cx,cy, x1,y1, 색, 켬, 끔)
            _, x0, y0, cx, cy, x1, y1, n, on, off = op
            pts = []
            for i in range(241):
                t = i / 240
                x = round((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1)
                y = round((1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1)
                if not pts or pts[-1] != (x, y):
                    pts.append((x, y))
            for i, (x, y) in enumerate(pts):
                if i % (on + off) < on and 0 < x < 127 and 0 < y < 127:
                    idx[y][x] = n
        elif op[0] == "line":
            _, x0, y0, x1, y1, n = op[:6]
            only = op[6] if len(op) > 6 else None   # only="opaque" 면 그림 위에만
            steps = max(abs(x1 - x0), abs(y1 - y0), 1)
            for i in range(steps + 1):
                x = round(x0 + (x1 - x0) * i / steps)
                y = round(y0 + (y1 - y0) * i / steps)
                if 0 < x < 127 and 0 < y < 127 and (only != "opaque" or idx[y][x] is not None):
                    idx[y][x] = n
    return kit.to_image(idx)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry" in sys.argv
    ids = args or [c[0] for c in C.CARDS]
    os.makedirs(OUT, exist_ok=True)
    import json
    logp = os.path.join(HERE, "prompts.json")
    log = json.load(open(logp, encoding="utf-8"))
    for cid in ids:
        if cid in log["cards"]:
            log["cards"][cid]["chosen"] = CHOICE.get(cid, DEFAULT_TAG)
            log["cards"][cid]["handFix"] = len(FIX.get(cid, []))
    if not dry:
        json.dump(log, open(logp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for cid in ids:
        im = make(cid)
        if not dry:
            im.save(os.path.join(OUT, cid + ".png"), optimize=True)
        print(cid, "ok")


if __name__ == "__main__":
    main()
