/**
 * 56라운드 2단계 새 기본기 (씬 쪽, 계약 art §18.7~§18.9) — 연격 파이프라인(PlayerStrikes·SwingFx)이 하지 않는 부분만:
 * - 돌진형(태클·막다가 떼면 돌진): 판정이 몸과 함께 이동(적마다 1회) · 맞은 적을 밀고 감 · 태클 첫 접촉 fx(몸을 따라감) ·
 *   돌진 땅 홈 fx(돌진 출발 발에 고정, 주인공 아래 — 벽에 막혀도 그대로, Q63)
 * - 도약 찍기: 나선 fx(도약 출발 발에 고정 — 벽에 막혀 짧게 뛰면 생략, Q55) · 착지 발밑 링 판정 · 착지 소리
 * - 버티기 올려베기 슈퍼아머 피격 흡수 fx · 대치 일격 준비 반짝임(칼집 입구, 연출만 — Q60)
 * - 고속 난타 fx: 몸과 같은 열을 과열 단계 시트로 바꿔 낌(`FlurryHold.view`)
 * 시각은 씬·플레이 시계(히트스톱 동안 멈춤).
 */
import { DEPTH, FEEDBACK, MOVE_FX, entityDepth } from '../../core/Constants';
import {
  EventBus,
  Events,
  type PlayerAttackPayload,
  type PlayerDamagedPayload,
  type PlayerSkillPayload,
} from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { PLAYER_DATA } from '../../data';
import type { Mob } from '../../objects/Mob';
import type { FxHandle } from '../../systems/fx/fxTypes';
import { circleHit, shapeHit, type HitShape, type Pt } from '../../systems/weapon/hitShapes';
import { predictTravel } from '../../systems/weapon/issenPath';
import { facingOf, rowDirFor } from '../../systems/sprites/spriteDefs';
import type { Game } from '../Game';
import type { MobStrike } from './IssenStrikes';
import { HIT_ORIGIN_UP_PX, shapeFacing } from './shared';
import type { SwingFx } from './SwingFx';

/** 돌진형 한 번 */
interface RushRun {
  p: PlayerAttackPayload;
  dir: Pt;
  shape: HitShape | null;
  bornAt: number;
  hit: Set<Mob>;
  contact: boolean;
  /** 판정 구간이 끝난 뒤 마지막 판정을 했는가 */
  swept: boolean;
}

const hitTarget = (mob: Mob) => {
  const b = mob.body;
  return { x: b.center.x, y: b.center.y, r: Math.min(b.halfWidth, b.halfHeight) };
};

export class MoveStrikes {
  /** 디버그: 마지막 돌진·도약·흡수·준비 */
  debugLast: Record<string, unknown> | null = null;
  private rush: RushRun | null = null;
  private flurryFx: { handle: FxHandle | null; id: string; facing: string } | null = null;

  constructor(
    private readonly g: Game,
    private readonly swing: SwingFx,
    private readonly strike: MobStrike,
  ) {}

  private get live(): boolean {
    return this.g.scene.isActive() && !this.g.frozen && !gameState.gameOver;
  }

  private at(ms: number, fn: () => void): void {
    if (ms <= 0) fn();
    else
      this.g.time.delayedCall(ms, () => {
        if (this.live) fn();
      });
  }

  /** 무기 보조 fx id (`<무기>_<이름>`) — 시트가 없으면 null */
  private fxId(name: string | undefined | null): string | null {
    if (!name) return null;
    const id = name.startsWith(`${gameState.weapon.id}_`) ? name : `${gameState.weapon.id}_${name}`;
    return this.g.fx.has(id) ? id : null;
  }

  // --- 돌진형 (태클·막다가 떼면 돌진) ---

  /** PLAYER_ATTACKED `rush` — 판정은 매 프레임 지금 몸 자리에서 (PlayerStrikes 가 휘두름 fx 뒤에 부른다) */
  startRush(p: PlayerAttackPayload): void {
    const r = p.rush;
    if (!r) return;
    const g = this.g;
    const len = Math.hypot(p.dirX, p.dirY) || 1;
    const shape = p.hitShape ? this.swing.resolveSpec(p, p.hitShape) : null;
    this.rush = {
      p,
      dir: { x: p.dirX / len, y: p.dirY / len },
      shape,
      bornAt: g.playNow(),
      hit: new Set(),
      contact: false,
      swept: false,
    };
    // 땅 홈 (돌진 출발 발 고정 · 주인공 아래 · 8행) — fx JSON spawnAtMs(몸 기준), 없으면 돌진 시작
    const ground = this.fxId(r.groundFx);
    if (ground) {
      const def = g.fx.sheet(ground) as { spawnAtMs?: number } | null;
      const spawnAt = typeof def?.spawnAtMs === 'number' ? def.spawnAtMs : r.dashFromMs;
      this.at(spawnAt, () => {
        const pl = g.player;
        g.fx.play(ground, pl.x, pl.y, {
          dir: rowDirFor(g.fx.sheet(ground), p.dirX, p.dirY, pl.facingDir),
          // 아트 depth below_player: 바닥 바로 위 (일섬 선과 같은 깊이)
          depth: FEEDBACK.ISSEN_LINE_DEPTH,
          belowLighting: true,
        });
      });
    }
    this.debugLast = { kind: 'rush', move: p.move, time: g.time.now, hits: 0, contactFx: null };
  }

