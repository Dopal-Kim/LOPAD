/**
 * 61 단계 6 (계약 UI §19) 일기장 '수련장' — 런 중에 수련장으로 갈 수 있는지 보고, 되면 런을 맡긴다.
 * 싸우는 중 · 보스 노드 · 메뉴·연출·전환 중이면 거부(이유 문자열). 맡길 때 층 구조물 상태(빚·취기 등)도 함께 든다.
 */
import { gameState } from '../../../core/GameState';
import type { UiTrainingStart } from '../../../contract/ui';
import { transitionGate } from '../../../systems/transition/transitionGate';
import type { Game } from '../../Game';
import { stashRun, type RunStash } from './session';

export function leaveRunForTraining(g: Game): Exclude<UiTrainingStart, 'ok'> | RunStash {
  if (g.director?.inCombat || g.structures?.inputLocked) return 'combat';
  if (g.nodeKind === 'boss') return 'boss';
  if (
    g.transitioning ||
    transitionGate.locked ||
    g.frozen ||
    g.menu?.isOpen ||
    g.birth?.active ||
    g.bossFlow?.busy ||
    gameState.rewardPending ||
    gameState.gameOver ||
    gameState.cleared
  )
    return 'busy';
  gameState.structureCarry = g.structures.exportFloorState();
  return stashRun();
}
