import { describe, expect, it } from 'vitest';
import { TRANSITION_TIMING, TRANSITION_UI, TransitionGate, type TransitionDeps } from './transitionGate';

function harness(renderer = true) {
  const ui: { event: string; payload: unknown }[] = [];
  const internal: unknown[] = [];
  const timers: { at: number; fn: () => void; dead: boolean }[] = [];
  let now = 0;
  const deps: TransitionDeps = {
    emitUi: (event, payload) => ui.push({ event, payload }),
    emitInternal: (p) => internal.push(p),
    rendererRegistered: () => renderer,
    setTimer: (ms, fn) => {
      const t = { at: now + ms, fn, dead: false };
      timers.push(t);
      return t;
    },
    clearTimer: (h) => {
      (h as { dead: boolean }).dead = true;
    },
  };
  const advance = (ms: number) => {
    now += ms;
    for (const t of [...timers])
      if (!t.dead && t.at <= now) {
        t.dead = true;
        t.fn();
      }
  };
  const gate = new TransitionGate();
  gate.attach(deps);
  return { gate, ui, internal, advance };
}

describe('그림 속 입구 전환 문지기', () => {
  it('UI 가 덮고 → 장면 교체 → READY → END', () => {
    const { gate, ui, internal } = harness();
    let swapped = 0;
    expect(gate.begin({ mode: 'enterNode', region: 'waste', nodeKind: 'battle' }, () => swapped++)).toBe(true);
    expect(gate.locked).toBe(true);
    expect(internal).toEqual([{ id: 1, mode: 'enterNode', region: 'waste', nodeKind: 'battle' }]);
    expect(ui[0]).toMatchObject({ event: TRANSITION_UI.BEGIN, payload: { id: 1, skippable: true } });
    expect(gate.begin({ mode: 'floor', region: 'x' }, () => {})).toBe(false);
    gate.onUiCovered({ id: 99 });
    expect(swapped).toBe(0);
    gate.onUiCovered({ id: 1 });
    expect(swapped).toBe(1);
    expect(gate.ready()).toBe(true);
    expect(ui.at(-1)).toEqual({ event: TRANSITION_UI.READY, payload: { id: 1 } });
    gate.onUiEnd({ id: 1 });
    expect(gate.locked).toBe(false);
  });

  it('UI 가 응답하지 않으면 3초 뒤 스스로 진행 · READY 뒤에도 3초 뒤 입력 재개', () => {
    const { gate, advance } = harness();
    let swapped = 0;
    gate.begin({ mode: 'exitRoom', region: 'waste' }, () => swapped++);
    advance(TRANSITION_TIMING.COVER_TIMEOUT_MS - 1);
    expect(swapped).toBe(0);
    advance(1);
    expect(swapped).toBe(1);
    gate.ready();
    advance(TRANSITION_TIMING.END_TIMEOUT_MS);
    expect(gate.locked).toBe(false);
  });

  it('덮인 뒤 새 장면이 ready 를 못 부르면 스스로 READY', () => {
    const { gate, ui, advance } = harness();
    gate.begin({ mode: 'training', region: 'training' }, () => {});
    gate.onUiCovered({ id: 1 });
    advance(TRANSITION_TIMING.READY_TIMEOUT_MS);
    expect(ui.some((u) => u.event === TRANSITION_UI.READY)).toBe(true);
  });

  it('UI 렌더러가 없으면 대체 덮기 뒤 바로 · ready 는 false (씬이 스스로 밝힌다)', () => {
    const { gate } = harness(false);
    let swapped = 0;
    let cover: (() => void) | null = null;
    gate.begin(
      { mode: 'enterNode', region: 'gate' },
      () => swapped++,
      (go) => (cover = go),
    );
    expect(swapped).toBe(0);
    cover!();
    expect(swapped).toBe(1);
    expect(gate.ready()).toBe(false);
    expect(gate.locked).toBe(false);
  });

  it('cancel: 덮개가 남지 않게 READY 를 보내고 끝', () => {
    const { gate, ui } = harness();
    gate.begin({ mode: 'enterNode', region: 'gate' }, () => {});
    gate.cancel();
    expect(ui.at(-1)?.event).toBe(TRANSITION_UI.READY);
    expect(gate.locked).toBe(false);
  });
});

import { resolveDoorName, trainingDoorName } from './doorNames';

describe('입구 그림 이름 (art §28)', () => {
  const have = new Set([
    'door_waste_battle',
    'door_gate_rest',
    'door_hall_boss',
    'door_outer_battle',
    'door_outer_event',
  ]);
  const exists = (n: string) => have.has(n);
  it('정확 → 별칭 → <지역>_battle → 없음', () => {
    expect(resolveDoorName('outer', 'event', null, exists)).toBe('door_outer_event');
    expect(resolveDoorName('waste', 'birth', null, exists)).toBe('door_waste_battle');
    expect(resolveDoorName('gate', 'post', null, exists)).toBe('door_gate_rest');
    expect(resolveDoorName('boss', 'boss', null, exists)).toBe('door_hall_boss');
    expect(resolveDoorName('outer', 'shop', null, exists)).toBe('door_outer_battle');
    expect(resolveDoorName('training', 'floor', null, exists)).toBeNull();
    expect(resolveDoorName('gate', 'post', { gate_post: 'outer_event' }, exists)).toBe('door_outer_event');
  });
  it('수련장 방 입구', () => {
    expect(trainingDoorName(true)).toBe('door_training_boss');
    expect(trainingDoorName(false)).toBe('door_training_training');
  });
});
