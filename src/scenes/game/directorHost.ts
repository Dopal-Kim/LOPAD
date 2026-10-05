/**
 * 방 상태 머신 만들기 (60라운드 6-1 정리 — Game.create 에서 분리, 동작 그대로): 회복·클리어·층 보상 · 구조물 웨이브 배율 ·
 * 노드 전용 웨이브 · 2차 묶음 훅(성소 깃발 대기 · 저주 길 2택 · E3 웨이브 +1 · 엘리트).
 */
import { gameState } from '../../core/GameState';
import { RoomDirector } from '../../systems/RoomDirector';
import { nodeWaves } from '../../systems/route';
import { ENEMIES } from '../../data';
import { UI_EVENTS, __system, type UiEnemyIntro } from '../../contract/ui';
import { enemyIntro } from '../../systems/enemyIntro';
import type { Enemy } from '../../objects/Enemy';
import type { Game } from '../Game';

export function createDirector(g: Game): RoomDirector {
  // 61라운드 P3: 잔 구간 전투는 그 단의 웨이브 (버려진 길은 노드 종류 웨이브)
  const waves = g.node ? nodeWaves(gameState.stageId, g.node) : undefined;
  return new RoomDirector({
    world: g.world,
    stage: gameState.stage,
    rng: g.rng,
    player: g.player,
    mobs: g.mobs,
    heal: (f) => g.player.heal(Math.round(gameState.maxHp * f), 'rest'),
    // 61라운드: 보스 처치 연출(쓰러짐·대사) 뒤에 보상·엔딩 (연출이 없으면 바로)
    onRunCleared: () => (g.bossFlow ? g.bossFlow.after(() => g.progress.beginEnding()) : g.progress.beginEnding()),
    onStageCleared: (room) =>
      g.bossFlow ? g.bossFlow.after(() => g.progress.beginStageReward(room)) : g.progress.beginStageReward(room),
    isLastStage: () => gameState.isLastStage,
    waveMods: (room, index, total) => {
      const s = g.structures?.waveMods(room) ?? { hpMult: 1, countMult: 1, extra: 0 };
      const b = g.bundle?.waveMods(index, total);
      return b ? { hpMult: s.hpMult * b.hpMult, countMult: s.countMult * b.countMult, extra: s.extra + b.extra } : s;
    },
    waves,
    holdTrial: (room) => g.bundle?.holdTrial(room) ?? false,
    extraWaves: () => g.bundle?.extraWaves() ?? 0,
    onWaveSpawned: (room, index, total, enemies) => {
      g.bundle?.onWaveSpawned(room, index, total, enemies);
      introduceNewcomers(enemies);
    },
  });
}

/** 61라운드 P3: 이번 런에 처음 나온 적 종류마다 짧은 소개 (계약 §17 ENEMY_INTRO — 이름 + 한 줄 요령) */
function introduceNewcomers(enemies: readonly Enemy[]): void {
  for (const id of enemyIntro.newcomers(
    gameState.seed,
    enemies.map((e) => e.id),
  )) {
    const def = ENEMIES[id];
    if (!def) continue;
    __system.emit(UI_EVENTS.ENEMY_INTRO, {
      id,
      name: def.name,
      ...(def.intro ? { desc: def.intro } : {}),
    } satisfies UiEnemyIntro);
  }
}
