# -*- coding: utf-8 -*-
"""
60라운드 Q7 — 2차 묶음 효과음 (엘리트·도전 성소·성과 등급·상점 리롤·층 소모품·이벤트 노드·숨은 노드·
지도 정보·약점 파훼·증류 화로).

build.py 가 SFX 등록이 끝난 자리(endure_trigger 뒤)에서 import 한다. 시드 = 1000 + 등록 순서이므로
이 파일의 @sfx 순서를 바꾸거나 중간에 끼우면 뒤에 오는 소리(sfx_branch2·sfx_passive)가 바뀐다 —
새 소리는 맨 뒤 모듈 끝에만 추가한다.

근거: parts/producer/decisions/2026-10-05-round-60-parallel-production.md Q5~Q7,
      design-2026-10-04-second-bundle.md (b 위험 노드 · c 이벤트 · d 숨은 노드·지도 정보 · e 상점 ·
      f 성소·등급 · g 엘리트 접두어 · h 파훼 · i 소모품) + 57라운드 Q38 확정 문구.
트리거 이름: UI 계약 §9.6(CHALLENGE_*·STRUCTURE_USED)·§14.11(NODE_GRADED·HIDDEN_NODE_FOUND·CONSUMABLE_USED)
            과 음향 계약 §6 목록(SHOP_PURCHASE·ROOM_ENTERED·ENEMY_DIED·BOSS_DIED·UI_MENU_SELECT)은 그대로 쓰고,
            없는 것(ELITE_SPAWNED·ELITE_PREFIX·CONSUMABLE_IMPACT·BOSS_BREAK·STATUS_CHANGED)은 제안.
재료: 엘리트 = 갑옷·전쟁 북·낮은 뿔나팔, 성소 = 깃대·깃발 천·북, 등급 = 일기장 도장·종·동전,
      소모품 = 유리·술·불·물, 이벤트·숨은 노드·지도 = 종이·깃펜·촛불·낮은 종. 목소리 없음(숨·으르렁도 노이즈).
"""
from build import *  # noqa: F401,F403  (DSP 유틸·악기 프리셋·sfx 데코레이터 — build.py 가 먼저 정의)
from build import GLASS, gulp, droplets, slosh, kha, crackle, gravel, slam_impact, blade_ring, tear, \
    sizzle, ash_pop, heavy_step, latch, heartbeat, quill_scratch, jing, tone_f  # noqa: F401


# ---------------------------------------------------------------------------
# 재료 (이 묶음 공용)
# ---------------------------------------------------------------------------

COIN = [(1, 1), (1.9, 0.5), (3.4, 0.25)]


def coin(sr, rng, f=2900, tau=0.045):
    return metal(sr, 0.2, f, rng, partials=COIN, tau=tau, jitter=0.01)


def war_drum(sr, rng, f0=100, f1=38, tau=0.12, g=1.0):
    """전쟁 북: 낮은 몸통 + 가죽 때림."""
    d = lowpass(kick(sr, 0.5, f0, f1, tau, rng=rng), sr, 500)
    mix_into(d, burst(sr, 0.05, rng, fc=900, q=0.7, tau=0.012), 0, 0.35)
    return scale(d, g)


def stamp(sr, rng, g=1.0, heavy=0.0):
    """일기장 도장 '꾹': 둔탁한 몸통 + 종이 때림 + 나무 탁자 울림(heavy 0~1)."""
    s = zeros(sec(sr, 0.3))
    mix_into(s, thud(sr, 0.18, 210 - 50 * heavy, 85, 0.03 + 0.02 * heavy), 0, 1.0)
    mix_into(s, burst(sr, 0.05, rng, fc=1300, q=0.6, tau=0.012), 0, 0.55)
    mix_into(s, click(sr, rng, 0.003, 3000), 0, 0.4)
    if heavy:
        mix_into(s, thud(sr, 0.25, 140, 60, 0.05), sec(sr, 0.004), 0.8 * heavy)
        mix_into(s, burst(sr, 0.12, rng, fc=380, q=0.6, tau=0.03, mode='low'), 0, 0.5 * heavy)
    return scale(s, g)


def cloth_flap(sr, rng, dur, fc=1500, rate=14.0, g=1.0):
    """깃발 천 펄럭임: 밴드 노이즈 + 불규칙하게 떨리는 진폭."""
    n = sec(sr, dur)
    s = svf(noise(sr, dur, rng), sr, fc, 0.9, 'band')
    am = normalize(lowpass([rng.uniform(-1, 1) for _ in range(n)], sr, rate), 1.0)
    s = mul(s, [max(0.0, 0.35 + 0.65 * a) for a in am])
    return scale(mul(s, env_adsr(sr, dur, dur * 0.1, 0.0, 1.0, dur * 0.5)), g)


def paper(sr, rng, dur, g=1.0):
    """종이(지도) 펼침: 바스락 노이즈 + 잔 딸깍."""
    n = sec(sr, dur)
    s = svf(noise(sr, dur, rng), sr, sweep(sr, n, 2200, 3600), 0.8, 'band')
    am = normalize(lowpass([rng.uniform(-1, 1) for _ in range(n)], sr, 30), 1.0)
    s = mul(s, [max(0.0, a) ** 1.5 for a in am])
    s = mul(s, env_adsr(sr, dur, dur * 0.15, 0.0, 1.0, dur * 0.4))
    for _ in range(int(dur * 30)):
        mix_into(s, click(sr, rng, 0.002, rng.uniform(2500, 6000)), sec(sr, rng.uniform(0, dur * 0.9)), rng.uniform(0.1, 0.3))
    return scale(s, g)


