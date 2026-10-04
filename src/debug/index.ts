import type Phaser from 'phaser';
import { gameState } from '../core/GameState';
import { UI_EVENTS, uiBus, uiCommands, type UiMenuId, type UiWarpDenied } from '../contract/ui';
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
    /** 49라운드: 계약 경로 메뉴 선택 (uiCommands.select) — 시험장 메뉴 검증용 */
    select: (menuId: UiMenuId, key: string) => void;
    /** 49라운드: 계약 경로 무기 시험장 진입 · 음소거 */
    startWeaponLab: () => void;
    setMuted: (muted: boolean) => void;
    toTitle: () => void;
  };
  economy: () => unknown;
  pickups: () => { kind: string; value: number; x: number; y: number }[];
  /** 플레이어를 향해 투사체 1발 (거리 px, 속도 px/s, 공격력) */
  fireAtPlayer: (distPx: number, speedPx: number, attack: number) => void;
  player: () => PlayerInfo;
  /** 로드된 스프라이트 시트·애니 키·현재 층 변형 */
  /** 57라운드 A2: weaponLoaded = 지금 올라간 런 무기 시트 · textureCount = 텍스처 수 */
  sprites: () => {
    sheets: string[];
    anims: string[];
    variant: string;
    aliases: Record<string, string>;
    weaponLoaded: string | null;
    textureCount: number;
  };
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
  /** 45라운드: 계약 경로(uiCommands.warpTo)로 워프 요청. ok = 시작, reason = WARP_DENIED 사유 */
  warp: (roomId: string) => { ok: boolean; reason: string | null };
  /** 45라운드: 워프 상태(ready·blocked·targets·warping) + 전투 여부·현재 방·잠금 남은 ms·마지막 워프 */
  warpInfo: () => WarpDebugInfo;
  /** 45라운드: 달리기 허용·중·배율·속도(px/s)·먼지 횟수 */
  sprintInfo: () => SprintDebugInfo;
  /** 47라운드: 구조물 목록 (id·종류·방·중심 좌표·타일·상태·아트 여부·다 씀) */
  structures: () => StructureDebugInfo[];
  /** 47라운드: 층 구조물 상태 (빚·취기·판돈·불씨·불붙은 무기·전당·링·룰렛·웅덩이·최근 결과) */
  structureState: () => Record<string, unknown>;
  /** 47라운드: 구조물 앞으로 순간이동 (id 또는 종류 이름 — 종류면 첫 번째). 이동한 좌표 */
  gotoStructure: (idOrKind: string) => { id: string; x: number; y: number } | null;
  /** 47라운드: 다음 프레임에 E 를 누른 것으로 (묘는 2초 누르기 완료로) */
  pressE: () => void;
  /** 47라운드: 타격형 구조물을 플레이어 쪽에서 한 번 친다 (id 또는 종류 이름) */
  hitStructure: (idOrKind: string) => boolean;
  /** 47라운드: 계약 §9 interactable · statuses */
  interactable: () => unknown;
  statuses: () => unknown;
  /** 47라운드: n층(1부터)으로 바로 이동 (세이브 없음) */
  gotoFloor: (n: number) => void;
  /** 48라운드 노드 지도: 계약 UiRoute + 현재 노드 세부(종류·클리어·출구·선택 중) */
  route: () => unknown;
  /** 48라운드: 다음 노드 선택 열기(출구에 선 것과 같음) · 노드 고르기(uiCommands.chooseNode 와 같은 경로) */
  openRouteChooser: () => boolean;
  chooseNode: (id: string) => boolean;
  /** 53라운드 Q47: 노드 고르기 취소 (uiCommands.cancelChoose 와 같은 경로) */
  cancelChoose: () => boolean;
  /** 48라운드 검증: 링크와 무관하게 이 층의 노드로 바로 (층 상태 유지) */
  gotoNode: (id: string) => boolean;
  /** 48라운드: 출구 타일 위로 순간이동 (출구가 열려 있을 때) */
  gotoExit: () => boolean;
  /** 48라운드: 3연격 상태(마지막 타·다음 허용 시각) + 마지막 근접 판정(모양·원점·맞은 수) */
  combo: () => unknown;
  /** 55라운드 §17 판정 모양 오버레이 켜기·끄기 (인자 없으면 그대로) — 반환 = 켜짐 여부 */
  hitShapes: (on?: boolean) => boolean;
  /** 48라운드: 탄생 연출 상태 · 건너뛰기 */
  birth: () => unknown;
  skipBirth: () => void;
  /** 49라운드: 무기 자원(기력·탄창·과열)·휴대(뽑음·오버레이 방식)·내딛기·정지 상태 */
  weaponState: () => unknown;
  /** 49라운드: 자원 값을 바로 바꾼다 (기력 바닥·탄창 비우기·최대 열 검증용). 자원이 없으면 false */
  setResource: (value: number) => boolean;
  /** 56라운드: 무기 고유 자원(검기·울분·숨)·그로기·낙인·일섬·꽂아내리기·월드 문구·숨 집중·차지 유지음 속도 */
  weaponKit: () => unknown;
  /** 56라운드: 고유 자원 값을 바로 바꾼다 (검기 3단 = 300 등). 자원이 없으면 false */
  setGauge: (value: number) => boolean;
  /** 56라운드 2단계 캡처용: 게임 씬 갱신을 멈추고(그림은 그대로) 다시 잇는다 */
  freeze: (on: boolean) => void;
  /** 49라운드 무기 시험장: 허수아비 누적 피해·맞은 수·쏜 탄 수 · 메뉴 */
  lab: () => unknown;
  /** 49라운드 무기 시험장: 'lab' 또는 'labBranch' 메뉴 열기 (L 키와 같은 경로) */
  openLabMenu: (which: 'lab' | 'labBranch') => boolean;
  /** 50라운드: 조명 요약(켜짐·주변광·광원 수) · 쿼터뷰 벽 요약(없으면 null) */
  lighting: () => unknown;
  quarter: () => unknown;
  /** 53라운드 Q6·Q8: 외벽 테두리 요약(없으면 null) · 카메라 북쪽 치우침 · Q4 상흔 상태 · 상흔 주입(없으면 견본 3획) */
  border: () => unknown;
  scar: () => unknown;
  injectScar: (scar?: unknown) => boolean;
  /** 54라운드 보스: 상태(페이즈·패턴·강화·강제·무적·기록) · 방 환경(촛대·술통·웅덩이·어둠·기울기) · 패턴 강제 · 페이즈 강제 */
  boss: BossDebugApi;
}

