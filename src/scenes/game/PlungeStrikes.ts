/**
 * 56라운드 Q10 대검 꽂아내리기 (씬 쪽): 판정 프레임(몸 hitAt)에 꽂힌 자리(몸 plantAnchors)에서 마우스 방향 충격파
 * (fx greatsword_plunge_wave — 회전, 앞머리가 지나간 칸만 맞음) + 꽂힌 자리 작은 충격원 + 땅 균열 l. 휘두름 이펙트 없음.
 * 시각은 씬 시계·플레이 시계(히트스톱 동안 멈춤). 앞머리 시간표는 `systems/weapon/plungeWave`.
 */
import { DEPTH, COLORS } from '../../core/Constants';
import type { PlayerAttackPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { Mob } from '../../objects/Mob';
import { circleHit, type Pt } from '../../systems/weapon/hitShapes';
import { waveEndMs, waveFrontRatio, waveHit, waveTimeline, type WaveTimeline } from '../../systems/weapon/plungeWave';
import { artScale } from '../../systems/sprites/spriteDefs';
import type { Game } from '../Game';
import type { MobStrike } from './IssenStrikes';
import type { SwingFx } from './SwingFx';

interface WaveRun {
  p: PlayerAttackPayload;
  origin: Pt;
  dir: Pt;
  lengthPx: number;
  halfWidthPx: number;
  timeline: WaveTimeline;
  bornAt: number;
  hit: Set<Mob>;
}

export class PlungeStrikes {
  debugLast: Record<string, unknown> | null = null;
  private wave: WaveRun | null = null;

  constructor(
    private readonly g: Game,
    private readonly swing: SwingFx,
    private readonly strike: MobStrike,
  ) {}

  private get live(): boolean {
    return this.g.scene.isActive() && !this.g.frozen && !gameState.gameOver;
  }

  start(p: PlayerAttackPayload): void {
    const g = this.g;
    const pl = p.plunge;
    if (!pl) return;
    g.time.delayedCall(Math.max(0, p.swingDelayMs), () => {
      if (this.live) this.impact(p);
    });
  }

  private impact(p: PlayerAttackPayload): void {
    const g = this.g;
    const pl = p.plunge!;
    const P = gameState.weapon.def.plunge;
    if (!P) return;
    const player = g.player;
    const origin = { x: player.x + pl.plantOffsetX, y: player.y + pl.plantOffsetY };
    const len = Math.hypot(p.dirX, p.dirY) || 1;
    const dir = { x: p.dirX / len, y: p.dirY / len };
    // 꽂힌 자리 작은 충격원
    let plantHits = 0;
    const plantP = { ...p, damageMult: p.damageMult * P.plantDamageMult };
    for (const child of [...g.mobs.getChildren()]) {
      const mob = child as Mob;
      if (!mob.active) continue;
      const b = mob.body;
      if (
        !circleHit(origin.x, origin.y, pl.plantRadiusPx, {
          x: b.center.x,
          y: b.center.y,
          r: Math.min(b.halfWidth, b.halfHeight),
        })
      )
        continue;
      plantHits += 1;
      this.strike(mob, plantP, plantHits === 1);
    }
    // 땅 균열 l (그림 표 crackFx)
    const crack = p.crack ? this.swing.playCrack(p.art, origin.x, origin.y, p.crack) : false;
    // 충격파 (회전 시트 — 길이에 맞춰 배율)
    const sheet = P.wave.sheet;
    const def = g.fx.sheet(sheet);
    const timeline = waveTimeline(def, P.wave.travelMs);
    let waveFx = false;
    if (def && g.fx.has(sheet)) {
      const hs = (def as { hitShape?: { lengthPx?: number } }).hitShape;
      const drawnLen = (typeof hs?.lengthPx === 'number' ? hs.lengthPx : def.frameWidth) * artScale(def);
      const angle = Math.atan2(dir.y, dir.x);
      waveFx =
        g.fx.play(sheet, origin.x, origin.y, {
          angle,
          flipY: dir.x < 0,
          depth: DEPTH.FX_GROUND,
          scaleMult: drawnLen > 0 ? pl.waveLengthPx / drawnLen : 1,
        }) !== null;
    } else this.placeholder(origin, dir, pl.waveLengthPx, pl.waveHalfWidthPx);
    this.wave = {
      p: { ...p, damageMult: p.damageMult * P.wave.damageMult },
      origin,
      dir,
      lengthPx: pl.waveLengthPx,
      halfWidthPx: pl.waveHalfWidthPx,
      timeline,
      bornAt: g.playNow(),
      hit: new Set(),
    };
    this.debugLast = {
      time: g.time.now,
      stage: pl.stage,
      origin,
      dir,
      lengthPx: Math.round(pl.waveLengthPx * 10) / 10,
      halfWidthPx: pl.waveHalfWidthPx,
      plantHits,
      crack,
      waveFx,
      waveHits: 0,
    };
  }

  /** 시트가 없을 때: 충격파 사각형 윤곽 */
  private placeholder(origin: Pt, dir: Pt, length: number, half: number): void {
    const g = this.g;
    const gfx = g.add.graphics().setDepth(DEPTH.ATTACK);
    gfx.lineStyle(2, COLORS.SHOCKWAVE, 0.9);
    gfx.setPosition(origin.x, origin.y).setRotation(Math.atan2(dir.y, dir.x));
    gfx.strokeRect(0, -half, length, half * 2);
    g.tweens.add({ targets: gfx, alpha: 0, duration: 260, onComplete: () => gfx.destroy() });
  }

  /** 매 프레임: 앞머리가 지나간 칸의 적 (적마다 1회) */
  update(): void {
    const w = this.wave;
    if (!w) return;
    const e = this.g.playNow() - w.bornAt;
    const front = w.lengthPx * waveFrontRatio(w.timeline, e);
    for (const child of [...this.g.mobs.getChildren()]) {
      const mob = child as Mob;
      if (!mob.active || w.hit.has(mob)) continue;
      const b = mob.body;
      if (
        !waveHit(w.origin, w.dir, front, w.halfWidthPx, {
          x: b.center.x,
          y: b.center.y,
          r: Math.min(b.halfWidth, b.halfHeight),
        })
      )
        continue;
      w.hit.add(mob);
      this.strike(mob, w.p, false);
    }
    if (this.debugLast) this.debugLast.waveHits = w.hit.size;
    if (e >= waveEndMs(w.timeline)) this.wave = null;
  }
}
