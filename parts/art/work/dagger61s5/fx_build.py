"""단검 fx 시트 쓰기 — 기존 격자 메타(고치기 전) 그대로 + 그림만 교체 + 설계 메모 갱신."""
import d5
import fx_thrust as T

DESIGN_THRUST = ("61 단계 5 '재 발톱' 찌르기 — 무기 날과 같은 발톱 곡선을 가늘게 늘인 바늘 획(백열 심은 끝에 맺힘, 끝이 휨) + "
                 "옆으로 비켜 선 짧고 많은 잔상 획 + 끝의 X 섬광(판정) → 다 그은 칸: 식는 획·작은 X 흉터·잔상이 앞으로 밀림 → 마디로 끊기며 먹·재 부스러기. "
                 "뭉툭한 원뿔·공기 고리 없음")
DESIGN_ACCEL = "가속 단계 = 같은 획이 길어지고(×1.1/×1.2) 조금 굵어지며 잔상 획 3/6/9 · 속도 틱 6/10/14 — 판정은 그대로"
GLOW_RULE = "백열 X0/X1·A26 은 glowFrames(판정 칸)만(획 심·X 섬광 가운데). 그 밖은 A25 이하"


def _meta(m, design, colors, extra=None):
    meta = dict(m)
    prev = m.get("design")
    for k in ("previous", "designRef", "effectRule", "brushStroke", "branchDesignV3", "note", "tierDesign"):
        meta.pop(k, None)
    meta.update(design=design, designPrevious=prev, source=d5.SRC, version=d5.VERSION, r61s5=d5.R61S5, colors=colors,
                glowRule=GLOW_RULE, semiTransparent=False)
    if extra:
        meta.update(extra)
    return meta


def write(name, rows, m, design, look, cap=14, extra=None, edge_ok=False):
    glow = set(m.get("glowFrames") or [])
    d5.reduce_colors(rows, cap if look is T.EMBER else 24, keep=(d5.X0, d5.X1))
    allowed = d5.FX_ALLOWED if look is T.EMBER else d5.aw_allowed()
    n = d5.check(name, rows, glow, allowed, cap if look is T.EMBER else 24, edge_ok=edge_ok)
    d5.write_grid("fx", "v3", name, rows, _meta(m, design, n, extra))
    return n


