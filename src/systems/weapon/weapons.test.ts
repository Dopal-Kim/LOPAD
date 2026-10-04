import { describe, expect, it } from 'vitest';
import { WEAPONS, WEAPON_RULES } from '../../data';
import { WeaponState } from './weapons';

describe('WeaponState (27라운드 분기 트리 → 57라운드 갈래 24노드)', () => {
  it('임계 도달 시 선택 대기가 되고 게이지는 멈춘다', () => {
    const w = new WeaponState('katana', WEAPONS.katana);
    expect(w.threshold).toBe(100);
    expect(w.gainPersonality(60)).toBe(false);
    expect(w.personality).toBe(60);
    expect(w.gainPersonality(50)).toBe(true);
    expect(w.choicePending).toBe(true);
    expect(w.personality).toBe(100);
    expect(w.stage).toBe(0);
    expect(w.gainPersonality(30)).toBe(false); // 선택 전엔 더 쌓이지 않음
    expect(w.personality).toBe(100);
    expect(w.options.map((o) => o.id)).toEqual(['iai', 'batto']);
  });

  it('1단 선풍 → 다음 임계 200 에서 2단 선택지는 선풍의 자식 (회오리·잔월)', () => {
    const w = new WeaponState('katana', WEAPONS.katana);
    w.gainPersonality(100);
    expect(w.choose('zangetsu')).toBeNull(); // 2단 노드는 아직 못 고름
    const node = w.choose('iai');
    expect(node?.name).toContain('선풍');
    expect(node?.move).toBe('spin');
    expect(node?.tags).toEqual(['chain', 'ranged']);
    expect(w.stage).toBe(1);
    expect(w.personality).toBe(0);
    expect(w.choicePending).toBe(false);
    // 57라운드: 옛 갈래 배율 없음 (1.0) — 갈래는 '하는 일'을 바꾼다
    expect(w.damageMult).toBeCloseTo(WEAPONS.katana.damageMult);
    expect(w.threshold).toBe(200);
    expect(w.gainPersonality(199)).toBe(false);
    expect(w.gainPersonality(1)).toBe(true);
    expect(w.options.map((o) => o.id)).toEqual(['vortex', 'zangetsu']);
    expect(w.choose('batto')).toBeNull();
    w.choose('zangetsu');
    expect(w.stage).toBe(2);
    expect(w.path).toEqual(['iai', 'zangetsu']);
    expect(w.evolution?.rule?.kind).toBe('zangetsu');
    expect(w.options).toEqual([]); // 트리 끝
    expect(w.displayName).toBe('사무라이 칼 · 잔월 (殘月)');
  });

  it('강화는 피해·범위 +15% 를 누적하고 단계는 유지한다', () => {
    const w = new WeaponState('greatsword', WEAPONS.greatsword);
    w.gainPersonality(100);
    w.choose('weight');
    const dmg1 = w.damageMult;
    w.gainPersonality(200);
    expect(w.reinforceNow()).toBe(true);
    expect(w.stage).toBe(1);
    expect(w.reinforce).toBe(1);
    expect(w.personality).toBe(0);
    expect(w.damageMult).toBeCloseTo(dmg1 * 1.15);
    expect(w.hitbox.width).toBeCloseTo(WEAPONS.greatsword.hitbox.width * 1.15);
    expect(w.threshold).toBe(200); // 다음 임계 그대로
    expect(w.options.map((o) => o.id)).toEqual(['giant', 'clot']); // 다시 3지선다
    expect(w.displayName).toBe('대검 · 중압 (重壓) +1');
  });

  it('강화 최대 3회 — 트리가 끝나도 칸 계산이 열려 있으면 게이지가 돈다 (57 Q37 · 각성 후 상한 5)', () => {
    const w = new WeaponState('bow', WEAPONS.bow);
    w.gainPersonality(100);
    w.choose('rapid');
    w.gainPersonality(200);
    w.choose('quiver');
    for (let i = 0; i < WEAPON_RULES.reinforceMax; i++) {
      expect(w.canEvolve).toBe(true);
      expect(w.gainPersonality(200)).toBe(true);
      expect(w.reinforceNow()).toBe(true);
    }
    expect(w.reinforce).toBe(3);
    expect(w.canReinforce).toBe(false);
    expect(w.canEvolve).toBe(false);
    expect(w.gainPersonality(500)).toBe(false);
    // 피의 계약·각성 칸이 열려 있으면 (Progression 이 칸 계산으로 넘김)
    expect(w.gainPersonality(500, true)).toBe(true);
    w.consumeChoice();
    expect(w.personality).toBe(0);
    expect(w.choicePending).toBe(false);
    expect(w.reinforceNow()).toBe(false);
    w.reinforceCapOverride = 5;
    expect(w.reinforceNow()).toBe(true);
    expect(w.reinforce).toBe(4);
    expect(w.mods.fireRateMult).toBeCloseTo(1.43);
    expect(w.mods.magazineBonus).toBe(12);
  });

  it('세이브 복원: 경로·강화·선택 대기, 모르는 id(옛 갈래 포함)는 잘라낸다', () => {
    const w = new WeaponState('dagger', WEAPONS.dagger);
    w.restore({ personality: 50, path: ['gale', 'flyknife'], reinforce: 2, choicePending: false });
    expect(w.path).toEqual(['gale', 'flyknife']);
    expect(w.reinforce).toBe(2);
    expect(w.mods.moveSpeedMult).toBe(1.15);
    const p = w.toProgress();
    const w2 = new WeaponState('dagger', WEAPONS.dagger);
    w2.restore(p);
    expect(w2.toProgress()).toEqual(p);
    const w3 = new WeaponState('dagger', WEAPONS.dagger);
    // 57라운드 삭제된 2단 (암살) 은 잘린다
    w3.restore({ personality: 0, path: ['gale', 'assassin'], reinforce: 9, choicePending: true });
    expect(w3.path).toEqual(['gale']);
    expect(w3.reinforce).toBe(WEAPON_RULES.reinforceMax);
    expect(w3.choicePending).toBe(true);
  });

  it('갈래 24노드: 무기당 1단 2 + 1단마다 2단 2, 1단은 새 동작, 노드마다 태그 1~2', () => {
    let n = 0;
    for (const w of Object.values(WEAPONS)) {
      expect(w.personality.branches).toHaveLength(2);
      for (const a of w.personality.branches) {
        n += 1;
        expect(typeof a.move).toBe('string');
        expect(a.tags!.length).toBeGreaterThanOrEqual(1);
        expect(a.next).toHaveLength(2);
        for (const b of a.next!) {
          n += 1;
          expect(b.tags!.length).toBeGreaterThanOrEqual(1);
          expect(b.tags!.length).toBeLessThanOrEqual(2);
        }
      }
    }
    expect(n).toBe(24);
    // S-1 충돌 해소: 철벽·암살·칼 2단 급소 삭제, 활 2단 관통 → 천공
    const ids = Object.values(WEAPONS).flatMap((w) =>
      w.personality.branches.flatMap((a) => [a.id, ...(a.next ?? []).map((b) => b.id)]),
    );
    for (const gone of ['ironwall', 'assassin', 'dashcrit', 'pierce']) expect(ids).not.toContain(gone);
    expect(ids).toContain('skypierce');
  });
});
