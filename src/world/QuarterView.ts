/**
 * 50라운드 쿼터뷰 그림 (결정 round-50 Q1, 계약 art §9): 바닥은 정면 격자 그대로, 벽은 앞면을 세워(wallHeightTiles 칸)
 * 그리고 윗면을 그 위에 얹는다. 출입·충돌은 바닥 격자(TileWorld 의 보이지 않는 충돌 레이어)가 맡고, 여기는 그림만.
 *
 * - 바닥 레이어: 타일셋 원래 크기(32px)의 타일맵을 월드 배율(TILE/32)로 줄여 깐다. 벽 칸 자리는 빈 칸(원경)으로 — 벽 그림이 덮는다
 * - 벽 (아트 JSON walls.stacking 규칙): 남쪽이 바닥인 벽(앞면이 보이는 북쪽 벽) = 그 칸 아랫단 → 위 칸 윗단(wallHeightTiles-1 칸)
 *   → 그 위 처마(topAboveFront). 그 밖의 벽(서·동·남 경계·두꺼운 벽 안쪽) = 앞면 없이 제자리에 윗면 — 경계 쪽은 가장자리 타일
 *   (left·right·bottom·corner_*), 나머지 top. 깊이 = 벽 칸 아래변 y 로 Y 정렬 → 앞면 아래(남쪽) 캐릭터는 앞, 뒤 캐릭터는 가려진다.
 *   가려진 주인공 둘레 벽 그림은 반투명(QUARTER.OCCLUDE_ALPHA)
 * - 바닥 그늘(floorShadows): 북쪽 벽 발치·서·동 경계 옆 바닥에 반투명 겹침
 * - 소품: 타일셋 props 를 같은 배율로 (JSON light → 광원, offset = 칸 안 좌표) · 앞면 창·문(tileLights) 광원
 */
import Phaser from 'phaser';
import { DEPTH, QUARTER, STRUCTURE_FX, TILE, entityDepth } from '../core/Constants';
import type { BigPropPlacement } from './bigProps';
import { TileId, type FloorLayout } from '../systems/mapgen';
import { lightRegistryOf } from '../systems/lighting/lightRegistry';
import { isOpenId, lightOffsetOf, pickVariant, wallKind, type PropPlacement, type TileSkin } from './tileskin';
import type { LightSource } from '../systems/lighting/lightRegistry';

interface WallImage {
  img: Phaser.GameObjects.Image;
  /** 그림의 월드 사각형 (가림 판정) */
  left: number;
  right: number;
  top: number;
  bottom: number;
}

export interface QuarterViewSource {
  /** 지금 칸의 게임 타일 ID (충돌 레이어 기준 — 출구·저장고 등 바뀐 칸 포함) */
  idAt(tx: number, ty: number): TileId;
  /** 바닥 칸에 놓을 시트 인덱스 (방 종류별 바닥·변형) */
  groundIndex(tx: number, ty: number): number;
}

