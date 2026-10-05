/**
 * 54라운드 1층 '만취' 패턴 모듈 단위 테스트 (가짜 보스·가짜 방 — Phaser 없음).
 */
import { describe, expect, it } from 'vitest';
import { BOSSES } from '../../data';
import type { BossPatternName } from '../../data/bossPatterns';
import { Rng } from '../../systems/rng';
import type { MobContext } from '../Mob';
import { BossBrain } from './BossBrain';
import { caskAngles } from './patterns/caskRoll';
import { reelTelegraphMs } from './patterns/drunkDash';
import { spillArms } from './patterns/fireSpill';
import type { BossArenaApi, BossHost, BossPoseApi } from './types';

const DEF = BOSSES.stage1;

interface Rec {
  t: number;
  e: string;
}

function harness(opts: { phase?: number; force?: BossPatternName[] } = {}) {
  const log: Rec[] = [];
  let time = 0;
  const ev = (e: string) => log.push({ t: time, e });
  let invulnUntil = 0;
  let stunnedFor = 0;
  let weak: { onHit: () => void } | null = null;
  const boss = { x: 0, y: 0, blocked: false };
  const player = { x: 80, y: 0 };
  const arena: BossArenaApi = {
    startTilt: (p) => ev(`tilt:${p.durationMs}:${p.tiltDeg}`),
    tilting: false,
    lightsOut: (p) => ev(`dark:${p.durationMs}:${p.darkAmbient}`),
    dark: false,
    traceCask: (from) => [from, { x: from.x + 10, y: from.y }],
    kickCask: (_f, dx, dy) => ev(`kick:${dx.toFixed(2)},${dy.toFixed(2)}`),
    spill: (pts) => ev(`spill:${pts.length}`),
    caskRadiusPx: (fallback) => fallback,
    throwTorch: (_f, _t, ms) => ev(`torch:${ms}`),
    setWeakPoint: (wp) => {
      weak = wp;
      ev(wp ? 'weak:on' : 'weak:off');
    },
  };
  const pose: BossPoseApi = {
    dashTelegraph: () => {},
    dashLoop: () => {},
    recover: () => {},
    holdFacing: () => {},
    release: () => {},
    phase: () => false,
    play: () => false,
    keyFrameMs: () => null,
    lean: () => {},
    lie: (on) => ev(`lie:${on}`),
    cupRect: () => ({ x: -5, y: -50, w: 10, h: 10 }),
    anchor: () => null,
    recoverHoldMs: () => 0,
    cupArt: false,
    facing: 'down',
  };
  const host: BossHost = {
    id: 'stage1',
    def: DEF,
    get phaseIndex() {
      return brain.phaseIndex;
    },
    rng: new Rng(7),
    get pos() {
      return { x: boss.x, y: boss.y };
    },
    get center() {
      return { x: boss.x, y: boss.y };
    },
    halfWidth: 20,
    pose,
    params: (n) => brain.params(n),
    inPick: (n) => brain.inPick(n),
    isReady: (n, c) => brain.isReady(n, c),
    readyAt: (n) => brain.readyAt(n),
    setReadyAt: (n, a) => brain.setReadyAt(n, a),
    scheduleNext: (t) => brain.scheduleNext(t),
    setVelocity: () => {},
    get blocked() {
      return boss.blocked;
    },
    angleTo: (x, y) => Math.atan2(y - boss.y, x - boss.x),
    paint: () => {},
    restoreColor: () => {},
    setInvulnerable: (u) => (invulnUntil = u),
    markBroken: (ms) => ev(`broken:${ms}`),
    addSummoned: () => {},
    emitTelegraph: (n) => ev(`telegraph:${n}`),
    emitAttack: (n) => ev(`attack:${n}`),
    emitAction: (a, i) => ev(`action:${a}${i === undefined ? '' : ':' + i}`),
    emitLoop: (l, on) => ev(`loop:${l}:${on}`),
    emitWallHit: () => ev('wall'),
  };
  const brain: BossBrain = new BossBrain(DEF, host, {
    approach: () => {},
    stunSelf: (_t, ms) => {
      stunnedFor = ms;
      ev(`stun:${ms}`);
    },
    releasePose: () => {},
    emitPhase: (i) => ev(`phase:${i + 1}`),
  });
  const begin = brain.begin.bind(brain);
  brain.begin = (p, ctx) => {
    ev(`begin:${p}`);
    begin(p, ctx);
  };
  if (opts.phase) brain.setPhase(opts.phase - 1);
  if (opts.force) brain.force(opts.force);
  const mark = { aim: () => {}, end: () => {}, active: true, setPoints: () => {}, kind: 'line' };
  const ctx = (): MobContext =>
    ({
      time,
      delta: 16,
      player,
      fire: () => {},
      telegraph: {
        line: () => mark,
        circle: () => mark,
        cone: () => mark,
        path: (_p: unknown, ms: number) => {
          ev(`path:${ms}`);
          return mark;
        },
      },
      playFx: () => {},
      countMobs: () => 0,
      areaHit: (_x: number, _y: number, r: number, a: number) => ev(`area:${r}:${a}`),
      summon: () => true,
      pack: {},
      arena,
    }) as unknown as MobContext;
  const tick = (ms: number, each?: () => void) => {
    const end = time + ms;
    for (; time < end; time += 16) {
      each?.();
      if (brain.nextPatternAt === 0) brain.scheduleNext(time);
      if (time < stunUntil()) continue;
      brain.update(ctx());
    }
  };
  let stunAt = 0;
  const stunUntil = () => (stunnedFor > 0 ? stunAt + stunnedFor : 0);
  return {
    log,
    brain,
    tick,
    get time() {
      return time;
    },
    get invulnUntil() {
      return invulnUntil;
    },
    hitCup: () => {
      stunAt = time;
      weak?.onHit();
    },
    boss,
    events: (prefix: string) => log.filter((r) => r.e.startsWith(prefix)),
  };
}

