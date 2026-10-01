import Phaser from 'phaser';
import { ASSETS, COLORS, SCENES, TEXTURES, TILE } from '../core/Constants';
import { TileId } from '../systems/mapgen';
import { SaveSlot, browserStorage } from '../systems/save';
import { BOSSES, ENEMIES, RUN, WEAPONS } from '../data';
import { metaStore } from '../systems/meta';
import { spriteLibrary } from '../systems/sprites';
import {
  fxSheetIds,
  sheetJsonPath,
  sheetTextureKey,
  wantedSheets,
  type SheetDef,
  type SheetJson,
} from '../systems/spriteDefs';
import { TileSkin, tileSkins, tilesetJsonPath, tilesetTextureKey, type TilesetJson } from '../world/tileskin';
import { UI_SCENES } from '../ui';

interface Manifest {
  files: string[];
}

/**
 * 아트 산출물 로드 (계약 contracts/art-assets.md).
 * 1) manifest.json → 존재하는 파일만 2) 시트·타일셋 JSON → 3) PNG(spritesheet/image) → 애니 등록.
 * 없는 파일은 조용히 건너뛰고(404 는 loaderror 로 무시) 플레이스홀더 텍스처로 폴백한다.
 */
export class Preloader extends Phaser.Scene {
  private manifest: Set<string> | null = null;
  private pendingSheets: { req: ReturnType<typeof wantedSheets>[number]; jsonKey: string; dir: string }[] = [];
  private pendingTiles: { floor: number; jsonKey: string }[] = [];

  constructor() {
    super(SCENES.PRELOADER);
  }

  preload(): void {
    // 로드 실패(404 등)는 오류가 아니라 "아트 미제공" 이다
    this.load.on(Phaser.Loader.Events.FILE_LOAD_ERROR, () => {});
    this.load.json(TEXTURES.MANIFEST, `${ASSETS.URL}/${ASSETS.MANIFEST}`);
  }

  create(): void {
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
    this.pendingSheets = [];
    for (const req of wantedSheets(
      Object.keys(ENEMIES),
      Object.keys(BOSSES),
      Object.keys(WEAPONS),
      fxSheetIds(WEAPONS),
    )) {
      const rel = sheetJsonPath(req);
      if (!exists(rel)) continue;
      const jsonKey = `json_${sheetTextureKey(req.name, req.action)}`;
      this.load.json(jsonKey, `${ASSETS.URL}/${rel}`);
      this.pendingSheets.push({ req, jsonKey, dir: rel.slice(0, rel.lastIndexOf('/') + 1) });
    }
    this.pendingTiles = [];
    for (let floor = 1; floor <= RUN.order.length; floor++) {
      const rel = tilesetJsonPath(floor);
      if (!exists(rel)) continue;
      const jsonKey = `json_${tilesetTextureKey(floor)}`;
      this.load.json(jsonKey, `${ASSETS.URL}/${rel}`);
      this.pendingTiles.push({ floor, jsonKey });
    }
  }

  /** JSON 이 읽힌 것만 PNG 로드 큐에 넣고, 끝나면 애니·타일셋 등록 후 라우팅 */
  private queueImages(): void {
    const sheets: SheetDef[] = [];
    for (const p of this.pendingSheets) {
      const json = this.cache.json.get(p.jsonKey) as SheetJson | undefined;
      if (!json || !json.image || !(json.frameWidth > 0) || !(json.frameHeight > 0) || !(json.frames > 0)) continue;
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
    this.load.once(Phaser.Loader.Events.COMPLETE, () => {
      for (const def of sheets) if (this.textures.exists(def.textureKey)) spriteLibrary.register(def);
      spriteLibrary.createBaseAnims(this);
      for (const t of tiles) if (this.textures.exists(t.key)) tileSkins.set(t.floor, new TileSkin(t.key, t.json, true));
      this.scene.start(...this.route());
    });
    this.load.start();
  }

  /** 세이브가 있으면 이어하기, ?weapon= 이면 선택 생략, 아니면 개성 선택 씬 */
  private route(): [string, object?] {
    const params = typeof location !== 'undefined' ? new URLSearchParams(location.search) : new URLSearchParams();
    if (params.has('resetmeta')) metaStore.clear();
    const forcedWeapon = params.get('weapon');
    if (forcedWeapon && WEAPONS[forcedWeapon]) return [SCENES.GAME, { mode: 'new', weapon: forcedWeapon }];
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
