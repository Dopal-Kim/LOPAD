/**
 * 플레이어 공격 (PLAYER_ATTACKED): 근접 연격 판정 (48라운드) · 대검 내리찍기 (49라운드) · 진화 부가 효과(쌍격·지진 2단).
 * 51라운드 정리: 활 = `BowShots`, 잔월·출혈 = `StrikeDots`. 53라운드 정리: 판정 모양·휘두름 이펙트·잔상 리본 = `SwingFx`.
 * 55라운드 §17: 타별 판정 모양(호·쐐기+충격원·찌르기·고리) · 내려찍기 끝점 바닥 충격 · 판정 모양 디버그 오버레이(`HitShapeOverlay`).
 * 55라운드 6-1: 후속 판정(칼 잔상 베기·차지 충격파 링)·추가 타·지진 2단 스케줄 = `StrikeSchedule`. 피해 계산·피격 연출은 GameCombat.
 * 56라운드: 칼 일섬 = `IssenStrikes` · 58라운드 대검 차지 균열 = `CrackLineStrikes`(꽂아내리기 대체) · 단검 낙인 = `BrandMarks` · 휘두름이 처음 맞힌 순간
 * 무기 그림 번쩍임(Q12)·검기 획득 · 내려찍기 땅 균열(Q5).
 */
