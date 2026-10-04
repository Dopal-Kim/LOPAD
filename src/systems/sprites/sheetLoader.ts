/**
 * 시트 로드 공용 단계 (57라운드 A2: Preloader 에서 분리 — 부팅 묶음과 무기 묶음이 같은 길로 읽는다).
 * 1) 후보 경로(v3 → v2 → 기존, 매니페스트에 있는 것) 의 시트 JSON 2) JSON 이 읽힌 것만 이미지 — 격자 시트는 spritesheet,
 *    `frames` 가 배열·객체인 트림 아틀라스(57라운드 Q16, `sheetAtlas`)는 atlas 3) 텍스처가 생긴 것만 spriteLibrary 에 등록.
 * 무기 묶음(`preloadWeaponSheets`)은 런 무기가 정해진 씬(Game·WeaponLab)의 preload 에서 그 무기만 읽고, 다른 무기의 시트는 내린다.
 */
import Phaser from 'phaser';
import { ASSETS } from '../../core/Constants';
import { spriteLibrary } from './sprites';
import { sheetJsonCandidates } from './spriteMeta';
import { normalizeStructureSheet, sheetToWorldUnits, type SheetDef, type SheetJson } from './sheetJson';
import { sheetTextureKey, type SheetRequest } from './sheetPaths';
import { isAtlasSheet, parseAtlasSheet, type AtlasData } from './sheetAtlas';
import { weaponSheetRequests } from './sheetSets';

export interface PendingSheet {
  req: SheetRequest;
  jsonKey: string;
  /** JSON 이 있는 폴더 (이미지 상대 경로의 기준) */
  dir: string;
}

/** 아트 산출물 파일 목록 (Preloader 가 매니페스트를 읽어 넣는다 — 없으면 null = 전부 있다고 본다) */
let manifest: Set<string> | null = null;
/** 지금 시트가 올라가 있는 런 무기 */
let loadedWeapon: string | null = null;

export function setAssetManifest(files: Set<string> | null): void {
  manifest = files;
}

/** 시트 JSON 캐시 키 */
export function sheetJsonKey(req: SheetRequest): string {
  return `json_${sheetTextureKey(req.name, req.action)}`;
}

/** 읽을 JSON 경로: 50·52라운드 새 도트(`v3/`·`v2/`)는 매니페스트에 있을 때만, 없으면 기존 경로 — 그것도 없으면 null */
function pickJsonPath(req: SheetRequest): string | null {
  const listed = (rel: string) => manifest !== null && manifest.has(rel);
  const paths = sheetJsonCandidates(req);
  const legacy = paths[paths.length - 1];
  const rel = paths.slice(0, -1).find(listed) ?? legacy;
  return manifest === null || manifest.has(rel) ? rel : null;
}

/** 시트 JSON 을 로드 큐에 넣는다 (이미 캐시에 있으면 다시 받지 않는다 — 호출 쪽이 `scene.cache.json` 을 본다) */
export function queueSheetJsons(scene: Phaser.Scene, reqs: readonly SheetRequest[]): PendingSheet[] {
  const out: PendingSheet[] = [];
  for (const req of reqs) {
    const rel = pickJsonPath(req);
    if (!rel) continue;
    const jsonKey = sheetJsonKey(req);
    if (!scene.cache.json.exists(jsonKey)) scene.load.json(jsonKey, `${ASSETS.URL}/${rel}`);
    out.push({ req, jsonKey, dir: rel.slice(0, rel.lastIndexOf('/') + 1) });
  }
  return out;
}

/** 시트 JSON → 격자 메타 SheetJson (+ 트림 아틀라스면 Phaser 아틀라스 데이터). 형식이 틀리면 null */
export function readSheetJson(raw: unknown): { json: SheetJson; atlas: AtlasData | null } | null {
  if (!raw || typeof raw !== 'object') return null;
  let json = raw as SheetJson;
  let atlas: AtlasData | null = null;
  if (isAtlasSheet(raw)) {
    const r = parseAtlasSheet(raw);
    if ('error' in r) {
      console.warn(`[sprites] 아틀라스 시트 형식 오류: ${r.error}`);
      return null;
    }
    json = r.json;
    atlas = r.atlas;
  }
  if (!json.image || !(json.frameWidth > 0) || !(json.frameHeight > 0) || !(json.frames > 0)) return null;
  return { json, atlas };
}

