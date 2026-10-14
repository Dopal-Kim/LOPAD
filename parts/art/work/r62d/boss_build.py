"""62 루프 4 (P18 §2) 보스 '만취' 완전 새 도트 — 15 동작 시트 + 림·가벼운 림 + 불타는 오버레이 2종. 결정적.

순서(같은 프로세스):
 1. body   : boss_body.install() → eanim.render_all(b1acts, 15 동작) → 격자 시트(boss1_v3 build.export 그대로) →
             JSON 은 git HEAD 의 기존 메타를 바탕으로 '새로 잰 앵커'만 바꿈(키 집합·ms·phaseFrames·피벗·틀 그대로) → 아틀라스
 2. rim    : boss61/hires_build.build_rim (새 실루엣으로 _rim 5시트)
 3. lite   : boss61/native.build_rim_lite (_rim_lite 5시트)
 4. onfire : boss61/native.build_onfire · build_onfire_down (몸 윤곽을 새 시트에서 다시 잼)
 5. portrait: ui_portraits/boss1.png (r62b cards.portrait) · preview: r62d/preview_boss_{before_after,actions,dark_rim}.png (동작별 x2·gif 는 R62D_ACT_PREVIEW=1)
환경변수 BOSS_STEPS="body rim lite onfire preview" 로 일부만, BOSS_ACTS="idle walk" 로 동작 일부만(body).
cup_shatter·소품·fx 는 그대로(술통 잔 그림·크기 불변).
"""
import importlib.util
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
sys.path.insert(0, HERE)
import boss_body  # noqa: E402  (hires → b1body 1.5배 판)
sys.path.insert(0, os.path.join(WORK, "boss61"))
import intro  # noqa: E402
import k61  # noqa: E402
from k61 import b2  # noqa: E402
import gridsheet  # noqa: E402
import b1acts  # noqa: E402
import eanim  # noqa: E402
import eprev  # noqa: E402
from PIL import Image  # noqa: E402

intro.install()
boss_body.install()
b1acts.META["walk"]["stride"] = {"px": 86, "cycleMs": 1040}
_spec = importlib.util.spec_from_file_location("b1build", os.path.join(WORK, "boss1_v3", "build.py"))
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)
assert B.FW == 288 and B.PIV == (144, 330)

REL = "assets/sprites/bosses/v3"
OUT = os.path.join(ROOT, REL)
ACTS = B.ORDER + ["intro"]
SRC = "parts/art/work/r62d/build.py --only boss (62 루프 4 · P18 §2) · boss_body.py / boss_build.py"
FRESH = {"cupAnchors", "handAnchors", "handR", "handL", "footAnchors", "impactAnchors", "bellyAnchors"}
ATLAS_KEYS = {"atlas", "frames", "textures", "meta", "framesPerDirection"}
NOTE = {
    "note": "62 루프 4(P18 §2) 완전 새 도트 — 실루엣·옷·얼굴을 새로(골격·자세·프레임·ms·피벗·틀·앵커 정의 그대로, 앵커 값은 새 그림에서 다시 잼).",
    "design": ("종 모양으로 벌어지는 녹슨 적갈 긴 외투(앞 터짐·숄 깃·접은 소매·등 허리띠) · 바랜 리넨 셔츠(벌어진 단추 틈·술 얼룩) · "
               "청회색 띠(왼쪽 매듭·늘어진 끝) · 띠에 쇠사슬로 매단 외상 장부 · 짝짝이 신(왼 검은 군화 / 오른 줄무늬 양말 + 헌 슬리퍼) · "
               "부스스하게 뻗친 머리 · 바다코끼리 콧수염 + 놋 고리 두 갈래 수염 · 술통 테 왕관(쇠 테 + 코르크 뿔 + 호박 유리)"),
    "finish": "월드 64 결 마무리 = r62c boss_redot 식(재질 램프 덩어리 명암·칸 경계 바이어 디더·먹 테)을 새 램프(외투 A16~A20 — 발광색 없음)로",
    "story": "parts/story world-bible(술독 제국 '잔'의 지배자, 무지한 죄인) · text-pack-61 C(장부를 못 읽음) · text-pack-63 유품 '만취의 짝짝이 신'",
}