describe('1층 데이터 (61라운드 P6 재구성)', () => {
  it('HP 1100 · 국면 100~65 / 65~30 / 30~ · 국면마다 패턴 추가 · 부채꼴·소환 없음', () => {
    expect(DEF.hp).toBe(1100);
    expect(DEF.phases.map((p) => p.hpFraction)).toEqual([1, 0.65, 0.3]);
    for (const p of DEF.phases) {
      expect(p.pick).not.toContain('fan');
      expect(p.pick).not.toContain('summon');
      // 세상이 돈다·등불 끄기는 고르는 패턴이 아니다 (국면 전환 연출·3국면 진입 확정)
      expect(p.pick).not.toContain('spin');
      expect(p.pick).not.toContain('lightsOut');
    }
    expect(DEF.phases[0].pick).toEqual(['dash', 'slam', 'caskRoll']);
    expect(DEF.phases[1].pick).toEqual(['dash', 'slam', 'caskRoll', 'drink', 'fireSpill']);
    expect(DEF.phases[2].pick).toEqual([...DEF.phases[1].pick, 'drunkDash']);
    expect(DEF.phases[2].intervalMs).toBeLessThan(DEF.phases[1].intervalMs);
    expect(DEF.phases[1].enterPattern).toBe('spin');
    expect(DEF.phases[2].enterPattern).toBe('spin');
    expect(DEF.breakDamageMult).toBe(1.5);
  });
});