def flame(sr, rng, dur, f0=250, f1=2200, a=0.05, g=1.0):
    """불길 '화륵': 컷오프가 열리는 저역 노이즈."""
    n = sec(sr, dur)
    s = svf(noise(sr, dur, rng), sr, sweep(sr, n, f0, f1), 0.7, 'low')
    return scale(mul(s, env_adsr(sr, dur, a, dur * 0.2, 0.5, dur * 0.6)), g)


def glass_shards(sr, rng, dur, count, t0, t1, f_lo=2200, f_hi=5200, g=0.3):
    s = zeros(sec(sr, dur))
    for _ in range(count):
        sh = metal(sr, 0.12, rng.uniform(f_lo, f_hi), rng, partials=GLASS, tau=rng.uniform(0.02, 0.05), jitter=0.02)
        mix_into(s, sh, sec(sr, rng.uniform(t0, t1)), g * rng.uniform(0.4, 1.0))
    return s


# ---------------------------------------------------------------------------
# (g) 엘리트 — 공용 등장 + 접두어 사건 4 + 처치
# ---------------------------------------------------------------------------

@sfx('elite_appear', 'ELITE_SPAWNED', "엘리트 등장(접두어 공용, 2차 묶음 g). 0.12 s 차오르는 바람 → 전쟁 북 두 번 + 갑옷 덜그럭 + 낮은 뿔나팔 A2·E3 + 호박빛 쇠 울림 A4. 호박 외곽선·이름표가 켜지는 프레임에 재생(파일 0.12 s = 북)", -2)
def _elite_appear(sr, rng):
    dur = 1.3
    s = zeros(sec(sr, dur))
    m = sec(sr, 0.12)
    pre = svf(noise(sr, 0.12, rng), sr, sweep(sr, m, 300, 1800), 1.0, 'band')
    mix_into(s, mul(pre, [(i / m) ** 2 for i in range(m)]), 0, 0.45)
    mix_into(s, war_drum(sr, rng, 100, 36, 0.13), m, 1.0)
    mix_into(s, war_drum(sr, rng, 115, 45, 0.08), m + sec(sr, 0.15), 0.6)
    mix_into(s, metal(sr, 0.18, 1100, rng, tau=0.04, jitter=0.05), m + sec(sr, 0.004), 0.25)  # 갑옷
    mix_into(s, burst(sr, 0.06, rng, fc=900, q=0.7, tau=0.014), m, 0.4)
    hn = add(horn(sr, 0.85, 110.0, fc=700), scale(horn(sr, 0.85, 164.81, fc=800), 0.6))
    mix_into(s, mul(hn, env_adsr(sr, 0.85, 0.05, 0.1, 0.7, 0.55)), m, 0.22)  # 낮은 뿔나팔
    mix_into(s, lowpass(metal(sr, 0.9, 440.0, rng, tau=0.3, jitter=0.004), sr, 2500), m + sec(sr, 0.01), 0.15)
    s = softclip(s, 1.2)
    return reverb(s, sr, size=0.8, decay=0.55, wet=0.18)


@sfx('elite_armor_break', 'ELITE_PREFIX{prefix:barrelArmor,phase:break}', "엘리트 접두어 '통 갑옷' 깨짐(첫 강공 적중 → 일반 상태). 술통 판자가 쪼개지는 크랙 여럿 + 속 빈 통 공명(230·520 Hz) + 쇠테 '쨍' + 나무 조각 흩어짐. 깨짐 fx 와 같은 프레임", -1)
def _elite_armor_break(sr, rng):
    dur = 0.8
    s = zeros(sec(sr, dur))
    for k, t0 in enumerate((0.0, 0.018, 0.04, 0.07)):
        mix_into(s, burst(sr, 0.04, rng, fc=rng.uniform(1300, 2600), q=0.9, tau=0.008), sec(sr, t0), 0.9 - 0.15 * k)
    for f, g in ((230.0, 0.5), (520.0, 0.3)):
        mix_into(s, mul(tone(sr, 0.3, f, f * 0.96), env_exp(sr, 0.3, 0.06)), 0, g)
    mix_into(s, thud(sr, 0.15, 160, 70, 0.03), 0, 0.7)
    mix_into(s, metal(sr, 0.5, 610, rng, tau=0.12, jitter=0.03), sec(sr, 0.02), 0.35)  # 쇠테
    mix_into(s, gravel(sr, rng, 0.6, 12, 0.03, 0.45, 0.3), 0)  # 판자 조각
    for t0 in (0.22, 0.34, 0.41):
        mix_into(s, thud(sr, 0.05, rng.uniform(260, 380), 180, 0.01), sec(sr, t0), 0.3)
    return softclip(tail(s, sr, 0.02), 1.3)


