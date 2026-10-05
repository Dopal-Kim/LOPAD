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
import {
  AWAKEN_OVERLAY_SUFFIX,
  awakenInFxId,
  awakenSheetRequests,
  branchSheetRequests,
  growthOverlayAction,
  growthSheetRequests,
  weaponSheetRequests,
} from './sheetSets';
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
/** 지금 시트가 올라가 있는 런 무기 · 무기 묶음 밖에서 더 올린 시트(갈래·각성 외형 — 무기를 바꿀 때 내린다) */
let loadedWeapon: string | null = null;
const extraLoaded = new Set<SheetRequest>();

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
export function queueRequests(scene: Phaser.Scene, reqs: readonly SheetRequest[], done: () => void): boolean {
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

/** 61 G: 런 무기 묶음 범위 — 경로 노드(갈래·길) · 각성 외형(고른 갈래·단계) */
export interface WeaponLoadScope {
  /** 시험장 = 갈래 그림 전부 */
  lab: boolean;
  /** 지금 경로 노드 id (1차·2차) */
  path: readonly string[];
  /** 각성 외형 (고른 갈래 id · 단계) — 없으면 null */
  growth: { branch: string; stage: 1 | 2; legacy: boolean } | null;
}

/** 아트 산출물 파일(assets 상대 경로)이 매니페스트에 있는가 (매니페스트가 없으면 true) */
export function assetListed(rel: string): boolean {
  return manifest === null || manifest.has(rel);
}

/** 이 요청의 시트 파일이 매니페스트에 있는가 (매니페스트가 없으면 true) */
export function sheetListed(req: SheetRequest): boolean {
  return pickJsonPath(req) !== null;
}

/**
 * 61 G 각성 외형 요청 (art §26 완료): 1차 a1 (+2차 a2·a2_glow) 오버레이 · 각성 연출 fx — 옛 `_awaken` 대신.
 * 그 동작의 a1 시트가 매니페스트에 없을 때만 옛 `<동작>_awaken` 폴백, 연출 fx 가 없을 때만 옛 `<무기>_awaken_in`.
 * 셋째 갈래(legacy)는 옛 각성 궤적 `<fx>_awaken` 도 (FxPool 교체 — AwakenFlow.aliases)
 */
export function growthLoadRequests(weaponId: string, scope: WeaponLoadScope): SheetRequest[] {
  const g = scope.growth;
  if (!g) return [];
  const range = scope.lab ? 'all' : scope.path;
  const want = growthSheetRequests(weaponId, g.branch, g.stage, range);
  const out = want.filter((r) => sheetListed(r));
  const have = new Set(out.map((r) => `${r.category}/${r.action}/${r.name}`));
  const fxListed = out.some((r) => r.category === 'fx');
  for (const r of awakenSheetRequests(weaponId, range)) {
    if (r.category === 'weapons') {
      const action = r.action.slice(0, -`_${AWAKEN_OVERLAY_SUFFIX}`.length);
      if (!have.has(`weapons/${growthOverlayAction(g.branch, 1, action)}/${weaponId}`)) out.push(r);
    } else if (r.name === awakenInFxId(weaponId)) {
      if (!fxListed) out.push(r);
    } else if (g.legacy) out.push(r);
  }
  return out;
}

/**
 * 57라운드 A2: 런 무기의 시트를 이 씬의 preload 에서 로드한다 (Game·WeaponLab — 런 시작·이어하기·시험장 무기 교체).
 * 다른 무기가 올라가 있으면 그 무기만의 시트를 먼저 내린다(GPU 메모리). 이미 올라간 시트는 다시 받지 않는다.
 * 61 G (P12 · VRAM): 런은 갈래 그림을 지금 경로 노드만 + 고른 갈래의 각성 외형만 (시험장은 갈래 그림 전부).
 * JSON 이 읽히는 대로 이미지를 같은 로드에 이어 붙이고, 로드가 끝나면(씬 create 전) 등록한다. 로드할 파일이 있으면 true
 */
export function preloadWeaponSheets(scene: Phaser.Scene, weaponId: string, scope: WeaponLoadScope): boolean {
  if (loadedWeapon !== weaponId && loadedWeapon) releaseWeaponSheets(scene, loadedWeapon, weaponId);
  const has = (r: SheetRequest) => scene.textures.exists(sheetTextureKey(r.name, r.action));
  const reqs = [
    ...weaponSheetRequests(weaponId, scope.lab ? 'all' : scope.path),
    ...growthLoadRequests(weaponId, scope),
  ].filter((r) => !has(r));
  loadedWeapon = weaponId;
  for (const r of reqs) extraLoaded.add(r);
  return queueRequests(scene, reqs, () => {});
}

/**
 * 61 G: 런 도중 각성했을 때 (create 뒤 — 1차·2차 각성·시험장 갈래 바꾸기) 그 갈래·길 그림과 각성 외형을 바로 로드한다.
 * 이미 있으면 done 만. 로드가 끝나기 전까지 오버레이는 없다(무기 그림만)·갈래 fx 는 윤곽 플레이스홀더
 */
export function loadGrowthSheets(
  scene: Phaser.Scene,
  weaponId: string,
  scope: WeaponLoadScope,
  done: () => void = () => {},
): void {
  const has = (r: SheetRequest) => scene.textures.exists(sheetTextureKey(r.name, r.action));
  const reqs = [
    ...(scope.lab ? [] : branchSheetRequests(weaponId, scope.path)),
    ...growthLoadRequests(weaponId, scope),
  ].filter((r) => !has(r));
  for (const r of reqs) extraLoaded.add(r);
  const started = queueRequests(scene, reqs, done);
  if (started && !scene.load.isLoading()) scene.load.start();
}

/** 다른 무기로 바뀔 때: 이전 무기만 쓰던 시트를 내린다 (새 무기도 쓰는 시트는 남긴다) — 갈래·각성 외형 포함 */
function releaseWeaponSheets(scene: Phaser.Scene, prevId: string, nextId: string): void {
  const keep = new Set(weaponSheetRequests(nextId).map((r) => sheetTextureKey(r.name, r.action)));
  const prev = [...weaponSheetRequests(prevId), ...extraLoaded];
  const drop = prev.filter((r) => !keep.has(sheetTextureKey(r.name, r.action)));
  spriteLibrary.removeSheets(scene, drop);
  extraLoaded.clear();
}

/** 자기 시트가 없는 보스는 폴백 시트를 쓴다 (2~7층 보스 = stage1 시트 + 층 램프 스왑) */
export function aliasBossFallbacks(): void {
  for (const id of Object.keys(BOSSES))
    if (!spriteLibrary.has(id) && spriteLibrary.has(SPRITES.BOSS_FALLBACK_SHEET))
      spriteLibrary.alias(id, SPRITES.BOSS_FALLBACK_SHEET);
}

/** 디버그: 지금 올라가 있는 런 무기 시트 (+ 더 올린 갈래·각성 외형 시트 수) */
export function loadedWeaponSheets(): string | null {
  return loadedWeapon ? `${loadedWeapon}${extraLoaded.size ? `+${extraLoaded.size}` : ''}` : null;
}
