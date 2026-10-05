import Phaser from 'phaser';
import { ASSETS, COLORS, FEEL, SCENES, TEXTURES, TILE } from '../core/Constants';
import { TileId } from '../systems/mapgen';
import { SaveSlot, browserStorage } from '../systems/save';
import { RUN, WEAPONS } from '../data';
import { floorLoaded } from '../data/scope';
import { metaStore } from '../systems/meta';
import { audio } from '../systems/audio/audio';
import { ensureFont } from '../systems/fonts';
import { audioFileRels, audioManifestRel, isAudioManifest, type AudioManifest } from '../systems/audio/audioDefs';
import { isLazyBgm } from '../systems/audio/audioMix';
import type { SheetDef } from '../systems/sprites/spriteDefs';
import {
  queueSheetImage,
  queueSheetJsons,
  registerSheets,
  setAssetManifest,
  type PendingSheet,
} from '../systems/sprites/sheetLoader';
import { bootSheetRequests } from '../systems/sprites/sheetSets';
import {
  TileSkin,
  namedTilesetJsonPath,
  namedTilesetJsonPathV2,
  namedTilesetTextureKey,
  propSheetJsonPath,
  propSheetName,
  propSkins,
  regionSkins,
  tileSkins,
  tilesetJsonPath,
  tilesetTextureKey,
  type TilesetJson,
} from '../world/tileskin';
import { regionIds, regionTilesets } from '../systems/route';
import { borderDefs, borderJsonRel, parseBorder } from '../world/border';
import { UI_SCENES } from '../ui';
import { bossQuery } from '../debug/bossQuery';
import { urlParams } from './game/shared';

interface Manifest {
  files: string[];
}

/** 음향 매니페스트 JSON 캐시 키 */
const AUDIO_MANIFEST_KEY = 'audio_manifest';

/**
 * 아트·음향 산출물 로드 (계약 contracts/art-assets.md, 음향은 assets/audio/manifest.json 계약 초안).
 * 1) manifest.json → 존재하는 파일만 2) 시트·타일셋·음향 매니페스트 JSON → 3) 그림·소리(OGG/M4A) → 애니 등록·오디오 등록.
 * 57라운드 A2: 시트는 부팅 묶음(무기와 무관한 것)만 — 무기 시트는 런 무기가 정해진 씬(Game·WeaponLab)의 preload 가 그 무기만
 * 읽는다 (`sheetLoader.preloadWeaponSheets`).
 * 없는 파일은 조용히 건너뛰고(404 는 loaderror 로 무시) 플레이스홀더 텍스처로 폴백한다.
 */
