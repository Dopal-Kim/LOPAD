/**
 * 우클릭 보조 동작 결과(27라운드: 가드 밀쳐내기 · 그림자 걸음) · 대쉬 시작 연출·잔상 피해 ·
 * 유지형 연출(조준 점선·차지 게이지 · 대쉬 잔상 · 달리기 먼지, 35·45라운드).
 * 60라운드 (57 Q42): 옛 진화 이펙트(질풍 gale 루프·발도 batto·허보 longinvuln·잔상 afterimage·철벽 ironwall) 끔 —
 * 갈래 1단 연격 변화 fx(계약 art §21, 씬 build/branch)가 대신한다.
 */
import Phaser from 'phaser';
import {
  COLORS,
  DEPTH,
  FEEDBACK,
  FEEL,
  PROTOTYPE,
  TILE,
  TRAVERSAL,
  entityDepth,
  fxLitDepth,
} from '../../core/Constants';
import type { GuardReleasedPayload, ShadowStepPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { PALETTE, PLAYER_DATA } from '../../data';
import type { Mob } from '../../objects/Mob';
import type { FxHandle } from '../../systems/fx/fx';
import { fxWeaponColor, hexToInt } from '../../systems/palette';
import { facingOf, progressFrame } from '../../systems/sprites/spriteDefs';
import type { Game } from '../Game';
import { PLAYER_RENDER_SCALE } from '../../systems/weapon/playerScale';

export class MotionFx {
  private aimChargeFx: FxHandle | null = null;
  private lastAimReady = false;
  private dashTrailNextAt = 0;
  /** 45라운드 달리기: 다음 발밑 먼지 시각 · 디버그 횟수 */
  private sprintDustNextAt = 0;
  sprintDustCount = 0;

  constructor(private readonly g: Game) {}

  /** 매 프레임 (일반 진행) */
  update(time: number): void {
    this.updateSprintDust(time);
    this.updateAimFx(time);
    this.updateDashTrail(time);
  }

  /** 정지·선택·전환 중: 유지형 연출을 끈다 */
  stopLoops(): void {
    this.stopAimFx(false);
  }

  /** 디버그 (조준 연출 상태) */
  get aimChargeFrame(): string | number | null {
    return this.g.fx.isActive(this.aimChargeFx) ? this.aimChargeFx!.sprite.frame.name : null;
  }

  // --- 보조 동작 결과 ---

  onGuardReleased(p: GuardReleasedPayload): void {
    const g = this.g;
    const S = gameState.weapon.def.secondary;
    // 56라운드 Q48 칼 가드: 떼도 밀쳐내지 않는다 (반경 0)
    if (S.kind !== 'guard' || S.pushRadiusTiles <= 0) return;
    const now = g.time.now;
    const radius = S.pushRadiusTiles * TILE;
    const counter = gameState.weapon.mods.guardCounterMult ?? 0;
    // 가드 밀쳐내기 충격파(guard_wave, 발 피벗·바라보는 방향·바닥 깊이). 시트가 없으면 링
    const dir = g.player.facingDir;
    if (g.fx.has('guard_wave')) g.fx.play('guard_wave', p.x, p.y, { dir, depth: DEPTH.FX_GROUND });
    else {
      const ring = g.add.graphics().setDepth(DEPTH.ATTACK);
      ring.lineStyle(2, COLORS.GUARD_PUSH, 0.9);
      ring.strokeCircle(p.x, p.y, radius);
      g.tweens.add({ targets: ring, alpha: 0, duration: PROTOTYPE.GUARD_PUSH_MS, onComplete: () => ring.destroy() });
    }
    g.structures.onPush(p.x, p.y, radius);
    for (const child of [...g.mobs.getChildren()]) {
      const m = child as Mob;
      if (!m.active) continue;
      const dx = m.x - p.x;
      const dy = m.y - p.y;
      const d = Math.hypot(dx, dy);
      if (d > radius) continue;
      const nx = d > 0 ? dx / d : 1;
      const ny = d > 0 ? dy / d : 0;
      m.knockback(now, nx, ny, S.pushSpeedTiles * TILE, S.pushMs);
      if (counter > 0) {
        // 철벽: 밀쳐내며 반격
        const { dmg } = g.combat.rollDamage(counter);
        if (g.combat.hitMob(m, dmg, { crit: false, dirX: nx, dirY: ny, knock: false })) g.progress.onKill(m, 'attack');
      }
    }
  }

  onShadowStep(p: ShadowStepPayload): void {
    const g = this.g;
    const S = gameState.weapon.def.secondary;
    if (S.kind !== 'shadowstep') return;
    // 57라운드 비도(단검 2단): 박힌 단검이 있으면 그 자리로
    const knife = g.build.branch.takeStuckKnife();
    if (knife) {
      g.player.teleportTo(knife.x, knife.y);
      this.stepRibbon(p.x, p.y, knife.x, knife.y);
      g.build.onShadowStep(p.x, p.y, knife.x, knife.y);
      return;
    }
    const target = g.combat.nearestMob(p.x, p.y, S.rangeTiles * TILE);
    const [pw, ph] = PLAYER_DATA.size;
    const half = Math.max(pw, ph) / 2;
    let dest: { x: number; y: number } | null = null;
    if (target) {
      const dx = target.x - p.x;
      const dy = target.y - p.y;
      const d = Math.hypot(dx, dy) || 1;
      const nx = dx / d;
      const ny = dy / d;
      const off = Math.max(target.body.width, target.body.height) / 2 + half + 2;
      const behind = { x: target.x + nx * off, y: target.y + ny * off };
      const front = { x: target.x - nx * off, y: target.y - ny * off };
      dest = g.world.isWalkableAt(behind.x, behind.y) ? behind : g.world.isWalkableAt(front.x, front.y) ? front : null;
    } else {
      const fx = p.facingX || 1;
      const fy = p.facingY;
      // 바라보는 방향으로 fallbackTiles, 막히면 한 칸씩 줄인다
      for (let tiles = S.fallbackTiles; tiles > 0; tiles -= 1) {
        const c = { x: p.x + fx * tiles * TILE, y: p.y + fy * tiles * TILE };
        if (g.world.isWalkableAt(c.x, c.y)) {
          dest = c;
          break;
        }
      }
    }
    if (!dest) return;
    // 출발 잔상: shadowstep_ghost(출발 위치 고정, 보던 방향, 플레이어 아래). 시트가 없으면 사각형
    if (g.fx.has('shadowstep_ghost')) {
      g.fx.play('shadowstep_ghost', p.x, p.y, {
        dir: facingOf(p.facingX, p.facingY, g.player.facingDir),
        depth: entityDepth(p.y) - DEPTH.OVERLAY_STEP,
      });
    } else {
      const ghost = g.add.rectangle(p.x, p.y, pw, ph, COLORS.PLAYER_SHADOW, 0.6).setDepth(DEPTH.ATTACK);
      g.tweens.add({ targets: ghost, alpha: 0, duration: PROTOTYPE.SHADOW_STEP_MS, onComplete: () => ghost.destroy() });
    }
    g.player.teleportTo(dest.x, dest.y);
    // 57라운드: 이동기 사건 (완벽 회피 무장 · 돌파 경로 베기 · 열풍)
    g.build.onShadowStep(p.x, p.y, dest.x, dest.y);
    // 56라운드 Q38: 리본은 돌진류에만 — 그림자 걸음 출발 → 도착을 짧게 긋는다
    this.stepRibbon(p.x, p.y, dest.x, dest.y);
    // 56라운드 Q16: 그 적 뒤에 서면 낙인 전부 폭발
    if (target && dest !== null) g.strikes.brands.onShadowStep(target);
  }

  /** 출발 → 도착 리본 (플레이 시계로 SHADOWSTEP_RIBBON_MS 동안 머리가 이동) */
  private stepRibbon(x0: number, y0: number, x1: number, y1: number): void {
    const g = this.g;
    const sheet = gameState.weapon.def.feel?.ribbon;
    if (!sheet) return;
    const t0 = g.playNow();
    const ms = FEEDBACK.SHADOWSTEP_RIBBON_MS;
    const up = FEEL.SECONDARY.BODY_CENTER_UP_PX;
    g.ribbons.start(
      (t) => {
        const k = (t - t0) / ms;
        if (k > 1) return null;
        const c = Math.max(0, k);
        return { x: x0 + (x1 - x0) * c, y: y0 - up + (y1 - y0) * c };
      },
      { sheet, depth: fxLitDepth(entityDepth(y1) + DEPTH.OVERLAY_STEP) },
    );
  }

  /**
   * 대쉬 시작: 출발 먼지(dash_dust, 고정) · 잔상 피해 영역(대쉬 경로). (옛 발도술·허보·잔상 진화 fx 는 57 Q42 로 끔)
   */
  onPlayerDashed(p: { dirX: number; dirY: number; x: number; y: number }): void {
    const g = this.g;
    const dir = facingOf(p.dirX, p.dirY, g.player.facingDir);
    const now = g.time.now;
    if (g.fx.has('dash_dust')) g.fx.play('dash_dust', p.x, p.y, { dir, depth: DEPTH.FX_GROUND });
    this.dashTrailNextAt = now; // 첫 dash_trail 은 다음 update 에서
    g.structures.onDash(p.x, p.y, p.dirX, p.dirY, PLAYER_DATA.dash.distanceTiles * TILE);
    const mult = gameState.weapon.mods.dashTrailDamageMult;
    if (!mult) return;
    const D = PLAYER_DATA.dash;
    const len = D.distanceTiles * TILE;
    const [pw] = PLAYER_DATA.size;
    const cx = p.x + p.dirX * len * 0.5;
    const cy = p.y + p.dirY * len * 0.5;
    const horizontal = Math.abs(p.dirX) >= Math.abs(p.dirY);
    const w = horizontal ? len : pw;
    const h = horizontal ? pw : len;
    const zone = g.add.rectangle(cx, cy, w, h, COLORS.DASH_TRAIL, 0.35).setDepth(DEPTH.ATTACK);
    g.physics.add.existing(zone);
    (zone.body as Phaser.Physics.Arcade.Body).setAllowGravity(false);
    const hit = new Set<Mob>();
    const overlap = g.physics.add.overlap(zone, g.mobs, (_z, m) => {
      const mob = m as Mob;
      if (hit.has(mob)) return;
      hit.add(mob);
      const { dmg } = g.combat.rollDamage(mult);
      if (g.combat.hitMob(mob, dmg, { crit: false, dirX: p.dirX, dirY: p.dirY })) g.progress.onKill(mob, 'dashAttack');
    });
    g.time.delayedCall(D.durationMs, () => {
      g.physics.world.removeCollider(overlap);
      g.tweens.add({ targets: zone, alpha: 0, duration: PROTOTYPE.SLASH_TRAIL_MS, onComplete: () => zone.destroy() });
    });
  }

  // --- 유지형 연출 ---

  /**
   * 조준 중: aim_line(몸 중심 → 커서, 길이 AIM_LINE_TILES) + aim_charge(진행도 프레임 = min(5, floor(progress×5))).
   * 차지 완료 후 발사되면 5프레임을 AIM_CHARGE_HOLD_MS 유지, 취소면 즉시 제거
   */
  private updateAimFx(time: number): void {
    const g = this.g;
    const S = FEEL.SECONDARY;
    const player = g.player;
    if (player.action !== 'aim') {
      if (g.aimLine.visible || this.aimChargeFx) this.stopAimFx(this.lastAimReady);
      return;
    }
    const progress = player.aimProgress(time);
    this.lastAimReady = progress >= 1;
    const c = player.getCenter();
    const cx = c.x;
    const cy = player.y - S.BODY_CENTER_UP_PX;
    // aim_line stateFrames: 차지 중 f0 / 완료 f1 (43라운드 B) · 갈래 조준선은 진행도 프레임
    // 51라운드 저격: 갈래 조준선(aim_line_snipe, 진행도 구동)이 있으면 그것
    // 56라운드 Q20: 오래 쥐면 조준선이 흔들린다 (화살도 같은 각으로 나간다)
    const angle = player.aimAngle + player.aimJitter(time);
    g.aimLine.show(cx, cy, angle, S.AIM_LINE_TILES * TILE, progress, g.strikes.bow.aimLineId);
    if (!g.fx.has('aim_charge')) return;
    // aim_charge 진행도 프레임 = min(마지막, floor(progress × 5)) — 6프레임 시트의 f5 = 완료
    const frame = progressFrame(progress, g.fx.framesOf('aim_charge'), S.AIM_CHARGE_DIVISOR);
    if (!g.fx.isActive(this.aimChargeFx)) {
      this.aimChargeFx = g.fx.play('aim_charge', cx, cy, {
        staticFrame: frame,
        follow: player,
        followOffset: { x: 0, y: -S.BODY_CENTER_UP_PX },
        depthOffset: DEPTH.OVERLAY_STEP * 3,
      });
    } else g.fx.setFrame(this.aimChargeFx, 'aim_charge', frame);
  }

  /** 조준 끝: 점선 제거, 차지 게이지는 발사(완료)면 짧게 유지 후 제거, 취소면 즉시 */
  stopAimFx(fired: boolean): void {
    const g = this.g;
    g.aimLine.hide();
    if (g.fx.isActive(this.aimChargeFx))
      g.fx.stop(this.aimChargeFx, fired ? FEEL.SECONDARY.AIM_CHARGE_HOLD_MS : 0, false);
    this.aimChargeFx = null;
    this.lastAimReady = false;
  }

  /**
   * 대쉬 중 DASH_TRAIL_INTERVAL_MS 마다 현재 위치에 dash_trail(고정, 대쉬 방향, 플레이어 아래).
   * 발도술·허보·잔상 노드일 때만 그 무기 W1 로 틴트 (JSON tint.when). 시트가 어두운 무채라 JSON tint.method 의 setTintFill(평면)
   */
  private updateDashTrail(time: number): void {
    const g = this.g;
    const player = g.player;
    if (player.action !== 'dash' || time < this.dashTrailNextAt || !g.fx.has('dash_trail')) return;
    const S = FEEL.SECONDARY;
    this.dashTrailNextAt = time + S.DASH_TRAIL_INTERVAL_MS;
    const d = player.dashDir;
    // 55라운드 Q13: v3 대쉬 잔상은 따뜻한 재 그대로 (DASH_TRAIL_TINT false 면 노드 틴트 없음)
    const tinted = S.DASH_TRAIL_TINT && S.DASH_TRAIL_TINT_NODES.some((id) => gameState.weapon.path.includes(id));
    const hex = tinted ? fxWeaponColor(PALETTE, gameState.weapon.id, S.DASH_TRAIL_RAMP_INDEX) : null;
    const method = g.fx.sheet('dash_trail')?.tint?.method ?? '';
    g.fx.play('dash_trail', player.x, player.y, {
      dir: facingOf(d.x, d.y, player.facingDir),
      depth: entityDepth(player.y) - DEPTH.OVERLAY_STEP,
      tint: hex ? hexToInt(hex) : undefined,
      tintFill: method.includes('setTintFill'),
      scaleMult: PLAYER_RENDER_SCALE,
    });
  }

  /** 달리는 동안 발밑에 dash_dust 를 작게·옅게 주기적으로 (시트가 없으면 작은 회색 점) */
  private updateSprintDust(time: number): void {
    const g = this.g;
    const player = g.player;
    if (!player.sprinting || time < this.sprintDustNextAt) return;
    const D = TRAVERSAL.SPRINT_DUST;
    this.sprintDustNextAt = time + D.INTERVAL_MS;
    this.sprintDustCount += 1;
    const v = player.body.velocity;
    const x = player.x;
    const y = player.y;
    if (g.fx.has(D.SHEET)) {
      g.fx.play(D.SHEET, x, y, {
        dir: facingOf(v.x, v.y, player.facingDir),
        depth: DEPTH.FX_GROUND,
        scaleMult: D.SCALE_MULT,
        alpha: D.ALPHA,
        hooks: false,
      });
      return;
    }
    const [, h] = PLAYER_DATA.size;
    const dot = g.add.circle(x, y + h / 2, D.DOT_RADIUS, D.DOT_COLOR, D.ALPHA).setDepth(DEPTH.FX_GROUND);
    g.tweens.add({ targets: dot, alpha: 0, duration: D.DOT_MS, onComplete: () => dot.destroy() });
  }
}
