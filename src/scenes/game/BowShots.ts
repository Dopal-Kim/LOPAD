/**
 * 활 (51라운드 정리 — PlayerStrikes 에서 분리): 화살 생성 · 연사 감쇠 · 갈래 시트 · 저격 거리 단계.
 * 51라운드 Q2: 산탄 계열(산탄·폭우·추적) 갈래는 트리에서 빠졌다 — spread·homingTurnDeg 처리는 화기류 때 재사용하려고 남긴다.
 * 계약 art §10: 속사 `bow_arrow_rapid`·`bow_arrow_aimed_rapid` + 발사 섬광 `bow_muzzle_rapid`(spawn arrow_spawn),
 * 저격 `bow_arrow_snipe`·`bow_arrow_aimed_snipe` + 꼬리 `bow_arrow_snipe_lv1/2/3`(화살 아래 깊이, 비행 거리 1/3·2/3 에서 교체),
 * 조준선 `aim_line_snipe`(MotionFx). 53라운드 무기 이펙트 v3: 2단 갈래 표시 = 화살·꼬리 시트 JSON secondaryVariants
 * (색 교체 · 따라가는 겹침 — 관통 `fx/pierce`). 적중형 겹침(필중 crit_burst)은 기존 치명 연출이 맡는다.
 */
