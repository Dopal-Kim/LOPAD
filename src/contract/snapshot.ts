/** 시스템 파트: 계약 스냅샷 생성 (UI 파트는 import 금지). */
import { gameState } from '../core/GameState';
import { ECONOMY, STORY } from '../data';
import type { FloorLayout } from '../systems/mapgen';
import type {
  UiCarry,
  UiInteractable,
  UiMap,
  UiMenu,
  UiRoute,
  UiSnapshot,
  UiStatus,
  UiWarpState,
  UiGroggy,
  UiWeaponGauge,
  UiWeaponResource,
  UiBuildState,
} from './ui';

export interface SnapshotContext {
  layout: FloorLayout | null;
  visited: ReadonlySet<string>;
  cleared: ReadonlySet<string>;
  bossName: string | null;
  paused: boolean;
  menu: UiMenu | null;
  /** 45라운드: 활성 전투 방 여부 · 달리는 중 · 워프 상태 (targets 는 방 id) */
  inCombat: boolean;
  sprinting: boolean;
  warp: UiWarpState;
  /** 47라운드 (계약 §9): 가장 가까운 E형 구조물 · HUD 상태 · 사용 가능한 E형 구조물이 남은 방 id. 생략 시 null / [] / 없음 */
  interactable?: UiInteractable | null;
  statuses?: readonly UiStatus[];
  structureRooms?: ReadonlySet<string>;
  /** 48라운드 (계약 §10): 노드 지도. 생략 시 null */
  route?: UiRoute | null;
  /** 49라운드 (계약 §11): 무기 자원 · 음소거 · 시험장. 생략 시 null / false / false */
  resource?: UiWeaponResource | null;
  muted?: boolean;
  lab?: boolean;
  /** 53라운드: 넣기/뽑기 (칼·대검만). 생략 시 null */
  carry?: UiCarry | null;
  /** 56라운드 (계약 §13): 무기 고유 자원 · 그로기 (칼·대검만). 생략 시 null */
  gauge?: UiWeaponGauge | null;
  groggy?: UiGroggy | null;
  /** 57라운드 (계약 §14.1): 태그·세트·이중 개성·저주. 생략 시 빈 값 */
  build?: UiBuildState | null;
}

export function buildUiMap(ctx: SnapshotContext): UiMap {
  const L = ctx.layout;
  if (!L) return { rooms: [], connections: [], currentRoomId: '', gridW: 0, gridH: 0 };
  const warpable = new Set(ctx.warp.targets);
  return {
    rooms: L.rooms.map((r) => ({
      id: r.id,
      type: r.type,
      cells: r.cells.map((c) => ({ cx: c.cx, cy: c.cy })),
      visited: ctx.visited.has(r.id),
      cleared: ctx.cleared.has(r.id),
      warpable: warpable.has(r.id),
      structureDot: ctx.structureRooms?.has(r.id) ?? false,
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
    potionMax:
      ECONOMY.drops.potion.maxCarry +
      gameState.meta.potionCarry +
      gameState.build.mods(gameState.passives, gameState.weapon).stats.potionMaxAdd,
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
      return {
        name: d?.name ?? id,
        level,
        description: d?.description ?? '',
        tags: [...(d?.tags ?? [])],
        maxLevel: gameState.passives.maxLevel,
      };
    }),
    savesLeft: gameState.savesLeft,
    seed: gameState.seed,
    map: buildUiMap(ctx),
    paused: ctx.paused,
    menu: ctx.menu,
    playerName: gameState.playerName,
    floorTitle: STORY.floors[gameState.stageId]?.title ?? gameState.stage.name,
    names: { potion: STORY.names.potion, gold: STORY.names.gold, shop: STORY.names.shop, souls: STORY.names.souls },
    inCombat: ctx.inCombat,
    sprinting: ctx.sprinting,
    warp: { ...ctx.warp, targets: [...ctx.warp.targets] },
    interactable: ctx.interactable
      ? {
          ...ctx.interactable,
          cost: ctx.interactable.cost ? { ...ctx.interactable.cost } : null,
          hold: ctx.interactable.hold ? { ...ctx.interactable.hold } : null,
          screen: { ...ctx.interactable.screen },
        }
      : null,
    statuses: (ctx.statuses ?? []).map((st) => ({ ...st })),
    route: ctx.route ? { ...ctx.route, nodes: ctx.route.nodes.map((n) => ({ ...n, links: [...n.links] })) } : null,
    resource: ctx.resource ? { ...ctx.resource } : null,
    muted: ctx.muted ?? false,
    lab: ctx.lab ?? false,
    carry: ctx.carry ? { ...ctx.carry } : null,
    gauge: ctx.gauge ? { ...ctx.gauge } : null,
    groggy: ctx.groggy ? { ...ctx.groggy } : null,
    build: ctx.build
      ? {
          tags: ctx.build.tags.map((t) => ({ ...t, effects: t.effects.map((e) => ({ ...e })) })),
          dualTraits: ctx.build.dualTraits.map((d) => ({ ...d })),
          curse: ctx.build.curse ? { ...ctx.build.curse } : null,
        }
      : { tags: [], dualTraits: [], curse: null },
  };
}
