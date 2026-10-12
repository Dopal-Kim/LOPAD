# -*- coding: utf-8 -*-
"""
62라운드 루프 2 (P16) — 1층 결 효과음: 메뉴 공통 · 적 등장 예고 · 슬로모(마지막 처치·사망) · 노드 시련 성공/실패 ·
1층 끝 결산 · 메타 '기억' 해금 · 상점(사기 다시·다시 진열 다시) · NPC 말 걸기 · 유품 획득 · 설정 토글. round '62-2'.
+ 7절 외벽 문(62-2E) · 8절 노드 이동 짧은 먹 번짐 암전 transition_fade(62 루프 3 시스템 H, round '62-3').

build.py 가 sfx_p14 다음(마지막)에 import 한다. 시드 = 1000 + 등록 순서 — 새 소리는 끝에 붙으므로 기존 312개는 바이트 불변,
`redo()` 로 다시 만든 shop_buy·shop_reroll 은 원래 자리(시드)를 지킨다. **새 효과음은 이 파일 끝에만.**

근거: 결정 `parts/producer/decisions/2026-10-12-P16-loop2.md`(§2 층 끝 · §3 죽음 · §4 기억 · §5 이벤트·상점 · §7 설정 ·
루프 1 요청 '적 등장 예고·마지막 처치 슬로모·메뉴 이동/선택'), 점검 `review-2026-10-12-stage1-competitive-audit.md` P2-3·T8.
시각 기준(시스템 읽기만): 등장 바닥 문양 1.0 s(`ENEMY_INCOMING.WAVE_DELAY_MS` 1000, 노드 첫 웨이브 +0.5 s) ·
마지막 처치 슬로모 0.3배 280 ms(`FEEL.KILL.SLOW`, 시련 끝 TRIAL_CLEARED) · 사망 0.25배 0.6 s → 먹 번짐(P16 §3).

재료 원칙(1층 결): 먹(젖은 저역 번짐·스밈·붓) · 나무(톡·좌판·마루) · 쇠(울림 없이 짧은 '탁' — 3 kHz 위 금속 꼬리 금지,
60 Q22 '프라이팬' 지양) · 불씨(타닥·잿불 일어남·꺼짐 '치익'). 음높이가 있는 것은 1층 곡과 같은 A 단조(A·C·E, 결산은 F 로 열림).
"""
from build import *  # noqa: F401,F403
from build import SFX, crackle, heartbeat  # noqa: F401
from sfx_core61 import punch, rustle, sub, wood_tok, snap, sparks, variant  # noqa: F401
from sfx_stage61 import redo, creak
from sfx_p14 import paper, ink_bloom, blot, brush  # noqa: F401

ROUND = '62-2'   # listen_index 의 round 값(62라운드 루프 2 · P16)


def sfx16(name, trigger, note, gain_db=0.0, loop=False, category='event'):
    """sfx() + round 표시(62-2)."""
    def deco(fn):
        sfx(name, trigger, note, gain_db, loop=loop, category=category)(fn)
        SFX[name]['round'] = ROUND
        return fn
    return deco


def variant16(base, k, note):
    """sfx_core61.variant() + round 표시(62-2)."""
    def deco(fn):
        variant(base, k, note)(fn)
        SFX['%s_v%d' % (base, k)]['round'] = ROUND
        return fn
    return deco


def fallback(name, by):
    """오디오·시드 그대로, note 앞에 [폴백 …] 표시 — 새 소리(by)가 대신하고 시스템이 새 id 가 없을 때만 쓴다."""
    SFX[name] = dict(SFX[name], note='[폴백 — 62-2: %s] %s' % (by, SFX[name]['note']))


# ===========================================================================
# 재료
# ===========================================================================

def ember(sr, rng, dur, count, g=1.0, fc=4200):
    """불씨 타닥: crackle 을 4.2 kHz 아래로 깎아 따뜻하게(쇠 빛 없는 잿불)."""
    return scale(lowpass(crackle(sr, rng, dur, count, 0.5), sr, fc), g)


def ember_flare(sr, rng, dur, f0=700, f1=3200, g=1.0, count=10):
    """잿불이 확 일어남: 오르는 대역 노이즈 '화르' + 타닥 몇 개(앞은 성기고 뒤로 촘촘)."""
    n = sec(sr, dur)
    s = svf(noise(sr, dur, rng), sr, sweep(sr, n, f0, f1), 0.9, 'band')
    s = mul(s, env_adsr(sr, dur, dur * 0.55, 0.0, 1.0, dur * 0.45, curve=1.6))
    mix_into(s, ember(sr, rng, dur, count, 0.8), 0, 1.0)
    return scale(s, g)


def snuff(sr, rng, dur=0.26, f0=4200, f1=1300, g=1.0):
    """불씨 꺼짐 '치익': 내려가는 좁은 대역 쉿 + 끝에 작은 타닥 둘."""
    n = sec(sr, dur)
    s = svf(noise(sr, dur, rng), sr, sweep(sr, n, f0, f1), 1.6, 'band')
    s = mul(s, env_adsr(sr, dur, 0.01, 0.0, 1.0, dur * 0.8, curve=0.8))
    mix_into(s, ember(sr, rng, dur * 0.6, 2, 0.5), sec(sr, dur * 0.4), 1.0)
    return scale(s, g)


def chime(sr, rng, f, dur=0.4, tau=0.12, g=1.0, lp=6000):
    """맑은 작은 종(sfx_p14 수련장 종 계보): 조화 배음 1·2·3, 4 ms 어택, 저역통과 — 쇳소리 없이 둥글게."""
    s = zeros(sec(sr, dur))
    for ratio, amp, t in ((1.0, 1.0, tau), (2.0, 0.2, tau * 0.55), (3.01, 0.05, tau * 0.32)):
        mix_into(s, mul(tone(sr, dur, f * ratio * (1 + rng.uniform(-0.001, 0.001))), env_exp(sr, dur, t)), 0, amp)
    s = mul(s, env_adsr(sr, dur, 0.004, 0.0, 1.0, dur * 0.3))
    return scale(lowpass(s, sr, lp), g)


def iron_tak(sr, rng, f=1700, g=1.0):
    """쇠 '탁'(울림 없음): 딸깍 + 짧은 쇠 배음(τ 12 ms) 을 4.5 kHz 아래로 + 아래 몸통 — 걸쇠·장신구."""
    s = zeros(sec(sr, 0.09))
    mix_into(s, click(sr, rng, 0.004, 3800), 0, 0.6)
    m = metal(sr, 0.08, f, rng, partials=[(1.0, 1.0), (1.52, 0.5), (2.31, 0.25)], tau=0.012, jitter=0.02)
    mix_into(s, lowpass(m, sr, 4500), 0, 0.5)
    mix_into(s, lowpass(punch(sr, 260, 150, 0.06, 0.012, 1.1), sr, 900), 0, 0.5)
    return scale(s, g)