def thrust_family(only=None):
    jobs = []
    for n in (1, 2, 3):
        base = "dagger_combo%d" % n
        for stage in (1, 2, 3):
            jobs.append((base if stage == 1 else "%s_accel%d" % (base, stage), lambda m, n=n, s=stage: T.combo_rows(m, n, s, T.EMBER),
                         DESIGN_THRUST + (" · " + DESIGN_ACCEL if stage > 1 else ""), T.EMBER))
        jobs.append((base + "_awaken", lambda m, n=n: T.combo_rows(m, n, 1, T.ONIBI),
                     "각성(귀화) 궤적 — 기본과 같은 '재 발톱' 바늘 획·잔상·X 섬광을 보라 몸 + 청록 불혀 색으로(60 Q19 각성 색). 틀·ms·피벗·행은 기본 시트와 1:1", T.ONIBI))
        for v in ("twin", "twin_dance", "twin_bleed", "gale", "gale_afterimage", "gale_assassin"):
            dsg = {"twin": "쌍격 1단 — 두 발톱 바늘이 앞 60% 에서 X 로 교차, 교차점 X 섬광 → X 흉터",
                   "twin_dance": "쌍격 2단 난무 — 교차 X + 엇갈린 작은 둘째 X + 짧은 잔상 다발",
                   "twin_bleed": "쌍격 2단 출혈 — 교차 X + 교차점에서 떨어지는 짙은 방울",
                   "gale": "질풍 1단 — 가는 본 발톱 + 부채꼴로 펼친 바람 발톱(짧은 초승달 획 3)",
                   "gale_afterimage": "질풍 2단 잔상 — 바람 발톱 5 + 촘촘한 잔상 획",
                   "gale_assassin": "질풍 2단 암살 — 바람 발톱 + 뒤로 말리는 먹 덩굴 + 큰 X 섬광"}[v]
            jobs.append(("%s_%s" % (base, v), lambda m, n=n, v=v: T.combo_rows(m, n, 1, T.EMBER, v), "61 단계 5 '재 발톱' " + dsg, T.EMBER))
    jobs.append(("dagger_combo3_double", lambda m: T.double_rows(m, T.EMBER),
                 "61 단계 5 '재 발톱' 쌍격 연격 변화 — −7°·+7° 로 엇갈린 두 발톱 바늘이 70ms 간격(둘째가 더 길고 X 섬광이 큼), 잔상 획·먹 부스러기", T.EMBER))
    jobs.append(("dagger_combo3_double_awaken", lambda m: T.double_rows(m, T.ONIBI),
                 "각성(귀화) 쌍격 연격 변화 — 위 그림을 보라·청록 색으로(틀·ms·피벗 동일)", T.ONIBI))
    for heat in (1, 2, 3):
        nm = "dagger_flurry" if heat == 1 else "dagger_flurry_heat%d" % heat
        jobs.append((nm, lambda m, h=heat: T.flurry_rows(m, T.EMBER, h),
                     "61 단계 5 '재 발톱' 고속 난타 — 짧은 발톱 바늘 3갈래(−10°·+12°·0°)마다 X 섬광, 앞 찌르기는 나이대로 식어 X 흉터·먹 부스러기로 남음(루프 이음 그대로). "
                     "열 %d단: 잔상 획 %d · 획 굵기 +%.1f%s" % (heat, {1: 2, 2: 4, 3: 6}[heat], 0.6 * (heat - 1), " · 손 둘레 재 아지랑이" if heat > 1 else ""), T.EMBER))
    jobs.append(("dagger_flurry_awaken", lambda m: T.flurry_rows(m, T.ONIBI, 1), "각성(귀화) 고속 난타 — 기본 난타 그림을 보라·청록 색으로", T.ONIBI))
    jobs.append(("dagger_backstab", lambda m: T.backstab_rows(m, T.EMBER),
                 "61 단계 5 '재 발톱' 등 뒤 치명 — 박히는 발톱 획 + 박힌 자리 큰 X 섬광 + 바깥으로 튀는 먹 바늘 → 먹 방울 고리 → 재", T.EMBER))
    jobs.append(("hit_dagger", lambda m: T.hit_rows(m, T.EMBER, False),
                 "61 단계 5 '재 발톱' 적중 — X 섬광 + 앞으로 긴 바늘 → 베인 발톱 자국 1 + 앞쪽 부채꼴 바늘 불티", T.EMBER))
    jobs.append(("hit_dagger_heavy", lambda m: T.hit_rows(m, T.EMBER, True),
                 "61 단계 5 '재 발톱' 강한 적중 — 겹 X 섬광 + 엇갈린 발톱 자국 2 + 불티 + 먹 방울", T.EMBER))
    out = []
    for name, fn, design, look in jobs:
        if only and not any(o == name or (o.endswith("*") and name.startswith(o[:-1])) for o in only):
            continue
        m, _ = d5.grid("fx/v3/" + name)
        rows = fn(m)
        extra = {}
        if name.startswith("dagger_combo") and m.get("accelLevel"):
            extra["accelRule"] = (m.get("accelRule") or "").replace("뒤로 밀린 잔상 창끝 0/1/2·속도선·공기 고리 1/2/3", "잔상 획 3/6/9·속도 틱 6/10/14")
        c = write(name, rows, m, design, look, extra=extra)
        out.append(name)
        print("fx", name, c)
    return out


