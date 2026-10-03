#!/usr/bin/env python3
"""주인공 v3 2차 빌드 — 옛 주인공 시트(대검·단검·활·기본 공격·탄생)를 v3 몸으로 교체 (53라운드 4번 피드백).

최종 산출: assets/sprites/player/v3/player_{greatsword_combo1..3,_dashslash,_slam,_draw,_sheathe,_special,
           dagger_combo1..3,_special, bow_aim, bow_reload, attack, birth}.png/.json  (몸 시트만 — 무기 오버레이는 재디자인 때)
미리보기(이 폴더): preview_<동작>_x2.png · preview_<동작>_x3.gif (회색 안내선 = 무기 방향, 시트에는 없음)
                  preview_oldweapon_<무기>.png (구 무기 시트 ×6 를 피벗 맞춤 A / 손 맞춤 B 로 겹친 점검)
                  preview_compare_old_new.png (구 16×24 ×6 ↔ 새 몸)
모듈: gear3.py(동작 정의·보간·자세·안내선) · birth3.py(탄생) · export2.py(시트·JSON·타이밍 assert)
사용: python3 parts/art/work/hero_v3/build2.py [동작 …]   (먼저 build.py 로 1차 시트가 있어야 함 — 탄생 끝 = player_idle 대조)
"""
import json
import os
import sys

from PIL import Image, ImageDraw

import birth3 as B
import export as EX
import export2 as E2
import gear3 as Q
import hero
import preview as PV
import v3kit

HERE = os.path.dirname(os.path.abspath(__file__))
DIRS = hero.DIRS


def rep_frame(data):
    for k in ("impactFrame", "holdFrame", "releaseFrame", "refillFrame"):
        if data.get(k) is not None:
            return data[k]
    return data["frames"] // 2


def oldweapon_preview(weapon, items):
    """items: [(이름, render 결과, data)] → preview_oldweapon_<weapon>.png"""
    CW, CH, PX, PY = 300, 330, 150, 292
    cols = [("right", "A"), ("right", "B"), ("down", "A"), ("down", "B"), ("left", "B"), ("up", "B")]
    out = Image.new("RGBA", (120 + CW * len(cols), 40 + CH * len(items)), PV.BG)
    dr = ImageDraw.Draw(out)
    PV.label(dr, 6, 6, "구 무기 시트 ×6 겹침 점검 — A = 피벗 맞춤, B = 추정 손잡이 → v3 손(handAnchors) 맞춤 · 1배")
    for c, (d, v) in enumerate(cols):
        PV.label(dr, 120 + c * CW + 6, 24, "%s %s" % (d, v))
    for j, (name, r, data) in enumerate(items):
        y0 = 40 + j * CH
        i = rep_frame(data)
        PV.label(dr, 6, y0 + 8, name.replace("greatsword_", "gs_").replace("dagger_", "dg_"))
        PV.label(dr, 6, y0 + 28, "f%d" % i)
        ow = Q.old_weapon_frames(name)
        oi = data["oldWeapon"]["oldFrameForFrame"][i]
        for c, (d, v) in enumerate(cols):
            cell = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
            body = r["frames"][d][i][0]
            bx, by = PX - hero.PIV[0], PY - hero.PIV[1]
            cell.alpha_composite(body, (bx, by))
            wf = ow["frames"][d][oi]
            big = wf.resize((wf.width * 6, wf.height * 6), Image.NEAREST)
            wx, wy = PX - ow["pivot"][0] * 6, PY - ow["pivot"][1] * 6
            if v == "B":
                g = data["oldWeapon"]["oldGripEstimate"][d][oi]
                h = data["handAnchors"][d][i][data["oldWeapon"]["gripHand"]]
                if g:
                    wx, wy = round(bx + h[0] - (g[0] * 6 + 3)), round(by + h[1] - (g[1] * 6 + 3))
            tmp = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
            tmp.alpha_composite(big, (max(0, wx), max(0, wy)), (max(0, -wx), max(0, -wy)))
            cell.alpha_composite(tmp)
            out.alpha_composite(cell, (120 + c * CW, y0))
    out.save(os.path.join(HERE, "preview_oldweapon_%s.png" % weapon))


