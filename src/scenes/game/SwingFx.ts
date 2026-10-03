/**
 * 근접 휘두름 (53라운드 6-1 정리 — PlayerStrikes 에서 분리): 연격 한 타의 판정 모양 · 휘두름 이펙트 고르기·재생 · 잔상 리본.
 * 이펙트 우선순위: 대쉬 공격 재사용 → 1단 갈래 연격 시트(`<무기>_combo<n>_<갈래>`, 53라운드 계약 §10) → 가열 시트 → 기본 연격(마지막 타는
 * 진화 베기). 2단 갈래·가열 변주(색 교체·덮어쓰기)는 `fxVariants`.
 */
import Phaser from 'phaser';
import { DEPTH, FEEL, WEAPON_FX, entityDepth, fxLitDepth } from '../../core/Constants';
import type { PlayerAttackPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { comboShape, facingAngle, rotateDir, type HitShape } from '../../systems/combo';
import { comboFxId, heatComboFxId, slashFxId } from '../../systems/fxIds';
import { branchComboFxId, resolveFxVariant, type FxVariant } from '../../systems/fxVariants';
import { spriteLibrary } from '../../systems/sprites';
import { animDurationMs, comboAction, facingOf } from '../../systems/spriteDefs';
import { arcPoint } from '../../systems/trailMath';
import type { Game } from '../Game';
import { HIT_ORIGIN_UP_PX, isFinisher, pathFx } from './shared';

export class SwingFx {
  constructor(private readonly g: Game) {}

  /** 씬 진행 중(정지·사망 아님)인지 — 지연 실행 콜백 공통 확인 */
  private get live(): boolean {
    return this.g.scene.isActive() && !this.g.frozen && !gameState.gameOver;
  }

  /** 48라운드: 연격 한 타의 판정 모양 (아트 메모가 있으면 그린 대로 — 타 크기 배율은 빼고 대쉬 배율만). 연격이 아니면 null */
  shape(p: PlayerAttackPayload): HitShape | null {
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

  /**
   * 근접 베기 이펙트 (계약 §3.1): 플레이어 attack 2프레임(휘두름) 시작에 발 피벗 앵커로 재생.
   * 거합·쌍격은 기본 베기를 대신하고, 파쇄·중압은 적중 판정 쪽(meleeSwing)에서 따로 나온다.
   */
  play(p: PlayerAttackPayload): void {
    const g = this.g;
    const weapon = gameState.weapon;
    // 2차가 1차를 대신한다: 만월(wide) → 거합(iai), 난무(dance) → 쌍격(twin). 그 외는 기본 베기
    const evo = pathFx(g.fx, 'wide', 'iai', 'dance', 'twin');
    // 48라운드 3연격: 연격 시트가 있으면 타마다 그 시트, 진화 베기는 마지막 타에 (연격 시트가 없으면 기존처럼 매 타 진화 베기)
    const combo = p.comboIndex !== undefined;
    const finisher = isFinisher(p);
    // 49라운드 대검 내리찍기: 베기 호 없음 — 충격파 이펙트는 착지 순간 meleeSwing 이 착지점에
    if (p.slam) return;
    // 49라운드 몸 시트 메모: fxSpawnAtMs(이펙트 f0 시각) · 대쉬 공격 fxReuse(재사용 이펙트·시각). 재생 배속(맞춘 길이) 반영
    const body = p.bodyAction ? spriteLibrary.sheet('player', p.bodyAction) : undefined;
    const fitScale = body && p.durationMs ? p.durationMs / animDurationMs(body) : 1;
    const DS = weapon.def.dashSlash;
    const reuse = p.dashSlash && DS ? this.branchOr(body?.fxReuse?.id ?? comboFxId(weapon.id, DS.fxCombo)) : null;
    const spawnAt = p.dashSlash
      ? (body?.fxReuse?.spawnAtMs ?? DS?.fxSpawnAtMs)
      : typeof body?.fxSpawnAtMs === 'number'
        ? body.fxSpawnAtMs
        : undefined;
    const comboId = combo ? comboFxId(weapon.id, p.comboIndex! + 1) : null;
    // 53라운드 계약 §10: 1단 갈래 연격 시트(fx/<무기>_combo<n>_<갈래>)가 있으면 매 타 그것 (진화 베기 대체보다 우선)
    const branchId = comboId ? this.branchOr(comboId) : null;
    const branchSheet = branchId !== null && branchId !== comboId;
    // 49라운드 단검 과열: 가열 단계 시트(fx/<무기>_combo<n>_heat<k>)가 있으면 그것, 없으면 기본 시트를 키운다.
    // 갈래 시트는 heat 시트 대신 JSON heatVariants(색 교체)
    const heat = p.heatStage ?? 0;
    const heatId = comboId && heat > 0 && !branchSheet ? heatComboFxId(weapon.id, p.comboIndex! + 1, heat) : null;
    const heatSheet = heatId !== null && g.fx.has(heatId);
    const branchHeat = branchSheet && heat > 0 && resolveFxVariant(g.fx.sheet(branchId!), { heat }) !== null;
    const heatScale = heat > 0 && !heatSheet && !branchHeat ? 1 + WEAPON_FX.HEAT_SCALE_PER_STAGE * heat : 1;
    const baseId = comboId && g.fx.has(comboId) ? (finisher && evo ? evo : comboId) : (evo ?? slashFxId(weapon.id));
    const id =
      reuse && g.fx.has(reuse) ? reuse : branchSheet ? branchId! : heatSheet && !(finisher && evo) ? heatId! : baseId;
    // 2단 갈래(경로 두 번째 노드)·가열 변주: 색 교체 + 섬광·흔들림·잔상·마지막 프레임 덮어쓰기
    const variant = this.swingVariant(id, heat);
    // 가열 단계로 빨라진 타: 이펙트도 같은 배속으로 (아트 playbackRateHint 와 같은 값)
    const fxFit = heat > 0 && fitScale > 0 && fitScale < 1 ? g.fx.durationOf(id) * fitScale : undefined;
    const dir = facingOf(p.dirX, p.dirY, g.player.facingDir);
    const hb = weapon.hitbox;
    const shape = this.shape(p);
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
      const sheetTrail = g.fx.has(id) && Boolean(variant?.trail ?? g.fx.sheet(id)?.trail);
      if (g.fx.has(id))
        g.fx.play(id, player.x, player.y, {
          dir,
          follow: player,
          depthOffset: DEPTH.OVERLAY_STEP * 2,
          trailSource: sheetTrail ? arcSource() : undefined,
          scaleMult: heatScale,
          durationMs: fxFit,
          variant,
        });
      if (!sheetTrail)
        g.trails.start('slash', arcSource(), {
          // 53라운드 Q64: 휘두름 잔상도 이펙트처럼 라이트맵 위
          depth: fxLitDepth(entityDepth(player.y) + DEPTH.OVERLAY_STEP * 3),
          width: heat > 0 ? Math.round(FEEL.TRAIL.BAND_PX * (1 + WEAPON_FX.HEAT_TRAIL_PER_STAGE * heat)) : undefined,
        });
    };
    const lead = g.fx.leadMs(id);
    const delay = Math.max(0, spawnAt !== undefined ? spawnAt * fitScale : p.swingDelayMs - lead);
    if (delay > 0) g.time.delayedCall(delay, play);
    else play();
  }

  /** 53라운드 계약 §10: 1단 갈래 시트 `<id>_<갈래>` 가 로드돼 있으면 그 id, 아니면 그대로 */
  private branchOr(id: string): string {
    const first = gameState.weapon.path[0];
    if (!first) return id;
    const n = /_combo(\d+)$/.exec(id);
    const branch = n ? branchComboFxId(gameState.weapon.id, Number(n[1]), first) : `${id}_${first}`;
    return this.g.fx.has(branch) ? branch : id;
  }

  /** 휘두름 이펙트 변주: 2단 갈래 secondaryVariants · 갈래 시트 heatVariants (없으면 null) */
  private swingVariant(id: string, heat: number): FxVariant | null {
    return resolveFxVariant(this.g.fx.sheet(id), { secondary: gameState.weapon.path[1] ?? null, heat });
  }
}