@sfx('elite_enrage', 'ELITE_PREFIX{prefix:enraged,phase:trigger}', "엘리트 접두어 '성난' 발동(HP 50% 이하 → 공격·이동 +40%). 낮은 으르렁(거친 저역 노이즈, 목소리 아님) + 빨라지는 심장 둘 + 열기 '훅' + 위로 긁는 쇠. 붉은 눈 빛 켜지는 프레임", -2)
def _elite_enrage(sr, rng):
    dur = 0.9
    n = sec(sr, dur)
    s = zeros(n)
    gr = svf(noise(sr, 0.6, rng), sr, sweep(sr, sec(sr, 0.6), 160, 320), 2.0, 'band')
    gr = mul(gr, [0.5 + 0.5 * math.sin(TAU * 33 * i / sr) for i in range(len(gr))])
    mix_into(s, mul(gr, env_adsr(sr, 0.6, 0.05, 0.1, 0.7, 0.35)), 0, 1.0)  # 으르렁(노이즈)
    mix_into(s, heartbeat(sr, rng, 1.0), 0, 0.6)
    mix_into(s, heartbeat(sr, rng, 1.0), sec(sr, 0.3), 0.7)
    mix_into(s, flame(sr, rng, 0.45, 220, 1800, 0.03), sec(sr, 0.08), 0.5)  # 열기
    sc = svf(noise(sr, 0.25, rng), sr, sweep(sr, sec(sr, 0.25), 1500, 5000), 2.0, 'band')
    mix_into(s, mul(sc, env_adsr(sr, 0.25, 0.08, 0.0, 1.0, 0.12)), sec(sr, 0.05), 0.25)  # 쇠 긁힘
    s = softclip(s, 1.3)
    return tail(s, sr, 0.02)


@sfx('elite_drink', 'ELITE_PREFIX{prefix:guzzler,phase:drink}', "엘리트 접두어 '들이켜는' 마시기(주변 적이 죽을 때 HP +15%·크기 +5%, 최대 3회). 잔 틱 → 빠른 꿀꺽 둘 + 짧은 '크아'(노이즈) + 몸이 커지는 낮은 부풂. 3회째는 rate 0.94 로 더 무겁게(선택)", -4)
def _elite_drink(sr, rng):
    dur = 0.75
    s = zeros(sec(sr, dur))
    mix_into(s, metal(sr, 0.15, 1700, rng, partials=GLASS, tau=0.04, jitter=0.005), 0, 0.3)
    mix_into(s, gulp(sr, rng, 120, 270, 0.13), sec(sr, 0.04), 0.9)
    mix_into(s, gulp(sr, rng, 135, 300, 0.12), sec(sr, 0.17), 0.85)
    mix_into(s, kha(sr, rng, 0.32, 0.35), sec(sr, 0.3), 0.5)
    sw = mul(tone(sr, 0.4, 70, 110), env_adsr(sr, 0.4, 0.15, 0.0, 1.0, 0.2))
    mix_into(s, lowpass(sw, sr, 300), sec(sr, 0.3), 0.6)  # 커지는 몸
    return tail(s, sr, 0.02)


@sfx('elite_leader_down', 'ELITE_PREFIX{prefix:ringleader,phase:death}', "엘리트 접두어 '패거리 두목' 쓰러짐(주변 적 1 s 경직). 깃 장식 깃대가 부러지는 '뚝' + 천이 내려앉음 + 낮게 오래 맥놀이 치는 둔한 종 D3(멍해짐). enemy_death·elite_die 위에 겹침", -2)
def _elite_leader_down(sr, rng):
    dur = 1.15
    s = zeros(sec(sr, dur))
    mix_into(s, burst(sr, 0.03, rng, fc=1900, q=0.9, tau=0.007), 0, 0.9)  # 깃대 부러짐
    mix_into(s, thud(sr, 0.12, 240, 120, 0.02), 0, 0.6)
    mix_into(s, cloth_flap(sr, rng, 0.4, 1100, 10.0), sec(sr, 0.05), 0.4)
    mix_into(s, thud(sr, 0.1, 180, 90, 0.02), sec(sr, 0.33), 0.35)
    b = add(bell(sr, 1.0, 146.83, rng, tau=0.5), scale(bell(sr, 1.0, 148.3, rng, tau=0.5), 0.8))  # 1.5 Hz 맥놀이
    mix_into(s, lowpass(b, sr, 1200), sec(sr, 0.06), 0.5)
    return reverb(tail(s, sr, 0.02), sr, size=0.8, decay=0.55, wet=0.18)


@sfx('elite_die', 'ENEMY_DIED{elite:true}', "엘리트 처치(보상 개성·전표 ×3). 무거운 몸 쓰러짐 + 갑옷 무너짐 셋 + 동전이 쏟아지는 소리 + 꺼지는 호박빛 종 A4. 일반 enemy_death 대신(또는 위에) 재생", -1)
def _elite_die(sr, rng):
    dur = 1.0
    s = zeros(sec(sr, dur))
    mix_into(s, thud(sr, 0.4, 115, 38, 0.08), 0, 1.0)
    mix_into(s, burst(sr, 0.2, rng, fc=400, q=0.6, tau=0.04, mode='low'), 0, 0.6)
    for k, t0 in enumerate((0.02, 0.09, 0.15)):
        mix_into(s, metal(sr, 0.16, 950 + 210 * k, rng, tau=0.035, jitter=0.06), sec(sr, t0), 0.3)
    for k in range(7):
        mix_into(s, coin(sr, rng, rng.uniform(2500, 3900), 0.04), sec(sr, 0.18 + 0.045 * k + rng.uniform(0, 0.02)), 0.3)
    mix_into(s, lowpass(bell(sr, 0.7, 440.0, rng, tau=0.3), sr, 2000), sec(sr, 0.2), 0.2)
    s = softclip(s, 1.2)
    return reverb(tail(s, sr, 0.02), sr, size=0.6, decay=0.5, wet=0.12)


# ---------------------------------------------------------------------------
# (f) 도전 성소(전장 깃발 C4) · 노드 성과 등급
# ---------------------------------------------------------------------------

