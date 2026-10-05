import { describe, expect, it, vi } from 'vitest';
import { EventEmitter } from 'node:events';
import { AUDIO_TRIGGERS, SFX } from './audioMap';
import { BUILD_SFX, PASSIVE_SFX, katanaThrustSfx, nextRapidVariant } from './audioBuild';
import { Events } from '../../core/EventBus';
import { withAttackTag } from '../build/attackTags';

vi.mock('phaser', () => ({ default: { Events: { EventEmitter } } }));

const fire = (event: string, payload: unknown) =>
  AUDIO_TRIGGERS.filter((tr) => tr.event === event && (!tr.when || tr.when(payload)));
const ids = (event: string, payload: unknown) =>
  fire(event, payload)
    .map((tr) => (typeof tr.sfx === 'function' ? tr.sfx(payload) : tr.sfx))
    .filter(Boolean);

describe('60라운드 효과음 연결 (audioBuild)', () => {
  it('potion_use 는 독주 회복(PLAYER_HEALED source potion)만 — POTION_USED 는 무음', () => {
    expect(ids(Events.PLAYER_HEALED, { source: 'potion' })).toEqual([SFX.potionUse]);
    expect(ids(Events.PLAYER_HEALED, { source: 'rest' })).toEqual([]);
    expect(ids(Events.PLAYER_HEALED, {})).toEqual([]);
    expect(ids(Events.POTION_USED, { potions: 1 })).toEqual([]);
  });

  it('각성은 awaken_<무기> (evolve 대신), 일반 개성 변화는 evolve', () => {
    expect(ids(Events.WEAPON_EVOLVED, { weapon: 'bow', kind: 'awaken' })).toEqual([
      [BUILD_SFX.awaken('bow'), 'sfx/evolve'],
    ]);
    expect(ids(Events.WEAPON_EVOLVED, { weapon: 'bow', kind: 'branch' })).toEqual([SFX.evolve]);
  });

  it('세트 2·4·6 단 · 저주(피의 계약) · 엘리트 사망 · 상점 그룹 · 이벤트 메뉴', () => {
    expect(ids(Events.TAG_SET_CHANGED, { tag: 'chain', stage: 4, prev: 3, delta: 1 })).toEqual([BUILD_SFX.setTier(2)]);
    expect(ids(Events.TAG_SET_CHANGED, { tag: 'chain', stage: 3, prev: 2, delta: 1 })).toEqual([]);
    expect(ids(Events.CURSE_GAINED, { id: 'credit', source: 'bloodPact' })).toEqual([BUILD_SFX.bloodPact]);
    expect(ids(Events.CURSE_GAINED, { id: 'credit', source: 'event' })).toEqual([BUILD_SFX.curseTake]);
    expect(ids(Events.ENEMY_DIED, { id: 'dummy', elite: true })).toEqual([[BUILD_SFX.eliteDie, SFX.enemyDeath]]);
    expect(ids(Events.SHOP_BOUGHT, { id: 'reroll', price: 15, group: 'reroll' })).toEqual([BUILD_SFX.shopReroll]);
    expect(ids(Events.SHOP_BOUGHT, { id: 'heal', price: 15 })).toEqual([SFX.shopBuy]);
    expect(ids(Events.MENU_SELECTED, { id: 'event', key: '1' })).toEqual([[BUILD_SFX.eventChoice, SFX.menuSelect]]);
  });

  it('성소 깃발은 door_close·trial_clear 대신 shrine_*', () => {
    expect(ids(Events.CHALLENGE_STARTED, { id: 'x', kind: 'warFlag' })).toEqual([BUILD_SFX.shrineActivate]);
    expect(ids(Events.CHALLENGE_CLEARED, { id: 'x', kind: 'warFlag', outcome: 'flawless' })).toEqual([
      BUILD_SFX.shrineClear,
    ]);
    expect(ids(Events.CHALLENGE_STARTED, { id: 'x', kind: 'dogRing' })).toEqual([SFX.doorClose]);
  });

  it('갈래 효과 · 루프 시작/끝 · 천공 연결 스택', () => {
    expect(ids(Events.BRANCH_EFFECT, { branch: 'zangetsu', effect: 'trail' })).toEqual([BUILD_SFX.katanaMoonTrail]);
    expect(ids(Events.BRANCH_EFFECT, { branch: 'skypierce', effect: 'link', stack: 2 })).toEqual([
      BUILD_SFX.bowLink(2),
    ]);
    const start = fire(Events.BRANCH_EFFECT, { branch: 'clot', effect: 'hold' });
    expect(start.some((tr) => tr.loop === BUILD_SFX.gsCongestLoop)).toBe(true);
    const burst = { branch: 'clot', effect: 'burst' };
    expect(fire(Events.BRANCH_EFFECT, burst).some((tr) => tr.stop?.includes(BUILD_SFX.gsCongestLoop))).toBe(true);
    expect(ids(Events.BRANCH_EFFECT, burst)).toEqual([BUILD_SFX.gsCongestBurst]);
  });

  it('패시브 발동 (독한 숨 술불 = fire_breath)', () => {
    expect(ids(Events.PASSIVE_PROC, { passive: 'domino' })).toEqual([PASSIVE_SFX.domino]);
    expect(ids(Events.PASSIVE_PROC, { passive: 'harshBreath', fire: true })).toEqual(['sfx/passive_fire_breath']);
    expect(ids(Events.PASSIVE_PROC, { passive: 'unknown' })).toEqual([]);
  });

  it('칼 찌르기 검기 단 · 속사 1→2→3 순환 (bow_shot 대신)', () => {
    expect(katanaThrustSfx(0)).toEqual([BUILD_SFX.katanaThrust]);
    expect(katanaThrustSfx(5)).toEqual([BUILD_SFX.katanaThrustKi(3), BUILD_SFX.katanaThrust]);
    const a = nextRapidVariant();
    const b = nextRapidVariant();
    expect(b).toBe((a % 3) + 1);
    const rapid = withAttackTag('rapidVolley', () =>
      fire(Events.PLAYER_ATTACKED, { kind: 'attack', releaseDelayMs: 0 }),
    );
    expect(rapid.length).toBeGreaterThan(0);
  });

  it('결정타 · 파훼 새 종류', () => {
    expect(ids(Events.BOSS_BREAK, { kind: 'cup', distinct: true, count: 1 })).toEqual([BUILD_SFX.breakCount]);
    expect(ids(Events.BOSS_BREAK, { kind: 'cup', distinct: false, count: 1 })).toEqual([]);
    expect(ids(Events.BOSS_BREAK, { kind: 'finisher', distinct: false, count: 2 })).toEqual([BUILD_SFX.breakFinisher]);
  });
});
