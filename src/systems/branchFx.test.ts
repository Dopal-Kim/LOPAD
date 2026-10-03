import { describe, expect, it } from 'vitest';
import { WEAPONS } from '../data';
import { aimLineFrame, branchFxSheetIds, levelMult, snipeLevel, stripFxPrefix } from './branchFx';
import { keyedDurations, startsOf } from './spriteDefs';
import { WeaponResource, effectiveResource } from './weaponResource';
import { WeaponState } from './weapons';

describe('51·52라운드 활 갈래 시트 (계약 art §10)', () => {
  it('활 1단 갈래 로드 목록 (화살·조준 화살·발사 섬광·조준선·꼬리) — 근접 갈래 이펙트는 보류', () => {
    const ids = branchFxSheetIds({
      katana: { kind: 'melee', personality: { branches: [{ id: 'iai' }] } },
      bow: { kind: 'ranged', personality: { branches: [{ id: 'snipe' }] } },
    });
    expect(ids).toEqual([
      'bow_arrow_snipe',
      'bow_arrow_aimed_snipe',
      'bow_muzzle_snipe',
      'aim_line_snipe',
      'bow_arrow_snipe_lv1',
      'bow_arrow_snipe_lv2',
      'bow_arrow_snipe_lv3',
    ]);
    expect(stripFxPrefix('fx/crit_burst')).toBe('crit_burst');
  });

  it('저격 단계: 최대 사거리 1/3 부터 lv2, 2/3 부터 lv3 · 단계 배율', () => {
    expect(snipeLevel(0, 300)).toBe(1);
    expect(snipeLevel(99, 300)).toBe(1);
    expect(snipeLevel(100, 300)).toBe(2);
    expect(snipeLevel(199, 300)).toBe(2);
    expect(snipeLevel(200, 300)).toBe(3);
    expect(snipeLevel(500, 300)).toBe(3);
    expect(levelMult([1, 1.5, 2.2], 1)).toBe(1);
    expect(levelMult([1, 1.5, 2.2], 3)).toBe(2.2);
    expect(levelMult(undefined, 3)).toBe(1);
  });

  it('저격 조준선 진행도 프레임: min(4, floor(p×5)), 완료 = 5 · 기본 조준선은 상태 프레임', () => {
    const snipe = { progressFrames: [0, 1, 2, 3, 4], stateFrames: { charging: [0, 4], complete: 5 }, frames: 6 };
    expect(aimLineFrame(snipe, 0)).toBe(0);
    expect(aimLineFrame(snipe, 0.39)).toBe(1);
    expect(aimLineFrame(snipe, 0.99)).toBe(4);
    expect(aimLineFrame(snipe, 1)).toBe(5);
    const base = { stateFrames: { charging: 0, complete: 1 }, frames: 2 };
    expect(aimLineFrame(base, 0.5)).toBe(0);
    expect(aimLineFrame(base, 1)).toBe(1);
  });
});

describe('51라운드 Q2 활 갈래 = 속사·저격 (산탄 계열 삭제)', () => {
  it('트리 id 가 아트 BRANCHES(rapid·snipe·volley·quiver·pierce·deadeye)와 같다', () => {
    const b = WEAPONS.bow.personality.branches;
    expect(b.map((x) => x.id)).toEqual(['rapid', 'snipe']);
    expect(b.flatMap((x) => (x.next ?? []).map((n) => n.id))).toEqual(['volley', 'quiver', 'pierce', 'deadeye']);
  });

  it('속사: 연사 배율이 시위 당김·다음 발 간격을 나누고 탄창이 늘어난다', () => {
    const w = new WeaponState('bow', WEAPONS.bow);
    const base = w.shotTiming;
    expect(base.drawMs).toBeGreaterThan(0);
    w.restore({ path: ['rapid'] });
    const r = w.shotTiming;
    expect(r.cooldownMs).toBeLessThan(base.cooldownMs);
    expect(r.drawMs).toBeLessThan(base.drawMs);
    const ammo = effectiveResource(WEAPONS.bow.resource!, w.mods);
    expect(ammo.max).toBeGreaterThan(WEAPONS.bow.resource!.max);
    w.restore({ path: ['rapid', 'quiver'] });
    const q = effectiveResource(WEAPONS.bow.resource!, w.mods);
    expect(q.max).toBeGreaterThan(ammo.max);
    expect(q.kind === 'ammo' && q.reloadMs).toBeLessThan(1300);
  });

  it('저격: 조준 사격 거리 단계 배율 · 관통, 필중은 lv3 확정 치명', () => {
    const w = new WeaponState('bow', WEAPONS.bow);
    w.restore({ path: ['snipe'] });
    expect(w.mods.snipe?.levelMults).toHaveLength(3);
    expect(w.mods.pierce).toBeGreaterThan(0);
    w.restore({ path: ['snipe', 'deadeye'] });
    expect(w.mods.snipe?.critFromLevel).toBe(3);
  });
});

describe('51라운드 Q3 템포 · Q4 넣기/뽑기', () => {
  it('두 구간 맞춤: 판정 프레임 시작이 keyAtMs, 전체가 totalMs', () => {
    const d = [90, 100, 60, 110, 140, 130]; // 대검 1타 시트 (판정 f2)
    const k = keyedDurations(d, 2, 380, 820)!;
    const s = startsOf(k);
    expect(s[2]).toBeCloseTo(380);
    expect(k.reduce((a, b) => a + b, 0)).toBeCloseTo(820);
    expect(keyedDurations(d, 0, 100, 500)).toBeNull();
    expect(keyedDurations(d, 2, 900, 820)).toBeNull();
  });

  it('데이터 템포: 3연격(1타 시작 → 3타 끝) 대검 > 칼 > 단검, 느릴수록 한 방 피해 큼', () => {
    const t3 = (id: string) => {
      const h = WEAPONS[id].combo!.hits;
      return h[0].cancelFromMs + h[1].cancelFromMs + h[2].durationMs;
    };
    expect(t3('greatsword')).toBeGreaterThan(1800);
    expect(t3('katana')).toBeGreaterThan(950);
    expect(t3('katana')).toBeLessThan(1250);
    expect(t3('dagger')).toBeLessThan(600);
    const hit = (id: string) => WEAPONS[id].damageMult * Math.max(...WEAPONS[id].combo!.hits.map((x) => x.damageMult));
    expect(hit('greatsword')).toBeGreaterThan(hit('katana'));
    expect(hit('katana')).toBeGreaterThan(hit('dagger'));
  });

  it('넣은 동안 기력 회복 배율', () => {
    const r = new WeaponResource(WEAPONS.katana.resource!);
    r.spend(50, 0);
    r.tick(1000, 1000);
    const normal = r.value;
    const r2 = new WeaponResource(WEAPONS.katana.resource!);
    r2.spend(50, 0);
    r2.regenMult = WEAPONS.katana.carry!.sheathedRegenMult!;
    r2.tick(1000, 1000);
    expect(r2.value).toBeGreaterThan(normal);
    expect(WEAPONS.katana.carry!.firstStrike?.forceCrit).toBe(true);
    expect(WEAPONS.greatsword.carry!.firstStrike?.knockbackMult).toBeGreaterThan(1);
  });
});
