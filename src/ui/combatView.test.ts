import { describe, expect, it } from 'vitest';
import type { UiWeaponGauge, UiWeaponResource } from '../contract/ui';
import { HP_TRAIL_START, bossLeft, combatRows, curseShort, hpLow, hpTrailStep, pickResources } from './combatView';
import { COMBAT_HUD } from './themeR61';

const gauge: UiWeaponGauge = { kind: 'kenki', label: '검기', value: 100, max: 300, stage: 1 };
const res: UiWeaponResource = { kind: 'stamina', label: '기력', value: 50, max: 100, state: 'ok' };

describe('combatView', () => {
  it('자원은 하나만 크게: 고유 자원 우선, 둘 다면 무기 자원은 보조 줄', () => {
    expect(pickResources(gauge, null)).toEqual({ main: 'gauge', sub: false });
    expect(pickResources(null, res)).toEqual({ main: 'resource', sub: false });
    expect(pickResources(gauge, res)).toEqual({ main: 'gauge', sub: true });
    expect(pickResources(null, null)).toEqual({ main: null, sub: false });
  });

  it('체력 낮음 (0 은 강조하지 않는다)', () => {
    expect(hpLow(30, 100, 0.3)).toBe(true);
    expect(hpLow(31, 100, 0.3)).toBe(false);
    expect(hpLow(0, 100, 0.3)).toBe(false);
    expect(hpLow(5, 0, 0.3)).toBe(false);
  });

  it('행 배치: 2배 눈금·보조 줄이 있으면 묶음이 커진다', () => {
    const a = combatRows(COMBAT_HUD, { big: false, sub: false, growth: false });
    const b = combatRows(COMBAT_HUD, { big: true, sub: false, growth: false });
    const c = combatRows(COMBAT_HUD, { big: true, sub: true, growth: false });
    const d = combatRows(COMBAT_HUD, { big: true, sub: true, growth: true });
    expect(a.growth).toBeNull();
    expect(d.growth).toBeGreaterThan(d.sub!);
    expect(d.slots).toBeGreaterThan(d.growth!);
    expect(d.h - c.h).toBe(COMBAT_HUD.growthRowH + COMBAT_HUD.rowGap);
    expect(a.sub).toBeNull();
    expect(b.h - a.h).toBe(COMBAT_HUD.bigRowH - COMBAT_HUD.rowH);
    expect(c.sub).not.toBeNull();
    expect(c.h - b.h).toBe(COMBAT_HUD.rowH + COMBAT_HUD.rowGap);
    expect(c.slots).toBeGreaterThan(c.sub!);
  });

  it('저주 짧은 꼴: 노드 우선', () => {
    const base = { id: 'c', name: '만취', benefit: '', penalty: '' };
    expect(curseShort({ ...base, nodesLeft: 3, killsLeft: 9 })).toEqual({ n: 3, unit: 'node' });
    expect(curseShort({ ...base, nodesLeft: null, killsLeft: 9 })).toEqual({ n: 9, unit: 'kill' });
    expect(curseShort({ ...base, nodesLeft: null, killsLeft: null })).toBeNull();
    expect(curseShort(null)).toBeNull();
  });

  it('보스 막대는 가운데, 묶음과 겹치면 오른쪽으로 비킨다', () => {
    expect(bossLeft(960, 320, 300, 12)).toBe(334);
    expect(bossLeft(960, 320, 200, 12)).toBe(320);
  });

  it('체력 피격 잔상: 맞으면 머물렀다 줄고, 연타는 보이는 자리에서 다시, 회복은 바로 따라간다', () => {
    const spec = { holdMs: 400, fallMs: 400 };
    let { trail, ghost } = hpTrailStep(HP_TRAIL_START, 1, 0, spec);
    expect(ghost).toBe(1);
    ({ trail, ghost } = hpTrailStep(trail, 0.6, 100, spec));
    expect(ghost).toBe(1);
    expect(hpTrailStep(trail, 0.6, 500, spec).ghost).toBe(1);
    expect(hpTrailStep(trail, 0.6, 700, spec).ghost).toBeCloseTo(0.8);
    expect(hpTrailStep(trail, 0.6, 900, spec).ghost).toBe(0.6);
    // 줄어드는 중 또 맞음: 0.8 에서 다시 머문다
    ({ trail, ghost } = hpTrailStep(trail, 0.4, 700, spec));
    expect(ghost).toBeCloseTo(0.8);
    expect(hpTrailStep(trail, 0.4, 1500, spec).ghost).toBe(0.4);
    // 회복이 잔상을 넘으면 잔상 없음
    ({ trail, ghost } = hpTrailStep(trail, 0.9, 800, spec));
    expect(ghost).toBe(0.9);
    expect(hpTrailStep(trail, 0.9, 2000, spec).ghost).toBe(0.9);
  });
});
