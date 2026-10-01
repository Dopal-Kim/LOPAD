import Phaser from 'phaser';
import { COLORS, SCENES, TEXTURES, TILE } from '../core/Constants';
import { TileId } from '../systems/mapgen';

/** 플레이스홀더 타일 텍스처를 코드로 만든다. 아트 파트 타일셋이 계약으로 들어오면 여기서 로드로 교체. */
export class Preloader extends Phaser.Scene {
  constructor() {
    super(SCENES.PRELOADER);
  }

  create(): void {
    this.buildTileTexture();
    this.scene.start(SCENES.GAME);
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
