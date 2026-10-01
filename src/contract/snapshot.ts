/** 시스템 파트: 계약 스냅샷 생성 (UI 파트는 import 금지). */
import { gameState } from '../core/GameState';
import { ECONOMY, STORY } from '../data';
import type { FloorLayout } from '../systems/mapgen';
import type { UiMap, UiMenu, UiSnapshot } from './ui';

export interface SnapshotContext {
  layout: FloorLayout | null;
  visited: ReadonlySet<string>;
  cleared: ReadonlySet<string>;
  bossName: string | null;
  paused: boolean;
  menu: UiMenu | null;
}

export function buildUiMap(ctx: SnapshotContext): UiMap {
  const L = ctx.layout;
  if (!L) return { rooms: [], connections: [], currentRoomId: '', gridW: 0, gridH: 0 };
  return {
    rooms: L.rooms.map((r) => ({
      id: r.id,
      type: r.type,
      cells: r.cells.map((c) => ({ cx: c.cx, cy: c.cy })),
      visited: ctx.visited.has(r.id),
      cleared: ctx.cleared.has(r.id),
    })),
    connections: L.connections.map((c) => ({ a: { cx: c.a.cx, cy: c.a.cy }, b: { cx: c.b.cx, cy: c.b.cy } })),
    currentRoomId: gameState.roomId,
    gridW: L.gridW,
    gridH: L.gridH,
  };
}

export function buildSnapshot(ctx: SnapshotContext): UiSnapshot {
  const w = gameState.weapon;
  return {
    hp: gameState.hp,
    maxHp: gameState.maxHp,
    gold: gameState.gold,
    potions: gameState.potions,
    potionMax: ECONOMY.drops.potion.maxCarry + gameState.meta.potionCarry,
    stageIndex: gameState.stageIndex,
    stageName: gameState.stage.name,
    trialsCleared: gameState.trialsCleared,
    trialsTotal: gameState.trialsTotal,
    bossUnlocked: gameState.bossUnlocked,
    exitOpen: gameState.exitOpen,
    weapon: {
      name: w.def.name,
      evolutionName: w.evolution?.name ?? null,
      personality: w.personality,
      threshold: w.threshold,
      secondaryName: w.def.secondary.name,
    },
    boss:
      gameState.bossMaxHp > 0
        ? { name: ctx.bossName ?? '보스', hp: gameState.bossHp, maxHp: gameState.bossMaxHp, phase: gameState.bossPhase }
        : null,
    stats: {
      attack: gameState.attack,
      defense: gameState.defense,
      crit: gameState.crit,
      sense: gameState.senses.sense,
    },
    passives: Object.entries(gameState.passives.owned).map(([id, level]) => {
      const d = gameState.passives.def(id);
      return { name: d?.name ?? id, level, description: d?.description ?? '' };
    }),
    savesLeft: gameState.savesLeft,
    seed: gameState.seed,
    map: buildUiMap(ctx),
    paused: ctx.paused,
    menu: ctx.menu,
    playerName: gameState.playerName,
    floorTitle: STORY.floors[gameState.stageId]?.title ?? gameState.stage.name,
    names: { potion: STORY.names.potion, gold: STORY.names.gold, shop: STORY.names.shop, souls: STORY.names.souls },
  };
}
