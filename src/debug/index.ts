import type Phaser from 'phaser';
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
  /** 적·보스를 옮긴다 (보스 벽 충돌 검증용). index 는 mobs() 순서 */
  moveMob: (index: number, x: number, y: number) => boolean;
  director: () => { alive: number; wave: number; active: string | undefined };
  stage: () => { index: number; id: string; name: string; savesLeft: number; exitOpen: boolean; isLast: boolean };
  save: () => unknown;
  lastAttack: () => unknown;
  /** 마지막 RUN_ENDED 페이로드 (엔딩 line·ending 검증용) */
  lastResult: () => unknown;
  shots: () => unknown[];
  meta: () => unknown;
  addPassive: (id: string) => boolean;
  ui: () => {
    pause: () => void;
    resume: () => void;
    snapshot: () => unknown;
    scenes: () => string[];
    continueRun: () => void;
    hasSave: () => boolean;
  };
  economy: () => unknown;
  pickups: () => { kind: string; value: number; x: number; y: number }[];
  /** 플레이어를 향해 투사체 1발 (거리 px, 속도 px/s, 공격력) */
  fireAtPlayer: (distPx: number, speedPx: number, attack: number) => void;
  player: () => PlayerInfo;
  /** 로드된 스프라이트 시트·애니 키·현재 층 변형 */
  sprites: () => { sheets: string[]; anims: string[]; variant: string; aliases: Record<string, string> };
  /** 활성 이펙트 스프라이트 */
  fx: () => unknown;
  stunAll: (ms: number) => void;
  mobs: () => {
    id: string;
    hp: number;
    x: number;
    y: number;
    stunned: boolean;
    anim: string | null;
    shoved: boolean;
    frame: number;
    animPaused: boolean;
  }[];
  /** 다음 층으로 강제 전환 (팔레트 스왑·타일셋 검증용) */
  nextStage: () => void;
  camera: () => CameraInfo;
  killAll: () => number;
  /** 특정 적 처치 (index 는 mobs() 순서) */
  killMob: (index: number) => boolean;
  /** 모든 적에게 피해 (crit 이면 치명타 연출) */
  hurtAll: (amount: number, crit?: boolean) => void;
  /** 게임 타일 ID (시트 인덱스가 아님) */
  tileAt: (tx: number, ty: number) => number;
  /** 소품 레이어의 시트 인덱스 (-1 = 없음) */
  propAt: (tx: number, ty: number) => number;
  /** 바닥 레이어의 시트 인덱스 (-1 = 없음) — roomFloors 검증용 */
  tileIndexAt: (tx: number, ty: number) => number;
  world: () => { tileset: string; art: boolean; props: number };
  doorsOf: (roomId: string) => { x: number; y: number; id: number }[][];
  /** 개성 게이지를 value 로 두고 임계 판정 (27라운드 검증용) */
  setPersonality: (value: number) => void;
  weapon: () => unknown;
  playerExtra: () => {
    action: string;
    guarding: boolean;
    shadowPrimed: boolean;
    aim: number;
    aimReady: boolean;
    shoved: boolean;
  };
  /** 오디오 요약: 로드 수·현재 BGM·최근 효과음·음소거 */
  audio: () => unknown;
  /** 피격 피드백 요약(35라운드): 설정 배율·히트스톱·흔들림 오프셋·데미지 숫자·글꼴·피격 이펙트 시트 유무 */
  feel: () => unknown;
  /** 강도 조절 (접근성): `setFeel({ shake: 0, hitstop: 0, knockback: 0, numbers: false })` */
  setFeel: (patch: FeelPatch) => unknown;
  /** 넉백 중인 적 수 */
  shoved: () => number;
  /** 35라운드 2단계: 활성 예고 마커·시트 유무 */
  telegraph: () => unknown;
  /** 활성 적 투사체 (텍스처·애니·회전·반사 여부) */
  projectiles: () => unknown[];
  /** 적·보스 행동 상태 (사수 조준/재장전·사격 수, 결사병 상태, 보스 패턴·기록) */
  behavior: () => unknown[];
  /** 마지막 보스 내리찍기 */
  lastSlam: () => unknown;
  /** 활성 방에 적 추가 (집단 돌격 검증용) */
  spawnEnemy: (id: string, x: number, y: number) => boolean;
  /** 보스 HP 를 내려 페이즈 전환 (피해 처리 경로) */
  setBossHp: (hp: number) => boolean;
  /** 42라운드: 활성 잔상 궤적(샘플 좌표) */
  trails: () => unknown;
  /** 42라운드: 화면 오버레이·채도 감소 상태 */
  screen: () => unknown;
  /** 35라운드 3단계: 조준 점선·차지 게이지 상태 */
  aimFx: () => unknown;
  /** 3지선다가 열린 상태에서 노드 id 로 바로 선택 (검증용) */
  evolveTo: (id: string) => boolean;
}

export type FeelPatch = Partial<{
  shake: number;
  hitstop: number;
  knockback: number;
  numbers: boolean;
  trail: boolean;
  flash: boolean;
}>;

/** 카메라 스크롤·배율·클램프 영역 (32라운드 추종 검증용) */
export interface CameraInfo {
  scrollX: number;
  scrollY: number;
  zoom: number;
  width: number;
  height: number;
  region: { x: number; y: number; w: number; h: number };
}

export interface PlayerInfo {
  x: number;
  y: number;
  action: string;
  anim: string | null;
  dir: string;
  animated: boolean;
  /** 무기 오버레이가 보이는 프레임 번호 (-1 = 숨김) */
  overlayFrame: number;
  moving: boolean;
}

