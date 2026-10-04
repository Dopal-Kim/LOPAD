/**
 * 근접 휘두름 (53라운드 6-1 정리 — PlayerStrikes 에서 분리): 연격 한 타의 판정 모양 · 휘두름 이펙트 고르기·재생 · 칼끝 리본.
 * 이펙트 고르기는 `swingSelect`(대쉬 공격 재사용 → 2단 전용 시트 → 1단 갈래 → 가열 → 기본 연격·진화 베기, 55라운드 Q16).
 * 55라운드 Q14: 이펙트 판정(백열) 프레임이 몸 판정 프레임 시작(실제 재생)에 오도록 띄우고, 히트스톱이면 그 프레임에서 멈춘다.
 * Q15: 갈래 판정 배율(hitboxMult·강화)만큼 그림도 키운다. Q7: 칼끝 리본(`bladeTip` + RibbonRenderer)이 42라운드 흰 리본을 대신한다.
 * 55라운드 §17: 타별 판정 모양은 데이터(`hitShape` → `resolveHitShape`, 아트 메모는 참고만), 휘두름·바닥 충격·잔상 이펙트는
 * 그림 이름 표(`combo.art`)의 로드된 첫 후보.
 * 56라운드: Q6 8행 이펙트 시트는 조준각 8분할 행(없으면 4방향 회전 규칙) · Q37 히트스톱 정지 = 붓획이 다 그어진 다음 칸
 * (띄우는 시각은 그대로 판정 프레임 = 몸 hitAt) · Q38 칼끝 리본은 돌진류(대쉬 공격)에만 · Q5 땅 균열(`playCrack`).
 */
