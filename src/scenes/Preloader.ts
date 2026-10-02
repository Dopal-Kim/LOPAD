import Phaser from 'phaser';
import { ASSETS, COLORS, FEEL, SCENES, SPRITES, TEXTURES, TILE } from '../core/Constants';
import { TileId } from '../systems/mapgen';
import { SaveSlot, browserStorage } from '../systems/save';
import { BOSSES, ENEMIES, RUN, WEAPONS } from '../data';
import { metaStore } from '../systems/meta';
import { audio } from '../systems/audio';
import { ensureFont } from '../systems/fonts';
import { audioFileRel, audioManifestRel, isAudioManifest, type AudioManifest } from '../systems/audioDefs';
import { spriteLibrary } from '../systems/sprites';
import {
  allFxSheetIds,
  normalizeStructureSheet,
  sheetJsonPath,
  sheetJsonPathV2,
  sheetToWorldUnits,
  sheetTextureKey,
  wantedSheets,
  type SheetDef,
  type SheetJson,
} from '../systems/spriteDefs';
import {
  TileSkin,
  namedTilesetJsonPath,
  namedTilesetJsonPathV2,
  namedTilesetTextureKey,
  regionSkins,
  tileSkins,
  tilesetJsonPath,
  tilesetTextureKey,
  type TilesetJson,
} from '../world/tileskin';
import { regionTilesets } from '../systems/route';
import { UI_SCENES } from '../ui';
import { allStructureSprites } from '../systems/structures/data';

interface Manifest {
  files: string[];
}

/** 음향 매니페스트 JSON 캐시 키 */
const AUDIO_MANIFEST_KEY = 'audio_manifest';

/**
 * 아트·음향 산출물 로드 (계약 contracts/art-assets.md, 음향은 assets/audio/manifest.json 계약 초안).
 * 1) manifest.json → 존재하는 파일만 2) 시트·타일셋·음향 매니페스트 JSON → 3) PNG·WAV → 애니 등록·오디오 등록.
 * 없는 파일은 조용히 건너뛰고(404 는 loaderror 로 무시) 플레이스홀더 텍스처로 폴백한다.
 */
export class Preloader extends Phaser.Scene {
  private manifest: Set<string> | null = null;
  private pendingSheets: { req: ReturnType<typeof wantedSheets>[number]; jsonKey: string; dir: string }[] = [];
  private pendingTiles: { floor: number; jsonKey: string }[] = [];
  /** 49라운드 art §7.3: 지역 타일셋 (tiles/stage1_<region>.json, 50라운드: tiles/v2/ 가 있으면 먼저) */
  private pendingRegionTiles: { name: string; jsonKey: string; dir: string }[] = [];
  private audioManifestQueued = false;

  constructor() {
    super(SCENES.PRELOADER);
  }

  preload(): void {
    // 로드 실패(404 등)는 오류가 아니라 "아트 미제공" 이다
    this.load.on(Phaser.Loader.Events.FILE_LOAD_ERROR, () => {});
    this.load.json(TEXTURES.MANIFEST, `${ASSETS.URL}/${ASSETS.MANIFEST}`);
  }

  create(): void {
    // 데미지 숫자 글꼴(34라운드 규칙 Galmuri11): CSS @font-face 로드를 미리 시작. 실패하면 monospace 폴백
    void ensureFont(FEEL.DAMAGE_TEXT.FONT_FAMILY);
    this.buildTileTexture();
    const m = this.cache.json.get(TEXTURES.MANIFEST) as Manifest | undefined;
    this.manifest = m && Array.isArray(m.files) ? new Set(m.files) : null;
    this.queueJsons();
    this.load.once(Phaser.Loader.Events.COMPLETE, () => this.queueImages());
    this.load.start();
  }

