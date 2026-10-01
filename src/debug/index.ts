import { gameState } from '../core/GameState';
import { uiCommands } from '../contract/ui';
import type { Mob } from '../objects/Mob';
import type { RoomDirector } from '../systems/RoomDirector';
import type { TileWorld } from '../world/TileWorld';

/**
 * 자동 검증용 훅. URL 에 ?debug=1 이 있을 때만 window.__lopad 에 노출된다.
 * 게임 로직이 아니라 테스트 도구이며, HUD/UI 가 아니다.
 */
export interface DebugApi {
  state: typeof gameState;
  rooms: () => { id: string; type: string; x: number; y: number }[];
  teleport: (roomId: string) => void;
  moveTo: (x: number, y: number) => void;
  director: () => { alive: number; wave: number; active: string | undefined };
  stage: () => { index: number; id: string; name: string; savesLeft: number; exitOpen: boolean; isLast: boolean };
  save: () => unknown;
  lastAttack: () => unknown;
  shots: () => unknown[];
  meta: () => unknown;
  addPassive: (id: string) => boolean;
  ui: () => { pause: () => void; resume: () => void; snapshot: () => unknown; scenes: () => string[] };
  economy: () => unknown;
  pickups: () => { kind: string; value: number; x: number; y: number }[];
  /** 플레이어를 향해 투사체 1발 (거리 px, 속도 px/s, 공격력) */
  fireAtPlayer: (distPx: number, speedPx: number, attack: number) => void;
  player: () => { x: number; y: number; action: string };
  stunAll: (ms: number) => void;
  mobs: () => { id: string; hp: number; x: number; y: number; stunned: boolean }[];
  camera: () => { scrollX: number; scrollY: number; zoom: number };
  killAll: () => number;
  hurtAll: (amount: number) => void;
  tileAt: (tx: number, ty: number) => number;
  doorsOf: (roomId: string) => { x: number; y: number; id: number }[][];
}

export function exposeDebug(api: {
  world: TileWorld;
  director: RoomDirector;
  player: { setPosition: (x: number, y: number) => unknown; body: { reset: (x: number, y: number) => void } };
  mobs: () => Mob[];
  kill: (m: Mob) => void;
  hurt: (m: Mob, amount: number) => void;
  fireAtPlayer: (distPx: number, speedPx: number, attack: number) => void;
  playerInfo: () => { x: number; y: number; action: string };
  stunAll: (ms: number) => void;
  now: () => number;
  stage: () => { index: number; id: string; name: string; savesLeft: number; exitOpen: boolean; isLast: boolean };
  save: () => unknown;
  lastAttack: () => unknown;
  shots: () => unknown[];
  meta: () => unknown;
  addPassive: (id: string) => boolean;
  scenes: () => string[];
  economy: () => unknown;
  pickups: () => { kind: string; value: number; x: number; y: number }[];
  camera: () => { scrollX: number; scrollY: number; zoom: number };
}): void {
  if (typeof location === 'undefined' || !new URLSearchParams(location.search).has('debug')) return;
  const dbg: DebugApi = {
    state: gameState,
    rooms: () =>
      api.world.layout.rooms.map((r) => {
        const c = api.world.roomCenter(r);
        return { id: r.id, type: r.type, x: c.x, y: c.y };
      }),
    teleport: (roomId) => {
      const c = api.world.roomCenter(api.world.room(roomId));
      api.player.body.reset(c.x, c.y);
    },
    moveTo: (x, y) => api.player.body.reset(x, y),
    director: () => api.director.debugInfo,
    stage: () => api.stage(),
    save: () => api.save(),
    lastAttack: () => api.lastAttack(),
    meta: () => api.meta(),
    addPassive: (id) => api.addPassive(id),
    ui: () => ({
      pause: () => uiCommands.pause(),
      resume: () => uiCommands.resume(),
      snapshot: () => uiCommands.getUiSnapshot(),
      scenes: () => api.scenes(),
    }),
    shots: () => api.shots(),
    economy: () => api.economy(),
    pickups: () => api.pickups(),
    fireAtPlayer: (d, s, a) => api.fireAtPlayer(d, s, a),
    player: () => api.playerInfo(),
    stunAll: (ms) => api.stunAll(ms),
    mobs: () =>
      api.mobs().map((m) => ({
        id: (m as Mob & { id?: string }).id ?? '?',
        hp: m.hp,
        x: m.x,
        y: m.y,
        stunned: m.isStunned(api.now()),
      })),
    camera: () => api.camera(),
    killAll: () => {
      const list = api.mobs();
      for (const m of list) api.kill(m);
      return list.length;
    },
    hurtAll: (amount) => {
      for (const m of api.mobs()) api.hurt(m, amount);
    },
    tileAt: (tx, ty) => api.world.layer.getTileAt(tx, ty)?.index ?? -1,
    doorsOf: (roomId) =>
      api.world
        .room(roomId)
        .doors.map((d) => d.tiles.map((t) => ({ ...t, id: api.world.layer.getTileAt(t.x, t.y)?.index ?? -1 }))),
  };
  (window as unknown as { __lopad: DebugApi }).__lopad = dbg;
}