def bellows(sr, dur, f, a=0.25, r=0.6, fc=1100, detune=0.004):
    """손풍금 리드를 바람통으로 천천히 부풀린 음(1층 곡 f1_jan·training 의 손풍금과 같은 재료, 느린 어택)."""
    x = add(tone(sr, dur, f * (1 - detune), kind='pulse'), scale(tone(sr, dur, f * (1 + detune), kind='square'), 0.6))
    x = add(scale(svf(x, sr, fc, 0.8, 'band'), 0.8), scale(lowpass(x, sr, 2000), 0.3))
    return mul(x, env_adsr(sr, dur, a, 0.0, 1.0, r, curve=1.4))


def air_drop(sr, rng, dur, f0, f1, g=1.0):
    """시간이 굳는 공기: 넓은 노이즈의 저역통과 차단 주파수가 f0 → f1 로 내려가며(귀가 먹먹) 줄어듦."""
    n = sec(sr, dur)
    s = svf(noise(sr, dur, rng), sr, sweep(sr, n, f0, f1), 0.7, 'low')
    return scale(mul(s, env_adsr(sr, dur, 0.008, 0.0, 1.0, dur * 0.85, curve=0.7)), g)


def air_rise(sr, rng, dur, f0, f1, g=1.0):
    """돌아오는 공기 '후욱': 오르는 대역 노이즈, 뒤가 커졌다 빠르게 닫힘."""
    n = sec(sr, dur)
    s = svf(noise(sr, dur, rng), sr, sweep(sr, n, f0, f1), 1.0, 'band')
    return scale(mul(s, env_adsr(sr, dur, dur * 0.6, 0.0, 1.0, dur * 0.4, curve=1.8)), g)


# ===========================================================================
# 1. 메뉴 공통 (타이틀 · 일기장 · 카드) — category ui
# ===========================================================================

def _bead(sr, rng, f):
    """먹 묻은 나무 구슬 '톡': 낮고 둥근 나무 톡(f) + 종이 결 아주 얇게(3 kHz 위 12 ms)."""
    s = zeros(sec(sr, 0.08))   # 0.08 s: 더 짧으면 ffmpeg 6.1 OGG 디코더가 끝을 자른다(61 menu_move 참고)
    mix_into(s, wood_tok(sr, rng, f, 0.05, 0.006, 0.45), 0, 1.0)
    mix_into(s, lowpass(punch(sr, f * 0.32, f * 0.2, 0.04, 0.008, 1.0), sr, 700), 0, 0.35)
    mix_into(s, highpass(paper(sr, rng, 0.012, 300, (3000, 6000), 1.0, bed=0.0), sr, 2500), 0, 0.18)
    return s


@sfx16('ui_move', 'UI_MENU_MOVE', "62-2 새 — 메뉴 커서 이동(타이틀·일기장·카드·설정 공통, menu_move 를 대신). 먹 묻은 나무 구슬을 톡 — 낮고 둥근 나무 '톡'(780 Hz, 6 ms 감쇠) + 아래 작은 몸통 + 종이 결 아주 얇게. 0.08 s(소리는 0.04 s 안에 끝). 변주 _v2(700 Hz)와 번갈아 — 커서가 걷는 느낌. 빠르게 넘겨도 귀가 지치지 않게 2 kHz 위가 거의 없다", -8, category='ui')
def _ui_move(sr, rng):
    return _bead(sr, rng, 780)


@variant16('ui_move', 2, '62-2 변주 — ui_move 700 Hz')
def _ui_move_v2(sr, rng):
    return _bead(sr, rng, 700)


@sfx16('ui_select', 'UI_MENU_SELECT', "62-2 새 — 메뉴 고름·확정(menu_select 를 대신). 0 s 짧은 붓 '쓱'(1.6→3.2 kHz, 털 결) → 12 ms 먹 도장 '꾹'(190→85 Hz, 700 Hz 위 깎음 — 딱 소리 없음) + 나무 '톡'(620 Hz) → 25~70 ms 불씨 두세 점(4.2 kHz 밑, 아주 작게). 0.22 s", -7, category='ui')
def _ui_select(sr, rng):
    s = zeros(sec(sr, 0.22))
    mix_into(s, brush(sr, rng, 0.07, 1600, 3200, bristle=0.5, a=0.2, r=0.6), 0, 0.45)
    k = lowpass(punch(sr, 190, 85, 0.15, 0.03, 1.25), sr, 700)
    mix_into(s, mul(k, env_adsr(sr, 0.15, 0.003, 0.0, 1.0, 0.1)), sec(sr, 0.012), 1.0)
    mix_into(s, wood_tok(sr, rng, 620, 0.05, 0.008, 0.4), sec(sr, 0.014), 0.3)
    mix_into(s, ember(sr, rng, 0.05, 3, 1.0), sec(sr, 0.025), 0.18)
    return s


@sfx16('ui_back', 'UI_MENU_CANCEL', "62-2 새 — 뒤로·닫기(menu_cancel 을 대신). 붓을 들어 올리는 '스' (2.4→1.1 kHz, 내려가며 빠짐) → 55 ms 종이를 내려놓는 둥근 '툭'(160→100 Hz, 저역만). ui_select 보다 작고 아래로 떨어진다. 0.16 s", -8, category='ui')
def _ui_back(sr, rng):
    s = zeros(sec(sr, 0.16))
    mix_into(s, brush(sr, rng, 0.08, 2400, 1100, bristle=0.45, a=0.12, r=0.8), 0, 0.6)
    mix_into(s, lowpass(punch(sr, 160, 100, 0.08, 0.016, 1.1), sr, 500), sec(sr, 0.055), 0.6)
    mix_into(s, wood_tok(sr, rng, 520, 0.04, 0.006, 0.3), sec(sr, 0.056), 0.18)
    return s


@sfx16('ui_toggle', 'UI_SETTING_TOGGLED', "62-2 새 — 설정 켜고 끄기(전체화면·히트스톱·흔들림·글자 크기 등). 작은 쇠 걸쇠 '탁'(1.7 kHz, τ 12 ms — 울림 없음) + 15 ms 뒤 나무 '톡'(1 kHz). 0.12 s. 켬/끔 구분은 시스템이 재생 속도로(켬 1.0 · 끔 0.9 권장)", -8, category='ui')
def _ui_toggle(sr, rng):
    s = zeros(sec(sr, 0.12))
    mix_into(s, iron_tak(sr, rng, 1700), 0, 0.8)
    mix_into(s, wood_tok(sr, rng, 1000, 0.05, 0.007, 0.4), sec(sr, 0.015), 0.5)
    return s