  /** 매니페스트에 있는(또는 매니페스트가 없으면 전부) 시트·타일셋 JSON 을 큐에 넣는다 */
  private queueJsons(): void {
    const exists = (rel: string) => this.manifest === null || this.manifest.has(rel);
    // 50라운드 새 2배 도트(`v2/`)는 매니페스트에 있을 때만 (매니페스트가 없으면 기존 경로)
    const listed = (rel: string) => this.manifest !== null && this.manifest.has(rel);
    const dirOf = (rel: string) => rel.slice(0, rel.lastIndexOf('/') + 1);
    this.pendingSheets = [];
    for (const req of wantedSheets(
      Object.keys(ENEMIES),
      Object.keys(BOSSES),
      Object.keys(WEAPONS),
      allFxSheetIds(WEAPONS),
      allStructureSprites(),
    )) {
      const v2 = sheetJsonPathV2(req);
      const rel = listed(v2) ? v2 : sheetJsonPath(req);
      if (!exists(rel)) continue;
      const jsonKey = `json_${sheetTextureKey(req.name, req.action)}`;
      this.load.json(jsonKey, `${ASSETS.URL}/${rel}`);
      this.pendingSheets.push({ req, jsonKey, dir: dirOf(rel) });
    }
    this.pendingTiles = [];
    for (let floor = 1; floor <= RUN.order.length; floor++) {
      const rel = tilesetJsonPath(floor);
      if (!exists(rel)) continue;
      const jsonKey = `json_${tilesetTextureKey(floor)}`;
      this.load.json(jsonKey, `${ASSETS.URL}/${rel}`);
      this.pendingTiles.push({ floor, jsonKey });
    }
    this.pendingRegionTiles = [];
    for (const name of regionTilesets()) {
      const v2 = namedTilesetJsonPathV2(name);
      const rel = listed(v2) ? v2 : namedTilesetJsonPath(name);
      if (!exists(rel)) continue;
      const jsonKey = `json_${namedTilesetTextureKey(name)}`;
      this.load.json(jsonKey, `${ASSETS.URL}/${rel}`);
      this.pendingRegionTiles.push({ name, jsonKey, dir: dirOf(rel) });
    }
    this.audioManifestQueued = exists(audioManifestRel());
    if (this.audioManifestQueued) this.load.json(AUDIO_MANIFEST_KEY, `${ASSETS.URL}/${audioManifestRel()}`);
  }

  /** 음향 매니페스트 entries 중 매니페스트(파일 목록)에 있는 WAV 만 로드 큐에 넣는다 */
  private queueAudio(): { manifest: AudioManifest; keys: string[] } | null {
    if (!this.audioManifestQueued) return null;
    const json = this.cache.json.get(AUDIO_MANIFEST_KEY) as unknown;
    if (!isAudioManifest(json)) return null;
    const exists = (rel: string) => this.manifest === null || this.manifest.has(rel);
    const keys: string[] = [];
    for (const entry of json.entries) {
      if (!entry || typeof entry.id !== 'string' || typeof entry.file !== 'string') continue;
      const rel = audioFileRel(entry);
      if (!exists(rel)) continue;
      keys.push(entry.id);
      if (!this.cache.audio.exists(entry.id)) this.load.audio(entry.id, `${ASSETS.URL}/${rel}`);
    }
    return { manifest: json, keys };
  }

  /** JSON 이 읽힌 것만 PNG 로드 큐에 넣고, 끝나면 애니·타일셋 등록 후 라우팅 */
  private queueImages(): void {
    const sheets: SheetDef[] = [];
    for (const p of this.pendingSheets) {
      const raw = this.cache.json.get(p.jsonKey) as SheetJson | undefined;
      if (!raw || !raw.image || !(raw.frameWidth > 0) || !(raw.frameHeight > 0) || !(raw.frames > 0)) continue;
      // 구조물 시트(계약 §5)는 fps·loop·directions·pivot 을 생략할 수 있다. 50라운드: 메모 길이는 월드 단위로 (pixelScale)
      const json = sheetToWorldUnits(p.req.category === 'structures' ? normalizeStructureSheet(raw) : raw);
      const textureKey = sheetTextureKey(p.req.name, p.req.action);
      const imageUrl = `${ASSETS.URL}/${p.dir}${json.image}`;
      // 동작 이름은 요청 기준 (이펙트 시트의 JSON action 은 파일 이름과 같아 내부 동작 'fx' 로 통일)
      sheets.push({ ...json, action: p.req.action, category: p.req.category, name: p.req.name, textureKey, imageUrl });
      if (!this.textures.exists(textureKey)) {
        this.load.spritesheet(textureKey, imageUrl, { frameWidth: json.frameWidth, frameHeight: json.frameHeight });
      }
    }
    const tiles: { floor: number; json: TilesetJson; key: string }[] = [];
    for (const p of this.pendingTiles) {
      const json = this.cache.json.get(p.jsonKey) as TilesetJson | undefined;
      if (!json || !json.image || !json.tiles) continue;
      const key = tilesetTextureKey(p.floor);
      tiles.push({ floor: p.floor, json, key });
      if (!this.textures.exists(key)) this.load.image(key, `${ASSETS.URL}/${ASSETS.TILES_DIR}/${json.image}`);
    }
    const regionTiles: { name: string; json: TilesetJson; key: string }[] = [];
    for (const p of this.pendingRegionTiles) {
      const json = this.cache.json.get(p.jsonKey) as TilesetJson | undefined;
      if (!json || !json.image || !json.tiles) continue;
      const key = namedTilesetTextureKey(p.name);
      regionTiles.push({ name: p.name, json, key });
      if (!this.textures.exists(key)) this.load.image(key, `${ASSETS.URL}/${p.dir}${json.image}`);
    }
    const audioQueue = this.queueAudio();
    this.load.once(Phaser.Loader.Events.COMPLETE, () => {
      for (const def of sheets) if (this.textures.exists(def.textureKey)) spriteLibrary.register(def);
      // 자기 시트가 없는 보스는 폴백 시트를 쓴다 (결정 로그 J: 2~7층 보스 = stage1 시트 + 층 램프 스왑)
      for (const id of Object.keys(BOSSES)) {
        if (!spriteLibrary.has(id) && spriteLibrary.has(SPRITES.BOSS_FALLBACK_SHEET))
          spriteLibrary.alias(id, SPRITES.BOSS_FALLBACK_SHEET);
      }
      spriteLibrary.createBaseAnims(this);
      for (const t of tiles) if (this.textures.exists(t.key)) tileSkins.set(t.floor, new TileSkin(t.key, t.json, true));
      for (const t of regionTiles)
        if (this.textures.exists(t.key)) regionSkins.set(t.name, new TileSkin(t.key, t.json, true));
      if (audioQueue) {
        audio.register(
          audioQueue.manifest,
          audioQueue.keys.filter((k) => this.cache.audio.exists(k)),
        );
      }
      const [key, data] = this.route();
      if (key === UI_SCENES.TITLE || key === SCENES.SETUP) audio.setState('title');
      this.scene.start(key, data);
    });
    this.load.start();
  }

