/**
 * 근접 휘두름 (53라운드 6-1 정리 — PlayerStrikes 에서 분리): 연격 한 타의 판정 모양 · 휘두름 이펙트 고르기·재생 · 칼끝 리본.
 * 이펙트 고르기는 `swingSelect`(대쉬 공격 재사용 → 2단 전용 시트 → 1단 갈래 → 가열 → 기본 연격·진화 베기, 55라운드 Q16).
 * 55라운드 Q14: 이펙트 판정(백열) 프레임이 몸 판정 프레임 시작(실제 재생)에 오도록 띄우고, 히트스톱이면 그 프레임에서 멈춘다.
 * Q15: 갈래 판정 배율(hitboxMult·강화)만큼 그림도 키운다. Q7: 칼끝 리본(`bladeTip` + RibbonRenderer)이 42라운드 흰 리본을 대신한다.
 */
import { DEPTH, fxLitDepth } from '../../core/Constants';
import type { PlayerAttackPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { comboShape, type HitShape } from '../../systems/combo';
import { comboFxId } from '../../systems/fxIds';
import { spriteLibrary } from '../../systems/sprites';
import { pickSwingFx } from '../../systems/swingSelect';
import {
  artScale,
  comboAction,
  facingOf,
  frameStarts,
  fxHoldFrame,
  swingFxDelayMs,
  type Facing,
} from '../../systems/spriteDefs';
import type { Game } from '../Game';
import { planBladeTip } from './bladeTip';
import { HIT_ORIGIN_UP_PX, isFinisher, pathFx } from './shared';

export class SwingFx {
  /** 디버그: 마지막 휘두름 이펙트 (시트·단계·배율·띄운 시각·리본 방식) */
  debugLast: unknown = null;

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
   * 근접 베기 이펙트: 발 피벗 앵커, 판정(백열) 프레임 = 몸 판정 프레임 시작. 파쇄·중압 충격은 적중 판정 쪽(meleeSwing)
   */
  play(p: PlayerAttackPayload): void {
    const g = this.g;
    const weapon = gameState.weapon;
    // 49라운드 대검 내리찍기: 베기 호 없음 — 충격파 이펙트는 착지 순간 meleeSwing 이 착지점에
    if (p.slam) return;
    const combo = p.comboIndex !== undefined;
    const DS = weapon.def.dashSlash;
    const body = p.bodyAction ? spriteLibrary.sheet('player', p.bodyAction) : undefined;
    const pick = pickSwingFx(
      {
        weaponId: weapon.id,
        comboN: combo ? p.comboIndex! + 1 : null,
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
    const def = g.fx.sheet(id);
    const dir = facingOf(p.dirX, p.dirY, g.player.facingDir);
    const shape = this.shape(p);
    // Q15: 갈래·강화 판정 배율만큼 그림도 (가열 배율과 곱). 판정 원점(발 위)이 그대로 있게 내려 붙인다
    const hb = weapon.def.hitbox.reach > 0 ? weapon.hitbox.reach / weapon.def.hitbox.reach : 1;
    const scaleMult = pick.heatScale * hb;
    const holdFrame = def ? fxHoldFrame(def) : 0;
    const lead = def ? (frameStarts(def)[holdFrame] ?? 0) : 0;
    const delay = swingFxDelayMs(p.swingDelayMs, lead);
    const player = g.player;
    const play = () => {
      if (!this.live || !g.fx.has(id)) return;
      g.fx.play(id, player.x, player.y, {
        dir,
        follow: player,
        followOffset: { x: 0, y: (combo ? HIT_ORIGIN_UP_PX : 0) * (scaleMult - 1) },
        depthOffset: DEPTH.OVERLAY_STEP * 2,
        scaleMult,
        variant: pick.variant,
        hitstopFrame: holdFrame,
        trail: false,
      });
    };
    if (delay > 0) g.time.delayedCall(delay, play);
    else play();
    const ribbon = this.startRibbon(p, dir, shape, id, hb);
    this.debugLast = { id, tier: pick.tier, scaleMult, delay, holdFrame, hitAt: p.swingDelayMs, ribbon };
  }

  /**
   * Q7 칼끝 리본: 판정 앞 1프레임 ~ 판정 뒤 1프레임 동안 칼끝(무기 bladeTipAnchors, 없으면 판정 호)을 찍는다.
   * 연격 시트 아래 깊이. 시각은 플레이 시계(히트스톱 동안 멈춤) — 공격 시작부터 잰다
   */
  private startRibbon(
    p: PlayerAttackPayload,
    dir: Facing,
    shape: HitShape | null,
    fxId: string,
    hb: number,
  ): string | null {
    const g = this.g;
    const weapon = gameState.weapon;
    const sheet = weapon.def.feel?.ribbon;
    if (!sheet) return null;
    const fxDef = g.fx.sheet(fxId) ?? g.fx.sheet(comboFxId(weapon.id, (p.comboIndex ?? 0) + 1));
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
