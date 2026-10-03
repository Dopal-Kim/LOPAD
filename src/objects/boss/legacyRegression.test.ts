/**
 * 54라운드 Q4 회귀: 2~7층·황제 보스는 새 틀(BossBrain + 패턴 모듈 + bosses.json patterns.<이름>)로 옮겼지만
 * 수치·동작이 35라운드와 같아야 한다.
 * 1) 수치: 옛 bosses.json(고정본 __fixtures__/bosses.legacy.json)의 페이즈별 dash·fan·slam·summon·volley·간격·목록 = 새 해석값
 * 2) 동작: 옛 Boss.think switch 상태 머신을 그대로 옮긴 참조 구현과 새 두뇌를 같은 가짜 세계에서 돌려 사건 기록이 같다
 */
import { describe, expect, it } from 'vitest';
import legacyJson from './__fixtures__/bosses.legacy.json';
import { BOSSES } from '../../data';
import { phaseIndexFor, resolvePatternParams, type BossPatternName } from '../../data/bossPatterns';
import type { BossDef } from '../../data/types';
import { COLORS, ENEMY_FX, SPRITES, TILE } from '../../core/Constants';
import { Rng } from '../../systems/rng';
import type { MobContext } from '../Mob';
import { BossBrain } from './BossBrain';
import type { BossHost, BossPoseApi, Vec } from './types';

/* eslint-disable @typescript-eslint/no-explicit-any */
type LegacyPhase = {
  hpFraction: number;
  dash: Record<string, number>;
  fan: Record<string, any> | null;
  patterns?: string[];
  patternIntervalMs?: number;
};
type LegacyBoss = {
  hp: number;
  contactAttack: number;
  approachSpeedTiles: number;
  phases: LegacyPhase[];
  slam?: Record<string, number>;
  summon?: Record<string, any>;
  volley?: Record<string, any>;
};
const LEGACY = legacyJson as unknown as Record<string, LegacyBoss>;
const LEGACY_IDS = ['stage2', 'stage3', 'stage4', 'stage5', 'stage6', 'stage7', 'emperor'];

describe('54라운드 회귀 1: 2~7층·황제 수치가 옛 데이터와 같다', () => {
  for (const id of LEGACY_IDS) {
    it(id, () => {
      const old = LEGACY[id];
      const def = BOSSES[id];
      for (const k of ['hp', 'contactAttack', 'approachSpeedTiles'] as const) expect(def[k]).toBe(old[k]);
      expect(def.phases.length).toBe(old.phases.length);
      old.phases.forEach((ph, i) => {
        const np = def.phases[i];
        expect(np.hpFraction).toBe(ph.hpFraction);
        expect(np.intervalMs).toBe(ph.patternIntervalMs ?? ph.dash.intervalMs);
        expect(np.pick).toEqual(ph.patterns);
        expect(np.enterPattern).toBeUndefined();
        const dash = { ...ph.dash };
        delete dash.intervalMs;
        expect(resolvePatternParams(def, i, 'dash')).toEqual(dash);
        if (ph.fan) {
          const { intervalMs, ...rest } = ph.fan;
          expect(resolvePatternParams(def, i, 'fan')).toEqual({ ...rest, cooldownMs: intervalMs });
        } else expect(np.pick).not.toContain('fan');
        for (const k of ['slam', 'summon', 'volley'] as const)
          if (old[k]) expect(resolvePatternParams(def, i, k)).toEqual(old[k]);
      });
    });
  }
});

// ---------------------------------------------------------------------------
// 가짜 세계 (물리 = 속도 적분, 벽 = 사각 방 밖)
// ---------------------------------------------------------------------------

interface Ev {
  t: number;
  e: string;
}

