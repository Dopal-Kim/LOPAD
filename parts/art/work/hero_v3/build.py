#!/usr/bin/env python3
"""주인공 v3 1단계 검수용 세트 빌드 (52라운드 Q7·Q8) — 대기 6 · 걷기 8 × 4방향.

출력은 전부 이 폴더(parts/art/work/hero_v3/) — assets/** 는 검수 뒤에 쓴다.
  out/player_idle.png/.json, out/player_walk.png/.json   시트 초안 (계약 §1 규약 + §11: pixelScale 0.5, pivot)
  preview_frames_x2.png        전 프레임 2배 (빨간 점 = 피벗)
  preview_idle.gif / preview_walk.gif          실제 크기(64×96 도트 1배 = 1920×1080 내부 렌더에서의 크기), 4방향 나란히
  preview_idle_x3.gif / preview_walk_x3.gif    같은 것 3배(검수 편의)
  preview_mock_lit.png         외곽 v2 바닥(32px 타일 → 2배 표시) 위 1배 합성 + 조명, 기존 v2 32×48(2배 표시)과 비교
  stats.json                   색 수 · 반투명 · 프레임 정보
사용: python3 parts/art/work/hero_v3/build.py
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

import hero
import v3kit
from v3kit import kit

OUTDIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(OUTDIR, "../../../.."))
SHEETS = os.path.join(OUTDIR, "out")
FW, FH, PIV = hero.FW, hero.FH, hero.PIV
BG = (46, 48, 56, 255)

FONT = None
for f in ["/usr/share/fonts/truetype/unifont/unifont.ttf", "/usr/share/fonts/opentype/unifont/unifont.otf"]:
    if os.path.exists(f):
        FONT = ImageFont.truetype(f, 16)
        break
FONT = FONT or ImageFont.load_default()


def label(d, x, y, t):
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        d.text((x + dx, y + dy), t, font=FONT, fill=(0, 0, 0))
    d.text((x, y), t, font=FONT, fill=(235, 236, 237))


def render_all():
    res = {}
    for act, (fn, ms, loop) in hero.ACTIONS.items():
        res[act] = {d: [hero.draw(d, p) for p in fn(d)] for d in hero.DIRS}
    return res


def write_sheet(act, frames_by_dir):
    fn, ms, loop = hero.ACTIONS[act]
    n = len(frames_by_dir["down"])
    sheet = Image.new("RGBA", (FW * n, FH * len(hero.DIRS)), (0, 0, 0, 0))
    for r, d in enumerate(hero.DIRS):
        for c, im in enumerate(frames_by_dir[d]):
            sheet.paste(im, (c * FW, r * FH))
    os.makedirs(SHEETS, exist_ok=True)
    sheet.save(os.path.join(SHEETS, "player_%s.png" % act))
    meta = {
        "image": "player_%s.png" % act,
        "action": act,
        "frameWidth": FW,
        "frameHeight": FH,
        "frames": n,
        "directions": hero.DIRS,
        "layout": "rows = directions (down, up, left, right), columns = frames",
        "frameIndex": "row * frames + column",
        "fps": round(1000 * n / sum(ms), 2),
        "frameDurationsMs": ms,
        "loop": loop,
        "pivot": {"x": PIV[0], "y": PIV[1]},
        "pixelScale": 0.5,
        "palette": "parts/art/palette/lopad.json (gray + 1층 램프 16~27, 런타임 스왑) + v2 재질 블록 SL·WD·PL (parts/art/work/v2_outer/palette_v2_proposal.json, 임시·고정색)",
        "emissiveColors": [kit.tohex(c) for c in (kit.A[23], kit.A[25], kit.A[26])],
        "source": "parts/art/work/hero_v3/build.py (52라운드 Q7·Q8 1단계 검수용 초안)",
        "note": "v3 2배 밀도 — 64×96 도트, 화면상 32×48 (계약 §11). 개념 gemini/concept_char/hero3_b. 검수 전 초안: assets 미반영.",
    }
    with open(os.path.join(SHEETS, "player_%s.json" % act), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return sheet


def preview_frames_x2(allf):
    k, pad = 2, 6
    rows = []
    for act in hero.ACTIONS:
        for d in hero.DIRS:
            rows.append((act, d, allf[act][d]))
    n = max(len(r[2]) for r in rows)
    W = 90 + n * (FW * k + pad)
    H = 8 + len(rows) * (FH * k + pad)
    out = Image.new("RGBA", (W, H), BG)
    dr = ImageDraw.Draw(out)
    for j, (act, d, frames) in enumerate(rows):
        y = 8 + j * (FH * k + pad)
        label(dr, 6, y + FH * k // 2 - 18, act)
        label(dr, 6, y + FH * k // 2, d)
        for i, im in enumerate(frames):
            x = 90 + i * (FW * k + pad)
            out.alpha_composite(im.resize((FW * k, FH * k), Image.NEAREST), (x, y))
            dr.rectangle((x + PIV[0] * k - 1, y + PIV[1] * k - 1, x + PIV[0] * k, y + PIV[1] * k), fill=(220, 60, 60, 255))
    out.save(os.path.join(OUTDIR, "preview_frames_x2.png"))


def gif(allf, act, k, name):
    fn, ms, loop = hero.ACTIONS[act]
    n = len(allf[act]["down"])
    frames = []
    for i in range(n):
        im = Image.new("RGBA", ((FW + 8) * 4 * k, (FH + 8) * k), (34, 36, 42, 255))
        for c, d in enumerate(hero.DIRS):
            f = allf[act][d][i].resize((FW * k, FH * k), Image.NEAREST)
            im.alpha_composite(f, (c * (FW + 8) * k + 4 * k, 4 * k))
        frames.append(im.convert("RGB").quantize(colors=128, dither=Image.Dither.NONE))
    frames[0].save(os.path.join(OUTDIR, name), save_all=True, append_images=frames[1:], duration=ms, loop=0, disposal=2)


def mock(allf):
    """외곽 v2 albedo 목업(960×540, 32px 타일)의 바닥 일부를 2배로 키워 1920×1080 내부 렌더 크기로 보고,
    그 위에 v3(1배)와 기존 v2 주인공(2배 최근접)을 나란히 놓고 조명 합성."""
    alb = Image.open(os.path.join(ROOT, "parts/art/work/v2_outer/preview_mock_albedo.png")).convert("RGBA")
    crop = alb.crop((40, 290, 280, 425)).resize((480, 270), Image.NEAREST)
    canvas = crop.copy()
    dr = ImageDraw.Draw(canvas)
    old = Image.open(os.path.join(ROOT, "assets/sprites/player/v2/player_idle.png")).crop((0, 0, 32, 48)).resize((64, 96), Image.NEAREST)
    charger = Image.open(os.path.join(ROOT, "assets/sprites/enemies/v2/charger_idle.png")).crop((0, 0, 32, 48)).resize((64, 96), Image.NEAREST)
    spots = [(40, 150, old, False),
             (130, 150, allf["idle"]["down"][2], True), (200, 150, allf["walk"]["right"][2], True),
             (270, 150, allf["walk"]["up"][4], True), (340, 150, allf["walk"]["left"][6], True),
             (410, 150, charger, False)]
    lights = []
    for x, y, im, hero_ in spots:
        dr.ellipse((x + 8, y + 86, x + 56, y + 98), fill=(10, 11, 14, 255))    # 발밑 그림자(목업 — 시스템이 그림)
    for x, y, im, hero_ in spots:
        canvas.alpha_composite(im, (x, y))
        if hero_:
            lights.append({"x": x + 32, "y": y + 50, "color": "#b0611a", "radius": 70, "intensity": 0.45})   # 몸 혼불 빛(임시)
    lights.append({"x": 40 + 32, "y": 150 + 50, "color": "#b0611a", "radius": 70, "intensity": 0.45})          # 기존 v2 도 같은 조건
    lit = kit.light_scene(canvas, lights, scale=2)
    out = Image.new("RGB", (lit.width * 2 + 12, lit.height + 30), (18, 19, 22))
    out.paste(lit, (0, 30))
    out.paste(lit.crop((110, 132, 350, 267)).resize((480, 270), Image.NEAREST), (lit.width + 12, 30))
    d = ImageDraw.Draw(out)
    label(d, 4, 6, "1배(1920×1080 내부 렌더 기준): 왼쪽 = 기존 v2(반려, 2배 표시) · v3 대기/우/상/좌 · 결사병 v2(2배)   |   오른쪽 = v3 부분 2배")
    out.save(os.path.join(OUTDIR, "preview_mock_lit.png"))


def stats(allf):
    allc = set()
    partial = False
    per = {}
    for act in allf:
        for d in allf[act]:
            for i, im in enumerate(allf[act][d]):
                cs = v3kit.colors_of(im)
                allc |= cs
                partial = partial or v3kit.has_alpha_partial(im)
            per[act] = len(allf[act]["down"])
    data = {"colors": len(allc), "colorBudget": 30, "semiTransparent": partial, "frames": per,
            "size": [FW, FH], "pivot": list(PIV), "pixelScale": 0.5,
            "palette": sorted("#%02x%02x%02x" % c for c in allc)}
    with open(os.path.join(OUTDIR, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return data


def main():
    allf = render_all()
    for act in allf:
        write_sheet(act, allf[act])
    preview_frames_x2(allf)
    for act in allf:
        gif(allf, act, 1, "preview_%s.gif" % act)
        gif(allf, act, 3, "preview_%s_x3.gif" % act)
    mock(allf)
    s = stats(allf)
    print("colors", s["colors"], "/ 30 · semiTransparent", s["semiTransparent"], "· frames", s["frames"])


if __name__ == "__main__":
    main()
