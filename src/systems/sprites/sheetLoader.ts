/**
 * 시트 로드 공용 단계 (57라운드 A2: Preloader 에서 분리 — 부팅 묶음과 무기 묶음이 같은 길로 읽는다).
 * 1) 후보 경로(v3 → v2 → 기존, 매니페스트에 있는 것) 의 시트 JSON 2) JSON 이 읽힌 것만 이미지 — 격자 시트는 spritesheet,
 *    트림 아틀라스(57라운드 Q16·Q38 `atlas57-1`, `sheetAtlas`)는 atlas(여러 장이면 multiatlas) 3) 텍스처가 생긴 것만
 *    spriteLibrary 에 등록.
 * 무기 묶음(`preloadWeaponSheets`)은 런 무기가 정해진 씬(Game·WeaponLab)의 preload 에서 그 무기만 읽고, 다른 무기의 시트는 내린다.
 */
import Phaser from 'phaser';
import { ASSETS } from '../../core/Constants';
import { spriteLibrary } from './sprites';
import { sheetJsonCandidates } from './spriteMeta';
import { normalizeStructureSheet, sheetToWorldUnits, type SheetDef } from './sheetJson';
import { sheetTextureKey, type SheetRequest } from './sheetPaths';
import { readSheetJson as parseSheetJson, type AtlasData } from './sheetAtlas';
import { awakenSheetRequests, bossSheetRequests, weaponSheetRequests } from './sheetSets';
import { SPRITES } from '../../core/Constants';
import { BOSSES } from '../../data';

export interface PendingSheet {
  req: SheetRequest;
  jsonKey: string;
  /** JSON 이 있는 폴더 (이미지 상대 경로의 기준) */
  dir: string;
}

/** 아트 산출물 파일 목록 (Preloader 가 매니페스트를 읽어 넣는다 — 없으면 null = 전부 있다고 본다) */
let manifest: Set<string> | null = null;
/** 지금 시트가 올라가 있는 런 무기 · 각성 오버레이가 올라가 있는 무기 */
let loadedWeapon: string | null = null;
let loadedAwaken: string | null = null;

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

/** 시트 JSON → 격자 메타 SheetJson (+ 트림 아틀라스면 Phaser 아틀라스 데이터). 형식이 틀리면 null (`sheetAtlas.readSheetJson`) */
export function readSheetJson(raw: unknown): ReturnType<typeof parseSheetJson> {
  return parseSheetJson(raw, (msg) => console.warn(`[sprites] 아틀라스 시트 형식 오류: ${msg}`));
}

/** 읽힌 시트 JSON → SheetDef, 이미지(격자 = spritesheet, 트림 = atlas)를 로드 큐에. JSON 이 없거나 형식이 틀리면 null */
export function queueSheetImage(scene: Phaser.Scene, p: PendingSheet): SheetDef | null {
  const read = readSheetJson(scene.cache.json.get(p.jsonKey));
  if (!read) return null;
  // 구조물 시트(계약 §5)는 fps·loop·directions·pivot 을 생략할 수 있다. 50라운드: 메모 길이는 월드 단위로 (pixelScale)
  const json = sheetToWorldUnits(
    p.req.category === 'structures' || p.req.category === 'items' ? normalizeStructureSheet(read.json) : read.json,
  );
  const textureKey = sheetTextureKey(p.req.name, p.req.action);
  const imageUrl = `${ASSETS.URL}/${p.dir}${json.image}`;
  if (!scene.textures.exists(textureKey)) {
    if (read.atlas) queueAtlas(scene, textureKey, `${ASSETS.URL}/${p.dir}`, read.atlas);
    else scene.load.spritesheet(textureKey, imageUrl, { frameWidth: json.frameWidth, frameHeight: json.frameHeight });
  }
  // 동작 이름은 요청 기준 (이펙트 시트의 JSON action 은 파일 이름과 같아 내부 동작 'fx' 로 통일)
  return { ...json, action: p.req.action, category: p.req.category, name: p.req.name, textureKey, imageUrl };
}

/**
 * 트림 아틀라스 이미지를 로드 큐에: 한 장이면 `load.atlas`(JSON Array 데이터), 4096 을 넘어 여러 장이면 `load.multiatlas`
 * (JSON 은 이미 읽었으므로 데이터 객체를 넘기고, 장 이미지는 `dir` 기준 상대 경로)
 */
function queueAtlas(scene: Phaser.Scene, key: string, dir: string, atlas: AtlasData): void {
  if (atlas.pages.length === 1) {
    const page = atlas.pages[0];
    scene.load.atlas(key, `${dir}${page.image}`, { frames: page.frames });
    return;
  }
  // Phaser 타입은 atlasURL 을 string 으로만 적지만 JSONFile 은 데이터 객체를 그대로 받는다 (load.atlas 와 같다)
  const data = { textures: atlas.pages.map((p) => ({ image: p.image, frames: p.frames })) };
  scene.load.multiatlas(key, data as unknown as string, dir);
}

/** 텍스처가 실제로 로드된 시트만 등록 (원본 애니 + 이미 만든 층 변형) */
export function registerSheets(scene: Phaser.Scene, defs: readonly SheetDef[]): void {
  spriteLibrary.addSheets(
    scene,
    defs.filter((d) => scene.textures.exists(d.textureKey)),
  );
}

