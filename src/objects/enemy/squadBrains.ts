/**
 * P19 무리 행동 (방향 문서 ④C · 계약 free-combat §2) — 접촉 피해 없이 '예고 → 공격'만:
 * - MeleeSwing: 근접 휘두르기 (징집병 베기 · 사수 밀치기). 예고(호박 부채꼴 + 몸 번쩍임) → 내딛으며 베기 → 끝에서 부채꼴 판정
 * - SwarmBrain (징집병): 토큰이 없으면 주인공 둘레 '포위 자리'를 돌고, 토큰을 받으면 붙어서 휘두른 뒤 물러난다
 * - DrumBrain (깃발 고수): 거리를 두고 북 — 반경 안 적 공격 속도 ↑ (오라 원), 가까우면 도망
 * - BombBrain (술배 자폭병): 달려와 예고(적색 원 — 따라다님) 뒤 폭발. 맞으면 바로 불이 붙고, 쓰러지면 잠시 뒤 그 자리에서 터진다
 */
import Phaser from 'phaser';
import { COLORS, DEPTH, ENEMY_SQUAD, TILE, type TelegraphTier } from '../../core/Constants';
import {
  EventBus,
  Events,
  type EnemyAttackPayload,
  type EnemyBehaviorPayload,
  type EnemyTelegraphPayload,
} from '../../core/EventBus';
import type { BombParams, DrumParams, SwingParams } from '../../data/enemyTypes';
import { unit } from '../../systems/hazards/hazardMath';
import type { TelegraphHandle } from '../../systems/telegraph';
import type { MobContext } from '../Mob';
import { beatTimesMs } from '../../systems/squad';
import { spriteLibrary } from '../../systems/sprites/sprites';
import { FX_ACTION, fxDrawScale } from '../../systems/sprites/spriteDefs';
import { takeToken, type BrainBody } from './hazardBrains';

/** 위치에서 뽑은 0..1 (같은 자리면 같은 값 — 난수 상태를 건드리지 않는 개체별 변주) */
function spread(x: number, y: number): number {
  const v = Math.sin(x * 12.9898 + y * 78.233) * 43758.5453;
  return v - Math.floor(v);
}

const lerp = (r: readonly [number, number], t: number) => r[0] + (r[1] - r[0]) * t;

/** 근접 휘두르기 (토큰은 부르는 쪽이 받는다) */
export class MeleeSwing {
  phase: 'idle' | 'windup' | 'strike' = 'idle';
  private until = 0;
  private angle = 0;
  private marker: TelegraphHandle | null = null;

  constructor(
    private readonly b: BrainBody,
    private readonly p: SwingParams,
  ) {}

  get busy(): boolean {
    return this.phase !== 'idle';
  }

  inReach(ctx: MobContext): boolean {
    return Math.hypot(ctx.player.x - this.b.x, ctx.player.y - this.b.y) <= this.p.triggerTiles * TILE;
  }

  start(ctx: MobContext): void {
    const b = this.b;
    const p = this.p;
    this.phase = 'windup';
    this.until = ctx.time + p.telegraphMs;
    this.angle = Math.atan2(ctx.player.y - b.y, ctx.player.x - b.x);
    b.body.setVelocity(0, 0);
    b.paint(COLORS.TELEGRAPH);
    b.attackAnim(ctx.time, p.telegraphMs + p.strikeMs);
    const c = b.body.center;
    const half = Phaser.Math.DegToRad(p.arcDeg / 2);
    // 바닥 부채꼴 = 내딛기 + 베는 거리 (예고 자리에서 닿는 끝까지)
    const reach = (p.rangeTiles + (p.lungeTiles ?? 0)) * TILE;
    this.marker = ctx.telegraph.cone(c.x, c.y, this.angle, half, reach, p.telegraphMs, { tier: 'warn' });
    EventBus.emit(Events.ENEMY_TELEGRAPH, { id: b.id, kind: 'swing' } satisfies EnemyTelegraphPayload);
  }

