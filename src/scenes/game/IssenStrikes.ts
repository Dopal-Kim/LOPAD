/**
 * 56라운드 Q2·Q3·Q28·Q29 칼 3타 일섬 (씬 쪽): 돌진 시작에 출발 발 위치로 일섬 선(실제 이동 칸 수로 t1~t4, 분신 없으면 `_solo`),
 * 판정 구간 동안 출발점 → 지금 몸까지 쓸고 지나간 직사각형(적마다 1회), 검기 3단 소모면 그림자 분신이 같은 선을 달려
 * 도착 순간 선 위 적 전부에게 50% 1회. 분신이 없으면 선 끝 폭발은 연출만. 돌진 동안 칼끝 리본(Q38 돌진류만).
 * 시각은 씬 시계(히트스톱 동안 멈춤) · 몸 재생 배율 k 를 곱한다. 기하는 `systems/issenPath`.
 */
import { FEEDBACK, entityDepth, fxLitDepth } from '../../core/Constants';
import { EventBus, Events, type PlayerAttackPayload, type PlayerSkillPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { PLAYER_DATA } from '../../data';
import type { IssenDef } from '../../data/types';
import type { Mob } from '../../objects/Mob';
import type { FxFollowTarget, FxHandle } from '../../systems/fxTypes';
import { issenHit, lineTier, predictTravel, shadowAt } from '../../systems/issenPath';
import type { Pt } from '../../systems/hitShapes';
import type { Game } from '../Game';
import { HIT_ORIGIN_UP_PX } from './shared';

/** 일섬 한 번의 진행 상태 */
interface IssenRun {
  p: PlayerAttackPayload;
  def: IssenDef;
  dir: Pt;
  facing: string;
  clone: boolean;
  /** 몸 재생 배율 (시트를 늘였으면 시각도 늘인다) */
  k: number;
  /** 출발 발 위치 (돌진 시작에 정함) */
  start: Pt | null;
  travel: number;
  sweeping: boolean;
  hit: Set<Mob>;
  lineId: string | null;
  /** 분신 따라가기 대상 · 출발 시각(플레이 시계) · 그 fx */
  shadow: (FxFollowTarget & { bornAt: number }) | null;
  shadowFx?: FxHandle | null;
}

/** 근접 타격 1회 (PlayerStrikes.strikeMob — first = 이 동작이 처음 맞힌 적: 무기 번쩍임·검기) */
export type MobStrike = (mob: Mob, p: PlayerAttackPayload, first: boolean) => void;

export class IssenStrikes {
  /** 디버그: 마지막 일섬 */
  debugLast: Record<string, unknown> | null = null;
  private run: IssenRun | null = null;

  constructor(
    private readonly g: Game,
    private readonly strike: MobStrike,
  ) {}

  private get live(): boolean {
    return this.g.scene.isActive() && !this.g.frozen && !gameState.gameOver;
  }

  start(p: PlayerAttackPayload): void {
    const def = gameState.weapon.def.issen;
    const is = p.issen;
    if (!def || !is) return;
    const g = this.g;
    const k = p.swingDelayMs > 0 && def.hitFromMs > 0 ? p.swingDelayMs / def.hitFromMs : 1;
    const run: IssenRun = {
      p,
      def,
      dir: { x: is.dirX, y: is.dirY },
      facing: is.facing,
      clone: is.clone,
      k,
      start: null,
      travel: 0,
      sweeping: false,
      hit: new Set(),
      lineId: null,
      shadow: null,
    };
    this.run = run;
    this.debugLast = { time: g.time.now, kenki: is.kenki, clone: is.clone, k, facing: is.facing };
    const at = (ms: number, fn: () => void) =>
      g.time.delayedCall(ms * k, () => {
        if (this.live && this.run === run) fn();
      });
    at(def.dashStartMs, () => this.dashStart(run));
    at(def.hitFromMs, () => (run.sweeping = true));
    at(def.hitToMs, () => {
      this.sweep(run);
      run.sweeping = false;
    });
    at(def.dashEndMs, () => this.dashEnd(run));
    at(def.dashStartMs + def.burstAtLineMs, () => this.emitSkill('burst'));
    if (run.clone) {
      at(def.shadow.startAtMs, () => this.shadowStart(run));
      at(def.shadow.hitAtMs, () => this.shadowHit(run));
    }
  }

  /** 돌진 시작: 출발점 고정 · 실제 이동 예측으로 선 고르기 · 칼끝 리본 */
  private dashStart(run: IssenRun): void {
    const g = this.g;
    const pl = g.player;
    run.start = { x: pl.x, y: pl.y };
    const [pw] = PLAYER_DATA.size;
    const predicted = predictTravel(
      pl.x,
      pl.y,
      run.dir,
      run.def.distancePx,
      (x, y) => g.world.isWalkableAt(x, y),
      2,
      pw / 2,
    );
    const tier = lineTier(predicted, run.def.tilePx, run.def.lineSheets.length);
    const base = run.def.lineSheets[tier];
    const solo = `${base}${run.def.soloSuffix}`;
    const id = run.clone ? base : g.fx.has(solo) ? solo : base;
    run.lineId = g.fx.has(id) ? id : null;
    if (run.lineId)
      // 아트 depth below_player: 바닥 바로 위(주인공·적·분신 아래) — 이펙트 띠가 아니라 라이트맵 아래 깊이
      g.fx.play(run.lineId, pl.x, pl.y, { dir: run.facing, depth: FEEDBACK.ISSEN_LINE_DEPTH, belowLighting: true });
    this.debugLast = { ...this.debugLast, start: run.start, predicted, tier: tier + 1, line: run.lineId };
    this.emitSkill('dash');
    // 56라운드 Q38: 리본은 돌진류에만 — 돌진 동안 칼끝(몸 중심 앞)
    const sheet = gameState.weapon.def.feel?.ribbon;
    if (sheet) {
      const until = g.playNow() + (run.def.dashEndMs - run.def.dashStartMs) * run.k;
      g.ribbons.start(
        (t) =>
          t > until || !pl.active
            ? null
            : { x: pl.x + run.dir.x * HIT_ORIGIN_UP_PX, y: pl.y - HIT_ORIGIN_UP_PX + run.dir.y * HIT_ORIGIN_UP_PX },
        { sheet, depth: fxLitDepth(pl.depth + 1e-6) },
      );
    }
  }

  private dashEnd(run: IssenRun): void {
    this.measure(run);
    this.debugLast = { ...this.debugLast, travel: Math.round(run.travel * 10) / 10 };
  }

  /** 출발점에서 지금 몸까지 돌진 축 위 거리 (뒤로는 0) */
  private measure(run: IssenRun): void {
    const s = run.start;
    if (!s) return;
    const pl = this.g.player;
    const along = (pl.x - s.x) * run.dir.x + (pl.y - s.y) * run.dir.y;
    run.travel = Math.max(run.travel, Math.min(run.def.distancePx, along));
  }

  /** 판정 구간: 쓸고 지나간 직사각형에 걸친 적 (적마다 1회) */
  private sweep(run: IssenRun): void {
    const s = run.start;
    if (!s) return;
    this.measure(run);
    const origin = { x: s.x, y: s.y - HIT_ORIGIN_UP_PX };
    const geom = { backPx: run.def.hitBackPx, extraPx: run.def.hitExtraPx, widthPx: run.def.hitWidthPx };
    for (const child of [...this.g.mobs.getChildren()]) {
      const mob = child as Mob;
      if (!mob.active || run.hit.has(mob)) continue;
      const b = mob.body;
      const t = { x: b.center.x, y: b.center.y, r: Math.min(b.halfWidth, b.halfHeight) };
      if (!issenHit(origin, run.dir, run.travel, geom, t)) continue;
      run.hit.add(mob);
      this.strike(mob, { ...run.p, x: s.x, y: s.y }, run.hit.size === 1);
    }
    this.debugLast = { ...this.debugLast, hits: run.hit.size };
  }

  /** 분신 출발: 출발점 → 도착점(실제로 멈춘 자리)을 travelMs 동안 */
  private shadowStart(run: IssenRun): void {
    const g = this.g;
    const s = run.start;
    if (!s) return;
    this.measure(run);
    const sheet = run.def.shadow.sheet;
    this.emitSkill('clone');
    if (!g.fx.has(sheet)) return;
    const follow = { x: s.x, y: s.y, active: true, depth: entityDepth(s.y), rotation: 0, bornAt: g.playNow() };
    run.shadow = follow;
    // Q51: 분신 깊이 = 발 기준 앞뒤 정렬 (라이트맵 아래 개체 깊이 — 매 프레임 update 가 갱신)
    run.shadowFx = g.fx.play(sheet, s.x, s.y, {
      dir: run.facing,
      follow,
      depth: entityDepth(s.y),
      belowLighting: true,
    });
  }

  /** 분신 도착: 선 위 적 전부 피해 × damageScale 1회 (Q29) */
  private shadowHit(run: IssenRun): void {
    const s = run.start;
    if (!s) return;
    this.measure(run);
    const origin = { x: s.x, y: s.y - HIT_ORIGIN_UP_PX };
    const geom = { backPx: run.def.hitBackPx, extraPx: run.def.hitExtraPx, widthPx: run.def.hitWidthPx };
    const p = { ...run.p, x: s.x, y: s.y, damageMult: run.p.damageMult * run.def.shadow.damageScale, forceCrit: false };
    let n = 0;
    for (const child of [...this.g.mobs.getChildren()]) {
      const mob = child as Mob;
      if (!mob.active) continue;
      const b = mob.body;
      if (
        !issenHit(origin, run.dir, run.travel, geom, {
          x: b.center.x,
          y: b.center.y,
          r: Math.min(b.halfWidth, b.halfHeight),
        })
      )
        continue;
      n += 1;
      this.strike(mob, p, false);
    }
    this.debugLast = { ...this.debugLast, cloneHits: n, travel: Math.round(run.travel * 10) / 10 };
  }

  /** 매 프레임: 판정 쓸기 · 분신 위치 */
  update(): void {
    const run = this.run;
    if (!run) return;
    if (run.sweeping) this.sweep(run);
    const sh = run.shadow;
    const s = run.start;
    if (sh && s) {
      const to = { x: s.x + run.dir.x * run.travel, y: s.y + run.dir.y * run.travel };
      const at = shadowAt(s, to, this.g.playNow() - sh.bornAt, run.def.shadow.travelMs * run.k);
      sh.x = at.x;
      sh.y = at.y;
      sh.depth = entityDepth(at.y);
      if (run.shadowFx && this.g.fx.isActive(run.shadowFx)) run.shadowFx.sprite.setDepth(sh.depth);
    }
  }

  private emitSkill(phase: PlayerSkillPayload['phase']): void {
    EventBus.emit(Events.PLAYER_SKILL, {
      weapon: gameState.weapon.id,
      move: 'issen',
      phase,
    } satisfies PlayerSkillPayload);
  }
}
