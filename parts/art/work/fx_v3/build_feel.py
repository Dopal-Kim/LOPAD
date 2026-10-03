"""55라운드 작업 B — 타격감·움직임 이펙트 (적중 스파크·재 입자·잔상 리본·움직임 fx 개선).

python3 parts/art/work/fx_v3/build_feel.py              # 전부 + 미리보기
python3 parts/art/work/fx_v3/build_feel.py hit_katana   # 그 시트만(+ 미리보기 갱신)

산출: assets/sprites/fx/v3/<이름>.png/.json (pixelScale 0.5). 기록: NOTES.md 9절.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import feel_kit as K  # noqa: E402
import feel_hits as H  # noqa: E402
import feel_particles as PT  # noqa: E402
import feel_motion as MO  # noqa: E402

WEAPON_KO = {"katana": "칼", "greatsword": "대검", "dagger": "단검", "bow": "활"}
HITSTOP = {"katana": 45, "greatsword": 80, "dagger": 30, "bow": 25}          # 55라운드 Q6
DESIGN = {
    "katana": "가는 사선 섬광 — 적중점을 가르는 긴 바늘 선(뒤아래→앞위 62°) + 공격 방향 바늘 → 선이 가운데서 갈라져 미끄러짐 + 좁은 원뿔 불티 → 점선 토막·재 조각",
    "greatsword": "무거운 충격 고리 + 먼지 — 큰 백열 원반·굵은 쐐기 광선 → 앞이 굵은 충격 고리(뒤는 가늘게) + 앞·옆 재 먼지 덩이 + 큰 재 조각 → 고리 점선·먼지 테두리",
    "dagger": "작은 연속 별빛 — 4점 별이 공격 방향으로 하나씩 이어 터짐(앞 별은 식고 새 별이 밝게) + 작은 불씨 점",
    "bow": "꽂히는 화살 파열 — 뒤에서 들어온 화살 줄기가 적중점에서 앞쪽 바늘로 터짐 → 앞이 볼록한 파열 호 + 재 화살대 파편이 앞으로 튐",
}
DESIGN_HEAVY = {
    "katana": "X 베기 — 두 사선 + 긴 앞 바늘·큰 코어 → 두 선이 갈라지며 앞쪽 초승달 충격 호 + 불티 12",
    "greatsword": "두 겹 충격 고리 + 큰 먼지 띠 — 쐐기 광선 11 → 굵은 고리 + 안쪽 고리 + 먼지 덩이 7 + 큰 재 조각 12",
    "dagger": "별빛 부채 — 큰 별 + 관통 바늘 → 앞으로 펼쳐지는 별 3 → 바깥 별 4 → 식는 별",
    "bow": "관통 파열 — 긴 화살 줄기 + 앞 바늘 5 → 두 겹 파열 호 + 관통 구멍 고리 + 파편 10",
}


def hit_meta(name, base):
    weapon = name.split("_")[1]
    heavy = name.endswith("_heavy")
    hs = HITSTOP[weapon]
    m = dict(base)
    m.update({
        "action": "hit_heavy" if heavy else "hit",
        "anchor": "hitbox_center",
        "spawn": "hit",
        "depth": "above",
        "rotate": True,
        "drawnFacing": "right",
        "flipY": "allowed",
        "weapon": weapon,
        "variant": "heavy" if heavy else "normal",
        "useFor": ("막타(연격 마지막 타)·치명타 — 같은 무기의 hit_<weapon> 대신" if heavy
                   else "그 무기의 일반 적중(연격 1·2타, 활 일반 화살 등)"),
        "replaces": "hit_burst (무기별로 바꿔 씀, 파일이 없으면 hit_burst)",
        "design": (DESIGN_HEAVY if heavy else DESIGN)[weapon],
        "hitstopMs": round(hs * (1.8 if heavy else 1.0)),
        "hitstopNote": ("55라운드 Q6 무기별 히트스톱(막타·치명타 ×1.8) 참고값. 히트스톱 동안 이 시트는 "
                        "holdFrame 에 멈춰 두기를 권장(판정 순간 백열이 보이도록)."),
        "holdFrame": 0,
        "pivotNote": (f"피벗 ({base['pivot']['x']},{base['pivot']['y']}) = 적중점. 시스템은 공격 방향 각도"
                      "(근접 = 주인공→적 중심, 활 = 화살 진행 각)으로 회전한다. flipY 는 위아래 뒤집기 허용"
                      "(칼은 연격 홀·짝 휘두름 방향에 맞추면 자연스럽다). 중력 표현이 없어 어느 각도로 돌려도 된다."),
        "particles": f"particles_ash recipes.{name} 참고(시스템 입자 발생기).",
    })
    if heavy or weapon == "greatsword":
        m["shakeHint"] = {"px": {"greatsword": 3, "katana": 2, "dagger": 2, "bow": 2}[weapon] + (1 if heavy else 0),
                          "ms": 90 if heavy else 70,
                          "note": "55라운드 Q8 화면 흔들림(막타·대검·치명타만 짧게) — 값은 아트 임시 제안, 시스템 판단."}
    return m


def build_hits(names):
    for name in names:
        frames, base = H.HITS[name]()
        glow = [0, 1]
        K.write(name, frames, hit_meta(name, base), glow_frames=glow)


def build_particles(names):
    if "particles_ash" in names:
        fr, meta = PT.particles_ash()
        meta["note"] = ("55라운드 Q8 재 파편 입자 — 시스템 입자 발생기용 작은 스프라이트 묶음. 재 조각 4종(크기·모양) + "
                        "불씨·불티 3종. kinds = 이름 → 프레임 범위·구동 방식·권장 수명·속도·중력.")
        K.write("particles_ash", fr, meta, glow_frames=[])
    for name, h in (("ribbon_ash", 3), ("ribbon_ash_thin", 2)):
        if name in names:
            fr, meta = PT.ribbon_sheet(h)
            meta["note"] = (f"55라운드 Q7 칼끝 잔상 리본 텍스처({h}도트 폭) — 가는 호박 선이 100ms 안에 재색으로 식으며 "
                            "소멸. 가로 그라데이션(꼬리 재 → 머리 호박 A25), 가장자리 줄은 꼬리 쪽이 짧아 끝이 뾰족, "
                            "꼬리 끝은 체크 디더 구멍. 반투명 0.")
            K.write(name, fr, meta, glow_frames=[])


def build_motion(names):
    for name in names:
        if name not in MO.MOTION:
            continue
        fn, glow = MO.MOTION[name]
        frames, meta = fn()
        dirs = list(frames)
        K.write(name, frames, meta, dirs=dirs, glow_frames=glow)


ALL_HITS = list(H.HITS)
ALL = ALL_HITS + ["particles_ash", "ribbon_ash", "ribbon_ash_thin"] + list(MO.MOTION)

if __name__ == "__main__":
    names = sys.argv[1:] or ALL
    build_hits([n for n in names if n in H.HITS])
    build_particles(names)
    build_motion(names)