export class Preloader extends Phaser.Scene {
  private manifest: Set<string> | null = null;
  private pendingSheets: PendingSheet[] = [];
  private pendingTiles: { floor: number; jsonKey: string }[] = [];
  /** 49라운드 art §7.3: 지역 타일셋 (tiles/stage1_<region>.json, 50라운드: tiles/v2/ 가 있으면 먼저) */
  private pendingRegionTiles: { name: string; jsonKey: string; dir: string; props?: boolean }[] = [];
  private audioManifestQueued = false;
  /** 53라운드 Q6: 외벽 테두리 border.json 이 있는 지역 (그림은 그 지역 노드에 들어갈 때 지연 로드 — BorderView) */
  private pendingBorders: { region: string; jsonKey: string }[] = [];

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
    setAssetManifest(this.manifest);
    this.queueJsons();
    this.load.once(Phaser.Loader.Events.COMPLETE, () => this.queueImages());
    this.load.start();
  }

  /** 매니페스트에 있는(또는 매니페스트가 없으면 전부) 시트·타일셋 JSON 을 큐에 넣는다 */
  private queueJsons(): void {
    const exists = (rel: string) => this.manifest === null || this.manifest.has(rel);
    // 50·52라운드 새 도트(`v3/`·`v2/`)는 매니페스트에 있을 때만 (매니페스트가 없으면 기존 경로). v3 → v2 → 기존, 동작 단위
    const listed = (rel: string) => this.manifest !== null && this.manifest.has(rel);
    const dirOf = (rel: string) => rel.slice(0, rel.lastIndexOf('/') + 1);
    this.pendingSheets = queueSheetJsons(this, bootSheetRequests());
    this.pendingTiles = [];
    // 61라운드 P9: 층 타일셋은 로드 범위(stages.json run.loadFloors) 안 층만 — 범위 밖 층은 플레이스홀더 타일
    for (let floor = 1; floor <= RUN.order.length; floor++) {
      if (!floorLoaded(floor)) continue;
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
    // 53라운드 v3 바닥 소품 시트 (`tiles/v3/<지역 타일셋>_props.json`) — 매니페스트에 있을 때만
    for (const name of regionTilesets()) {
      const rel = propSheetJsonPath(name);
      if (!listed(rel)) continue;
      const jsonKey = `json_${namedTilesetTextureKey(propSheetName(name))}`;
      this.load.json(jsonKey, `${ASSETS.URL}/${rel}`);
      this.pendingRegionTiles.push({ name, jsonKey, dir: dirOf(rel), props: true });
    }
    this.pendingBorders = [];
    for (const region of regionIds()) {
      const rel = borderJsonRel(region);
      if (!listed(rel)) continue;
      const jsonKey = `json_border_${region}`;
      this.load.json(jsonKey, `${ASSETS.URL}/${rel}`);
      this.pendingBorders.push({ region, jsonKey });
    }
    this.audioManifestQueued = exists(audioManifestRel());
    if (this.audioManifestQueued) this.load.json(AUDIO_MANIFEST_KEY, `${ASSETS.URL}/${audioManifestRel()}`);
  }

  /**
   * 음향 매니페스트 entries 중 매니페스트(파일 목록)에 있는 형식만 로드 큐에 넣는다 (57라운드 Q38: `files` ogg → m4a 순 —
   * Phaser 가 재생 가능한 첫 형식을 고른다)
   */
  private queueAudio(): { manifest: AudioManifest; keys: string[] } | null {
    if (!this.audioManifestQueued) return null;
    const json = this.cache.json.get(AUDIO_MANIFEST_KEY) as unknown;
    if (!isAudioManifest(json)) return null;
    const exists = (rel: string) => this.manifest === null || this.manifest.has(rel);
    const keys: string[] = [];
    // 61라운드 계약 sound §9: 층 전용 BGM(use.floor)은 WebAudio 면 지연 로드 (audio.registerLazy → 층·노드 진입 때)
    const lazyOk = this.sound instanceof Phaser.Sound.WebAudioSoundManager;
    const lazy = new Map<string, string[]>();
    for (const entry of json.entries) {
      if (!entry || typeof entry.id !== 'string' || typeof entry.file !== 'string') continue;
      const rels = audioFileRels(entry).filter(exists);
      if (rels.length === 0) continue;
      // 61라운드 단계 2 첫 로딩 줄이기: 로드 범위 밖 층 전용 BGM(2~8층 floor_low·mid·high)은 부팅에서 뺀다 (범위를 넓히면 다시 읽힌다)
      if (outOfScopeBgm(entry)) continue;
      if (lazyOk && isLazyBgm(entry)) {
        lazy.set(
          entry.id,
          rels.map((rel) => `${ASSETS.URL}/${rel}`),
        );
        continue;
      }
      keys.push(entry.id);
      if (!this.cache.audio.exists(entry.id))
        this.load.audio(
          entry.id,
          rels.map((rel) => `${ASSETS.URL}/${rel}`),
        );
    }
    audio.registerLazy(lazy);
    return { manifest: json, keys };
  }

  /** JSON 이 읽힌 것만 PNG 로드 큐에 넣고, 끝나면 애니·타일셋 등록 후 라우팅 */
  private queueImages(): void {
    const sheets: SheetDef[] = [];
    for (const p of this.pendingSheets) {
      const def = queueSheetImage(this, p);
      if (def) sheets.push(def);
    }
    const tiles: { floor: number; json: TilesetJson; key: string }[] = [];
    for (const p of this.pendingTiles) {
      const json = this.cache.json.get(p.jsonKey) as TilesetJson | undefined;
      if (!json || !json.image || !json.tiles) continue;
      const key = tilesetTextureKey(p.floor);
      tiles.push({ floor: p.floor, json, key });
      if (!this.textures.exists(key)) this.load.image(key, `${ASSETS.URL}/${ASSETS.TILES_DIR}/${json.image}`);
    }
    const regionTiles: { name: string; json: TilesetJson; key: string; props?: boolean }[] = [];
    for (const p of this.pendingRegionTiles) {
      const json = this.cache.json.get(p.jsonKey) as TilesetJson | undefined;
      // 소품 시트는 tiles 가 없어도 된다 (props·bigProps 만)
      if (!json || !json.image || (!json.tiles && !p.props)) continue;
      const key = namedTilesetTextureKey(p.props ? propSheetName(p.name) : p.name);
      regionTiles.push({ name: p.name, json, key, props: p.props });
      if (!this.textures.exists(key)) this.load.image(key, `${ASSETS.URL}/${p.dir}${json.image}`);
    }
    borderDefs.clear();
    for (const b of this.pendingBorders) {
      const def = parseBorder(this.cache.json.get(b.jsonKey), b.region);
      if (def) borderDefs.set(b.region, def);
    }
    const audioQueue = this.queueAudio();
    this.load.once(Phaser.Loader.Events.COMPLETE, () => {
      registerSheets(this, sheets);
      // 61라운드 단계 2: 보스 시트는 보스 노드에서 읽는다 (sheetLoader.preloadBossSheets — 폴백 별칭도 그때)
      for (const t of tiles) if (this.textures.exists(t.key)) tileSkins.set(t.floor, new TileSkin(t.key, t.json, true));
      for (const t of regionTiles)
        if (this.textures.exists(t.key))
          (t.props ? propSkins : regionSkins).set(t.name, new TileSkin(t.key, t.json, true));
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
    const params = urlParams();
    if (params.has('resetmeta')) metaStore.clear();
    const forcedWeapon = params.get('weapon');
    // 49라운드: ?lab 이면 무기 시험장으로 바로 (검증용, ?weapon= 으로 무기)
    if (params.has('lab'))
      return [SCENES.WEAPON_LAB, forcedWeapon && WEAPONS[forcedWeapon] ? { labWeapon: forcedWeapon } : {}];
    const weapon = forcedWeapon && WEAPONS[forcedWeapon] ? forcedWeapon : undefined;
    // 50라운드: ?slice=<지역> 이면 새 런으로 그 지역 전투 노드에 바로 (외곽 거리 시범 확인용)
    const slice = params.get('slice');
    if (slice) return [SCENES.GAME, { mode: 'new', weapon, slice }];
    // 54라운드: ?boss · ?bossPhase=n · ?bossPattern=a,b → 새 런으로 1층(또는 ?floor 없이 현재 층) 보스 노드에 바로
    if (bossQuery().jump) return [SCENES.GAME, { mode: 'new', weapon, bossJump: true }];
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

/** 층 목록(floors)이 있는 BGM 인데 그 층이 전부 로드 범위(stages.json run.loadFloors) 밖이면 true */
function outOfScopeBgm(e: { kind?: string; floors?: number[] }): boolean {
  return e.kind === 'bgm' && Array.isArray(e.floors) && e.floors.length > 0 && !e.floors.some((f) => floorLoaded(f));
}
