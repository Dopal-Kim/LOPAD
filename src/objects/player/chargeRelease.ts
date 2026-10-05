/**
 * 대검 홀드 차지를 뗐을 때 (56라운드 6-1 — MeleeDriver 에서 분리):
 * 58라운드 Q3: 어느 갈래든 마우스 방향으로 휘둘러 내리찍기(몸 `greatsword_charge_swing`, 없으면 `charge_slam`) — 쐐기 길이·피해 =
 * 단계 배율 × 울분, 균열 m/m/l — 그리고 내리찍은 자리에서 균열이 커서까지(`combo.charge.crackLine`, 판정은 씬 CrackLineStrikes).
 * 56라운드 Q10 꽂아내리기는 이것으로 대체. 울분(Q15)은 전부 소모해 위력·범위를 키운다.
 */
import { EventBus, Events, type PlayerAttackPayload, type PlayerChargePayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { ComboChargeDef, ComboHitDef } from '../../data/types';
import type { InputState } from '../../systems/InputSystem';
import { artScale, rowDirFor } from '../../systems/sprites/spriteDefs';
import { weaponRangeScale } from '../../systems/weapon/playerScale';
import { chargeStages } from '../../systems/build/current';
import type { Player } from '../Player';
import { strikeBodyAction } from './attackEmit';
import { aimVector, type ComboStrike } from './heavyMoves';

/** MeleeDriver 가 넘기는 것: 내딛기·정지 처리 */
export type AfterStrike = (payload: PlayerAttackPayload, hit: ComboHitDef, time: number, moving: boolean) => void;

function emitCharge(payload: PlayerChargePayload): PlayerChargePayload {
  EventBus.emit(Events.PLAYER_CHARGE, payload);
  return payload;
}

/** 몸 시트가 찍은 자리(`slamAnchors` — 칼끝이 바닥에 닿은 점, 몸 시트 도트)를 주면 발 피벗 기준 월드 오프셋 */
function crackStartOffset(p: Player, action: string, aimX: number, aimY: number): { x: number; y: number } | undefined {
  const sheet = p.visual.sheet(action);
  if (!sheet) return undefined;
  const anchors = sheet.slamAnchors;
  if (!anchors) return undefined;
  const dir = rowDirFor(sheet, aimX, aimY, p.visual.facing);
  const hf = sheet.hitFrames?.[0] ?? (typeof sheet.impactFrame === 'number' ? sheet.impactFrame : 0);
  const a = anchors[dir]?.[hf];
  if (!a) return undefined;
  const k = artScale(sheet) * p.visual.drawScale;
  return { x: (a[0] - sheet.pivot.x) * k, y: (a[1] - sheet.pivot.y) * k };
}

/** 차지를 떼서 → 휘둘러 내리찍기 (+ 균열). 반환 = 낸 PLAYER_CHARGE release (디버그) */
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
  // 60라운드: 거인 4단 포함 (chargeStages)
  const stages = chargeStages(C);
  const st = stages[Math.min(stage, stages.length) - 1];
  combo.reset();
  if (res?.def.kind === 'stamina') res.spend(res.def.cost.slam, time);
  const first = p.gear.firstStrike;
  p.gear.markDrawn(time);
  // 56라운드 Q15: 울분 전부 소모 → 피해·범위
  const grudge = p.gauges.consumeGrudge();
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
  // 58라운드 Q3: 균열이 커서까지 (차지 단계 최대 칸 수)
  const CL = C.crackLine;
  const tiles = CL ? CL.tilesByStage[Math.min(stage, CL.tilesByStage.length) - 1] : 0;
  const aim = aimVector(p, input);
  const startOffset = CL && tiles > 0 ? crackStartOffset(p, strikeBodyAction(p, strike), aim.x, aim.y) : undefined;
  const payload = p.fireAttack(
    input,
    time,
    strike,
    false,
    first,
    CL && tiles > 0
      ? {
          crackLine: {
            stage,
            maxTiles: tiles,
            cursorX: input.aimX,
            cursorY: input.aimY,
            halfWidthPx: CL.halfWidthPx * weaponRangeScale(w),
            damageMult: CL.damageMult,
            ...(startOffset ? { startOffset } : {}),
          },
        }
      : undefined,
  );
  // 타격음은 판정 프레임에 (음향 charge_slam_lv<n> 0ms = 타격 순간)
  const ev = emitCharge({ phase: 'release', stage, impactDelayMs: payload.swingDelayMs });
  const total = Math.max(payload.durationMs ?? hit.durationMs, p.visual.lastDurationMs);
  p.setAction('slam', time + total);
  p.slowUntil(time + total);
  after(payload, hit, time, moving);
  return ev;
}
