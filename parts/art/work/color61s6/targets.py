"""61 단계 6 (P14 §2) 칼 '서리'·단검 '독' 색 정체성 — 대상 시트 목록(계약 art §28). 다른 무기(대검·활)는 다른 아트 작업."""
import glob
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
SPR = os.path.join(ROOT, "assets", "sprites")


def _names(pat):
    return sorted(os.path.relpath(p, SPR)[:-5] for p in glob.glob(os.path.join(SPR, pat)))


# 안 쓰는·보관 시트(README 61 단계 5: 55 이전 연격·보관 Q35·폐기 §25) — 색을 바꾸지 않음
K_SKIP_FX = {"katana_slash", "katana_crescent", "katana_crescent_echo", "katana_issen_shadow"}
D_SKIP_FX = {"dagger_slash", "dagger_combo1_heat1", "dagger_combo2_heat1", "dagger_combo3_heat1",
             "dagger_combo1_heat2", "dagger_combo2_heat2", "dagger_combo3_heat2",
             "dagger_combo1_heat3", "dagger_combo2_heat3", "dagger_combo3_heat3", "dagger_overheat_cool"}


def katana_fx():
    out = []
    for r in _names("fx/v3/katana_*.json") + _names("fx/v3/hit_katana*.json"):
        b = os.path.basename(r)
        if b in K_SKIP_FX or b.startswith(("katana_combo1", "katana_combo2", "katana_combo3")):
            continue
        out.append(r)
    return out


def dagger_fx():
    out = []
    for r in _names("fx/v3/dagger_*.json") + _names("fx/v3/hit_dagger*.json") + ["fx/v3/shadowstep_ghost"]:
        if os.path.basename(r) in D_SKIP_FX:
            continue
        out.append(r)
    return out


def trait_fx(w):
    return _names("fx/v3/trait_%s_*.json" % w) + _names("fx/v3/trait_res_%s_*.json" % w)


def ki_overlays():
    return _names("weapons/v3/katana_*_ki[123].json")


def awaken_overlays(w):
    return _names("weapons/v3/%s_*_awaken.json" % w)


def v4(w, layer):
    """layer = a1 | a2 | a2_glow"""
    out = []
    for r in _names("weapons/v4/%s_*_%s_*.json" % (w, layer)):
        b = os.path.basename(r)
        if layer == "a2" and "_a2_glow_" in b:
            continue
        out.append(r)
    return out


def katana_base():
    return [r for r in _names("weapons/v3/katana_*.json")
            if not r.endswith(("_awaken",)) and not r[-4:-1] == "_ki" and "icon" not in r]


def looks(w):
    return sorted(os.path.relpath(p, SPR) for p in glob.glob(os.path.join(SPR, "looks", "%s_*.png" % w)))


def cards(w):
    return sorted(os.path.relpath(p, SPR) for p in glob.glob(os.path.join(SPR, "ui_traits", "%s_*.png" % w))
                  + glob.glob(os.path.join(SPR, "ui_traits", "res_%s_*.png" % w)))


if __name__ == "__main__":
    for k, v in [("katana_fx", katana_fx()), ("dagger_fx", dagger_fx()), ("trait_katana", trait_fx("katana")),
                 ("trait_dagger", trait_fx("dagger")), ("ki", ki_overlays()), ("k_awaken", awaken_overlays("katana")),
                 ("d_awaken", awaken_overlays("dagger")), ("k_a2glow", v4("katana", "a2_glow")), ("d_a2glow", v4("dagger", "a2_glow")),
                 ("katana_base", katana_base()), ("k_looks", looks("katana")), ("d_looks", looks("dagger")),
                 ("k_cards", cards("katana")), ("d_cards", cards("dagger"))]:
        print(k, len(v), " ".join(os.path.basename(x) for x in v[:80]))