@sfx('shrine_activate', 'CHALLENGE_STARTED{kind:warFlag}', "도전 성소 발동(전장 깃발을 세움 → 엘리트 1 + 마지막 웨이브 +1). 깃대를 땅에 박는 '쿵' + 깃발 천이 펼쳐지는 펄럭 + 멀리 울리는 뿔나팔 D3 + 짧은 북 연타 → 북 한 번", -1, category='world')
def _shrine_activate(sr, rng):
    dur = 1.7
    s = zeros(sec(sr, dur))
    mix_into(s, thud(sr, 0.25, 150, 55, 0.05), 0, 1.0)  # 깃대 박음
    mix_into(s, burst(sr, 0.08, rng, fc=600, q=0.7, tau=0.02, mode='low'), 0, 0.6)
    mix_into(s, gravel(sr, rng, 0.3, 6, 0.0, 0.15, 0.25), 0)
    mix_into(s, cloth_flap(sr, rng, 0.55, 1500, 16.0), sec(sr, 0.1), 0.6)
    hn = horn(sr, 1.1, 146.83, fc=900)
    mix_into(s, mul(hn, env_adsr(sr, 1.1, 0.25, 0.0, 1.0, 0.6)), sec(sr, 0.2), 0.18)
    for k in range(7):  # 북 연타
        mix_into(s, handdrum(sr, rng, 0.15, 190, 110, 0.4), sec(sr, 0.55 + 0.06 * k), 0.25 + 0.05 * k)
    mix_into(s, war_drum(sr, rng, 95, 34, 0.14), sec(sr, 1.0), 1.0)
    s = softclip(s, 1.2)
    return reverb(s, sr, size=1.0, decay=0.6, wet=0.25)


@sfx('shrine_clear', 'CHALLENGE_CLEARED{kind:warFlag,outcome:clear}', "도전 성소 성공(전표 +25 + 노드 보상 한 번 더). 북 두 번 + 깃발 펄럭 + 종 D5 → A5 + 동전 반짝임", -2, category='event')
def _shrine_clear(sr, rng):
    dur = 1.4
    s = zeros(sec(sr, dur))
    mix_into(s, war_drum(sr, rng, 105, 40, 0.1), 0, 0.9)
    mix_into(s, war_drum(sr, rng, 120, 45, 0.1), sec(sr, 0.17), 1.0)
    mix_into(s, cloth_flap(sr, rng, 0.45, 1600, 15.0), sec(sr, 0.05), 0.35)
    mix_into(s, bell(sr, 1.0, 587.33, rng, tau=0.4), sec(sr, 0.2), 0.4)
    mix_into(s, bell(sr, 0.95, 880.0, rng, tau=0.38), sec(sr, 0.33), 0.35)
    for k in range(3):
        mix_into(s, coin(sr, rng, 3000 + 450 * k), sec(sr, 0.36 + 0.06 * k), 0.25)
    return reverb(s, sr, size=0.9, decay=0.6, wet=0.22)


@sfx('shrine_fail', 'CHALLENGE_CLEARED{kind:warFlag,outcome:fail}', "도전 성소 실패(조건은 시스템 정의 대기). 삐걱이다 부러지는 깃대 + 쓰러지는 '쿵' + 천이 털썩 + 반음 내려앉는 뿔나팔 D3→C#3 + 둔한 북", -3, category='event')
def _shrine_fail(sr, rng):
    dur = 1.25
    s = zeros(sec(sr, dur))
    n = sec(sr, 0.25)
    cr = svf(noise(sr, 0.25, rng), sr, sweep(sr, n, 500, 380), 3.0, 'band')
    cr = mul(cr, [0.5 + 0.5 * math.sin(TAU * 26 * i / sr) for i in range(n)])
    mix_into(s, mul(cr, env_adsr(sr, 0.25, 0.08, 0.0, 1.0, 0.05)), 0, 0.6)  # 삐걱
    mix_into(s, burst(sr, 0.035, rng, fc=1700, q=0.9, tau=0.008), sec(sr, 0.24), 0.9)  # 부러짐
    mix_into(s, thud(sr, 0.3, 140, 50, 0.06), sec(sr, 0.5), 0.9)  # 쓰러짐
    mix_into(s, cloth_flap(sr, rng, 0.3, 900, 8.0), sec(sr, 0.52), 0.35)
    hn = mul(horn(sr, 0.6, 146.83, fc=700), env_adsr(sr, 0.6, 0.05, 0.0, 1.0, 0.3))
    hn2 = mul(horn(sr, 0.6, 138.59, fc=650), env_adsr(sr, 0.6, 0.05, 0.0, 1.0, 0.45))
    mix_into(s, hn, sec(sr, 0.3), 0.12)
    mix_into(s, hn2, sec(sr, 0.62), 0.12)
    mix_into(s, lowpass(war_drum(sr, rng, 80, 35, 0.12), sr, 300), sec(sr, 0.62), 0.6)
    return reverb(tail(s, sr, 0.02), sr, size=0.8, decay=0.55, wet=0.2)


@sfx('grade_perfect', 'NODE_GRADED{grade:perfect}', "노드 성과 등급 완(完) = 무피격 + 제한 시간 안(전표 +20 · 개성 +15). 무거운 일기장 도장 '꾹' + 종 D5·A5·D6 차례로 + 동전 둘. 도장 연출 프레임", -2, category='event')
def _grade_perfect(sr, rng):
    dur = 1.35
    s = zeros(sec(sr, dur))
    mix_into(s, stamp(sr, rng, 1.0, heavy=1.0), 0, 1.0)
    for k, (f, g) in enumerate(((587.33, 0.38), (880.0, 0.33), (1174.66, 0.28))):
        mix_into(s, bell(sr, 1.0 - 0.08 * k, f, rng, tau=0.4), sec(sr, 0.08 + 0.08 * k), g)
    mix_into(s, coin(sr, rng, 2900), sec(sr, 0.3), 0.3)
    mix_into(s, coin(sr, rng, 3700), sec(sr, 0.37), 0.25)
    return reverb(s, sr, size=0.8, decay=0.55, wet=0.2)


