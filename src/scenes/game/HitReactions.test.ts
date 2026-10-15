import { describe, expect, it, vi } from 'vitest';
import { EventEmitter } from 'node:events';

// EventBus 가 Phaser 를 import 하므로(window 필요) 이벤트 이미터만 node 것으로 대체한다
vi.mock('phaser', () => ({ default: { Events: { EventEmitter } } }));

import { EventBus, Events } from '../../core/EventBus';
import { REACTION, TILE } from '../../core/Constants';
import { strikeReaction, wallSlamDamage, type StrikeReaction } from '../../systems/reactions';
import { WEAPONS } from '../../data';
import type { Mob } from '../../objects/Mob';
import type { Game } from '../Game';
import { HitReactions } from './HitReactions';

/** Mob 이 HitReactions 에 보여 주는 면만 흉내 낸다 (넉백은 즉시 시작 속도비 1) */
function fakeMob(id: string, x: number, y: number, o: { poise?: number; elite?: boolean; boss?: boolean } = {}) {
  const m = {
    active: true,
    spriteId: id,
    x,
    y,
    hp: 14,
    maxHp: 14,
    isBoss: Boolean(o.boss),
    elite: o.elite ? { prefix: 'p', name: 'n' } : null,
    stunImmune: false,
    flight: null as Mob['flight'],
    air: null as { until: number; extends: number } | null,
    staggerMs: 0,
    shoveArgs: null as null | { x: number; y: number; dist: number },
    body: {
      center: { x, y },
      halfWidth: 5,
      halfHeight: 5,
      bottom: y + 5,
      blocked: { none: true, left: false, right: false, up: false, down: false },
      reset: (nx: number, ny: number) => {
        m.x = nx;
        m.y = ny;
      },
    },
    get airState() {
      return m.air;
    },
    extendAir(n: { until: number; extends: number }) {
      m.air = n;
      return true;
    },
    poiseAgainst: () => o.poise ?? 0,
    canLaunch: () => !m.isBoss,
    launch(ms: number) {
      m.air = { until: ms, extends: 0 };
      return true;
    },
    canStagger: () => !m.isBoss,
    stagger(ms: number) {
      m.staggerMs = Math.max(m.staggerMs, ms);
    },
    shove(dx: number, dy: number, dist: number) {
      m.shoveArgs = { x: dx, y: dy, dist };
    },
    get shoveDir() {
      return m.shoveArgs ? { x: m.shoveArgs.x, y: m.shoveArgs.y } : null;
    },
    shoveSpeedRatio: 1,
    stopShove() {
      m.shoveArgs = null;
      m.flight = null;
    },
  };
  return m;
}
type FakeMob = ReturnType<typeof fakeMob>;

function fakeGame(mobs: FakeMob[], opts: { wallX?: number; fallX?: number } = {}) {
  const hits: { id: string; dmg: number }[] = [];
  const kills: { id: string; kind: string }[] = [];
  const g = {
    time: { now: 0 },
    scene: { isActive: () => true },
    mobs: { getChildren: () => mobs },
    world: {
      isWalkableAt: (x: number) => opts.wallX === undefined || x < opts.wallX,
      fallZoneAt: (x: number) => (opts.fallX !== undefined && x >= opts.fallX ? 'water' : null),
    },
    structures: { caskAt: () => false, burstCasksIn: () => 0 },
    combat: {
      hitMob: (m: FakeMob, dmg: number) => {
        hits.push({ id: m.spriteId, dmg });
        m.hp -= dmg;
        if (m.hp <= 0) m.active = false;
        return m.hp <= 0;
      },
    },
    progress: { onKill: (m: FakeMob, kind: string) => kills.push({ id: m.spriteId, kind }) },
    shake: { add: () => {} },
    hitFx: { knockDust: () => {} },
    hitStop: { request: () => true },
  };
  return { g: g as unknown as Game, hits, kills, raw: g };
}

