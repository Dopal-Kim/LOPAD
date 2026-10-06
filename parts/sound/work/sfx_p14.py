# -*- coding: utf-8 -*-
"""
61라운드 단계 6 (P14) — 그림 속 입구 전환 3 · 수련장 과제·도장 2 (+ 과제 종 변주 2). round '61-6'.

build.py 가 sfx_stage61 다음(마지막)에 import 한다. 시드 = 1000 + 등록 순서 — 이 모듈은 끝에 붙으므로 기존 305개는
바이트 불변이다. sfx_stage61.py 가 1700줄을 넘어 새 단계부터 모듈을 나눴다(CLAUDE.md 6-1). **새 효과음은 이 파일 끝에만.**

시스템 확정 트리거(계약 sound §12, 시스템 audioTraining.ts):
  TRANSITION_BEGIN{mode}  enterNode·training → transition_enter · exitRoom → transition_exit · floor → transition_floor(없으면 enter)
  TRAINING_TASK{room,id}  → training_task(+_v2·_v3 번갈아) · TRAINING_STAMP{room,all} → training_stamp
UI 전환 타이밍(설계 P14 §3): 0~1.1 s 입구로 파고듦·어둠이 덮음 → 그 뒤 먹 붓질이 걷히며 방이 나타남. 건너뛰기(아무 키) 가능 —
건너뛰면 시스템이 전환음을 150 ms 페이드로 끊는다(manifest mixing.transition).

재료 원칙: 종이(고역 사각임 · 결) · 바람(좁은 대역 스윕) · 먹(젖은 저역 번짐) · 붓(털 결 진폭 떨림) · 나무 액자 '톡'.
전투 소리(쇠·화약) 재료는 쓰지 않는다 — 그림 세계로 넘어가는 소리라 재료를 갈라 둔다.
"""
from build import *  # noqa: F401,F403
from build import SFX, droplets  # noqa: F401
from sfx_core61 import punch, rustle, sub, wood_tok, variant  # noqa: F401

ROUND6 = '61-6'   # listen_index 의 round 값(61라운드 단계 6 · P14)


def sfx6(name, trigger, note, gain_db=0.0, loop=False, category='world'):
    """sfx() + round 표시(61-6)."""
    def deco(fn):
        sfx(name, trigger, note, gain_db, loop=loop, category=category)(fn)
        SFX[name]['round'] = ROUND6
        return fn
    return deco


def variant6(base, k, note):
    """sfx_core61.variant() + round 표시(61-6)."""
    def deco(fn):
        variant(base, k, note)(fn)
        SFX['%s_v%d' % (base, k)]['round'] = ROUND6
        return fn
    return deco


# ===========================================================================
# 재료
# ===========================================================================

def _grain(sr, rng, n, rate):
    """0~1 무작위 진폭 결(rate Hz 저역통과, 최대 1로 정규화)."""
    return normalize(lowpass([rng.uniform(0, 1) ** 2 for _ in range(n)], sr, rate), 1.0)


def paper(sr, rng, dur, density=60.0, fc=(2600, 7000), g=1.0, bed=0.35):
    """종이 사각임: 짧은 고역 바스락 알갱이(초당 density 개, fc 범위) + 얇게 깔린 종이 결(고역 rustle)."""
    s = zeros(sec(sr, dur))
    count = max(1, int(density * dur))
    for _ in range(count):
        t = sec(sr, rng.uniform(0, dur * 0.92))
        d = rng.uniform(0.004, 0.014)
        c = burst(sr, d, rng, fc=rng.uniform(fc[0], fc[1]), q=rng.uniform(0.9, 1.6), tau=rng.uniform(0.001, 0.004))
        mix_into(s, c, t, rng.uniform(0.25, 1.0))
    if bed:
        mix_into(s, highpass(rustle(sr, rng, dur, (fc[0] + fc[1]) * 0.5, 60.0, 0.7), sr, fc[0] * 0.7), 0, bed)
    return scale(mul(s, env_adsr(sr, dur, dur * 0.12, 0.0, 1.0, dur * 0.45)), g)