# ===========================================================================
# 2. 전투 흐름 — 적 등장 예고 · 마지막 처치 슬로모 · 사망 슬로모
# ===========================================================================

@sfx16('enemy_incoming', 'ENEMY_INCOMING', "62-2 새 — 적 등장 예고(웨이브마다 1회 — 바닥 먹 번짐 + 불씨 고리 맥박 1.0 s 와 같은 시간 축). 0 s 먹이 바닥에 '툭' 스밈(작게) → 0~1.0 s 젖은 먹 번짐(220→900 Hz 로 열림) + 낮게 차오르는 부풂(55→95 Hz) + 0·0.33·0.66 s 불씨 고리 맥박(타닥 묶음, 점점 커짐) → **1.00 s** 적이 일어섬: 공기 '훅' + 낮은 '둥'(120→55 Hz) + 불씨 확 → 0.35 s 꼬리. 1.40 s. 시작 = 등장 1.0 s 전(delayMs 가 1000 보다 길면 delayMs − 1000 만큼 늦춰 시작 — mixing.cues)", -5, category='combat')
def _enemy_incoming(sr, rng):
    dur = 1.40
    s = zeros(sec(sr, dur))
    mix_into(s, blot(sr, 150, 80), 0, 0.25)
    mix_into(s, ink_bloom(sr, rng, 1.05, 220, 900), 0, 0.55)
    n = sec(sr, 1.0)
    swell = mul(lowpass(tone(sr, 1.0, 55, 95), sr, 200), [(i / n) ** 1.8 for i in range(n)])
    mix_into(s, swell, 0, 0.45)
    for k, t in enumerate((0.0, 0.33, 0.66)):
        mix_into(s, ember(sr, rng, 0.14, 5 + 2 * k, 1.0), sec(sr, t), 0.35 + 0.15 * k)
        mix_into(s, lowpass(punch(sr, 140, 90, 0.08, 0.02, 1.0), sr, 400), sec(sr, t), 0.12 + 0.06 * k)
    # 1.0 s 일어섬
    mix_into(s, burst(sr, 0.12, rng, fc=420, q=0.6, tau=0.03, mode='low'), sec(sr, 1.0), 0.7)
    mix_into(s, lowpass(punch(sr, 120, 55, 0.3, 0.07, 1.2), sr, 300), sec(sr, 1.0), 0.8)
    mix_into(s, ember_flare(sr, rng, 0.18, 900, 3000, 1.0, 6), sec(sr, 0.86), 0.3)
    return reverb(s, sr, size=0.8, decay=0.5, wet=0.16)


@sfx16('last_kill_slow', 'FEEL_SLOWMO{kind:lastKill}', "62-2 새 — 방 마지막 적 처치 슬로모(0.3배 280 ms, 보스 방 제외 · 히트스톱 끔이면 슬로모도 소리도 없음). 0 s 시간이 굳는 깊은 '웅'(110→42 Hz) + 귀가 먹먹해지는 공기(3.5 kHz→350 Hz 로 닫힘) + 낮은 드론 → **0.28 s** 시간이 풀림: 돌아오는 공기 '후욱'(300→2.2 kHz) + 흩어지는 불씨 + 먹 꼬리. 0.95 s. 처치음(enemy_death) 위에 겹친다", -4, category='combat')
def _last_kill_slow(sr, rng):
    dur = 0.93
    s = zeros(sec(sr, dur))
    mix_into(s, sub(sr, 110, 42, 0.55, 0.2, 200), 0, 1.0)
    mix_into(s, air_drop(sr, rng, 0.32, 3500, 350), 0, 0.45)
    dr = mul(lowpass(tone(sr, 0.4, 55, 48, kind='saw'), sr, 160), env_adsr(sr, 0.4, 0.03, 0.0, 1.0, 0.25))
    mix_into(s, dr, 0, 0.25)
    mix_into(s, air_rise(sr, rng, 0.26, 300, 2200), sec(sr, 0.10), 0.8)
    mix_into(s, ember(sr, rng, 0.35, 9, 1.0), sec(sr, 0.30), 0.3)
    mix_into(s, ink_bloom(sr, rng, 0.45, 260, 700), sec(sr, 0.30), 0.25)
    return tail(reverb(s, sr, size=1.0, decay=0.55, wet=0.2), sr, 0.02)


@sfx16('death_slow', 'PLAYER_DIED', "62-2 새 — 주인공 사망 연출(시스템 data/runEnd.json death: 0.25배 슬로모 600 ms → 먹 번짐 1100 ms → 250 ms 멈춤 → 결산, 합 1.95 s · UI 이벤트 ui:death-started 와 같은 순간). 0 s 몸이 꺾이는 둔탁한 '쿵'(120→40 Hz, 500 Hz 위 깎음) + 귀가 닫힘(6 kHz→250 Hz) + 심장 한 번 → 0~1.2 s 아래로 꺼지는 저음(90→35 Hz) → 0.45 s 더 느리고 작은 심장 → **0.60 s** 먹 방울 '툭'(번짐 시작) + 젖은 먹이 종이에 스며 퍼짐(180~700 Hz, 0.60~1.70 s — 화면 먹 번짐 1100 ms 와 같은 길이) + 종이 젖는 결 → 1.50 s 마지막 불씨 '치익' → 1.62 s 먹이 자리 잡는 낮은 '툭'. 2.00 s(결산 화면이 뜰 때 끝남). player_death(RUN_ENDED)를 대신 — 둘 다 울리지 않음", 0, category='event')
def _death_slow(sr, rng):
    dur = 1.98
    s = zeros(sec(sr, dur))
    mix_into(s, lowpass(punch(sr, 120, 40, 0.5, 0.12, 1.3), sr, 500), 0, 1.0)
    mix_into(s, burst(sr, 0.12, rng, fc=500, q=0.6, tau=0.035, mode='low'), 0, 0.5)
    mix_into(s, air_drop(sr, rng, 0.62, 6000, 250), 0, 0.4)
    mix_into(s, heartbeat(sr, rng, 0.8), sec(sr, 0.04))
    fall = mul(lowpass(tone(sr, 1.2, 90, 35), sr, 300), env_adsr(sr, 1.2, 0.05, 0.0, 1.0, 0.9))
    mix_into(s, fall, 0, 0.45)
    mix_into(s, lowpass(heartbeat(sr, rng, 0.45), sr, 150), sec(sr, 0.45))
    mix_into(s, blot(sr, 150, 70), sec(sr, 0.60), 0.5)
    mix_into(s, ink_bloom(sr, rng, 1.1, 180, 700), sec(sr, 0.60), 0.85)
    mix_into(s, paper(sr, rng, 0.85, 14, (1200, 3200), 0.5, bed=0.4), sec(sr, 0.68), 0.35)
    mix_into(s, snuff(sr, rng, 0.28, 3600, 1100), sec(sr, 1.50), 0.18)
    mix_into(s, blot(sr, 120, 55), sec(sr, 1.62), 0.35)
    return tail(reverb(s, sr, size=1.4, decay=0.7, wet=0.3), sr, 0.02)


