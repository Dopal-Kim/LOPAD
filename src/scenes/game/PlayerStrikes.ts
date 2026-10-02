/**
 * 플레이어 공격 (PLAYER_ATTACKED): 근접 3연격 판정 모양·휘두름 이펙트·잔상 리본 (48라운드) · 대검 내리찍기 (49라운드) ·
 * 활 화살 · 진화 부가 효과(쌍격·지진 2단·잔월·출혈·추적). 피해 계산·피격 연출은 GameCombat.
 */
import Phaser from 'phaser';
import { COLORS, DEPTH, ENEMY_FX, FEEL, PROTOTYPE, TILE, WEAPON_FX, entityDepth } from '../../core/Constants';
import type { PlayerAttackPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { Mob } from '../../objects/Mob';
import type { Projectile } from '../../objects/Projectile';
import { comboShape, facingAngle, hitShapeBounds, rotateDir, shapeHit, type HitShape } from '../../systems/combo';
import type { FxHandle } from '../../systems/fx';
import { spriteLibrary } from '../../systems/sprites';
import {
  FX_ACTION,
  animDurationMs,
  arrowFxId,
  comboAction,
  comboFxId,
  facingOf,
  heatComboFxId,
  hitFrameOffsets,
  radiusFitScale,
  slamFxId,
  slashFxId,
  type Facing,
} from '../../systems/spriteDefs';
import { arcPoint } from '../../systems/trailMath';
import type { Game } from '../Game';
import { HIT_ORIGIN_UP_PX, evolutionFxId, isFinisher, pathFx } from './shared';

/** 잔월: 남아 있는 베기 궤적 (지속 피해 영역) */
interface DotZone {
  x: number;
  y: number;
  w: number;
  h: number;
  until: number;
  nextAt: number;
  tickMs: number;
  dmg: number;
}

/** 출혈: 적별 지속 피해 (+ 적에 붙은 bleed 루프 이펙트) */
interface Bleed {
  mob: Mob;
  dmg: number;
  ticksLeft: number;
  nextAt: number;
  tickMs: number;
  fx: FxHandle | null;
}

export class PlayerStrikes {
  /** 디버그: 마지막 공격 이벤트 · 최근 근접 판정 (모양·원점·맞은 수) */
  debugLastAttack: unknown = null;
  debugLastSwing: unknown = null;
  private lastShotAt = -Infinity;
  private rapidCount = 0;
  private giantFx: FxHandle | null = null;
  private dotZones: DotZone[] = [];
  private bleeds: Bleed[] = [];

  constructor(private readonly g: Game) {}

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
    const weapon = gameState.weapon;
    if (weapon.def.kind === 'ranged') {
      this.fireArrow(p);
      return;
    }
    const mods = weapon.mods;
    // 48라운드 3연격: 판정은 휘두름 프레임(hitFrames[0]) 시작에, 지진 2단·충격파는 마지막 타에서만
    const combo = p.comboIndex !== undefined;
    const finisher = isFinisher(p);
    this.playSwingFx(p);
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

  /** 48라운드: 연격 한 타의 판정 모양 (아트 메모가 있으면 그린 대로 — 타 크기 배율은 빼고 대쉬 배율만). 연격이 아니면 null */
  private swingShape(p: PlayerAttackPayload): HitShape | null {
    const w = gameState.weapon;
    const c = w.def.combo;
    if (!c || p.comboIndex === undefined) return null;
    const hbScale = w.def.hitbox.reach > 0 ? w.hitbox.reach / w.def.hitbox.reach : 1;
    // 49라운드 대검 내리찍기: 착지점 둘레 원 (반경 × 진화·강화 배율)
    if (p.slam) {
      const r = p.slam.radiusPx * hbScale * p.sizeMult;
      return { kind: 'arc', radius: r, arcDeg: 360, centerDeg: 0, fromDeg: -180, toDeg: 180 };
    }
    // 49라운드 대검 대쉬 공격: 몸 시트 메모(hitRadiusPx·arcDeg·arcFrom/To — 그린 대로)가 있으면 그것, 없으면 3타 모양 × 대쉬 배율 + 데이터 각도
    if (p.dashSlash) {
      const dm = p.bodyAction ? spriteLibrary.sheet('player', p.bodyAction) : undefined;
      const drawnDs = Boolean(dm && typeof dm.hitRadiusPx === 'number');
      const ds = comboShape(c, w.def.hitbox, hbScale * (drawnDs ? 1 : p.sizeMult), drawnDs ? dm : null);
      if (ds.kind !== 'arc' || (drawnDs && typeof dm!.arcDeg === 'number')) return ds;
      const half = p.dashSlash.arcDeg / 2;
      return { ...ds, arcDeg: p.dashSlash.arcDeg, centerDeg: 0, fromDeg: -half, toDeg: half };
    }
    const n = p.comboIndex + 1;
    const memo = this.g.fx.sheet(comboFxId(w.id, n)) ?? spriteLibrary.sheet('player', comboAction(w.id, n)) ?? null;
    const drawn = Boolean(memo && (typeof memo.hitRadiusPx === 'number' || memo.thrust));
    const hitSize = c.hits[p.comboIndex]?.sizeMult ?? 1;
    const size = drawn ? p.sizeMult / hitSize : p.sizeMult;
    const shape = comboShape(c, w.def.hitbox, hbScale * size, drawn ? memo : null);
    // 아트 메모에 휘두름 방향이 없으면 짝수 번째 타(2타)는 반대로
    if (shape.kind === 'arc' && !(memo && typeof memo.arcFromDeg === 'number') && p.comboIndex % 2 === 1)
      return { ...shape, fromDeg: shape.toDeg, toDeg: shape.fromDeg };
    return shape;
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

  // --- 활 ---

  /** 활: 화살은 attack 3프레임(시위 놓음) 시작에 맞춰 생성 (시트가 없으면 즉시). 연사 판정은 입력 시점 */
  private fireArrow(p: PlayerAttackPayload): void {
    const g = this.g;
    const R = gameState.weapon.def.ranged!;
    const now = g.time.now;
    const aimed = p.kind === 'aimed';
    let rapidMult = 1;
    if (!aimed) {
      this.rapidCount = now - this.lastShotAt <= R.rapidWindowMs ? this.rapidCount + 1 : 0;
      this.lastShotAt = now;
      rapidMult = Math.max(R.rapidMin, 1 - R.rapidDecay * this.rapidCount);
    }
    const release = () => {
      if (!this.live) return;
      this.spawnArrows({ ...p, x: g.player.x, y: g.player.y }, rapidMult);
    };
    if (p.releaseDelayMs > 0) g.time.delayedCall(p.releaseDelayMs, release);
    else release();
  }

  private spawnArrows(p: PlayerAttackPayload, rapidMult: number): void {
    const g = this.g;
    const weapon = gameState.weapon;
    const R = weapon.def.ranged!;
    const mods = weapon.mods;
    const now = g.time.now;
    const aimed = p.kind === 'aimed';
    const { dmg, crit } = g.combat.rollDamage(p.damageMult * rapidMult, p.forceCrit, p.kind);
    // 조준 사격·섬광: 무한 관통
    const pierce = aimed || mods.pierceInfinite ? Infinity : (mods.pierce ?? 0);
    const size = weapon.hitbox.width * p.sizeMult;
    const speed = R.projectileSpeedTiles * TILE * (mods.projectileSpeedMult ?? 1);
    const base = Math.atan2(p.dirY, p.dirX);
    // 화살 텍스처 (계약 §3.1 projectile 앵커, 진행 각도 회전). 없으면 사각형. 중시(2차)는 조준 화살 대신 heavyarrow
    const heavy = aimed ? this.pathFx('heavyarrow') : null;
    const arrowTexture = heavy
      ? spriteLibrary.textureKey(heavy, FX_ACTION)
      : spriteLibrary.textureKey(arrowFxId(weapon.id, aimed), FX_ACTION);
    // 화살 꼬리 루프: 섬광(flash) / 추적(seek) 이 관통(pierce) 대신
    const tailFx = this.pathFx('flash', 'seek', 'pierce');
    // 산탄·폭우: 부채꼴 (조준 사격은 한 발). 발사 이펙트는 발사점에 1회 (폭우 rain 이 scatter 대신)
    const spread = !aimed && mods.spread ? mods.spread : { count: 1, spreadDeg: 0 };
    const burstFx = this.pathFx('rain', 'scatter');
    if (spread.count > 1 && burstFx) {
      g.fx.play(burstFx, p.x + p.dirX * weapon.hitbox.reach, p.y + p.dirY * weapon.hitbox.reach, {
        angle: base,
        depth: DEPTH.PROJECTILE,
      });
    }
    const n = Math.max(1, spread.count);
    for (let i = 0; i < n; i++) {
      const t = n === 1 ? 0 : i / (n - 1) - 0.5;
      const a = base + Phaser.Math.DegToRad(spread.spreadDeg) * t;
      const dx = Math.cos(a);
      const dy = Math.sin(a);
      const shot = g.playerShots.get() as Projectile | null;
      if (!shot) return;
      shot.launch(
        p.x + dx * weapon.hitbox.reach,
        p.y + dy * weapon.hitbox.reach,
        dx,
        dy,
        { speedPx: speed, attack: dmg, size, lifeMs: R.projectileLifeMs },
        now,
        'player',
        pierce,
        { texture: arrowTexture, rotate: true },
      );
      shot.crit = crit;
      if (mods.homingTurnDeg) shot.homingTurn = Phaser.Math.DegToRad(mods.homingTurnDeg);
      if (aimed && mods.aimedShotStunMs) shot.hitStunMs = mods.aimedShotStunMs;
      // 중시: 적중 시 번개 낙하(heavyarrow_hit, 섬광·흔들림은 시트 JSON)
      if (heavy && g.fx.has('heavyarrow_hit')) shot.impactFx = 'heavyarrow_hit';
      // 관통·섬광·추적: 화살 뒤에 빛줄 루프, 화살이 사라지면 함께 사라진다
      if (tailFx) {
        g.fx.play(tailFx, shot.x, shot.y, {
          angle: a,
          follow: shot,
          followRotation: true,
          depth: DEPTH.PROJECTILE - 0.01,
        });
      }
    }
  }

  // --- 근접 이펙트 ---

  /**
   * 근접 베기 이펙트 (계약 §3.1): 플레이어 attack 2프레임(휘두름) 시작에 발 피벗 앵커로 재생.
   * 거합·쌍격은 기본 베기를 대신하고, 파쇄·중압은 적중 판정 쪽(meleeSwing)에서 따로 나온다.
   */
  private playSwingFx(p: PlayerAttackPayload): void {
    const g = this.g;
    const weapon = gameState.weapon;
    // 2차가 1차를 대신한다: 만월(wide) → 거합(iai), 난무(dance) → 쌍격(twin). 그 외는 기본 베기
    const evo = this.pathFx('wide', 'iai', 'dance', 'twin');
    // 48라운드 3연격: 연격 시트가 있으면 타마다 그 시트, 진화 베기는 마지막 타에 (연격 시트가 없으면 기존처럼 매 타 진화 베기)
    const combo = p.comboIndex !== undefined;
    const finisher = isFinisher(p);
    // 49라운드 대검 내리찍기: 베기 호 없음 — 충격파 이펙트는 착지 순간 meleeSwing 이 착지점에
    if (p.slam) return;
    // 49라운드 몸 시트 메모: fxSpawnAtMs(이펙트 f0 시각) · 대쉬 공격 fxReuse(재사용 이펙트·시각). 재생 배속(맞춘 길이) 반영
    const body = p.bodyAction ? spriteLibrary.sheet('player', p.bodyAction) : undefined;
    const fitScale = body && p.durationMs ? p.durationMs / animDurationMs(body) : 1;
    const DS = weapon.def.dashSlash;
    const reuse = p.dashSlash && DS ? (body?.fxReuse?.id ?? comboFxId(weapon.id, DS.fxCombo)) : null;
    const spawnAt = p.dashSlash
      ? (body?.fxReuse?.spawnAtMs ?? DS?.fxSpawnAtMs)
      : typeof body?.fxSpawnAtMs === 'number'
        ? body.fxSpawnAtMs
        : undefined;
    const comboId = combo ? comboFxId(weapon.id, p.comboIndex! + 1) : null;
    // 49라운드 단검 과열: 가열 단계 시트(fx/<무기>_combo<n>_heat<k>)가 있으면 그것, 없으면 기본 시트를 키운다
    const heat = p.heatStage ?? 0;
    const heatId = comboId && heat > 0 ? heatComboFxId(weapon.id, p.comboIndex! + 1, heat) : null;
    const heatSheet = heatId !== null && g.fx.has(heatId);
    const heatScale = heat > 0 && !heatSheet ? 1 + WEAPON_FX.HEAT_SCALE_PER_STAGE * heat : 1;
    const baseId = comboId && g.fx.has(comboId) ? (finisher && evo ? evo : comboId) : (evo ?? slashFxId(weapon.id));
    const id = reuse && g.fx.has(reuse) ? reuse : heatSheet && !(finisher && evo) ? heatId : baseId;
    // 가열 단계로 빨라진 타: 이펙트도 같은 배속으로 (아트 playbackRateHint 와 같은 값)
    const fxFit = heat > 0 && fitScale > 0 && fitScale < 1 ? g.fx.durationOf(id) * fitScale : undefined;
    const dir = facingOf(p.dirX, p.dirY, g.player.facingDir);
    const hb = weapon.hitbox;
    const shape = this.swingShape(p);
    // 잔상 궤적(42라운드, fx-design §6.1): 플레이어 중심의 호를 SLASH_SWEEP_MS 동안 훑는다. 첫 샘플 시각부터 잰다
    const T = FEEL.TRAIL;
    const base = Math.atan2(p.dirY, p.dirX);
    let radius = hb.reach * p.sizeMult * T.SLASH_RADIUS_MULT + hb.width * 0.5;
    let mid = base;
    let half = T.SLASH_HALF_ANGLE * (dir === 'left' || dir === 'up' ? -1 : 1);
    if (shape?.kind === 'arc') {
      // 48라운드: 판정 호 그대로 (from→to = 휘두름 방향, left 는 좌우 반전)
      const from = base + Phaser.Math.DegToRad(facingAngle(shape.fromDeg, dir));
      const to = base + Phaser.Math.DegToRad(facingAngle(shape.toDeg, dir));
      radius = shape.radius;
      mid = (from + to) / 2;
      half = (to - from) / 2;
    }
    const sweep = Math.max(p.activeMs ?? hb.activeMs, T.SLASH_SWEEP_MS);
    const centerUp = combo ? HIT_ORIGIN_UP_PX : 0;
    const player = g.player;
    const arcSource = () => {
      let t0 = -1;
      return () => {
        if (t0 < 0) t0 = g.time.now;
        const t = (g.time.now - t0) / sweep;
        if (t > 1 || !player.active) return null;
        const c = combo ? { x: player.x, y: player.y - centerUp } : player.getCenter();
        if (shape?.kind === 'thrust') {
          // 찌르기: 몸 중심에서 앞으로 뻗는 직선
          const d = rotateDir(p.dirX, p.dirY, facingAngle(shape.angleDeg, dir));
          const r = shape.fromPx + shape.length * Math.min(1, t * 1.5);
          return { x: c.x + d.x * r, y: c.y + d.y * r };
        }
        return arcPoint(c.x, c.y, radius, mid, half, t);
      };
    };
    const play = () => {
      if (!this.live) return;
      // 시트 JSON trail 이 있으면 FxPool 이 fromFrame 에 같은 호로 리본을 시작(색·수명·폭은 JSON). 없으면 기본 리본을 바로
      const sheetTrail = g.fx.has(id) && Boolean(g.fx.sheet(id)?.trail);
      if (g.fx.has(id))
        g.fx.play(id, player.x, player.y, {
          dir,
          follow: player,
          depthOffset: DEPTH.OVERLAY_STEP * 2,
          trailSource: sheetTrail ? arcSource() : undefined,
          scaleMult: heatScale,
          durationMs: fxFit,
        });
      if (!sheetTrail)
        g.trails.start('slash', arcSource(), {
          depth: entityDepth(player.y) + DEPTH.OVERLAY_STEP * 3,
          width: heat > 0 ? Math.round(FEEL.TRAIL.BAND_PX * (1 + WEAPON_FX.HEAT_TRAIL_PER_STAGE * heat)) : undefined,
        });
    };
    const lead = g.fx.leadMs(id);
    const delay = Math.max(0, spawnAt !== undefined ? spawnAt * fitScale : p.swingDelayMs - lead);
    if (delay > 0) g.time.delayedCall(delay, play);
    else play();
  }

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
    const shape = this.swingShape(p);
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
    if (mods.trailDot) this.leaveTrailDot(p, { cx, cy, w, h }, swingFx);

    g.time.delayedCall(activeMs, () => {
      g.physics.world.removeCollider(overlap);
      if (clear) g.physics.world.removeCollider(clear);
      zone.destroy();
    });
  }

  /** 잔월: 판정 사각형 자리에 지속 피해 영역 + 남는 궤적 그림 (2차 시트 → 거합 꼬리 → 사각형) */
  private leaveTrailDot(
    p: PlayerAttackPayload,
    r: { cx: number; cy: number; w: number; h: number },
    swingFx: string | null,
  ): void {
    const g = this.g;
    const T = gameState.weapon.mods.trailDot!;
    const now = g.time.now;
    const { dmg } = g.combat.rollDamage(p.damageMult * T.damageMult);
    const dot: DotZone = {
      x: r.cx,
      y: r.cy,
      w: r.w,
      h: r.h,
      until: now + T.lingerMs,
      nextAt: now + T.tickMs,
      tickMs: T.tickMs,
      dmg,
    };
    this.dotZones.push(dot);
    const zangetsu = this.pathFx('zangetsu');
    const dir = facingOf(p.dirX, p.dirY, g.player.facingDir);
    if (zangetsu && swingFx) {
      // 잔월(2차 전용 시트): 거합이 끝난 자리(고정)에 루프, 한 바퀴 = 틱 간격이 되도록 틱을 루프 시작에 맞춘다. 바닥 깊이
      const start = p.swingDelayMs + g.fx.durationOf(swingFx);
      const linger = T.lingerMs - start;
      if (linger > 0) {
        const at = { x: p.x, y: p.y };
        g.time.delayedCall(start, () => {
          if (!g.scene.isActive()) return;
          g.fx.play(zangetsu, at.x, at.y, { dir, depth: DEPTH.FX_GROUND, durationMs: linger });
          dot.nextAt = g.time.now + dot.tickMs;
        });
      }
    } else if (swingFx === 'iai') {
      // 잔월(시트 없음): 거합 이펙트의 꼬리(마지막 3프레임)를 본 재생이 끝난 뒤 남은 시간 동안 반복
      const start = p.swingDelayMs + g.fx.durationOf('iai');
      const linger = T.lingerMs - start;
      if (linger > 0) {
        const at = { x: p.x, y: p.y, depth: entityDepth(p.y) + DEPTH.OVERLAY_STEP * 2 };
        g.time.delayedCall(start, () => {
          if (g.scene.isActive())
            g.fx.play('iai', at.x, at.y, { dir, depth: at.depth, durationMs: linger, tailFrames: 3 });
        });
      }
    } else {
      const rect = g.add.rectangle(r.cx, r.cy, r.w, r.h, COLORS.TRAIL_DOT, 0.35).setDepth(DEPTH.ATTACK);
      g.tweens.add({ targets: rect, alpha: 0, duration: T.lingerMs, onComplete: () => rect.destroy() });
    }
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
    if (g.combat.hitMob(mob, dmg, { crit, dirX: p.dirX, dirY: p.dirY, critFx })) {
      g.progress.onKill(mob, stunnedByParry ? 'parry' : p.kind === 'aimed' ? 'attack' : p.kind);
      return;
    }
    g.structures.onMobHit(mob, false);
    if (mods.hitStunMs) mob.stun(now, mods.hitStunMs, 'hit');
    if (mods.bleed) {
      const B = mods.bleed;
      const tick = Math.max(1, Math.round(gameState.attack * gameState.weapon.damageMult * B.damageMult));
      const cur = this.bleeds.find((b) => b.mob === mob);
      if (cur) {
        cur.ticksLeft = B.ticks;
        cur.dmg = Math.max(cur.dmg, tick);
        // 재적중: 루프를 다시 시작해 0프레임(글린트) = 다음 틱에 맞춘다
        cur.nextAt = now + B.tickMs;
        if (g.fx.isActive(cur.fx)) g.fx.stop(cur.fx, 0, false);
        cur.fx = this.playBleedFx(mob);
      } else
        this.bleeds.push({
          mob,
          dmg: tick,
          ticksLeft: B.ticks,
          nextAt: now + B.tickMs,
          tickMs: B.tickMs,
          fx: this.playBleedFx(mob),
        });
    }
  }

  /** 출혈(2차): 적 히트박스 중심에 붙어 루프 (한 바퀴 = 틱 간격, 아트 JSON). 시트가 없으면 null */
  private playBleedFx(mob: Mob): FxHandle | null {
    const id = this.pathFx('bleed');
    if (!id) return null;
    const c = mob.body.center;
    return this.g.fx.play(id, c.x, c.y, {
      follow: mob,
      followOffset: { x: c.x - mob.x, y: c.y - mob.y },
      depthOffset: DEPTH.OVERLAY_STEP * 3,
    });
  }

  // --- 매 프레임: 추적 화살 · 잔월 · 출혈 ---

  update(time: number, delta: number): void {
    this.tickHoming(delta);
    this.tickDotZones(time);
    this.tickBleeds(time);
  }

  /** 추적: 플레이어 화살이 가장 가까운 적을 향해 선회 */
  private tickHoming(delta: number): void {
    for (const child of this.g.playerShots.getChildren()) {
      const shot = child as Projectile;
      if (!shot.active || shot.homingTurn <= 0) continue;
      const target = this.g.combat.nearestMob(shot.x, shot.y, Infinity);
      if (target) shot.steerToward(target.x, target.y, delta);
    }
  }

  /** 잔월: 남은 궤적 영역이 주기마다 겹친 적에게 피해 */
  private tickDotZones(time: number): void {
    if (this.dotZones.length === 0) return;
    const g = this.g;
    for (const z of this.dotZones) {
      if (time < z.nextAt) continue;
      z.nextAt = time + z.tickMs;
      const bodies = g.physics.overlapRect(z.x - z.w / 2, z.y - z.h / 2, z.w, z.h, true, false);
      for (const b of bodies) {
        const go = (b as Phaser.Physics.Arcade.Body).gameObject as unknown;
        if (!g.mobs.contains(go as Phaser.GameObjects.GameObject)) continue;
        const mob = go as Mob;
        if (!mob.active) continue;
        if (g.combat.hitMob(mob, z.dmg, { crit: false, dirX: 0, dirY: 0, tick: true }))
          g.progress.onKill(mob, 'attack');
      }
    }
    this.dotZones = this.dotZones.filter((z) => time < z.until);
  }

  /** 출혈: 주기마다 피해, 횟수 소진·적 사망 시 제거 */
  private tickBleeds(time: number): void {
    if (this.bleeds.length === 0) return;
    const g = this.g;
    for (const b of this.bleeds) {
      if (!b.mob.active || time < b.nextAt) continue;
      b.nextAt = time + b.tickMs;
      b.ticksLeft -= 1;
      if (g.combat.hitMob(b.mob, b.dmg, { crit: false, dirX: 0, dirY: 0, tick: true }))
        g.progress.onKill(b.mob, 'attack');
      else b.mob.flashColor(COLORS.BLEED);
    }
    for (const b of this.bleeds) {
      if (b.mob.active && b.ticksLeft > 0) continue;
      if (g.fx.isActive(b.fx)) g.fx.stop(b.fx);
    }
    this.bleeds = this.bleeds.filter((b) => b.mob.active && b.ticksLeft > 0);
  }
}