class World {
  time = 0;
  readonly delta = 16;
  readonly log: Ev[] = [];
  readonly player = { x: 0, y: 0 };
  mobs = 0;
  /** 방 (월드 px) */
  readonly room = { x0: -130, y0: -85, x1: 130, y1: 85 };
  boss = { x: 0, y: 0, vx: 0, vy: 0, blocked: false };
  ev(e: string): void {
    this.log.push({ t: this.time, e });
  }
  step(): void {
    const b = this.boss;
    const nx = b.x + (b.vx * this.delta) / 1000;
    const ny = b.y + (b.vy * this.delta) / 1000;
    const R = this.room;
    b.blocked = nx < R.x0 || nx > R.x1 || ny < R.y0 || ny > R.y1;
    b.x = Math.max(R.x0, Math.min(R.x1, nx));
    b.y = Math.max(R.y0, Math.min(R.y1, ny));
  }
  /** 플레이어는 원을 그리며 돈다 (예고·돌진 방향이 바뀌게) */
  movePlayer(): void {
    const a = this.time / 1700;
    this.player.x = Math.cos(a) * 120;
    this.player.y = Math.sin(a * 1.3) * 70;
  }
  ctx(): MobContext {
    // eslint-disable-next-line @typescript-eslint/no-this-alias
    const w = this;
    const mark = (kind: string) => ({
      kind,
      aim: () => {},
      end: () => w.ev(`end:${kind}`),
      active: true,
      setPoints: () => {},
    });
    return {
      time: w.time,
      delta: w.delta,
      player: w.player,
      fire: (_x: number, _y: number, dx: number, dy: number, spec: { attack: number }) =>
        w.ev(`fire:${dx.toFixed(3)},${dy.toFixed(3)}:${spec.attack}`),
      telegraph: {
        line: (_x: number, _y: number, a: number, len: number, ms: number) => {
          w.ev(`tline:${a.toFixed(3)}:${len}:${ms}`);
          return mark('line');
        },
        circle: (x: number, y: number, r: number, ms: number) => {
          w.ev(`tcircle:${x.toFixed(1)},${y.toFixed(1)}:${r}:${ms}`);
          return mark('circle');
        },
        cone: (_x: number, _y: number, a: number, half: number, r: number, ms: number) => {
          w.ev(`tcone:${a.toFixed(3)}:${half.toFixed(3)}:${r}:${ms}`);
          return mark('cone');
        },
        path: () => mark('path'),
      } as unknown as MobContext['telegraph'],
      playFx: () => {},
      countMobs: () => w.mobs,
      areaHit: (x: number, y: number, r: number, atk: number) =>
        w.ev(`area:${x.toFixed(1)},${y.toFixed(1)}:${r}:${atk}`),
      summon: () => {
        w.mobs++;
        w.ev('summon1');
        return true;
      },
      pack: {} as MobContext['pack'],
      arena: null,
    };
  }
}

/** 몸 연출은 기록만 (35라운드 구현과 같은 호출 순서인지까지 본다) */
function fakePose(w: World): BossPoseApi {
  return {
    dashTelegraph: (_t, _tg, fit, first) => w.ev(`pose:tele:${fit}:${first}`),
    dashLoop: () => w.ev('pose:dash'),
    recover: (_t, ms) => w.ev(`pose:recover:${ms ?? '-'}`),
    holdFacing: (_t, _tg, ms) => w.ev(`pose:hold:${ms ?? '-'}`),
    release: () => w.ev('pose:release'),
    phase: () => false,
    play: () => false,
    keyFrameMs: () => null,
    lean: () => {},
    lie: () => {},
    cupRect: () => ({ x: 0, y: 0, w: 1, h: 1 }),
    anchor: () => null,
    recoverHoldMs: () => 0,
    cupArt: false,
    facing: 'down',
  };
}

// ---------------------------------------------------------------------------
// 35라운드 Boss.think 참조 구현 (옛 코드를 가짜 세계로 그대로 옮김 — 수치는 옛 JSON)
// ---------------------------------------------------------------------------

