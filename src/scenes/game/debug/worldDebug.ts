/**
 * `?debug=1` 검증 훅 — 조명·쿼터뷰·외벽·상흔 · 빌드·2차 묶음·보스 (60라운드 6-1: DebugHooks 에서 분리, 동작 그대로)
 */
import { gameState } from '../../../core/GameState';
import type { Boss } from '../../../objects/Boss';
import type { Mob } from '../../../objects/Mob';
import { isBossPatternName } from '../../../data/bossPatterns';
import { sanitizeScar } from '../../../systems/setup/scar';
import type { Game } from '../../Game';
import { CONSUMABLE_IDS } from '../../../data/bundle2';
import type { ConsumableId, ElitePrefixId, MapInfoId } from '../../../data/bundle2Types';
import { buyIntel } from '../../../systems/bundle2/routeExtras';
import type { DebugApi } from '../../../debug';

/** 53라운드 Q4 검증용 견본 상흔 (정규화 3획: 긴 사선 · 갈래 · 짧은 가로) */
const DEBUG_SCAR = {
  v: 1,
  aspect: 460 / 420,
  strokes: [
    [0.22, 0.12, 0.38, 0.34, 0.5, 0.52, 0.63, 0.74, 0.78, 0.9],
    [0.5, 0.52, 0.36, 0.66, 0.28, 0.84],
    [0.56, 0.3, 0.7, 0.26, 0.84, 0.32],
  ],
};

export function worldDebug(
  g: Game,
): Pick<
  DebugApi,
  'lighting' | 'quarter' | 'border' | 'scar' | 'injectScar' | 'build' | 'bundle' | 'boss' | 'setBossHp'
> {
  return {
    lighting: () => g.lighting?.summary() ?? null,
    quarter: () =>
      g.world.quarter
        ? { ...g.world.quarter.summary, placements: g.world.bigProps, canal: g.world.canal, decals: g.world.decals }
        : null,
    border: () => (g.border ? { ...g.border.summary(), lookUp: +g.cam.lookUpPx.toFixed(1) } : null),
    scar: () => ({
      view: (({ x, y, width, height }) => ({ x, y, width, height }))(g.cameras.main.worldView),
      data: gameState.scar,
      state: g.player.scar.state,
      anchor: g.player.scar.lastAnchor,
      aboveLight: g.player.scar.aboveLight,
    }),
    injectScar: (scar) => {
      const s = sanitizeScar(scar ?? DEBUG_SCAR);
      if (!s) return false;
      gameState.scar = s;
      g.player.scar.refresh();
      return true;
    },
    build: {
      info: () => g.build.debug(),
      ui: () => g.build.toUi(),
      addPassive: (id, levels = 1) => {
        let ok = false;
        for (let i = 0; i < levels; i++) ok = gameState.passives.add(id) || ok;
        return ok;
      },
      curse: (id, pact) => g.build.grantCurse(id, { pact: Boolean(pact) }),
      endCurse: () => g.build.endCurse(),
      dual: (id) => g.build.addDualTrait(id),
      perfect: (kind) => (kind === 'perfectEvade' ? g.build.perfect.onEvade() : g.build.perfect.onPerfect(kind, 10)),
      drink: () => g.build.drink('potion'),
      bossFloor: (n) => {
        gameState.build.bossFloorCleared = n;
        gameState.build.touch();
      },
      evolveSlots: () =>
        g.buildMenus
          .slots()
          .map((sl) => ({ kind: sl.kind, enabled: sl.enabled, node: sl.node?.id ?? null, locked: sl.locked ?? null })),
      openPassiveMenu: (source = 'boss') => g.buildMenus.openPassiveMenu(source),
      openCurseMenu: () => g.buildMenus.openCurseMenu(),
      openEvolveMenu: () => {
        gameState.weapon.choicePending = true;
        g.buildMenus.openEvolveMenu();
      },
    },
    bundle: {
      info: () => g.bundle.debug(),
      gain: (id) => (CONSUMABLE_IDS as readonly string[]).includes(id) && g.bundle.consumables.gain(id as ConsumableId),
      elite: (prefix) => {
        const p = g.player;
        const mobs = (g.mobs.getChildren() as Mob[]).filter((m) => m.active && !m.isBoss && !m.elite);
        mobs.sort((a, b) => Math.hypot(a.x - p.x, a.y - p.y) - Math.hypot(b.x - p.x, b.y - p.y));
        return mobs[0] ? g.bundle.elites.makeElite(mobs[0], (prefix as ElitePrefixId | undefined) ?? null) : false;
      },
      intel: (id) => {
        const ex = gameState.bundle.floor;
        return ex ? buyIntel(ex, id as MapInfoId) : false;
      },
    },
    boss: {
      info: () => findBoss(g)?.debugInfo ?? null,
      arena: () => g.bossArena?.summary() ?? null,
      force: (patterns, now) => {
        const b = findBoss(g);
        if (!b) return false;
        const list = patterns.filter(isBossPatternName);
        b.debugForce(list.length > 0 ? list : null, now);
        return true;
      },
      phase: (n) => {
        const b = findBoss(g);
        if (!b) return false;
        b.debugPhase(n);
        return true;
      },
      hitCup: () => g.bossArena?.debugHitCup() ?? false,
      geom: () => {
        const b = findBoss(g);
        return b ? { ...b.debugGeom, cup: g.bossArena?.debugCup() ?? null } : null;
      },
      tilt: (opts) => {
        const b = findBoss(g);
        if (!g.bossArena || !b) return null;
        g.bossArena.startTilt({
          ...b.params<Parameters<NonNullable<typeof g.bossArena>['startTilt']>[0]>('spin'),
          ...opts,
        });
        return g.bossArena.screen.summary();
      },
    },
    setBossHp: (hp) => {
      for (const m of g.mobs.getChildren() as Mob[]) {
        if (m.isBoss && m.active) {
          m.takeDamage(Math.max(0, m.hp - hp));
          return true;
        }
      }
      return false;
    },
  };
}