  /** 휘두르는 동안 매 프레임. 다 끝났으면 true */
  update(ctx: MobContext): boolean {
    const b = this.b;
    const p = this.p;
    if (this.phase === 'windup') {
      // 사수: 예고 동안 뒷걸음 (뒤쫓아 붙은 주인공만 밀린다)
      const back = p.backstepTiles ? (p.backstepTiles * TILE * 1000) / p.telegraphMs : 0;
      b.body.setVelocity(-Math.cos(this.angle) * back, -Math.sin(this.angle) * back);
      if (back > 0) this.marker?.aim(b.body.center.x, b.body.center.y);
      if (ctx.time < this.until) return false;
      this.marker?.end();
      this.marker = null;
      b.restore();
      EventBus.emit(Events.ENEMY_ATTACK, { id: b.id, kind: 'swing' } satisfies EnemyAttackPayload);
      this.phase = 'strike';
      this.until = ctx.time + p.strikeMs;
    }
    // 베기: 내딛으며(lungeTiles) 벤다 — 판정은 내딛은 끝에서
    const lunge = p.lungeTiles ? (p.lungeTiles * TILE * 1000) / p.strikeMs : 0;
    b.body.setVelocity(Math.cos(this.angle) * lunge, Math.sin(this.angle) * lunge);
    if (ctx.time < this.until) return false;
    b.body.setVelocity(0, 0);
    const c = b.body.center;
    const half = Phaser.Math.DegToRad(p.arcDeg / 2);
    ctx.meleeHit?.(b.self, c.x, c.y, this.angle, half, p.rangeTiles * TILE, Math.round(p.attack * b.attackScale()));
    this.phase = 'idle';
    return true;
  }

  interrupt(): void {
    this.marker?.end();
    this.marker = null;
    this.phase = 'idle';
  }
}

type SwarmPhase = 'ring' | 'commit' | 'swing' | 'retreat';

/** 징집병: 포위 자리 → (토큰) 붙기 → 휘두르기 → 물러나기 */
export class SwarmBrain {
  phase: SwarmPhase = 'ring';
  private until = 0;
  private nextAt = 0;
  private ringAngle: number | null = null;
  private readonly ringR: number;
  private readonly orbit: number;
  private readonly retreatMs: number;
  readonly swing: MeleeSwing;

  constructor(
    private readonly b: BrainBody,
    p: SwingParams,
  ) {
    this.swing = new MeleeSwing(b, p);
    const t = spread(b.x, b.y);
    this.ringR = lerp(ENEMY_SQUAD.RING_TILES, t) * TILE;
    this.orbit = (t < 0.5 ? -1 : 1) * ENEMY_SQUAD.ORBIT_RAD_PER_S;
    this.retreatMs = lerp(ENEMY_SQUAD.RETREAT_MS, 1 - t);
  }

  get state(): string {
    return this.phase === 'swing' ? this.swing.phase : this.phase;
  }

  get threat(): TelegraphTier | null {
    return this.swing.busy ? 'warn' : null;
  }

  /** speed = 지금 이동 속도 (무리 돌격 배율 포함, Enemy 가 정한다) */
  think(ctx: MobContext, speed: number): void {
    const b = this.b;
    const dx = ctx.player.x - b.x;
    const dy = ctx.player.y - b.y;
    const dist = Math.hypot(dx, dy);
    switch (this.phase) {
      case 'swing':
        if (this.swing.update(ctx)) {
          ctx.squad?.release(b.self);
          this.phase = 'retreat';
          this.until = ctx.time + this.retreatMs;
        }
        return;
      case 'retreat': {
        const away = unit(-dx, -dy);
        b.body.setVelocity(away.x * speed * 0.7, away.y * speed * 0.7);
        if (ctx.time >= this.until) this.toRing(ctx, b.def.attackIntervalMs / Math.max(0.1, b.attackRateMult));
        return;
      }
      case 'commit':
        // P19 2단계: 토큰은 휘두르기를 시작할 때 받는다 (다가가는 동안 쥐고 있지 않는다 — 토큰 = 예고·공격 중)
        if (this.swing.inReach(ctx)) {
          if (takeToken(b, ctx)) {
            this.phase = 'swing';
            this.swing.start(ctx);
          } else this.toRing(ctx, ENEMY_SQUAD.RETRY_MS);
        } else if (ctx.time >= this.until) {
          ctx.squad?.release(b.self);
          this.toRing(ctx, ENEMY_SQUAD.RETRY_MS);
        } else b.moveTo(ctx.player.x, ctx.player.y, speed);
        return;
      case 'ring':
        if (ctx.time >= this.nextAt && dist <= ENEMY_SQUAD.ENGAGE_TILES * TILE) {
          if (ctx.squad?.available(b.id, b.elite) ?? true) {
            this.phase = 'commit';
            this.until = ctx.time + ENEMY_SQUAD.COMMIT_MS;
            b.moveTo(ctx.player.x, ctx.player.y, speed);
            return;
          }
          this.nextAt = ctx.time + ENEMY_SQUAD.RETRY_MS;
        }
        this.circle(ctx, speed);
    }
  }