class LegacyBoss_ {
  phaseIndex = 0;
  state = 'approach';
  stateUntil = 0;
  nextPatternAt = 0;
  readyAt = new Map<string, number>();
  dashX = 1;
  dashY = 0;
  dashesLeft = 0;
  slamTarget = { x: 0, y: 0 };
  volleyX = 1;
  volleyY = 0;
  volleyLeft = 0;
  volleyNextAt = 0;
  current: string | null = null;
  hp: number;
  constructor(
    readonly def: LegacyBoss,
    readonly w: World,
    readonly rng: Rng,
  ) {
    this.hp = def.hp;
  }
  get P(): LegacyPhase {
    return this.def.phases[this.phaseIndex];
  }
  get c(): Vec {
    return { x: this.w.boss.x, y: this.w.boss.y };
  }
  vel(x: number, y: number): void {
    this.w.boss.vx = x;
    this.w.boss.vy = y;
  }
  angleTo(x: number, y: number): number {
    return Math.atan2(y - this.c.y, x - this.c.x);
  }
  think(ctx: MobContext): void {
    const w = this.w;
    if (this.nextPatternAt === 0) this.scheduleNext(ctx.time);
    const P = this.P;
    switch (this.state) {
      case 'approach': {
        const dx = ctx.player.x - this.c.x;
        const dy = ctx.player.y - this.c.y;
        const len = Math.hypot(dx, dy);
        const s = this.def.approachSpeedTiles * TILE;
        if (len * len > 1) this.vel((dx / len) * s, (dy / len) * s);
        else this.vel(0, 0);
        if (ctx.time >= this.nextPatternAt) this.begin(this.choose(ctx), ctx);
        break;
      }
      case 'telegraph':
        if (ctx.time >= this.stateUntil) {
          w.ev('end:line');
          const dx = ctx.player.x - this.c.x;
          const dy = ctx.player.y - this.c.y;
          const len = Math.hypot(dx, dy);
          this.dashX = len > 0 ? dx / len : 0;
          this.dashY = len > 0 ? dy / len : 0;
          this.state = 'dash';
          this.stateUntil = ctx.time + P.dash.durationMs;
          w.ev('paint:restore');
          w.ev('pose:dash');
          w.ev('attack:dash');
        }
        break;
      case 'dash': {
        const s = P.dash.speedTiles * TILE;
        this.vel(this.dashX * s, this.dashY * s);
        if (w.boss.blocked) {
          this.state = 'stun';
          this.stateUntil = ctx.time + P.dash.wallStunMs;
          this.vel(0, 0);
          w.ev(`paint:${COLORS.STUN}`);
          w.ev(`pose:recover:${P.dash.wallStunMs}`);
          this.scheduleNext(ctx.time);
          w.ev('wall');
        } else if (ctx.time >= this.stateUntil) {
          this.vel(0, 0);
          if (this.dashesLeft > 0) {
            this.dashesLeft -= 1;
            this.beginTelegraph(ctx, P.dash.telegraphMs * 0.5, false);
          } else {
            w.ev('pose:recover:-');
            this.finish(ctx.time);
            this.afterDash(ctx);
          }
        }
        break;
      }
      case 'stun':
        this.vel(0, 0);
        if (ctx.time >= this.stateUntil) {
          this.state = 'approach';
          w.ev('pose:release');
          w.ev('paint:restore');
          this.afterDash(ctx);
        }
        break;
      case 'fanTelegraph':
        this.vel(0, 0);
        if (ctx.time >= this.stateUntil) {
          w.ev('end:cone');
          this.fireFan(ctx);
          this.finish(ctx.time);
        }
        break;
      case 'slamTelegraph':
        this.vel(0, 0);
        if (ctx.time >= this.stateUntil) {
          w.ev('end:circle');
          const S = this.def.slam!;
          ctx.areaHit(this.slamTarget.x, this.slamTarget.y, S.radiusTiles * TILE, S.attack);
          w.ev('attack:slam');
          w.ev('pose:recover:-');
          this.finish(ctx.time);
        }
        break;
      case 'volleyTelegraph':
        this.vel(0, 0);
        if (ctx.time >= this.stateUntil) {
          w.ev('end:line');
          const dx = ctx.player.x - this.c.x;
          const dy = ctx.player.y - this.c.y;
          const len = Math.hypot(dx, dy);
          this.volleyX = len > 0 ? dx / len : 0;
          this.volleyY = len > 0 ? dy / len : 0;
          this.volleyLeft = this.def.volley!.count;
          this.volleyNextAt = ctx.time;
          this.state = 'volley';
          w.ev('attack:volley');
        }
        break;
      case 'volley': {
        this.vel(0, 0);
        const V = this.def.volley!;
        if (ctx.time >= this.volleyNextAt && this.volleyLeft > 0) {
          this.volleyLeft -= 1;
          this.volleyNextAt = ctx.time + V.shotGapMs;
          ctx.fire(0, 0, this.volleyX, this.volleyY, { attack: V.attack } as any);
        }
        if (this.volleyLeft <= 0) this.finish(ctx.time);
        break;
      }
      case 'recover':
        this.vel(0, 0);
        if (ctx.time >= this.stateUntil) this.finish(ctx.time);
        break;
    }
  }
  choose(ctx: MobContext): string {
    const ready = (this.P.patterns ?? []).filter((p) => this.isReady(p, ctx));
    if (ready.length === 0) return 'dash';
    return this.rng.pick(ready);
  }
  isReady(p: string, ctx: MobContext): boolean {
    if (ctx.time < (this.readyAt.get(p) ?? 0)) return false;
    if (p === 'fan') return Boolean(this.P.fan);
    if (p === 'summon') return ctx.countMobs('dummy') < this.def.summon!.max;
    return true;
  }
  begin(p: string, ctx: MobContext): void {
    this.current = p;
    this.w.ev(`begin:${p}`);
    if (p === 'dash') {
      this.dashesLeft = (this.P.dash.repeat ?? 1) - 1;
      this.beginTelegraph(ctx, this.P.dash.telegraphMs, true);
    } else if (p === 'fan') this.beginFan(ctx);
    else if (p === 'slam') this.beginSlam(ctx);
    else if (p === 'summon') this.doSummon(ctx);
    else if (p === 'volley') this.beginVolley(ctx);
  }
  finish(time: number): void {
    const p = this.current;
    if (p) this.readyAt.set(p, time + this.cooldown(p));
    this.current = null;
    this.state = 'approach';
    this.scheduleNext(time);
  }
  cooldown(p: string): number {
    if (p === 'dash') return 0;
    if (p === 'fan') return this.P.fan?.intervalMs ?? 0;
    return (this.def as any)[p]?.cooldownMs ?? 0;
  }
  scheduleNext(time: number): void {
    this.nextPatternAt = time + (this.P.patternIntervalMs ?? this.P.dash.intervalMs);
  }
  afterDash(ctx: MobContext): void {
    const F = this.P.fan;
    if (!F?.afterDash || ctx.time < (this.readyAt.get('fan') ?? 0)) return;
    this.current = 'fan';
    this.w.ev('begin:fan');
    this.beginFan(ctx);
  }
  beginTelegraph(ctx: MobContext, ms: number, emit: boolean): void {
    const P = this.P;
    this.state = 'telegraph';
    this.stateUntil = ctx.time + ms;
    this.vel(0, 0);
    this.w.ev(`paint:${COLORS.TELEGRAPH}`);
    this.w.ev(`pose:tele:${ms + P.dash.durationMs}:${emit}`);
    ctx.telegraph.line(
      0,
      0,
      this.angleTo(ctx.player.x, ctx.player.y),
      (P.dash.speedTiles * TILE * P.dash.durationMs) / 1000,
      ms,
    );
    if (emit) this.w.ev('telegraph:dash');
  }
  beginFan(ctx: MobContext): void {
    const F = this.P.fan!;
    const tele = F.telegraphMs ?? 0;
    if (tele <= 0) {
      this.fireFan(ctx);
      this.finish(ctx.time);
      return;
    }
    this.state = 'fanTelegraph';
    this.stateUntil = ctx.time + tele;
    this.vel(0, 0);
    this.w.ev(`pose:hold:${tele}`);
    ctx.telegraph.cone(
      0,
      0,
      this.angleTo(ctx.player.x, ctx.player.y),
      (F.spreadDeg / 2) * (Math.PI / 180),
      (F.telegraphTiles ?? 5) * TILE,
      tele,
    );
    this.w.ev('telegraph:fan');
  }
  fireFan(ctx: MobContext): void {
    const F = this.P.fan!;
    this.w.ev('pose:hold:-');
    this.w.ev('attack:fan');
    const base = Math.atan2(ctx.player.y - this.c.y, ctx.player.x - this.c.x);
    const spread = F.spreadDeg * (Math.PI / 180);
    for (let i = 0; i < F.count; i++) {
      const a = F.count === 1 ? base : base - spread / 2 + (spread * i) / (F.count - 1);
      ctx.fire(0, 0, Math.cos(a), Math.sin(a), { attack: F.attack } as any);
    }
    this.readyAt.set('fan', ctx.time + F.intervalMs);
  }
  beginSlam(ctx: MobContext): void {
    const S = this.def.slam!;
    this.state = 'slamTelegraph';
    this.stateUntil = ctx.time + S.telegraphMs;
    this.vel(0, 0);
    this.slamTarget = { x: ctx.player.x, y: ctx.player.y };
    this.w.ev(`pose:hold:${S.telegraphMs}`);
    ctx.telegraph.circle(this.slamTarget.x, this.slamTarget.y, S.radiusTiles * TILE, S.telegraphMs);
    this.w.ev('telegraph:slam');
  }
  doSummon(ctx: MobContext): void {
    const S = this.def.summon!;
    const n = Math.min(S.count, Math.max(0, S.max - ctx.countMobs(S.enemy)));
    for (let i = 0; i < n; i++) ctx.summon(S.enemy, 0, 0);
    this.w.ev('attack:summon');
    this.w.ev('pose:hold:-');
    this.state = 'recover';
    this.stateUntil = ctx.time + Math.max(0, SPRITES.BOSS_DASH_FRAME_MS);
  }
  beginVolley(ctx: MobContext): void {
    const V = this.def.volley!;
    this.state = 'volleyTelegraph';
    this.stateUntil = ctx.time + V.telegraphMs;
    this.vel(0, 0);
    this.w.ev(`pose:hold:${V.telegraphMs}`);
    ctx.telegraph.line(0, 0, this.angleTo(ctx.player.x, ctx.player.y), V.telegraphTiles * TILE, V.telegraphMs);
    this.w.ev('telegraph:volley');
  }
  damage(amount: number): void {
    this.hp -= amount;
    const idx = phaseIndexFor(this.hp / this.def.hp, this.def.phases);
    if (idx !== this.phaseIndex) {
      this.phaseIndex = idx;
      this.w.ev(`phase:${idx + 1}`);
      this.nextPatternAt = 0;
    }
  }
}