# ===========================================================================
# 3. 노드 시련 (68초 무피격 등) — 성공 · 실패 순간
# ===========================================================================

@sfx16('trial_win', 'NODE_GRADED{grade:perfect}', "62-2 새 — 노드 시련 성공(1층은 등급이 '완' 하나 — 제한 시간 안·무피격으로 노드를 끝냄, 일기장 쪽지에 完 도장 + 보상 아이콘 반짝). grade_perfect 를 1층 결로 대신(둘 다 울리지 않음). 0 s 먹 도장 '꾹'(170→80 Hz, 딱 소리 없음) + 붓 끝 '착' + 잿불 반짝 일어남 → 40 ms 작은 종 A5 → 0.14 s E6(맑게, 짧게) + 0.11 s 전표 '착'(전표 +20) + 불씨 몇 점. 0.80 s. 권장 음량 -2 dB(grade_perfect -2 와 같은 자리)", -2)
def _trial_win(sr, rng):
    dur = 0.78
    s = zeros(sec(sr, dur))
    k = lowpass(punch(sr, 170, 80, 0.2, 0.045, 1.3), sr, 800)
    mix_into(s, mul(k, env_adsr(sr, 0.2, 0.003, 0.0, 1.0, 0.14)), 0, 0.8)
    mix_into(s, paper(sr, rng, 0.05, 140, (2000, 5000), 1.0, bed=0.0), 0, 0.25)
    mix_into(s, brush(sr, rng, 0.06, 2200, 4200, bristle=0.5, a=0.15, r=0.7), sec(sr, 0.01), 0.35)
    mix_into(s, ember_flare(sr, rng, 0.16, 900, 3600, 1.0, 6), sec(sr, 0.01), 0.3)
    mix_into(s, chime(sr, rng, 880.0, 0.45, 0.12), sec(sr, 0.04), 0.75)
    mix_into(s, chime(sr, rng, 1318.5, 0.5, 0.16), sec(sr, 0.14), 0.6)
    mix_into(s, burst(sr, 0.012, rng, fc=4500, q=1.2, tau=0.002), sec(sr, 0.11), 0.35)
    mix_into(s, burst(sr, 0.012, rng, fc=2400, q=1.2, tau=0.0025), sec(sr, 0.114), 0.3)
    mix_into(s, ember(sr, rng, 0.3, 5, 1.0), sec(sr, 0.2), 0.2)
    return tail(reverb(s, sr, size=0.7, decay=0.45, wet=0.16), sr, 0.02)


@sfx16('trial_fail', 'NODE_TRIAL_BROKEN', "62-2 새 — 노드 시련이 깨진 순간(NODE_TRIAL_BROKEN{nodeId,reason:hit|time} — 첫 피격 또는 제한 시간 넘김, 보상 아이콘이 꺼짐). 0 s 먹이 '철퍽' 튐(900 Hz 아래 젖은 터짐 + 방울 몇) + 불씨 꺼짐 '치익'(4.2→1.3 kHz) → 80 ms 둔탁한 나무 '툭'(160→80 Hz) → 0.10 s 낮은 두 음 A3·B♭3 짧게 겹침(아쉬움, 0.3 s). 0.65 s. 맞는 순간이면 hit_player 와 함께 울리므로 작고 낮게", -5)
def _trial_fail(sr, rng):
    dur = 0.63
    s = zeros(sec(sr, dur))
    mix_into(s, lowpass(burst(sr, 0.1, rng, fc=600, q=0.6, tau=0.03, mode='low'), sr, 900), 0, 0.7)
    mix_into(s, lowpass(droplets(sr, rng, 0.2, 4, 0.01, 0.12, 400, 900, 0.5), sr, 1500), 0, 0.5)
    mix_into(s, snuff(sr, rng, 0.26, 4200, 1300), sec(sr, 0.005), 0.35)
    mix_into(s, lowpass(punch(sr, 160, 80, 0.14, 0.03, 1.2), sr, 600), sec(sr, 0.08), 0.6)
    for f, g in ((220.0, 0.5), (233.08, 0.4)):
        mix_into(s, chime(sr, rng, f, 0.42, 0.14, 1.0, 2500), sec(sr, 0.10), g)
    return tail(reverb(s, sr, size=0.7, decay=0.45, wet=0.15), sr, 0.02)


# ===========================================================================
# 4. 1층 끝 결산 · 메타 '기억' 해금 · 유품
# ===========================================================================

@sfx16('floor_end_sting', 'ui:floor-end', "62-2 새 — 1층 끝 결산 일기장이 열림(UI 이벤트 ui:floor-end — 군주의 유품·개성 발현 뒤 FLOOR_END_DELAY 1.2 s, 곧바로 결과 씬). 0 s 무거운 일기장 '툭'(110→50 Hz) + 쪽 넘김 → 0.12 s 손풍금 A 단조(A2·E3·A3·C4) 바람통처럼 부풂 + 0.15 s 종 E5 → 1.15 s 붓 한 획 + 화음이 F 장7(F2·C3·A3·E4)로 열림 + 1.20 s 종 A5 — 끝나지 않고 열린 채로('다음 장은 아직 그려지지 않았다') → 2.6 s 까지 잦아듦, 내내 잿불 타닥 아주 작게. 2.70 s", -2)
def _floor_end_sting(sr, rng):
    dur = 2.68
    s = zeros(sec(sr, dur))
    mix_into(s, lowpass(punch(sr, 110, 50, 0.4, 0.1, 1.2), sr, 400), 0, 0.8)
    mix_into(s, burst(sr, 0.08, rng, fc=700, q=0.6, tau=0.02, mode='low'), 0, 0.4)
    mix_into(s, paper(sr, rng, 0.32, 50, (2000, 5000), 1.0, bed=0.35), sec(sr, 0.02), 0.35)
    for f, g in ((110.0, 0.55), (164.81, 0.45), (220.0, 0.4), (261.63, 0.35)):
        mix_into(s, bellows(sr, 1.25, f, 0.28, 0.35, 1000), sec(sr, 0.12), g)
    for f, g in ((87.31, 0.5), (130.81, 0.45), (220.0, 0.38), (329.63, 0.32)):
        mix_into(s, bellows(sr, 1.45, f, 0.3, 1.0, 1000), sec(sr, 1.15), g)
    mix_into(s, chime(sr, rng, 659.26, 0.9, 0.3, 1.0, 5000), sec(sr, 0.15), 0.35)
    mix_into(s, chime(sr, rng, 880.0, 1.2, 0.4, 1.0, 5000), sec(sr, 1.20), 0.3)
    mix_into(s, brush(sr, rng, 0.32, 900, 2600, bristle=0.55, a=0.25, r=0.55), sec(sr, 1.12), 0.35)
    mix_into(s, ember(sr, rng, 2.4, 16, 1.0, 3600), sec(sr, 0.1), 0.12)
    return tail(reverb(s, sr, size=1.3, decay=0.7, wet=0.28), sr, 0.02)


