/**
 * 플레이어 공격 (PLAYER_ATTACKED): 근접 3연격 판정 (48라운드) · 대검 내리찍기 (49라운드) · 진화 부가 효과(쌍격·지진 2단).
 * 51라운드 정리: 활 = `BowShots`, 잔월·출혈 = `StrikeDots`. 53라운드 정리: 판정 모양·휘두름 이펙트·잔상 리본 = `SwingFx`.
 * 피해 계산·피격 연출은 GameCombat.
 */
import Phaser from 'phaser';
import { COLORS, DEPTH, ENEMY_FX, FEEL, PROTOTYPE } from '../../core/Constants';
import type { PlayerAttackPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { Mob } from '../../objects/Mob';
import type { Projectile } from '../../objects/Projectile';
import { facingAngle, hitShapeBounds, rotateDir, shapeHit, type HitShape } from '../../systems/combo';
import type { FxHandle } from '../../systems/fx';
import { facingOf, hitFrameOffsets, radiusFitScale, type Facing } from '../../systems/spriteDefs';
import { comboFxId, slamFxId, slashFxId } from '../../systems/fxIds';
import type { Game } from '../Game';
import { BowShots } from './BowShots';
import { StrikeDots } from './StrikeDots';
import { SwingFx } from './SwingFx';
import { HIT_ORIGIN_UP_PX, evolutionFxId, isFinisher, pathFx } from './shared';

export class PlayerStrikes {
  /** 디버그: 마지막 공격 이벤트 · 최근 근접 판정 (모양·원점·맞은 수) */
  debugLastAttack: unknown = null;
  debugLastSwing: unknown = null;
  /** 디버그 (51라운드 템포 실측): 최근 공격 시각 (게임 시간 ms) */
  readonly attackLog: { time: number; kind: string; comboIndex: number | null; firstStrike: string | null }[] = [];
  readonly bow: BowShots;
  readonly dots: StrikeDots;
  private readonly swing: SwingFx;
  private giantFx: FxHandle | null = null;

  constructor(private readonly g: Game) {
    this.bow = new BowShots(g);
    this.dots = new StrikeDots(g);
    this.swing = new SwingFx(g);
  }

  private pathFx(...candidates: string[]): string | null {
    return pathFx(this.g.fx, ...candidates);
  }

  /** 씬 진행 중(정지·사망 아님)인지 — 지연 실행 콜백 공통 확인 */
  private get live(): boolean {
    return this.g.scene.isActive() && !this.g.frozen && !gameState.gameOver;
  }

  onPlayerAttacked(p: PlayerAttackPayload): void {
    const g = this.g;
    this.debugLastAttack = { ...p, time: g.time.now };
    this.attackLog.push({
      time: g.time.now,
      kind: p.kind,
      comboIndex: p.comboIndex ?? null,
      firstStrike: p.firstStrike ?? null,
    });
    if (this.attackLog.length > 40) this.attackLog.shift();
    const weapon = gameState.weapon;
    if (weapon.def.kind === 'ranged') {
      this.bow.fire(p);
      return;
    }
    const mods = weapon.mods;
    // 48라운드 3연격: 판정은 휘두름 프레임(hitFrames[0]) 시작에, 지진 2단·충격파는 마지막 타에서만
    const combo = p.comboIndex !== undefined;
    const finisher = isFinisher(p);
    this.swing.play(p);
    this.playGiantFx(p);
    const strike = () => {
      if (!this.live) return;
      // 49라운드 내리찍기: 착지점 = 그 순간 발 피벗 + 시트 impactOffsetPx
      const at = p.slam
        ? { ...p, x: g.player.x + p.slam.offsetX, y: g.player.y + p.slam.offsetY }
        : combo
          ? { ...p, x: g.player.x, y: g.player.y }
          : p;
      this.meleeSwing(at);
      // 쌍격·난무: 추가 타격. 시트 hitFrames 가 있으면 그 프레임 시작 간격(43라운드 B), 없으면 TWIN_DELAY_MS 간격
      const hits = Math.max(1, mods.hits ?? 1);
      const multiFx = this.pathFx('dance', 'twin');
      const offsets = FEEL.SYNC_HIT_FRAMES && multiFx ? hitFrameOffsets(g.fx.sheet(multiFx), hits) : null;
      for (let i = 1; i < hits; i++) {
        g.time.delayedCall(offsets?.[i] ?? PROTOTYPE.TWIN_DELAY_MS * i, () => {
          if (g.scene.isActive() && !g.frozen) this.meleeSwing({ ...at, x: g.player.x, y: g.player.y });
        });
      }
      // 지진: 충격파 2단 (quake 시트는 1단에서 한 번만 — 3프레임 시작이 2단 판정 시점)
      const second = mods.shockwaveSecond;
      if (mods.shockwave && second && finisher) {
        g.time.delayedCall(second.delayMs, () => {
          if (g.scene.isActive() && !g.frozen)
            this.meleeSwing(
              {
                ...at,
                x: g.player.x,
                y: g.player.y,
                sizeMult: at.sizeMult * second.sizeMult,
                damageMult: at.damageMult * second.damageMult,
              },
              true,
            );
        });
      }
    };
    const hitDelay = combo ? p.swingDelayMs : 0;
    if (hitDelay > 0) g.time.delayedCall(hitDelay, strike);
    else strike();
  }

  /** 거인(2차): 공격 애니 동안 플레이어 아래에서 슈퍼아머 오라 루프 (공격 애니 = 쿨다운에 맞춤) */
  private playGiantFx(p: PlayerAttackPayload): void {
    const g = this.g;
    const id = this.pathFx('giant');
    if (!id) return;
    if (g.fx.isActive(this.giantFx)) g.fx.stop(this.giantFx, 0, false);
    this.giantFx = g.fx.play(id, g.player.x, g.player.y, {
      follow: g.player,
      depthOffset: -DEPTH.OVERLAY_STEP,
      durationMs: p.durationMs ?? gameState.weapon.hitbox.cooldownMs,
    });
  }

  // --- 근접 이펙트 ---

  /**
   * 49라운드 대검 내리찍기 충격파 이펙트 `fx/<무기>_slam` (anchor hitbox_center = 판정 원 중심, 바닥 깊이,
   * 배율 = 판정 반경 / 그림 반경 — 정수일 때만, boss_slam 규약). 섬광·흔들림은 시트 JSON. 시트가 없으면 false
   */
  private playSlamImpactFx(x: number, y: number, radiusPx: number, dirX: number, dirY: number): boolean {
    const fx = this.g.fx;
    const id = slamFxId(gameState.weapon.id);
    if (!fx.has(id)) return false;
    const def = fx.sheet(id);
    const scaleMult = radiusFitScale(radiusPx, def?.hitRadiusPx ?? ENEMY_FX.SLAM_BASE_RADIUS_PX);
    const dir = facingOf(dirX, dirY, this.g.player.facingDir);
    return fx.play(id, x, y, { dir, depth: DEPTH.FX_GROUND, scaleMult }) !== null;
  }

  // --- 근접 판정 ---

  private meleeSwing(p: PlayerAttackPayload, secondWave = false): void {
    const g = this.g;
    const weapon = gameState.weapon;
    const mods = weapon.mods;
    const hb = weapon.hitbox;
    // 48라운드 3연격: 몸 중심(발 위 10px) 부채꼴·찌르기 판정. 물리 영역은 외접 사각형이고 겹친 적을 모양으로 다시 거른다
    const shape = this.swing.shape(p);
    const facing = facingOf(p.dirX, p.dirY, g.player.facingDir);
    const ox = p.x;
    // 49라운드 내리찍기: 원 중심 = 착지점 그대로 (몸 중심 보정 없음)
    const oy = p.slam ? p.y : p.y - HIT_ORIGIN_UP_PX;
    let cx: number;
    let cy: number;
    let w: number;
    let h: number;
    if (shape) {
      const b = hitShapeBounds(ox, oy, p.dirX, p.dirY, shape, facing);
      cx = b.x + b.w / 2;
      cy = b.y + b.h / 2;
      w = Math.max(1, b.w);
      h = Math.max(1, b.h);
    } else {
      cx = p.x + p.dirX * hb.reach * p.sizeMult;
      cy = p.y + p.dirY * hb.reach * p.sizeMult;
      // Arcade 바디는 축 정렬 사각형이라 지배적인 축에 맞춰 폭·높이를 바꿔 근사한다.
      const horizontal = Math.abs(p.dirX) >= Math.abs(p.dirY);
      w = (horizontal ? hb.width : hb.height) * p.sizeMult;
      h = (horizontal ? hb.height : hb.width) * p.sizeMult;
    }
    const finisher = isFinisher(p);
    const activeMs = p.activeMs ?? hb.activeMs;
    // 47라운드: 타격형 구조물·화로 점화·불붙은 무기의 웅덩이 점화
    g.structures.onMeleeSwing(cx, cy, w, h, p.dirX, p.dirY);
    // 베기 시트가 있으면 판정 사각형은 보이지 않게(판정만), 없으면 기존 플레이스홀더 표시
    const evoFx = evolutionFxId(g.fx);
    const swingFx = this.pathFx('wide', 'iai', 'dance', 'twin');
    const comboFx = p.comboIndex !== undefined ? comboFxId(weapon.id, p.comboIndex + 1) : null;
    const hasSwingArt = g.fx.has(slashFxId(weapon.id)) || swingFx !== null || (comboFx !== null && g.fx.has(comboFx));
    // 연격 판정은 모양이라 사각형 플레이스홀더를 그리지 않는다 (시트가 없으면 모양 윤곽)
    const zone = g.add.rectangle(cx, cy, w, h, COLORS.ATTACK, hasSwingArt || shape ? 0 : 0.6).setDepth(DEPTH.ATTACK);
    if (shape && !hasSwingArt) this.drawShapeOutline(ox, oy, p.dirX, p.dirY, shape, facing);
    // 궤적·충격파: 시트가 있으면 시트, 없으면 Graphics 플레이스홀더
    if (mods.slashTrail && !swingFx) this.drawSlashTrail(cx, cy, p.dirX, p.dirY, Math.max(w, h));
    if (mods.shockwave && finisher) {
      // 49라운드 내리찍기: fx/<무기>_slam 이 파쇄(crush) 대신 (섬광·흔들림은 시트). 지진·분쇄 2차 이펙트는 그 위에 그대로
      const slamFx =
        p.slam && !secondWave && shape?.kind === 'arc'
          ? this.playSlamImpactFx(cx, cy, shape.radius, p.dirX, p.dirY)
          : false;
      // 지진(quake)·분쇄(pulverize) 가 파쇄(crush) 대신. quake 는 1단에서 한 번(3프레임 = 2단 시점), 2단은 다시 안 그린다
      const shockFx = slamFx ? this.pathFx('quake', 'pulverize') : this.pathFx('quake', 'pulverize', 'crush');
      if (shockFx === 'quake' && secondWave) {
        /* 1단에서 재생한 quake 의 3~5프레임이 2단 링 */
      } else if (shockFx) g.fx.play(shockFx, cx, cy, { depth: DEPTH.FX_GROUND });
      else if (!slamFx) g.combat.drawShockwave(cx, cy, Math.max(w, h));
      if (!slamFx) g.shake.add(g.time.now, FEEL.SHAKE.SHOCKWAVE.PX, FEEL.SHAKE.SHOCKWAVE.MS);
    }
    // 중압: 적중 판정 시작에 히트박스 중심 아래 6px (피벗 = 바닥 타격점)
    if (evoFx === 'weight') g.fx.play('weight', cx, cy + PROTOTYPE.WEIGHT_FX_DROP_PX, { depth: DEPTH.ATTACK });
    g.physics.add.existing(zone);
    (zone.body as Phaser.Physics.Arcade.Body).setAllowGravity(false);

    const hit = new Set<Mob>();
    const swingLog = {
      shape,
      origin: { x: ox, y: oy },
      dir: { x: p.dirX, y: p.dirY },
      facing,
      bounds: { cx, cy, w, h },
      comboIndex: p.comboIndex ?? null,
      activeMs,
      hits: 0,
      time: g.time.now,
    };
    this.debugLastSwing = swingLog;
    const overlap = g.physics.add.overlap(zone, g.mobs, (_z, m) => {
      const mob = m as Mob;
      if (hit.has(mob)) return;
      if (shape) {
        const b = mob.body;
        const target = { x: b.center.x, y: b.center.y, r: Math.min(b.halfWidth, b.halfHeight) };
        if (!shapeHit(ox, oy, p.dirX, p.dirY, shape, target, facing)) return;
      }
      hit.add(mob);
      swingLog.hits += 1;
      this.applyMeleeHit(mob, p);
    });
    // 분쇄: 충격파 범위의 적 투사체 소멸
    const clear =
      mods.shockwave && finisher && mods.shockwaveClearsProjectiles
        ? g.physics.add.overlap(zone, g.projectiles, (_z, pr) => {
            const proj = pr as Projectile;
            if (proj.active && !proj.reflected) proj.deactivate();
          })
        : null;
    // 잔월: 궤적이 남아 지속 피해
    if (mods.trailDot) this.dots.leaveTrailDot(p, { cx, cy, w, h }, swingFx);

    g.time.delayedCall(activeMs, () => {
      g.physics.world.removeCollider(overlap);
      if (clear) g.physics.world.removeCollider(clear);
      zone.destroy();
    });
  }

  /** 연격 판정 모양 윤곽 (시트가 없을 때 플레이스홀더) */
  private drawShapeOutline(ox: number, oy: number, dirX: number, dirY: number, shape: HitShape, facing: Facing): void {
    const g = this.g.add.graphics().setDepth(DEPTH.ATTACK);
    g.lineStyle(1, COLORS.ATTACK, 0.8);
    g.fillStyle(COLORS.ATTACK, 0.25);
    if (shape.kind === 'arc') {
      const c = rotateDir(dirX, dirY, facingAngle(shape.centerDeg, facing));
      const a = Math.atan2(c.y, c.x);
      const half = Phaser.Math.DegToRad(shape.arcDeg / 2);
      g.slice(ox, oy, shape.radius, a - half, a + half, false);
      g.fillPath();
      g.strokePath();
    } else {
      const d = rotateDir(dirX, dirY, facingAngle(shape.angleDeg, facing));
      const px = -d.y * (shape.width / 2);
      const py = d.x * (shape.width / 2);
      const sx = ox + d.x * shape.fromPx;
      const sy = oy + d.y * shape.fromPx;
      const ex = sx + d.x * shape.length;
      const ey = sy + d.y * shape.length;
      const pts = [
        new Phaser.Math.Vector2(sx + px, sy + py),
        new Phaser.Math.Vector2(ex + px, ey + py),
        new Phaser.Math.Vector2(ex - px, ey - py),
        new Phaser.Math.Vector2(sx - px, sy - py),
      ];
      g.fillPoints(pts, true);
      g.strokePoints(pts, true);
    }
    this.g.tweens.add({ targets: g, alpha: 0, duration: PROTOTYPE.SLASH_TRAIL_MS, onComplete: () => g.destroy() });
  }

  /** 진화 무기의 베기 궤적 (플레이스홀더 연출. 정식 이펙트는 아트 파트) */
  private drawSlashTrail(cx: number, cy: number, dirX: number, dirY: number, length: number): void {
    const g = this.g.add.graphics().setDepth(DEPTH.ATTACK);
    const angle = Math.atan2(dirY, dirX);
    g.lineStyle(2, COLORS.ATTACK, 0.9);
    g.beginPath();
    g.arc(cx - dirX * length * 0.3, cy - dirY * length * 0.3, length * 0.9, angle - 0.6, angle + 0.6, false);
    g.strokePath();
    this.g.tweens.add({ targets: g, alpha: 0, duration: PROTOTYPE.SLASH_TRAIL_MS, onComplete: () => g.destroy() });
  }

  /** 근접 타격 1회: 피해 → (사망) 또는 중압 경직·출혈 */
  private applyMeleeHit(mob: Mob, p: PlayerAttackPayload): void {
    const g = this.g;
    const now = g.time.now;
    const mods = gameState.weapon.mods;
    const stunnedByParry = mob.isParryStunned(now);
    const { dmg, crit } = g.combat.rollDamage(p.damageMult, p.forceCrit, p.kind);
    // 2차 전용 치명 이펙트: 급소(대쉬 베기 적중) → dashcrit, 암살(그림자 걸음 직후) → assassin. 둘 다 crit_burst 대신
    const critFx = p.primed ? this.pathFx('assassin') : p.kind === 'dashAttack' ? this.pathFx('dashcrit') : null;
    // 51라운드 Q4: 대검 끌어내기 첫 타 = 크게 밀쳐냄
    const knockMult = p.knockbackMult;
    if (g.combat.hitMob(mob, dmg, { crit, dirX: p.dirX, dirY: p.dirY, critFx, knockMult })) {
      g.progress.onKill(mob, stunnedByParry ? 'parry' : p.kind === 'aimed' ? 'attack' : p.kind);
      return;
    }
    g.structures.onMobHit(mob, false);
    if (mods.hitStunMs) mob.stun(now, mods.hitStunMs, 'hit');
    if (mods.bleed) this.dots.applyBleed(mob);
  }

  // --- 매 프레임: 추적 화살·저격 꼬리 · 잔월 · 출혈 ---

  update(time: number, delta: number): void {
    this.bow.update(delta);
    this.dots.update(time);
  }
}