/** 새 두뇌를 같은 가짜 세계에 붙인다 */
function newBoss(def: BossDef, w: World, rng: Rng): { brain: BossBrain; damage: (n: number) => void } {
  let hp = def.hp;
  const host: BossHost = {
    id: 'x',
    def,
    get phaseIndex() {
      return brain.phaseIndex;
    },
    rng,
    get pos() {
      return { x: w.boss.x, y: w.boss.y };
    },
    get center() {
      return { x: w.boss.x, y: w.boss.y };
    },
    halfWidth: 20 - ENEMY_FX.SUMMON_GAP_PX + ENEMY_FX.SUMMON_GAP_PX,
    pose: fakePose(w),
    params: (n) => brain.params(n),
    inPick: (n) => brain.inPick(n),
    isReady: (n, c) => brain.isReady(n, c),
    readyAt: (n) => brain.readyAt(n),
    setReadyAt: (n, a) => brain.setReadyAt(n, a),
    scheduleNext: (t) => brain.scheduleNext(t),
    setVelocity: (x, y) => {
      w.boss.vx = x;
      w.boss.vy = y;
    },
    get blocked() {
      return w.boss.blocked;
    },
    angleTo: (x, y) => Math.atan2(y - w.boss.y, x - w.boss.x),
    paint: (c) => w.ev(`paint:${c}`),
    restoreColor: () => w.ev('paint:restore'),
    setInvulnerable: () => {},
    addSummoned: () => {},
    emitTelegraph: (n) => w.ev(`telegraph:${n}`),
    emitAttack: (n) => w.ev(`attack:${n}`),
    emitAction: () => {},
    emitLoop: () => {},
    emitWallHit: () => w.ev('wall'),
  };
  const brain: BossBrain = new BossBrain(def, host, {
    approach: (ctx) => {
      const dx = ctx.player.x - w.boss.x;
      const dy = ctx.player.y - w.boss.y;
      const len = Math.hypot(dx, dy);
      const s = def.approachSpeedTiles * TILE;
      if (len * len > 1) host.setVelocity((dx / len) * s, (dy / len) * s);
      else host.setVelocity(0, 0);
    },
    stunSelf: () => {},
    releasePose: () => {},
    emitPhase: (i) => w.ev(`phase:${i + 1}`),
  });
  const origBegin = brain.begin.bind(brain);
  brain.begin = (p: BossPatternName, ctx: MobContext) => {
    w.ev(`begin:${p}`);
    origBegin(p, ctx);
  };
  return {
    brain,
    damage: (n) => {
      hp -= n;
      brain.checkPhase(hp / def.hp);
    },
  };
}