def inhale_wind(sr, rng, dur, f0, f1, q=0.9, power=2.2, cut=0.06):
    """안쪽으로 빨려드는 바람: 대역이 오르며 점점 커지다(지수 power) 끝에서 cut 초에 닫힘(입구 안으로 삼켜짐)."""
    n = sec(sr, dur)
    w = svf(noise(sr, dur, rng), sr, sweep(sr, n, f0, f1), q, 'band')
    nc = max(1, sec(sr, cut))
    env = [((i / n) ** power) * (1.0 if i < n - nc else (n - i) / nc) for i in range(n)]
    return mul(w, env)


def dive_swell(sr, dur, f0, f1, peak=0.8, fc=220):
    """그림 안으로 깊어지는 낮은 부풂: 내려가는 사인(f0→f1)이 peak 지점까지 차오르고 빠짐 — 저역통과."""
    n = sec(sr, dur)
    s = tone(sr, dur, f0, f1)
    k = max(1, int(n * peak))
    env = [((i / k) ** 1.6) if i < k else max(0.0, 1.0 - (i - k) / max(1, n - k)) ** 1.5 for i in range(n)]
    return lowpass(mul(s, env), sr, fc)


def ink_bloom(sr, rng, dur, f0=320, f1=1100, g=1.0):
    """먹 번짐: 젖은 저역 노이즈가 천천히 퍼짐(대역 f0→f1 열렸다 닫힘) + 느린 물결 떨림 — 어택 없음."""
    n = sec(sr, dur)
    fc = [f0 + (f1 - f0) * math.sin(math.pi * min(1.0, i / n)) for i in range(n)]
    s = svf(noise(sr, dur, rng), sr, fc, 0.8, 'low')
    s = mul(s, [0.65 + 0.35 * v for v in _grain(sr, rng, n, 9.0)])
    return scale(mul(s, env_adsr(sr, dur, dur * 0.35, 0.0, 1.0, dur * 0.55, curve=0.7)), g)


def blot(sr, f0=170, f1=85, g=1.0):
    """먹이 종이에 '툭' 스밈: 둥근 저역 몸통(저역통과 — 딱 소리 없음)."""
    return scale(lowpass(punch(sr, f0, f1, 0.22, 0.06, 1.1), sr, 600), g)


def brush(sr, rng, dur, f0, f1, g=1.0, bristle=0.55, q=0.8, a=0.25, r=0.5):
    """붓 한 획: 털 결(80~150 Hz 무작위 떨림)이 있는 대역 노이즈 스윕. 종이에 닿아 끌리는 '쓱'."""
    n = sec(sr, dur)
    s = svf(noise(sr, dur, rng), sr, sweep(sr, n, f0, f1), q, 'band')
    s = mul(s, [1 - bristle + bristle * v for v in _grain(sr, rng, n, rng.uniform(80, 150))])
    mix_into(s, highpass(svf(noise(sr, dur, rng), sr, f1 * 1.8, 1.2, 'band'), sr, 2500), 0, 0.25)   # 털끝 마찰
    return scale(mul(s, env_adsr(sr, dur, dur * a, 0.0, 1.0, dur * r, curve=0.8)), g)


def frame_tok(sr, rng, f=820, g=1.0):
    """나무 액자 닫힘 '톡': 액자 테 나무 '톡' + 작은 몸통 + 18 ms 뒤 걸쇠처럼 더 높은 작은 '틱'."""
    s = zeros(sec(sr, 0.16))
    mix_into(s, wood_tok(sr, rng, f, 0.09, 0.014, 0.7), 0, 1.0)
    mix_into(s, lowpass(punch(sr, 260, 150, 0.09, 0.022, 1.2), sr, 900), 0, 0.55)
    mix_into(s, wood_tok(sr, rng, f * 1.9, 0.05, 0.006, 0.5), sec(sr, 0.018), 0.35)
    return scale(s, g)


