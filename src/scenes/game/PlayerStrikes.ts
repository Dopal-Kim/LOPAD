/**
 * 플레이어 공격 (PLAYER_ATTACKED): 근접 연격 판정 (48라운드) · 대검 내리찍기 (49라운드) · 진화 부가 효과(쌍격·지진 2단).
 * 51라운드 정리: 활 = `BowShots`, 잔월·출혈 = `StrikeDots`. 53라운드 정리: 판정 모양·휘두름 이펙트·잔상 리본 = `SwingFx`.
 * 55라운드 §17: 타별 판정 모양(호·쐐기+충격원·찌르기·고리) · 후속 판정(칼 잔상 베기·차지 충격파 링 — 씬 시계 지연이라 히트스톱 동안 멈춤)
 * · 내려찍기 끝점 바닥 충격 · 판정 모양 디버그 오버레이(`HitShapeOverlay`). 피해 계산·피격 연출은 GameCombat.
 */
import Phaser from 'phaser';
import { COLORS, DEPTH, ENEMY_FX, FEEL, PROTOTYPE } from '../../core/Constants';
import type { PlayerAttackPayload, PlayerChargePayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { ComboFollowUpDef } from '../../data/types';
import type { Mob } from '../../objects/Mob';
import type { Projectile } from '../../objects/Projectile';
import { hitShapeBounds, shapeCenterPoint, shapeHit, type Pt } from '../../systems/hitShapes';
import type { FxHandle } from '../../systems/fx';
import { facingOf, hitFrameOffsets, radiusFitScale } from '../../systems/spriteDefs';
import { slamFxId, slashFxId } from '../../systems/fxIds';
import { isBackswing, isHeavyStrike } from '../../systems/hitFeel';
import type { Game } from '../Game';
import { BowShots } from './BowShots';
import { HitShapeOverlay } from './HitShapeOverlay';
import { StrikeDots } from './StrikeDots';
import { SwingFx } from './SwingFx';
import { HIT_ORIGIN_UP_PX, evolutionFxId, isFinisher, isMeleeStrike, pathFx, shapeFacing } from './shared';

/** 판정 한 번의 옵션: 지진 2단 · 55라운드 후속 판정(원점·모양 덮어쓰기) */
interface SwingOpts {
  secondWave?: boolean;
  follow?: ComboFollowUpDef;
  origin?: Pt;
  /** 후속 판정 전용 이펙트를 이미 띄웠다 (플레이스홀더 없음) */
  followFx?: boolean;
}

/** 디버그로 남기는 최근 판정 수 */
const SWING_LOG_MAX = 12;

export class PlayerStrikes {
  /** 디버그: 마지막 공격 이벤트 · 최근 근접 판정 (모양·원점·맞은 수) */
  debugLastAttack: unknown = null;
  debugLastSwing: unknown = null;
  /** 55라운드 디버그: 최근 판정들 (후속 판정 포함 — 잔상 베기·충격파 링 시각·맞은 수) */
  readonly swingLog: Record<string, unknown>[] = [];
  readonly overlay: HitShapeOverlay;
  /** 디버그: 마지막 차지 단계 번쩍임 이펙트를 재생했는가 */
  chargeFlashFx = false;
  /** 디버그 (51라운드 템포 실측): 최근 공격 시각 (게임 시간 ms) */
  readonly attackLog: { time: number; kind: string; comboIndex: number | null; firstStrike: string | null }[] = [];
  readonly bow: BowShots;
  readonly dots: StrikeDots;
  private readonly swing: SwingFx;

  /** 디버그: 마지막 휘두름 이펙트 (55라운드 — 시트·단계·배율·띄운 시각·리본 방식) */
  get debugSwingFx(): unknown {
    return this.swing.debugLast;
  }
  private giantFx: FxHandle | null = null;

  constructor(private readonly g: Game) {
    this.bow = new BowShots(g);
    this.dots = new StrikeDots(g);
    this.swing = new SwingFx(g);
    this.overlay = new HitShapeOverlay(g);
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
    const combo = isMeleeStrike(p);
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
      const main = this.meleeSwing(at);
      // 55라운드 §17 후속 판정: 칼 잔상 베기(150ms 뒤 같은 호 50%) · 차지 3단 충격파 링(끝점). 씬 시계라 히트스톱 동안 멈춘다
      for (const fu of p.followUps ?? []) {
        // 전용 이펙트는 그 판정(정지) 프레임이 후속 판정 시각에 오게 먼저 띄운다 (칼 잔상: 320ms 띄움 → 350ms 판정)
        const lead = this.swing.followUpLeadMs(fu.art);
        const fuAt = fu.at === 'impact' ? (main.impact ?? undefined) : undefined;
        if (lead !== null)
          g.time.delayedCall(Math.max(0, fu.delayMs - lead), () => {
            if (this.live) this.swing.playFollowUpFx(fu.art, at.dirX, at.dirY, fuAt);
          });
        g.time.delayedCall(fu.delayMs, () => {
          if (!this.live) return;
          const origin = fuAt;
          this.meleeSwing(
            {
              ...at,
              x: g.player.x,
              y: g.player.y,
              damageMult: at.damageMult * fu.damageMult,
              activeMs: fu.activeMs ?? at.activeMs,
              hitShape: fu.hitShape ?? at.hitShape,
              followUps: undefined,
            },
            { follow: fu, origin, followFx: lead !== null },
          );
        });
      }
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
              { secondWave: true },
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

  /** 판정 한 번. 반환 = 끝점(쐐기 충격원·고리 중심, 없으면 null) — 후속 판정 원점 */
  private meleeSwing(p: PlayerAttackPayload, opts: SwingOpts = {}): { impact: Pt | null } {
    const g = this.g;
    const weapon = gameState.weapon;
    const mods = weapon.mods;
    const hb = weapon.hitbox;
    const secondWave = Boolean(opts.secondWave);
    const follow = opts.follow ?? null;
    // 48라운드 3연격: 몸 중심(발 위 10px) 부채꼴·찌르기 판정. 물리 영역은 외접 사각형이고 겹친 적을 모양으로 다시 거른다
    const shape = this.swing.shape(p);
    const facing = shapeFacing(p, facingOf(p.dirX, p.dirY, g.player.facingDir));
    // 49라운드 내리찍기: 원 중심 = 착지점 그대로 (몸 중심 보정 없음). 55라운드 후속 판정 'impact' = 본 타 끝점
    const ox = opts.origin?.x ?? p.x;
    const oy = opts.origin?.y ?? (p.slam ? p.y : p.y - HIT_ORIGIN_UP_PX);
    const impact = shape ? shapeCenterPoint(ox, oy, p.dirX, p.dirY, shape, facing) : null;
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
    // 후속 판정은 충격파 갈래·진화 베기를 다시 부르지 않는다
    const finisher = isFinisher(p) && !follow;
    const activeMs = p.activeMs ?? hb.activeMs;
    // 47라운드: 타격형 구조물·화로 점화·불붙은 무기의 웅덩이 점화
    g.structures.onMeleeSwing(cx, cy, w, h, p.dirX, p.dirY);
    // 54라운드: 보스방 — 약점 잔 · 술통 방향 바꾸기 · 쓰러진 촛대 다시 켜기
    g.bossArena?.onMeleeSwing(cx, cy, w, h, p.dirX, p.dirY);
    // 베기 시트가 있으면 판정 사각형은 보이지 않게(판정만), 없으면 기존 플레이스홀더 표시
    const evoFx = evolutionFxId(g.fx);
    const swingFx = this.pathFx('wide', 'iai', 'dance', 'twin');
    // 그림이 있는가: 베기·진화 시트, 내리찍기 충격 시트, 이 공격의 휘두름 이펙트(SwingFx 가 고른 것)
    const hasSwingArt =
      g.fx.has(slashFxId(weapon.id)) ||
      swingFx !== null ||
      (p.slam ? g.fx.has(slamFxId(weapon.id)) : this.swing.lastFxLoaded);
    // 연격 판정은 모양이라 사각형 플레이스홀더를 그리지 않는다 (시트가 없으면 모양 윤곽)
    const zone = g.add.rectangle(cx, cy, w, h, COLORS.ATTACK, hasSwingArt || shape ? 0 : 0.6).setDepth(DEPTH.ATTACK);
    if (shape) {
      this.overlay.debug(ox, oy, p.dirX, p.dirY, shape, facing, activeMs, follow !== null);
      // 후속 판정 이펙트 (잔상 베기 전용 fx) — 없으면 윤곽 플레이스홀더 · 고리는 충격파 그림
      const followFx = Boolean(opts.followFx);
      // 55라운드 내려찍기 끝점 바닥 충격 (본 타만)
      const impactFx =
        !follow && !secondWave && shape.kind === 'wedge' && shape.impact !== null && impact !== null
          ? this.swing.playImpactFx(
              p.art,
              impact.x,
              impact.y,
              shape.impact.radius,
              p.dirX,
              p.dirY,
              p.shapeScale?.impactMult,
            )
          : false;
      if (follow && !followFx && shape.kind === 'ring' && impact)
        g.combat.drawShockwave(impact.x, impact.y, shape.radius);
      else if (follow ? !followFx : !hasSwingArt && !impactFx)
        this.overlay.placeholder(ox, oy, p.dirX, p.dirY, shape, facing);
    }
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
      // 55라운드: 내려찍기 쐐기는 충격파를 끝점에
      const sx = impact?.x ?? cx;
      const sy = impact?.y ?? cy;
      if (shockFx === 'quake' && secondWave) {
        /* 1단에서 재생한 quake 의 3~5프레임이 2단 링 */
      } else if (shockFx) g.fx.play(shockFx, sx, sy, { depth: DEPTH.FX_GROUND });
      else if (!slamFx) g.combat.drawShockwave(sx, sy, Math.max(w, h));
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
      impact,
      dir: { x: p.dirX, y: p.dirY },
      facing,
      bounds: { cx, cy, w, h },
      comboIndex: p.comboIndex ?? null,
      art: p.art ?? null,
      charge: p.charge ?? null,
      heavy: isHeavyStrike(p),
      followUp: follow?.id ?? null,
      damageMult: p.damageMult,
      activeMs,
      hits: 0,
      time: g.time.now,
    };
    if (!follow) this.debugLastSwing = swingLog;
    this.swingLog.push(swingLog);
    if (this.swingLog.length > SWING_LOG_MAX) this.swingLog.shift();
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
    return { impact };
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
    // 55라운드 Q10: 막타(연격 마지막 타·대쉬 공격) · 판정 호가 반대로 훑는 타는 되돌아 휘두름(스파크 반전)
    const heavy = isHeavyStrike(p);
    const backswing = isBackswing(this.swing.shape(p));
    const from = { x: g.player.x, y: g.player.y - HIT_ORIGIN_UP_PX };
    if (g.combat.hitMob(mob, dmg, { crit, dirX: p.dirX, dirY: p.dirY, critFx, knockMult, heavy, backswing, from })) {
      g.progress.onKill(mob, stunnedByParry ? 'parry' : p.kind === 'aimed' ? 'attack' : p.kind);
      return;
    }
    g.structures.onMobHit(mob, false);
    if (mods.hitStunMs) mob.stun(now, mods.hitStunMs, 'hit');
    if (mods.bleed) this.dots.applyBleed(mob);
  }

  /** 55라운드 Q22 대검 차지 국면: 단계 번쩍임 이펙트 (틴트 번쩍임은 Player) */
  onPlayerCharge(p: PlayerChargePayload): void {
    if (p.phase === 'stage') this.chargeFlashFx = this.swing.playChargeFlash(p.stage);
  }

  // --- 매 프레임: 추적 화살·저격 꼬리 · 잔월 · 출혈 ---

  update(time: number, delta: number): void {
    this.bow.update(delta);
    this.dots.update(time);
  }
}