@sfx('grade_good', 'NODE_GRADED{grade:good}', "노드 성과 등급 양(良) = 무피격·제한 시간 중 하나(전표 +10). 가벼운 도장 + 종 A4 한 번 + 동전 하나", -4, category='event')
def _grade_good(sr, rng):
    dur = 0.85
    s = zeros(sec(sr, dur))
    mix_into(s, stamp(sr, rng, 0.85, heavy=0.0), 0, 1.0)
    mix_into(s, bell(sr, 0.75, 440.0, rng, tau=0.32), sec(sr, 0.07), 0.35)
    mix_into(s, coin(sr, rng, 3100), sec(sr, 0.2), 0.25)
    return reverb(s, sr, size=0.6, decay=0.5, wet=0.15)


# ---------------------------------------------------------------------------
# (e) 상점 리롤 · (d) 지도 정보 구매
# ---------------------------------------------------------------------------

@sfx('shop_reroll', 'SHOP_PURCHASE{group:reroll}', "상점 진열 리롤(전표 15 → 25 → 35, 진열 3칸 새로). 좌판 천을 걷어 다시 펼치는 휙 + 물건이 뒤섞이는 나무·쇠 딸깍 + 동전 둘. shop_buy 대신", -4, category='pickup')
def _shop_reroll(sr, rng):
    dur = 0.62
    s = zeros(sec(sr, dur))
    mix_into(s, coin(sr, rng, 2700), 0, 0.5)
    mix_into(s, coin(sr, rng, 3300), sec(sr, 0.05), 0.4)
    mix_into(s, cloth_flap(sr, rng, 0.3, 1200, 20.0), sec(sr, 0.08), 0.7)
    for _ in range(7):
        t0 = rng.uniform(0.22, 0.45)
        if rng.random() < 0.5:
            mix_into(s, thud(sr, 0.05, rng.uniform(280, 420), 180, 0.01), sec(sr, t0), 0.45)
        else:
            mix_into(s, metal(sr, 0.07, rng.uniform(1400, 2600), rng, tau=0.015, jitter=0.05), sec(sr, t0), 0.18)
    mix_into(s, thud(sr, 0.1, 300, 140, 0.02), sec(sr, 0.47), 0.6)  # 좌판 두드림
    return tail(s, sr, 0.02)


@sfx('map_info_buy', 'SHOP_PURCHASE{group:mapInfo}', "지도 정보 구매(다음 단 공개 10 / 층 전체 25 / 숨은 노드 위치 20 — 국경 초소 지도 장수·상점 노드). 동전 둘 + 지도 펼치는 바스락 + 깃펜이 길을 긋는 두 획", -4, category='pickup')
def _map_info_buy(sr, rng):
    dur = 0.9
    s = zeros(sec(sr, dur))
    mix_into(s, coin(sr, rng, 2800), 0, 0.5)
    mix_into(s, coin(sr, rng, 3500), sec(sr, 0.05), 0.4)
    mix_into(s, paper(sr, rng, 0.32), sec(sr, 0.12), 0.8)
    mix_into(s, quill_scratch(sr, rng, 0.14, 2600, 4800), sec(sr, 0.5), 0.5)
    mix_into(s, quill_scratch(sr, rng, 0.12, 3200, 5600), sec(sr, 0.68), 0.45)
    return tail(s, sr, 0.02)


# ---------------------------------------------------------------------------
# (i) 층 테마 소모품 3종
# ---------------------------------------------------------------------------

@sfx('bottle_throw', 'CONSUMABLE_USED{id:fireBottle}', "소모품 '화염 술병' 투척(누르면 커서 방향 즉시). 심지에 불붙는 '칙' + 팔 휘두름 + 빙글 도는 병 속 술 출렁(9 Hz). 착탄은 bottle_burst", -3)
def _bottle_throw(sr, rng):
    dur = 0.45
    n = sec(sr, dur)
    s = zeros(n)
    mix_into(s, sizzle(sr, rng, 0.12, fc=4500, tau=0.04), 0, 0.5)  # 심지
    mix_into(s, whoosh(sr, 0.18, rng, 1400, 450, q=1.0, a=0.3, r=0.5), sec(sr, 0.05), 0.7)
    sp = svf(noise(sr, 0.3, rng), sr, 900, 1.2, 'band')
    sp = mul(sp, [0.4 + 0.6 * abs(math.sin(math.pi * 9 * i / sr)) for i in range(len(sp))])
    mix_into(s, mul(sp, env_adsr(sr, 0.3, 0.05, 0.0, 1.0, 0.2)), sec(sr, 0.12), 0.45)  # 도는 병
    mix_into(s, slosh(sr, rng, 0.28, 400, 800), sec(sr, 0.1), 0.3)
    return tail(s, sr, 0.02)