def _enter(sr, rng, dur, cover, wind, sub_f, paper_fc, ink, strokes, boom=0.0, sub_g=0.35):
    """그림 속 입구 공통 틀. cover = 어둠이 화면을 덮는 시각(바람이 삼켜지는 순간). strokes = 걷히는 붓질 [(시각, 길이, f0, f1, g)]."""
    s = zeros(sec(sr, dur))
    # 0 s 종이 사각임(그림 두루마리에 다가감) — 앞쪽에 몰리고 점점 성기게
    mix_into(s, paper(sr, rng, 0.42, 70, paper_fc, 0.9), 0, 0.8)
    mix_into(s, paper(sr, rng, 0.5, 25, paper_fc, 0.6, bed=0.2), sec(sr, 0.3), 0.45)
    # 안쪽으로 빨려드는 바람 + 깊어지는 낮은 부풂(덮이는 순간이 정점)
    mix_into(s, inhale_wind(sr, rng, cover, wind[0], wind[1], 0.9, 2.2, 0.07), 0, 0.85)
    mix_into(s, inhale_wind(sr, rng, cover * 0.92, wind[0] * 1.6, wind[1] * 1.7, 2.5, 2.6, 0.05), sec(sr, cover * 0.08), 0.22)
    mix_into(s, dive_swell(sr, cover + 0.25, sub_f[0], sub_f[1], cover / (cover + 0.25)), 0, sub_g)
    if boom:
        mix_into(s, sub(sr, 95, 38, 0.6, 0.18, 160), sec(sr, cover - 0.01), boom)
    # 먹 번짐: 덮이기 조금 전에 스며들어 덮이는 순간 '툭' 스밈
    mix_into(s, ink_bloom(sr, rng, ink[1], ink[2], ink[3]), sec(sr, ink[0]), 0.6)
    mix_into(s, blot(sr, 170 if not boom else 130, 85 if not boom else 60), sec(sr, cover), 0.45)
    # 걷히는 먹 붓질(방이 나타남)
    for t, d, f0, f1, g in strokes:
        mix_into(s, brush(sr, rng, d, f0, f1), sec(sr, t), g)
    return tail(reverb(s, sr, size=1.1, decay=0.55, wet=0.18), sr, 0.02)


# ===========================================================================
# 1. 그림 속 입구 전환 (TRANSITION_BEGIN{mode})
# ===========================================================================

@sfx6('transition_enter', 'TRANSITION_BEGIN{mode:enterNode|training}', "61-6 새 — 그림 속 입구로 파고듦(노드·수련장 방 들어가기). 0 s 두루마리 종이 사각임(2.6~7 kHz 알갱이, 점점 성기게) → 안쪽으로 빨려드는 바람(250 Hz→1.9 kHz 로 오르며 점점 커짐) + 깊어지는 낮은 부풂(120→55 Hz) → 1.10 s 어둠이 덮이며 바람이 삼켜지고(70 ms 닫힘) 먹이 '툭' 스밈 + 젖은 먹 번짐(0.8~1.45 s) → 1.12·1.26 s 걷히는 붓질 두 획. 1.45 s(UI: 0~1.1 s 파고듦·덮임, 그 뒤 붓질 걷힘). 쇠·화약 재료 없음", -2)
def _transition_enter(sr, rng):
    return _enter(sr, rng, 1.43, 1.10, (250, 1900), (120, 55), (2600, 7000), (0.80, 0.62, 300, 1100),
                  [(1.12, 0.20, 900, 2800, 0.6), (1.26, 0.17, 1200, 3300, 0.45)])


