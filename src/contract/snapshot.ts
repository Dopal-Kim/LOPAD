/** 시스템 파트: 계약 스냅샷 생성 (UI 파트는 import 금지). */
import { gameState } from '../core/GameState';
import { tagOn } from '../data/build';
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
  UiConsumableSlot,
  UiElite,
  UiNodeTrial,
  UiSettings,
  UiBossSnapshot,
  UiGrowth,
  UiTraining,
  UiDoor,
  UiExitHint,
} from './ui';
import { ownedRelics } from '../systems/relics';
import { DEFAULT_SETTINGS } from '../systems/settings';
import { weaponVerbs } from '../systems/weapon/verbs';
import { nextMarkOf } from '../systems/growth/growth';
import { firstSteps } from '../systems/ritual/firstSteps';
import { RITUAL } from '../core/Constants';
import { metaSummary } from './metaSummary';
import { withLoop2D, type Loop2DSnapshotContext } from './snapshotLoop2D';

export interface SnapshotContext {
  layout: FloorLayout | null;
  visited: ReadonlySet<string>;
  cleared: ReadonlySet<string>;
  bossName: string | null;
  /** 61라운드 (계약 §17): 보스 선택 필드 (국면·파훼 창·촛대·어둠). 생략 시 없음 */
  bossExtra?: Partial<UiBossSnapshot> | null;
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
  /** 53라운드: 넣기/뽑기 (61라운드: F 삭제 — 늘 null). 생략 시 null */
  carry?: UiCarry | null;
  /** 56라운드 (계약 §13): 무기 고유 자원 · 그로기 (칼·대검만). 생략 시 null */
  gauge?: UiWeaponGauge | null;
  groggy?: UiGroggy | null;
  /** 57라운드 (계약 §14.1): 태그·세트·이중 개성·저주. 생략 시 빈 값 */
  build?: UiBuildState | null;
  /** 60라운드 (계약 §14.8~14.10): 소모품 칸 · 엘리트 이름표 · 노드 성과 진행. 생략 시 null / [] / null */
  consumable?: UiConsumableSlot | null;
  elites?: readonly UiElite[];
  nodeTrial?: UiNodeTrial | null;
  /** 61라운드 (계약 §15): 설정. 생략 시 기본값 */
  settings?: UiSettings;
  /** 61 G (계약 §18): 무기 성장. 생략 시 null */
  growth?: UiGrowth | null;
  /** 61 단계 6 (계약 §19): 수련장. 생략 시 null */
  training?: UiTraining | null;
  /** 62 루프 2 C (P1-6): 출구 방향. 생략 시 null */
  exitHint?: UiExitHint | null;
  /** 62 루프 2 E: 출구 문 상태. 생략 시 null */
  door?: UiDoor | null;
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

export function buildSnapshot(ctx: SnapshotContext & Loop2DSnapshotContext): UiSnapshot {
  const w = gameState.weapon;
  // 62 루프 2 시스템 D: 노점 카드·팻말·전체화면·묶인 키 (snapshotLoop2D)
  return withLoop2D(ctx, {
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
      // 61 G: 옛 '개성 n/임계' 자리 = 각성 게이지 · 다음 눈금 (정식 표시는 growth)
      personality: Math.floor(w.gauge),
      threshold: ctx.growth?.next?.at ?? nextMarkOf(gameState.build.floor, w.marksDone).at,
      secondaryName: w.def.secondary.name,
    },
    boss:
      gameState.bossMaxHp > 0
        ? {
            ...(ctx.bossExtra ?? {}),
            name: ctx.bossName ?? '보스',
            hp: gameState.bossHp,
            maxHp: gameState.bossMaxHp,
            phase: gameState.bossPhase,
          }
        : null,
    stats: {
      attack: gameState.attack,
      defense: gameState.defense,
      crit: gameState.crit,
      sense: gameState.senses.sense,
    },
    // 62 루프 2 C (P1-5): 유품 — 옛 passives 칸은 호환으로 같은 유품을 옛 꼴(이름 · 한 문장 · 태그 하나)로
    relics: ownedRelics(gameState.passives, w.id),
    passives: Object.entries(gameState.passives.owned).map(([id, level]) => {
      const d = gameState.passives.def(id);
      const r = ownedRelics(
        { owned: { [id]: level }, def: (x) => gameState.passives.def(x), maxLevel: gameState.passives.maxLevel },
        w.id,
      )[0];
      if (r) return { name: r.name, level, description: r.line, tags: r.tag ? [r.tag] : [], maxLevel: r.maxLevel };
      return {
        name: d?.name ?? id,
        level,
        description: d?.description ?? '',
        // 61라운드 P4: 이 층에서 꺼진 태그는 빼고
        tags: (d?.tags ?? []).filter((t) => tagOn(t, gameState.build.floor)),
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
    // 61라운드 P1: 무기 4동사 (갈래가 바꾼 칸 포함)
    weaponVerbs: weaponVerbs(w.id, w.def, w.nodes),
    groggy: ctx.groggy ? { ...ctx.groggy } : null,
    build: ctx.build
      ? {
          tags: ctx.build.tags.map((t) => ({ ...t, effects: t.effects.map((e) => ({ ...e })) })),
          dualTraits: ctx.build.dualTraits.map((d) => ({ ...d })),
          curse: ctx.build.curse ? { ...ctx.build.curse } : null,
        }
      : { tags: [], dualTraits: [], curse: null },
    consumable: ctx.consumable
      ? { ...ctx.consumable, item: ctx.consumable.item ? { ...ctx.consumable.item } : null }
      : null,
    elites: (ctx.elites ?? []).map((e) => ({ ...e, prefixes: [...e.prefixes], screen: { ...e.screen } })),
    nodeTrial: ctx.nodeTrial ? { ...ctx.nodeTrial } : null,
    settings: { ...(ctx.settings ?? DEFAULT_SETTINGS) },
    growth: ctx.growth
      ? {
          ...ctx.growth,
          marks: ctx.growth.marks.map((m) => ({ ...m })),
          next: ctx.growth.next ? { ...ctx.growth.next } : null,
          branches: ctx.growth.branches.map((b) => ({
            ...b,
            paths: [{ ...b.paths[0] }, { ...b.paths[1] }] as typeof b.paths,
          })),
          traits: ctx.growth.traits.map((t) => ({ ...t })),
          temper: { ...ctx.growth.temper },
          firstTime: { ...ctx.growth.firstTime },
        }
      : null,
    training: ctx.training
      ? {
          ...ctx.training,
          tasks: ctx.training.tasks.map((t) => ({ ...t })),
          rooms: ctx.training.rooms.map((r) => ({ ...r })),
        }
      : null,
    // 62 P1-10: 첫 생 첫 노드들만 작은 키 막대 (시험장·수련장 제외)
    keyBar:
      !ctx.lab &&
      !ctx.training &&
      firstSteps.keyBar(ctx.route?.nodes.find((n) => n.state === 'current')?.col, RITUAL.KEY_BAR_NODES),
    meta: metaSummary(),
    exitHint: ctx.exitHint ? { ...ctx.exitHint } : null,
    door: ctx.door ? { ...ctx.door, screen: { ...ctx.door.screen } } : null,
  });
}