import Phaser from 'phaser';
import { DEPTH, TILE } from '../../core/Constants';
import type { PlayerAttackPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { Projectile } from '../../objects/Projectile';
import {
  aimLineFxId,
  branchArrowFxId,
  levelMult,
  muzzleFxId,
  snipeCritFromLevel,
  snipeLevel,
  stripFxPrefix,
  tailFxIds,
} from '../../systems/branchFx';
import type { FxHandle } from '../../systems/fx';
import { resolveFxVariant, type FxVariant } from '../../systems/fxVariants';
import { spriteLibrary } from '../../systems/sprites';
import { FX_ACTION, fxDrawScale } from '../../systems/spriteDefs';
import { arrowFxId } from '../../systems/fxIds';
import type { Game } from '../Game';
import { pathFx } from './shared';

/** 저격 화살 한 발의 상태 (발사점·사거리·단계·꼬리) */
interface SnipeShot {
  ox: number;
  oy: number;
  rangePx: number;
  level: number;
  mults: number[];
  bounds?: number[];
  critFromLevel?: number;
  /** 확정 치명으로 굴린 피해 (필중 lv3 적중용) */
  critAttack: number;
  tailIds: string[];
  tail: FxHandle | null;
}

export class BowShots {
  /** 디버그: 마지막 발사 (시트·갈래·변형·저격) · 마지막 적중 배율 */
  debugLastShot: unknown = null;
  debugLastHit: unknown = null;
  private lastShotAt = -Infinity;
  private rapidCount = 0;
  private readonly snipes = new Map<Projectile, SnipeShot>();

  constructor(private readonly g: Game) {}

  private get first(): string | undefined {
    return gameState.weapon.path[0];
  }

  /** 2단 갈래 변주 (경로 두 번째 노드의 secondaryVariants). 없으면 null */
  private variantOf(id: string): FxVariant | null {
    return resolveFxVariant(this.g.fx.sheet(id), { secondary: gameState.weapon.path[1] ?? null });
  }

  /** 조준선 시트 (갈래 조준선이 있으면 그것 — AimLine 이 로드 여부를 다시 본다) */
  get aimLineId(): string {
    return aimLineFxId(gameState.weapon.def.kind === 'ranged' ? this.first : null);
  }

  /** 활: 화살은 몸 시트 releaseFrame 시작(시위 놓음)에 맞춰 생성 (시트가 없으면 즉시). 연사 판정은 입력 시점 */
  fire(p: PlayerAttackPayload): void {
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
      if (!this.g.scene.isActive() || this.g.frozen || gameState.gameOver) return;
      this.spawnArrows({ ...p, x: g.player.x, y: g.player.y }, rapidMult);
    };
    if (p.releaseDelayMs > 0) g.time.delayedCall(p.releaseDelayMs, release);
    else release();
  }

  /** 화살 시트: 1단 갈래 시트가 있으면 그것 → 중시(옛 2차) → 기본 */
  private arrowSheet(aimed: boolean): { id: string; branch: boolean } {
    const fx = this.g.fx;
    const w = gameState.weapon.id;
    const b = this.first;
    if (b && fx.has(branchArrowFxId(w, aimed, b))) return { id: branchArrowFxId(w, aimed, b), branch: true };
    const heavy = aimed ? pathFx(fx, 'heavyarrow') : null;
    return { id: heavy ?? arrowFxId(w, aimed), branch: false };
  }

  private spawnArrows(p: PlayerAttackPayload, rapidMult: number): void {
    const g = this.g;
    const weapon = gameState.weapon;
    const R = weapon.def.ranged!;
    const mods = weapon.mods;
    const now = g.time.now;
    const aimed = p.kind === 'aimed';
    const { dmg, crit } = g.combat.rollDamage(p.damageMult * rapidMult, p.forceCrit, p.kind);
    // 조준 사격·섬광·관통(저격 2단): 무한 관통
    const pierce = aimed || mods.pierceInfinite ? Infinity : (mods.pierce ?? 0);
    const size = weapon.hitbox.width * p.sizeMult;
    const speed = R.projectileSpeedTiles * TILE * (mods.projectileSpeedMult ?? 1);
    const base = Math.atan2(p.dirY, p.dirX);
    const arrow = this.arrowSheet(aimed);
    const def = g.fx.sheet(arrow.id);
    // 2단 갈래: 화살 색 교체 텍스처 (만들 수 없으면 원본)
    const variant = arrow.branch ? this.variantOf(arrow.id) : null;
    const swapped = variant?.swaps.length ? spriteLibrary.recolored(g, arrow.id, FX_ACTION, variant.swaps) : null;
    const texture = swapped?.texture ?? spriteLibrary.textureKey(arrow.id, FX_ACTION);
    const anim = def?.loop
      ? (swapped?.anim('down') ?? spriteLibrary.animKey(arrow.id, FX_ACTION, 'down') ?? undefined)
      : undefined;
    const origin = def
      ? { originX: def.pivot.x / def.frameWidth, originY: def.pivot.y / def.frameHeight, scale: fxDrawScale(def) }
      : {};
    // 옛 갈래 꼬리 (섬광·추적·관통 루프) — 갈래 화살 시트가 없을 때만
    const legacyTail = arrow.branch ? null : pathFx(g.fx, 'flash', 'seek', 'pierce');
    // 저격: 거리 단계 (aimedOnly 면 조준 사격만). 53라운드 Q16: 모든 화살 levelMults, 조준 사격은 aimedLevelMults
    const S = mods.snipe && (!mods.snipe.aimedOnly || aimed) ? mods.snipe : null;
    const snipeMults = S ? (aimed && S.aimedLevelMults ? S.aimedLevelMults : S.levelMults) : null;
    // 53라운드 Q40: 필중 최장 거리 확정 치명은 조준 사격만 (critAimedOnly) — 거리 배율은 모든 화살
    const critFromLevel = snipeCritFromLevel(S, aimed);
    // 산탄·폭우(화기류 때 재사용): 부채꼴 (조준 사격은 한 발). 발사 이펙트는 발사점에 1회
    const spread = !aimed && mods.spread ? mods.spread : { count: 1, spreadDeg: 0 };
    const burstFx = pathFx(g.fx, 'rain', 'scatter');
    const reach = weapon.hitbox.reach;
    if (spread.count > 1 && burstFx)
      g.fx.play(burstFx, p.x + p.dirX * reach, p.y + p.dirY * reach, { angle: base, depth: DEPTH.PROJECTILE });
    // 속사: 발사 섬광 (화살이 생기는 점 = arrow_spawn, 1회 재생 — 간격이 짧으면 처음부터 다시)
    const muzzle = this.first ? muzzleFxId(weapon.id, this.first) : null;
    if (muzzle && g.fx.has(muzzle))
      g.fx.play(muzzle, p.x + p.dirX * reach, p.y + p.dirY * reach, { angle: base, depth: DEPTH.PROJECTILE + 0.01 });
    const n = Math.max(1, spread.count);
    for (let i = 0; i < n; i++) {
      const t = n === 1 ? 0 : i / (n - 1) - 0.5;
      const a = base + Phaser.Math.DegToRad(spread.spreadDeg) * t;
      const dx = Math.cos(a);
      const dy = Math.sin(a);
      const shot = g.playerShots.get() as Projectile | null;
      if (!shot) return;
      this.dropSnipe(shot);
      const sx = p.x + dx * reach;
      const sy = p.y + dy * reach;
      shot.launch(
        sx,
        sy,
        dx,
        dy,
        { speedPx: speed, attack: dmg, size, lifeMs: R.projectileLifeMs },
        now,
        'player',
        pierce,
        { texture: texture ?? undefined, rotate: true, anim, ...origin },
      );
      shot.crit = crit;
      if (mods.homingTurnDeg) shot.homingTurn = Phaser.Math.DegToRad(mods.homingTurnDeg);
      if (aimed && mods.aimedShotStunMs) shot.hitStunMs = mods.aimedShotStunMs;
      // 중시: 적중 시 번개 낙하(heavyarrow_hit, 섬광·흔들림은 시트 JSON)
      if (!arrow.branch && aimed && pathFx(g.fx, 'heavyarrow') && g.fx.has('heavyarrow_hit'))
        shot.impactFx = 'heavyarrow_hit';
      if (legacyTail)
        g.fx.play(legacyTail, shot.x, shot.y, {
          angle: a,
          follow: shot,
          followRotation: true,
          depth: DEPTH.PROJECTILE - 0.01,
        });
      // 2단 갈래 따라가는 겹침 (관통: fx/pierce 를 저격 꼬리 위·화살 아래에)
      for (const o of variant?.followOverlays ?? [])
        if (g.fx.has(o))
          g.fx.play(o, shot.x, shot.y, {
            angle: a,
            follow: shot,
            followRotation: true,
            depth: DEPTH.PROJECTILE - 0.005,
          });
      if (S) {
        const tails = (def?.tailSheets ?? tailFxIds(branchArrowFxId(weapon.id, false, this.first ?? ''))).map(
          stripFxPrefix,
        );
        const entry: SnipeShot = {
          ox: sx,
          oy: sy,
          rangePx: speed * (R.projectileLifeMs / 1000),
          level: 0,
          mults: snipeMults!,
          bounds: S.bounds,
          critFromLevel,
          critAttack: critFromLevel ? g.combat.rollDamage(p.damageMult * rapidMult, true, p.kind).dmg : dmg,
          tailIds: tails,
          tail: null,
        };
        this.snipes.set(shot, entry);
        this.updateTail(shot, entry);
      }
    }
    this.debugLastShot = {
      time: now,
      aimed,
      sheet: arrow.id,
      branchSheet: arrow.branch,
      texture,
      variant: variant ? { swaps: variant.swaps.length, overlays: variant.followOverlays } : null,
      muzzle: muzzle && g.fx.has(muzzle) ? muzzle : null,
      pierce,
      snipe: S ? { mults: snipeMults, critFromLevel: critFromLevel ?? null } : null,
      dmg,
      crit,
    };
  }

  /** 저격 꼬리: 단계가 바뀌면 시트만 교체 (같은 피벗, 화살 아래 깊이) */
  private updateTail(shot: Projectile, e: SnipeShot): void {
    const lv = snipeLevel(Math.hypot(shot.x - e.ox, shot.y - e.oy), e.rangePx, e.bounds);
    if (lv === e.level) return;
    e.level = lv;
    const fx = this.g.fx;
    if (fx.isActive(e.tail)) fx.stop(e.tail, 0, false);
    e.tail = null;
    const id = e.tailIds[Math.min(e.tailIds.length, lv) - 1];
    if (!id || !fx.has(id)) return;
    e.tail = fx.play(id, shot.x, shot.y, {
      angle: shot.rotation,
      follow: shot,
      followRotation: true,
      depth: DEPTH.PROJECTILE - 0.01,
      variant: this.variantOf(id),
    });
  }

  private dropSnipe(shot: Projectile): void {
    const e = this.snipes.get(shot);
    if (!e) return;
    if (this.g.fx.isActive(e.tail)) this.g.fx.stop(e.tail, 0, false);
    this.snipes.delete(shot);
  }

  /** 화살 적중 (GameCombat): 저격 거리 단계 배율 · 필중 lv3 확정 치명. 저격 화살이 아니면 그대로 */
  hitMods(shot: Projectile): { attack: number; crit: boolean } {
    const e = this.snipes.get(shot);
    if (!e) return { attack: shot.attack, crit: shot.crit };
    const lv = snipeLevel(Math.hypot(shot.x - e.ox, shot.y - e.oy), e.rangePx, e.bounds);
    const forced = e.critFromLevel !== undefined && lv >= e.critFromLevel && !shot.crit;
    const crit = shot.crit || forced;
    const attack = Math.max(1, Math.round((forced ? e.critAttack : shot.attack) * levelMult(e.mults, lv)));
    this.debugLastHit = { level: lv, mult: levelMult(e.mults, lv), attack, crit, forced };
    return { attack, crit };
  }

  /** 매 프레임: 추적 화살 선회 · 저격 꼬리 단계 */
  update(delta: number): void {
    const g = this.g;
    for (const child of g.playerShots.getChildren()) {
      const shot = child as Projectile;
      if (!shot.active || shot.homingTurn <= 0) continue;
      const target = g.combat.nearestMob(shot.x, shot.y, Infinity);
      if (target) shot.steerToward(target.x, target.y, delta);
    }
    for (const [shot, e] of this.snipes) {
      if (!shot.active) {
        this.dropSnipe(shot);
        continue;
      }
      this.updateTail(shot, e);
    }
  }
}