export function exposeDebug(api: {
  world: TileWorld;
  director: RoomDirector;
  player: { setPosition: (x: number, y: number) => unknown; body: { reset: (x: number, y: number) => void } };
  mobs: () => Mob[];
  kill: (m: Mob) => void;
  hurt: (m: Mob, amount: number, crit?: boolean) => void;
  fireAtPlayer: (distPx: number, speedPx: number, attack: number) => void;
  playerInfo: () => PlayerInfo;
  sprites: () => { sheets: string[]; anims: string[]; variant: string; aliases: Record<string, string> };
  fx: () => unknown;
  stunAll: (ms: number) => void;
  now: () => number;
  stage: () => { index: number; id: string; name: string; savesLeft: number; exitOpen: boolean; isLast: boolean };
  save: () => unknown;
  lastAttack: () => unknown;
  lastResult: () => unknown;
  shots: () => unknown[];
  meta: () => unknown;
  addPassive: (id: string) => boolean;
  scenes: () => string[];
  economy: () => unknown;
  pickups: () => { kind: string; value: number; x: number; y: number }[];
  camera: () => CameraInfo;
  setPersonality: (value: number) => void;
  weapon: () => unknown;
  playerExtra: () => {
    action: string;
    guarding: boolean;
    shadowPrimed: boolean;
    aim: number;
    aimReady: boolean;
    shoved: boolean;
  };
  nextStage: () => void;
  audio: () => unknown;
  feel: () => unknown;
  setFeel: (patch: FeelPatch) => unknown;
  shoved: () => number;
  telegraph: () => unknown;
  projectiles: () => unknown[];
  behavior: () => unknown[];
  lastSlam: () => unknown;
  spawnEnemy: (id: string, x: number, y: number) => boolean;
  setBossHp: (hp: number) => boolean;
  trails: () => unknown;
  screen: () => unknown;
  aimFx: () => unknown;
  evolveTo: (id: string) => boolean;
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
    moveMob: (index, x, y) => {
      const m = api.mobs()[index];
      if (!m || !m.active) return false;
      m.body.reset(x, y);
      return true;
    },
    director: () => api.director.debugInfo,
    stage: () => api.stage(),
    save: () => api.save(),
    lastAttack: () => api.lastAttack(),
    lastResult: () => api.lastResult(),
    meta: () => api.meta(),
    addPassive: (id) => api.addPassive(id),
    ui: () => ({
      pause: () => uiCommands.pause(),
      resume: () => uiCommands.resume(),
      snapshot: () => uiCommands.getUiSnapshot(),
      scenes: () => api.scenes(),
      continueRun: () => uiCommands.continueRun(),
      hasSave: () => uiCommands.hasSave(),
    }),
    shots: () => api.shots(),
    economy: () => api.economy(),
    pickups: () => api.pickups(),
    fireAtPlayer: (d, s, a) => api.fireAtPlayer(d, s, a),
    player: () => api.playerInfo(),
    sprites: () => api.sprites(),
    fx: () => api.fx(),
    stunAll: (ms) => api.stunAll(ms),
    mobs: () =>
      api.mobs().map((m) => ({
        id: (m as Mob & { id?: string }).id ?? '?',
        hp: m.hp,
        x: m.x,
        y: m.y,
        stunned: m.isStunned(api.now()),
        anim: m.visual.current,
        shoved: m.isShoved,
        frame: m.anims.currentFrame?.index ?? 0,
        animPaused: m.anims.isPaused,
      })),
    nextStage: () => api.nextStage(),
    camera: () => api.camera(),
    setPersonality: (v) => api.setPersonality(v),
    weapon: () => api.weapon(),
    playerExtra: () => api.playerExtra(),
    audio: () => api.audio(),
    feel: () => api.feel(),
    setFeel: (patch) => api.setFeel(patch),
    shoved: () => api.shoved(),
    telegraph: () => api.telegraph(),
    projectiles: () => api.projectiles(),
    behavior: () => api.behavior(),
    lastSlam: () => api.lastSlam(),
    spawnEnemy: (id, x, y) => api.spawnEnemy(id, x, y),
    setBossHp: (hp) => api.setBossHp(hp),
    trails: () => api.trails(),
    screen: () => api.screen(),
    aimFx: () => api.aimFx(),
    evolveTo: (id) => api.evolveTo(id),
    killAll: () => {
      const list = api.mobs();
      for (const m of list) api.kill(m);
      return list.length;
    },
    killMob: (index) => {
      const m = api.mobs()[index];
      if (!m || !m.active) return false;
      api.kill(m);
      return true;
    },
    hurtAll: (amount, crit) => {
      for (const m of api.mobs()) api.hurt(m, amount, crit);
    },
    tileAt: (tx, ty) => api.world.tileIdAt(tx, ty),
    propAt: (tx, ty) => api.world.propsLayer?.getTileAt(tx, ty)?.index ?? -1,
    tileIndexAt: (tx, ty) => api.world.layer.getTileAt(tx, ty)?.index ?? -1,
    world: () => ({
      tileset: api.world.skin.textureKey,
      art: api.world.skin.isArt,
      props: api.world.propsLayer?.filterTiles((t: Phaser.Tilemaps.Tile) => t.index >= 0).length ?? 0,
    }),
    doorsOf: (roomId) =>
      api.world.room(roomId).doors.map((d) => d.tiles.map((t) => ({ ...t, id: api.world.tileIdAt(t.x, t.y) }))),
  };
  (window as unknown as { __lopad: DebugApi }).__lopad = dbg;
}