describe('한 잔 더 (Q6)', () => {
  it('얼큰: 다 마시면 다음 패턴 강화 (돌진 강화 수치)', () => {
    const h = harness({ force: ['drink', 'dash'] });
    const P = h.brain.params<{ liftMs: number; gulpMs: number; finishMs: number }>('drink');
    h.tick(DEF.phases[0].intervalMs + P.liftMs + P.gulpMs + P.finishMs + 100);
    expect(h.events('weak:on')).toHaveLength(1);
    expect(h.events('weak:off').length).toBeGreaterThanOrEqual(1);
    expect(h.brain.empowered).toBe(true);
    h.tick(DEF.phases[0].intervalMs + 50);
    expect(h.brain.current).toBe('dash');
    expect(h.brain.runEmpowered).toBe(true);
    expect(h.brain.params<{ speedTiles: number }>('dash').speedTiles).toBe(20);
  });

  it('만취: 다 마시면 다음 패턴 강화 (화면 패턴은 부르지 않는다 — 61라운드)', () => {
    const h = harness({ phase: 2, force: ['drink'] });
    const P = h.brain.params<{ liftMs: number; gulpMs: number; finishMs: number }>('drink');
    h.tick(DEF.phases[1].intervalMs + P.liftMs + P.gulpMs + P.finishMs + 100);
    expect(h.events('tilt:')).toHaveLength(0);
    expect(h.events('begin:spin')).toHaveLength(0);
    expect(h.brain.empowered).toBe(true);
  });

  it('들이켜는 동안 잔을 맞히면 3초 경직, 화면 패턴 취소', () => {
    const h = harness({ phase: 2, force: ['drink'] });
    const P = h.brain.params<{ liftMs: number }>('drink');
    h.tick(DEF.phases[1].intervalMs + P.liftMs + 300);
    expect(h.brain.state).toBe('drinkGulp');
    h.hitCup();
    h.tick(50);
    expect(h.events('stun:')).toEqual([expect.objectContaining({ e: 'stun:3000' })]);
    expect(h.events('broken:')).toEqual([expect.objectContaining({ e: 'broken:3000' })]);
    expect(h.events('action:cupBreak')).toHaveLength(1);
    expect(h.events('loop:gulp:false')).toHaveLength(1);
    expect(h.events('tilt:')).toHaveLength(0);
    expect(h.events('begin:spin')).toHaveLength(0);
  });

  it('인사불성: 다 마셔도 등불 끄기는 없다 (3국면 진입 때 한 번 확정)', () => {
    const h = harness({ phase: 3, force: ['drink'] });
    const P = h.brain.params<{ liftMs: number; gulpMs: number; finishMs: number }>('drink');
    h.tick(DEF.phases[2].intervalMs + P.liftMs + P.gulpMs + P.finishMs + 100);
    expect(h.events('begin:lightsOut')).toHaveLength(0);
  });
});

describe('3연 취권 돌진 (Q9)', () => {
  it('예고 600→350→350 (인사불성 500→300→300)', () => {
    expect([0, 1, 2].map((i) => reelTelegraphMs({ telegraphSeqMs: [600, 350, 350] }, i))).toEqual([600, 350, 350]);
    expect(reelTelegraphMs({ telegraphSeqMs: [600] }, 2)).toBe(600);
    expect(reelTelegraphMs({}, 0)).toBe(500);
    const h = harness({ phase: 3, force: ['drunkDash'] });
    h.tick(DEF.phases[2].intervalMs + 20);
    h.tick(4000);
    expect(h.events('path:').map((r) => r.e)).toEqual(['path:500', 'path:300', 'path:300']);
  });

  it('세 번째 뒤 넘어져 2초 (접촉 피해 없음) → 끝', () => {
    const h = harness({ phase: 2, force: ['drunkDash', 'slam'] });
    h.tick(DEF.phases[1].intervalMs + 20);
    const P = h.brain.params<{ durationMs: number; fallMs: number }>('drunkDash');
    h.tick(600 + 350 + 350 + 3 * P.durationMs + 100);
    expect(h.brain.state).toBe('fall');
    expect(h.brain.contactAttack()).toBe(0);
    expect(h.events('action:reelDash').map((r) => r.e)).toEqual([
      'action:reelDash:0',
      'action:reelDash:1',
      'action:reelDash:2',
    ]);
    expect(h.events('broken:')).toEqual([expect.objectContaining({ e: `broken:${P.fallMs}` })]);
    h.tick(P.fallMs);
    expect(h.brain.state).toBe('approach');
  });

  it('돌진 중 벽·기둥에 막히면 벽 경직으로 끝', () => {
    const h = harness({ phase: 2, force: ['drunkDash'] });
    h.tick(DEF.phases[1].intervalMs + 620);
    expect(h.brain.state).toBe('reel');
    h.boss.blocked = true;
    h.tick(20);
    expect(h.events('wall')).toHaveLength(1);
    expect(h.brain.state).toBe('wallStun');
    const P = h.brain.params<{ wallStunMs: number }>('drunkDash');
    expect(h.events('broken:')).toEqual([expect.objectContaining({ e: `broken:${P.wallStunMs}` })]);
  });
});

