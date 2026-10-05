# -*- coding: utf-8 -*-
"""
60라운드 Q7 — 패시브별 소리 (패시브 29종 중 발동이 눈에 띄는 9종, 10파일).

build.py 가 sfx_branch2 다음(마지막)에 import 한다(시드 = 1000 + 등록 순서). 새 효과음은 이 파일 맨 끝에 추가한다.

근거: design-2026-10-04-build-axis.md 1.5·1.6(패시브 1~25), design-2026-10-04-build-axis-chwigi.md 3장(26~29),
      57라운드 Q22~Q37('패시브 풀 25종 전부 + 취기 패시브') · Q38(취기 신규 4종).
고른 기준: 발동 순간이 화면에 보이는 '사건'이 있고(불씨·분신·파편·웅덩이·뿜기·돌진), 기존 소리로 대신되지 않는 것.
          수치만 바꾸는 패시브(공격·이동·치명·사거리·방어·소지량)와 기존 소리가 이미 그 순간을 맡는 것
          (마지막 잔 = endure_trigger, 사냥 표지 = pickup_gold, 붉은 분필 = mark_stack, 장교의 견장 = hit_enemy_crit,
          흩어진 촉 = bow_arrow_split 재사용)은 만들지 않았다.
트리거: 제안 이벤트 PASSIVE_PROC{passive:<id>} 하나로 모음(패시브 id 는 음향 제안 — 시스템 id 로 바꿔 적는다).
작게 깔리게: 처치·타격마다 날 수 있는 소리라 gainDb 를 낮게(-5~-8) 두고 20 ms 중복 규칙을 그대로 쓴다.
"""
from build import *  # noqa: F401,F403
from build import GLASS, BLADE, blade_ring, tear, sizzle, ash_pop, crackle, droplets, slosh, heartbeat, \
    gravel, tone_f  # noqa: F401


def _flame(sr, rng, dur, f0, f1, a=0.03):
    n = sec(sr, dur)
    s = svf(noise(sr, dur, rng), sr, sweep(sr, n, f0, f1), 0.7, 'low')
    return mul(s, env_adsr(sr, dur, a, dur * 0.2, 0.5, dur * 0.6))


def _shard(sr, rng, f, tau=0.03):
    return metal(sr, 0.14, f, rng, partials=GLASS, tau=tau, jitter=0.02)


@sfx('passive_glass_shard', 'PASSIVE_PROC{passive:brokenShard}', "패시브 #10 '깨진 잔 조각'(타격 12% 출혈) 발동. 작은 유리 조각 둘이 '찰캉' + 젖은 틱. 그 타격의 hit_enemy 위에 작게", -8)
def _passive_glass_shard(sr, rng):
    s = zeros(sec(sr, 0.3))
    mix_into(s, _shard(sr, rng, 3100), 0, 0.5)
    mix_into(s, _shard(sr, rng, 4300, 0.025), sec(sr, 0.025), 0.35)
    mix_into(s, droplets(sr, rng, 0.2, 2, 0.02, 0.12, 450, 800, 0.3), 0)
    return tail(s, sr, 0.02)


@sfx('passive_ember_sleeve', 'PASSIVE_PROC{passive:burningSleeve}', "패시브 #11 '불붙은 소매'(대쉬 경로에 불씨 1 s+) 발동. 소매에서 번지는 짧은 불 '화륵' + 뒤로 남는 타닥. dash 위에 겹침", -8)
def _passive_ember_sleeve(sr, rng):
    dur = 0.55
    s = zeros(sec(sr, dur))
    mix_into(s, _flame(sr, rng, 0.3, 350, 1900), 0, 0.8)
    mix_into(s, crackle(sr, rng, 0.45, 7, 0.4), sec(sr, 0.06))
    return tail(s, sr, 0.02)


@sfx('passive_blood_scent', 'PASSIVE_PROC{passive:bloodScent}', "패시브 #18 '피 냄새'(지속 피해 중인 적 처치 → 지속 피해가 다른 적에게 옮겨붙음) 발동. 갈라져 날아가는 젖은 바람 둘 → 0.24 s 도착하는 지짐·핏방울", -6)
def _passive_blood_scent(sr, rng):
    dur = 0.45
    s = zeros(sec(sr, dur))
    for k in range(2):
        w = lowpass(whoosh(sr, 0.22, rng, 1400, 3000 + 500 * k, q=1.4, a=0.2, r=0.5), sr, 3500)
        mix_into(s, w, sec(sr, 0.015 * k), 0.5)
    mix_into(s, sizzle(sr, rng, 0.15, fc=4500, tau=0.04), sec(sr, 0.24), 0.4)
    mix_into(s, droplets(sr, rng, 0.18, 3, 0.0, 0.1, 400, 750, 0.3), sec(sr, 0.24))
    return tail(s, sr, 0.02)