  /** 돌진 판정 한 프레임 */
  private sweepRush(run: RushRun): void {
    const g = this.g;
    const p = run.p;
    const r = p.rush!;
    const e = g.playNow() - run.bornAt;
    const from = p.swingDelayMs;
    const to = from + (p.activeMs ?? 0);
    if (e > Math.max(to, r.dashToMs) && run.swept) {
      this.rush = null;
      return;
    }
    // 판정 구간 — 긴 프레임이 구간을 건너뛰어도 끝난 첫 프레임에 한 번은 판정한다
    if (e < from || (e > to && run.swept) || !run.shape) return;
    run.swept = e > to;
    if (this.debugLast) {
      this.debugLast.sweeps = ((this.debugLast.sweeps as number) ?? 0) + 1;
      this.debugLast.lastSweep = { e: Math.round(e), x: Math.round(g.player.x), y: Math.round(g.player.y) };
    }
    const pl = g.player;
    const facing = shapeFacing(p, facingOf(p.dirX, p.dirY, pl.facingDir));
    const ox = pl.x;
    const oy = pl.y - HIT_ORIGIN_UP_PX;
    for (const child of [...g.mobs.getChildren()]) {
      const mob = child as Mob;
      if (!mob.active || run.hit.has(mob)) continue;
      if (!shapeHit(ox, oy, run.dir.x, run.dir.y, run.shape, hitTarget(mob), facing)) continue;
      run.hit.add(mob);
      if (!run.contact) this.contact(run);
      this.strike(mob, { ...p, x: pl.x, y: pl.y }, run.hit.size === 1);
      // Q55: 적을 밀고 감 — 남은 돌진 거리 + 여유만큼 같은 방향으로 (크게 튕기지 않음)
      if (mob.active) {
        const span = Math.max(1, r.dashToMs - r.dashFromMs);
        const left = Math.max(0, Math.min(1, (r.dashToMs - e) / span));
        const ms = Math.max(MOVE_FX.CARRY_MIN_MS, r.dashToMs - e);
        mob.shove(run.dir.x, run.dir.y, r.dashPx * left + r.carryExtraPx, ms, mob.isBoss);
      }
    }
    if (this.debugLast) this.debugLast.hits = run.hit.size;
  }

  /** 태클: 첫 접촉 순간 fx (몸을 따라감, 8행) — 빗나가면 없음 (Q55) */
  private contact(run: RushRun): void {
    run.contact = true;
    const g = this.g;
    const id = this.fxId(run.p.rush?.contactFx);
    if (!id) return;
    const pl = g.player;
    g.fx.play(id, pl.x, pl.y, {
      dir: rowDirFor(g.fx.sheet(id), run.dir.x, run.dir.y, pl.facingDir),
      follow: pl,
      depthOffset: DEPTH.OVERLAY_STEP * 2,
    });
    if (this.debugLast) this.debugLast.contactFx = id;
  }

  // --- 도약 찍기 ---

  /** PLAYER_ATTACKED `leap` — 나선(벽에 막히면 생략) · 착지 링 판정·소리 (쐐기·끝 충격원·균열은 PlayerStrikes 일반 판정) */
  startLeap(p: PlayerAttackPayload): void {
    const L = p.leap;
    const def = gameState.weapon.def.moves?.leap;
    if (!L || !def) return;
    const g = this.g;
    const len = Math.hypot(p.dirX, p.dirY) || 1;
    const dir = { x: p.dirX / len, y: p.dirY / len };
    const [pw] = PLAYER_DATA.size;
    const predicted = predictTravel(
      L.startX,
      L.startY,
      dir,
      def.leap.px,
      (x, y) => g.world.isWalkableAt(x, y),
      2,
      pw / 2,
    );
    const spiral = predicted >= def.leap.px * MOVE_FX.SPIRAL_MIN_RATIO ? this.fxId(L.spiralFx) : null;
    if (spiral) {
      const sdef = g.fx.sheet(spiral) as { spawnAtMs?: number } | null;
      this.at(typeof sdef?.spawnAtMs === 'number' ? sdef.spawnAtMs : MOVE_FX.SPIRAL_AT_MS, () =>
        g.fx.play(spiral, L.startX, L.startY, {
          dir: rowDirFor(g.fx.sheet(spiral), dir.x, dir.y, g.player.facingDir),
          depth: entityDepth(L.startY) + DEPTH.OVERLAY_STEP * 3,
        }),
      );
    }
    this.debugLast = {
      kind: 'leap',
      time: g.time.now,
      stage: L.stage,
      predicted: Math.round(predicted * 10) / 10,
      spiral,
      ringHits: 0,
    };
    this.at(p.swingDelayMs, () => this.land(p));
  }