  /** 세이브가 있으면 이어하기, ?weapon= 이면 선택 생략, 아니면 개성 선택 씬 */
  private route(): [string, object?] {
    const params = typeof location !== 'undefined' ? new URLSearchParams(location.search) : new URLSearchParams();
    if (params.has('resetmeta')) metaStore.clear();
    const forcedWeapon = params.get('weapon');
    // 49라운드: ?lab 이면 무기 시험장으로 바로 (검증용, ?weapon= 으로 무기)
    if (params.has('lab'))
      return [SCENES.WEAPON_LAB, forcedWeapon && WEAPONS[forcedWeapon] ? { labWeapon: forcedWeapon } : {}];
    const weapon = forcedWeapon && WEAPONS[forcedWeapon] ? forcedWeapon : undefined;
    // 50라운드: ?slice=<지역> 이면 새 런으로 그 지역 전투 노드에 바로 (외곽 거리 시범 확인용)
    const slice = params.get('slice');
    if (slice) return [SCENES.GAME, { mode: 'new', weapon, slice }];
    if (weapon) return [SCENES.GAME, { mode: 'new', weapon }];
    const skipTitle = params.has('new') || params.has('seed') || params.has('notitle');
    if (!skipTitle && this.scene.manager.keys[UI_SCENES.TITLE]) return [UI_SCENES.TITLE];
    const hasSave = !params.has('new') && !params.has('seed') && new SaveSlot(browserStorage()).read() !== null;
    if (hasSave) return [SCENES.GAME];
    return [SCENES.SETUP];
  }

  /** 플레이스홀더 타일 텍스처 (아트 타일셋이 없는 층에서 사용) */
  private buildTileTexture(): void {
    if (this.textures.exists(TEXTURES.TILES)) return;
    const colors: Record<TileId, string> = {
      [TileId.Void]: COLORS.TILE_VOID,
      [TileId.Floor]: COLORS.TILE_FLOOR,
      [TileId.Wall]: COLORS.TILE_WALL,
      [TileId.DoorOpen]: COLORS.DOOR_OPEN,
      [TileId.DoorClosed]: COLORS.DOOR_CLOSED,
      [TileId.DoorLocked]: COLORS.DOOR_LOCKED,
      [TileId.Corridor]: COLORS.TILE_CORRIDOR,
      [TileId.Exit]: COLORS.EXIT,
      [TileId.Shop]: COLORS.SHOP,
    };
    const count = Object.keys(colors).length;
    const canvas = this.textures.createCanvas(TEXTURES.TILES, TILE * count, TILE)!;
    const ctx = canvas.context;
    for (let i = 0; i < count; i++) {
      ctx.fillStyle = colors[i as TileId];
      ctx.fillRect(i * TILE, 0, TILE, TILE);
      // 바닥·복도는 격자 느낌을 위해 가장자리 1px 어둡게
      if (i === TileId.Floor || i === TileId.Corridor) {
        ctx.fillStyle = 'rgba(0,0,0,0.25)';
        ctx.fillRect(i * TILE, 0, TILE, 1);
        ctx.fillRect(i * TILE, 0, 1, TILE);
      }
    }
    canvas.refresh();
  }
}