/** 같은 시나리오: 20초, 5초·11초에 큰 피해(페이즈 전환), 플레이어는 돈다 */
function run(kind: 'legacy' | 'new', id: string): Ev[] {
  const w = new World();
  const rng = new Rng(12345);
  const legacy = kind === 'legacy' ? new LegacyBoss_(LEGACY[id], w, rng) : null;
  const neo = kind === 'new' ? newBoss(BOSSES[id], w, rng) : null;
  const hits: [number, number][] = [
    [5000, Math.ceil(BOSSES[id].hp * 0.45)],
    [11000, Math.ceil(BOSSES[id].hp * 0.3)],
  ];
  for (w.time = 0; w.time < 20000; w.time += w.delta) {
    w.movePlayer();
    for (const [t, n] of hits)
      if (w.time === t) {
        legacy?.damage(n);
        neo?.damage(n);
      }
    const ctx = w.ctx();
    if (legacy) legacy.think(ctx);
    if (neo) {
      if (neo.brain.nextPatternAt === 0) neo.brain.scheduleNext(ctx.time);
      neo.brain.update(ctx);
    }
    w.step();
  }
  return w.log;
}

describe('54라운드 회귀 2: 2~7층·황제 패턴 진행이 35라운드 상태 머신과 같다', () => {
  for (const id of LEGACY_IDS) {
    it(id, () => {
      const a = run('legacy', id);
      const b = run('new', id);
      expect(a.length).toBeGreaterThan(50);
      // 사건 종류 몇 가지는 반드시 나와야 의미가 있다
      expect(a.some((e) => e.e === 'wall')).toBe(true);
      expect(b).toEqual(a);
    });
  }
});