  private toRing(ctx: MobContext, waitMs: number): void {
    this.phase = 'ring';
    this.ringAngle = null;
    this.nextAt = ctx.time + waitMs;
  }

  /** 포위 자리: 주인공 둘레 ringR 을 천천히 돈다 (자리에 닿으면 선다) */
  private circle(ctx: MobContext, speed: number): void {
    const b = this.b;
    const dx = b.x - ctx.player.x;
    const dy = b.y - ctx.player.y;
    const d = Math.hypot(dx, dy);
    // 주인공이 먼저 다가오면 물러나지 않는다 (쫓아가 벨 수 있게) — 옆으로만 천천히 돈다
    if (d <= this.ringR) {
      this.ringAngle = null;
      const t = unit(-dy, dx);
      const k = speed * 0.4 * Math.sign(this.orbit);
      b.body.setVelocity(t.x * k, t.y * k);
      return;
    }
    if (this.ringAngle === null) this.ringAngle = Math.atan2(dy, dx);
    this.ringAngle += (this.orbit * ctx.delta) / 1000;
    const tx = ctx.player.x + Math.cos(this.ringAngle) * this.ringR;
    const ty = ctx.player.y + Math.sin(this.ringAngle) * this.ringR;
    if (Math.hypot(tx - b.x, ty - b.y) > 3) b.moveTo(tx, ty, speed);
    else b.body.setVelocity(0, 0);
  }

  /** 경직·움찔: 휘두르기를 끊고 포위 자리로 (토큰은 Enemy 가 반납) */
  /**
   * 끊김: 휘두르기를 멈춘다. keep(짧은 움찔)이면 토큰을 쥔 채 움찔이 끝나면 다시 붙어 처음부터 예고하고,
   * 아니면(경직·맨손·띄움) 포위 자리로 (토큰은 Enemy 가 반납). 토큰을 쥐고 있었는지 돌려준다
   */
  interrupt(time: number, keep = false): boolean {
    const held = this.phase === 'commit' || this.phase === 'swing';
    this.swing.interrupt();
    if (keep && held) {
      this.phase = 'commit';
      this.until = time + ENEMY_SQUAD.COMMIT_MS;
      return true;
    }
    this.phase = 'ring';
    this.ringAngle = null;
    this.nextAt = time + ENEMY_SQUAD.RETRY_MS;
    return false;
  }
}

/** 오라 그림 (art §34 drum_aura — 반경 radiusPx 도트) */
const DRUM_AURA_FX = 'drum_aura';

/** 깃발 고수 (공격 없음 — 토큰을 쓰지 않는다) */
export class DrumBrain {
  private nextBeat = 0;
  private aura: Phaser.GameObjects.Graphics | null = null;
  /** 첫 북(오라가 처음 켜짐 = 사기 고양)을 쳤다 */
  private rallied = false;

  constructor(
    private readonly b: BrainBody,
    private readonly p: DrumParams,
    private readonly scene: Phaser.Scene,
  ) {}

  get state(): string {
    return 'drum';
  }

  get threat(): TelegraphTier | null {
    return null;
  }

