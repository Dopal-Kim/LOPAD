import { describe, expect, it } from 'vitest';
import { WEAPONS } from '../../data';
import { aimLineFrame, branchFxSheetIds, levelMult, snipeCritFromLevel, snipeLevel, stripFxPrefix } from './branchFx';
import { keyedDurations, startsOf } from '../sprites/spriteDefs';
import { WeaponResource, effectiveResource } from '../weapon/weaponResource';
import { WeaponState } from '../weapon/weapons';

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
  it('트리 id: 1단 속사·저격 (아트 BRANCHES), 2단 연궁·무한통·필중·천공 (57 S-1: 2단 관통 → 천공)', () => {
    const b = WEAPONS.bow.personality.branches;
    expect(b.map((x) => x.id)).toEqual(['rapid', 'snipe']);
    expect(b.flatMap((x) => (x.next ?? []).map((n) => n.id))).toEqual(['volley', 'quiver', 'deadeye', 'skypierce']);
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
    // 57라운드 빌드 축 조정: 피멍 최대 +30% · 식힘 ×2
    const adj = effectiveResource(WEAPONS.bow.resource!, w.mods, { maxMult: 1.3, coolMult: 2 });
    expect(adj.max).toBe(Math.round(q.max * 1.3));
    expect(adj.kind === 'ammo' && adj.reloadMs).toBe(
      WEAPONS.bow.resource!.kind === 'ammo' ? WEAPONS.bow.resource!.reloadMs * 2 : 0,
    );
  });

  it('저격: 거리 단계 배율 최대 ×1.6 · 필중 상한 ×2.2 (57라운드 — 필중 치명은 정밀 조준 완벽 놓기 규칙)', () => {
    const w = new WeaponState('bow', WEAPONS.bow);
    w.restore({ path: ['snipe'] });
    expect(w.mods.snipe?.levelMults).toHaveLength(3);
    expect(w.mods.snipe?.aimedLevelMults?.[2]).toBeCloseTo(1.6);
    w.restore({ path: ['snipe', 'deadeye'] });
    expect(w.mods.snipe?.aimedLevelMults?.[2]).toBeCloseTo(2.2);
    expect(w.mods.snipe?.critFromLevel).toBeUndefined();
    expect(w.evolution?.rule?.kind).toBe('deadeye');
  });

  it('53라운드 Q40 규칙 함수: 최장 거리 확정 치명은 조준 사격만 (플래그가 있을 때)', () => {
    const S = { critFromLevel: 3, critAimedOnly: true, levelMults: [1, 1.4, 2] };
    expect(snipeCritFromLevel(S, true)).toBe(3);
    expect(snipeCritFromLevel(S, false)).toBeUndefined();
    // 플래그가 없으면 예전처럼 모든 화살
    expect(snipeCritFromLevel({ critFromLevel: 3 }, false)).toBe(3);
    expect(snipeCritFromLevel(null, true)).toBeUndefined();
  });

  it('53라운드 Q16: 저격 거리 배율은 모든 화살, 조준 사격은 단계마다 더 높다', () => {
    const w = new WeaponState('bow', WEAPONS.bow);
    for (const path of [['snipe'], ['snipe', 'deadeye']]) {
      w.restore({ path });
      const S = w.mods.snipe!;
      expect(S.aimedOnly).toBeFalsy();
      expect(S.aimedLevelMults).toHaveLength(S.levelMults.length);
      expect(S.levelMults[S.levelMults.length - 1]).toBeGreaterThan(1);
      for (let i = 1; i < S.levelMults.length; i++) expect(S.aimedLevelMults![i]).toBeGreaterThan(S.levelMults[i]);
    }
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
    // 56라운드 Q25 대검 새 그림 시간 그대로(3타 약 2.6초) · Q1 칼 약 1.5초
    expect(t3('greatsword')).toBeGreaterThan(2000);
    expect(t3('katana')).toBeGreaterThan(1400);
    expect(t3('katana')).toBeLessThan(1700);
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