@sfx('bottle_burst', 'CONSUMABLE_IMPACT{id:fireBottle}', "화염 술병 착탄(반경 1.5칸 불 웅덩이 4 s). 유리 깨짐 + 술 첨벙 + 0.04 s 불 '화륵' + 타닥. 웅덩이가 타는 동안은 boss1_fire_loop 1개 재사용(가장 가까운 불 기준)", -1)
def _bottle_burst(sr, rng):
    dur = 0.9
    n = sec(sr, dur)
    s = zeros(n)
    mix_into(s, burst(sr, 0.03, rng, fc=3500, q=0.9, tau=0.006), 0, 0.9)
    mix_into(s, glass_shards(sr, rng, 0.4, 9, 0.0, 0.25), 0)
    ns = sec(sr, 0.3)
    sp = svf(noise(sr, 0.3, rng), sr, sweep(sr, ns, 4000, 700), 1.0, 'band')
    mix_into(s, mul(sp, env_exp(sr, 0.3, 0.08)), sec(sr, 0.01), 0.5)  # 첨벙
    mix_into(s, thud(sr, 0.25, 95, 40, 0.06), sec(sr, 0.04), 0.9)
    mix_into(s, flame(sr, rng, 0.75, 250, 2400, 0.03), sec(sr, 0.04), 0.85)
    mix_into(s, crackle(sr, rng, 0.7, 12, 0.35), sec(sr, 0.1))
    s = softclip(s, 1.3)
    return tail(s, sr, 0.02)


@sfx('strong_drink', 'CONSUMABLE_USED{id:strongDrink}', "소모품 '깡술 한 모금'(8 s 공격 +20% · 받는 피해 +10% · 경직 없음). 코르크 '퐁' + 빠른 꿀꺽 셋 + 짧은 '크아'(노이즈, 목소리 아님) + 속이 달아오르는 낮은 불 '훅' + 심장 한 번. 독주(potion_use)보다 거칠고 뜨겁다", -3, category='pickup')
def _strong_drink(sr, rng):
    dur = 1.0
    s = zeros(sec(sr, dur))
    mix_into(s, click(sr, rng, 0.004, 2500), 0, 0.6)
    mix_into(s, mul(tone(sr, 0.05, 420, 200), env_exp(sr, 0.05, 0.012)), 0, 0.5)  # 퐁
    for k, t0 in enumerate((0.1, 0.22, 0.34)):
        mix_into(s, gulp(sr, rng, 130 + 15 * k, 300 + 30 * k, 0.11), sec(sr, t0), 0.85)
    mix_into(s, kha(sr, rng, 0.36, 0.45), sec(sr, 0.48), 0.55)
    mix_into(s, flame(sr, rng, 0.45, 180, 900, 0.08), sec(sr, 0.5), 0.55)  # 달아오름
    mix_into(s, heartbeat(sr, rng, 1.0), sec(sr, 0.55), 0.6)
    return tail(s, sr, 0.02)


@sfx('cold_water', 'CONSUMABLE_USED{id:coldWater}', "소모품 '냉수 한 바가지'(그로기 해제·기력 50% / 과열 0 / 탄창·숨 가득, 3 s 기울기 무시). 나무 바가지가 통에 닿는 '톡' + 물 뜨는 출렁 → 머리에 끼얹는 '촤악' + 물방울 + 맑은 '팅' A6 + 길게 내쉬는 숨(노이즈)", -3, category='pickup')
def _cold_water(sr, rng):
    dur = 1.05
    s = zeros(sec(sr, dur))
    mix_into(s, thud(sr, 0.06, 320, 190, 0.012), 0, 0.6)
    mix_into(s, click(sr, rng, 0.003, 2800), 0, 0.3)
    mix_into(s, slosh(sr, rng, 0.2, 500, 1000), sec(sr, 0.03), 0.5)
    ns = sec(sr, 0.4)
    sp = svf(noise(sr, 0.4, rng), sr, sweep(sr, ns, 3200, 800), 0.6, 'band')
    mix_into(s, mul(sp, env_adsr(sr, 0.4, 0.02, 0.05, 0.6, 0.3)), sec(sr, 0.24), 0.9)  # 촤악
    mix_into(s, droplets(sr, rng, 0.5, 10, 0.05, 0.45, 700, 2000, 0.3), sec(sr, 0.3))
    mix_into(s, bell(sr, 0.6, 1760.0, rng, tau=0.25), sec(sr, 0.36), 0.12)  # 맑아짐
    ne = sec(sr, 0.45)
    ex = svf(noise(sr, 0.45, rng), sr, sweep(sr, ne, 1300, 550), 1.1, 'band')
    mix_into(s, mul(ex, env_adsr(sr, 0.45, 0.06, 0.0, 1.0, 0.35)), sec(sr, 0.55), 0.3)
    return tail(s, sr, 0.02)


# ---------------------------------------------------------------------------
# (c) 이벤트 노드 · (d) 숨은 노드
# ---------------------------------------------------------------------------

@sfx('event_enter', 'EVENT_NODE_ENTERED', "이벤트 노드 진입('?' 노드, 1층 9종 중 하나). 촛불이 흔들리는 바람 + 일기장 쪽 넘김 + 낮게 부푸는 D2·A2 드론 + 멀리 종 F4 한 번 + 희미한 고음. 월드 이벤트라 돌방 울림", -3, category='world')
def _event_enter(sr, rng):
    dur = 1.6
    n = sec(sr, dur)
    s = zeros(n)
    fl = svf(noise(sr, 0.5, rng), sr, 420, 1.0, 'band')
    fl = mul(fl, [0.5 + 0.5 * math.sin(TAU * 5.5 * i / sr) for i in range(len(fl))])
    mix_into(s, mul(fl, env_adsr(sr, 0.5, 0.1, 0.0, 1.0, 0.3)), 0, 0.4)  # 촛불
    mix_into(s, paper(sr, rng, 0.2), sec(sr, 0.12), 0.6)  # 쪽 넘김
    dr = add(tone(sr, 1.3, 73.42), scale(tone(sr, 1.3, 110.0), 0.6))
    mix_into(s, mul(dr, env_adsr(sr, 1.3, 0.5, 0.0, 1.0, 0.7)), sec(sr, 0.1), 0.3)
    mix_into(s, lowpass(bell(sr, 1.1, 349.23, rng, tau=0.5), sr, 1800), sec(sr, 0.35), 0.3)
    sh = mul(tone(sr, 0.8, 2793.8, 2800.0), env_adsr(sr, 0.8, 0.2, 0.0, 1.0, 0.5))
    mix_into(s, sh, sec(sr, 0.45), 0.015)
    return reverb(s, sr, size=1.2, decay=0.7, wet=0.32)


