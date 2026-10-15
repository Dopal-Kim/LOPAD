"""P20 — 탄생(player_birth, 192×192 down 34프레임): birth3 연출(혼불 모임·재 무덤·흙으로 굳음·터짐·무릎 → 일어섬) 그대로, 몸만 새 리그.

새 다리가 길어 같은 웅크림 값이면 덜 앉으므로 무릎 꿇기 웅크림을 1.45배. 마지막 프레임 = 새 player_idle down 0(픽셀 동일, 탄생 끝 튐 없음).
일어서는 칸(14~16)은 손을 새 대기 0 의 손 자리로 보간.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(WORK, "hero_v3"))
import body20 as B  # noqa: E402
import rig20  # noqa: E402
import sync19 as S  # noqa: E402
import hero  # noqa: E402


def idle0():
    import gridsheet
    jp = os.path.join(S.GRID, "player", "v3", "player_idle.json")
    m = gridsheet.load_meta(jp)
    im = Image.open(os.path.join(S.GRID, "player", "v3", "player_idle.png")).convert("RGBA")
    r = m["directions"].index("down")
    return im.crop((0, r * 144, 96, r * 144 + 144)), m["handAnchors"]["down"][0]


def build(log):
    import birth3
    import gear3
    body0, hands0 = idle0()
    target = {"R": B.px_to_design(hands0["handR"]), "L": B.px_to_design(hands0["handL"])}

    def pose20(**kw):
        p = hero.pose(**kw)
        if p["crouch"] > 3:
            p["crouch"] *= 1.45
        return p

    class FakeR:
        def __init__(self, img):
            self.image = img
            self.anchors = {}

    def draw_rig(d, p):
        if p.get("_idle0"):
            return FakeR(body0.copy())
        return rig20.draw_rig(d, B.clean(p))

    def saya_hold(d, p):
        if p.get("crouch", 0) <= 1.0 and p.get("head", 0) == 0 and not p.get("squash"):
            return dict(p, _idle0=True)
        t = max(0.0, min(1.0, 1.0 - (p["crouch"] - 1.45) / (14 * 1.45 - 1.45)))
        q = dict(p)
        if t > 0.35:
            q["handAt"] = {k: v for k, v in target.items()}
            q["reachFrac"] = 1.06
        return q

    birth3.pose = pose20
    birth3.hero = type("H", (), {"draw_rig": staticmethod(draw_rig), "act_idle": staticmethod(hero.act_idle)})
    birth3.K = type("K", (), {"saya_hold": staticmethod(saya_hold)})
    frames, ms, first, groups, old = birth3.render()
    meta = S.src_meta("player/v3/player_birth")
    assert len(frames) == meta["frames"], (len(frames), meta["frames"])
    assert ms == meta["frameDurationsMs"], "탄생 ms 가 바뀜"
    last = frames[-1][0].crop((48, 48, 144, 192))
    assert last.tobytes() == body0.tobytes(), "탄생 마지막 != 새 player_idle down 0"
    m = dict(meta)
    m["p20"] = "P20 새 몸: birth3 연출 그대로, 몸만 새 리그(무릎 꿇기 웅크림 ×1.45). 마지막 프레임 = 새 player_idle down 0"
    m["source"] = "parts/art/work/hero20/birth20.py (P20 새 몸 — birth3 연출)"
    S.write_grid("player/v3/player_birth", {"down": [f[0] for f in frames]}, m)
    log["player_birth"] = dict(frames=len(frames))
    print("player_birth", len(frames))
