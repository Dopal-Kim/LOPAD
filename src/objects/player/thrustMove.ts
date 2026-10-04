/**
 * 58라운드 Q1 칼 3연격 3타 찌르기 (연격 타 `move: "thrust"`, 일섬 대체): 검기를 전부 소모해 단수(0~3)만큼 사거리·피해를 키운다.
 * 판정 직사각형·피해 배율·fx 그림 키는 무기 데이터 `moves.thrust.byKi[단수]`, 내딛기는 `moves.thrust.lunge`(방향키와 무관 — 아트 lungePx).
 * 일반 연격 파이프라인(PLAYER_ATTACKED → 판정 모양·휘두름 fx `katana_thrust(_ki<n>)`·히트스톱)을 그대로 쓴다.
 */
import { gameState } from '../../core/GameState';
import type { PlayerAttackPayload } from '../../core/EventBus';
import type { Player } from '../Player';
import type { ComboStrike } from './heavyMoves';
import { addTravel } from './moveStrike';

/** 검기 소모 → 이번 찌르기 (데이터가 없으면 그대로) · 소모 단수 */
export function applyThrust(p: Player, strike: ComboStrike): { strike: ComboStrike; kenki: number } {
  const T = gameState.weapon.def.moves?.thrust;
  if (!T) return { strike, kenki: 0 };
  const stages = p.gauges.consumeKenki().stages;
  const lv = T.byKi[Math.max(0, Math.min(stages, T.byKi.length - 1))];
  const hit = {
    ...strike.hit,
    art: lv.art,
    damageMult: strike.hit.damageMult * lv.damageMult,
    hitShape: { kind: 'rect' as const, fromMult: lv.fromMult, lengthMult: lv.lengthMult, widthMult: lv.widthMult },
  };
  return { strike: { ...strike, hit }, kenki: stages };
}

/** 찌르기 내딛기 (조준 방향, 몸 재생 배율 k) */
export function thrustLunge(p: Player, payload: PlayerAttackPayload, durationMs: number, time: number): void {
  const L = gameState.weapon.def.moves?.thrust?.lunge;
  if (!L) return;
  const total = Math.max(payload.durationMs ?? durationMs, 1);
  addTravel(p, payload.dirX, payload.dirY, L, time, total / Math.max(1, durationMs));
}