@sfx('passive_domino', 'PASSIVE_PROC{passive:domino}', "패시브 #20 '도미노'(처치 시 가장 가까운 적에게 재 파편 1발) 발동. 쓰러진 자리의 작은 재 '푹' + 날아가는 짧은 바람 + 0.2 s 박히는 틱", -7)
def _passive_domino(sr, rng):
    s = zeros(sec(sr, 0.32))
    mix_into(s, ash_pop(sr, rng, 0.15, 220, 90, 0.4), 0, 0.5)
    mix_into(s, whoosh(sr, 0.15, rng, 3000, 6200, q=1.6, a=0.1, r=0.6), sec(sr, 0.03), 0.5)
    mix_into(s, click(sr, rng, 0.003, 3600), sec(sr, 0.2), 0.6)
    mix_into(s, thud(sr, 0.04, 260, 150, 0.01), sec(sr, 0.2), 0.3)
    return tail(s, sr, 0.02)


@sfx('passive_mirror_clone', 'PASSIVE_PROC{passive:brokenMirror}', "패시브 #24 '깨진 거울'(대쉬 후 0.5 s 안 첫 공격을 그림자 분신이 한 번 더) 발동. 깨진 거울 '팅'(유리) + 짧게 빨려드는 어두운 역바람 → 0.14 s 분신 베기(어둡게) + 쇠 틱. 칼 shadow_clone(칼날 울림)과 유리 결로 구분", -5)
def _passive_mirror_clone(sr, rng):
    dur = 0.45
    s = zeros(sec(sr, dur))
    mix_into(s, _shard(sr, rng, 2640, 0.05), 0, 0.4)
    mix_into(s, _shard(sr, rng, 3950, 0.04), sec(sr, 0.01), 0.25)
    m = sec(sr, 0.12)
    nz = svf(noise(sr, 0.12, rng), sr, sweep(sr, m, 400, 2400), 1.4, 'band')
    mix_into(s, mul(nz, [(i / m) ** 1.6 for i in range(m)]), sec(sr, 0.02), 0.4)
    cut = lowpass(whoosh(sr, 0.13, rng, 6000, 1800, q=1.8, a=0.1, r=0.6), sr, 4500)
    mix_into(s, cut, sec(sr, 0.14), 0.7)
    mix_into(s, metal(sr, 0.1, 2000, rng, tau=0.03, jitter=0.03), sec(sr, 0.15), 0.12)
    return reverb(tail(s, sr, 0.02), sr, size=0.5, decay=0.45, wet=0.18)


@sfx('passive_ember_heart', 'PASSIVE_PROC{passive:emberHeart}', "패시브 #25 '잔불 심장'(전설, 강공 적중 지점에 불 웅덩이 2~4 s) 발동. 심장 한 번 '쿵' + 피어오르는 불 '훅' + 타닥. 웅덩이가 타는 동안 boss1_fire_loop 1개 재사용(가까운 것 기준)", -4)
def _passive_ember_heart(sr, rng):
    dur = 0.8
    s = zeros(sec(sr, dur))
    mix_into(s, heartbeat(sr, rng, 1.0), 0, 0.8)
    mix_into(s, thud(sr, 0.2, 95, 45, 0.05), sec(sr, 0.02), 0.5)
    mix_into(s, _flame(sr, rng, 0.55, 220, 2200), sec(sr, 0.04), 0.8)
    mix_into(s, crackle(sr, rng, 0.6, 10, 0.35), sec(sr, 0.1))
    s = softclip(s, 1.2)
    return tail(s, sr, 0.02)


@sfx('passive_spilled_drink', 'PASSIVE_PROC{passive:spilledDrink}', "패시브 #26 '엎지른 술'(처치 시 15~30% 술 웅덩이) 발동. 쏟아지는 술 '철퍽' + 물방울 + 작은 잔 '팅'. 보스 boss1_liquor_splash 보다 짧고 작다", -7)
def _passive_spilled_drink(sr, rng):
    dur = 0.4
    n = sec(sr, 0.22)
    s = zeros(sec(sr, dur))
    sp = svf(noise(sr, 0.22, rng), sr, sweep(sr, n, 3200, 700), 1.0, 'band')
    mix_into(s, mul(sp, env_exp(sr, 0.22, 0.06)), 0, 0.7)
    mix_into(s, thud(sr, 0.06, 200, 110, 0.015), 0, 0.4)
    mix_into(s, droplets(sr, rng, 0.3, 5, 0.03, 0.25, 500, 1400, 0.3), 0)
    mix_into(s, _shard(sr, rng, 2300, 0.04), sec(sr, 0.02), 0.12)
    return tail(s, sr, 0.02)