MISC = [
    ("shadowstep_ghost", "shadowstep", "61 단계 5 그림자 걸음 출발 — 먹빛 실루엣(밝은 재 테·호박 금 자리)이 아래부터 녹아 발밑 먹 웅덩이로 번지고(가닥이 바닥을 타고 퍼짐), 위는 구멍이 나며 떠오름 → 웅덩이가 마르며 갈라짐", T.EMBER),
    ("dagger_thrown", "thrown", "61 단계 5 투척 발톱 — 작은 발톱 날(손가락 고리 포함)이 끝부터 날아가며 짧은 잔상 획 3을 끈다(루프마다 휨 방향이 번갈아 = 회전감)", T.EMBER),
    ("dagger_fan_throw", "fan_throw", "61 단계 5 부채 투척 — 왼팔이 뒤에서 앞으로 쓸어내는 발톱 호 + 놓는 자리에서 −15°·0°·+15° 발톱 바늘 셋(머리 X 섬광) → 식으며 끊김", T.EMBER),
    ("dagger_brand_mark", "brand_mark", "61 단계 5 낙인 — 적 몸에 새긴 발톱 자국(먹 테두리 + 불씨 심). 스택 1~3 = 나란한 자국 1~3, 4 = 가로지르는 넷째 자국(X), 5 = 감싸 닫는 발톱 고리(표식 완성). 새 자국은 지져지는 순간 백열·작은 X 불꽃, 남은 자국은 잔불로 깜빡이고 불씨가 오름", T.EMBER),
    ("dagger_brand_burst", "brand_burst", "61 단계 5 낙인 기폭 — 새긴 자국이 부풀며 갈라짐 → 큰 X + 바깥으로 뻗는 발톱 바늘 8(판정) → 발톱 고리 6이 돌며 퍼지고 먹 튐이 고리로 → 마르는 먹·재 부스러기(솜 연기 없음)", T.EMBER),
    ("dagger_brand_bleed", "brand_bleed", "61 단계 5 낙인 출혈 — 새긴 발톱 자국 셋에서 호박빛 피 방울이 뚝뚝(루프)", T.EMBER),
    ("dagger_brand_hop", "brand_hop", "61 단계 5 낙인 옮김 — X 로 새긴 발톱 자국 하나가 짧은 잔상 획을 끌며 날아감", T.EMBER),
    ("dagger_stuck_blade", "stuck_blade", "61 단계 5 꽂힌 날 — 땅에 비스듬히 박힌 발톱 날(고리 위) + 패인 자리, 날선을 타고 오르는 반짝임 → 재로", T.EMBER),
    ("dagger_cross_clone", "cross_clone", "61 단계 5 쌍격 분신 — 분신 몸은 먹빛(밝은 재 테·호박 금 그대로), 교차 베기는 발톱 바늘 두 개의 X + 교차점 X 섬광 → X 흉터가 마디로 끊기며 재", T.EMBER),
    ("dagger_hundred_ghosts", "hundred_ghosts", "61 단계 5 백귀 — 세 방향에서 다가오는 혼불(옛 0~2 칸 그대로) → 한가운데서 세 갈래 발톱 베기(보라 몸·청록 심) + X 섬광 → 꿰뚫고 나가 청록·보라 부스러기", T.ONIBI),
    ("dagger_awaken_in", "awaken_in", "61 단계 5 각성 순간 — 머리 위 '재 발톱' 날이 끝부터 귀화(보라·청록)로 타들어 감(6칸) → 번쩍·X·고리 → 혼불과 머묾 → 픽셀 단위로 사라짐", T.ONIBI),
]


def misc(only=None):
    import fx_misc as M
    for name, fn, design, look in MISC:
        if only and name not in only:
            continue
        m, fr = d5.grid("fx/v3/" + name)
        f = getattr(M, fn)
        rows = f(m, fr) if fn in ("cross_clone", "hundred_ghosts", "awaken_in") else f(m)
        edge_ok = name in ("dagger_awaken_in",)
        c = write(name, rows, m, design, look, cap=14, edge_ok=edge_ok)
        print("fx", name, c)


if __name__ == "__main__":
    import sys
    a = sys.argv[1:]
    if a and a[0] == "misc":
        misc(a[1:] or None)
    else:
        thrust_family(a or None)
