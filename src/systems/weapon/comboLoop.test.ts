import { describe, expect, it } from 'vitest';
import { WEAPONS } from '../data';
import { validateCombo } from '../data/validateCombo';
import type { ComboDef } from '../data/types';
import { ChargeHold, type ChargeEvent } from './chargeHold';
import { ComboTracker } from './combo';
import { artCandidates, comboArtNames, hitArtKey, overlayArtCandidates, pickArt } from './comboArt';
import { isHeavyStrike } from './hitFeel';
import { Momentum } from './momentum';
import { overlayActionsFor } from './spriteDefs';

/** 다음 타 허용 시각마다 눌러 n 타를 이어 친 번호 */
function chain(c: ComboTracker, n: number, allowHeavy = true): number[] {
  const out: number[] = [];
  let t = 0;
  for (let i = 0; i < n; i++) {
    t = Math.max(t, c.readyAt());
    c.press(t);
    const idx = c.poll(t, true, allowHeavy);
    if (idx === null) throw new Error(`poll null at ${t}`);
    out.push(idx);
  }
  return out;
}

describe('55라운드 Q18 대검 G-C 순환', () => {
  const gs = WEAPONS.greatsword.combo!;

  it('입력이 이어지는 한 H1→V→H2→V→H1… 회복 없이 교대', () => {
    const c = new ComboTracker(gs);
    expect(chain(c, 9)).toEqual([0, 1, 2, 3, 0, 1, 2, 3, 0]);
    // 순환이라 마지막 타(V) 뒤에도 cancelFromMs 에 다음 타 (finisherRecoverMs 없음)
    const c2 = new ComboTracker(gs);
    chain(c2, 4);
    expect(c2.readyAt() - c2.lastStartedAt).toBe(gs.hits[3].cancelFromMs);
  });

  it('Q30: 연격 V 는 일반 타격(막타 아님) — 기력 바닥이어도 순환은 그대로', () => {
    const c = new ComboTracker(gs);
    expect([0, 1, 2, 3].map((i) => c.isHeavy(i))).toEqual([false, false, false, false]);
    expect(chain(new ComboTracker(gs), 4, false)).toEqual([0, 1, 2, 3]);
  });

  it('리셋 시간이 지나면 H1 부터', () => {
    const c = new ComboTracker(gs);
    c.press(0);
    c.poll(0, true);
    const late = gs.hits[0].durationMs + gs.resetMs + 1;
    c.press(late);
    expect(c.poll(late, true)).toBe(0);
  });

  it('회귀: 칼은 3타 뒤 회복 후 1타 (순환 아님), 막타 = 3타', () => {
    const k = WEAPONS.katana.combo!;
    const c = new ComboTracker(k);
    expect(chain(c, 3)).toEqual([0, 1, 2]);
    const h = k.hits[2];
    expect(c.readyAt() - c.lastStartedAt).toBe(h.durationMs + k.finisherRecoverMs);
    expect([0, 1, 2].map((i) => c.isHeavy(i))).toEqual([false, false, true]);
  });

  it('회귀: 단검은 데이터 heavy 없이 마지막 타가 막타 (48·55라운드 규칙 그대로)', () => {
    const c = new ComboTracker(WEAPONS.dagger.combo!);
    expect([0, 1, 2].map((i) => c.isHeavy(i))).toEqual([false, false, true]);
    expect(chain(c, 3)).toEqual([0, 1, 2]);
  });
});

describe('55라운드 Q23 관성', () => {
  const def = WEAPONS.greatsword.combo!.momentum!;

  it('이어지는 타마다 +5%, 최대 +20%, 최대일 때 충격원 배율', () => {
    const m = new Momentum(def);
    const speeds: number[] = [];
    for (let i = 0; i < 7; i++) {
      m.input(i * 600);
      speeds.push(Number(m.onHit(i * 600).speedMult.toFixed(2)));
    }
    expect(speeds).toEqual([1, 1.05, 1.1, 1.15, 1.2, 1.2, 1.2]);
    expect(m.atMax).toBe(true);
    expect(m.impactMult).toBe(def.maxImpactMult);
  });

  it('1초 무입력이면 처음부터, 홀드도 입력, 피격이면 처음부터', () => {
    const m = new Momentum(def);
    m.input(0);
    m.onHit(0);
    m.input(500);
    m.onHit(500);
    expect(m.bonus).toBeCloseTo(0.1);
    m.input(1400); // 900ms 뒤 — 이어짐
    expect(m.bonus).toBeCloseTo(0.1);
    m.expire(2401); // 1001ms 무입력
    expect(m.bonus).toBe(0);
    m.input(3000);
    m.onHit(3000);
    m.reset();
    expect(m.speedMult).toBe(1);
  });
});