@sfx16('memory_unlock', 'MEMORY_UNLOCKED', "62-2 새 — 일기장 '기억' 장에서 영혼으로 해금(memory.unlock 이 true 일 때 한 번 — 소품을 고르는 것은 ui_select. 소품·무기 양상·개성 풀·상점 품목·능력치 공통). 0·0.14·0.30 s 붓으로 글씨 세 획(점점 높게) → 0.35 s 먹이 번지며 그림이 떠오름(먹 번짐 0.85 s + 0.45 s 먹 '툭') → 0.45·0.58·0.72 s 작은 종 A4·C5·E5(A 단조 화음, 부드럽게) + 따뜻한 잿불이 일어나 잦아듦. 1.40 s", -4)
def _memory_unlock(sr, rng):
    dur = 1.38
    s = zeros(sec(sr, dur))
    for t, d, f0, f1, g in ((0.0, 0.13, 900, 2200, 1.0), (0.14, 0.12, 1100, 2600, 0.9), (0.30, 0.16, 1300, 3000, 1.0)):
        mix_into(s, brush(sr, rng, d, f0, f1, bristle=0.55, a=0.2, r=0.6), sec(sr, t), g)
    mix_into(s, ink_bloom(sr, rng, 0.85, 260, 900), sec(sr, 0.35), 0.5)
    mix_into(s, blot(sr, 160, 80), sec(sr, 0.45), 0.35)
    for t, f in ((0.45, 440.0), (0.58, 523.25), (0.72, 659.26)):
        mix_into(s, chime(sr, rng, f, 0.65, 0.25, 1.0, 5000), sec(sr, t), 0.5)
    mix_into(s, ember_flare(sr, rng, 0.35, 500, 2400, 1.0, 8), sec(sr, 0.42), 0.22)
    mix_into(s, ember(sr, rng, 0.6, 7, 1.0, 3600), sec(sr, 0.7), 0.15)
    return tail(reverb(s, sr, size=1.1, decay=0.6, wet=0.25), sr, 0.02)


@sfx16('relic_take', 'ui:relic-gained', "62-2 새 — 유품 카드를 고름·손에 넣음(UI 이벤트 ui:relic-gained — 보스·엘리트 '유품', '군주의 유품' 3택, 지닌 것 단계 올림 공통). 0 s 잿불 속에서 확 일어남(800 Hz→3.5 kHz '화르' + 타닥) → 0.22 s 쇠붙이를 쥐는 '철컥'(울림 없음, 620·1.4 kHz 짧게) + 손에 쥐는 둔탁한 몸통 → 0.30 s 낮은 종 A3·E4(둥글게) + 먹 도장 '꾹' → 1.0 s 까지 잿불 꼬리. 1.10 s. trait_manifest(개성)와 결은 같고 더 무겁다", -3)
def _relic_take(sr, rng):
    dur = 1.08
    s = zeros(sec(sr, dur))
    mix_into(s, ember_flare(sr, rng, 0.26, 800, 3500, 1.0, 12), 0, 0.55)
    mix_into(s, iron_tak(sr, rng, 620), sec(sr, 0.22), 0.6)
    mix_into(s, iron_tak(sr, rng, 1400), sec(sr, 0.235), 0.35)
    mix_into(s, lowpass(punch(sr, 150, 70, 0.2, 0.05, 1.2), sr, 500), sec(sr, 0.22), 0.6)
    mix_into(s, chime(sr, rng, 220.0, 0.8, 0.35, 1.0, 3000), sec(sr, 0.30), 0.45)
    mix_into(s, chime(sr, rng, 329.63, 0.75, 0.3, 1.0, 3500), sec(sr, 0.30), 0.35)
    mix_into(s, lowpass(punch(sr, 190, 85, 0.14, 0.03, 1.2), sr, 700), sec(sr, 0.31), 0.35)
    mix_into(s, ember(sr, rng, 0.7, 8, 1.0, 3600), sec(sr, 0.32), 0.18)
    return tail(reverb(s, sr, size=0.9, decay=0.55, wet=0.2), sr, 0.02)


# ===========================================================================
# 5. 상점 · NPC (E 로 사기 · 말 걸어 다시 진열)
# ===========================================================================

@redo('shop_buy', "62-2 다시(P16 §5 — 노점 칸에서 E 로 사기). 0 s 전표를 건네는 종이 '착' 두 겹(4.5·2.4 kHz) → 60 ms 나무 좌판 '톡'(620 Hz) + 둥근 몸통(200→110 Hz) → 0.14 s 물건을 집어 드는 천 스침 → 0.22 s 작은 쇠 '탁'(장신구·병마개 — 울림 없음). 0.50 s. 옛 '동전' 대신 1층 화폐 전표(군표) 결. 권장 음량 -4 → -2 dB", gain_db=-2.0, round_=ROUND)
def _shop_buy62(sr, rng):
    s = zeros(sec(sr, 0.5))
    mix_into(s, burst(sr, 0.014, rng, fc=4500, q=1.2, tau=0.0025), 0, 1.0)
    mix_into(s, burst(sr, 0.014, rng, fc=2400, q=1.2, tau=0.003), sec(sr, 0.006), 0.9)
    mix_into(s, paper(sr, rng, 0.05, 160, (2400, 5200), 1.0, bed=0.0), sec(sr, 0.01), 0.45)
    mix_into(s, wood_tok(sr, rng, 620, 0.06, 0.01, 0.5), sec(sr, 0.06), 0.8)
    mix_into(s, lowpass(punch(sr, 200, 110, 0.12, 0.025, 1.2), sr, 600), sec(sr, 0.06), 0.6)
    mix_into(s, rustle(sr, rng, 0.16, 1500, 40.0), sec(sr, 0.14), 0.35)
    mix_into(s, iron_tak(sr, rng, 2100), sec(sr, 0.22), 0.3)
    return tail(reverb(s, sr, size=0.6, decay=0.4, wet=0.12), sr, 0.02)


