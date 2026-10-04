/**
 * 56라운드 Q2·Q3 칼 3타 일섬 (벽력일섬 느낌): 납도 자세 → 조준 4방향으로 4칸 돌진(적 관통·벽에 막히면 멈춤·돌진 중 무적) → 잔심·납도.
 * 검기를 전부 소모해 강화, 3단이면 그림자 분신(Q28). 판정·일섬 선·분신·터짐은 씬(IssenStrikes)이 PLAYER_ATTACKED `issen` 으로.
 * 몸 시트 `player_katana_issen` 시각(돌진 220~370ms, 판정 250~330ms)은 무기 데이터 `issen` 이 기준.
 */
import { gameState } from '../../core/GameState';
import type { WeaponFirstStrikeDef } from '../../data/types';
import type { InputState } from '../../systems/InputSystem';
import { facingVector } from '../../systems/weapon/issenPath';
import { facingOf } from '../../systems/sprites/spriteDefs';
import type { Player } from '../Player';
import { aimVector, type ComboStrike } from './heavyMoves';

/** 일섬 시작 — 반환 = 동작 길이 ms (데이터가 없으면 0 → 호출 쪽이 일반 휘두름) */
export function startIssen(
  p: Player,
  input: InputState,
  time: number,
  strike: ComboStrike,
  first: WeaponFirstStrikeDef | null,
): number {
  const I = gameState.weapon.def.issen;
  if (!I) return 0;
  const aim = aimVector(p, input);
  const facing = facingOf(aim.x, aim.y, p.visual.facing);
  const v = facingVector(facing);
  // 선·분신 시트가 4방향 축으로 그려져 있으므로 조준도 그 축으로 (몸 행·판정·이동 모두)
  const snapped: InputState = { ...input, aimX: p.x + v.x * 100, aimY: p.y + v.y * 100 };
  const kenki = p.gauges.consumeKenki();
  const hit = { ...strike.hit, damageMult: strike.hit.damageMult * kenki.damageMult };
  const payload = p.fireAttack(snapped, time, { ...strike, hit, heavy: true }, false, first, {
    issen: { facing, dirX: v.x, dirY: v.y, kenki: kenki.stages, clone: kenki.clone },
  });
  const total = Math.max(payload.durationMs ?? strike.durationMs, p.visual.lastDurationMs);
  // 몸 시트를 재생 속도에 맞춰 늘였으면(관성 등) 돌진 구간도 같은 배율
  const k = total / Math.max(1, strike.hit.durationMs);
  p.setAction('skill', time + total);
  p.slowUntil(time + total);
  p.startLunge(v.x, v.y, I.distancePx, (I.dashEndMs - I.dashStartMs) * k, time, I.dashStartMs * k);
  p.defense.addInvulnWindow(I.dashStartMs * k, I.dashEndMs * k);
  return total;
}