@sfx('passive_liquor_spray', 'PASSIVE_PROC{passive:harshBreath}', "패시브 #28 '독한 숨'(마시기 직후 3 s 안 첫 공격 = 앞 원뿔 2칸 술 뿜기, 맞은 자리 웅덩이) 발동. 입술 '프'(노이즈, 목소리 아님) → 넓게 퍼지는 술 안개 '푸쉬' + 흩어지는 물방울. 그 공격의 휘두름 위에 겹침", -3)
def _passive_liquor_spray(sr, rng):
    dur = 0.55
    s = zeros(sec(sr, dur))
    mix_into(s, burst(sr, 0.03, rng, fc=500, q=0.7, tau=0.008, mode='low'), 0, 0.6)
    ns = sec(sr, 0.36)
    sp = svf(noise(sr, 0.36, rng), sr, sweep(sr, ns, 1500, 4200), 0.8, 'band')
    sp = mul(sp, [0.6 + 0.4 * math.sin(TAU * 23 * i / sr) for i in range(ns)])
    mix_into(s, mul(sp, env_adsr(sr, 0.36, 0.02, 0.05, 0.7, 0.25)), sec(sr, 0.015), 0.8)
    mix_into(s, droplets(sr, rng, 0.45, 9, 0.05, 0.4, 600, 1800, 0.22), 0)
    return tail(s, sr, 0.02)


@sfx('passive_fire_breath', 'PASSIVE_PROC{passive:harshBreath,fire:true}', "패시브 #28 '독한 숨' 술불 위에서 뿜음 = 화염 뿜기(×1.5). 술 안개 '푸쉬'에 불이 붙어 0.05 s 부터 낮게 으르렁대는 불길 + 타닥. passive_liquor_spray 대신", -2)
def _passive_fire_breath(sr, rng):
    dur = 0.85
    s = zeros(sec(sr, dur))
    mix_into(s, burst(sr, 0.03, rng, fc=500, q=0.7, tau=0.008, mode='low'), 0, 0.5)
    ns = sec(sr, 0.3)
    sp = svf(noise(sr, 0.3, rng), sr, sweep(sr, ns, 1500, 3800), 0.8, 'band')
    mix_into(s, mul(sp, env_adsr(sr, 0.3, 0.02, 0.0, 1.0, 0.2)), sec(sr, 0.01), 0.45)
    mix_into(s, thud(sr, 0.2, 100, 45, 0.05), sec(sr, 0.05), 0.6)
    roar = _flame(sr, rng, 0.7, 250, 2600, 0.04)
    roar = mul(roar, [0.7 + 0.3 * math.sin(TAU * 11 * i / sr) for i in range(len(roar))])
    mix_into(s, roar, sec(sr, 0.05), 0.9)
    mix_into(s, crackle(sr, rng, 0.65, 12, 0.35), sec(sr, 0.1))
    s = softclip(s, 1.3)
    return tail(s, sr, 0.02)


@sfx('passive_drunk_fist', 'PASSIVE_PROC{passive:drunkFist}', "패시브 #29 '취권'(영웅, 취기 중 대쉬 직후 공격 = 휘는 궤적 2칸 비틀 돌진 베기, 연속 3회) 한 번. 7 Hz 로 휘는 무거운 바람 + 술 출렁 → 0.22 s 베기 + 둔탁한 디딤. 1·2·3회 rate 1.0/1.06/1.12, 3회째 뒤 0.5 s 비틀 경직에 drunk_sway 재사용 권장(보스 '3연 취권' 오마주)", -3)
def _passive_drunk_fist(sr, rng):
    dur = 0.5
    n = sec(sr, 0.24)
    s = zeros(sec(sr, dur))
    fc = [500 * math.exp(math.log(2600 / 500) * i / n) * (1 + 0.35 * math.sin(TAU * 7 * i / sr)) for i in range(n)]
    w = svf(noise(sr, 0.24, rng), sr, fc, 1.2, 'band')
    mix_into(s, mul(w, env_adsr(sr, 0.24, 0.06, 0.0, 1.0, 0.08)), 0, 0.7)
    mix_into(s, slosh(sr, rng, 0.22, 380, 700), sec(sr, 0.02), 0.35)
    t = sec(sr, 0.22)
    mix_into(s, whoosh(sr, 0.12, rng, 6000, 1900, q=1.8, a=0.1, r=0.6), t, 0.75)
    mix_into(s, metal(sr, 0.1, 2100, rng, tau=0.03, jitter=0.03), t + sec(sr, 0.01), 0.15)
    mix_into(s, heavy_step(sr, rng, 0.8), t, 0.5)
    return tail(s, sr, 0.02)