def git_json(rel):
    r = subprocess.run(["git", "-C", ROOT, "show", "HEAD:" + rel], capture_output=True)
    return json.loads(r.stdout.decode("utf-8")) if r.returncode == 0 else None


def merge_meta(name, fresh):
    """fresh(격자 JSON) 에 HEAD 메타를 덮는다 — 새로 잰 키(FRESH)와 격자 형식 키만 fresh 값."""
    head = git_json(f"{REL}/{name}.json")
    if head is None:
        return fresh
    out = dict(fresh)
    for k, v in head.items():
        if k in ATLAS_KEYS or k in FRESH or k in ("redot62c",):
            continue
        out[k] = v
    out["source"] = SRC
    out["version"] = "v3-r62d"
    out["redraw62d"] = dict(NOTE)
    return out


def edge_count(frames):
    n = 0
    for lst in frames.values():
        for f in lst:
            bb = f.getchannel("A").getbbox()
            if bb and (bb[0] == 0 or bb[1] == 0 or bb[2] == f.width or bb[3] == f.height):
                n += 1
    return n


CACHE = os.environ.get("R62D_CACHE", "")          # 지정하면 렌더 결과를 이 폴더에 저장·재사용(마무리 단계만 다시 돌릴 때)


def render_cached(acts):
    import pickle
    res, todo = {}, []
    for act in acts:
        p = os.path.join(CACHE, act + ".pkl") if CACHE else None
        if p and os.path.exists(p):
            raw = pickle.load(open(p, "rb"))
            res[act] = {d: [(Image.frombytes("RGBA", sz, b), inf) for b, sz, inf in lst] for d, lst in raw.items()}
        else:
            todo.append(act)
    if todo:
        new = eanim.render_all("b1acts", todo)
        for act in todo:
            res[act] = new[act]
            if CACHE:
                os.makedirs(CACHE, exist_ok=True)
                raw = {d: [(im.tobytes(), im.size, inf) for im, inf in lst] for d, lst in new[act].items()}
                pickle.dump(raw, open(os.path.join(CACHE, act + ".pkl"), "wb"))
    return res


def limit_colors(res, act, cap=40):
    """시트(4방향) 색 수를 cap 이하로: 가장 적게 쓴 비발광 색을 남은 색 중 가장 가까운 색으로 합친다(피격 섬광 칸이 색을 늘림)."""
    em = {tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in boss_body.BB.EMIT}
    cnt = {}
    for lst in res[act].values():
        for im, _ in lst:
            for n, c in im.getcolors(1 << 20) or []:
                if c[3]:
                    cnt[c[:3]] = cnt.get(c[:3], 0) + n
    remap = {}
    while len(cnt) > cap:
        victim = min((c for c in cnt if c not in em), key=lambda c: cnt[c])
        n = cnt.pop(victim)
        tgt = min((c for c in cnt if c not in em), key=lambda c: sum((a - b) ** 2 for a, b in zip(c, victim)))
        cnt[tgt] += n
        for k, v in list(remap.items()):
            if v == victim:
                remap[k] = tgt
        remap[victim] = tgt
    if remap:
        for lst in res[act].values():
            for im, _ in lst:
                px = im.load()
                for y in range(im.height):
                    for x in range(im.width):
                        c = px[x, y]
                        if c[3] and c[:3] in remap:
                            px[x, y] = remap[c[:3]] + (255,)
    return len(remap)


def build_body(acts):
    res = render_cached(acts)
    stats = {}
    for act in acts:
        merged = limit_colors(res, act)
        if merged:
            print(act, "색 합침", merged, flush=True)
        ms, frames, j = B.export(act, res[act])
        name = "stage1_%s" % act
        jp = os.path.join(OUT, name + ".json")
        j = json.load(open(jp, encoding="utf-8"))
        j = merge_meta(name, j)
        with open(jp, "w", encoding="utf-8") as f:
            json.dump(j, f, ensure_ascii=False, indent=1)
        cs = B.colors(frames)
        edge = edge_count(frames)
        assert len(cs) <= 40 and edge == 0, (act, len(cs), edge)
        stats[act] = {"frames": len(ms), "colors": len(cs)}
        b2.WRITTEN.append(("bosses", name))
        print(act, stats[act], flush=True)
        if os.environ.get("R62D_ACT_PREVIEW"):              # 동작별 x2·gif(약 22MB) — 필요할 때만, 저장소에는 넣지 않음
            preview_act(act, frames, ms, j)
    return stats