  think(ctx: MobContext): void {
    const b = this.b;
    const p = this.p;
    const dx = b.x - ctx.player.x;
    const dy = b.y - ctx.player.y;
    const dist = Math.hypot(dx, dy) / TILE;
    const away = unit(dx, dy);
    const speed = b.def.speedTiles * TILE;
    if (dist < p.fleeTiles) {
      b.body.setVelocity(away.x * speed * 1.2, away.y * speed * 1.2);
      ctx.bark?.(b.self, 'flee', b.def.barks?.flee);
    } else if (dist < p.keepMinTiles) b.body.setVelocity(away.x * speed, away.y * speed);
    else if (dist > p.keepMaxTiles) b.moveTo(ctx.player.x, ctx.player.y, speed);
    else b.body.setVelocity(0, 0);
    const r = p.radiusTiles * TILE;
    const auraDef = spriteLibrary.sheet(DRUM_AURA_FX, FX_ACTION);
    // 그림이 없으면 자리표시 원
    const aura = auraDef ? null : (this.aura ??= this.scene.add.graphics().setDepth(DEPTH.FX_GROUND));
    aura?.setPosition(b.x, b.y).setAlpha(Math.max(0.2, aura.alpha - ctx.delta / 1000));
    if (ctx.time < this.nextBeat) return;
    this.nextBeat = ctx.time + p.beatMs;
    ctx.squad?.drum(b.x, b.y, r, ctx.time + p.beatMs + 100, p.rateMult);
    aura?.clear().lineStyle(1, Phaser.Display.Color.HexStringToColor(b.def.color).color, 1).strokeCircle(0, 0, r);
    aura?.setAlpha(0.8);
    b.attackAnim(ctx.time);
    EventBus.emit(Events.ENEMY_BEHAVIOR, { id: b.id, kind: 'drum' } satisfies EnemyBehaviorPayload);
    this.beats(ctx, r, auraDef);
  }

  /**
   * 북채가 닿는 프레임마다(시트 beatFrames) 북소리(ENEMY_ATTACK beat — 처음 한 번은 rally)와 오라 그림을 0 프레임부터 다시.
   * 시트가 없으면 북 순간 한 번
   */
  private beats(ctx: MobContext, r: number, auraDef: ReturnType<typeof spriteLibrary.sheet>): void {
    const b = this.b;
    const first = !this.rallied;
    this.rallied = true;
    if (first)
      EventBus.emit(Events.ENEMY_ATTACK, { id: b.id, kind: 'drum', phase: 'rally' } satisfies EnemyAttackPayload);
    ctx.bark?.(b.self, 'beat', b.def.barks?.beat);
    const t0 = beatTimesMs(b.visual.sheet('attack'));
    const times = t0.length > 0 ? t0 : [0];
    const artR = (auraDef as { radiusPx?: number } | undefined)?.radiusPx;
    const scaleMult = auraDef && artR ? r / (artR * fxDrawScale(auraDef)) : 1;
    times.forEach((ms, i) => {
      const hit = () => {
        if (!b.active) return;
        if (!first)
          EventBus.emit(Events.ENEMY_ATTACK, { id: b.id, kind: 'drum', phase: 'beat' } satisfies EnemyAttackPayload);
        if (auraDef)
          ctx.playFx(DRUM_AURA_FX, b.x, b.y, {
            depth: DEPTH.FX_GROUND,
            scaleMult,
            durationMs: (times[i + 1] ?? this.p.beatMs) - ms,
            follow: b.self,
          });
      };
      if (ms > 0) this.scene.time.delayedCall(ms, hit);
      else hit();
    });
  }

  interrupt(_time: number): void {}

  destroy(): void {
    this.aura?.destroy();
    this.aura = null;
  }
}

/** 술배 자폭병 */
export class BombBrain {
  phase: 'run' | 'fuse' = 'run';
  /** 터졌다 (쓰러질 때 다시 터지지 않게) */
  exploded = false;
  /** 달리는 중이라고 알렸다 (음향 bomber_fuse 루프 — run/runEnd 짝) */
  private running = false;
  private until = 0;
  private marker: TelegraphHandle | null = null;
  /** 마지막으로 받은 컨텍스트 (맞아서 불붙음 · 쓰러진 뒤 폭발) */
  private ctx: MobContext | null = null;

  constructor(
    private readonly b: BrainBody,
    private readonly p: BombParams,
  ) {}

  get state(): string {
    return this.phase;
  }

  get threat(): TelegraphTier | null {
    return this.phase === 'fuse' ? 'danger' : null;
  }

