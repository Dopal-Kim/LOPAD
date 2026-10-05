import { describe, expect, it } from 'vitest';
import {
  BOSSES,
  ENEMIES,
  PLAYER_DATA,
  RUN,
  STAGES,
  STORY,
  WEAPONS,
  WEAPON_RULES,
  validateEnemies,
  validateWeapons,
} from './index';
import type { EnemyTable, WeaponTable } from './types';

describe('data/*.json', () => {
  it('플레이어·적·보스·스테이지 데이터가 검증을 통과한다', () => {
    expect(PLAYER_DATA.stats.hp).toBeGreaterThan(0);
    expect(Object.keys(ENEMIES)).toEqual(expect.arrayContaining(['dummy', 'archer', 'charger']));
    expect(BOSSES.stage1.phases[0].hpFraction).toBe(1);
    expect(STAGES.stage1.boss).toBe('stage1');
    expect(RUN.order).toHaveLength(8);
    for (const id of RUN.order) expect(BOSSES[STAGES[id].boss]).toBeDefined();
    expect(BOSSES.emperor.phases).toHaveLength(3);
    expect(BOSSES.emperor.name).toContain('평');
    for (const id of RUN.order) expect(STORY.floors[id].title).toContain('층');
    expect(STORY.floors.stage8.empire).toBe('평상');
    expect(RUN.maxSaves).toBe(2);
  });

  it('잘못된 행동 키는 거부한다', () => {
    const bad = { x: { ...ENEMIES.dummy, behavior: 'fly' } } as unknown as EnemyTable;
    expect(() => validateEnemies(bad)).toThrow(/behavior/);
  });

  it('무기 4종: 우클릭 보조 동작 1종, 1차 2 · 2차 각 2, 임계 오름차순 (27라운드)', () => {
    const ids = Object.keys(WEAPONS);
    expect(ids).toEqual(['katana', 'greatsword', 'dagger', 'bow']);
    const secondaryNames = ids.map((id) => WEAPONS[id].secondary.name);
    // 56라운드 Q48: 칼 우클릭 = 가드(누른 직후 0.15초 = 패링)
    expect(secondaryNames).toEqual(['가드·패링', '가드', '그림자 걸음', '당겨 쏘기']); // 57라운드 Q7: 활 우클릭 이름
    for (const id of ids) {
      const P = WEAPONS[id].personality;
      expect(P.thresholds).toEqual([100, 200]);
      expect(P.branches).toHaveLength(2);
      for (const b of P.branches) {
        expect(b.next).toHaveLength(2);
        for (const n of b.next!) expect(n.next ?? []).toHaveLength(0);
      }
      const names = [...P.branches, ...P.branches.flatMap((b) => b.next!)].map((n) => n.name);
      expect(new Set(names).size).toBe(6);
    }
    expect(WEAPON_RULES).toMatchObject({ reinforceBonus: 0.15, reinforceMax: 3 });
    // 61라운드 P2 DPS 기준선 (systems/weapon/dps.test)
    expect(WEAPON_RULES.dpsBaseline?.attack).toBe(5);
  });

  it('무기 데이터 오류를 거부한다: 임계 역순, 선택지 수, 모르는 효과 키', () => {
    const clone = () => JSON.parse(JSON.stringify(WEAPONS)) as WeaponTable;
    const a = clone();
    a.katana.personality.thresholds = [200, 100];
    expect(() => validateWeapons(a)).toThrow(/오름차순/);
    const b = clone();
    b.dagger.personality.branches = b.dagger.personality.branches.slice(0, 1);
    expect(() => validateWeapons(b)).toThrow(/2개/);
    const c = clone();
    c.dagger.personality.branches[0].next = c.dagger.personality.branches[0].next!.slice(0, 1);
    expect(() => validateWeapons(c)).toThrow(/next 는 2개/);
    const d = clone();
    (d.greatsword.personality.branches[1].mods as Record<string, unknown>).laser = 1;
    expect(() => validateWeapons(d)).toThrow(/mods.laser/);
    const e = clone();
    (e.katana as unknown as { secondary: unknown }).secondary = { kind: 'kick', name: 'x' };
    expect(() => validateWeapons(e)).toThrow(/secondary.kind/);
    // 61라운드: 4동사 표시 · 숨 갈래 · 옛 hitbox 대신 연격 반경
    const f = clone();
    delete (f.katana.verbs as Partial<typeof f.katana.verbs>).hold;
    expect(() => validateWeapons(f)).toThrow(/verbs.hold/);
    const g = clone();
    (g.bow.gauge as { branch?: string }).branch = 'nope';
    expect(() => validateWeapons(g)).toThrow(/gauge.branch/);
    const h = clone();
    delete h.dagger.combo!.radiusPx;
    expect(() => validateWeapons(h)).toThrow(/radiusPx/);
  });
});