import Phaser from 'phaser';
import { COLORS, DEPTH, ENEMY_FX, FEEL, MOVE_FX, PROTOTYPE } from '../../core/Constants';
import {
  EventBus,
  Events,
  type ComboFinishPayload,
  type PlayerAttackPayload,
  type PlayerChargePayload,
} from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { Mob } from '../../objects/Mob';
import type { Projectile } from '../../objects/Projectile';
import { hitShapeBounds, shapeCenterPoint, shapeHit, type Pt } from '../../systems/weapon/hitShapes';
import { facingOf, radiusFitScale } from '../../systems/sprites/spriteDefs';
import { slamFxId, slashFxId } from '../../systems/fx/fxIds';
import { isBackswing, isHeavyStrike } from '../../systems/hitFeel';
import type { Game } from '../Game';
import { BowShots } from './BowShots';
import { HitShapeOverlay } from './HitShapeOverlay';
import { StrikeDots } from './StrikeDots';
import { StrikeSchedule, type SwingOpts } from './StrikeSchedule';
import { SwingFx } from './SwingFx';
import { BrandMarks } from './BrandMarks';
import { IssenStrikes } from './IssenStrikes';
import { CrackLineStrikes, crackOrigin } from './CrackLineStrikes';
import { MoveStrikes } from './MoveStrikes';
import { ArrowRain } from './ArrowRain';
import { HIT_ORIGIN_UP_PX, isComboFinish, isFinisher, isMeleeStrike, rotatesLeft, shapeFacing } from './shared';

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
  readonly attackLog: { time: number; kind: string; comboIndex: number | null; move: string | null }[] = [];
  readonly bow: BowShots;
  readonly dots: StrikeDots;
  /** 56라운드 일섬 · 꽂아내리기 · 낙인 */
  readonly issen: IssenStrikes;
  /** 58라운드 Q3 대검 차지 균열 (꽂아내리기 대체) */
  readonly crackLine: CrackLineStrikes;
  readonly brands: BrandMarks;
  /** 56라운드 2단계 새 기본기 (돌진형·도약 찍기·흡수·준비 반짝임·난타 fx) · 활 화살비 */
  readonly moves: MoveStrikes;
  readonly rain: ArrowRain;
  private readonly swing: SwingFx;
  private readonly schedule: StrikeSchedule;

  /** 디버그: 마지막 휘두름 이펙트 (55라운드 — 시트·단계·배율·띄운 시각·리본 방식) */
  get debugSwingFx(): unknown {
    return this.swing.debugLast;
  }

  constructor(private readonly g: Game) {
    this.bow = new BowShots(g);
    this.dots = new StrikeDots(g);
    this.swing = new SwingFx(g);
    this.overlay = new HitShapeOverlay(g);
    this.schedule = new StrikeSchedule(g, this.swing, (p, opts) => this.meleeSwing(p, opts));
    const strike = (mob: Mob, p: PlayerAttackPayload, first: boolean) => this.strikeMob(mob, p, first);
    this.issen = new IssenStrikes(g, strike);
    this.crackLine = new CrackLineStrikes(g, strike);
    this.brands = new BrandMarks(g);
    this.moves = new MoveStrikes(g, this.swing, strike);
    this.rain = new ArrowRain(g);
  }

  onPlayerAttacked(p: PlayerAttackPayload): void {
    const g = this.g;
    this.debugLastAttack = { ...p, time: g.time.now };
    this.attackLog.push({
      time: g.time.now,
      kind: p.kind,
      comboIndex: p.comboIndex ?? null,
      move: p.move ?? null,
    });
    if (this.attackLog.length > 40) this.attackLog.shift();
    const weapon = gameState.weapon;
    if (weapon.def.kind === 'ranged') {
      this.bow.fire(p);
      return;
    }
    // 56라운드: 전용 동작 — 판정·연출을 각 모듈이 (휘두름 이펙트·일반 판정 없음)
    if (p.issen) {
      this.issen.start(p);
      return;
    }
    // 56라운드 2단계: 태클·막다가 떼면 돌진 — 판정이 몸과 함께 이동 (휘두름 fx 는 그림 표대로)
    if (p.rush) {
      this.swing.play(p);
      this.moves.startRush(p);
      return;
    }
    // 도약 찍기: 쐐기·끝 충격원·균열은 아래 일반 판정, 나선·착지 링은 MoveStrikes
    if (p.leap) this.moves.startLeap(p);
    // 48라운드 3연격: 판정은 휘두름 프레임(hitFrames[0]) 시작에, 지진 2단·충격파는 마지막 타에서만
    const combo = isMeleeStrike(p);
    const finisher = isFinisher(p);
    this.swing.play(p);
    const strike = () => {
      if (!this.schedule.live) return;
      // 49라운드 내리찍기: 착지점 = 그 순간 발 피벗 + 시트 impactOffsetPx
      const at = p.slam
        ? { ...p, x: g.player.x + p.slam.offsetX, y: g.player.y + p.slam.offsetY }
        : combo
          ? { ...p, x: g.player.x, y: g.player.y }
          : p;
      const main = this.meleeSwing(at);
      // 58라운드 Q3 대검 차지: 내리찍은 자리에서 커서까지 균열
      if (p.crackLine) this.crackLine.start(at, main.impact);
      // 후속 판정 · 쌍격·난무 추가 타 · 지진 2단 (씬 시계 — 히트스톱 동안 멈춤)
      this.schedule.after(at, main.impact, finisher);
    };
    const hitDelay = combo ? p.swingDelayMs : 0;
    if (hitDelay > 0) g.time.delayedCall(hitDelay, strike);
    else strike();
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
    const reach = weapon.reachPx;
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
      // 61라운드 P9: 모양이 없는 판정(옛 hitbox 대체) — 조준 방향 R 앞에 R × R 사각형
      cx = p.x + p.dirX * reach * p.sizeMult;
      cy = p.y + p.dirY * reach * p.sizeMult;
      w = reach * p.sizeMult;
      h = reach * p.sizeMult;
    }
    // 후속 판정은 충격파 갈래·진화 베기를 다시 부르지 않는다
    const finisher = isFinisher(p) && !follow;
    const activeMs = p.activeMs ?? MOVE_FX.FALLBACK_ACTIVE_MS;
    // 47라운드: 타격형 구조물·화로 점화·불붙은 무기의 웅덩이 점화
    g.structures.onMeleeSwing(cx, cy, w, h, p.dirX, p.dirY);
    // 54라운드: 보스방 — 약점 잔 · 술통 방향 바꾸기 · 쓰러진 촛대 다시 켜기
    g.bossArena?.onMeleeSwing(cx, cy, w, h, p.dirX, p.dirY);
    // 61라운드 단계 2: 술통 짐꾼 술통 되치기
    g.hazards?.onMeleeSwing(cx, cy, w, h, p.dirX, p.dirY);
    // 베기 시트가 있으면 판정 사각형은 보이지 않게(판정만), 없으면 기존 플레이스홀더 표시
    // 그림이 있는가: 베기 시트, 내리찍기 충격 시트, 이 공격의 휘두름 이펙트(SwingFx 가 고른 것). 옛 진화 시트는 57 Q42 로 끔
    const hasSwingArt =
      g.fx.has(slashFxId(weapon.id)) || (p.slam ? g.fx.has(slamFxId(weapon.id)) : this.swing.lastFxLoaded);
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
      // 56라운드 Q5: 내려찍기 끝점 땅 균열 (본 타만 — V s(관성 최대 m) · 차지 m/m/l)
      // 58라운드 Q3 차지 휘둘러 내리찍기: 땅 충격도 찍은 자리(몸 slamAnchors)에
      const crackAt = p.crackLine ? crackOrigin(p, g.player, impact) : impact;
      if (!follow && !secondWave && p.crack && crackAt) this.swing.playCrack(p.art, crackAt.x, crackAt.y, p.crack);
      if (follow && !followFx && shape.kind === 'ring' && impact)
        g.combat.drawShockwave(impact.x, impact.y, shape.radius);
      else if (follow ? !followFx : !hasSwingArt && !impactFx)
        this.overlay.placeholder(ox, oy, p.dirX, p.dirY, shape, facing);
    }
    // 궤적·충격파: 시트가 있으면 시트, 없으면 Graphics 플레이스홀더
    if (mods.slashTrail) this.drawSlashTrail(cx, cy, p.dirX, p.dirY, Math.max(w, h));
    if (mods.shockwave && finisher) {
      // 49라운드 내리찍기: fx/<무기>_slam 이 파쇄(crush) 대신 (섬광·흔들림은 시트). 지진·분쇄 2차 이펙트는 그 위에 그대로
      const slamFx =
        p.slam && !secondWave && shape?.kind === 'arc'
          ? this.playSlamImpactFx(cx, cy, shape.radius, p.dirX, p.dirY)
          : false;
      // 55라운드: 내려찍기 쐐기는 충격파를 끝점에 (옛 지진·분쇄·파쇄 진화 시트는 57 Q42 로 끔 — 윤곽)
      const sx = impact?.x ?? cx;
      const sy = impact?.y ?? cy;
      if (!slamFx) g.combat.drawShockwave(sx, sy, Math.max(w, h));
      if (!slamFx) g.shake.add(g.time.now, FEEL.SHAKE.SHOCKWAVE.PX, FEEL.SHAKE.SHOCKWAVE.MS);
    }
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
      const first = swingLog.hits === 1 && !follow && !secondWave;
      // 61라운드 계약 sound §9: 연격 마지막 타가 처음 맞힌 순간 한 번 (활은 이 경로가 아님)
      if (first && isComboFinish(p))
        EventBus.emit(Events.PLAYER_COMBO_FINISH, { weapon: weapon.id } satisfies ComboFinishPayload);
      this.strikeMob(mob, p, first);
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
    if (mods.trailDot) this.dots.leaveTrailDot(p, { cx, cy, w, h });

    // 판정 영역은 물리 한 단계는 살아 있어야 겹침이 잡힌다 — 프레임이 판정 시간보다 길면(느린 기기) 한 프레임 + 여유만큼 (56라운드 2단계)
    g.time.delayedCall(Math.max(activeMs, g.game.loop.delta + 1), () => {
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

  /**
   * 근접 타격 1회: 피해 → (사망) 또는 중압 경직·출혈·낙인. first = 이 휘두름이 처음 맞힌 적 → 56라운드 Q12 무기 그림 번쩍임·Q14 검기.
   * 일섬·꽂아내리기 모듈도 쓴다
   */
  strikeMob(mob: Mob, p: PlayerAttackPayload, first = false): void {
    const g = this.g;
    const now = g.time.now;
    if (first) {
      g.player.overlay.flashHit();
      g.player.gauges.onStrikeHit();
    }
    const mods = gameState.weapon.mods;
    const stunnedByParry = mob.isParryStunned(now);
    // 57라운드 빌드 축: 강공 피해·일회성 배율·확정 치명 (BuildCombat)
    const bb = g.build.combat.strikeBonus(mob, p);
    const { dmg, crit } = g.combat.rollDamage(p.damageMult * bb.mult, p.forceCrit || bb.forceCrit, p.kind, mob);
    // 51라운드 Q4: 대검 끌어내기 첫 타 = 크게 밀쳐냄
    const knockMult = p.knockbackMult;
    // 55라운드 Q10·Q30: 막타(데이터 heavy — 칼 3타·잔상, 대검 차지 내려찍기 · 대쉬 공격) · 판정 호가 반대로 훑는 타는 되돌아 휘두름(스파크 반전)
    const heavy = isHeavyStrike(p);
    const backswing = isBackswing(this.swing.shape(p));
    // Q28: 왼쪽 회전 연격(칼·대검 타별 모양)은 왼쪽이어도 스파크를 바로 세우지 않는다 — 되돌아 휘두름만 데이터로
    const rotateLeft = rotatesLeft(p);
    const from = { x: g.player.x, y: g.player.y - HIT_ORIGIN_UP_PX };
    const style = {
      crit,
      dirX: p.dirX,
      dirY: p.dirY,
      // 옛 2차 전용 치명 이펙트(dashcrit·assassin)는 57 Q42 로 끔 — 공용 crit_burst
      critFx: null,
      knockMult,
      heavy,
      backswing,
      rotateLeft,
      from,
      // 56라운드 2단계 등 뒤 찌르기: 전용 섬광만 (공용 적중·치명 fx 없음)
      ...(p.noImpactFx ? { noImpactFx: true } : {}),
    };
    const died = g.combat.hitMob(mob, dmg, style);
    g.build.combat.afterStrike(mob, p, crit, died);
    if (died) {
      g.progress.onKill(mob, stunnedByParry ? 'parry' : p.kind === 'aimed' ? 'attack' : p.kind);
      return;
    }
    g.structures.onMobHit(mob, false);
    if (mods.hitStunMs) mob.stun(now, mods.hitStunMs, 'hit');
    if (mods.bleed) this.dots.applyBleed(mob);
    // 56라운드 Q16: 단검 낙인 (같은 적 타격마다, 등 뒤 2)
    this.brands.onHit(mob, p.dirX, p.dirY);
  }

  /** 55라운드 Q22 대검 차지 국면: 단계 번쩍임 이펙트 (틴트 번쩍임은 Player) */
  onPlayerCharge(p: PlayerChargePayload): void {
    if (p.phase === 'stage') this.chargeFlashFx = this.swing.playChargeFlash(p.stage);
  }

  // --- 매 프레임: 추적 화살·저격 꼬리 · 잔월 · 출혈 ---

  update(time: number, delta: number): void {
    this.bow.update(delta);
    this.dots.update(time);
    this.issen.update();
    this.crackLine.update();
    this.brands.update(time);
    this.moves.update();
    this.rain.update();
  }
}
