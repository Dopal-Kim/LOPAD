import { afterEach, describe, expect, it } from 'vitest';
import { FEEL } from '../core/Constants';
import { DEFAULT_FEEL, HitStop, Shake, feelSettings, knockFactor, knockSpeed, setFeel } from './feel';

afterEach(() => setFeel(DEFAULT_FEEL));

describe('feel: 히트스톱', () => {
  it('요청하면 그 시간 동안 활성, 간격 안의 재요청은 무시(연타 중첩 금지)', () => {
    const h = new HitStop();
    expect(h.request(1000, FEEL.HITSTOP.HIT_MS)).toBe(true);
    expect(h.active(1000)).toBe(true);
    expect(h.active(1000 + FEEL.HITSTOP.HIT_MS - 1)).toBe(true);
    expect(h.active(1000 + FEEL.HITSTOP.HIT_MS)).toBe(false);
    // 80ms 안의 두 번째 요청은 무시
    expect(h.request(1000 + FEEL.HITSTOP.MIN_GAP_MS - 1, FEEL.HITSTOP.CRIT_MS)).toBe(false);
    expect(h.count).toBe(1);
    // 간격을 넘기면 다시
    expect(h.request(1000 + FEEL.HITSTOP.MIN_GAP_MS, FEEL.HITSTOP.CRIT_MS)).toBe(true);
    expect(h.remaining(1000 + FEEL.HITSTOP.MIN_GAP_MS)).toBe(FEEL.HITSTOP.CRIT_MS);
  });

  it('배율 0 이면 꺼진다 (접근성)', () => {
    setFeel({ hitstop: 0 });
    const h = new HitStop();
    expect(h.request(0, 40)).toBe(false);
    expect(h.active(1)).toBe(false);
  });
});

describe('feel: 흔들림', () => {
  it('진폭은 선형 감쇠, 여러 개면 가장 큰 것, 오프셋은 정수', () => {
    const s = new Shake(() => 0); // 각도 0 → x 축
    s.add(0, 4, 100);
    expect(s.amplitude(0)).toBe(4);
    expect(s.amplitude(50)).toBe(2);
    s.add(50, 2, 60); // 더 작은 것은 묻힌다
    expect(s.amplitude(50)).toBe(2);
    expect(s.sample(50)).toEqual({ x: 2, y: 0 });
    expect(s.amplitude(100)).toBe(2 * (1 - 50 / 60));
    expect(s.sample(120)).toEqual({ x: 0, y: 0 });
    expect(s.activeCount).toBe(0);
  });

  it('배율 0 이면 흔들리지 않는다', () => {
    setFeel({ shake: 0 });
    const s = new Shake(() => 0);
    s.add(0, 6, 160);
    expect(s.sample(10)).toEqual({ x: 0, y: 0 });
    expect(s.count).toBe(0);
  });
});

describe('feel: 넉백 수식', () => {
  it('선형 감쇠 초속 v0 = 2d/T → 적분하면 거리 d', () => {
    const T = FEEL.KNOCKBACK.MS;
    const v0 = knockSpeed(6, T);
    expect(v0).toBe(120); // 6px / 0.1s × 2
    // 1ms 간격 수치 적분
    let dist = 0;
    for (let t = 0; t < T; t++) dist += (v0 * knockFactor(t + 0.5, T)) / 1000;
    expect(dist).toBeCloseTo(6, 1);
    expect(knockFactor(T, T)).toBe(0);
    expect(knockFactor(T * 2, T)).toBe(0);
  });

  it('배율 적용·0 이면 0', () => {
    setFeel({ knockback: 0.5 });
    expect(knockSpeed(10, 100)).toBe(100);
    setFeel({ knockback: 0 });
    expect(knockSpeed(10, 100)).toBe(0);
  });

  it('setFeel 은 음수·잘못된 값을 무시한다', () => {
    setFeel({ shake: -1, hitstop: 2, numbers: false });
    expect(feelSettings.shake).toBe(1);
    expect(feelSettings.hitstop).toBe(2);
    expect(feelSettings.numbers).toBe(false);
  });

  it('42라운드: 잔상 궤적·화면 섬광 스위치 (기본 켜짐)', () => {
    expect(DEFAULT_FEEL.trail).toBe(true);
    expect(DEFAULT_FEEL.flash).toBe(true);
    setFeel({ trail: false, flash: false });
    expect(feelSettings.trail).toBe(false);
    expect(feelSettings.flash).toBe(false);
  });
});