@sfx('event_choice', 'UI_MENU_SELECT{menu:event}', "이벤트 선택지 확정('지나간다'는 menu_cancel). 깃펜 한 획 + 가벼운 도장 + 낮은 종 D4. 이벤트 메뉴에서는 menu_select 대신", -4, category='event')
def _event_choice(sr, rng):
    dur = 0.75
    s = zeros(sec(sr, dur))
    mix_into(s, quill_scratch(sr, rng, 0.1, 2800, 4800), 0, 0.5)
    mix_into(s, stamp(sr, rng, 0.7, heavy=0.0), sec(sr, 0.1), 1.0)
    mix_into(s, lowpass(bell(sr, 0.6, 293.66, rng, tau=0.3), sr, 1600), sec(sr, 0.12), 0.35)
    return reverb(s, sr, size=0.6, decay=0.5, wet=0.15)


@sfx('hidden_node_found', 'HIDDEN_NODE_FOUND', "숨은 노드 발견(단서 소품 조사 → 지도에 숨은 길). 속 빈 벽을 두 번 두드림 + 돌이 밀리는 마찰 + 깃펜이 길을 긋는 소리 + 위로 오르는 종 D5·F5·A5(작게)", -2, category='world')
def _hidden_node_found(sr, rng):
    dur = 1.45
    s = zeros(sec(sr, dur))
    for t0 in (0.0, 0.13):  # 두드림
        mix_into(s, thud(sr, 0.09, 230, 140, 0.02), sec(sr, t0), 0.8)
        mix_into(s, burst(sr, 0.03, rng, fc=1100, q=0.8, tau=0.008), sec(sr, t0), 0.4)
    ns = sec(sr, 0.3)
    sc = svf(noise(sr, 0.3, rng), sr, 320, 1.2, 'band')
    sc = mul(sc, [0.6 + 0.4 * math.sin(TAU * 19 * i / sr) for i in range(ns)])
    mix_into(s, mul(sc, env_adsr(sr, 0.3, 0.05, 0.0, 1.0, 0.15)), sec(sr, 0.25), 0.6)  # 돌 밀림
    mix_into(s, quill_scratch(sr, rng, 0.28, 2600, 5000), sec(sr, 0.42), 0.4)
    for k, f in enumerate((587.33, 698.46, 880.0)):
        mix_into(s, bell(sr, 0.8 - 0.06 * k, f, rng, tau=0.35), sec(sr, 0.5 + 0.1 * k), 0.28 - 0.02 * k)
    return reverb(s, sr, size=1.0, decay=0.6, wet=0.25)


# ---------------------------------------------------------------------------
# (h) 약점 파훼 처치 보너스 (두 겹: 다양성 + 결정타)
# ---------------------------------------------------------------------------

@sfx('break_count', 'BOSS_BREAK{distinct:true}', "약점 파훼 다양성 +1(이번 보스전에서 처음 성공한 파훼 종류 — 잔·기둥·술통·취권). 일기장에 표 긋는 '슥' + 나무 틱 + 맑은 종 A5. n번째마다 rate 1.0 / 1.059 / 1.189 / 1.335(A5→B♭5→C6→D6, D 단조) 권장. 파훼 자체 소리(boss1_cup_shatter 등) 뒤 120 ms", -3, category='boss')
def _break_count(sr, rng):
    dur = 0.75
    s = zeros(sec(sr, dur))
    mix_into(s, quill_scratch(sr, rng, 0.07, 2600, 4400), 0, 0.6)
    mix_into(s, thud(sr, 0.05, 420, 300, 0.01), sec(sr, 0.06), 0.5)
    mix_into(s, bell(sr, 0.65, 880.0, rng, tau=0.3), sec(sr, 0.06), 0.4)
    return reverb(s, sr, size=0.6, decay=0.5, wet=0.15)


