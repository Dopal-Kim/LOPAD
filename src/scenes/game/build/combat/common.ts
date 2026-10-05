/**
 * 빌드 축 타격 규칙(BuildCombat·AttackPassives·ShotRules·KillRules)이 함께 쓰는 작은 도우미 (60라운드 6-1 정리 — 동작 그대로).
 */
import { EventBus, Events, type PassiveProcPayload } from '../../../../core/EventBus';
import { gameState } from '../../../../core/GameState';

/** 지금 공격력 (기본 공격력 × 무기 배율) — 지속 피해 틱·재 파편 피해의 기준 */
export function buildAttack(): number {
  return gameState.attack * gameState.weapon.damageMult;
}

/** 60라운드 음향 훅: 패시브 발동 (PASSIVE_PROC — passive = 패시브 id, fire = 술불 위 독한 숨) */
export function emitProc(r: { id: string }, fire?: boolean): void {
  EventBus.emit(Events.PASSIVE_PROC, {
    passive: r.id,
    ...(fire !== undefined ? { fire } : {}),
  } satisfies PassiveProcPayload);
}
