#!/usr/bin/env python3
"""61라운드 시스템 D 요청 — 보스 '만취' v3 전 동작 1.5배 네이티브 + 등장(intro) 시트 + 어둠용 림라이트 오버레이 + 불타는 오버레이 1.5배.

사용: python3 parts/art/work/boss61/hires_build.py [body] [onfire] [rim] [preview]   (인자 없으면 전부, 순서대로)
  body    : assets/sprites/bosses/v3/stage1_<동작>(15종 = 54라운드 14 + intro) 를 288×360 · 피벗 (144,330) 으로 다시 그림
  onfire  : fx/v3/boss1_onfire·boss1_onfire_down 을 같은 틀로(불길은 최근접 1.5배 — 임시. 61 단계 4 에서 native.py 가 네이티브로 대체 — 틀이 이미 1.5배면 건너뜀)
  rim     : bosses/v3/stage1_<동작>_rim(어둠 3국면용 실루엣 림라이트 — idle·walk·stagger_dash·hurt·attack)
몸·무기 판정에 쓰는 앵커(cupAnchors·handAnchors·footAnchors·impactAnchors·bellyAnchors)는 새 판에서 다시 잰 값(1.5배 좌표).
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hires  # noqa: E402,F401  (판 크기 1.5배로 바꿈 — 반드시 b1acts 보다 먼저)
import intro  # noqa: E402
import k61  # noqa: E402
from k61 import b2, ROOT  # noqa: E402
import gridsheet  # noqa: E402
import b1acts  # noqa: E402
import eanim  # noqa: E402
from PIL import Image  # noqa: E402

intro.install()
b1acts.META["walk"]["stride"] = {"px": 86, "cycleMs": 1040}
spec = importlib.util.spec_from_file_location("b1build", os.path.join(hires.B1, "build.py"))
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)
assert B.FW == 288 and B.PIV == (144, 330)

OUT = os.path.join(ROOT, "assets", "sprites", "bosses", "v3")
FX = os.path.join(ROOT, "assets", "sprites", "fx", "v3")
ACTS = os.environ.get("BOSS_ACTS", "").split() or (B.ORDER + ["intro"])
SRC = "parts/art/work/boss61/hires_build.py (61라운드 1.5배 네이티브 — 54라운드 boss1_v3 골격·셰이딩 코드 그대로, 판 크기만)"
NAT = {"nativeScale": 1.5, "renderScaleHint": 1.0,
       "nativeNote": ("61라운드: 54라운드 시트(192×240 · 피벗 (96,220))를 1.5배 해상도로 다시 그림(최근접 확대 아님). pixelScale 0.5 그대로 → "
                      "화면 크기가 이미 1.5배(논리 144×180). 시스템이 보스에 따로 곱하던 렌더 배율(약 1.5)은 1.0 으로 — renderScaleHint. "
                      "모든 앵커·피벗·stride 는 이 판 좌표(옛 값 × 1.5 근사, 새 판에서 다시 잼)"),
       "previousSize": {"frameWidth": 192, "frameHeight": 240, "pivot": {"x": 96, "y": 220}}}


def build_body():
    res = eanim.render_all("b1acts", ACTS)
    stats = {}
    for act in ACTS:
        ms, frames, j = B.export(act, res[act])
        name = "stage1_%s" % act
        jp = os.path.join(OUT, name + ".json")
        j = json.load(open(jp, encoding="utf-8"))
        j.update(NAT)
        j["source"] = SRC
        j["version"] = "v3-r61"
        if act == "intro":
            for k in ("walkLoop", "toastLoop"):
                j[k] = intro.META[k]
            j["actionNote"] = intro.META["note"]
        if act in ("drink", "phase_drink", "drink_break"):
            j["cupAnchorsNote"] = j["cupAnchorsNote"].replace("20도트", "%d도트" % hires.b1body.VIS_MIN)
        json.dump(j, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        cs = B.colors(frames)
        edge = 0
        for lst in frames.values():
            for f in lst:
                a = f.getchannel("A")
                w, h = f.size
                bb = a.getbbox()
                if bb and (bb[0] == 0 or bb[1] == 0 or bb[2] == w or bb[3] == h):
                    edge += 1
        assert len(cs) <= 40 and edge == 0, (act, len(cs), edge)
        stats[act] = {"frames": len(ms), "colors": len(cs)}
        b2.WRITTEN.append(("bosses", name))
        print(act, stats[act])
    return stats


# ------------------------------------------------------------------ 불타는 오버레이(같은 틀로)
def build_onfire():
    """boss1_onfire(4행×16)·boss1_onfire_down(1행×16) — 불길 그림은 54라운드 것을 최근접 1.5배(불꽃·불티는 덩어리 그림이라 계단이 거의 안 보임).
    좌표 필드(pivot·light offset·radius·frameOffsets)는 1.5배. 다음 패스에서 onfire.py 를 새 판 실루엣으로 다시 돌려 네이티브로 바꿀 수 있음."""
    for name in ("boss1_onfire", "boss1_onfire_down"):
        jp = os.path.join(FX, name + ".json")
        m = gridsheet.load_meta(jp)
        if m.get("frameWidth") == 288:
            print(name, "이미 1.5배 — 건너뜀")
            continue
        g = gridsheet.open_grid(jp)
        g = g.resize((g.width * 3 // 2, g.height * 3 // 2), Image.NEAREST)
        fw, fh = m["frameWidth"] * 3 // 2, m["frameHeight"] * 3 // 2
        rows = len(m["directions"])
        n = m["frames"]
        frames = [g.crop((i * fw, r * fh, (i + 1) * fw, (r + 1) * fh)) for r in range(rows) for i in range(n)]
        meta = {k: v for k, v in m.items() if k not in ("image", "frameWidth", "frameHeight", "frames", "frameDurationsMs", "loop")}
        meta["pivot"] = {"x": 144, "y": 330}

        def sc(L):
            if not L:
                return L
            L = dict(L)
            if "radius" in L:
                L["radius"] = round(L["radius"] * 1.5)
            if "offset" in L:
                o = L["offset"]
                L["offset"] = [round(v * 1.5) for v in o] if isinstance(o, list) else {k: round(v * 1.5) for k, v in o.items()}
            return L
        if "light" in meta:
            meta["light"] = sc(meta["light"])
        if "lightByPhase" in meta:
            lb = meta["lightByPhase"]
            meta["lightByPhase"] = {k: (round(v * 1.5) if isinstance(v, (int, float)) else sc(v)) for k, v in lb.items()}
        if "frameOffsets" in meta:
            fo = meta["frameOffsets"]
            meta["frameOffsets"] = {a: {k: ([round(c * 1.5) for c in v] if isinstance(v, list) else v) for k, v in d.items()}
                                    if isinstance(d, dict) else [([round(c * 1.5) for c in v] if isinstance(v, list) else v) for v in d]
                                    for a, d in fo.items()} if isinstance(fo, dict) else fo
        meta.update(NAT)
        meta["nativeNote"] = ("61라운드: 보스 시트 1.5배 네이티브에 맞춘 틀(288×360 · 피벗 (144,330)). 불길 그림은 54라운드 그림을 최근접 1.5배(임시) — "
                              "좌표 필드(light·lightByPhase·frameOffsets)는 1.5배")
        meta["version"] = "v3-r61"
        b2.write_sheet("fx", name, frames, fw, fh, meta, rows=rows, durations=m["frameDurationsMs"], loop=m.get("loop", False))
        print(name, fw, fh)


def build_cup_shatter():
    """약점 잔 부서짐 fx — 잔이 1.5배(약 44×55)가 되어 54라운드 그림(128×128)을 최근접 1.5배(192×192 · 피벗 (96,90))로 맞춤(임시)."""
    name = "boss1_cup_shatter"
    jp = os.path.join(FX, name + ".json")
    m = gridsheet.load_meta(jp)
    if m.get("frameWidth") == 192:
        print(name, "이미 1.5배 — 건너뜀")
        return
    g = gridsheet.open_grid(jp)
    g = g.resize((g.width * 3 // 2, g.height * 3 // 2), Image.NEAREST)
    fw, fh, n = 192, 192, m["frames"]
    frames = [g.crop((i * fw, 0, (i + 1) * fw, fh)) for i in range(n)]
    meta = {k: v for k, v in m.items() if k not in ("image", "frameWidth", "frameHeight", "frames", "frameDurationsMs", "loop")}
    meta["pivot"] = {"x": 96, "y": 90}
    meta.update(NAT)
    meta["nativeNote"] = "61라운드: 보스 1.5배 네이티브 잔(약 44×55)에 맞춰 54라운드 그림을 최근접 1.5배(임시) — 피벗 1.5배"
    meta["version"] = "v3-r61"
    b2.write_sheet("fx", name, frames, fw, fh, meta, rows=1, durations=m["frameDurationsMs"], loop=m.get("loop", False))
    print(name, fw, fh)


# ------------------------------------------------------------------ 어둠용 림라이트
RIM_ACTS = ["idle", "walk", "attack", "stagger_dash", "hurt"]
RIM_OUT = (0xe2, 0xa3, 0x3c, 255)      # A23
RIM_IN = (0xd6, 0x7a, 0x11, 255)       # A21
RIM_HI = (0xee, 0xcc, 0x78, 255)       # A25


def rim_frame(im):
    """실루엣 안쪽 가장자리 2도트 — 위·오른쪽(뒤쪽 촛불 역광) 쪽은 굵고 밝게, 아래·왼쪽은 1도트 점선. 조명 위에 그림(어둠에서도 보임)."""
    w, h = im.size
    a = im.getchannel("A").load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    o = out.load()
    on = lambda x, y: 0 <= x < w and 0 <= y < h and a[x, y] == 255  # noqa: E731
    for y in range(h):
        for x in range(w):
            if not on(x, y):
                continue
            up = not on(x, y - 1)
            rt = not on(x + 1, y)
            lf = not on(x - 1, y)
            dn = not on(x, y + 1)
            up2 = not on(x, y - 2)
            rt2 = not on(x + 2, y)
            if up or rt:
                o[x, y] = RIM_HI if (up and rt) else RIM_OUT
            elif up2 or rt2:
                o[x, y] = RIM_IN
            elif (lf or dn) and (x + y) % 2 == 0:
                o[x, y] = RIM_IN
    return out


def build_rim():
    for act in RIM_ACTS:
        name = "stage1_%s" % act
        jp = os.path.join(OUT, name + ".json")
        m = gridsheet.load_meta(jp)
        g = gridsheet.open_grid(jp)
        fw, fh, n = m["frameWidth"], m["frameHeight"], m["frames"]
        frames = [rim_frame(g.crop((i * fw, r * fh, (i + 1) * fw, (r + 1) * fh))) for r in range(len(m["directions"])) for i in range(n)]
        meta = {"directions": m["directions"], "pivot": m["pivot"], "version": "v3-r61", "overlayOf": "bosses/v3/" + name,
                "drawRule": ("보스 시트와 같은 프레임 번호·같은 시각·같은 피벗·같은 flip 으로 보스 바로 위에 겹친다(depth above_target). "
                             "3국면 '인사불성' 등불 끄기(lightsOut) 동안만 켬 — 조명 위에 그려(drawOver lightmap) 어둠 속에서도 보스 윤곽이 보이게. "
                             "목록에 없는 동작(slam·throw·kick·drink·fall·death 등)은 오버레이 없이 그리거나, 시스템이 보스 그림을 호박색 tintFill 로 한 번 더 "
                             "뒤에 그려 대신해도 됨(VRAM 절약)"),
                "drawOver": "lightmap", "paletteSwap": "none", "depth": "above_target",
                "emissiveColors": ["#e2a33c", "#d67a11", "#eecc78"],
                "design": "실루엣 안쪽 가장자리 역광: 위·오른쪽 2도트(A23 바깥·A21 안, 모서리 A25) + 아래·왼쪽 1도트 점선(A21)",
                "source": SRC + " · rim", "nativeScale": 1.5, "renderScaleHint": 1.0}
        b2.write_sheet("bosses", name + "_rim", frames, fw, fh, meta, rows=len(m["directions"]), durations=m["frameDurationsMs"],
                       loop=m.get("loop", False))
        print(name + "_rim", len(frames))


def preview():
    rows = []
    for act, fi in (("intro", (0, 4, 8, 10, 12, 13, 15)), ("idle", (0, 4)), ("attack", (3, 6)), ("hurt", (1,))):
        jp = os.path.join(OUT, "stage1_%s.json" % act)
        m = gridsheet.load_meta(jp)
        g = gridsheet.open_grid(jp)
        for i in fi:
            rows.append(g.crop((i * 288, 0, (i + 1) * 288, 360)))
    W = 288 * 6
    im = Image.new("RGBA", (W, 360 * 2 + 400), (30, 28, 34, 255))
    for k, f in enumerate(rows[:12]):
        im.alpha_composite(f, ((k % 6) * 288, (k // 6) * 360))
    # 어둠 목업: 림라이트 켬/끔 비교
    dark = Image.new("RGBA", (W, 400), (8, 7, 10, 255))
    jp = os.path.join(OUT, "stage1_idle.json")
    g = gridsheet.open_grid(jp)
    rim = gridsheet.open_grid(os.path.join(OUT, "stage1_idle_rim.json"))
    for k in range(4):
        f = g.crop((0, k * 360, 288, (k + 1) * 360))
        dim = Image.eval(f, lambda v: v)  # 원본
        px = dim.load()
        for y in range(360):
            for x in range(288):
                c = px[x, y]
                if c[3]:
                    px[x, y] = (c[0] // 7, c[1] // 7, c[2] // 7, 255)
        dark.alpha_composite(dim, (k * 288 * 3 // 2 // 1 if False else k * 420, 20))
        if k % 2:
            dark.alpha_composite(rim.crop((0, k * 360, 288, (k + 1) * 360)), (k * 420, 20))
    im.alpha_composite(dark, (0, 720))
    p = os.path.join(HERE, "preview_boss_hires.png")
    im.convert("RGB").save(p)
    print(p, im.size)


if __name__ == "__main__":
    steps = sys.argv[1:] or ["body", "onfire", "rim", "preview"]
    if "body" in steps:
        build_body()
        for r in k61.to_atlas():
            print("atlas", r)
    if "onfire" in steps:
        build_onfire()
        for r in k61.to_atlas():
            print("atlas", r)
    if "onfire" in steps:
        build_cup_shatter()
        for r in k61.to_atlas():
            print("atlas", r)
    if "rim" in steps:
        build_rim()
        for r in k61.to_atlas():
            print("atlas", r)
    if "preview" in steps:
        preview()