export interface BossDebugApi {
  info: () => unknown;
  arena: () => unknown;
  /** 패턴을 이 순서로 되풀이 (빈 목록 = 해제). now 면 지금 바로 다음 패턴 */
  force: (patterns: string[], now?: boolean) => boolean;
  /** 페이즈 n(1부터)으로 (HP 를 그 페이즈 시작 값으로 — 진입 연출 포함) */
  phase: (n: number) => boolean;
  /** 지금 약점 잔을 맞힌 것으로 */
  hitCup: () => boolean;
  /** 보스 판정·그림 기하 (바디·스프라이트·그림자·약점 잔) */
  geom: () => unknown;
  /** 세상이 돈다 화면 효과만 바로 (1층 spin 수치, opts 로 흐림·길이 덮어쓰기 — 검증용) */
  tilt: (opts?: { blur?: number; durationMs?: number }) => unknown;
}

export interface StructureDebugInfo {
  id: string;
  kind: string;
  roomId: string;
  x: number;
  y: number;
  tx: number;
  ty: number;
  w: number;
  h: number;
  state: string;
  visual: string;
  art: boolean;
  exhausted: boolean;
  rolling: boolean;
}

export interface StructureDebugApi {
  list: () => StructureDebugInfo[];
  state: () => Record<string, unknown>;
  standPoint: (id: string) => { x: number; y: number } | null;
  pressE: () => void;
  hit: (id: string) => boolean;
  interactable: () => unknown;
  statuses: () => unknown;
}

export interface WarpDebugInfo {
  ready: boolean;
  blocked: 'combat' | 'busy' | null;
  targets: string[];
  warping: boolean;
  inCombat: boolean;
  currentRoomId: string;
  lockedMs: number;
  last: unknown;
}

export interface SprintDebugInfo {
  allowed: boolean;
  sprinting: boolean;
  mult: number;
  speedPx: number;
  vx: number;
  vy: number;
  dust: number;
  /** 53라운드 Q10: 현재 애니 키 · 걷기/달리기 재생 배속 · 감속 배율 (낮으면 walk) */
  anim: string | null;
  strideRate: number;
  slowMult: number;
}

export type FeelPatch = Partial<{
  shake: number;
  hitstop: number;
  knockback: number;
  numbers: boolean;
  trail: boolean;
  flash: boolean;
  /** 54라운드 Q7 화면 기울기 배율 (0 = 끔) */
  tilt: number;
}>;