def preview_act(act, frames, ms, j):
    ph = j.get("phaseFrames") or {}
    strong = {j[k] for k in ("impactFrame", "releaseFrame", "holdFrame", "groundHitFrame", "roarFrame") if k in j and isinstance(j[k], int)}
    marks = {i for k, v in ph.items() for i in v if k not in ("recover", "finish", "rise", "stop")}
    states = [next((k for k, v in ph.items() if i in v), "") for i in range(len(ms))] if ph else None
    d = os.path.join(HERE, "preview_boss")
    os.makedirs(d, exist_ok=True)
    eprev.frames_x2(os.path.join(d, "preview_%s_x2.png" % act), "만취 %s (62 루프 4 새 도트)" % act, frames, ms, B.PIV, marks=marks,
                    strong=strong, states=states)
    eprev.gif_x3(os.path.join(d, "preview_%s.gif" % act), frames, ms, k=1)


def fix_overlay_meta(names):
    """림·불길 시트: 다시 만든 JSON 에 HEAD 의 설명·규칙 키를 되돌림(그림·좌표 키는 새 값)."""
    keep_new = {"frameOffsets", "colors"}
    for cat, name in names:
        rel = f"assets/sprites/{cat}/v3/{name}.json"
        p = os.path.join(ROOT, rel)
        cur = json.load(open(p, encoding="utf-8"))
        head = git_json(rel)
        if head is None:
            continue
        for k, v in head.items():
            if k in ATLAS_KEYS or k in keep_new:
                continue
            cur[k] = v
        cur["source"] = SRC
        cur["version"] = "v3-r62d"
        cur["redraw62d"] = "62 루프 4 보스 새 도트의 실루엣으로 다시 만듦(틀·피벗·열·ms·규칙 그대로)"
        with open(p, "w", encoding="utf-8") as f:
            json.dump(cur, f, ensure_ascii=False, indent=1)
            f.write("\n")


def build():
    steps = os.environ.get("BOSS_STEPS", "body rim lite onfire portrait preview").split()
    acts = os.environ.get("BOSS_ACTS", "").split() or ACTS
    out = {}
    if "body" in steps:
        b2.WRITTEN.clear()
        out["body"] = build_body(acts)
        out["atlas_body"] = len(k61.to_atlas())
    if "rim" in steps:
        b2.WRITTEN.clear()
        import hires_build as HB
        HB.build_rim()
        names = list(b2.WRITTEN)
        fix_overlay_meta(names)
        out["rim"] = k61.to_atlas()
    if "lite" in steps or "onfire" in steps:
        import native as NV
        b2.WRITTEN.clear()
        if "lite" in steps:
            for cat, name, rows, meta, ms, loop, size in NV.build_rim_lite():
                NV.write(cat, name, rows, meta, ms, loop, size=size)
        if "onfire" in steps:
            cat, name, rows, meta, ms, loop = NV.build_onfire()
            NV.write(cat, name, rows, meta, ms, loop)
            cat, name, rows, meta, ms, loop = NV.build_onfire_down()
            NV.write(cat, name, rows, meta, ms, loop)
        names = list(b2.WRITTEN)
        fix_overlay_meta(names)
        out["lite_onfire"] = k61.to_atlas()
    if "portrait" in steps:
        # 결산 처치자 초상 — r62b cards.portrait(같은 함수·같은 시드 순번, portraits.json 그대로). 모듈 이름(common) 충돌을 피해 새 프로세스로
        code = ("import sys; sys.path.insert(0, %r); import cards as RC, common as C, os; "
                "im = RC.portrait('bosses/v3/stage1_idle', 0, 0, 5); C.save_png(im, os.path.join(C.SPR, 'ui_portraits', 'boss1.png'))"
                % os.path.join(WORK, "r62b"))
        subprocess.run([sys.executable, "-c", code], check=True, cwd=os.path.join(WORK, "r62b"))
        out["portrait"] = "ui_portraits/boss1.png"
    if "preview" in steps:
        import boss_preview
        out["preview"] = boss_preview.build()
    return out
