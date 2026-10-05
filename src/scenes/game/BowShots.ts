/**
 * 활 (51라운드 정리 — PlayerStrikes 에서 분리): 화살 생성 · 연사 감쇠 · 갈래 시트 · 저격 거리 단계.
 * 51라운드 Q2: 산탄 계열(산탄·폭우·추적) 갈래는 트리에서 빠졌다 — spread·homingTurnDeg 처리는 화기류 때 재사용하려고 남긴다.
 * 계약 art §10: 속사 `bow_arrow_rapid`·`bow_arrow_aimed_rapid` + 발사 섬광 `bow_muzzle_rapid`(spawn arrow_spawn),
 * 저격 `bow_arrow_snipe`·`bow_arrow_aimed_snipe` + 꼬리 `bow_arrow_snipe_lv1/2/3`(화살 아래 깊이, 비행 거리 1/3·2/3 에서 교체),
 * 조준선 `aim_line_snipe`(MotionFx). 55라운드 Q16: 2단 갈래 = 2단 전용 화살 시트(`<1단 화살>_<2단>`, JSON tailSheets 가 2단 꼬리) →
 * 없으면 53라운드 대체(1단 시트 secondaryVariants 색 교체 · 관통 `fx/pierce` 겹침). Q17: 2단 꼬리가 있으면 구 pierce 겹침 없음.
 * 적중형 겹침(필중 crit_burst)은 기존 치명 연출이 맡는다.
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
} from '../../systems/fx/branchFx';
import type { FxHandle } from '../../systems/fx/fx';
import { isHeavyStrike } from '../../systems/hitFeel';
import { runtimeFxVariant, type FxVariant } from '../../systems/fx/fxVariants';
import { spriteLibrary } from '../../systems/sprites/sprites';
import { FX_ACTION, artScale, facingOf, fxDrawScale } from '../../systems/sprites/spriteDefs';
import { arrowFxId, perfectReleaseFxId } from '../../systems/fx/fxIds';
import type { Game } from '../Game';
import { HIT_ORIGIN_UP_PX } from './shared';
import { PLAYER_RENDER_SCALE } from '../../systems/weapon/playerScale';

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
  /** 2단 전용 화살이 가리킨 2단 꼬리인지 (그러면 꼬리 변주 = 그 시트 runtime) */
  tier2: boolean;
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

  /** 2단 갈래 변주 — 60라운드 (57 Q42): 옛 2단 색 교체·전용 시트는 끔 (2단 갈래 fx 는 계약 art §21, build/branch) */
  private variantOf(_id: string): FxVariant | null {
    return null;
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

  /**
   * 화살 시트: 1단 갈래 화살(속사·저격 — 51·52라운드 시트) → 기본. 60라운드 (57 Q42): 옛 2단 전용 시트·색 교체·중시(옛 2차)는 끔
   */
  private arrowSheet(aimed: boolean): { id: string; branch: boolean; tier2: boolean; variant: FxVariant | null } {
    const fx = this.g.fx;
    const w = gameState.weapon.id;
    const b = this.first;
    const tier1 = b ? branchArrowFxId(w, aimed, b) : null;
    if (tier1 && fx.has(tier1)) return { id: tier1, branch: true, tier2: false, variant: null };
    return { id: arrowFxId(w, aimed), branch: false, tier2: false, variant: null };
  }

  /**
   * 56라운드 Q58·계약 §18.11: 화살이 생기는 점 = 무기 놓기 시트(`<무기>_release`) arrowSpawnAnchors[방향][0] (무기 시트 좌표 →
   * 피벗 기준 × 도트 배율, 발 기준 월드 오프셋). 시트·값이 없으면 null (기존 — 조준 방향 reach, 발 높이)
   */
  private spawnOffset(dirX: number, dirY: number): { x: number; y: number } | null {
    const w = gameState.weapon.id;
    const sheet = spriteLibrary.sheet(w, 'release');
    const anchors = (sheet as { arrowSpawnAnchors?: Record<string, ([number, number] | null)[]> } | undefined)
      ?.arrowSpawnAnchors;
    const pt = anchors?.[facingOf(dirX, dirY, this.g.player.facingDir)]?.[0];
    if (!sheet || !pt) return null;
    const k = artScale(sheet) * PLAYER_RENDER_SCALE;
    return { x: (pt[0] - sheet.pivot.x) * k, y: (pt[1] - sheet.pivot.y) * k };
  }

  private spawnArrows(p: PlayerAttackPayload, rapidMult: number): void {
    const g = this.g;
    const weapon = gameState.weapon;
    const R = weapon.def.ranged!;
    const mods = weapon.mods;
    const now = g.time.now;
    const aimed = p.kind === 'aimed';
    // 57라운드 빌드 축: 강공·일회성 배율 · 갈래(저격 완벽 놓기·천공 스택·필중) · 원격 사거리·속도·관통
    const bb = g.build.arrowMods(p);
    const { dmg, crit } = g.combat.rollDamage(p.damageMult * rapidMult * bb.mult, p.forceCrit || bb.forceCrit, p.kind);
    // 조준 사격·섬광·관통(저격 2단): 무한 관통
    // 56라운드 Q9: 약한 화살(일찍 놓기)은 관통 없음
    const weak = p.bowPower === 'weak';
    const pierce =
      (aimed && p.pierce !== false) || mods.pierceInfinite ? Infinity : (mods.pierce ?? 0) + (weak ? 0 : bb.pierceAdd);
    const size = weapon.hitbox.width * p.sizeMult * bb.sizeMult;
    const speed = R.projectileSpeedTiles * TILE * (mods.projectileSpeedMult ?? 1) * bb.speedMult;
    const base = Math.atan2(p.dirY, p.dirX);
    // 56라운드 Q26: 약한 화살 전용 그림(없으면 기본 화살을 어둡게)
    const D = weapon.def.draw;
    const weakSheet = weak && D && g.fx.has(D.weakArrowSheet) ? D.weakArrowSheet : null;
    const arrow = weakSheet
      ? { id: weakSheet, branch: false, tier2: false, variant: null }
      : weak
        ? { id: arrowFxId(weapon.id, false), branch: false, tier2: false, variant: null }
        : this.arrowSheet(aimed);
    // 60라운드 계약 art §21: 교체 표(각성 궤적 `bow_arrow_awaken` 등 — 꼬리 때문에 틀이 길어도 피벗 기준)를 거친 실제 시트
    const sheetId = g.fx.resolve(arrow.id);
    const def = g.fx.sheet(arrow.id);
    // 2단 갈래: 2단 전용 시트면 그 runtime, 대체 경로면 화살 색 교체 텍스처 (만들 수 없으면 원본)
    const variant = arrow.variant;
    const swapped = variant?.swaps.length ? spriteLibrary.recolored(g, sheetId, FX_ACTION, variant.swaps) : null;
    const texture = swapped?.texture ?? spriteLibrary.textureKey(sheetId, FX_ACTION);
    const anim = def?.loop
      ? (swapped?.anim('down') ?? spriteLibrary.animKey(sheetId, FX_ACTION, 'down') ?? undefined)
      : undefined;
    const origin = def
      ? { originX: def.pivot.x / def.frameWidth, originY: def.pivot.y / def.frameHeight, scale: fxDrawScale(def) }
      : {};
    // 저격: 거리 단계 (aimedOnly 면 조준 사격만). 53라운드 Q16: 모든 화살 levelMults, 조준 사격은 aimedLevelMults
    const S = mods.snipe && (!mods.snipe.aimedOnly || aimed) ? mods.snipe : null;
    const snipeMults = S ? (aimed && S.aimedLevelMults ? S.aimedLevelMults : S.levelMults) : null;
    // 53라운드 Q40: 필중 최장 거리 확정 치명은 조준 사격만 (critAimedOnly) — 거리 배율은 모든 화살
    const critFromLevel = snipeCritFromLevel(S, aimed);
    // 산탄·폭우(화기류 때 재사용): 부채꼴 (조준 사격은 한 발). 발사 이펙트는 발사점에 1회
    const spread = !aimed && mods.spread ? mods.spread : { count: 1, spreadDeg: 0 };
    const reach = weapon.hitbox.reach;
    // 화살이 생기는 점 (arrowSpawnAnchors — 없으면 조준 방향 reach)
    const so = this.spawnOffset(p.dirX, p.dirY);
    const ax = p.x + (so ? so.x : p.dirX * reach);
    const ay = p.y + (so ? so.y : p.dirY * reach);
    // 속사: 발사 섬광 (화살이 생기는 점 = arrow_spawn, 1회 재생 — 간격이 짧으면 처음부터 다시)
    // 56라운드 Q9: 완벽 놓기 섬광 (화살이 생기는 점, 발사 각도)
    const perfectFx = perfectReleaseFxId(weapon.id);
    if (p.bowPower === 'perfect' && g.fx.has(perfectFx))
      g.fx.play(perfectFx, ax, so ? ay : ay - HIT_ORIGIN_UP_PX, {
        angle: base,
        flipY: p.dirX < 0,
        depth: DEPTH.PROJECTILE + 0.02,
      });
    const muzzle = this.first ? muzzleFxId(weapon.id, this.first) : null;
    if (muzzle && g.fx.has(muzzle)) g.fx.play(muzzle, ax, ay, { angle: base, depth: DEPTH.PROJECTILE + 0.01 });
    const n = Math.max(1, spread.count);
    for (let i = 0; i < n; i++) {
      const t = n === 1 ? 0 : i / (n - 1) - 0.5;
      const a = base + Phaser.Math.DegToRad(spread.spreadDeg) * t;
      const dx = Math.cos(a);
      const dy = Math.sin(a);
      const shot = g.playerShots.get() as Projectile | null;
      if (!shot) return;
      this.dropSnipe(shot);
      const sx = so ? ax : p.x + dx * reach;
      const sy = so ? ay : p.y + dy * reach;
      shot.launch(
        sx,
        sy,
        dx,
        dy,
        { speedPx: speed, attack: dmg, size, lifeMs: R.projectileLifeMs * bb.lifeMult },
        now,
        'player',
        pierce,
        { texture: texture ?? undefined, rotate: true, anim, ...origin },
      );
      shot.crit = crit;
      shot.heavy = isHeavyStrike(p);
      g.build.onArrowSpawn(shot, p);
      if (weak && !weakSheet && D) shot.setTint(D.weakArrowTint);
      if (mods.homingTurnDeg) shot.homingTurn = Phaser.Math.DegToRad(mods.homingTurnDeg);
      if (aimed && mods.aimedShotStunMs) shot.hitStunMs = mods.aimedShotStunMs;
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
          tier2: arrow.tier2,
        };
        this.snipes.set(shot, entry);
        this.updateTail(shot, entry);
      }
    }
    this.debugLastShot = {
      time: now,
      aimed,
      sheet: arrow.id,
      power: p.bowPower ?? null,
      branchSheet: arrow.branch,
      tier2: arrow.tier2,
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
      variant: e.tier2 ? runtimeFxVariant(fx.sheet(id)) : this.variantOf(id),
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