/**
 * 57라운드 Q38 검증: 올라간 텍스처의 GPU 메모리 추정 (장마다 폭 × 높이 × 4 바이트, 밉맵 없음). 합계 · 분류별 합 ·
 * 큰 텍스처 상위 10
 */
export function textureBytes(g: Game): { total: number; byGroup: Record<string, number>; top: [string, number][] } {
  const list: [string, number][] = [];
  const byGroup: Record<string, number> = {};
  for (const key of g.textures.getTextureKeys()) {
    const bytes = g.textures.get(key).source.reduce((a, s) => a + s.width * s.height * 4, 0);
    list.push([key, bytes]);
    // 시트(sheet_ — 층 변형 @·색 교체 # 포함) · 외벽(border_) · 타일 · 그 밖
    const group = key.startsWith('sheet_')
      ? /[@#]/.test(key)
        ? 'sheetVariant'
        : 'sheet'
      : key.startsWith('border_')
        ? 'border'
        : key.startsWith('tile')
          ? 'tiles'
          : 'other';
    byGroup[group] = (byGroup[group] ?? 0) + bytes;
  }
  list.sort((a, b) => b[1] - a[1]);
  return { total: list.reduce((a, [, b]) => a + b, 0), byGroup, top: list.slice(0, 10) };
}

function findBoss(g: Game): Boss | null {
  for (const m of g.mobs.getChildren() as Mob[]) if (m.active && m.isBoss) return m as Boss;
  return null;
}

/** `route()` 디버그: 계약 UiRoute + 종류·클리어·출구·경로·선택지·전투장·지역·세트·튜토리얼·잠금 */
export function routeInfo(g: Game): unknown {
  const route = gameState.route;
  if (!route) return null;
  const arena = g.nodeArena;
  const sp = arena?.setPiece;
  return {
    ...route.toUi(),
    kind: g.nodeKind,
    cleared: route.currentCleared,
    exitOpen: g.route.exitOpen,
    path: [...route.path],
    options: route.nextOptions().map((n) => ({ id: n.id, kind: n.kind, name: n.name })),
    kinds: route.graph.nodes.map((n) => ({ id: n.id, kind: n.kind, col: n.col, row: n.row })),
    arena: g.layout?.arena ?? null,
    region: arena ? { id: arena.regionId, tileset: arena.tileset, skin: g.world.skin.textureKey } : null,
    setPiece: sp
      ? {
          template: sp.template,
          fixed: sp.fixed,
          cover: sp.cover.length,
          center: sp.center,
          signs: sp.signs,
          dummies: sp.dummies,
          decor: sp.decor.map((d) => ({ name: d.name, role: d.role, sprites: d.sprites })),
          view: g.setPieceView?.summary ?? null,
        }
      : null,
    tutorial: g.tutorial
      ? { step: g.tutorial.machine.stepIndex, done: g.tutorial.done, skip: () => g.tutorial?.skip() }
      : null,
    room: g.layout?.rooms[0]
      ? { id: g.layout.rooms[0].id, type: g.layout.rooms[0].type, floor: g.layout.rooms[0].floor }
      : null,
    locked: g.route.locked(g.time.now),
  };
}
