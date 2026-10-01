import Phaser from 'phaser';
import { COLORS, SCENES, TEXTURES, TILE } from '../core/Constants';
import { TileId } from '../systems/mapgen';
import { SaveSlot, browserStorage } from '../systems/save';
import { WEAPONS } from '../data';
import { metaStore } from '../systems/meta';
import { UI_SCENES } from '../ui';

/** 플레이스홀더 타일 텍스처를 코드로 만든다. 아트 파트 타일셋이 계약으로 들어오면 여기서 로드로 교체. */
export class Preloader extends Phaser.Scene {
  constructor() {
    super(SCENES.PRELOADER);
  }

  create(): void {
    this.buildTileTexture();
    this.scene.start(...this.route());
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
