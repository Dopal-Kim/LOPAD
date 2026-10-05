import Phaser from 'phaser';
import { UI_SCREEN, type UiElite } from '../contract/ui';
import { plateMidW, platePos, readPlateJson, slice3, type PlateSlices } from './eliteView';
import { GlowText } from './glow';
import { ELITE_PLATE_TEX, accentHex } from './kit';
import { GRAY, hexToNum } from './theme';
import { ELITE_PLATE } from './themeBuild';

interface Plate {
  name: string;
  box: Phaser.GameObjects.Container;
  text: GlowText;
  hp: Phaser.GameObjects.Graphics;
  w: number;
  h: number;
  hpX: number;
  hpW: number;
  hpY: number;
  lastHp: number;
}

/** 조각 프레임 이름 (이름표 텍스처에 한 번 더한다) */
const FRAME = { left: 'plate-l', mid: 'plate-m', right: 'plate-r' } as const;

/**
 * 60라운드 계약 §14.9 엘리트 이름표 — `UiSnapshot.elites`(화면 안의 살아 있는 엘리트)마다 머리 위에 아트 `elite_nameplate`
 * 바탕(가로 3조각: 캡 26 도트 · 가운데 반복 · 캡 26 도트, 도트 밀도 그대로 = scale 0.5) + 이름(권장 #eecc78 = 슬롯 25) +
 * 아래 체력 선. 문장 아이콘·외곽선·접두어 fx 는 월드(시스템·아트) 몫이고, 이름표는 그 위 2단(60 Q12): 머리 위 점에서
 * `ELITE_PLATE.aboveHead` 위가 이름표 아래 끝. 오버레이(메뉴·지도·일시정지)가 떠 있으면 숨긴다. id 로 재사용한다.
 */
export class ElitePlates {
  private plates = new Map<string, Plate>();
  private slices: PlateSlices | null = null;
  private meta: ReturnType<typeof readPlateJson> = null;
  private ready = false;
  private stageIndex = 0;

  constructor(private scene: Phaser.Scene) {}

  render(elites: readonly UiElite[] | undefined, show: boolean, stageIndex: number): void {
    const list = show && Array.isArray(elites) ? elites : [];
    if (stageIndex !== this.stageIndex) {
      this.stageIndex = stageIndex;
      this.clear();
    }
    const seen = new Set<string>();
    for (const e of list) {
      if (!e || typeof e.id !== 'string') continue;
      seen.add(e.id);
      let p = this.plates.get(e.id);
      if (p && p.name !== e.name) {
        p.box.destroy();
        p = undefined;
      }
      if (!p) {
        p = this.make(e.name);
        this.plates.set(e.id, p);
      }
      const pos = platePos(
        e.screen?.x ?? 0,
        e.screen?.y ?? 0,
        p.w,
        p.h,
        ELITE_PLATE.aboveHead,
        UI_SCREEN.WIDTH,
        UI_SCREEN.HEIGHT,
        ELITE_PLATE.margin,
      );
      p.box.setPosition(pos.x, pos.y);
      const ratio = e.maxHp > 0 ? Math.max(0, Math.min(1, e.hp / e.maxHp)) : 0;
      if (ratio !== p.lastHp) {
        p.lastHp = ratio;
        this.drawHp(p, ratio);
      }
    }
    for (const [id, p] of this.plates) {
      if (seen.has(id)) continue;
      p.box.destroy();
      this.plates.delete(id);
    }
  }

  destroy(): void {
    this.clear();
  }

  private clear(): void {
    for (const p of this.plates.values()) p.box.destroy();
    this.plates.clear();
  }

  /** 이름표 텍스처 조각을 한 번 준비한다 (없으면 글자만) */
  private prepare(): void {
    if (this.ready) return;
    this.ready = true;
    const scene = this.scene;
    this.meta = readPlateJson(scene.cache.json.get(ELITE_PLATE_TEX.json));
    if (!this.meta || !scene.textures.exists(ELITE_PLATE_TEX.key)) return;
    const s = slice3(this.meta.frame, this.meta.leftW, this.meta.rightW);
    const tex = scene.textures.get(ELITE_PLATE_TEX.key);
    for (const k of ['left', 'mid', 'right'] as const) {
      const pc = s[k];
      if (pc && !tex.has(FRAME[k])) tex.add(FRAME[k], 0, pc.tx, pc.ty, pc.w, pc.h);
    }
    this.slices = s;
  }

  private make(name: string): Plate {
    this.prepare();
    const scene = this.scene;
    const sc = ELITE_PLATE.scale;
    const text = new GlowText(scene, 0, 0, name, 'plate_name', { stageIndex: this.stageIndex });
    const s = this.slices;
    const meta = this.meta;
    const children: Phaser.GameObjects.GameObject[] = [];
    let w: number;
    let h: number;
    let textCy: number;
    let hpX: number;
    let hpW: number;
    let bottom: number;
    if (s && meta) {
      const midW = plateMidW(text.textW, sc, ELITE_PLATE.textPadDots, s, meta.minWidth);
      const key = ELITE_PLATE_TEX.key;
      const bg: Phaser.GameObjects.GameObject[] = [];
      if (s.left) bg.push(scene.add.image(s.left.dx, s.left.dy, key, FRAME.left).setOrigin(0, 0));
      if (s.mid) bg.push(scene.add.tileSprite(s.leftW, s.mid.dy, midW, s.mid.h, key, FRAME.mid).setOrigin(0, 0));
      if (s.right) bg.push(scene.add.image(s.leftW + midW + s.right.dx, s.right.dy, key, FRAME.right).setOrigin(0, 0));
      // 바탕만 도트 밀도(scale 0.5)로 줄인다 — 글자는 HUD 와 같은 1배
      children.push(scene.add.container(0, 0, bg).setScale(sc));
      w = Math.round((s.leftW + midW + s.rightW) * sc);
      bottom = Math.round(meta.pivotY * sc);
      h = bottom;
      textCy = meta.textCenterY * sc;
      hpX = Math.round(s.leftW * sc);
      hpW = Math.max(1, Math.round(midW * sc));
    } else {
      w = text.displayWidth;
      h = text.displayHeight;
      bottom = h;
      textCy = h / 2;
      hpX = 0;
      hpW = w;
    }
    text.setPosition(Math.round(w / 2 - text.displayWidth / 2), Math.round(textCy - text.displayHeight / 2));
    const hp = scene.add.graphics();
    children.push(text, hp);
    const hpY = bottom + ELITE_PLATE.hpGap;
    const box = scene.add.container(0, 0, children).setDepth(ELITE_PLATE.depth);
    return { name, box, text, hp, w, h, hpX, hpW, hpY, lastHp: -1 };
  }

  private drawHp(p: Plate, ratio: number): void {
    const g = p.hp.clear();
    g.fillStyle(hexToNum(GRAY[2]), 1).fillRect(p.hpX, p.hpY, p.hpW, ELITE_PLATE.hpH);
    const fw = Math.round(p.hpW * ratio);
    if (fw > 0)
      g.fillStyle(hexToNum(accentHex(this.scene, this.stageIndex, ELITE_PLATE.hpSlot)), 1).fillRect(
        p.hpX,
        p.hpY,
        fw,
        ELITE_PLATE.hpH,
      );
  }
}
