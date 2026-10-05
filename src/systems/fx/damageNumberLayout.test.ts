import { describe, expect, it } from 'vitest';
import { numberLabel, placeNumber, type PlacedNumber } from './damageNumberLayout';

const cfg = { RADIUS_PX: 14, MERGE_MS: 260, STEP_PX: 9, SPREAD_X: 7, MAX_STEPS: 4 };
const n = (id: number, ox: number, oy: number, at: number, kind: PlacedNumber['kind'] = 'hit', amount = 5): PlacedNumber => ({
  id,
  ox,
  oy,
  at,
  kind,
  amount,
});

describe('61라운드 피해 숫자 겹침 정리', () => {
  it('같은 자리·짧은 간격 = 합치기 (치명이 섞이면 치명)', () => {
    expect(placeNumber([n(1, 100, 100, 0)], { x: 104, y: 98, kind: 'hit', amount: 3, now: 200 }, cfg, 600)).toEqual({
      merge: true,
      id: 1,
      amount: 8,
      kind: 'hit',
    });
    const r = placeNumber([n(1, 100, 100, 0)], { x: 100, y: 100, kind: 'crit', amount: 9, now: 100 }, cfg, 600);
    expect(r).toMatchObject({ merge: true, amount: 14, kind: 'crit' });
  });

  it('틱·주인공 피격은 다른 무리와 합치지 않고 비켜 띄운다', () => {
    const r = placeNumber([n(1, 100, 100, 0)], { x: 100, y: 100, kind: 'tick', amount: 2, now: 50 }, cfg, 600);
    expect(r).toEqual({ merge: false, dx: 7, dy: -9 });
  });

  it('간격이 길면 합치지 않고 근처 수만큼 위로·좌우 번갈아, 멀면 그대로', () => {
    const act = [n(1, 100, 100, 0), n(2, 100, 100, 0, 'tick')];
    expect(placeNumber(act, { x: 100, y: 100, kind: 'hit', amount: 1, now: 400 }, cfg, 600)).toEqual({
      merge: false,
      dx: -7,
      dy: -18,
    });
    expect(placeNumber(act, { x: 200, y: 100, kind: 'hit', amount: 1, now: 400 }, cfg, 600)).toEqual({
      merge: false,
      dx: 0,
      dy: 0,
    });
  });

  it('문자열', () => {
    expect(numberLabel('player', 7)).toBe('-7');
    expect(numberLabel('crit', 12)).toBe('12!');
    expect(numberLabel('tick', 2)).toBe('2');
  });
});