@sfx('break_finisher', 'BOSS_BREAK{kind:finisher}', "결정타(파훼 경직 중 마지막 일격 → 전표 +50 · 개성 +30 · 도감 기록). 0.08 s 빨려드는 역바람 → 밝은 칼날 울림 D6 + 쪼개지는 쇠 + 큰 징 D3 + 종 D5·A5·D6, 길게 울림. boss_die 와 같은 프레임에 겹침(대역이 위·아래로 나뉨, 파일 0.08 s = 일격)", 0, category='boss')
def _break_finisher(sr, rng):
    dur = 1.9
    s = zeros(sec(sr, dur))
    m = sec(sr, 0.08)
    pre = svf(noise(sr, 0.08, rng), sr, sweep(sr, m, 800, 6000), 1.5, 'band')
    mix_into(s, mul(pre, [(i / m) ** 2 for i in range(m)]), 0, 0.6)
    mix_into(s, click(sr, rng, 0.004, 6000), m, 0.9)
    mix_into(s, thud(sr, 0.3, 125, 42, 0.06), m, 1.3)  # 일격의 무게(boss_die 의 긴 추락음보다 짧고 단단하게)
    mix_into(s, burst(sr, 0.08, rng, fc=1500, q=0.8, tau=0.016), m, 0.9)
    mix_into(s, metal(sr, 0.5, 760, rng, tau=0.1, jitter=0.04), m, 0.45)  # 쪼개지는 쇠
    mix_into(s, blade_ring(sr, 1.2, 1174.66, rng, bright=1.0, tau=0.45, vib=0.002), m, 0.4)
    mix_into(s, jing(sr, 1.6, 146.83, rng, bright=0.3, tau=0.9), m, 0.5)
    for k, f in enumerate((587.33, 880.0, 1174.66)):
        mix_into(s, bell(sr, 1.3 - 0.1 * k, f, rng, tau=0.5), m + sec(sr, 0.12 + 0.07 * k), 0.24)
    sh = mul(tone(sr, 1.2, 3520, 3540), env_adsr(sr, 1.2, 0.1, 0.0, 1.0, 0.9))
    mix_into(s, sh, m, 0.02)
    s = softclip(s, 1.3)
    return reverb(s, sr, size=1.3, decay=0.75, wet=0.32)


# ---------------------------------------------------------------------------
# 증류 화로 (1-2, 통과형 → 불 무기 6 s, 저주 '불붙은 혀' 획득처)
# ---------------------------------------------------------------------------

@sfx('still_ignite', 'STRUCTURE_FIRE', "증류 화로 통과 → 무기에 불(fireWeapon 6 s). 증류기 끓는 거품 + 화로가 '후욱' 숨 쉬듯 타오름 + 칼날에 불이 옮겨붙는 '화륵' + 달아오르는 쇠 험 D4 + 타닥. 이어서 fire_weapon_loop", -2, category='world')
def _still_ignite(sr, rng):
    dur = 1.15
    s = zeros(sec(sr, dur))
    mix_into(s, droplets(sr, rng, 0.35, 8, 0.0, 0.3, 250, 600, 0.3), 0)  # 끓는 거품
    mix_into(s, flame(sr, rng, 0.5, 150, 700, 0.12), 0, 0.6)  # 화로 숨
    mix_into(s, thud(sr, 0.2, 90, 45, 0.05), sec(sr, 0.22), 0.6)
    mix_into(s, flame(sr, rng, 0.7, 300, 3200, 0.04), sec(sr, 0.22), 0.8)  # 옮겨붙음
    hot = mul(lowpass(tone(sr, 0.7, 293.66, 297.0, kind='saw'), sr, 900), env_adsr(sr, 0.7, 0.2, 0.0, 1.0, 0.4))
    mix_into(s, hot, sec(sr, 0.25), 0.12)
    mix_into(s, crackle(sr, rng, 0.8, 14, 0.35), sec(sr, 0.25))
    s = softclip(s, 1.2)
    return tail(s, sr, 0.02)


@sfx('fire_weapon_loop', 'STATUS_CHANGED{id:fireWeapon,phase:start}', "불 무기 지속 루프(1.0 s, fireWeapon 6 s 동안). 칼날을 핥는 낮은 불길(2·5 Hz 일렁임) + 아주 작은 쉿 + 드문 타닥 + 희미한 D4 쇠 험. 시작 200 ms 페이드인, 상태 끝(fire_weapon_end)에서 150 ms 페이드아웃. 전투음 아래에 깔리게 작게", -14, loop=True)
def _fire_weapon_loop(sr, rng):
    dur = 1.0
    n = sec(sr, dur)
    s = wrap2(lambda x: svf(x, sr, 520, 0.7, 'low'), noise_loop(sr, n, rng))
    fl = [a * b for a, b in zip(lfo_loop(sr, n, 2.0, 0.25, 0.75), lfo_loop(sr, n, 5.0, 0.15, 0.85, 0.3))]
    s = mul(s, fl)
    hiss = wrap2(lambda x: svf(x, sr, 3200, 0.7, 'high'), noise_loop(sr, n, rng))
    mix_into(s, hiss, 0, 0.04)
    hum = mul(tone_loop(sr, n, 293.66, 'sine', 0.25), lfo_loop(sr, n, 3.0, 0.4, 0.6, 0.25))
    mix_into(s, hum, 0, 0.04)
    mix_into(s, fade_edges(crackle(sr, rng, dur - 0.05, 9, 0.4), sr, 0.005), sec(sr, 0.02))
    return s


@sfx('fire_weapon_end', 'STATUS_CHANGED{id:fireWeapon,phase:end}', "불 무기 꺼짐(6 s 끝). 식는 쇠의 증기 쉿(5k→2k) + 작은 '푸' + 마지막 타닥 둘. fire_weapon_loop 를 150 ms 페이드아웃하며 같은 프레임", -6)
def _fire_weapon_end(sr, rng):
    dur = 0.5
    n = sec(sr, 0.42)
    s = zeros(sec(sr, dur))
    st = svf(noise(sr, 0.42, rng), sr, sweep(sr, n, 5200, 2000), 0.8, 'band')
    mix_into(s, mul(st, env_adsr(sr, 0.42, 0.01, 0.0, 1.0, 0.38)), 0, 0.6)
    mix_into(s, lowpass(thud(sr, 0.08, 160, 80, 0.02), sr, 500), 0, 0.4)
    mix_into(s, crackle(sr, rng, 0.3, 2, 0.4), sec(sr, 0.04))
    return tail(s, sr, 0.03)
