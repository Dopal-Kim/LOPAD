/**
 * 대검 홀드 차지를 뗐을 때 (56라운드 6-1 — MeleeDriver 에서 분리):
 * - 기본(55라운드 Q22 → 56라운드 Q10): 충격파 링 없는 강한 차지 내려찍기 — 쐐기 길이·피해 = 단계 배율 × 울분, 균열 m/m/l
 * - 개성 발현(56라운드 Q56: 어느 갈래든 1단, 공격 수단 표 'plunge') 뒤: 휘두르지 않고 칼을 땅에 꽂아 마우스 방향 충격파 + 균열 l (판정은 씬 PlungeStrikes)
 * 울분(Q15)은 둘 다 전부 소모해 위력·범위를 키운다.
 */
import { EventBus, Events, type PlayerAttackPayload, type PlayerChargePayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { ComboChargeDef, ComboHitDef, PlungeDef, WeaponFirstStrikeDef } from '../../data/types';
import type { InputState } from '../../systems/InputSystem';
import { comboRadius } from '../../systems/hitShapes';
import { pickMove } from '../../systems/moves';
import { artScale, rowDirFor } from '../../systems/spriteDefs';
import type { Player } from '../Player';
import { strikeBodyAction } from './attackEmit';
import { aimVector, type ComboStrike } from './heavyMoves';

/** MeleeDriver 가 넘기는 것: 내딛기·정지 처리 */
export type AfterStrike = (payload: PlayerAttackPayload, hit: ComboHitDef, time: number, moving: boolean) => void;

function emitCharge(payload: PlayerChargePayload): PlayerChargePayload {
  EventBus.emit(Events.PLAYER_CHARGE, payload);
  return payload;
}

/** 갈래·강화 판정 배율 (현재 reach / 기본 reach) */
function hitboxScale(): number {
  const w = gameState.weapon;
  return w.def.hitbox.reach > 0 ? w.hitbox.reach / w.def.hitbox.reach : 1;
}

/** 현재 판정 반경 R (데이터 radiusPx × 갈래·강화 배율) */
function currentRadius(): number {
  const w = gameState.weapon;
  const c = w.def.combo;
  return (c ? comboRadius(c, w.def.hitbox) : w.def.hitbox.reach) * hitboxScale();
}

/** 차지를 떼서 → 기본 차지 내려찍기 또는 꽂아내리기. 반환 = 낸 PLAYER_CHARGE release (디버그) */
export function releaseCharge(
  p: Player,
  input: InputState,
  time: number,
  C: ComboChargeDef,
  stage: number,
  moving: boolean,
  after: AfterStrike,
): PlayerChargePayload {
  const w = gameState.weapon;
  const combo = p.combo!;
  const res = p.resource;
  const st = C.stages[Math.min(stage, C.stages.length) - 1];
  combo.reset();
  if (res?.def.kind === 'stamina') res.spend(res.def.cost.slam, time);
  const first = p.gear.firstStrike;
  p.gear.markDrawn(time);
  // 56라운드 Q15: 울분 전부 소모 → 피해·범위
  const grudge = p.gauges.consumeGrudge();
  // 56라운드 Q56: 어느 갈래든 1단이 발현하면 차지 = 꽂아내리기 (갈래별 차이는 충격파 모양·효과)
  const plunge = w.def.plunge && pickMove(w.id, 'chargeRelease', w.path, () => w.path.length > 0);
  if (plunge && w.def.plunge) return startPlunge(p, input, time, C, stage, w.def.plunge, grudge, first);
  // 단계별 그림 키(stages[i].art) — 아트 단계 시트·균열 행은 그림 표
  const art = st.art ?? C.hit.art;
  const hit: ComboHitDef = { ...C.hit, art, damageMult: C.hit.damageMult * st.damageMult * grudge.damageMult };
  const crack = art ? w.def.combo?.art?.[art]?.crackRow : undefined;
  const strike: ComboStrike = {
    index: 0,
    count: combo.hits.length,
    hit,
    durationMs: hit.durationMs,
    heavy: hit.heavy ?? true,
    charge: stage,
    shapeScale: {
      lengthMult: st.lengthMult * grudge.rangeMult,
      ...(st.impactMult !== undefined ? { impactMult: st.impactMult } : {}),
    },
    ...(st.followUps ? { extraFollowUps: st.followUps } : {}),
    ...(crack ? { crack } : {}),
  };
  const payload = p.fireAttack(input, time, strike, false, first);
  // 타격음은 판정 프레임에 (음향 charge_slam_lv<n> 0ms = 타격 순간)
  const ev = emitCharge({ phase: 'release', stage, impactDelayMs: payload.swingDelayMs });
  const total = Math.max(payload.durationMs ?? hit.durationMs, p.visual.lastDurationMs);
  p.setAction('slam', time + total);
  p.slowUntil(time + total);
  after(payload, hit, time, moving);
  return ev;
}

/** 56라운드 Q10 꽂아내리기 — 몸 `greatsword_charge_plunge`(8방향) + 씬이 충격파·충격원·균열 */
function startPlunge(
  p: Player,
  input: InputState,
  time: number,
  C: ComboChargeDef,
  stage: number,
  P: PlungeDef,
  grudge: { damageMult: number; rangeMult: number },
  first: WeaponFirstStrikeDef | null,
): PlayerChargePayload {
  const combo = p.combo!;
  const st = C.stages[Math.min(stage, C.stages.length) - 1];
  const R = currentRadius();
  const hit: ComboHitDef = {
    ...C.hit,
    art: P.art,
    damageMult: C.hit.damageMult * st.damageMult * grudge.damageMult,
    durationMs: P.durationMs,
    hitAtMs: P.hitAtMs,
    cancelFromMs: P.durationMs,
    hitShape: undefined,
    step: undefined,
  };
  const strike: ComboStrike = {
    index: 0,
    count: combo.hits.length,
    hit,
    durationMs: hit.durationMs,
    heavy: true,
    charge: stage,
  };
  // 꽂힌 자리 = 몸 시트 plantAnchors (판정 프레임, 방향 행) → 발 피벗 기준 월드 오프셋. 없으면 조준 방향 R × 0.3
  const aim = aimVector(p, input);
  const action = strikeBodyAction(p, strike);
  const sheet = p.visual.sheet(action);
  const dir = rowDirFor(sheet, aim.x, aim.y, p.visual.facing);
  const hf = sheet?.hitFrames?.[0] ?? (typeof sheet?.impactFrame === 'number' ? sheet.impactFrame : 0);
  const anchor = sheet?.plantAnchors?.[dir]?.[hf] ?? null;
  const k = sheet ? artScale(sheet) : 0;
  const plant =
    sheet && anchor
      ? { x: (anchor[0] - sheet.pivot.x) * k, y: (anchor[1] - sheet.pivot.y) * k }
      : { x: aim.x * R * 0.3, y: aim.y * R * 0.3 };
  const lengths = P.wave.lengthMultByStage;
  const payload = p.fireAttack(input, time, strike, false, first, {
    plunge: {
      stage,
      waveLengthPx: R * (lengths[Math.min(stage, lengths.length) - 1] ?? 1) * grudge.rangeMult,
      waveHalfWidthPx: P.wave.halfWidthPx * hitboxScale(),
      plantOffsetX: plant.x,
      plantOffsetY: plant.y,
      plantRadiusPx: R * P.plantRadiusRatio,
    },
    crack: P.crackRow,
  });
  const ev = emitCharge({ phase: 'release', stage, impactDelayMs: payload.swingDelayMs, mode: 'plunge' });
  const total = Math.max(payload.durationMs ?? hit.durationMs, p.visual.lastDurationMs);
  p.setAction('skill', time + total);
  p.slowUntil(time + total);
  return ev;
}
