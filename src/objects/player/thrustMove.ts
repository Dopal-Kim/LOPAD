/**
 * 칼 3연격 3타 찌르기 (연격 타 `move: "thrust"`, 58라운드 Q1): 판정 직사각형·피해는 연격 타 데이터(`combo.hits[2]`),
 * 내딛기는 `moves.thrust.lunge`(방향키와 무관 — 아트 lungePx). 61라운드 P1: 검기를 쓰지 않는다 — 검기는 좌 홀드 발도만 소모.
 * 일반 연격 파이프라인(PLAYER_ATTACKED → 판정 모양·휘두름 fx `katana_thrust`·히트스톱)을 그대로 쓴다.
 */
import { gameState } from '../../core/GameState';
import type { PlayerAttackPayload } from '../../core/EventBus';
import type { Player } from '../Player';
import { addTravel } from './moveStrike';

/** 찌르기 내딛기 (조준 방향, 몸 재생 배율 k) */
export function thrustLunge(p: Player, payload: PlayerAttackPayload, durationMs: number, time: number): void {
  const L = gameState.weapon.def.moves?.thrust?.lunge;
  if (!L) return;
  const total = Math.max(payload.durationMs ?? durationMs, 1);
  addTravel(p, payload.dirX, payload.dirY, L, time, total / Math.max(1, durationMs));
}