  think(ctx: MobContext): void {
    this.ctx = ctx;
    const b = this.b;
    if (this.phase === 'fuse') {
      b.body.setVelocity(0, 0);
      this.marker?.aim(b.body.center.x, b.body.center.y);
      if (ctx.time >= this.until) this.explode(ctx);
      return;
    }
    if (!this.running) {
      this.running = true;
      EventBus.emit(Events.ENEMY_ATTACK, { id: b.id, kind: 'explode', phase: 'run' } satisfies EnemyAttackPayload);
      ctx.bark?.(b.self, 'charge', b.def.barks?.charge);
    }
    b.moveTo(ctx.player.x, ctx.player.y, b.def.speedTiles * TILE);
    const d = Math.hypot(ctx.player.x - b.x, ctx.player.y - b.y);
    if (d <= this.p.triggerTiles * TILE && takeToken(b, ctx)) this.light(ctx);
  }

  /** 맞음: 불이 붙는다 (토큰과 무관 — 날아간 자리에서 터진다) */
  onHit(): void {
    if (this.phase !== 'run' || !this.ctx || !this.b.active) return;
    this.light(this.ctx, true);
    this.ctx.bark?.(this.b.self, 'launched', this.b.def.barks?.launched);
  }

  private endRun(): void {
    if (!this.running) return;
    this.running = false;
    EventBus.emit(Events.ENEMY_ATTACK, {
      id: this.b.id,
      kind: 'explode',
      phase: 'runEnd',
    } satisfies EnemyAttackPayload);
  }

  /** 쓰러짐: deathFuseMs 뒤 그 자리에서 터진다 (이미 터졌으면 없음) */
  onDeath(scene: Phaser.Scene): void {
    this.endRun();
    this.marker?.end();
    this.marker = null;
    const ctx = this.ctx;
    if (this.exploded || !ctx?.blast) return;
    this.exploded = true;
    const c = { x: this.b.body.center.x, y: this.b.body.center.y };
    const r = this.p.radiusTiles * TILE;
    const self = this.b.self;
    const attack = Math.round(this.b.def.attack * this.b.attackScale());
    const blast = ctx.blast;
    ctx.telegraph.circle(c.x, c.y, r, this.p.deathFuseMs, { tier: 'danger' });
    scene.time.delayedCall(this.p.deathFuseMs, () => blast(c.x, c.y, r, attack, this.p.mobDamage, self));
  }

  /** 심지: 제자리면 attack(1초 예고 시트), 맞아서 불붙었으면 swell 루프(날아가는 동안 — art §34) */
  private light(ctx: MobContext, byHit = false): void {
    const b = this.b;
    this.endRun();
    this.phase = 'fuse';
    this.until = ctx.time + this.p.fuseMs;
    b.body.setVelocity(0, 0);
    b.paint(COLORS.TELEGRAPH);
    const swell = byHit ? b.visual.sheet('swell') : undefined;
    if (swell)
      b.visual.loopFrames(
        'swell',
        b.visual.facing,
        Array.from({ length: swell.frames }, (_, i) => i),
        swell.frameDurationsMs?.[0] ?? 80,
      );
    else {
      b.attackAnim(ctx.time, this.p.fuseMs);
      ctx.bark?.(b.self, 'fuse', b.def.barks?.fuse);
    }
    const c = b.body.center;
    this.marker = ctx.telegraph.circle(c.x, c.y, this.p.radiusTiles * TILE, this.p.fuseMs, { tier: 'danger' });
    EventBus.emit(Events.ENEMY_TELEGRAPH, {
      id: b.id,
      kind: 'fuse',
      ms: this.p.fuseMs,
    } satisfies EnemyTelegraphPayload);
  }

  private explode(ctx: MobContext): void {
    const b = this.b;
    this.marker?.end();
    this.marker = null;
    this.exploded = true;
    ctx.squad?.release(b.self);
    // 스스로 터짐: 쓰러지는 그림 = explode 시트 (폭발 이벤트는 GameCombat.blast)
    b.self.corpseAction = 'explode';
    const c = b.body.center;
    ctx.blast?.(
      c.x,
      c.y,
      this.p.radiusTiles * TILE,
      Math.round(b.def.attack * b.attackScale()),
      this.p.mobDamage,
      b.self,
    );
  }

  /** 경직·움찔은 불붙은 심지를 끄지 못한다 */
  interrupt(_time: number): void {}
}
