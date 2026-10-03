"""적 v3 동작 공용: 구 시트 타이밍 → 새 프레임 분할, 자세 보간, 병렬 렌더.

타이밍 원칙(주인공 v3 2차와 같음): 구 프레임 하나를 n 개로 나누고(ms 균등 분할) 구 프레임 '시작 ms' 를 그대로 둔다.
→ 공격 단계(예고·돌진·내리찍기·발사)·피격 플래시·사망 시점이 구 시트와 같은 시각. check_timing 이 assert.
구 JSON 사본: old_sheets/ (dummy·archer = 16×24 구 시트, charger = v2 32×48 시트 'charger_v2_*' — 구 24×24 와 ms 동일).
"""
import importlib
import json
import os
from multiprocessing import Pool

import erig

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
OLD_DIR = os.path.join(HERE, "old_sheets")
ACTS = ["idle", "walk", "attack", "hurt", "death"]
DIRS = erig.DIRS

# 구 프레임 → 새 프레임 수 (공격은 적 모듈의 ATTACK_SPLIT)
SPLIT = {"idle": None, "walk": None, "hurt": [1, 2], "death": [1, 2, 2, 2, 2, 1]}


def old_json(eid, act):
    name = "charger_v2_%s.json" % act if eid == "charger" else "%s_%s.json" % (eid, act)
    with open(os.path.join(OLD_DIR, name)) as f:
        return json.load(f)


def split_of(mod, act):
    old = old_json(mod.ID, act)
    sp = mod.ATTACK_SPLIT if act == "attack" else SPLIT[act]
    return old, (sp or [1] * old["frames"])


def split_ms(old_ms, split):
    new, fmap = [], []
    for ms, n in zip(old_ms, split):
        base = ms // n
        rem = ms - base * n
        parts = [base + (1 if j < rem else 0) for j in range(n)]
        fmap.append(list(range(len(new), len(new) + n)))
        new += parts
    return new, fmap


def starts(ms):
    out, t = [], 0
    for m in ms:
        out.append(t)
        t += m
    return out


def check_timing(eid, act, old_ms, new_ms, fmap):
    assert sum(old_ms) == sum(new_ms), (eid, act, "total", sum(old_ms), sum(new_ms))
    so, sn = starts(old_ms), starts(new_ms)
    for k, nf in enumerate(fmap):
        assert sn[nf[0]] == so[k], (eid, act, "start of old frame", k, sn[nf[0]], so[k])
        end_new = sn[nf[-1]] + new_ms[nf[-1]]
        assert end_new == so[k] + old_ms[k], (eid, act, "end of old frame", k)
    assert sorted(i for nf in fmap for i in nf) == list(range(len(new_ms)))


# ---- 자세 보간 ------------------------------------------------------------------
def _lerp(a, b, t):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return a + (b - a) * t
    if isinstance(a, tuple) and isinstance(b, tuple) and len(a) == len(b):
        return tuple(_lerp(x, y, t) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        out = {}
        for k in set(a) | set(b):
            if k in a and k in b:
                out[k] = _lerp(a[k], b[k], t)
            else:
                out[k] = (a if t < 0.5 else b).get(k, (b if t < 0.5 else a).get(k))
        return out
    return a if t < 0.5 else b


def lerp_pose(a, b, t):
    out = {}
    for k in set(a) | set(b):
        if k in ("flash", "eye", "fall_ok"):
            out[k] = a.get(k) if t < 0.5 else b.get(k)
        elif k in a and k in b and a[k] is not None and b[k] is not None:
            out[k] = _lerp(a[k], b[k], t)
        else:
            out[k] = a.get(k) if t < 0.5 else b.get(k)
    return out


def ease(t):
    return t * t * (3 - 2 * t)


# ---- 렌더 ----------------------------------------------------------------------
def _task(args):
    modname, act, d, i = args
    mod = importlib.import_module(modname)
    p = mod.ACTIONS[act](d)[i]
    im, info = mod.render_full(d, p)
    return (act, d, i, im.tobytes(), im.size, info)


def render_all(modname, acts=ACTS, procs=None):
    """→ {act: {dir: [(RGBA, info)]}}"""
    from PIL import Image
    mod = importlib.import_module(modname)
    tasks = []
    for act in acts:
        for d in DIRS:
            n = len(mod.ACTIONS[act](d))
            tasks += [(modname, act, d, i) for i in range(n)]
    with Pool(procs or os.cpu_count()) as pool:
        res = pool.map(_task, tasks, chunksize=2)
    out = {}
    for act, d, i, raw, size, info in res:
        out.setdefault(act, {}).setdefault(d, {})[i] = (Image.frombytes("RGBA", size, raw), info)
    return {a: {d: [v[i] for i in sorted(v)] for d, v in dd.items()} for a, dd in out.items()}
