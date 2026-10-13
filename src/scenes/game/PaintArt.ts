/**
 * 61 단계 6 (P14 §3 · 계약 art §28 · UI §19) 그림 속 입구 그림 · 수련장 지도 그림 지연 로드.
 * 파일: `sprites/paint/door_<region>_<kind>.png` (+ 같은 이름 .json 메타 doorRect·doorCenter·light — UI 가 씀, 시스템은 로드만) ·
 * `sprites/paint/doors.json` (별칭 aliases) · `sprites/paint/map_training.png` (+ .json 메타 rooms[]{index,x,y,r}).
 * 입구 찾는 순서 (art §28): 정확한 이름 → 별칭 → `door_<region>_battle` → 없음(UI 대체).
 * 한 장 약 0.9MB 라 전환에 쓰는 1~2장만 그때 받는다. 텍스처 키 = `paint/<이름>` (cache.json 같은 키에 메타).
 * 62 H: 입구 그림은 노드 지도·수련장 지도의 **작은 미리보기**로도 쓴다 (RoutePreview 가 고를 수 있는 노드 + 그다음 열만 미리 받는다).
 */
import type Phaser from 'phaser';
import { ASSETS } from '../../core/Constants';
import { assetListed } from '../../systems/sprites/sheetLoader';
import { queueImageOnce } from '../../systems/sprites/imageOnce';
import { resolveDoorName, smallDoorName } from '../../systems/transition/doorNames';

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

const paintListed = (name: string): boolean => assetListed(`${DIR}/${name}.png`);

/** 지역·노드 종류(·62 I 위험) → 쓸 입구 그림 이름 (`door_…`, 없으면 null) */
export function doorFor(scene: Phaser.Scene, region: string, kind: string, risk?: string | null): string | null {
  const index = scene.cache.json.get(DOOR_INDEX) as { aliases?: Record<string, string> } | undefined;
  return resolveDoorName(region, kind, index?.aliases ?? null, paintListed, risk);
}

/** 62 I (art §32-2): 지도 미리보기 카드 그림 이름 — `_small` 카드판이 있으면 그것 (층 전환 등 큰 그림은 doorFor 그대로) */
export function previewDoorFor(scene: Phaser.Scene, region: string, kind: string, risk?: string | null): string | null {
  return smallDoorName(doorFor(scene, region, kind, risk), paintListed);
}

/** 별칭 표(doors.json)를 이미 받았나 — 62 H 미리보기 키 기억은 받은 뒤에만 */
export function doorIndexReady(scene: Phaser.Scene): boolean {
  return scene.cache.json.exists(DOOR_INDEX) || !assetListed(`${DIR}/doors.json`);
}

/** 메타 json 을 이미 큐에 넣은 키 (씬 사이 같은 json 을 두 번 넣지 않게 — 받히면 지운다) */
const jsonQueued = new Set<string>();

/**
 * 그림(+메타)을 받아 둔다 — 이미 있거나 매니페스트에 없으면 아무것도 안 한다. 62 H: 그림은 `queueImageOnce`(씬 사이 이중 로드 없음 —
 * 다른 씬이 받는 중이면 들어오기를 기다린다). 기다릴 것이 있으면 true, onDone = 그림이 다 들어오고 이 로더가 끝난 뒤(메타 포함)
 */
export function loadPaint(scene: Phaser.Scene, names: readonly string[], onDone?: () => void): boolean {
  let pending = 0;
  let started = false;
  let queuedHere = false;
  const arrive = () => {
    pending -= 1;
    if (started && pending === 0) onDone?.();
  };
  for (const name of names) {
    const key = paintKey(name);
    if (scene.textures.exists(key) || !assetListed(`${DIR}/${name}.png`)) continue;
    pending += 1;
    if (queueImageOnce(scene, key, `${ASSETS.URL}/${DIR}/${name}.png`, arrive)) queuedHere = true;
    if (assetListed(`${DIR}/${name}.json`) && !scene.cache.json.exists(key) && !jsonQueued.has(key)) {
      jsonQueued.add(key);
      scene.load.once(`filecomplete-json-${key}`, () => jsonQueued.delete(key));
      scene.load.json(key, `${ASSETS.URL}/${DIR}/${name}.json`);
      queuedHere = true;
    }
  }
  if (pending === 0 && !queuedHere) return false;
  if (queuedHere) {
    pending += 1;
    scene.load.once('complete', arrive);
    if (!scene.load.isLoading()) scene.load.start();
  }
  started = true;
  if (pending === 0) onDone?.();
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