export class QuarterView {
  private readonly map: Phaser.Tilemaps.Tilemap;
  private readonly ground: Phaser.Tilemaps.TilemapLayer;
  private readonly propsLayer: Phaser.Tilemaps.TilemapLayer | null = null;
  /** 바닥 그늘 겹침 레이어 (floorShadows 가 있을 때) */
  private readonly shadeLayer: Phaser.Tilemaps.TilemapLayer | null = null;
  /** 큰 소품 그림·가림 판정·광원 (벽을 다시 만들어도 그대로) */
  private bigImages: Phaser.GameObjects.Image[] = [];
  private readonly bigByColumn = new Map<number, WallImage[]>();
  private wallLightsFixed: LightSource[] = [];
  private bigPlaced = 0;
  /** 앞면 창·문 광원 (벽을 다시 만들면 다시 단다) */
  private wallLights: LightSource[] = [];
  private walls: WallImage[] = [];
  /** 열(타일 x) → 그 열의 벽 그림 (가림 판정은 캐릭터 둘레 열만 본다) */
  private byColumn = new Map<number, WallImage[]>();
  private faded: WallImage[] = [];
  private readonly scale: number;

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly layout: FloorLayout,
    private readonly skin: TileSkin,
    private readonly src: QuarterViewSource,
    props: readonly PropPlacement[] = [],
  ) {
    const px = skin.tilePx;
    this.scale = TILE / px;
    ensureTileFrames(scene, skin.textureKey, px);
    const data = layout.tiles.map((row, y) => row.map((_, x) => this.groundOf(x, y)));
    this.map = scene.make.tilemap({ data, tileWidth: px, tileHeight: px });
    const tileset = this.map.addTilesetImage(skin.textureKey, skin.textureKey, px, px, 0, 0)!;
    this.ground = this.map.createLayer(0, tileset, 0, 0)!;
    this.ground.setScale(this.scale).setDepth(DEPTH.TILES);
    if (skin.quarter?.shadows) {
      const shade = this.map.createBlankLayer('qv_shade', tileset, 0, 0, layout.widthTiles, layout.heightTiles)!;
      shade.setScale(this.scale).setDepth(DEPTH.TILES + DEPTH.LIGHT_LAYER_STEP);
      this.shadeLayer = shade;
    }
    if (props.length > 0) {
      const layer = this.map.createBlankLayer('qv_props', tileset, 0, 0, layout.widthTiles, layout.heightTiles)!;
      layer.setScale(this.scale).setDepth(DEPTH.PROPS);
      for (const p of props) layer.putTileAt(p.index, p.x, p.y);
      this.propsLayer = layer;
      this.registerPropLights(props);
    }
    this.rebuildWalls();
  }

  /** 바닥 레이어 인덱스: 벽 칸은 빈 칸(원경) — 벽 그림이 덮는다. 북쪽 벽 틈은 골목 입구 */
  private groundOf(x: number, y: number): number {
    const id = this.src.idAt(x, y);
    if (id === TileId.Wall) return this.skin.voidIndex;
    if (id === TileId.Void && this.isAlley(x, y)) return this.skin.alleyIndex ?? this.skin.voidIndex;
    return this.src.groundIndex(x, y);
  }

  /**
   * 52라운드 Q11: 북쪽 벽 틈 = 집 사이 골목 입구. 바닥 바로 북쪽의 빈 칸, 그리고 그 위로 앞면 높이만큼 이어진 빈 칸
   * (양옆 집 앞면과 같은 높이로 어두운 골목이 보인다)
   */
  private isAlley(x: number, y: number): boolean {
    const H = this.skin.quarter?.heightTiles ?? 0;
    for (let k = 0; k <= H; k++) {
      const id = this.src.idAt(x, y + k);
      if (id !== TileId.Void) return k > 0 && isOpenId(id);
    }
    return false;
  }

  /** 칸 하나가 바뀜 (출구·상점·문) */
  refreshGround(tx: number, ty: number): void {
    this.ground.putTileAt(this.groundOf(tx, ty), tx, ty);
  }

  private isWall(x: number, y: number): boolean {
    return this.src.idAt(x, y) === TileId.Wall;
  }

  private isOpen = (x: number, y: number): boolean => isOpenId(this.src.idAt(x, y));

  /** 벽 그림 다시 만들기 (저장고 벽 등 벽 칸이 바뀌면) — 바닥 그늘·창 광원도 함께 */
  rebuildWalls(): void {
    for (const w of this.walls) w.img.destroy();
    this.walls = [];
    this.byColumn = new Map();
    this.faded = [];
    const reg = lightRegistryOf(this.scene);
    for (const l of this.wallLights) reg.remove(l);
    this.wallLights = [];
    const Q = this.skin.quarter!;
    const H = Q.heightTiles;
    const pick = (list: readonly number[], x: number, y: number) => list[pickVariant(x, y, list.length, TileId.Wall)];
    const { widthTiles: W, heightTiles: Ht } = this.layout;
    const islands = Q.stone ? this.wallIslands() : new Set<string>();
    for (let y = 0; y < Ht; y++)
      for (let x = 0; x < W; x++) {
        if (!this.isWall(x, y)) continue;
        // 바닥 칸도 다시 (벽이 생기거나 사라진 칸)
        this.refreshGround(x, y);
        const depth = entityDepth((y + 1) * TILE);
        const stone = Q.stone && islands.has(`${x},${y}`) ? Q.stone : null;
        if (stone) {
          // 엄폐 담(경계에 닿지 않는 벽 섬) = 돌담 세트: 앞면 아랫단 → 윗단 → 윗면, 앞면 없는 칸은 윗면
          if (this.isOpen(x, y + 1)) {
            this.place(x, y, pick(stone.lower, x, y), depth);
            for (let k = 1; k < H; k++) this.place(x, y - k, pick(stone.upper, x, y - k), depth);
            this.place(x, y - H, stone.top, depth);
          } else this.place(x, y, stone.top, depth);
        } else if (this.isOpen(x, y + 1)) {
          // 앞면이 보이는 벽: 아랫단(제자리) → 윗단 → 처마
          const lower = pick(Q.frontLower, x, y);
          this.place(x, y, lower, depth);
          this.addTileLight(lower, x, y);
          for (let k = 1; k < H; k++) this.place(x, y - k, pick(Q.frontUpper, x, y - k), depth);
          this.place(x, y - H, Q.topAboveFront, depth);
        } else {
          // 앞면 없는 벽: 제자리 윗면 (경계 가장자리)
          const kind = wallKind(this.isOpen, x, y);
          this.place(x, y, (kind && Q.edges[kind]) ?? Q.top, depth);
        }
      }
    this.rebuildShade();
  }

  /** 경계(빈 칸 = 바깥)에 닿지 않는 벽 덩어리 칸 (`"x,y"`) — 전투장 안 엄폐 담 */
  private wallIslands(): Set<string> {
    const { widthTiles: W, heightTiles: Ht } = this.layout;
    const seen = new Set<string>();
    const out = new Set<string>();
    for (let y = 0; y < Ht; y++)
      for (let x = 0; x < W; x++) {
        const key = `${x},${y}`;
        if (seen.has(key) || !this.isWall(x, y)) continue;
        const comp: string[] = [];
        let touchesVoid = false;
        const stack = [[x, y]];
        seen.add(key);
        while (stack.length > 0) {
          const [cx, cy] = stack.pop()!;
          comp.push(`${cx},${cy}`);
          for (let oy = -1; oy <= 1; oy++)
            for (let ox = -1; ox <= 1; ox++) {
              const nx = cx + ox;
              const ny = cy + oy;
              const id = this.src.idAt(nx, ny);
              if (id === TileId.Void) touchesVoid = true;
              const nk = `${nx},${ny}`;
              if (Math.abs(ox) + Math.abs(oy) === 1 && id === TileId.Wall && !seen.has(nk)) {
                seen.add(nk);
                stack.push([nx, ny]);
              }
            }
        }
        if (!touchesVoid) for (const c of comp) out.add(c);
      }
    return out;
  }

  /** 바닥 그늘: 북쪽이 벽이면 n, 서쪽 경계면 w, 동쪽 경계면 e (북+서 = nw, 북+동 = ne) */
  private rebuildShade(): void {
    const layer = this.shadeLayer;
    const S = this.skin.quarter?.shadows;
    if (!layer || !S) return;
    const { widthTiles: W, heightTiles: Ht } = this.layout;
    for (let y = 0; y < Ht; y++)
      for (let x = 0; x < W; x++) {
        layer.removeTileAt(x, y);
        if (!this.isOpen(x, y)) continue;
        const n = this.isWall(x, y - 1) || (this.src.idAt(x, y - 1) === TileId.Void && this.isAlley(x, y - 1));
        const w = this.isWall(x - 1, y);
        const e = this.isWall(x + 1, y);
        const idx = n && w ? (S.nw ?? S.n) : n && e ? (S.ne ?? S.n) : n ? S.n : w ? S.w : e ? S.e : undefined;
        if (idx !== undefined) layer.putTileAt(idx, x, y);
      }
  }

  /** 앞면 타일 광원 (JSON tileLights: 창·문틈) — 반경·offset = 시트 도트 px */
  private addTileLight(index: number, tx: number, ty: number): void {
    const l = this.skin.def.tileLights?.[String(index)];
    if (!l) return;
    const k = this.scale;
    const o = lightOffsetOf(l.offset) ?? { x: this.skin.tilePx / 2, y: this.skin.tilePx / 2 };
    this.wallLights.push(
      lightRegistryOf(this.scene).add(
        { ...l, radius: l.radius * k },
        { x: tx * TILE + o.x * k, y: ty * TILE + o.y * k },
      ),
    );
  }

  private place(tx: number, ty: number, frame: number, depth: number): void {
    const img = this.scene.add
      .image(tx * TILE + TILE / 2, (ty + 1) * TILE, this.skin.textureKey, frame)
      .setOrigin(0.5, 1)
      .setScale(this.scale)
      .setDepth(depth);
    const w: WallImage = { img, left: tx * TILE, right: (tx + 1) * TILE, top: ty * TILE, bottom: (ty + 1) * TILE };
    this.walls.push(w);
    const col = this.byColumn.get(tx);
    if (col) col.push(w);
    else this.byColumn.set(tx, [w]);
  }

  /**
   * 가려짐 비침: 대상(발 피벗 x,y · 그림 폭·높이 · 깊이)보다 앞(깊이가 큰) 벽 그림이 대상 그림과 겹치면 반투명.
   * 매 프레임 (대상 둘레 열만 본다)
   */
  updateOcclusion(targets: readonly { x: number; y: number; w: number; h: number; depth: number }[]): void {
    for (const w of this.faded) w.img.setAlpha(1);
    this.faded = [];
    const pad = QUARTER.OCCLUDE_PAD_PX;
    for (const t of targets) {
      const left = t.x - t.w / 2 - pad;
      const right = t.x + t.w / 2 + pad;
      const top = t.y - t.h - pad;
      const bottom = t.y + pad;
      for (let cx = Math.floor(left / TILE); cx <= Math.floor(right / TILE); cx++)
        for (const w of [...(this.byColumn.get(cx) ?? []), ...(this.bigByColumn.get(cx) ?? [])]) {
          if (w.img.depth <= t.depth) continue;
          if (w.right <= left || w.left >= right || w.bottom <= top || w.top >= bottom) continue;
          w.img.setAlpha(QUARTER.OCCLUDE_ALPHA);
          this.faded.push(w);
        }
    }
  }

  /**
   * 52라운드 Q11 큰 소품 그림: 시트 rect 를 프레임으로, 피벗 = 발자국 아래 가운데. occludeAbove 가 있으면 그 높이 아래(받침)는
   * 바닥 깊이, 위는 Y 정렬(가려진 주인공 둘레면 반투명) · JSON light → 광원 (offset = rect 안 도트 좌표)
   */
  addBigProps(list: readonly BigPropPlacement[]): void {
    const defs = new Map(this.skin.bigProps.map((b) => [b.name, b]));
    const tex = this.scene.textures.get(this.skin.textureKey);
    const k = this.scale;
    const reg = lightRegistryOf(this.scene);
    for (const p of list) {
      const d = defs.get(p.name);
      if (!d) continue;
      const frame = `big:${d.name}`;
      if (!tex.has(frame)) tex.add(frame, 0, d.rect.x, d.rect.y, d.rect.w, d.rect.h);
      const x = (p.tx + p.w / 2) * TILE;
      const bottom = (p.ty + p.h) * TILE;
      const y = bottom - (d.rect.h - d.pivot.y) * k;
      const make = () =>
        this.scene.add
          .image(x, y, this.skin.textureKey, frame)
          .setOrigin(d.pivot.x / d.rect.w, d.pivot.y / d.rect.h)
          .setScale(k);
      const upper = make().setDepth(entityDepth(bottom));
      const cut = typeof d.occludeAbove === 'number' ? Math.max(0, Math.round(d.pivot.y - d.occludeAbove)) : d.rect.h;
      if (cut < d.rect.h) {
        upper.setCrop(0, 0, d.rect.w, cut);
        this.bigImages.push(
          make()
            .setCrop(0, cut, d.rect.w, d.rect.h - cut)
            .setDepth(STRUCTURE_FX.OCCLUDE_BASE_DEPTH),
        );
      }
      this.bigImages.push(upper);
      const w: WallImage = {
        img: upper,
        left: x - d.pivot.x * k,
        right: x + (d.rect.w - d.pivot.x) * k,
        top: y - d.pivot.y * k,
        bottom: y - (d.pivot.y - cut) * k,
      };
      for (let cx = Math.floor(w.left / TILE); cx <= Math.floor((w.right - 1) / TILE); cx++) {
        const col = this.bigByColumn.get(cx);
        if (col) col.push(w);
        else this.bigByColumn.set(cx, [w]);
      }
      if (d.light) {
        const o = lightOffsetOf(d.light.offset);
        this.wallLightsFixed.push(
          reg.add(
            { ...d.light, radius: d.light.radius * k },
            o ? { x: x + (o.x - d.pivot.x) * k, y: y + (o.y - d.pivot.y) * k } : { x, y: y - d.pivot.y * k * 0.5 },
          ),
        );
      }
    }
    this.bigPlaced = list.length;
  }

  /** 타일셋 소품 JSON light → 광원 (반경 = 시트 도트 px × 배율) */
  private registerPropLights(props: readonly PropPlacement[]): void {
    const lit = new Map(this.skin.props.filter((p) => p.light).map((p) => [p.index, p.light!]));
    if (lit.size === 0) return;
    const reg = lightRegistryOf(this.scene);
    for (const p of props) {
      const l = lit.get(p.index);
      if (!l) continue;
      const o = lightOffsetOf(l.offset) ?? { x: this.skin.tilePx / 2, y: this.skin.tilePx / 2 };
      reg.add(
        { ...l, radius: l.radius * this.scale },
        { x: p.x * TILE + o.x * this.scale, y: p.y * TILE + o.y * this.scale },
      );
    }
  }

  /** 디버그 */
  get summary(): { bigProps: number; walls: number; faded: number; tilePx: number; heightTiles: number } {
    return {
      bigProps: this.bigPlaced,

      walls: this.walls.length,
      faded: this.faded.length,
      tilePx: this.skin.tilePx,
      heightTiles: this.skin.quarter?.heightTiles ?? 0,
    };
  }

  destroy(): void {
    for (const w of this.walls) w.img.destroy();
    this.walls = [];
    this.byColumn.clear();
    const reg = lightRegistryOf(this.scene);
    for (const l of [...this.wallLights, ...this.wallLightsFixed]) reg.remove(l);
    this.wallLights = [];
    this.wallLightsFixed = [];
    for (const i of this.bigImages) i.destroy();
    this.bigImages = [];
    this.ground.destroy();
    this.shadeLayer?.destroy();
    this.propsLayer?.destroy();
    this.map.destroy();
  }
}

/** 타일셋 이미지에 인덱스별 프레임(이름 = 인덱스)을 붙인다 (벽 그림을 Image 로 쓰려고) */
function ensureTileFrames(scene: Phaser.Scene, key: string, px: number): void {
  const tex = scene.textures.get(key);
  if (!tex || tex.key === '__MISSING' || tex.has('0')) return;
  const src = tex.getSourceImage() as { width: number; height: number };
  const cols = Math.floor(src.width / px);
  const rows = Math.floor(src.height / px);
  for (let i = 0; i < cols * rows; i++) tex.add(i, 0, (i % cols) * px, Math.floor(i / cols) * px, px, px);
}