describe('국면 전환 (Q1 → 61라운드 P6)', () => {
  it('65% 아래로 → 진행 중 패턴을 끊고 세상이 돈다(2.2초) + 들이켜기(무적), 화면 패턴은 그 뒤 없음', () => {
    const h = harness({ force: ['dash'] });
    h.tick(DEF.phases[0].intervalMs + 100);
    expect(h.brain.current).toBe('dash');
    expect(h.brain.checkPhase(0.64)).toBe(true);
    h.tick(20);
    expect(h.brain.current).toBe('phaseDrink');
    expect(h.invulnUntil).toBeGreaterThan(h.time);
    expect(h.events('phase:2')).toHaveLength(1);
    expect(h.events('tilt:')).toEqual([expect.objectContaining({ e: 'tilt:2200:8' })]);
    const D = h.brain.params<{ durationMs: number }>('phaseDrink');
    h.brain.force(null);
    h.tick(D.durationMs + 40);
    expect(h.events('begin:lightsOut')).toHaveLength(0);
  });

  it('30% 아래로 → 세상이 돈다 → 들이켜기 → 등불 끄기 확정 → 어둠 속 3연 취권', () => {
    const h = harness({ phase: 2 });
    h.tick(100);
    expect(h.brain.checkPhase(0.29)).toBe(true);
    h.tick(20);
    expect(h.events('phase:3')).toHaveLength(1);
    const D = h.brain.params<{ durationMs: number }>('phaseDrink');
    const L = h.brain.params<{ telegraphMs: number }>('lightsOut');
    h.tick(D.durationMs + L.telegraphMs + 60);
    const begins = h.events('begin:').map((r) => r.e);
    expect(begins).toEqual(
      expect.arrayContaining(['begin:spin', 'begin:phaseDrink', 'begin:lightsOut', 'begin:drunkDash']),
    );
    const order = ['begin:spin', 'begin:phaseDrink', 'begin:lightsOut', 'begin:drunkDash'].map((e) =>
      begins.indexOf(e),
    );
    expect(order).toEqual([...order].sort((a, b) => a - b));
    expect(h.events('dark:')).toHaveLength(1);
  });
});

describe('술독 굴리기 · 불붙은 술 · 등불 끄기 (Q3·Q8)', () => {
  it('술독 굴리기: 예고 뒤 걷어차기 (강화면 2개)', () => {
    expect(caskAngles(0, 1, 30)).toEqual([0]);
    expect(caskAngles(0, 2, 30).map((a) => +a.toFixed(3))).toEqual([-0.262, 0.262]);
    const h = harness({ force: ['caskRoll'] });
    const P = h.brain.params<{ telegraphMs: number }>('caskRoll');
    h.tick(DEF.phases[0].intervalMs + P.telegraphMs + 400);
    expect(h.events('kick:')).toHaveLength(1);
    expect(h.events('action:kick')).toHaveLength(1);
  });

  it('불붙은 술: 뿌리기 → 횃불', () => {
    const arms = spillArms({ x: 0, y: 0 }, 0, { lengthTiles: 9, wobbleTiles: 1, arms: 2, armSpreadDeg: 40 });
    expect(arms).toHaveLength(2);
    const h = harness({ phase: 2, force: ['fireSpill'] });
    const P = h.brain.params<{ telegraphMs: number; torchTelegraphMs: number; torchFlightMs: number }>('fireSpill');
    h.tick(DEF.phases[1].intervalMs + P.telegraphMs + 40);
    expect(h.events('spill:')).toHaveLength(1);
    expect(h.events('torch:')).toHaveLength(0);
    h.tick(P.torchTelegraphMs + 40);
    expect(h.events('torch:').map((r) => r.e)).toEqual([`torch:${P.torchFlightMs}`]);
  });

  it('등불 끄기: 원 예고 → 반경 피해 + 어둠 12초 → 어둠 속 3연 취권', () => {
    const h = harness({ phase: 3, force: ['lightsOut'] });
    const P = h.brain.params<{ telegraphMs: number; durationMs: number }>('lightsOut');
    h.tick(DEF.phases[2].intervalMs + P.telegraphMs + 40);
    expect(h.events('dark:')).toEqual([expect.objectContaining({ e: 'dark:12000:#2a2a36' })]);
    expect(h.events('area:')).toHaveLength(1);
    expect(h.events('begin:drunkDash')).toHaveLength(1);
  });
});