/**
 * 요청 목록을 이 씬의 로더에 이어 붙인다: JSON 이 읽히는 대로 이미지를 같은 로드에 넣고, 로드가 끝나면 등록한 뒤 done.
 * 로드할 파일이 없으면 바로 등록·done 하고 false
 */
function queueRequests(scene: Phaser.Scene, reqs: readonly SheetRequest[], done: () => void): boolean {
  const defs: SheetDef[] = [];
  const onJson = (p: PendingSheet) => {
    const d = queueSheetImage(scene, p);
    if (d) defs.push(d);
  };
  const pending = queueSheetJsons(scene, reqs);
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
    done();
  };
  if (scene.load.list.size === 0) {
    finish();
    return false;
  }
  scene.load.once(Phaser.Loader.Events.COMPLETE, finish);
  return true;
}

/**
 * 57라운드 A2: 런 무기의 시트를 이 씬의 preload 에서 로드한다 (Game·WeaponLab — 런 시작·이어하기·시험장 무기 교체).
 * 이미 그 무기면 아무것도 하지 않는다. 다른 무기가 올라가 있으면 그 무기만의 시트를 먼저 내린다(GPU 메모리).
 * 60라운드: awaken 이면 최종 각성 오버레이(`<무기 동작>_awaken`, 계약 art §21 — 각성 런에서만)도 같이.
 * JSON 이 읽히는 대로 이미지를 같은 로드에 이어 붙이고, 로드가 끝나면(씬 create 전) 등록한다. 로드할 파일이 있으면 true
 */
export function preloadWeaponSheets(scene: Phaser.Scene, weaponId: string, awaken = false): boolean {
  const wantAwaken = awaken && loadedAwaken !== weaponId;
  if (loadedWeapon === weaponId && !wantAwaken) return false;
  const reqs: SheetRequest[] = [];
  if (loadedWeapon !== weaponId) {
    if (loadedWeapon) releaseWeaponSheets(scene, loadedWeapon, weaponId);
    loadedWeapon = null;
    reqs.push(...weaponSheetRequests(weaponId));
  }
  if (wantAwaken) reqs.push(...awakenSheetRequests(weaponId));
  const had = loadedWeapon;
  return queueRequests(scene, reqs, () => {
    loadedWeapon = had ?? weaponId;
    if (wantAwaken) loadedAwaken = weaponId;
  });
}

/**
 * 60라운드: 런 도중 각성했을 때 (create 뒤 — 시험장 a 키·개성 '각성' 칸) 각성 오버레이를 바로 로드한다. 이미 있으면 done 만.
 * 로드가 끝나기 전까지 오버레이는 없다(무기 그림만)
 */
export function loadAwakenSheets(scene: Phaser.Scene, weaponId: string, done: () => void = () => {}): void {
  if (loadedAwaken === weaponId) {
    done();
    return;
  }
  const started = queueRequests(scene, awakenSheetRequests(weaponId), () => {
    loadedAwaken = weaponId;
    done();
  });
  if (started && !scene.load.isLoading()) scene.load.start();
}

/** 다른 무기로 바뀔 때: 이전 무기만 쓰던 시트를 내린다 (새 무기도 쓰는 시트는 남긴다) — 각성 오버레이 포함 */
function releaseWeaponSheets(scene: Phaser.Scene, prevId: string, nextId: string): void {
  const keep = new Set(weaponSheetRequests(nextId).map((r) => sheetTextureKey(r.name, r.action)));
  const prev = [...weaponSheetRequests(prevId), ...(loadedAwaken === prevId ? awakenSheetRequests(prevId) : [])];
  const drop = prev.filter((r) => !keep.has(sheetTextureKey(r.name, r.action)));
  spriteLibrary.removeSheets(scene, drop);
  if (loadedAwaken === prevId) loadedAwaken = null;
}

/** 61라운드 단계 2: 보스 묶음을 올렸는지 (한 번 올리면 게임 동안 둔다 — 1층 범위) */
let bossLoaded = false;

/**
 * 61라운드 단계 2 첫 로딩 줄이기: 보스 노드에 들어갈 때(Game preload) 보스 묶음을 읽는다. 이미 있으면 false.
 * 끝나면 자기 시트가 없는 보스를 폴백 시트에 잇는다 (결정 로그 J)
 */
export function preloadBossSheets(scene: Phaser.Scene): boolean {
  if (bossLoaded) return false;
  return queueRequests(scene, bossSheetRequests(), () => {
    bossLoaded = true;
    aliasBossFallbacks();
  });
}

/** 자기 시트가 없는 보스는 폴백 시트를 쓴다 (2~7층 보스 = stage1 시트 + 층 램프 스왑) */
export function aliasBossFallbacks(): void {
  for (const id of Object.keys(BOSSES))
    if (!spriteLibrary.has(id) && spriteLibrary.has(SPRITES.BOSS_FALLBACK_SHEET))
      spriteLibrary.alias(id, SPRITES.BOSS_FALLBACK_SHEET);
}

/** 디버그: 지금 올라가 있는 런 무기 시트 (각성 오버레이면 + '+awaken') */
export function loadedWeaponSheets(): string | null {
  return loadedWeapon && loadedAwaken === loadedWeapon ? `${loadedWeapon}+awaken` : loadedWeapon;
}
