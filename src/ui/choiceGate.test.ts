import { describe, expect, it } from 'vitest';
import { CHOICE_GATE, ChoiceGate, MOUSE, armMsOf, doorWalking } from './choiceGate';

const ARM = CHOICE_GATE.armMs + CHOICE_GATE.marginMs;

describe('62 루프 2 UI D 무장 게이트', () => {
  it('계약 armMs 가 있으면 그 값, 없거나 이상하면 기본값', () => {
    expect(armMsOf(500)).toBe(500);
    expect(armMsOf(0)).toBe(0);
    expect(armMsOf(undefined)).toBe(CHOICE_GATE.armMs);
    expect(armMsOf(-1)).toBe(CHOICE_GATE.armMs);
    expect(armMsOf(Number.NaN)).toBe(CHOICE_GATE.armMs);
    expect(armMsOf('400')).toBe(CHOICE_GATE.armMs);
  });

  it('무장 시간 동안은 숫자·Enter 를 받지 않고, 그 뒤 새로 누른 키는 받는다', () => {
    const g = new ChoiceGate(1000);
    expect(g.armed(1000 + ARM - 1)).toBe(false);
    expect(g.keyOk('Digit1', 1100)).toBe(false);
    // 1100 의 입력이 무장 끝을 1100 + quiet 까지 밀었을 수 있다 — 그보다 뒤
    const later = Math.max(1000 + ARM, 1100 + CHOICE_GATE.quietMs);
    expect(g.keyOk('Digit1', later)).toBe(true);
    expect(g.keyOk('Enter', later + 50)).toBe(true);
  });

  it('무장 진행은 0 → 1', () => {
    const g = new ChoiceGate(0);
    expect(g.progress(0)).toBe(0);
    expect(g.progress(ARM / 2)).toBeCloseTo(0.5, 2);
    expect(g.progress(ARM * 2)).toBe(1);
  });

  it('armMs 0 이면 여유만 지나면 바로 받는다', () => {
    const g = new ChoiceGate(0, { armMs: 0 });
    expect(g.keyOk('Enter', CHOICE_GATE.marginMs)).toBe(true);
  });

  it('그리기 전에 눌린 키(렉으로 늦게 처리된 것)는 시각이 지나도 버린다', () => {
    const g = new ChoiceGate(1000);
    expect(g.keyOk('Digit2', 990)).toBe(false);
    // 무장 끝은 밀리지 않는다 (그려지기 전 입력)
    expect(g.armedAt).toBe(1000 + ARM);
  });

  it('자동 반복 키는 늘 버린다', () => {
    const g = new ChoiceGate(0);
    expect(g.keyOk('Enter', 5000, true)).toBe(false);
  });

  it('연타: 무장 중 입력이 계속 오면 무장 끝이 밀리고, 상한을 넘지 않는다', () => {
    const g = new ChoiceGate(0);
    let t = 0;
    for (; t < 600; t += 100) expect(g.keyOk('Space', t)).toBe(false);
    expect(g.armed(t)).toBe(false);
    expect(g.armedAt).toBe(500 + CHOICE_GATE.quietMs);
    // 계속 두드려도 상한에서 무장된다
    for (; t < 3000; t += 100) g.keyOk('Space', t);
    expect(g.armedAt).toBe(CHOICE_GATE.maxArmMs);
  });

  it('열기 전부터 눌려 있던 키는 한 번 뗀 뒤에만 인정 (keyUp)', () => {
    const g = new ChoiceGate(0, { held: { keys: ['Space'], mouse: false } });
    expect(g.keyOk('Space', 2000)).toBe(false);
    g.keyUp('Space');
    expect(g.keyOk('Space', 2100)).toBe(true);
  });

  it('열기 전부터 눌려 있던 키: 열린 뒤 뗀 기록(lastUp)이 있으면 놓아준다', () => {
    const ups: Record<string, number> = {};
    const g = new ChoiceGate(100, {
      held: { keys: ['Digit1'], mouse: false },
      lastUp: (c) => ups[c] ?? -Infinity,
    });
    expect(g.keyOk('Digit1', 2000)).toBe(false);
    ups.Digit1 = 50; // 열기 전에 뗀 기록은 소용없다 (그 뒤 다시 눌러 열 때 눌려 있었다)
    expect(g.keyOk('Digit1', 2001)).toBe(false);
    ups.Digit1 = 2002;
    expect(g.keyOk('Digit1', 2003)).toBe(true);
  });

  it('좌클릭: 무장 뒤 새로 누르고 떼야 고른다', () => {
    const g = new ChoiceGate(0);
    expect(g.pressOk(100)).toBe(false);
    expect(g.releaseOk()).toBe(false);
    const t = g.armedAt + 10;
    expect(g.pressOk(t)).toBe(true);
    expect(g.releaseOk()).toBe(true);
    // 누름 없이 뗀 것은 아니다
    expect(g.releaseOk()).toBe(false);
  });

  it('열기 전부터 누르던 마우스 버튼: 뗄 때까지 클릭으로 치지 않는다', () => {
    const g = new ChoiceGate(0, { held: { keys: [], mouse: true } });
    const t = g.armedAt + 10;
    expect(g.pressOk(t)).toBe(false);
    expect(g.releaseOk()).toBe(false);
    // 뗀 뒤 다시 누르면 된다
    expect(g.pressOk(t + 100)).toBe(true);
    expect(g.releaseOk()).toBe(true);
  });

  it('열기 전부터 누르던 마우스: 다른 곳에서 뗀 기록(lastUp)으로도 풀린다', () => {
    let up = -Infinity;
    const g = new ChoiceGate(0, { held: { keys: [], mouse: true }, lastUp: (c) => (c === MOUSE ? up : -Infinity) });
    const t = g.armedAt + 10;
    expect(g.pressOk(t)).toBe(false);
    up = t + 5;
    expect(g.pressOk(t + 10)).toBe(true);
  });

  it('무장 중 클릭도 연타 막기로 무장 끝을 민다', () => {
    const g = new ChoiceGate(0);
    g.pressOk(300);
    expect(g.armedAt).toBe(300 + CHOICE_GATE.quietMs);
  });
});

describe('62 루프 2 시스템 E 문 걸음', () => {
  it('walkOut·inside·walkIn 동안만 조작 안내를 숨긴다', () => {
    expect(doorWalking('walkOut')).toBe(true);
    expect(doorWalking('inside')).toBe(true);
    expect(doorWalking('walkIn')).toBe(true);
    expect(doorWalking('open')).toBe(false);
    expect(doorWalking('closed')).toBe(false);
    expect(doorWalking(undefined)).toBe(false);
  });
});
