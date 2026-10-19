"""P21 아트 B 단계 4 — 처형 동작 hero_execute_{katana,greatsword,dagger,bow} (몸 + 무기 오버레이, 0.45초).

방식: 이미 P20 새 몸으로 렌더된 공격 시트(몸 player/v3 + 무기 weapons/v3, 프레임마다 손·무기 동기 완료)에서 처형에 맞는 프레임을 골라
0.45초로 다시 짠다(몸·무기 같은 프레임 번호 → 동기 그대로). 타격 뒤 프레임은 날에 피(검붉은 BL)를 묻힌다.
활은 단검 역수 3타 몸(앞·아래로 박기)에 '손에 쥔 화살' 오버레이를 새로 그린다(grip → 날끝 방향, 화살촉 + 깃).

python3 parts/art/work/gore21/execute_build.py [katana greatsword dagger bow] [--no-assets]
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "atlas57"))
sys.path.insert(0, os.path.join(HERE, "..", "v2_outer"))
import gk  # noqa: E402
import gridsheet  # noqa: E402
import kit  # noqa: E402
from gk import BL0, BL1, BL2, BL3, G  # noqa: E402
from PIL import Image  # noqa: E402

SRC = "parts/art/work/gore21/execute_build.py (P21 처형 — P20 몸 공격 시트 프레임 재구성 + 날 피)"
PLAN = {   # 무기: (원 시트, 고른 원 프레임, ms(합 450), 타격 프레임(새 번호), 사망 변형, 설명)
    "katana": ("katana_iai", [3, 7, 8, 9, 10, 10, 11, 12], [60, 30, 30, 40, 80, 60, 80, 70], 2, "behead",
               "목 베기 — 칼집에 넣은 채 낮게 겨눔(0) → 발도(1) → 목 높이 수평 일섬(2·3) → 잔심(4·5) → 피 털기 chiburi(6) → 납도 시작(7)"),
    "greatsword": ("greatsword_cleave", [2, 4, 7, 8, 9, 10, 11, 13, 17], [50, 60, 40, 30, 30, 90, 50, 50, 50], 4, "bisect",
                   "내려쳐 두 동강 — 머리 위로 치켜듦(0·1) → 끌어내림(2·3) → 정수리부터 내려찍음(4) → 땅에 박힘(5) → 끌어 뽑음(6·7) → 다시 듦(8)"),
    "dagger": ("dagger_backstab", [0, 1, 2, 3, 4, 5, 6, 7, 8], [40, 40, 50, 25, 45, 70, 70, 60, 50], 4, "collapse",
               "뒤로 돌아 목 찌르기 — 등 뒤로 파고듦(0·1) → 웅크림(2) → 목덜미로 박음(3·4) → 깊이(5) → 비틂(6) → 뜯어냄(7, 큰 분출) → 물러남(8)"),
    "bow": ("dagger_combo3", [0, 1, 2, 3, 4, 5, 6, 7], [70, 60, 30, 40, 80, 60, 60, 50], 2, "pinned",
            "근접 화살 박기 — 화살을 역수로 쥐고 치켜듦(0·1) → 앞·아래로 목에 박음(2·3) → 눌러 넘어뜨림(4~6) → 손을 뗌(7). 화살은 적에게 남는다(사망 변형 pinned)"),
}
PER_FRAME_BODY = ("handAnchors", "scarAnchor", "weaponOffsetDots", "eyeAnchors", "chestAnchors", "koiguchiAnchors")
PER_FRAME_WEAPON = ("depthByFrame", "handAnchors", "gripAnchors", "bladeTipAnchors", "koiguchiAnchors")
KEEP_BODY = ("frameWidth", "frameHeight", "directions", "layout", "frameIndex", "pivot", "pixelScale", "palette", "emissiveColors",
             "dirTransform", "dirTransformNote", "directionRows", "directionNote", "bodyRig", "p20")
KEEP_WEAPON = ("frameWidth", "frameHeight", "directions", "layout", "frameIndex", "pivot", "pixelScale", "palette", "anchor",
               "playerFrameOffset", "depth", "occlusionBaked", "depthNote", "gripHand", "dirTransform", "dirTransformNote",
               "directionRows", "directionNote", "twoHanded", "reverseGrip", "colorBudget")


def grid(rel):
    p = os.path.join(gk.SPR, rel + ".json")
    m = gridsheet.load_meta(p)
    im = gridsheet.open_grid(p)
    fw, fh, n = m["frameWidth"], m["frameHeight"], m["frames"]
    return m, {d: [im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(n)] for r, d in enumerate(m["directions"])}


def remap(m, keys, picks):
    out = {}
    for k in keys:
        v = m.get(k)
        if isinstance(v, dict) and all(isinstance(x, list) for x in v.values()):
            out[k] = {d: [lst[i] for i in picks] for d, lst in v.items()}
    return out


def bloody_blade(im, grip, tip, k_after, seed):
    """날 위 피: grip→tip 선 근처(±2) 불투명 픽셀 중 날 쪽 35~95% 를 듬성듬성 BL 로(밝은 날일수록 BL2, 끝 쪽 방울 1)."""
    if not grip or not tip:
        return
    px = im.load()
    gx, gy = grip
    tx, ty = tip
    L = math.hypot(tx - gx, ty - gy)
    if L < 4:
        return
    ux, uy = (tx - gx) / L, (ty - gy) / L
    W, H = im.size
    for y in range(max(0, int(min(gy, ty)) - 3), min(H, int(max(gy, ty)) + 4)):
        for x in range(max(0, int(min(gx, tx)) - 3), min(W, int(max(gx, tx)) + 4)):
            c = px[x, y]
            if not c[3]:
                continue
            t = ((x - gx) * ux + (y - gy) * uy) / L
            sdn = (x - gx) * -uy + (y - gy) * ux
            # 2차 비평: 해시 점박이 = 녹 → 한쪽 날 가장자리를 따라 이어진 피 띠 + 끊긴 마디(낮은 주파수)
            if 0.4 < t < 0.97 and -0.6 <= sdn < 2.6 and int(t * 13 + (seed % 5)) % 4 != 0 and t < 0.4 + 0.6 * k_after:
                L_ = 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
                px[x, y] = gk.hexrgb(BL1 if (sdn > 1.2 or L_ < 90) else BL2)
    # 날끝 아래로 맺힌 방울
    bx, by = int(round(tx - ux * 2)), int(round(ty - uy * 2)) + 2
    if 0 <= bx < W and 0 <= by < H and not px[bx, by][3]:
        px[bx, by] = gk.hexrgb(BL2)


def draw_arrow(im, grip, tip):
    """손에 역수로 쥔 화살: grip 에서 날끝 방향으로 촉(길이 30), 반대쪽으로 깃(10). 쥔 손 근처 2도트는 비움(주먹이 가림)."""
    gx, gy = grip
    ux, uy = tip[0] - gx, tip[1] - gy
    L = math.hypot(ux, uy) or 1
    ux, uy = ux / L, uy / L
    nx, ny = -uy, ux
    head = (gx + ux * 30, gy + uy * 30)
    nock = (gx - ux * 12, gy - uy * 12)
    for i, (x, y) in enumerate(gk.line_cells(nock[0], nock[1], head[0], head[1])):
        if math.hypot(x - gx, y - gy) < 2.2:
            continue
        gk_put(im, x, y, kit.WD[4] if i % 6 else kit.WD[3])
    for j in range(4):                                  # 쇠 촉(삼각)
        w = (3 - j) * 0.6
        cx, cy = head[0] - ux * j, head[1] - uy * j
        for s in (-1, 0, 1):
            gk_put(im, cx + nx * s * w, cy + ny * s * w, G[11] if s <= 0 else G[8])
    gk_put(im, head[0] + ux, head[1] + uy, G[13])
    for j in range(5):                                  # 깃
        cx, cy = nock[0] + ux * j, nock[1] + uy * j
        w = 2 if j < 3 else 1
        for s in (1, -1):
            for q in range(1, w + 1):
                gk_put(im, cx + nx * s * q - ux * q * 0.5, cy + ny * s * q - uy * q * 0.5, G[9] if s > 0 else G[6])


def gk_put(im, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < im.width and 0 <= y < im.height:
        im.putpixel((x, y), gk.hexrgb(c))


def build(weapon, assets):
    src, picks, ms, impact, variant, desc = PLAN[weapon]
    assert sum(ms) == 450 and len(ms) == len(picks) and 6 <= len(picks) <= 10, weapon
    name = "hero_execute_" + weapon
    bm, bf = grid("player/v3/player_" + src)
    wm, wf = grid("weapons/v3/" + src)
    starts = [sum(ms[:i]) for i in range(len(ms))]
    common = {"frameDurationsMs": ms, "fps": round(1000.0 * len(ms) / 450, 2), "loop": False, "impactFrame": impact,
              "hitFrames": [impact], "timingMs": {"hitAt": starts[impact], "total": 450},
              "execute": {"weapon": weapon, "deathVariant": variant, "invulnMs": 450, "slowmo": {"scale": 0.3, "ms": 120, "atMs": starts[impact]},
                          "note": "계약 dark-brutal §4 — 0.45초 무적 · 타격 프레임 시작에 슬로 0.3배 120ms·줌 펀치 · 끝나면 ENEMY_DIED + DEATH_VARIANT"},
              "sourceSheet": src, "sourceFrames": picks, "label": desc, "source": SRC, "version": "v3-p21"}
    brows = [[bf[d][i] for i in picks] for d in bm["directions"]]
    bmeta = {k: bm[k] for k in KEEP_BODY if k in bm}
    bmeta.update(remap(bm, PER_FRAME_BODY, picks))
    bmeta.update(common)
    bmeta.update({"action": "execute_" + weapon, "weapon": weapon,
                  "weaponOverlayV3": "weapons/v3/%s (같은 프레임 번호·같은 시각에 겹침 — 무기 오버레이 동기)" % name,
                  "note": "처형 몸(P21). " + desc + ". 몸·무기 프레임은 원 시트 sourceFrames 를 그대로 가져와 손·무기 동기 유지(P20 새 몸)"})
    wrows = []
    seed = 0
    for d in wm["directions"]:
        row = []
        for j, i in enumerate(picks):
            im = wf[d][i].copy()
            seed += 17
            grip = (wm.get("gripAnchors") or {}).get(d, [None] * 99)[i]
            tip = (wm.get("bladeTipAnchors") or {}).get(d, [None] * 99)[i]
            if weapon == "bow":
                dag = im
                im = Image.new("RGBA", im.size, (0, 0, 0, 0))   # 단검 그림 대신 쥔 화살
                draw_arrow(im, grip, tip)
                # 가림 굽기: 몸 위에 겹친 화살 픽셀은 원 단검이 보이던 자리에서만 남김(몸 뒤로 간 부분은 지움 — occlusionBaked 유지)
                off = wm["playerFrameOffset"]
                body = bf[d][i]
                ip, dp, bp = im.load(), dag.load(), body.load()
                for yy in range(im.height):
                    for xx in range(im.width):
                        if ip[xx, yy][3]:
                            bx, by = xx - off["x"], yy - off["y"]
                            if 0 <= bx < body.width and 0 <= by < body.height and bp[bx, by][3] and not dp[xx, yy][3]:
                                ip[xx, yy] = (0, 0, 0, 0)
                if j >= impact:
                    bloody_blade(im, grip, (grip[0] + (tip[0] - grip[0]) * 30 / max(1, math.dist(grip, tip)),
                                            grip[1] + (tip[1] - grip[1]) * 30 / max(1, math.dist(grip, tip))), 1.0, seed)
            elif j >= impact:
                bloody_blade(im, grip, tip, min(1.0, 0.5 + 0.25 * (j - impact)), seed)
            row.append(im)
        wrows.append(row)
    wmeta = {k: wm[k] for k in KEEP_WEAPON if k in wm}
    wmeta.update(remap(wm, PER_FRAME_WEAPON, picks))
    wmeta.update(common)
    wmeta.update({"action": "execute_" + weapon, "weapon": weapon, "bodySheet": name,
                  "overlay": "%s(player/v3) 와 같은 프레임 번호(row*columns+column)를 같은 시각에 겹친다. 피벗 = 주인공 피벗 + playerFrameOffset" % name,
                  "bloodFrom": impact, "bloodNote": "타격 프레임부터 날에 검붉은 피(BL1·BL2) + 날끝 방울 1",
                  "note": desc + (" · 무기 그림 = 손에 역수로 쥔 화살(촉 30 · 깃 12 도트, 활은 등에 멘 채 — 그리지 않음)" if weapon == "bow" else "")})
    if weapon == "bow":
        wmeta["design"] = "쥔 화살(새 그림) — 원 단검 오버레이의 gripAnchors·bladeTipAnchors 방향을 따름"
    if assets:
        gk.write_sheet("player", "v3", name, brows, bmeta)
        gk.write_sheet("weapons", "v3", name, wrows, wmeta)
    # 미리보기: 몸 + 무기 겹침
    off = wm["playerFrameOffset"]
    comp = []
    for r, d in enumerate(bm["directions"][:4]):
        row = []
        for j in range(len(picks)):
            w = wrows[r][j]
            c = Image.new("RGBA", w.size, (0, 0, 0, 0))
            c.alpha_composite(brows[r][j], (off["x"], off["y"]))
            c.alpha_composite(w)
            row.append(c)
        comp.append(row)
    gk.preview(comp, os.path.join(HERE, "out", "preview", name + ".png"), scale=2)
    print("ok", name, len(picks), "frames", flush=True)


if __name__ == "__main__":
    ws = [a for a in sys.argv[1:] if not a.startswith("-")] or list(PLAN)
    for w in ws:
        build(w, "--no-assets" not in sys.argv)