@sfx6('transition_exit', 'TRANSITION_BEGIN{mode:exitRoom}', "61-6 새 — 방 화면이 그림으로 굳어 액자에 들어감(출구로 나가기). 0 s 붓 한 획 '쓱'(털 결 떨림, 1.1→3.4 kHz 로 끌리다 2.2 kHz 로 빠짐, 0.40 s) → 0.22~0.95 s 굳어 가는 종이 결(마른 바스락, 점점 성기게) + 얇게 마르는 바람 → 0.95 s 액자 닫히는 나무 '톡' + 걸쇠 '틱'(18 ms 뒤) + 작은 방 울림. 1.30 s(그 뒤 줌 아웃해 두루마리 지도로)", -2)
def _transition_exit(sr, rng):
    dur = 1.28
    s = zeros(sec(sr, dur))
    st = brush(sr, rng, 0.40, 1100, 3400, bristle=0.6, a=0.18, r=0.55)
    mix_into(st, brush(sr, rng, 0.18, 3400, 2200, bristle=0.5, a=0.1, r=0.8), sec(sr, 0.24), 0.45)   # 획 끝 붓 빠짐
    mix_into(s, st, 0, 0.9)
    mix_into(s, lowpass(punch(sr, 210, 140, 0.05, 0.012, 1.0), sr, 700), 0, 0.15)                  # 붓이 닿는 작은 눌림
    mix_into(s, paper(sr, rng, 0.75, 45, (2200, 5600), 1.0, bed=0.3), sec(sr, 0.22), 0.4)
    n = sec(sr, 0.7)
    dry = svf(noise(sr, 0.7, rng), sr, sweep(sr, n, 1800, 900), 0.8, 'band')
    mix_into(s, mul(dry, env_adsr(sr, 0.7, 0.15, 0.0, 1.0, 0.45)), sec(sr, 0.25), 0.18)
    mix_into(s, frame_tok(sr, rng, 820), sec(sr, 0.95), 0.75)
    return tail(reverb(s, sr, size=0.8, decay=0.45, wet=0.15), sr, 0.02)


@sfx6('transition_floor', 'TRANSITION_BEGIN{mode:floor}', "61-6 새 — 큰 그림 입구(층 넘어가기, 다음 지역 키아트로 들어감). transition_enter 와 같은 틀을 더 깊고 낮게: 낮은 종이 사각임(2~5.5 kHz) → 더 낮게 빨려드는 바람(150 Hz→1.2 kHz, 1.22 s 동안) + 깊은 부풂(90→40 Hz) → 1.22 s 덮이며 멀리서 울리는 낮은 '둥'(95→38 Hz) + 더 크고 긴 먹 번짐(220~800 Hz, 0.85~1.6 s) → 1.24·1.38 s 느린 붓질 두 획. 1.60 s", -2)
def _transition_floor(sr, rng):
    return _enter(sr, rng, 1.58, 1.22, (150, 1200), (90, 40), (2000, 5500), (0.85, 0.75, 220, 800),
                  [(1.24, 0.24, 700, 2200, 0.55), (1.38, 0.2, 900, 2600, 0.42)], boom=0.6, sub_g=0.55)


# ===========================================================================
# 2. 수련장 (TRAINING_TASK · TRAINING_STAMP)
# ===========================================================================

def _chime(sr, rng, f):
    """맑은 작은 종: 거의 조화 배음(1·2·3 — 쇳소리 없이 둥글게), 4 ms 어택, τ 0.11 s, 6.5 kHz 저역통과 — 자주 울려도 귀가 덜 지침."""
    dur = 0.40
    s = zeros(sec(sr, dur))
    for ratio, amp, tau in ((1.0, 1.0, 0.11), (2.0, 0.22, 0.06), (3.01, 0.06, 0.035)):
        mix_into(s, mul(tone(sr, dur, f * ratio * (1 + rng.uniform(-0.001, 0.001))), env_exp(sr, dur, tau)), 0, amp)
    s = mul(s, env_adsr(sr, dur, 0.004, 0.0, 1.0, 0.12))
    mix_into(s, mul(tone(sr, 0.15, f * 2.0 * 1.003), env_exp(sr, 0.15, 0.03)), sec(sr, 0.002), 0.05)   # 아주 얇은 반짝임
    return lowpass(reverb(s, sr, size=0.6, decay=0.4, wet=0.14), sr, 6500)


