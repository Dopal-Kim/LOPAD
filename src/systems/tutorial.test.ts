import { describe, expect, it } from 'vitest';
import { ROUTE } from './route';
import { TutorialMachine, fillText, type TutorialDef, type TutorialEvent } from './tutorial';

const TILE = 16;
const DEF: TutorialDef = ROUTE.tutorial!;
const center = { x: 100 * TILE, y: 100 * TILE };
const at = (dx: number, dy: number) => ({ x: center.x + dx * TILE, y: center.y + dy * TILE });
const signs = DEF.steps.map((s) => at(s.sign[0], s.sign[1]));
const dummies = DEF.dummies.map(([dx, dy]) => at(dx, dy));
const types = (e: TutorialEvent[]) => e.map((x) => x.type);

const machine = () => new TutorialMachine(DEF, signs, dummies, TILE, { name: '패링', description: '받아친다' });

describe('49라운드 탄생 전장 조작 안내 (단계 머신)', () => {
  it('단계 순서: 이동 → 공격 → 대쉬 → 보조 동작 → 좌 홀드(61라운드 4동사) → 약한 적 → 끝', () => {
    expect(DEF.steps.map((s) => s.action)).toEqual(['arrive', 'hitDummy', 'dash', 'secondary', 'hold', 'fight']);
    expect(DEF.steps.find((s) => s.action === 'hold')?.keys).toEqual(['좌클릭 길게']);
  });

  it('시작하면 첫 표식 강조 + 안내(promptOnStart). 표식에 닿으면 다음 단계', () => {
    const m = machine();
    expect(m.started).toBe(false);
    const ev = m.start();
    expect(types(ev)).toEqual(['step', 'prompt']);
    expect(m.update(center)).toEqual([]);
    const next = m.update(signs[0]);
    expect(m.stepIndex).toBe(1);
    expect(next[0]).toEqual({ type: 'step', step: 1, sign: 1 });
  });

  it('표식에 다가가면 그 단계 안내 문구가 한 번만', () => {
    const m = machine();
    m.start();
    m.update(signs[0]);
    const p = m.update(signs[1]);
    expect(p).toEqual([{ type: 'prompt', step: 1, text: DEF.steps[1].text }]);
    expect(m.update(signs[1])).toEqual([]);
  });

  it('허수아비 근처 공격 count 번 → 다음. 허수아비가 멀면 세지 않지만 흔들림은 맞을 때마다', () => {
    const m = machine();
    m.start();
    m.update(signs[0]);
    const far = at(-10, 0);
    expect(m.attack({ ...far, dirX: 1, dirY: 0 }, far, false)).toEqual([]);
    const d0 = dummies[0];
    const need = DEF.steps[1].count ?? 1;
    for (let i = 0; i < need - 1; i++) {
      const e = m.attack({ ...d0, dirX: 1, dirY: 0 }, d0, false);
      expect(types(e)).toContain('dummyHit');
      expect(m.stepIndex).toBe(1);
    }
    m.attack({ ...d0, dirX: 1, dirY: 0 }, d0, false);
    expect(m.stepIndex).toBe(2);
  });

  it('원거리(활): 조준 원뿔 안 허수아비를 겨누면 맞힘', () => {
    const m = machine();
    m.start();
    m.update(signs[0]);
    const from = at(0, -6);
    const target = dummies[0];
    const dx = target.x - from.x;
    const dy = target.y - from.y;
    expect(types(m.attack({ ...from, dirX: dx, dirY: dy }, from, true))).toContain('dummyHit');
    expect(m.attack({ ...from, dirX: -dx, dirY: -dy }, from, true)).toEqual([]);
    // 근접 무기는 같은 거리에서 못 맞힌다
    expect(m.attack({ ...from, dirX: dx, dirY: dy }, from, false)).toEqual([]);
  });

  it('지금 단계가 아닌 행동은 세지 않는다 (대쉬를 미리 해도 공격 단계는 그대로)', () => {
    const m = machine();
    m.start();
    m.update(signs[0]);
    expect(m.action('dash')).toEqual([]);
    expect(m.action('secondary')).toEqual([]);
    expect(m.stepIndex).toBe(1);
  });

  it('대쉬 → 보조 동작({name} 치환) → 좌 홀드({holdName}) → 약한 적 전투 요청 → 전멸이면 끝', () => {
    const m = machine();
    m.start();
    m.update(signs[0]);
    for (let i = 0; i < (DEF.steps[1].count ?? 1); i++)
      m.attack({ ...dummies[0], dirX: 1, dirY: 0 }, dummies[0], false);
    expect(m.step!.action).toBe('dash');
    m.action('dash');
    expect(m.step!.action).toBe('secondary');
    const prompt = m.update(signs[3]);
    expect(prompt[0]).toMatchObject({
      type: 'prompt',
      text: fillText(DEF.steps[3].text, { name: '패링', description: '받아친다' }),
    });
    expect((prompt[0] as { text: string }).text).toContain('패링');
    m.action('secondary');
    expect(m.step!.action).toBe('hold');
    expect(m.action('dash')).toEqual([]);
    const ev = m.action('hold');
    expect(types(ev)).toEqual(['step', 'prompt', 'fight']);
    expect(m.fightCleared()).toEqual([{ type: 'done', text: DEF.doneText }]);
    expect(m.done).toBe(true);
    expect(m.update(center)).toEqual([]);
  });

  it('전투 단계 전에는 fightCleared 가 무시되고, skip 은 바로 끝', () => {
    const m = machine();
    m.start();
    expect(m.fightCleared()).toEqual([]);
    expect(types(m.skip())).toEqual(['done']);
    expect(m.done).toBe(true);
    expect(m.skip()).toEqual([]);
  });
});
