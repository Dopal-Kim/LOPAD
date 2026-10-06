"""61 단계 6 (P14 §2) — 대검 '용암' · 활 '비취' 색 정체성 (계약 art §28). 작업 폴더 parts/art/work/color61s6_gb/

방법 = '램프만 바꿔 다시 굽기': 원 그림·틀·트림·피벗·프레임·ms 는 그대로 두고, 빛나는 색(호박·금빛·갈색 재)을
같은 밝기 순서의 무기 램프(ramps.py)로 1:1 교체한다. 알파는 손대지 않으므로 아틀라스 frame 사각형·trim 이 그대로다.
원 빌드 스크립트(fx_v3·combo56_fx·awaken60·weapons61·growth61·traits61s5_*·traitcards61s5 …)는 열 개가 넘고
뒤 라운드의 손질(아틀라스 변환·다시 그림)이 겹겹이 얹혀 있어, 각각을 다시 돌리면 이번 색 말고도 다른 차이가 생길 수 있다 —
그래서 '현재 산출물'에 램프 교체를 얹는 후처리 단계로 둔다. 표가 멱등(키 ∩ 값 = ∅)이라 원 빌드를 다시 돌린 뒤 이 스크립트를
이어 돌리면 같은 결과가 된다.

대상(무기 w = greatsword | bow):
  fx      fx/v3/{w}_* · hit_{w}* · trait_{w}_* · trait_res_{w}_*(+_on)            색표 MAP[w]   (활 불화살·술별 = 술불 색 유지)
  overlay weapons/v3/{w}_*_awaken · greatsword_*_grudge1~3                          색표 MAP[w]
  v4      weapons/v4/{w}_*_{a1,a2}_* (빛·장식 색만) · 모든 v4 JSON 의 pathTint·trailTint  색표 V4[w]
  looks   looks/{w}_* — 층 차이로 갈래 덧붙임만 다시 칠하고 _a2_<길> 은 새 pathTint 로 다시 구움, looks/{w}.json
  cards   ui_traits/{w}_* · res_{w}_* — 효과 덩어리만(주인공 몸의 호박 금은 그대로)

사용: python3 parts/art/work/color61s6_gb/build.py [--dry] [--weapon greatsword bow] [--only 이름부분 ...] [--part fx overlay v4 looks cards]
      → 바뀐 시트 목록 changed.json, 그다음 preview.py 로 전/후 그림.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import deque
from glob import glob

from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
SPR = os.path.join(ROOT, "assets", "sprites")
sys.path.insert(0, HERE)

import importlib.util  # noqa: E402

import ramps as R  # noqa: E402

_spec = importlib.util.spec_from_file_location("atlas57_build", os.path.join(ROOT, "parts", "art", "work", "atlas57", "build.py"))
_a57 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_a57)
dump_json, save_png = _a57.dump_json, _a57.save_png   # atlas57 — 같은 PNG 저장·JSON 모양

MAP = {"greatsword": R.GS_MAP, "bow": R.BOW_MAP}
V4 = {"greatsword": R.GS_MAP, "bow": R.BOW_V4}
CARD = {"greatsword": R.GS_CARD, "bow": R.BOW_CARD}
KEEP = {  # 무기 색을 입히지 않는 시트(이유는 README)
    "fx/v3/trait_bow_fireArrow": "불화살 = 술불(pool_liquor_fire) 로 이어지는 불 — 바닥 술불과 같은 호박 불 유지",
    "fx/v3/trait_bow_b_starDrunk": "술별 = 술에 붙는 불꽃 왕관 — 바닥 술불과 같은 호박 불 유지",
}
TAG = "61s6-P14-weapon-color"
HEX = re.compile(r'"(#[0-9a-fA-F]{6})"')


# ---------------------------------------------------------------- 공통
def rel(p):
    return os.path.relpath(p, SPR).replace(os.sep, "/")


def recolor_image(im: Image.Image, cmap: dict) -> tuple[Image.Image, int]:
    """RGB 만 색 → 색으로 바꾼다(알파 그대로). 반환 (그림, 바뀐 픽셀 수)."""
    im = im.convert("RGBA")
    r, g, b, a = im.split()
    rgb = Image.merge("RGB", (r, g, b))
    present = {"#%02x%02x%02x" % c[1][:3] for c in (im.getcolors(1 << 24) or []) if c[1][3]}
    todo = [h for h in cmap if h in present]
    clash = present & {cmap[h] for h in todo}
    assert not clash, f"새 색이 이미 그림에 있음(색 합쳐짐): {sorted(clash)}"
    alpha_on = a.point(lambda v: 255 if v else 0)
    n = 0
    for h in todo:
        cr, cg, cb = R.rgb(h)
        m = ImageChops.multiply(ImageChops.multiply(r.point(lambda v, c=cr: 255 if v == c else 0),
                                                    g.point(lambda v, c=cg: 255 if v == c else 0)),
                                ImageChops.multiply(b.point(lambda v, c=cb: 255 if v == c else 0), alpha_on))
        hist = m.histogram()
        n += hist[255]
        rgb.paste(R.rgb(cmap[h]), (0, 0), m)
    out = Image.merge("RGBA", (*rgb.split(), a))
    return out, n


def recolor_json_text(text: str, cmap: dict) -> str:
    """메타 안 색 문자열(light·flash·trail·colorSwap 등)을 같은 표로. tagColor·legacy 는 표 키가 아니라 자연히 제외."""
    return HEX.sub(lambda m: '"%s"' % cmap.get(m.group(1).lower(), m.group(1)), text)


def note(meta: dict, weapon: str, how: str):
    meta["weaponColor"] = {
        "round": TAG,
        "weapon": weapon,
        "name": {"greatsword": "용암", "bow": "비취"}[weapon],
        "key": {"greatsword": "#ff5a2a", "bow": "#40e0a0"}[weapon],
        "secondary": {"greatsword": "검붉은 재", "bow": "바랜 금"}[weapon],
        "how": how,
        "source": "parts/art/work/color61s6_gb/build.py (ramps.py 색표)",
    }


def recolor_sheet(jpath: str, cmap: dict, weapon: str, dry: bool, how: str, tints=None):
    text = open(jpath, encoding="utf-8").read()
    meta = json.loads(text)
    d = os.path.dirname(jpath)
    pages = [t["image"] for t in meta["textures"]] if "textures" in meta else [meta["meta"]["image"] if "meta" in meta else meta["image"]]
    total = 0
    imgs = []
    for p in pages:
        im0 = Image.open(os.path.join(d, p)).convert("RGBA")
        im1, n = recolor_image(im0, cmap)
        total += n
        imgs.append((p, im0, im1, n))
    new_meta = json.loads(recolor_json_text(text, cmap))
    if tints is not None:
        tints(new_meta)
    if total:
        note(new_meta, weapon, how)
    elif "weaponColor" in meta:
        new_meta["weaponColor"] = meta["weaponColor"]   # 이미 바꾼 시트(멱등 재실행)
    changed_meta = new_meta != meta
    if not dry:
        for p, im0, im1, n in imgs:
            if n:
                save_png(im1, os.path.join(d, p))
        if changed_meta:
            out = dump_json(new_meta) if ("frames" in new_meta or "textures" in new_meta) else json.dumps(new_meta, ensure_ascii=False, indent=1)
            open(jpath, "w", encoding="utf-8").write(out)
    return total, changed_meta


# ---------------------------------------------------------------- 목록
def sheet_list(weapon: str, part: str):
    w = weapon
    if part == "fx":
        pats = [f"fx/v3/{w}_*.json", f"fx/v3/hit_{w}*.json", f"fx/v3/trait_{w}_*.json", f"fx/v3/trait_res_{w}_*.json"]
    elif part == "overlay":
        pats = [f"weapons/v3/{w}_*_awaken.json"] + ([f"weapons/v3/{w}_*_grudge[123].json"] if w == "greatsword" else [])
    elif part == "v4":
        pats = [f"weapons/v4/{w}_*.json"]
    else:
        return []
    out = []
    for pt in pats:
        out += glob(os.path.join(SPR, pt))
    return sorted(set(out))


def v4_tints(weapon):
    T = R.PATH_TINT[weapon]

    def fix(meta):
        b = meta.get("branch")
        if b in T:
            if "pathTint" in meta:
                meta["pathTint"] = {k: list(v) for k, v in T[b].items()}
            if "trailTint" in meta:
                meta["trailTint"] = {k: R.trail_tint(v) for k, v in T[b].items()}
                meta["trailTintRule"] = "61 단계 6: trailTint = pathTint 를 흰색 쪽으로 45% — 궤적 fx 가 이미 무기 색(용암·비취)이라 곱해도 어두워지지 않게 색 기울기만"
    return fix


# ---------------------------------------------------------------- looks (정지 그림 192)
def tint(im, rgb):
    """growth61/looks.py 와 같은 곱(정수 내림)."""
    px = im.load()
    out = im.copy()
    po = out.load()
    for y in range(im.height):
        for x in range(im.width):
            c = px[x, y]
            if c[3]:
                po[x, y] = (c[0] * rgb[0] // 255, c[1] * rgb[1] // 255, c[2] * rgb[2] // 255, 255)
    return out


def layer_recolor(top: Image.Image, under: Image.Image, cmap: dict) -> Image.Image:
    """top = under 위에 덧붙인 결과. under 와 다른 픽셀(= 덧붙인 층)만 색표로 바꾼다."""
    t, u = top.load(), under.load()
    out = top.copy()
    o = out.load()
    for y in range(top.height):
        for x in range(top.width):
            c = t[x, y]
            if c[3] and c != u[x, y]:
                h = "#%02x%02x%02x" % c[:3]
                if h in cmap:
                    o[x, y] = (*R.rgb(cmap[h]), c[3])
    return out


def build_looks(weapon: str, dry: bool, log: list):
    L = os.path.join(SPR, "looks")
    jp = os.path.join(L, f"{weapon}.json")
    meta = json.load(open(jp, encoding="utf-8"))
    base = Image.open(os.path.join(L, meta["base"])).convert("RGBA")
    cmap = V4[weapon]
    for bid, br in meta["branches"].items():
        a1o = Image.open(os.path.join(L, br["a1"])).convert("RGBA")
        a2o = Image.open(os.path.join(L, br["a2"])).convert("RGBA")
        gl = Image.open(os.path.join(L, br["a2Glow"])).convert("RGBA")
        # 원 구성 확인(옛 tint 로 다시 구우면 원 파일과 같아야 한다 — 첫 실행 때만 의미 있음)
        a1n = layer_recolor(a1o, base, cmap)
        a2n = layer_recolor(a2o, a1o, cmap)
        # a2 의 덧붙임 층 = a2o 와 a1o 가 다른 곳 → a1n 위에 다시 얹기
        a2c = a1n.copy()
        po, pn, pa = a2o.load(), a2n.load(), a2c.load()
        a1p = a1o.load()
        for y in range(a2o.height):
            for x in range(a2o.width):
                if po[x, y] != a1p[x, y]:
                    pa[x, y] = pn[x, y]
        T = R.PATH_TINT[weapon][bid]
        outs = {br["a1"]: a1n, br["a2"]: a2c}
        for pid, rgb in T.items():
            s3 = a2c.copy()
            s3.alpha_composite(tint(gl, rgb))
            outs[br["a2ByPath"][pid]] = s3
        for fn, im in outs.items():
            old = Image.open(os.path.join(L, fn)).convert("RGBA")
            if old.tobytes() != im.tobytes():
                log.append(f"looks/{fn}")
                if not dry:
                    save_png(im, os.path.join(L, fn))
        br["pathTint"] = {k: list(v) for k, v in T.items()}
    meta["pathTintRule"] = ("61 단계 6 (P14 §2): 길 강조색 = 무기 색 계열 안 두 변주 — 대검 '용암'(주홍·진홍) · 활 '비취'(비취 녹·바랜 금). "
                            "a1·a2 의 빛·장식 색도 같은 램프(parts/art/work/color61s6_gb/ramps.py)")
    note(meta, weapon, "갈래 덧붙임 층의 빛·장식 색 → 무기 램프, _a2_<길> = 새 pathTint 로 다시 구움 (base 그대로)")
    old = open(jp, encoding="utf-8").read()
    new = json.dumps(meta, ensure_ascii=False, indent=1)
    if old != new:
        log.append(f"looks/{weapon}.json")
        if not dry:
            open(jp, "w", encoding="utf-8").write(new)


# ---------------------------------------------------------------- 카드 (128 장면)
N8 = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]


def card_recolor(im: Image.Image, weapon: str):
    """효과 덩어리만 무기 램프로. 덩어리 = 밝은 호박·금 + 흰 심(8-이웃). 규칙:
    - 작고(<40) 둘레의 60% 이상이 주인공 검은 몸 색이면 = 주인공 몸의 호박 금(그대로)
    - 활: 바랜 금 화살줄(옅은 색)이 주황(불·술)보다 많은 덩어리만(불·술 웅덩이는 그대로).
      옅은 색(#eecc78 이상)이 절반을 넘는 덩어리 = 화살·화살줄(검은 외곽선이 있어도 주인공 금이 아님) → 바꿈
    - 바꾼 덩어리에 붙은 어두운 호박(가장자리)은 2걸음까지 따라 바꿈."""
    W, H = im.size
    px = im.load()
    hexat = [["#%02x%02x%02x" % px[x, y][:3] if px[x, y][3] else None for x in range(W)] for y in range(H)]
    bright, core, dark = set(R.CARD_BRIGHT), set(R.CARD_CORE), set(R.CARD_DARK)
    hero = set(R.CARD_HERO_DARK)
    seen = [[False] * W for _ in range(H)]
    cmap = CARD[weapon]
    out = im.copy()
    po = out.load()
    stats = {"comp": 0, "mapped": 0, "heroKeep": 0, "fireKeep": 0, "px": 0}
    for y0 in range(H):
        for x0 in range(W):
            if seen[y0][x0] or hexat[y0][x0] not in bright:
                continue
            comp, q = [], deque([(x0, y0)])
            seen[y0][x0] = True
            while q:
                x, y = q.popleft()
                comp.append((x, y))
                for dx, dy in N8:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and not seen[ny][nx] and hexat[ny][nx] in bright | core:
                        seen[ny][nx] = True
                        q.append((nx, ny))
            stats["comp"] += 1
            cs = set(comp)
            border = [hexat[y + dy][x + dx] for x, y in comp for dx, dy in N8
                      if 0 <= x + dx < W and 0 <= y + dy < H and (x + dx, y + dy) not in cs]
            nb = len(border) or 1
            strict_pale = weapon == "bow" and sum(1 for x, y in comp if hexat[y][x] in R.CARD_PALE[1:]) * 2 > len(comp)
            if not strict_pale and len(comp) < 40 and sum(1 for h in border if h in hero) / nb >= 0.6:
                stats["heroKeep"] += 1
                continue
            if weapon == "bow":
                pale = sum(1 for x, y in comp if hexat[y][x] in R.CARD_PALE)
                orange = sum(1 for x, y in comp if hexat[y][x] in R.CARD_ORANGE)
                if orange >= pale:
                    stats["fireKeep"] += 1
                    continue
            stats["mapped"] += 1
            # 가장자리 어두운 호박 따라가기(2걸음)
            front = list(comp)
            for _ in range(2):
                nxt = []
                for x, y in front:
                    for dx, dy in N8:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in cs and hexat[ny][nx] in dark:
                            cs.add((nx, ny))
                            nxt.append((nx, ny))
                front = nxt
            for x, y in cs:
                h = hexat[y][x]
                if h in cmap:
                    po[x, y] = (*R.rgb(cmap[h]), px[x, y][3])
                    stats["px"] += 1
    return out, stats


def build_cards(weapon: str, dry: bool, log: list, only=None):
    D = os.path.join(SPR, "ui_traits")
    res = {}
    for f in sorted(glob(os.path.join(D, f"{weapon}_*.png")) + glob(os.path.join(D, f"res_{weapon}_*.png"))):
        if only and not any(o in os.path.basename(f) for o in only):
            continue
        im = Image.open(f).convert("RGBA")
        out, st = card_recolor(im, weapon)
        res[os.path.basename(f)] = st
        if out.tobytes() != im.tobytes():
            log.append(rel(f))
            if not dry:
                save_png(out, f)
    return res


# ---------------------------------------------------------------- 실행
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--weapon", nargs="*", default=["greatsword", "bow"])
    ap.add_argument("--part", nargs="*", default=["fx", "overlay", "v4", "looks", "cards"])
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    R.check_idempotent()
    changed, meta_only, report = [], [], {}
    for w in a.weapon:
        for part in ("fx", "overlay", "v4"):
            if part not in a.part:
                continue
            for jp in sheet_list(w, part):
                name = rel(jp)[:-5]
                if a.only and not any(o in name for o in a.only):
                    continue
                if name in KEEP:
                    report[name] = "keep: " + KEEP[name]
                    continue
                if part == "v4" and "_a2_glow_" in name:
                    cmap, how = {}, ""
                else:
                    cmap = V4[w] if part == "v4" else MAP[w]
                    how = {"fx": "이펙트 호박·갈색 재·금빛 → 무기 램프", "overlay": "각성·울분 빛 → 무기 램프",
                           "v4": "갈래 외형의 빛·장식 색 → 무기 램프"}[part]
                n, mc = recolor_sheet(jp, cmap, w, a.dry, how, tints=v4_tints(w) if part == "v4" else None)
                if n:
                    changed.append(name)
                    report[name] = n
                elif mc:
                    meta_only.append(name)
        if "looks" in a.part:
            lg = []
            build_looks(w, a.dry, lg)
            changed += lg
        if "cards" in a.part:
            lg = []
            report["cards_" + w] = build_cards(w, a.dry, lg, a.only)
            changed += lg
    print(f"그림 바뀜 {len(changed)} · 메타만(pathTint) {len(meta_only)}" + (" (dry)" if a.dry else ""))
    if not a.dry and changed:
        json.dump({"changed": changed, "metaOnly": meta_only, "report": report}, open(os.path.join(HERE, "changed.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