@sfx6('training_task', 'TRAINING_TASK', "61-6 새 — 수련장 과제 하나 완료(과제 목록 체크). 짧고 맑은 작은 종 A5(880 Hz, 배음 1·2·3 — 둥글게), 4 ms 부드러운 어택, 0.11 s 감쇠, 6.5 kHz 위 깎음. 0.40 s. 변주 _v2 C6 · _v3 E6(A 단조 화음 — 수련장 곡과 같은 조, 연달아 울리면 화음처럼)", -7, category='event')
def _training_task(sr, rng):
    return _chime(sr, rng, 880.0)


@variant6('training_task', 2, "61-6 변주 — training_task C6(1046.5 Hz)")
def _training_task_v2(sr, rng):
    return _chime(sr, rng, 1046.5)


@variant6('training_task', 3, "61-6 변주 — training_task E6(1318.5 Hz)")
def _training_task_v3(sr, rng):
    return _chime(sr, rng, 1318.5)


def _tack(sr, rng, dur, count, lo=700, hi=2400):
    """인주 끈적: 떨어지며 아주 작은 젖은 '쩍' 알갱이가 몰렸다 끊김(점점 촘촘·작게)."""
    s = zeros(sec(sr, dur))
    for k in range(count):
        x = (k / max(1, count - 1)) ** 0.6
        c = burst(sr, 0.006, rng, fc=rng.uniform(lo, hi), q=2.0, tau=rng.uniform(0.0006, 0.0016))
        mix_into(s, c, sec(sr, x * dur * 0.9), (1.0 - 0.6 * x) * rng.uniform(0.5, 1.0))
    return lowpass(s, sr, 3500)


@sfx6('training_stamp', 'TRAINING_STAMP', "61-6 새 — 수련장 방 도장(과제를 다 하면 인장을 찍음). 0 s 종이 눌림 바스락(짧게) + 인장이 꾹 찍히는 둔탁한 '쿡'(150→75 Hz, 3 ms 부드러운 어택, 900 Hz 위 깎음 — 딱 소리 없음) + 돌 인장 몸 '톡'(낮게) → 0.05 s 한 번 더 누름(더 낮게) → 0.30 s 떼어낼 때 인주 끈적 '쩍'(젖은 알갱이 14개, 1.5~3.5 kHz 밑) + 작은 흡착 '뽁'(280→520 Hz). 0.60 s", -3, category='event')
def _training_stamp(sr, rng):
    dur = 0.58
    s = zeros(sec(sr, dur))
    mix_into(s, paper(sr, rng, 0.07, 140, (2000, 5000), 1.0, bed=0.0), 0, 0.3)
    k = lowpass(punch(sr, 150, 75, 0.22, 0.05, 1.3), sr, 900)
    mix_into(s, mul(k, env_adsr(sr, 0.22, 0.003, 0.0, 1.0, 0.15)), 0, 1.0)
    mix_into(s, lowpass(burst(sr, 0.05, rng, fc=500, q=0.7, tau=0.012, mode='low'), sr, 900), 0, 0.5)
    mix_into(s, lowpass(wood_tok(sr, rng, 620, 0.07, 0.01, 0.4), sr, 1800), sec(sr, 0.002), 0.3)
    mix_into(s, lowpass(punch(sr, 110, 60, 0.15, 0.04, 1.1), sr, 500), sec(sr, 0.05), 0.45)
    mix_into(s, _tack(sr, rng, 0.11, 14), sec(sr, 0.30), 0.6)
    pop = mul(tone(sr, 0.05, 280, 520), env_adsr(sr, 0.05, 0.006, 0.0, 1.0, 0.035))
    mix_into(s, lowpass(pop, sr, 1200), sec(sr, 0.39), 0.25)
    return tail(reverb(s, sr, size=0.5, decay=0.35, wet=0.1), sr, 0.02)