/** 카메라 스크롤·배율·클램프 영역 (32라운드 추종 검증용) */
export interface CameraInfo {
  scrollX: number;
  scrollY: number;
  zoom: number;
  /** 48라운드: 게임 월드 카메라 배율 (zoom 은 창 배율). 52라운드: 실제 캔버스 배율 (= logicalZoom × resolution) */
  camZoom?: number;
  /** 52라운드: 논리 px 1개 = 실제 캔버스 px · 월드 → 논리 화면 배율 */
  resolution?: number;
  logicalZoom?: number;
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
  /** 57라운드 A2: weaponLoaded = 지금 올라간 런 무기 시트 · textureCount = 텍스처 수 */
  sprites: () => {
    sheets: string[];
    anims: string[];
    variant: string;
    aliases: Record<string, string>;
    weaponLoaded: string | null;
    textureCount: number;
  };
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
  warpInfo: () => WarpDebugInfo;
  sprintInfo: () => SprintDebugInfo;
  structures: StructureDebugApi;
  gotoFloor: (n: number) => void;
  route: () => unknown;
  openRouteChooser: () => boolean;
  chooseNode: (id: string) => boolean;
  /** 53라운드 Q47: 노드 고르기 취소 (uiCommands.cancelChoose 와 같은 경로) */
  cancelChoose: () => boolean;
  gotoNode: (id: string) => boolean;
  gotoExit: () => boolean;
  combo: () => unknown;
  /** 55라운드 §17 판정 모양 오버레이 켜기·끄기 (인자 없으면 그대로) — 반환 = 켜짐 여부 */
  hitShapes: (on?: boolean) => boolean;
  birth: () => unknown;
  skipBirth: () => void;
  weaponState: () => unknown;
  setResource: (value: number) => boolean;
  weaponKit: () => unknown;
  setGauge: (value: number) => boolean;
  freeze: (on: boolean) => void;
  lab: () => unknown;
  openLabMenu: (which: 'lab' | 'labBranch') => boolean;
  lighting: () => unknown;
  quarter: () => unknown;
  border: () => unknown;
  scar: () => unknown;
  injectScar: (scar?: unknown) => boolean;
  boss: BossDebugApi;
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
      select: (menuId, key) => uiCommands.select(menuId, key),
      startWeaponLab: () => uiCommands.startWeaponLab(),
      setMuted: (muted) => uiCommands.setMuted(muted),
      toTitle: () => uiCommands.toTitle(),
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
    warp: (roomId) => {
      let reason: string | null = null;
      const onDenied = (p: UiWarpDenied) => (reason = p.reason);
      uiBus.on(UI_EVENTS.WARP_DENIED, onDenied);
      const ok = uiCommands.warpTo(roomId);
      uiBus.off(UI_EVENTS.WARP_DENIED, onDenied);
      return { ok, reason };
    },
    warpInfo: () => api.warpInfo(),
    sprintInfo: () => api.sprintInfo(),
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
    structures: () => api.structures.list(),
    structureState: () => api.structures.state(),
    gotoStructure: (idOrKind) => {
      const list = api.structures.list();
      const s =
        list.find((x) => x.id === idOrKind) ??
        list.find((x) => x.kind === idOrKind && !x.exhausted && x.state !== 'broken');
      if (!s) return null;
      const p = api.structures.standPoint(s.id);
      if (!p) return null;
      api.player.body.reset(p.x, p.y);
      return { id: s.id, x: p.x, y: p.y };
    },
    pressE: () => api.structures.pressE(),
    hitStructure: (idOrKind) => {
      const list = api.structures.list();
      const s = list.find((x) => x.id === idOrKind) ?? list.find((x) => x.kind === idOrKind && x.state === 'idle');
      return s ? api.structures.hit(s.id) : false;
    },
    interactable: () => api.structures.interactable(),
    statuses: () => api.structures.statuses(),
    gotoFloor: (n) => api.gotoFloor(n),
    route: () => api.route(),
    openRouteChooser: () => api.openRouteChooser(),
    chooseNode: (id) => api.chooseNode(id),
    cancelChoose: () => api.cancelChoose(),
    gotoNode: (id) => api.gotoNode(id),
    gotoExit: () => api.gotoExit(),
    combo: () => api.combo(),
    hitShapes: (on) => api.hitShapes(on),
    birth: () => api.birth(),
    skipBirth: () => api.skipBirth(),
    weaponState: () => api.weaponState(),
    setResource: (v) => api.setResource(v),
    weaponKit: () => api.weaponKit(),
    freeze: (on) => api.freeze(on),
    setGauge: (v) => api.setGauge(v),
    lab: () => api.lab(),
    openLabMenu: (which) => api.openLabMenu(which),
    lighting: () => api.lighting(),
    quarter: () => api.quarter(),
    border: () => api.border(),
    scar: () => api.scar(),
    injectScar: (scar) => api.injectScar(scar),
    boss: api.boss,
    doorsOf: (roomId) =>
      api.world.room(roomId).doors.map((d) => d.tiles.map((t) => ({ ...t, id: api.world.tileIdAt(t.x, t.y) }))),
  };
  (window as unknown as { __lopad: DebugApi }).__lopad = dbg;
}
