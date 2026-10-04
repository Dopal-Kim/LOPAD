"""58라운드 검기·울분 오버레이 — combo56_res/overlay.py(56 Q14·Q15 방식) 를 새 시트·다시 낸 시트에 다시 돌린다.
assets 는 아틀라스이므로 rk.load_sheet 를 격자 되살리기(gridcompat)로 바꿔 읽는다(아직 격자인 새 시트도 그대로 읽힘)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gridcompat  # noqa: E402

gridcompat.patch_rk()
import overlay  # noqa: E402  (combo56_res)

KATANA58 = ["katana_thrust", "katana_issen_dash"]
GS58 = ["greatsword_sweep_cw", "greatsword_sweep_ccw", "greatsword_cleave", "greatsword_charge", "greatsword_charge_slam",
        "greatsword_charge_plunge", "greatsword_tackle", "greatsword_brace_upswing", "greatsword_leap_slam", "greatsword_guard_rush",
        "greatsword_charge_swing"]


def build(only=None):
    overlay.KATANA_SHEETS = list(dict.fromkeys(overlay.KATANA_SHEETS + KATANA58))
    overlay.GS_SHEETS = list(dict.fromkeys(overlay.GS_SHEETS + ["greatsword_charge_swing"]))
    names = set(only or (KATANA58 + GS58))
    return overlay.build(names)


if __name__ == "__main__":
    print("\n".join(build(set(sys.argv[1:]) or None)))
