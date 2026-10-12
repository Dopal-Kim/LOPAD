import { describe, expect, it } from 'vitest';
import { HeldKeyFilter, MenuGuard, withoutMenuGuard } from './menuGuard';

describe('62 루프 2 E 메뉴 입력 가드', () => {
  const clockAt = () => {
    let t = 1000;
    return { now: () => t, set: (v: number) => (t = v) };
  };

  it('열린 뒤 armMs 동안 선택을 받지 않는다', () => {
    const c = clockAt();
    const g = new MenuGuard(400, true, c.now);
    expect(g.accepts()).toBe(true); // 열린 적 없음
    g.arm();
    c.set(1100);
    expect(g.accepts()).toBe(false);
    c.set(1399);
    expect(g.accepts()).toBe(false);
    c.set(1400);
    expect(g.accepts()).toBe(true);
    expect(g.blocked).toBe(2);
  });

  it('UI 가 늦게 그리면(menuShown) 그때부터 다시 armMs', () => {
    const c = clockAt();
    const g = new MenuGuard(400, true, c.now);
    g.arm();
    c.set(2200); // 성과 카드 뒤 1.2초 늦게 그림
    g.shown();
    c.set(2500);
    expect(g.accepts()).toBe(false);
    c.set(2600);
    expect(g.accepts()).toBe(true);
    // 다시 열면 shown 은 지워진다
    g.arm();
    c.set(3000);
    expect(g.readyAt).toBe(3000);
  });

  it('꺼짐(?menuguard=0)·디버그 경로는 바로 받는다', () => {
    const c = clockAt();
    const off = new MenuGuard(400, false, c.now);
    off.arm();
    expect(off.accepts()).toBe(true);
    const on = new MenuGuard(400, true, c.now);
    on.arm();
    expect(withoutMenuGuard(() => on.accepts())).toBe(true);
    expect(on.accepts()).toBe(false);
  });

  it('열릴 때 누르고 있던 키는 뗐다 다시 눌러야 · 자동 반복은 무시', () => {
    const f = new HeldKeyFilter(['Digit1', 'Space']);
    expect(f.acceptDown('Digit1', false)).toBe(false);
    expect(f.acceptDown('Digit2', false)).toBe(true);
    expect(f.acceptDown('Digit2', true)).toBe(false);
    f.up('Digit1');
    expect(f.acceptDown('Digit1', false)).toBe(true);
    expect(f.size).toBe(1);
  });
});
