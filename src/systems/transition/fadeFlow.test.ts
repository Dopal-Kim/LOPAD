import { describe, expect, it } from 'vitest';
import { generateRoute, RouteState } from '../route';
import { nodeFadeInfo, trainingFadeInfo } from './fadeFlow';
import { TRANSITION_TIMING, TRANSITION_UI, TransitionGate, type TransitionDeps } from './transitionGate';

/** 문지기 + 가짜 시계 (transitionGate.test 와 같은 꼴) */
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

describe('62 H 지도에서 고른 뒤 짧은 암전 (fade)', () => {
  it('노드: 지역(보스 = boss)·종류·id·덮기 시간, 입구 그림·줌 중심은 싣지 않는다', () => {
    const g = generateRoute('stage1', 'fade:0');
    const boss = g.nodes.find((n) => n.kind === 'boss')!;
    const first = g.nodes.find((n) => n.col === 0)!;
    expect(nodeFadeInfo('stage1', first, 400)).toEqual({
      mode: 'fade',
      region: 'waste',
      nodeKind: first.kind,
      nodeId: first.id,
      durationMs: 400,
    });
    const b = nodeFadeInfo('stage1', boss, 400);
    expect(b.region).toBe('boss');
    expect(b).not.toHaveProperty('doorKey');
    expect(b).not.toHaveProperty('from');
  });

  it('수련장: 방으로(training·boss + 방 id) · 방 → 지도 마당(id 없음)', () => {
    expect(trainingFadeInfo({ id: 'katana', boss: false }, 400)).toEqual({
      mode: 'fade',
      region: 'training',
      nodeKind: 'training',
      nodeId: 'katana',
      durationMs: 400,
    });
    expect(trainingFadeInfo({ id: 'shadow', boss: true }, 400).nodeKind).toBe('boss');
    expect(trainingFadeInfo(null, 400)).not.toHaveProperty('nodeId');
  });

  it('흐름: 문 안 → 지도(고르기) → 고름 → fade begin → UI 덮음 → 씬 교체 → READY → END', () => {
    const { gate, ui, internal } = harness();
    const route = new RouteState(generateRoute('stage1', 'flow:1'), 1);
    const steps: string[] = [];
    // 문 안 = 지도 열림 (고르기 상태) — 외길이어도 지도를 거친다
    route.choosing = true;
    steps.push('map');
    const pick = route.nextOptions()[0];
    expect(route.enter(pick.id)).toBe(true);
    steps.push('choose');
    const info = nodeFadeInfo('stage1', route.current!, 400);
    expect(gate.begin(info, () => steps.push('restart'))).toBe(true);
    expect(internal.at(-1)).toMatchObject({ mode: 'fade', nodeKind: pick.kind });
    expect(ui.at(-1)).toMatchObject({
      event: TRANSITION_UI.BEGIN,
      payload: { mode: 'fade', durationMs: 400, nodeId: pick.id },
    });
    gate.onUiCovered({ id: 1 });
    expect(gate.ready()).toBe(true);
    steps.push('ready');
    gate.onUiEnd({ id: 1 });
    expect(gate.locked).toBe(false);
    expect(steps).toEqual(['map', 'choose', 'restart', 'ready']);
  });

  it('fade 안전장치는 짧다: UI 가 덮지 않으면 1.2초 · 걷어내고 END 가 없으면 1.5초', () => {
    const { gate, advance } = harness();
    let swapped = 0;
    gate.begin(trainingFadeInfo(null, 400), () => swapped++);
    advance(TRANSITION_TIMING.FADE_COVER_TIMEOUT_MS - 1);
    expect(swapped).toBe(0);
    advance(1);
    expect(swapped).toBe(1);
    expect(gate.ready()).toBe(true);
    advance(TRANSITION_TIMING.FADE_END_TIMEOUT_MS - 1);
    expect(gate.locked).toBe(true);
    advance(1);
    expect(gate.locked).toBe(false);
    expect(TRANSITION_TIMING.FADE_COVER_TIMEOUT_MS).toBeLessThan(TRANSITION_TIMING.COVER_TIMEOUT_MS);
  });

  it('UI 렌더러가 없으면 카메라 암전(대체 덮기) 뒤 바로', () => {
    const { gate } = harness(false);
    let swapped = 0;
    let cover: (() => void) | null = null;
    gate.begin(
      trainingFadeInfo({ id: 'step', boss: false }, 400),
      () => swapped++,
      (go) => (cover = go),
    );
    cover!();
    expect(swapped).toBe(1);
    expect(gate.ready()).toBe(false);
    expect(gate.locked).toBe(false);
  });
});

describe('62 H 지도 미리보기 (RouteState)', () => {
  it('previewTargets = 고를 수 있는 노드 + 그다음 열 (중복 없음)', () => {
    const r = new RouteState(generateRoute('stage1', 'preview:2'), 1);
    r.enter(r.nextOptions()[0].id);
    const opts = r.nextOptions();
    const targets = r.previewTargets();
    const ids = new Set(targets.map((n) => n.id));
    expect(ids.size).toBe(targets.length);
    for (const n of opts) {
      expect(ids.has(n.id)).toBe(true);
      for (const l of n.links) expect(ids.has(l)).toBe(true);
    }
    const cols = new Set(targets.map((n) => n.col));
    const c = opts[0].col;
    for (const col of cols) expect([c, c + 1]).toContain(col);
  });

  it('toUi: previewOf 가 있으면 previewKey (보스 지역 = boss) · previewRegion = 그 열의 지역', () => {
    const r = new RouteState(generateRoute('stage1', 'preview:3'), 1);
    const asked: string[] = [];
    r.previewOf = (n, region) => {
      asked.push(region);
      return n.kind === 'shop' ? null : `paint/door_${region}_${n.kind}`;
    };
    const ui = r.toUi();
    const boss = ui.nodes.find((n) => n.type === 'boss')!;
    expect(boss.previewKey).toBe('paint/door_boss_boss');
    expect(boss.previewRegion).toBe('hall');
    expect(asked).toContain('boss');
    const first = ui.nodes.find((n) => n.col === 0)!;
    expect(first.previewRegion).toBe('waste');
    for (const n of ui.nodes) if (n.previewKey === undefined) expect(['shop']).toContain(r.node(n.id)!.kind);
    // 훅이 없으면 previewKey 없음 (지역은 그대로)
    r.previewOf = null;
    expect(r.toUi().nodes.every((n) => n.previewKey === undefined && Boolean(n.previewRegion))).toBe(true);
  });
});