describe('55라운드 Q22 홀드 차지', () => {
  const def = WEAPONS.greatsword.combo!.charge!;
  const run = (h: ChargeHold, from: number, to: number, held: boolean, ready = true, step = 16) => {
    const ev: (ChargeEvent & { t: number })[] = [];
    for (let t = from; t <= to; t += step) for (const e of h.update(t, held, ready)) ev.push({ ...e, t });
    return ev;
  };

  it('holdMs 전에 떼면 tap(일반 연격)', () => {
    const h = new ChargeHold(def);
    h.press(0);
    expect(run(h, 0, 100, true)).toEqual([]);
    expect(h.update(120, false, true)).toEqual([{ kind: 'tap' }]);
    expect(h.phase).toBe('idle');
  });

  it('홀드 → start → 0.4/0.8/1.2초 단계 → 떼면 그 단계 release', () => {
    const h = new ChargeHold(def);
    h.press(0);
    const ev = run(h, 0, 1300, true, true, 10);
    expect(ev.map((e) => e.kind)).toEqual(['start', 'stage', 'stage', 'stage']);
    expect(ev[0].t).toBe(def.holdMs);
    expect(ev.slice(1).map((e) => e.t)).toEqual([400, 800, 1200]);
    expect(h.stage).toBe(3);
    expect(h.update(1310, false, true)).toEqual([{ kind: 'release', stage: 3 }]);
  });

  it('단계 전에 떼면 tap, 행동 불가 동안은 차지 시계가 서 있다', () => {
    const h = new ChargeHold(def);
    h.press(0);
    run(h, 0, 300, true);
    expect(h.charging).toBe(true);
    expect(h.update(320, false, true)).toEqual([{ kind: 'tap' }]);
    const h2 = new ChargeHold(def);
    h2.press(0);
    expect(run(h2, 0, 500, true, false)).toEqual([]); // 직전 타가 아직 — 차지 시작 안 함
    const ev = run(h2, 510, 1000, true, true, 10);
    expect(ev[0]).toMatchObject({ kind: 'start', t: 510 + def.holdMs });
    expect(ev.find((e) => e.kind === 'stage')!.t).toBe(510 + def.stages[0].atMs);
  });

  it('cancel 은 차지를 버린다', () => {
    const h = new ChargeHold(def);
    h.press(0);
    run(h, 0, 500, true);
    expect(h.cancel()).toBe(true);
    expect(h.update(600, false, true)).toEqual([]);
  });
});

describe('55라운드 §17 그림 이름 표 (데이터 한 곳 매핑)', () => {
  const gs = WEAPONS.greatsword.combo!;

  it('후보 순서대로 로드된 첫 시트, 새 시트가 없으면 기존 시트로 대체', () => {
    expect(artCandidates(gs, 'v', 'body')).toEqual(['cleave', 'slam', 'combo3']);
    expect(pickArt(artCandidates(gs, 'v', 'body'), (n) => n === 'combo3')).toBe('combo3');
    expect(artCandidates(gs, 'v', 'fx')).toEqual(['cleave']);
    expect(artCandidates(gs, 'charge', 'fx')).toEqual([]);
    expect(artCandidates(gs, 'v', 'impactFx')).toEqual(['cleave_impact', 'slam']);
    // fx 가 없으면 몸 후보와 같게, 표에 없는 키는 그 이름 그대로 (기존 combo<n>)
    expect(artCandidates({ art: { a: { body: ['x'] } } }, 'a', 'fx')).toEqual(['x']);
    expect(artCandidates(WEAPONS.dagger.combo, 'combo2', 'fx')).toEqual(['combo2']);
    expect(hitArtKey(WEAPONS.dagger.combo, 1)).toBe('combo2');
    expect(hitArtKey(gs, 1)).toBe('v');
  });

  it('로드 목록·무기 오버레이가 표의 새 이름도 안다', () => {
    const names = comboArtNames({ art: { v: { body: ['vslam', 'slam'], fx: ['vslam_fx'], impactFx: ['crack'] } } });
    expect(names).toEqual({ body: ['vslam', 'slam'], fx: ['vslam_fx', 'crack'] });
    const art = { v: { body: ['vslam'] } };
    expect(overlayActionsFor('greatsword_vslam', 'greatsword', (r) => overlayArtCandidates({ art }, r))).toEqual([
      'vslam',
      'attack',
    ]);
    // 기존 규칙 그대로
    expect(overlayActionsFor('greatsword_combo2', 'greatsword')).toEqual(['combo2', 'attack']);
    expect(overlayActionsFor('greatsword_vslam', 'greatsword')).toEqual([]);
  });
});

describe('55라운드 막타·검사', () => {
  it('isHeavyStrike: 데이터 heavy 가 우선, 없으면 마지막 타 규칙', () => {
    expect(isHeavyStrike({ kind: 'attack', comboIndex: 1, comboCount: 4, heavy: true })).toBe(true);
    expect(isHeavyStrike({ kind: 'attack', comboIndex: 3, comboCount: 4, heavy: false })).toBe(false);
    expect(isHeavyStrike({ kind: 'attack', comboIndex: 2, comboCount: 3 })).toBe(true);
    expect(isHeavyStrike({ kind: 'dashAttack', heavy: false })).toBe(true);
  });

  it('validateCombo: 잘못된 모양·표에 없는 그림 키·단계 순서를 거른다', () => {
    const base = structuredClone(WEAPONS.greatsword.combo!) as ComboDef;
    expect(() => validateCombo(base, 'gs')).not.toThrow();
    const bad1 = structuredClone(base);
    bad1.hits[0].hitShape = { kind: 'arc', fromDeg: 10, toDeg: 10 };
    expect(() => validateCombo(bad1, 'gs')).toThrow(/fromDeg/);
    const bad2 = structuredClone(base);
    bad2.hits[0].art = 'nope';
    expect(() => validateCombo(bad2, 'gs')).toThrow(/art/);
    const bad3 = structuredClone(base);
    bad3.charge!.stages[1].atMs = 300;
    expect(() => validateCombo(bad3, 'gs')).toThrow(/오름차순/);
    const bad4 = structuredClone(base);
    (bad4.hits[1].hitShape as { kind: string }).kind = 'blob';
    expect(() => validateCombo(bad4, 'gs')).toThrow(/arc\|wedge\|rect\|ring/);
  });
});