@redo('shop_reroll', "62-2 다시(P16 §5 — 상인에게 말 걸어 '다시 진열'). 0 s 좌판 천을 걷는 '휙'(500 Hz→2 kHz) + 천 펄럭 → 0.25·0.33·0.43 s 물건을 다시 놓는 나무 '톡' 셋(700·900·800 Hz) → 0.55 s 천이 내려앉는 둥근 '툭'. 0.70 s. 동전 없음(전표 결은 shop_buy). 권장 음량 -4 → -2 dB", gain_db=-2.0, round_=ROUND)
def _shop_reroll62(sr, rng):
    s = zeros(sec(sr, 0.7))
    mix_into(s, whoosh(sr, 0.2, rng, 500, 2000, q=1.0, a=0.35, r=0.5), 0, 0.55)
    flap = mul(rustle(sr, rng, 0.26, 1300, 55.0), [0.55 + 0.45 * abs(math.sin(math.pi * 18 * i / sr)) for i in range(sec(sr, 0.26))])
    mix_into(s, flap, sec(sr, 0.05), 0.5)
    for t, f in ((0.25, 700), (0.33, 900), (0.43, 800)):
        mix_into(s, wood_tok(sr, rng, f, 0.05, 0.008, 0.5), sec(sr, t), 0.55)
        mix_into(s, lowpass(punch(sr, f * 0.3, f * 0.18, 0.05, 0.012, 1.0), sr, 500), sec(sr, t), 0.25)
    mix_into(s, lowpass(punch(sr, 150, 90, 0.12, 0.03, 1.0), sr, 400), sec(sr, 0.55), 0.4)
    mix_into(s, burst(sr, 0.06, rng, fc=900, q=0.6, tau=0.015, mode='low'), sec(sr, 0.55), 0.25)
    return tail(reverb(s, sr, size=0.6, decay=0.4, wet=0.12), sr, 0.02)


@sfx16('npc_talk', 'EVENT_TALK', "62-2 새 — NPC 에게 E 로 말 걸기(이벤트 방 인물 EVENT_TALK · 상인 SHOP_TALK 같은 소리, 대화 상자가 열림). 0 s 옷깃 스침(1.4 kHz) + 70 ms 나무 마루 작은 '삐걱'(짧게) → 0.20 s 일기장 쪽 넘김(대화가 열림) + 촛불 불씨 한두 점. 0.60 s. 목소리 없음 — 말은 글로만", -4, category='world')
def _npc_talk(sr, rng):
    dur = 0.58
    s = zeros(sec(sr, dur))
    mix_into(s, rustle(sr, rng, 0.18, 1400, 35.0), 0, 0.5)
    n = sec(sr, 0.14)
    cr = svf(tone(sr, 0.14, 95, 120, kind='saw'), sr, sweep(sr, n, 600, 1100), 3.0, 'band')
    mix_into(s, mul(cr, env_adsr(sr, 0.14, 0.03, 0.0, 1.0, 0.08)), sec(sr, 0.07), 0.25)
    mix_into(s, lowpass(punch(sr, 140, 90, 0.08, 0.02, 1.0), sr, 400), sec(sr, 0.07), 0.25)
    pg = svf(noise(sr, 0.16, rng), sr, sweep(sr, sec(sr, 0.16), 2800, 1200), 0.9, 'band')
    mix_into(s, mul(pg, env_adsr(sr, 0.16, 0.03, 0.0, 1.0, 0.1)), sec(sr, 0.20), 0.45)
    mix_into(s, paper(sr, rng, 0.14, 60, (2200, 5000), 1.0, bed=0.25), sec(sr, 0.22), 0.25)
    mix_into(s, lowpass(punch(sr, 170, 110, 0.05, 0.012, 1.0), sr, 500), sec(sr, 0.34), 0.25)
    mix_into(s, ember(sr, rng, 0.2, 2, 1.0, 3600), sec(sr, 0.3), 0.12)
    return tail(reverb(s, sr, size=0.7, decay=0.45, wet=0.15), sr, 0.02)


# ===========================================================================
# 6. 대체된 옛 소리 표시 (오디오 그대로)
# ===========================================================================

fallback('menu_move', '메뉴 공통 이동은 ui_move 가 대신. 이 소리는 ui_move 가 없을 때와 기존 임시 연결(룰렛 등)용')
fallback('menu_select', '메뉴 공통 선택은 ui_select 가 대신. ui_select 가 없을 때만')
fallback('menu_cancel', '메뉴 공통 뒤로는 ui_back 이 대신. 기존 임시 연결(시간 초과 등)은 그대로')
fallback('player_death', '사망은 death_slow(PLAYER_DIED)가 대신 — 둘 다 울리지 않음. death_slow 가 없을 때만')
fallback('grade_perfect', "1층 노드 시련 성공(完)은 trial_win 이 대신 — 둘 다 울리지 않음. trial_win 이 없을 때와 2층 이후 '완'")


# ===========================================================================
# 7. 외벽 문 (62 루프 2 시스템 E — 노드 출구 발판이 없어지고 외벽 문으로 걸어 나감)
#    시스템 이벤트 core/eventsLoop2E: DOOR_OPENED 'door:opened'{side,kind:node|floor|training} ·
#    DOOR_WALK 'door:walk'{phase:out|in|back,side,ms}. 시각: 널문이 바깥으로 밀려 걷힘 0.52 s, 문 빛 0.7 s 에 차오름,
#    나가기 = 문 안으로 2.5칸 자동 걸음(끝 2칸에서 몸이 흐려짐) · 들어오기 ≈ 0.6~0.7 s · 지도 취소 = 문턱 안 1.8칸.
# ===========================================================================

def _boot(sr, rng, g=1.0, sill=False):
    """주인공 발 한 걸음(장화 · 돌바닥): 둥근 몸통(115→70 Hz, 600 Hz 위 깎음) + 흙 긁힘 + 돌 부스러기 한두 점.
    sill=True 면 나무 문턱 — 속 빈 나무 '톡'(420 Hz)이 겹친다."""
    s = zeros(sec(sr, 0.16))
    mix_into(s, lowpass(punch(sr, 115, 70, 0.1, 0.022, 1.1), sr, 600), 0, 0.9)
    mix_into(s, lowpass(burst(sr, 0.05, rng, fc=1300, q=0.6, tau=0.012), sr, 3000), 0.0, 0.35)
    mix_into(s, gravel(sr, rng, 0.1, 2, 0.005, 0.05, 0.12), 0)
    if sill:
        mix_into(s, wood_tok(sr, rng, 420, 0.07, 0.014, 0.35), sec(sr, 0.004), 0.5)
    return scale(s, g)


def _passage(sr, rng, dur, f0, f1, g=1.0):
    """문 안 통로의 울림: 낮은 대역 노이즈(f0→f1)가 통처럼 웅 — 바깥 바람이 문 안에서 맴돎."""
    n = sec(sr, dur)
    s = svf(noise(sr, dur, rng), sr, sweep(sr, n, f0, f1), 2.2, 'band')
    return scale(lowpass(s, sr, 500), g)


