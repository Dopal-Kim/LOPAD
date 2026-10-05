/**
 * 칼 일섬 (56라운드 Q2·Q3 → 58라운드 Q1 대쉬 공격 전용): 대쉬 후 공격 창 안 좌클릭 → 칼집 잡기 → 조준 4방향으로 4칸 돌진
 * (적 관통·벽에 막히면 멈춤·돌진 중 무적) → 잔심·납도. 61라운드 P1: 검기를 쓰지 않는다(검기는 좌 홀드 발도) — 늘 분신 없는 선.
 * 판정·일섬 선·분신·터짐은 씬(IssenStrikes)이 PLAYER_ATTACKED `issen` 으로.
 * 몸 시트 `player_katana_issen_dash`(없으면 `player_katana_issen`) 시각(돌진 220~370ms, 판정 250~330ms)은 무기 데이터 `issen` 이 기준.
 * 3연격 3타 찌르기는 `thrustMove`.
 */
import { gameState } from '../../core/GameState';
import type { MoveStrikeDef } from '../../data/types';
import type { InputState } from '../../systems/InputSystem';
import { facingVector } from '../../systems/weapon/issenPath';
import { facingOf } from '../../systems/sprites/spriteDefs';
import type { Player } from '../Player';
import { aimVector, type ComboStrike } from './heavyMoves';

/** 대쉬 일섬 시작 — 반환 = 동작 길이 ms (데이터가 없으면 0 → 호출 쪽이 일반 대쉬 공격) */
export function startIssen(p: Player, input: InputState, time: number, def: MoveStrikeDef): number {
  const I = gameState.weapon.def.issen;
  if (!I) return 0;
  const res = p.resource;
  if (res?.def.kind === 'stamina' && def.staminaCost) res.spend(def.staminaCost, time);
  p.gear.markDrawn(time);
  p.combo?.reset();
  p.clearLunges();
  const aim = aimVector(p, input);
  const facing = facingOf(aim.x, aim.y, p.visual.facing);
  const v = facingVector(facing);
  // 선·분신 시트가 4방향 축으로 그려져 있으므로 조준도 그 축으로 (몸 행·판정·이동 모두)
  const snapped: InputState = { ...input, aimX: p.x + v.x * 100, aimY: p.y + v.y * 100 };
  const hit = { ...def.hit, art: def.hit.art ?? def.art };
  const strike: ComboStrike = {
    index: 0,
    count: 1,
    hit,
    durationMs: hit.durationMs,
    heavy: true,
    ...(def.useDashAttackMult === false ? { noDashBaseMult: true } : {}),
  };
  // 60라운드 (58 Q10): 일섬 자체 피해 × 갈래 배율(대쉬 공격 갈래 배율·급소)만 — 기본 대쉬 배율 ×1.5 는 데이터로 뺀다
  const payload = p.fireAttack(snapped, time, strike, true, {
    issen: { facing, dirX: v.x, dirY: v.y },
  });
  const total = Math.max(payload.durationMs ?? strike.durationMs, p.visual.lastDurationMs);
  // 몸 시트를 재생 속도에 맞춰 늘였으면 돌진 구간도 같은 배율
  const k = total / Math.max(1, hit.durationMs);
  p.setAction('skill', time + total);
  p.slowUntil(time + total);
  p.startLunge(v.x, v.y, I.distancePx, (I.dashEndMs - I.dashStartMs) * k, time, I.dashStartMs * k);
  p.defense.addInvulnWindow(I.dashStartMs * k, I.dashEndMs * k);
  return total;
}