import { DEPTH, ENEMY_FX, fxLitDepth } from '../../core/Constants';
import type { PlayerAttackPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { HitShapeSpec } from '../../data/types';
import { artCandidates, pickArt } from '../../systems/comboArt';
import { comboFxId, slamFxId } from '../../systems/fxIds';
import { comboRadius, comboShape, resolveHitShape, type HitShape } from '../../systems/hitShapes';
import { spriteLibrary } from '../../systems/sprites';
import type { FxVariant } from '../../systems/fxVariants';
import { pickSwingFx } from '../../systems/swingSelect';
import {
  artScale,
  comboAction,
  facingOf,
  frameStarts,
  fxHoldFrame,
  fxImpactFrame,
  radiusFitScale,
  rowDirFor,
  swingFxDelayMs,
  type Dir8,
  type Facing,
} from '../../systems/spriteDefs';
import type { ShakeHint } from './swingShake';
import { crackShake } from './swingShake';
import type { Game } from '../Game';
import { planBladeTip } from './bladeTip';
import { HIT_ORIGIN_UP_PX, isFinisher, isMeleeStrike, pathFx } from './shared';

export class SwingFx {
  /** 디버그: 마지막 휘두름 이펙트 (시트·단계·배율·띄운 시각·리본 방식) */
  debugLast: unknown = null;
  /** 이 공격의 휘두름 이펙트가 로드된 시트인가 (없으면 판정 윤곽 플레이스홀더) */
  lastFxLoaded = false;

  constructor(private readonly g: Game) {}

  /** 씬 진행 중(정지·사망 아님)인지 — 지연 실행 콜백 공통 확인 */
  private get live(): boolean {
    return this.g.scene.isActive() && !this.g.frozen && !gameState.gameOver;
  }

  /** 판정 배율 = 갈래·강화 (현재 reach / 기본 reach) */
  private get hbScale(): number {
    const w = gameState.weapon;
    return w.def.hitbox.reach > 0 ? w.hitbox.reach / w.def.hitbox.reach : 1;
  }

  /** 55라운드 §17: 데이터 모양 → px (R = radiusPx × 갈래·강화 × 타·대쉬 크기 배율) */
  resolveSpec(p: PlayerAttackPayload, spec: HitShapeSpec): HitShape | null {
    const w = gameState.weapon;
    const c = w.def.combo;
    if (!c) return null;
    return resolveHitShape(spec, comboRadius(c, w.def.hitbox) * this.hbScale * p.sizeMult, p.shapeScale);
  }

  /** 48라운드: 연격 한 타의 판정 모양 (아트 메모가 있으면 그린 대로 — 타 크기 배율은 빼고 대쉬 배율만). 연격이 아니면 null */
  shape(p: PlayerAttackPayload): HitShape | null {
    const w = gameState.weapon;
    const c = w.def.combo;
    if (!c || !isMeleeStrike(p)) return null;
    const hbScale = this.hbScale;
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
    // 55라운드 §17: 타별 데이터 모양 (칼 K-A·대검 G-C·차지 내려찍기)
    if (p.hitShape) return this.resolveSpec(p, p.hitShape);
    if (p.comboIndex === undefined) return null;
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

  /** 그림 이름 표에서 이펙트 id (`<무기>_<이름>`, 로드된 첫 후보). candidates 가 비면 null, 로드된 것이 없으면 첫 후보 id */
  private artFxId(art: string | undefined, cat: 'fx' | 'impactFx'): { id: string | null; listed: boolean } {
    const w = gameState.weapon;
    if (art === undefined) return { id: null, listed: false };
    const names = artCandidates(w.def.combo, art, cat);
    if (names.length === 0) return { id: null, listed: true };
    const name = pickArt(names, (n) => this.g.fx.has(`${w.id}_${n}`)) ?? names[0];
    return { id: `${w.id}_${name}`, listed: true };
  }

  /**
   * 근접 베기 이펙트: 발 피벗 앵커, 판정(백열) 프레임 = 몸 판정 프레임 시작. 파쇄·중압 충격은 적중 판정 쪽(meleeSwing)
   */
  play(p: PlayerAttackPayload): void {
    const g = this.g;
    const weapon = gameState.weapon;
    // 49라운드 대검 내리찍기: 베기 호 없음 — 충격파 이펙트는 착지 순간 meleeSwing 이 착지점에
    this.lastFxLoaded = false;
    if (p.slam) return;
    const combo = isMeleeStrike(p);
    const DS = weapon.def.dashSlash;
    const body = p.bodyAction ? spriteLibrary.sheet('player', p.bodyAction) : undefined;
    const dir = facingOf(p.dirX, p.dirY, g.player.facingDir);
    const shape = this.shape(p);
    // Q15: 갈래·강화 판정 배율만큼 그림도 (가열 배율과 곱). 판정 원점(발 위)이 그대로 있게 내려 붙인다
    const hb = this.hbScale;
    // 55라운드 §17: 그림 이름 표의 휘두름 이펙트 (빈 목록 = 휘두름 이펙트 없음 — 내려찍기는 끝점 바닥 충격만)
    const art = p.dashSlash ? { id: null, listed: false } : this.artFxId(p.art, 'fx');
    if (art.listed && art.id === null) {
      const ribbon = this.startRibbon(p, dir, shape, null, hb);
      this.debugLast = { id: null, art: p.art, tier: 'none', delay: 0, hitAt: p.swingDelayMs, ribbon };
      return;
    }
    const pick = pickSwingFx(
      {
        weaponId: weapon.id,
        comboN: p.comboIndex !== undefined ? p.comboIndex + 1 : null,
        ...(art.listed ? { comboId: art.id } : {}),
        finisher: isFinisher(p),
        path: weapon.path,
        heat: p.heatStage ?? 0,
        reuseId: p.dashSlash && DS ? (body?.fxReuse?.id ?? comboFxId(weapon.id, DS.fxCombo)) : null,
        // 2차가 1차를 대신한다: 만월(wide) → 거합(iai), 난무(dance) → 쌍격(twin)
        evoId: pathFx(g.fx, 'wide', 'iai', 'dance', 'twin'),
      },
      { has: (id) => g.fx.has(id), sheet: (id) => g.fx.sheet(id) },
    );
    const id = pick.id;
    this.lastFxLoaded = g.fx.has(id);
    const scaleMult = pick.heatScale * hb;
    // 56라운드 Q6: 8행 이펙트 시트(대검 붓획)는 몸과 같은 8분할 행
    const fxDir = rowDirFor(g.fx.sheet(id), p.dirX, p.dirY, g.player.facingDir);
    const delay = this.playAligned(id, p.swingDelayMs, scaleMult, combo, pick.variant, fxDir, 1 + (p.momentum ?? 0));
    const ribbon = this.startRibbon(p, dir, shape, id, hb);
    this.debugLast = { id, art: p.art, tier: pick.tier, scaleMult, delay, hitAt: p.swingDelayMs, ribbon };
  }

  /**
   * 휘두름 시트를 그 판정(백열) 프레임이 hitAtMs 에 오게 띄운다 (Q14). 반환 = 띄운 지연 ms (시트가 없으면 -1)
   */
  private playAligned(
    id: string,
    hitAtMs: number,
    scaleMult: number,
    combo: boolean,
    variant: FxVariant | null,
    dir: Dir8,
    timeScale = 1,
  ): number {
    const g = this.g;
    const def = g.fx.sheet(id);
    if (!def) return -1;
    const holdFrame = fxHoldFrame(def);
    // 판정 프레임(impactFrame — 아트 spawnRule: spawnAtMs = hitAt − 판정 프레임까지)이 몸 hitAt 에 오게 띄운다.
    // Q23 관성: 이펙트도 몸과 같은 배속 (판정 프레임까지 시간도 그만큼 짧다). 정지는 Q37 붓획 다음 칸(holdFrame)
    const lead = (frameStarts(def)[fxImpactFrame(def)] ?? 0) / timeScale;
    const delay = swingFxDelayMs(hitAtMs, lead);
    const player = g.player;
    const play = () => {
      if (!this.live || !g.fx.has(id)) return;
      g.fx.play(id, player.x, player.y, {
        dir,
        follow: player,
        followOffset: { x: 0, y: (combo ? HIT_ORIGIN_UP_PX : 0) * (scaleMult - 1) },
        depthOffset: DEPTH.OVERLAY_STEP * 2,
        scaleMult,
        variant,
        hitstopFrame: holdFrame,
        trail: false,
        timeScale,
      });
    };
    if (delay > 0) g.time.delayedCall(delay, play);
    else play();
    return delay;
  }

  /**
   * 55라운드 §17 후속 판정의 이펙트 (그림 표 키 — 지금 이 순간이 판정): 칼 잔상 베기 = 몸을 따라, 차지 충격파 링(at) = 끝점 바닥.
   * 시트가 없으면 false (호출 쪽 플레이스홀더)
   */
  playFollowUpFx(art: string | undefined, dirX: number, dirY: number, at?: { x: number; y: number }): boolean {
    const g = this.g;
    const { id } = this.artFxId(art, 'fx');
    if (!id || !g.fx.has(id)) return false;
    const def = g.fx.sheet(id);
    const dir = rowDirFor(def, dirX, dirY, g.player.facingDir);
    const hitstopFrame = def ? fxHoldFrame(def) : 0;
    if (at)
      return g.fx.play(id, at.x, at.y, { dir, depth: DEPTH.FX_GROUND, scaleMult: this.hbScale, hitstopFrame }) !== null;
    const player = g.player;
    const k = this.hbScale;
    return (
      g.fx.play(id, player.x, player.y, {
        dir,
        follow: player,
        followOffset: { x: 0, y: HIT_ORIGIN_UP_PX * (k - 1) },
        depthOffset: DEPTH.OVERLAY_STEP * 2,
        scaleMult: k,
        hitstopFrame,
        trail: false,
      }) !== null
    );
  }

  /** 후속 판정 이펙트의 판정 프레임까지 ms — 판정 시각보다 이만큼 먼저 띄운다. 시트가 없으면 null */
  followUpLeadMs(art: string | undefined): number | null {
    const { id } = this.artFxId(art, 'fx');
    const def = id ? this.g.fx.sheet(id) : undefined;
    if (!id || !def || !this.g.fx.has(id)) return null;
    return frameStarts(def)[fxImpactFrame(def)] ?? 0;
  }

  /** 55라운드 Q22 차지 단계 번쩍임 이펙트 (단계 그림 키 → 차지 자세 키의 flashFx, 몸을 따라). 시트가 없으면 false */
  playChargeFlash(stage: number): boolean {
    const g = this.g;
    const C = gameState.weapon.def.combo?.charge;
    if (!C || stage < 1) return false;
    const key = C.stages[stage - 1]?.art ?? C.holdArt ?? C.hit.art;
    const names = artCandidates(gameState.weapon.def.combo, key ?? '', 'flashFx');
    const w = gameState.weapon.id;
    const name = pickArt(names, (n) => g.fx.has(`${w}_${n}`));
    if (!name) return false;
    const player = g.player;
    const fid = `${w}_${name}`;
    const a = player.aimAngle;
    return (
      g.fx.play(fid, player.x, player.y, {
        dir: rowDirFor(g.fx.sheet(fid), Math.cos(a), Math.sin(a), player.facingDir),
        follow: player,
        depthOffset: DEPTH.OVERLAY_STEP * 2,
      }) !== null
    );
  }

  /**
   * 56라운드 Q5 땅 균열 (그림 표 `crackFx` — 행 = 크기 s·m·l, 회전 없음): 판정 순간 끝점(꽂힌 자리)에 바닥 깊이, 흔들림 = 시트 shakeHint.
   * 시트가 없으면 false
   */
  playCrack(art: string | undefined, x: number, y: number, row: string): boolean {
    const g = this.g;
    const w = gameState.weapon;
    const names = art !== undefined ? artCandidates(w.def.combo, art, 'crackFx') : [];
    const name = pickArt(names, (n) => g.fx.has(`${w.id}_${n}`));
    if (!name) return false;
    const id = `${w.id}_${name}`;
    const ok = g.fx.play(id, x, y, { dir: row, depth: DEPTH.FX_GROUND, scaleMult: this.hbScale }) !== null;
    const sh = crackShake((g.fx.sheet(id) as { shakeHint?: ShakeHint } | null)?.shakeHint, row);
    if (ok && sh) g.shake.add(g.time.now, sh.px, sh.ms);
    return ok;
  }

  /**
   * 55라운드 §17 내려찍기 끝점 바닥 충격 (`impactFx` — 대체 = 49라운드 fx/<무기>_slam). 판정 순간 끝점에, 배율 = 충격원 / 그림 반경.
   * 시트가 없으면 false (호출 쪽 플레이스홀더)
   */
  playImpactFx(
    art: string | undefined,
    x: number,
    y: number,
    radiusPx: number,
    dirX: number,
    dirY: number,
    impactMult?: number,
  ): boolean {
    const fx = this.g.fx;
    const { id } = this.artFxId(art, 'impactFx');
    const sheet = id ?? (art === undefined ? slamFxId(gameState.weapon.id) : null);
    if (!sheet || !fx.has(sheet)) return false;
    const def = fx.sheet(sheet);
    // 새 끝점 충격 그림(그림 표의 첫 후보 — 0.35R 로 그림)은 충격원 배율(관성 최대·차지 단계) × 갈래 배율,
    // 대체(49라운드 내리찍기 충격파)는 반경 맞춤 규칙
    const first = art !== undefined ? artCandidates(gameState.weapon.def.combo, art, 'impactFx')[0] : undefined;
    const drawnFor = first !== undefined && sheet === `${gameState.weapon.id}_${first}`;
    const scaleMult = drawnFor
      ? (impactMult ?? 1) * this.hbScale
      : radiusFitScale(radiusPx, def?.hitRadiusPx ?? ENEMY_FX.SLAM_BASE_RADIUS_PX);
    const dir = rowDirFor(def, dirX, dirY, this.g.player.facingDir);
    return fx.play(sheet, x, y, { dir, depth: DEPTH.FX_GROUND, scaleMult }) !== null;
  }

  /**
   * Q7 칼끝 리본: 판정 앞 1프레임 ~ 판정 뒤 1프레임 동안 칼끝(무기 bladeTipAnchors, 없으면 판정 호)을 찍는다.
   * 연격 시트 아래 깊이. 시각은 플레이 시계(히트스톱 동안 멈춤) — 공격 시작부터 잰다
   */
  private startRibbon(
    p: PlayerAttackPayload,
    dir: Facing,
    shape: HitShape | null,
    fxId: string | null,
    hb: number,
  ): string | null {
    const g = this.g;
    const weapon = gameState.weapon;
    const sheet = weapon.def.feel?.ribbon;
    // 56라운드 Q38: 기본 연격에서는 끄고 돌진류(대쉬 공격 — 일섬·그림자 걸음은 IssenStrikes·MotionFx)에만
    if (!sheet || p.kind !== 'dashAttack') return null;
    const fxDef =
      (fxId ? g.fx.sheet(fxId) : undefined) ??
      (p.comboIndex !== undefined ? g.fx.sheet(comboFxId(weapon.id, p.comboIndex + 1)) : undefined);
    const tipDots = fxDef?.trailFill?.bladeTipRadiusDots;
    const tipRadius = fxDef && typeof tipDots === 'number' ? tipDots * artScale(fxDef) * hb : null;
    const plan = planBladeTip(p, weapon.id, dir, shape, tipRadius);
    if (!plan) return null;
    const player = g.player;
    const t0 = g.playNow();
    let last: { x: number; y: number } | null = null;
    const begin = () => {
      if (!this.live) return;
      g.ribbons.start(
        (t) => {
          const e = t - t0;
          if (e > plan.to || !player.active) return null;
          const off = plan.at(e);
          if (off) last = { x: player.x + off.x, y: player.y + off.y };
          return last;
        },
        { sheet, depth: fxLitDepth(player.depth + DEPTH.OVERLAY_STEP * 1.5) },
      );
    };
    if (plan.from > 0) g.time.delayedCall(plan.from, begin);
    else begin();
    return plan.mode;
  }
}