@redo('door_open', "62-2E 다시(시스템 E — 노드 출구 발판 대신 외벽 문). 방을 비우면 진행 방향 외벽의 닫힌 널문이 바깥으로 밀려 걷히고(0.52 s) 문 빛(호박 등불)이 0.7 s 에 차오름. 0 s 나무 빗장 '덜컥' + 쇠 걸쇠 '탁'(울림 없음) → 0.06~0.52 s 널문이 밀리며 삐걱(낮게) + 판자가 돌 문틀을 긁음 + 열린 틈으로 들어오는 바람 → **0.52 s** 판자가 바깥에 내려앉는 둔탁한 '툭·톡'(멀리) → 0.15~0.80 s 문 등불이 잿불처럼 일어나 따뜻한 낮은 부풂 + 0.68 s 낮은 종 A3(작게, '오르는 길') → 1.25 s 까지 불씨 꼬리. 1.28 s. 노드·층·수련장 방 출구 공통(kind 무관). exit_open(STORY exitOpened '오르는 길 열림')을 대신 — 같은 순간 둘 다 울리지 않음. 방+복도 층(외벽 문 없는 옛 발판 층)의 방 클리어 문 열림(ROOM_CLEARED)도 이 소리를 쓰되 door:opened 와 같은 순간이면 한 번만. 권장 음량 -3 → 0 dB(대신하는 exit_open 자리 — 100 ms 최대 RMS -20 dBFS, 발소리 -23 위)", gain_db=0.0, trigger='door:opened', round_=ROUND)
def _door_open62e(sr, rng):
    dur = 1.25
    s = zeros(sec(sr, dur))
    # 0 s 빗장
    mix_into(s, lowpass(punch(sr, 150, 85, 0.1, 0.025, 1.2), sr, 600), 0, 0.7)
    mix_into(s, wood_tok(sr, rng, 520, 0.06, 0.01, 0.6), 0, 0.55)
    mix_into(s, iron_tak(sr, rng, 1500), sec(sr, 0.03), 0.45)
    # 0.06~0.52 s 널문 밀림
    mix_into(s, creak(sr, rng, 0.46, 72, 100, (380, 900), 15.0, 2.6), sec(sr, 0.06), 0.42)
    n = sec(sr, 0.44)
    scr = lowpass(svf(noise(sr, 0.44, rng), sr, sweep(sr, n, 900, 450), 1.1, 'band'), sr, 1600)
    mix_into(s, mul(scr, env_adsr(sr, 0.44, 0.12, 0.0, 1.0, 0.18)), sec(sr, 0.08), 0.25)
    mix_into(s, whoosh(sr, 0.5, rng, 240, 620, q=0.7, a=0.45, r=0.45), sec(sr, 0.12), 0.28)
    # 0.52 s 판자가 바깥에 내려앉음(멀리 — 낮게 깎음)
    mix_into(s, lowpass(punch(sr, 120, 60, 0.14, 0.035, 1.1), sr, 400), sec(sr, 0.52), 0.5)
    mix_into(s, lowpass(wood_tok(sr, rng, 380, 0.06, 0.012, 0.4), sr, 1200), sec(sr, 0.60), 0.3)
    # 0.15~0.80 s 문 빛
    mix_into(s, ember_flare(sr, rng, 0.6, 450, 2200, 1.0, 8), sec(sr, 0.15), 0.26)
    warm = mul(lowpass(tone(sr, 0.9, 110, kind='tri'), sr, 300), env_adsr(sr, 0.9, 0.5, 0.0, 1.0, 0.35, curve=1.5))
    mix_into(s, warm, sec(sr, 0.15), 0.18)
    mix_into(s, chime(sr, rng, 220.0, 0.55, 0.22, 1.0, 3000), sec(sr, 0.68), 0.22)
    mix_into(s, ember(sr, rng, 0.45, 5, 1.0, 3600), sec(sr, 0.78), 0.12)
    return tail(reverb(s, sr, size=0.8, decay=0.5, wet=0.17), sr, 0.03)


@sfx16('door_walk_out', 'door:walk{phase:out}', "62-2E 새 — 열린 외벽 문 안으로 걸어 들어감(나가기 — 문턱에 들어서면 조작이 잠기고 2.5칸 자동 걸음, 끝 2칸에서 몸이 흐려짐 → 그림 속 입구 전환). 0 s 돌바닥 발소리 → 0.24 s 나무 문턱 '톡' 섞인 발소리 → 0.48 s 문 안 발소리(작고 어둡게, 울림 큼) — 걸음마다 소리가 멀어지고 낮아지며 문 안 통로 울림(낮은 '웅')이 커졌다가 0.60~1.00 s 어둠에 잠겨 사라짐. 1.05 s. 걸음 간격 0.24 s 는 2.5칸 ≈ 0.7 s 기준(ms 가 크게 다르면 재생 속도 700/ms, 0.85~1.15 로 묶음 권장). 이어지는 transition_exit/enter 앞에 놓임", -6, category='world')
def _door_walk_out(sr, rng):
    dur = 1.02
    near = zeros(sec(sr, dur))
    far = zeros(sec(sr, dur))
    mix_into(near, _boot(sr, rng, 1.0), 0, 0.85)
    mix_into(near, lowpass(_boot(sr, rng, 1.0, sill=True), sr, 2200), sec(sr, 0.24), 0.6)
    mix_into(far, lowpass(_boot(sr, rng, 1.0), sr, 900), sec(sr, 0.48), 0.45)
    mix_into(far, lowpass(_boot(sr, rng, 1.0), sr, 500), sec(sr, 0.72), 0.18)   # 어둠 속 마지막 걸음(거의 안 들림)
    ps = _passage(sr, rng, 0.95, 160, 90)
    mix_into(far, mul(ps, env_adsr(sr, 0.95, 0.4, 0.0, 1.0, 0.5, curve=1.3)), sec(sr, 0.08), 0.22)
    mix_into(far, mul(lowpass(tone(sr, 0.8, 62, 52), sr, 150), env_adsr(sr, 0.8, 0.3, 0.0, 1.0, 0.45)), sec(sr, 0.2), 0.18)
    s = add(reverb(near, sr, size=0.6, decay=0.4, wet=0.12), reverb(far, sr, size=1.2, decay=0.65, wet=0.45, predelay=0.012))
    return tail(s, sr, 0.03)


@sfx16('door_walk_in', 'door:walk{phase:in}', "62-2E 새 — 반대편 외벽 문 안에서 걸어 나와 새 노드에 들어섬(≈0.6~0.7 s, 그동안 조작·전투 잠금 — 들어오면 입구 문이 닫힌다). door_walk_out 을 거꾸로: 0 s 문 안 통로 울림이 이미 맴돌고 문 안 발소리(작고 어둡게) → 0.22 s 나무 문턱 발소리 → 0.44 s 돌바닥 발소리(가깝고 또렷하게, 울림 거의 없음) → 0.60 s 마지막 디딤 + 옷깃 스침(조작이 풀리는 순간). 0.85 s. 걸음 간격 0.22 s(ms 가 크게 다르면 재생 속도 650/ms, 0.85~1.15)", -6, category='world')
def _door_walk_in(sr, rng):
    return _walk_in(sr, rng, ((0.0, 'far', 0.4), (0.22, 'sill', 0.6), (0.44, 'near', 0.85), (0.60, 'near', 0.6)), 0.82)


