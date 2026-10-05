/**
 * 방 상태 머신 만들기 (60라운드 6-1 정리 — Game.create 에서 분리, 동작 그대로): 회복·클리어·층 보상 · 구조물 웨이브 배율 ·
 * 노드 전용 웨이브 · 2차 묶음 훅(성소 깃발 대기 · 저주 길 2택 · E3 웨이브 +1 · 엘리트).
 */
import { gameState } from '../../core/GameState';
import { RoomDirector } from '../../systems/RoomDirector';
import { kindDef } from '../../systems/route';
import type { Game } from '../Game';

export function createDirector(g: Game): RoomDirector {
  const kd = g.nodeKind ? kindDef(g.nodeKind) : null;
  return new RoomDirector({
    world: g.world,
    stage: gameState.stage,
    rng: g.rng,
    player: g.player,
    mobs: g.mobs,
    heal: (f) => g.player.heal(Math.round(gameState.maxHp * f), 'rest'),
    onRunCleared: () => g.progress.beginEnding(),
    onStageCleared: (room) => g.progress.beginStageReward(room),
    isLastStage: () => gameState.isLastStage,
    waveMods: (room, index, total) => {
      const s = g.structures?.waveMods(room) ?? { hpMult: 1, countMult: 1, extra: 0 };
      const b = g.bundle?.waveMods(index, total);
      return b ? { hpMult: s.hpMult * b.hpMult, countMult: s.countMult * b.countMult, extra: s.extra + b.extra } : s;
    },
    waves: kd?.waves,
    holdTrial: (room) => g.bundle?.holdTrial(room) ?? false,
    extraWaves: () => g.bundle?.extraWaves() ?? 0,
    onWaveSpawned: (room, index, total, enemies) => g.bundle?.onWaveSpawned(room, index, total, enemies),
  });
}