  /** 착지: 발밑 링 (반지름 R × 0.6) — 적마다 1회, 소리 */
  private land(p: PlayerAttackPayload): void {
    const g = this.g;
    const L = p.leap!;
    const pl = g.player;
    const skill: PlayerSkillPayload = { weapon: gameState.weapon.id, move: 'leap', phase: 'land', stage: L.stage };
    EventBus.emit(Events.PLAYER_SKILL, skill);
    const ring = { ...p, damageMult: p.damageMult * L.ringDamageMult, x: pl.x, y: pl.y };
    let n = 0;
    for (const child of [...g.mobs.getChildren()]) {
      const mob = child as Mob;
      if (!mob.active || !circleHit(pl.x, pl.y, L.ringRadiusPx, hitTarget(mob))) continue;
      n += 1;
      this.strike(mob, ring, false);
    }
    if (this.debugLast) this.debugLast.ringHits = n;
    g.strikes.overlay.debug(
      pl.x,
      pl.y,
      p.dirX,
      p.dirY,
      { kind: 'ring', radius: L.ringRadiusPx, inner: 0, dist: 0 },
      'right',
      p.activeMs ?? 60,
      true,
    );
  }

  // --- 흡수 · 준비 반짝임 ---

  /** PLAYER_DAMAGED: 슈퍼아머로 받았으면 흡수 fx (몸 위, 따라감) */
  onPlayerDamaged(p: PlayerDamagedPayload): void {
    if (!p.armored) return;
    const g = this.g;
    const id = this.fxId(gameState.weapon.def.moves?.brace?.absorbFx);
    if (id) g.fx.play(id, g.player.x, g.player.y, { follow: g.player, depthOffset: DEPTH.OVERLAY_STEP * 3 });
    this.debugLast = { kind: 'absorb', time: g.time.now, amount: p.amount, fx: id };
  }

  /** PLAYER_SKILL: 대치 일격 준비 반짝임 (칼집 입구 — 연출만) */
  onSkill(p: PlayerSkillPayload): void {
    if (p.move !== 'iai' || p.phase !== 'ready' || !p.at) return;
    const g = this.g;
    const id = this.fxId(gameState.weapon.def.moves?.iai?.readyFx);
    if (id) g.fx.play(id, p.at.x, p.at.y, { depth: g.player.depth + DEPTH.OVERLAY_STEP * 3 });
    this.debugLast = { kind: 'iaiReady', time: g.time.now, at: p.at, fx: id };
  }

  // --- 고속 난타 fx ---

  /** 몸 열과 같은 열로 (과열 단계가 바뀌면 시트만 바꿔 낌) */
  private syncFlurry(): void {
    const g = this.g;
    const view = g.player.moves.flurry?.view ?? null;
    const cur = this.flurryFx;
    if (!view || !g.fx.has(view.fx)) {
      if (cur) g.fx.stop(cur.handle, 0, false);
      this.flurryFx = null;
      return;
    }
    if (!cur || cur.id !== view.fx || cur.facing !== view.facing || !g.fx.isActive(cur.handle)) {
      if (cur) g.fx.stop(cur.handle, 0, false);
      const handle = g.fx.play(view.fx, g.player.x, g.player.y, {
        dir: view.facing,
        follow: g.player,
        depthOffset: DEPTH.OVERLAY_STEP * 2,
        staticFrame: view.column,
      });
      this.flurryFx = { handle, id: view.fx, facing: view.facing };
    }
    g.fx.setFrame(this.flurryFx!.handle, view.fx, view.column, view.facing);
  }

  /** 매 프레임 */
  update(): void {
    if (this.rush) this.sweepRush(this.rush);
    this.syncFlurry();
  }

  destroy(): void {
    this.rush = null;
    this.flurryFx = null;
  }
}
