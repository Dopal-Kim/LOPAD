/**
 * 61 단계 6 (P14 §3 · 계약 art §28 · UI §19) 그림 속 입구 그림 · 수련장 지도 그림 지연 로드.
 * 파일: `sprites/paint/door_<region>_<kind>.png` (+ 같은 이름 .json 메타 doorRect·doorCenter·light — UI 가 씀, 시스템은 로드만) ·
 * `sprites/paint/doors.json` (별칭 aliases) · `sprites/paint/map_training.png` (+ .json 메타 rooms[]{index,x,y,r}).
 * 입구 찾는 순서 (art §28): 정확한 이름 → 별칭 → `door_<region>_battle` → 없음(UI 대체).
 * 한 장 약 0.9MB 라 전환에 쓰는 1~2장만 그때 받는다. 텍스처 키 = `paint/<이름>` (cache.json 같은 키에 메타).
 */
import type Phaser from 'phaser';
import { ASSETS } from '../../core/Constants';
import { assetListed } from '../../systems/sprites/sheetLoader';
import { resolveDoorName } from '../../systems/transition/doorNames';

const DIR = 'sprites/paint';
/** 별칭 표 (doors.json) cache.json 키 */
const DOOR_INDEX = 'paint/doors';

export const paintKey = (name: string): string => `paint/${name}`;
export const MAP_TRAINING = 'map_training';

/** 로드돼 있으면 텍스처 키 */
export function paintLoaded(scene: Phaser.Scene, name: string): string | undefined {
  const key = paintKey(name);
  return scene.textures.exists(key) ? key : undefined;
}

/** 별칭 표를 받아 둔다 (작은 json — 씬 시작에 한 번) */
export function loadDoorIndex(scene: Phaser.Scene): void {
  if (scene.cache.json.exists(DOOR_INDEX) || !assetListed(`${DIR}/doors.json`)) return;
  scene.load.json(DOOR_INDEX, `${ASSETS.URL}/${DIR}/doors.json`);
  if (!scene.load.isLoading()) scene.load.start();
}

/** 지역·노드 종류 → 쓸 입구 그림 이름 (`door_…`, 없으면 null) */
export function doorFor(scene: Phaser.Scene, region: string, kind: string): string | null {
  const index = scene.cache.json.get(DOOR_INDEX) as { aliases?: Record<string, string> } | undefined;
  return resolveDoorName(region, kind, index?.aliases ?? null, (name) => assetListed(`${DIR}/${name}.png`));
}

/** 받는 중인 그림 (텍스처 키 → 받는 씬) — 같은 키를 두 번 넣지 않게 (그 씬이 끝났으면 다시 받는다) */
const inflight = new Map<string, Phaser.Scene>();

/** 그림(+메타)을 받아 둔다 — 이미 있거나 받는 중이거나 매니페스트에 없으면 아무것도 안 한다. 받기 시작했으면 true */
export function loadPaint(scene: Phaser.Scene, names: readonly string[], onDone?: () => void): boolean {
  let queued = false;
  for (const name of names) {
    const key = paintKey(name);
    if (scene.textures.exists(key) || !assetListed(`${DIR}/${name}.png`)) continue;
    const owner = inflight.get(key);
    if (owner && owner.sys.isActive()) {
      // 이 씬이 이미 받는 중 — 끝나기를 같이 기다린다
      if (owner === scene) queued = true;
      continue;
    }
    inflight.set(key, scene);
    scene.load.once(`filecomplete-image-${key}`, () => inflight.delete(key));
    scene.load.image(key, `${ASSETS.URL}/${DIR}/${name}.png`);
    if (assetListed(`${DIR}/${name}.json`) && !scene.cache.json.exists(key))
      scene.load.json(key, `${ASSETS.URL}/${DIR}/${name}.json`);
    queued = true;
  }
  if (!queued) return false;
  if (onDone) scene.load.once('complete', onDone);
  if (!scene.load.isLoading()) scene.load.start();
  return true;
}

/**
 * 입구 그림 하나를 받은 뒤(또는 waitMs 가 지나면) then(doorKey) — 전환 시작 직전에 쓴다.
 * 이미 있으면 바로, 없으면 null 로 바로
 */
export function withDoor(
  scene: Phaser.Scene,
  name: string | null,
  waitMs: number,
  then: (doorKey: string | undefined) => void,
): void {
  if (!name) return then(undefined);
  const ready = paintLoaded(scene, name);
  if (ready) return then(ready);
  let done = false;
  const finish = () => {
    if (done) return;
    done = true;
    then(paintLoaded(scene, name));
  };
  if (!loadPaint(scene, [name], finish)) return finish();
  scene.time.delayedCall(waitMs, finish);
}

/** 수련장 지도 메타의 방 자리 (순서 index — 데이터 방 순서와 같은 차례) → 논리 화면 좌표 */
export function mapRoomPoint(
  scene: Phaser.Scene,
  order: number,
  screen: { w: number; h: number },
): { x: number; y: number } | undefined {
  const key = paintKey(MAP_TRAINING);
  if (!scene.cache.json.exists(key)) return undefined;
  const meta = scene.cache.json.get(key) as
    { width?: number; height?: number; rooms?: { index?: number; x: number; y: number }[] } | undefined;
  const rooms = [...(meta?.rooms ?? [])].sort((a, b) => (a.index ?? 0) - (b.index ?? 0));
  const r = rooms[order];
  const w = meta?.width ?? screen.w;
  const h = meta?.height ?? screen.h;
  if (!r || !(w > 0) || !(h > 0)) return undefined;
  return { x: Math.round((r.x / w) * screen.w), y: Math.round((r.y / h) * screen.h) };
}
