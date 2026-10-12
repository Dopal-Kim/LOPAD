/**
 * 62 루프 2 F (art §31-10): 외벽 테두리가 없는 방(수련장 일반 방)의 서·동 문틀 그림 — `tiles/border/<지역>/doors.json`.
 * 외벽 문(BorderView 문 조각)과 같은 배치 규칙(`sideDoorPlacement`)으로 문틀 · 발광(가산) · 횃불 빛을 그리고,
 * 닫힘 덮개·열림 시트는 `DoorLeaf`. ArenaDoors 는 BorderView 와 같은 꼴(`SideDoorHost`)로 쓴다.
 * 문틀은 벽 타일 위(그 문 줄 쿼터뷰 벽보다 앞) · 널문은 그 위.
 */
import Phaser from 'phaser';
import { ASSETS, BORDER, entityDepth } from '../core/Constants';
import { lightRegistryOf, type LightSource } from '../systems/lighting/lightRegistry';
import { loadBorderTexture } from './BorderView';
import { DoorLeaf, addDoorSheetFrames } from './DoorLeaf';
import {
  WORLD_PER_LOGICAL,
  borderFileRel,
  borderTextureKey,
  doorFiles,
  sideDoorPlacement,
  type BorderDoor,
  type DoorsOnlyDef,
  type WorldRect,
} from './border';

type Side = 'west' | 'east';

/** ArenaDoors 가 문 그림에 묻는 것 (BorderView · SideDoorArt 공용) */
export interface SideDoorHost {
  hasSideDoorArt(side: Side): boolean;
  hasDoorLeaf(side: Side): boolean;
  setDoorOpen(side: Side, open: boolean, animate: boolean): void;
}

export class SideDoorArt implements SideDoorHost {
  private readonly objects: Phaser.GameObjects.GameObject[] = [];
  private readonly lights: LightSource[] = [];
  private readonly leaves = new Map<Side, DoorLeaf>();
  private readonly leafOpen = new Map<Side, boolean>();
  private destroyed = false;
  ready = false;

  constructor(
    private readonly scene: Phaser.Scene,
    readonly def: DoorsOnlyDef,
    private readonly floor: WorldRect,
    /** 문 줄 (문 가운데 월드 y) */
    private readonly sideDoors: readonly { side: Side; y: number }[],
  ) {
    const files = [...new Set(sideDoors.flatMap((d) => (def.doors[d.side] ? doorFiles(def.doors[d.side]!) : [])))];
    void Promise.all(
      files.map((f) => loadBorderTexture(scene.textures, this.key(f), `${ASSETS.URL}/${borderFileRel(def.region, f)}`)),
    ).then(() => {
      if (!this.destroyed) this.build();
    });
  }

  private key(file: string): string {
    return borderTextureKey(this.def.region, file);
  }

  private build(): void {
    for (const d of this.sideDoors) {
      const door = this.def.doors[d.side];
      if (door && this.scene.textures.exists(this.key(door.image))) this.draw(d.side, door, d.y);
    }
    this.ready = true;
  }

  private draw(side: Side, door: BorderDoor, centerY: number): void {
    const scene = this.scene;
    const ps = this.def.pixelScale;
    const k = WORLD_PER_LOGICAL;
    const at = sideDoorPlacement(door, side, this.floor, centerY);
    // 문 줄 쿼터뷰 벽(Y 정렬) 앞 — 그림 아래 끝 줄 기준
    const depth = entityDepth(at.y + door.height * k) + 1e-4;
    const img = (file: string, d: number) =>
      scene.add
        .image(at.x, at.y, this.key(file))
        .setOrigin(0, 0)
        .setScale(ps * k)
        .setFlipX(door.flipX)
        .setDepth(d);
    this.objects.push(img(door.image, depth));
    if (door.emissive && scene.textures.exists(this.key(door.emissive)))
      this.objects.push(img(door.emissive, BORDER.DEPTH_EMISSIVE).setBlendMode(Phaser.BlendModes.ADD));
    const reg = lightRegistryOf(scene);
    for (const l of door.lights)
      this.lights.push(
        reg.add(
          {
            color: l.color,
            radius: l.radius * k,
            intensity: l.intensity,
            flicker: typeof l.flicker === 'number' ? l.flicker : (l.flicker?.amp ?? 0),
          },
          { x: at.x + l.x * k, y: at.y + l.y * k },
        ),
      );
    // 널문 (닫힘 덮개 · 열림 시트)
    const sheet = door.openSheet && scene.textures.exists(this.key(door.openSheet.file)) ? door.openSheet : null;
    const closedKey = door.closed && scene.textures.exists(this.key(door.closed)) ? this.key(door.closed) : null;
    if (!sheet && !closedKey) return;
    const key = sheet ? this.key(sheet.file) : closedKey!;
    const names = sheet
      ? addDoorSheetFrames(scene.textures, key, sheet.frames, sheet.frameWidth / ps, sheet.frameHeight / ps)
      : null;
    const leafImg = scene.add
      .image(at.x, at.y, key, names?.[0])
      .setOrigin(0, 0)
      .setScale(ps * k)
      .setDepth(depth + 1e-5);
    this.objects.push(leafImg);
    const frames = names && sheet ? { names, durationsMs: sheet.frameDurationsMs } : null;
    this.leaves.set(side, new DoorLeaf(scene, leafImg, frames, this.leafOpen.get(side) ?? false));
  }

  hasSideDoorArt(side: Side): boolean {
    return Boolean(this.def.doors[side]);
  }

  hasDoorLeaf(side: Side): boolean {
    const d = this.def.doors[side];
    return Boolean(d && (d.closed || d.openSheet));
  }

  setDoorOpen(side: Side, open: boolean, animate: boolean): void {
    this.leafOpen.set(side, open);
    this.leaves.get(side)?.set(open, animate);
  }

  summary(): Record<string, unknown> {
    return {
      region: this.def.region,
      ready: this.ready,
      objects: this.objects.length,
      lights: this.lights.length,
      leaves: [...this.leaves].map(([s, l]) => `${s}:${l.isOpen ? 'open' : 'closed'}`),
    };
  }

  destroy(): void {
    this.destroyed = true;
    for (const l of this.leaves.values()) l.destroy();
    this.leaves.clear();
    for (const o of this.objects) o.destroy();
    this.objects.length = 0;
    const reg = lightRegistryOf(this.scene);
    for (const l of this.lights) reg.remove(l);
    this.lights.length = 0;
  }
}