def compare_preview(items):
    """구 16×24(×6 최근접) ↔ 새 96×144 + 안내선, right 방향 대표 프레임."""
    CW, CH = 2 * 200, 220
    per = 4
    rows = (len(items) + per - 1) // per
    out = Image.new("RGBA", (CW * per, 40 + rows * CH), PV.BG)
    dr = ImageDraw.Draw(out)
    PV.label(dr, 6, 6, "옛 주인공(16×24 ×6) ↔ 새 주인공 v3 (오른쪽 보기 · 대표 프레임 · 1배 · 회색 = 무기 안내선)")
    items = [it for it in items if os.path.exists(it[3])]          # 구 시트가 지워졌으면 그 칸은 건너뜀
    for j, (name, r, data, old_png, old_fw, old_fh, old_i) in enumerate(items):
        x0, y0 = (j % per) * CW, 40 + (j // per) * CH
        PV.label(dr, x0 + 6, y0 + 2, "%s f%d" % (name, old_i[1]))
        im = Image.open(old_png).convert("RGBA")
        row = 3 if name != "birth" else 0
        o = im.crop((old_i[0] * old_fw, row * old_fh, (old_i[0] + 1) * old_fw, (row + 1) * old_fh))
        o = o.resize((old_fw * 6, old_fh * 6), Image.NEAREST)
        if name == "birth":
            o = o.crop((48, 48, 144, 192))
        out.alpha_composite(o.crop((0, 0, min(o.width, 190), min(o.height, 200))), (x0 + 52, y0 + 68))
        n = r if name == "birth" else PV.compose(r["frames"]["right"][old_i[1]][0], r["frames"]["right"][old_i[1]][2])
        out.alpha_composite(n.crop((0, 0, 192, 192)).crop((0, 0, 192, 192)), (x0 + 200, y0 + 20))
    out.save(os.path.join(HERE, "preview_compare_old_new.png"))


def main(only=None):
    EX.ensure_dirs()
    want = lambda a: not only or a in only          # noqa: E731
    cols, report, by_weapon, cmp_items = set(), {}, {}, []
    for name in Q.GEAR:
        if not want(name):
            continue
        r = Q.render(name)
        im, data = E2.export_gear(name, r)
        cols |= v3kit.colors_of(im)
        assert not v3kit.has_alpha_partial(im), name
        comp = {d: [PV.compose(f[0], f[2]) for f in r["frames"][d]] for d in DIRS}
        states = data["frameStates"]
        act = data.get("activeFrames") or ([data["holdFrame"]] if data.get("holdFrame") is not None else [])
        PV.frames_x2(name, comp, r["ms"], impact=data.get("impactFrame"), active=act, states=states)
        PV.gif_x3(name, comp, r["ms"])
        report[name] = dict(frames=len(r["ms"]), ms=r["ms"], old=r["old"]["frameDurationsMs"], timing=data.get("timingMs"),
                            impact=data.get("impactFrame"), cancel=data.get("cancelFromFrame"), hold=data.get("holdFrame"))
        by_weapon.setdefault(r["weapon"], []).append((name, r, data))
        rf = rep_frame(data)
        cmp_items.append((name, r, data, os.path.join(Q.OLD_P, "player_%s.png" % name), 16, 24,
                          (data["oldWeapon"]["oldFrameForFrame"][rf] if data["oldWeapon"] else 0, rf)))
        print(name, len(r["ms"]), "frames ok")
    for w, items in by_weapon.items():
        if all(it[2]["oldWeapon"] for it in items):
            oldweapon_preview(w, items)
    if want("birth"):
        frames, ms, first, groups, old = B.render()
        idle0 = Image.open(os.path.join(EX.OUT_P, "player_idle.png")).convert("RGBA").crop((0, 0, hero.FW, hero.FH))
        im, data = E2.export_birth(frames, ms, first, groups, old, idle0)
        cols |= v3kit.colors_of(im)
        fb = {"down": [f[0] for f in frames]}
        PV.frames_x2("birth", fb, ms, impact=data["burstFrame"], active=[data["burstFrame"]],
                     states=[k for i in range(len(ms)) for k, v in data["phases"].items() if i in v])
        PV.gif_x3("birth", fb, ms)
        report["birth"] = dict(frames=len(ms), ms=ms, old=old["frameDurationsMs"], burst=data["burstFrame"], eyeOpen=data["eyeOpenFrame"])
        cmp_items.append(("birth", frames[first[13]][0], data, os.path.join(Q.OLD_P, "player_birth.png"), 32, 32, (13, first[13])))
    if not only:
        compare_preview(cmp_items)
    st = json.load(open(os.path.join(HERE, "stats.json"), encoding="utf-8"))
    p1 = {tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in st["heroPalette"]}
    extra = cols - p1
    print("2차 몸 색", len(cols), "· 1차 팔레트 밖", sorted("#%02x%02x%02x" % c for c in extra), "· 합계", len(p1 | cols), "/ 30")
    with open(os.path.join(HERE, "stats2.json"), "w", encoding="utf-8") as f:
        json.dump({"colorsUnion": len(p1 | cols), "outsidePhase1": sorted("#%02x%02x%02x" % c for c in extra), "moves": report},
                  f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