def _walk_in(sr, rng, steps, dur):
    near = zeros(sec(sr, dur))
    far = zeros(sec(sr, dur))
    for t, kind, g in steps:
        if kind == 'far':
            mix_into(far, lowpass(_boot(sr, rng, 1.0), sr, 900), sec(sr, t), g)
        elif kind == 'sill':
            mix_into(near, lowpass(_boot(sr, rng, 1.0, sill=True), sr, 2200), sec(sr, t), g)
        else:
            mix_into(near, _boot(sr, rng, 1.0), sec(sr, t), g)
    ps = _passage(sr, rng, 0.5, 90, 160)
    mix_into(far, mul(ps, env_adsr(sr, 0.5, 0.06, 0.0, 1.0, 0.4, curve=0.8)), 0, 0.3)
    t_last = steps[-1][0]
    mix_into(near, rustle(sr, rng, 0.12, 1300, 40.0), sec(sr, t_last + 0.01), 0.22)
    s = add(reverb(near, sr, size=0.6, decay=0.4, wet=0.1), reverb(far, sr, size=1.2, decay=0.6, wet=0.4, predelay=0.012))
    return tail(s, sr, 0.03)


@sfx16('door_walk_back', 'door:walk{phase:back}', "62-2E 새 — 지도 고르기 취소: 문 안에서 문턱 안쪽 1.8칸으로 걸어 나옴(문은 열린 채 — 닫히지 않음). door_walk_in 과 같은 재료로 더 짧게 — 0 s 문 안 발소리(어둡게) → 0.22 s 나무 문턱 → 0.40 s 돌바닥 디딤 + 옷깃 스침. 0.65 s. 없으면 door_walk_in 으로 대신해도 된다", -7, category='world')
def _door_walk_back(sr, rng):
    return _walk_in(sr, rng, ((0.0, 'far', 0.4), (0.22, 'sill', 0.55), (0.40, 'near', 0.7)), 0.62)


fallback('exit_open', "노드 지도 층 · 수련장의 출구 열림은 door_open(door:opened)이 대신 — 같은 순간 둘 다 울리지 않음. "
                      "이 소리는 방+복도 층의 옛 발판 출구(STORY exitOpened)용으로 남김")


# ===========================================================================
# 8. 짧은 먹 번짐 암전 (62 시스템 H — 계약 ui-system-interface §25)
#    노드 이동 = 지도에서 고르기 → TRANSITION_BEGIN{mode:'fade', durationMs≈400} → UI 먹 번짐 덮기(≈0.4 s)
#    → COVERED → 재시작 → READY → 0.3 s 걷기 → END → 반대편 문 입장(door_walk_in). 노드 이동마다 울리므로 작고 부드럽게.
# ===========================================================================

def _ink_hush(sr, rng, dur, f0, f1, cover, cut=0.07):
    """먹이 번지는 '쉭': 저역통과 노이즈의 차단 주파수가 f0 → f1 로 천천히 열리며 cover 초까지 부풀고, cut 초에 걸쳐 닫힘(덮임).
    어택 없음 — 곡선(지수 1.7)으로 차오른다."""
    n = sec(sr, dur)
    s = svf(noise(sr, dur, rng), sr, sweep(sr, n, f0, f1), 0.75, 'low')
    k = sec(sr, cover)
    nc = max(1, sec(sr, cut))
    env = [((i / k) ** 1.7) if i < k else max(0.0, 1.0 - (i - k) / nc) ** 1.4 for i in range(n)]
    return mul(s, env)


@sfx16('transition_fade', 'TRANSITION_BEGIN{mode:fade}', "62 시스템 H 새 — 노드 이동 짧은 먹 번짐 암전(지도에서 노드를 고른 뒤 · 수련장 방 고르기·방 → 지도 마당 공통 — §25). 0 s 먹이 종이에 번지는 부드러운 '쉭'(저역통과 노이즈, 260 Hz→1.5 kHz 로 천천히 열림 — 어택 없음) + 젖은 먹 번짐 + 마른 종이 결 몇 알갱이(1.8~4 kHz, 아주 작게) → **0.38 s** 화면이 다 덮임: 쉭이 70 ms 에 닫히며 먹이 자리 잡는 아주 작은 '툭'(140→80 Hz, 500 Hz 위 깎음) → 0.42~0.64 s 걷힐 때 아주 작은 숨 '후'(450→1.1 kHz, 들숨처럼 올랐다 빠짐). 0.68 s. 4.5 kHz 위·딱 소리 없음 — 노드마다 들어도 지치지 않게 작게(권장 -10 dB — 100 ms 최대 RMS ≈ -27 dBFS, door_walk_in -23 보다 4 dB 아래). transition_exit ×0.5·속도 1.2 대체를 대신", -10, category='world')
def _transition_fade(sr, rng):
    dur = 0.66
    cover = 0.38
    s = zeros(sec(sr, dur))
    # 0~0.38 s 먹이 번지는 쉭 + 젖은 먹 번짐(아래 바닥) + 종이 결
    mix_into(s, _ink_hush(sr, rng, 0.46, 260, 1500, cover), 0, 0.8)
    mix_into(s, ink_bloom(sr, rng, 0.52, 200, 700), 0, 0.35)
    mix_into(s, lowpass(paper(sr, rng, 0.34, 18, (1800, 4000), 1.0, bed=0.15), sr, 4500), sec(sr, 0.04), 0.22)
    # 0.38 s 덮임 — 먹이 자리 잡는 아주 작은 '툭'
    mix_into(s, lowpass(blot(sr, 140, 80), sr, 500), sec(sr, cover - 0.005), 0.22)
    # 0.42~0.64 s 걷힐 때 아주 작은 숨
    n = sec(sr, 0.22)
    br = svf(noise(sr, 0.22, rng), sr, sweep(sr, n, 450, 1100), 0.9, 'band')
    mix_into(s, mul(br, env_adsr(sr, 0.22, 0.09, 0.0, 1.0, 0.12, curve=1.3)), sec(sr, 0.42), 0.16)
    return tail(lowpass(reverb(s, sr, size=0.7, decay=0.4, wet=0.14), sr, 4500), sr, 0.02)


SFX['transition_fade']['round'] = '62-3'   # 62라운드 루프 3(P17 묶음 B) — 이 파일 끝에 이어 붙임(시드 순서 유지)