/** 이벤트 기록 (이름 순서) */
function record(): { list: [string, unknown][]; stop: () => void } {
  const list: [string, unknown][] = [];
  const names = [
    Events.ENEMY_STAGGERED,
    Events.ENEMY_KNOCKED,
    Events.ENEMY_WALL_SLAM,
    Events.ENEMY_BOWLED,
    Events.ENEMY_LAUNCHED,
    Events.ENEMY_FELL,
    Events.COMBO_STREAK,
  ];
  const fns = names.map((n) => {
    const f = (p: unknown) => list.push([n, p]);
    EventBus.on(n, f);
    return [n, f] as const;
  });
  return { list, stop: () => fns.forEach(([n, f]) => EventBus.off(n, f)) };
}

const asMob = (m: FakeMob) => m as unknown as Mob;
const hit = (dmg = 10) => ({ dmg, nx: 1, ny: 0, knock: true });
const tier = (t: 1 | 2 | 3, power = t): StrikeReaction => ({ tier: t, launch: false, power, launchMaxPoise: 0 });

describe('P19 HitReactions — 반응 이벤트', () => {
  it('버팀 0 징집병: 1단계 타 → 움찔(flinch) + 밀림(KNOCKED 1) · 날림 상태 없음', () => {
    const m = fakeMob('dummy', 100, 100);
    const { g } = fakeGame([m]);
    const r = record();
    new HitReactions(g).apply(asMob(m), tier(1), hit());
    r.stop();
    expect(r.list.map((e) => e[0])).toEqual([Events.ENEMY_STAGGERED, Events.ENEMY_KNOCKED]);
    expect(r.list[0][1]).toMatchObject({ kind: 'flinch', ms: REACTION.FLINCH_MS });
    expect(r.list[1][1]).toMatchObject({ tier: 1, distTiles: REACTION.KNOCK[1].TILES });
    expect(m.flight).toBeNull();
  });

  it('버팀 1 결사병 측후: 1단계는 버팀 · 단검(버팀 무시 1)은 버팀이 깨짐(stagger)', () => {
    const m = fakeMob('charger', 100, 100, { poise: 1 });
    const { g } = fakeGame([m]);
    const hr = new HitReactions(g);
    const r = record();
    hr.apply(asMob(m), tier(1), hit());
    expect(r.list.some((e) => e[0] === Events.ENEMY_STAGGERED)).toBe(false);
    hr.apply(asMob(m), strikeReaction(WEAPONS.dagger.feel?.reaction, { kind: 'attack', comboIndex: 0 }), hit());
    r.stop();
    expect(r.list.find((e) => e[0] === Events.ENEMY_STAGGERED)?.[1]).toMatchObject({ kind: 'stagger' });
  });

  it('칼 1타 띄움: 버팀 0 은 LAUNCHED (넉백 없음) · 공중에서 맞으면 체공 연장 · 버팀 1 은 띄우지 않는다', () => {
    const light = fakeMob('dummy', 100, 100);
    const heavy = fakeMob('porter', 200, 100, { poise: 1 });
    const { g } = fakeGame([light, heavy]);
    const hr = new HitReactions(g);
    const rise = strikeReaction(WEAPONS.katana.feel?.reaction, { kind: 'attack', comboIndex: 0 });
    const r = record();
    hr.apply(asMob(light), rise, hit());
    hr.apply(asMob(heavy), rise, hit());
    r.stop();
    expect(r.list.filter((e) => e[0] === Events.ENEMY_LAUNCHED)).toHaveLength(1);
    expect(light.shoveArgs).toBeNull();
    expect(heavy.air).toBeNull();
    const before = light.air!.until;
    hr.apply(asMob(light), tier(1), hit());
    expect(light.air!.until).toBe(before + REACTION.LAUNCH.EXTEND_MS);
  });

  it('벽꽝: 2단계 날림이 벽에 닿으면 KNOCKED → WALL_SLAM 순서 · 속도 기반 추가 피해 · 쓰러짐', () => {
    const m = fakeMob('dummy', 100, 100);
    m.hp = 100;
    const { g, hits } = fakeGame([m], { wallX: 100 + 5 + REACTION.WALL_SLAM.PROBE_PAD_PX - 1 });
    const hr = new HitReactions(g);
    const r = record();
    hr.apply(asMob(m), tier(2), hit(10));
    hr.update();
    r.stop();
    expect(r.list.map((e) => e[0])).toEqual([Events.ENEMY_STAGGERED, Events.ENEMY_KNOCKED, Events.ENEMY_WALL_SLAM]);
    expect(r.list[2][1]).toMatchObject({ surface: 'wall', bonusDamage: wallSlamDamage(10, 1) });
    expect(hits).toEqual([{ id: 'dummy', dmg: wallSlamDamage(10, 1) }]);
    expect(m.staggerMs).toBe(REACTION.WALL_SLAM.DOWN_MS);
    expect(m.flight).toBeNull();
  });

  it('1단계 밀림은 벽에 닿아도 벽꽝이 아니다', () => {
    const m = fakeMob('dummy', 100, 100);
    const { g } = fakeGame([m], { wallX: 104 });
    const hr = new HitReactions(g);
    const r = record();
    hr.apply(asMob(m), tier(1), hit());
    hr.update();
    r.stop();
    expect(r.list.some((e) => e[0] === Events.ENEMY_WALL_SLAM)).toBe(false);
  });

  it('볼링: 3단계 날림이 다른 적과 닿으면 BOWLED · 둘 다 40% · 맞은 적은 1칸 밀리며 연쇄를 잇는다', () => {
    const a = fakeMob('dummy', 100, 100);
    const b = fakeMob('archer', 111, 100);
    a.hp = b.hp = 100;
    const { g, hits } = fakeGame([a, b]);
    const hr = new HitReactions(g);
    const r = record();
    hr.apply(asMob(a), tier(3), hit(10));
    hr.update();
    r.stop();
    const bowled = r.list.find((e) => e[0] === Events.ENEMY_BOWLED);
    expect(bowled?.[1]).toMatchObject({ hitter: 'dummy', target: 'archer', damage: 4 });
    expect(hits.map((h) => h.id).sort()).toEqual(['archer', 'dummy']);
    expect(b.shoveArgs?.dist).toBeCloseTo(REACTION.BOWL.PUSH_TILES * TILE);
    expect(b.flight?.chain).toBe(1);
    expect(a.flight).toBeNull();
  });

  it('낙하 구역: 날아가 떨어지면 FELL + 즉사(감각 환경) · 정예는 30% 피해 뒤 뒤로 돌아온다', () => {
    const m = fakeMob('dummy', 100, 100);
    const e = fakeMob('charger', 100, 200, { elite: true });
    e.hp = e.maxHp = 50;
    const { g, kills } = fakeGame([m, e], { fallX: 106 });
    const hr = new HitReactions(g);
    const r = record();
    hr.apply(asMob(m), tier(2), hit());
    hr.apply(asMob(e), tier(2), hit());
    hr.update();
    r.stop();
    expect(r.list.filter((x) => x[0] === Events.ENEMY_FELL)).toHaveLength(2);
    expect(kills).toEqual([{ id: 'dummy', kind: 'environment' }]);
    expect(e.hp).toBe(50 - Math.round(50 * REACTION.FALL.ELITE_HP_RATIO));
  });

  it('보스: 움찔·띄움·날림 상태 없음 (넉백만 ¼)', () => {
    const m = fakeMob('boss', 100, 100, { boss: true });
    const { g } = fakeGame([m]);
    const r = record();
    new HitReactions(g).apply(asMob(m), { ...tier(3), launch: true }, hit());
    r.stop();
    expect(r.list.map((e) => e[0])).toEqual([Events.ENEMY_KNOCKED]);
    expect(m.flight).toBeNull();
    expect(m.shoveArgs?.dist).toBeCloseTo(REACTION.KNOCK[3].TILES * TILE * REACTION.BOSS_MULT);
  });

  it('연속 처치: 1.5초 안 두 번째 처치부터 COMBO_STREAK', () => {
    const { g, raw } = fakeGame([]);
    const hr = new HitReactions(g);
    const r = record();
    hr.onEnemyDied();
    raw.time.now = 1200;
    hr.onEnemyDied();
    raw.time.now = 5000;
    hr.onEnemyDied();
    r.stop();
    expect(r.list).toEqual([[Events.COMBO_STREAK, { count: 2, windowMs: REACTION.STREAK.WINDOW_MS }]]);
  });
});