/** 읽힌 시트 JSON → SheetDef, 이미지(격자 = spritesheet, 트림 = atlas)를 로드 큐에. JSON 이 없거나 형식이 틀리면 null */
export function queueSheetImage(scene: Phaser.Scene, p: PendingSheet): SheetDef | null {
  const read = readSheetJson(scene.cache.json.get(p.jsonKey));
  if (!read) return null;
  // 구조물 시트(계약 §5)는 fps·loop·directions·pivot 을 생략할 수 있다. 50라운드: 메모 길이는 월드 단위로 (pixelScale)
  const json = sheetToWorldUnits(p.req.category === 'structures' ? normalizeStructureSheet(read.json) : read.json);
  const textureKey = sheetTextureKey(p.req.name, p.req.action);
  const imageUrl = `${ASSETS.URL}/${p.dir}${json.image}`;
  if (!scene.textures.exists(textureKey)) {
    if (read.atlas) scene.load.atlas(textureKey, imageUrl, read.atlas);
    else scene.load.spritesheet(textureKey, imageUrl, { frameWidth: json.frameWidth, frameHeight: json.frameHeight });
  }
  // 동작 이름은 요청 기준 (이펙트 시트의 JSON action 은 파일 이름과 같아 내부 동작 'fx' 로 통일)
  return { ...json, action: p.req.action, category: p.req.category, name: p.req.name, textureKey, imageUrl };
}

/** 텍스처가 실제로 로드된 시트만 등록 (원본 애니 + 이미 만든 층 변형) */
export function registerSheets(scene: Phaser.Scene, defs: readonly SheetDef[]): void {
  spriteLibrary.addSheets(
    scene,
    defs.filter((d) => scene.textures.exists(d.textureKey)),
  );
}

/**
 * 57라운드 A2: 런 무기의 시트를 이 씬의 preload 에서 로드한다 (Game·WeaponLab — 런 시작·이어하기·시험장 무기 교체).
 * 이미 그 무기면 아무것도 하지 않는다. 다른 무기가 올라가 있으면 그 무기만의 시트를 먼저 내린다(GPU 메모리).
 * JSON 이 읽히는 대로 이미지를 같은 로드에 이어 붙이고, 로드가 끝나면(씬 create 전) 등록한다. 로드할 파일이 있으면 true
 */
export function preloadWeaponSheets(scene: Phaser.Scene, weaponId: string): boolean {
  if (loadedWeapon === weaponId) return false;
  if (loadedWeapon) releaseWeaponSheets(scene, loadedWeapon, weaponId);
  loadedWeapon = null;
  const defs: SheetDef[] = [];
  const onJson = (p: PendingSheet) => {
    const d = queueSheetImage(scene, p);
    if (d) defs.push(d);
  };
  const pending = queueSheetJsons(scene, weaponSheetRequests(weaponId));
  const waiting: string[] = [];
  for (const p of pending) {
    if (scene.cache.json.exists(p.jsonKey)) onJson(p);
    else {
      const ev = `${Phaser.Loader.Events.FILE_KEY_COMPLETE}json-${p.jsonKey}`;
      scene.load.once(ev, () => onJson(p));
      waiting.push(ev);
    }
  }
  const finish = () => {
    // 404 로 오지 않은 JSON 의 1회 처리기가 다음 로드에 남지 않게
    for (const ev of waiting) scene.load.removeAllListeners(ev);
    registerSheets(scene, defs);
    loadedWeapon = weaponId;
  };
  if (scene.load.list.size === 0) {
    finish();
    return false;
  }
  scene.load.once(Phaser.Loader.Events.COMPLETE, finish);
  return true;
}

/** 다른 무기로 바뀔 때: 이전 무기만 쓰던 시트를 내린다 (새 무기도 쓰는 시트는 남긴다) */
function releaseWeaponSheets(scene: Phaser.Scene, prevId: string, nextId: string): void {
  const keep = new Set(weaponSheetRequests(nextId).map((r) => sheetTextureKey(r.name, r.action)));
  const drop = weaponSheetRequests(prevId).filter((r) => !keep.has(sheetTextureKey(r.name, r.action)));
  spriteLibrary.removeSheets(scene, drop);
}

/** 디버그: 지금 올라가 있는 런 무기 시트 */
export function loadedWeaponSheets(): string | null {
  return loadedWeapon;
}
